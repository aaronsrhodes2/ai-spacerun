"""A client for purple Skippy's MCP door (SkippyTel's purple-mcp, on skippy-pc at http://127.0.0.1:47860/mcp).

Purple Skippy is the development agent: it can read and change the Captain's projects, run commands and tests, and
deploy. Every call hands it a task in plain words, and the work is a job, not a function call: seconds to minutes.
So nothing here is ever called from the game's own Lua (which cannot make HTTP calls anyway), never per tick, and the
game never waits on it. The path is:

    Factorio mod (Lua)  <->  RCON  <->  this bridge (Python)  <->  HTTP  <->  purple-mcp

The door is MCP Streamable HTTP, stateless: one JSON-RPC POST, one JSON answer. Its tools:
    purple_ask(message, conv?, project?, wait_s?)   -> {task, conv, text, steps, next, done, ok?}   or {busy: true}
    purple_result(task, after?, wait_s?)            -> the text since `after`, next, done, ok, error
    purple_cancel(task)
On loopback the door needs no key. From another machine it needs `Authorization: Bearer <PURPLE_MCP_KEY>`. The home
token never comes near this code: the door holds it.

Standard library only; no MCP SDK."""
import json
import time
import urllib.error
import urllib.request

DEFAULT_URL = "http://127.0.0.1:47860/mcp"
MIN_POLL = 2.0                              # never ask the door more often than this


class PurpleError(Exception):
    """Purple could not be reached or could not do it, with a sentence a person can act on."""


def _post(url, body, headers, timeout):
    """(status, parsed JSON). The door answers JSON; a server that answers as an event stream is read too."""
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers=dict({"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}, **headers))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, _parse(r.read().decode(), r.headers.get("Content-Type") or "")
    except urllib.error.HTTPError as e:
        try:
            return e.code, _parse(e.read().decode(), e.headers.get("Content-Type") or "")
        except ValueError:
            return e.code, {}


def _get(url, headers, timeout):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, json.loads(r.read().decode() or "{}")


def _parse(text, content_type):
    if "text/event-stream" in content_type:
        for line in text.splitlines():
            if line.startswith("data:"):
                return json.loads(line[5:].strip())
        return {}
    return json.loads(text or "{}")


class PurpleClient:
    def __init__(self, url=DEFAULT_URL, key="", post=_post, get=_get, timeout=130):
        self.url, self.key, self.post, self.get, self.timeout = (url or DEFAULT_URL).rstrip("/"), key or "", post, get, timeout
        self.ready = False
        self.next_id = 0

    def _headers(self):
        return {"Authorization": "Bearer " + self.key} if self.key else {}

    def _rpc(self, method, params):
        self.next_id += 1
        try:
            status, got = self.post(self.url, {"jsonrpc": "2.0", "id": self.next_id, "method": method, "params": params}, self._headers(), self.timeout)
        except (urllib.error.URLError, OSError, ValueError) as e:
            raise PurpleError("purple Skippy's door could not be reached at %s (%s). Is purple-mcp running on this computer?" % (self.url, getattr(e, "reason", e)))
        if status in (401, 403):
            raise PurpleError("purple Skippy's door refused the call: away from skippy-pc it needs its key (PURPLE_MCP_KEY)")
        if status != 200:
            raise PurpleError("purple Skippy's door answered %s" % status)
        if got.get("error"):
            raise PurpleError("purple Skippy's door refused the call: %s" % (got["error"].get("message") or got["error"]))
        return got.get("result") or {}

    def health(self):
        """(ready, a sentence). Never raises: a door that is shut is an answer."""
        try:
            status, got = self.get(self.url.rsplit("/", 1)[0] + "/health", self._headers(), 10)
        except (urllib.error.URLError, OSError, ValueError) as e:
            return False, "purple Skippy's door could not be reached at %s (%s). Is purple-mcp running on this computer?" % (self.url, getattr(e, "reason", e))
        if status != 200 or not got.get("ok"):
            return False, "purple Skippy's door answered %s" % status
        return True, "ready"

    def call(self, tool, args):
        """One tool call. The answer is a JSON string in result.content[0].text; isError means it failed."""
        if not self.ready:
            self._rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "skippy-copilot", "version": "1"}})
            self.ready = True
        result = self._rpc("tools/call", {"name": tool, "arguments": {k: v for k, v in args.items() if v is not None}})
        content = result.get("content") or []
        text = content[0].get("text") if content and isinstance(content[0], dict) else ""
        if result.get("isError"):
            raise PurpleError("purple Skippy could not do that: %s" % (text or "no reason given")[:300])
        try:
            got = json.loads(text or "{}")
        except ValueError:
            got = {"text": text}
        return got if isinstance(got, dict) else {"text": str(got)}

    def ask(self, message, conv=None, project=None, wait_s=30):
        """Start a run. Returns {task, conv, text, steps, next, done, ok?}, or {busy: True} when purple is on another job."""
        return self.call("purple_ask", {"message": message, "conv": conv, "project": project, "wait_s": wait_s})

    def result(self, task, after=0, wait_s=30):
        return self.call("purple_result", {"task": task, "after": after, "wait_s": wait_s})

    def cancel(self, task):
        """Stop a run. Never raises: this is tidying up."""
        try:
            self.call("purple_cancel", {"task": task})
            return True
        except PurpleError:
            return False

    def run_to_completion(self, message, conv=None, on_text=None, project=None, timeout=1800, poll=3.0, busy_wait=300,
                          sleep=time.sleep, clock=time.time):
        """Ask, then poll until done. Returns {text, steps, ok, error, task, conv}. `on_text` is given each new piece of
        text as it comes. Past `timeout` seconds the run is cancelled. This blocks its caller for as long as purple
        works, so the game loop does not use it: it keeps a job and polls between its other work (copilot/loop.py)."""
        poll = max(poll, MIN_POLL)
        started = clock()
        got = self.ask(message, conv, project, wait_s=30)
        while got.get("busy"):
            if clock() - started > busy_wait:
                raise PurpleError("purple Skippy is busy with another job; try again in a while")
            sleep(10)
            got = self.ask(message, conv, project, wait_s=30)
        task, texts, steps = got.get("task"), [], 0
        while True:
            piece = got.get("text") or ""
            if piece:
                texts.append(piece)
                if on_text:
                    on_text(piece)
            steps = merge_steps(steps, got.get("steps"))
            if got.get("done"):
                return {"text": "\n".join(texts).strip(), "steps": steps, "ok": got.get("ok") is not False, "error": got.get("error"),
                        "task": task, "conv": got.get("conv") or conv}
            if not task:
                raise PurpleError("purple Skippy's door gave no task id to follow")
            if clock() - started > timeout:
                self.cancel(task)
                raise PurpleError("purple Skippy worked on this for over %d minutes; it has been stopped" % (timeout // 60))
            sleep(poll)
            got = self.result(task, got.get("next") or 0, wait_s=30)


def merge_steps(have, more):
    """The door reports how many steps (tool uses) purple has taken, as a number."""
    return max(have, more) if isinstance(more, int) and not isinstance(more, bool) else have
