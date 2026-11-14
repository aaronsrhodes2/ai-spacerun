"""Purple Skippy as the source of every turn (the Captain, 2026-11-13: purple Skippy in a specific workspace is the AI
for all turns; one source, one key, no collection of models).

Purple Skippy is an agent, not a bare model: Claude Code on skippy-pc thinking with Skippy Core's coder, reached through
the SkippyTel project's bridge (SkippyTel/services/claude-bridge). So the thinking loop is purple's own. This side only:
  - sends each turn to purple, in one conversation, in one workspace (a project of the bridge's registry), and
  - waits for the answer.
Purple reaches the game through the workspace's MCP server (copilot/mcp_server.py), which offers the same tools the
bridge's own loop would.

The bridge's calls used here:
  POST /workshop                {task, conv, message, project, brain: "core", who}   -> {ok, task, done}
  GET  /workshop/run/<task>?after=N&wait=S                                          -> {events, next, done, ok, error}
  POST /workshop/cancel/<task>                                                      stops a run
with `Authorization: Bearer <token>`. An event is {t: "text", text} or {t: "tool", name, detail}.

Purple is built for long jobs: a run takes minutes, and the bridge runs one at a time. It suits a standing goal handed
over whole. For quick answers to chat, the model behind it can be the source directly (COPILOT_SOURCE=anthropic)."""
import json
import time
import urllib.error
import urllib.request
import uuid


class SourceError(Exception):
    """The AI source could not answer, with a sentence a person can act on."""


def _http(method, url, token, body=None, timeout=40):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method=method, headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or "{}")
        except ValueError:
            return e.code, {}
    except (urllib.error.URLError, OSError) as e:
        raise SourceError("purple Skippy's bridge could not be reached at %s (%s). Is SkippyTel's bridge running?" % (url.split("/workshop")[0], getattr(e, "reason", e)))


class Purple:
    def __init__(self, url, token, workspace, http=_http, sleep=time.sleep, max_wait=3600, busy_wait=600):
        if not url or not token:
            raise SourceError("purple Skippy needs the bridge's address and its token (COPILOT_URL and COPILOT_KEY)")
        if not workspace:
            raise SourceError("purple Skippy needs a workspace: the id of a project in the bridge's registry (COPILOT_WORKSPACE)")
        self.url, self.token, self.workspace = url.rstrip("/"), token, workspace
        self.http, self.sleep, self.max_wait, self.busy_wait = http, sleep, max_wait, busy_wait

    def health(self):
        """(ready, a sentence). Never raises: a bridge that is down is an answer."""
        try:
            status, body = self.http("GET", self.url + "/health", self.token)
        except SourceError as e:
            return False, str(e)
        shop = body.get("workshop") or {}
        if status != 200:
            return False, "purple Skippy's bridge answered %s" % status
        if not shop.get("ready"):
            return False, shop.get("reason") or "purple Skippy is not ready"
        ids = [p.get("id") for p in shop.get("projects") or []]
        if ids and self.workspace not in ids:
            return False, "the workspace '%s' is not one of purple Skippy's projects (%s)" % (self.workspace, ", ".join(ids))
        return True, "ready" + (" (busy with another run right now)" if shop.get("busy") else "")

    def ask(self, message, conv):
        """One turn. Returns {"text", "tools": [names], "ok", "error"}. Waits while purple is busy with someone else."""
        task = "factorio-" + uuid.uuid4().hex[:16]
        body = {"task": task, "conv": conv, "message": message, "project": self.workspace, "brain": "core", "who": "factorio-copilot"}
        waited = 0
        while True:
            status, got = self.http("POST", self.url + "/workshop", self.token, body)
            if status == 200:
                break
            if status == 409 and got.get("error") == "busy" and waited < self.busy_wait:
                self.sleep(10)
                waited += 10
                continue
            raise SourceError(self._why(status, got))
        texts, tools, after, started = [], [], 0, time.time()
        while True:
            status, got = self.http("GET", "%s/workshop/run/%s?after=%d&wait=20" % (self.url, task, after), self.token)
            if status != 200:
                raise SourceError(self._why(status, got))
            for e in got.get("events") or []:
                if e.get("t") == "text" and e.get("text"):
                    texts.append(e["text"])
                elif e.get("t") == "tool":
                    tools.append(e.get("name") or "")
            after = got.get("next", after)
            if got.get("done"):
                return {"text": "\n".join(texts).strip(), "tools": tools, "ok": bool(got.get("ok")), "error": got.get("error")}
            if time.time() - started > self.max_wait:
                self.cancel(task)                               # do not leave a run going that nobody is waiting for
                raise SourceError("purple Skippy has been working on this for over %d minutes; it has been stopped" % (self.max_wait // 60))

    def cancel(self, task):
        """Stop a run. Never raises: this is tidying up."""
        try:
            status, _ = self.http("POST", "%s/workshop/cancel/%s" % (self.url, task), self.token, {})
            return status == 200
        except SourceError:
            return False

    @staticmethod
    def _why(status, got):
        if status == 401:
            return "purple Skippy's bridge refused the key (COPILOT_KEY)"
        if status == 503:
            return "purple Skippy's bridge is not ready: %s" % (got.get("message") or got.get("error") or "no token configured there")
        if status == 409:
            return "purple Skippy is busy with another run: %s" % (got.get("message") or "try again in a while")
        if status == 400:
            return "purple Skippy's bridge did not accept the request (is '%s' a project it knows?)" % (got.get("error") or "bad request")
        return "purple Skippy's bridge answered %s %s" % (status, got.get("error") or "")


TURN = ("You are playing Factorio as Skippy Copilot in this workspace. Follow the factorio-copilot skill. Use only the tools of the "
        "skippy-copilot MCP server to see and change the game; do not edit files or run commands for this. Answer the player in at most three "
        "short sentences of plain text.\n\n%s")


class PurpleAgent:
    """Stands where the bridge's own Agent stands, with purple Skippy doing the thinking and the tool calls."""

    def __init__(self, game, purple, toolbox, conv=None):
        self.game, self.purple, self.toolbox = game, purple, toolbox
        self.conv = conv or ("factorio-" + time.strftime("%Y%m%d-%H%M%S"))
        self.model = type("M", (), {"model": "purple Skippy in workspace '%s'" % purple.workspace})()
        self.tools = toolbox.offered
        self.names = toolbox.names
        self.local = toolbox.local
        self.has_alerts = "alerts" in toolbox.mod_names

    def log(self, **entry):
        self.toolbox.log(**entry)

    def alerts(self):
        if not self.has_alerts:
            return "", set()
        r = self.game.call("alerts")
        found = (r.get("result") or {}).get("alerts") if r.get("ok") else None
        if not isinstance(found, list) or not found:
            return "", set()
        parts = ["%s x%d on %s%s" % (a.get("kind"), a.get("count") or 1, a.get("surface"), (" (%s)" % a["means"]) if a.get("means") else "") for a in found]
        return "Alerts showing in the game right now: " + "; ".join(parts) + ".", {(a.get("surface"), a.get("kind")) for a in found}

    def handle(self, text, who="player", light=True):
        started = time.time()
        stats = {"steps": 1, "calls": 0, "misses": 0, "tokens_in": 0, "tokens_out": 0}
        self.log(event="request", who=who, text=text)
        if light:
            self.game.call("set_state", {"state": "thinking", "note": text[:40]})
        alert_text, _ = self.alerts()
        answer, outcome = None, "answered"
        try:
            got = self.purple.ask(TURN % (text + ((chr(10) * 2 + alert_text) if alert_text else "")), self.conv)
            stats["calls"] = sum(1 for n in got["tools"] if "skippy" in n.lower() or n in self.names)
            answer = got["text"] or None
            if not got["ok"]:
                outcome = "source error"
                self.log(event="error", error=str(got.get("error"))[:300])
                answer = answer or None
            elif not answer:
                outcome = "no answer"
        except SourceError as e:
            outcome, answer = "source error", None
            self.log(event="error", error=str(e)[:300])
            self.last_error = str(e)
        stats["seconds"] = round(time.time() - started, 1)
        self.log(event="answer", outcome=outcome if answer else (outcome if outcome != "answered" else "no answer"), text=answer, **stats)
        if light:
            self.game.call("set_state", {"state": "idle" if answer and outcome == "answered" else "failed", "note": "" if answer and outcome == "answered" else outcome})
        return answer, (outcome if answer or outcome != "answered" else "no answer"), stats
