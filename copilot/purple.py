"""Purple Skippy as the source of every turn (the Captain, 2026-11-13: purple Skippy in a specific workspace is the AI
for all turns; one source, one key, no collection of models).

Purple Skippy is an agent, not a bare model: it thinks in its own loop and reaches the game through the workspace's MCP
server (copilot/mcp_server.py), which offers the same tools the bridge's own loop would. This side only sends each
turn to purple, in one conversation, in one workspace (a project of purple's registry), and waits for the answer.

Purple is reached through its MCP door (copilot/purple_client.py), which needs no key on skippy-pc. Purple is built for
long jobs: a run takes seconds to minutes and it does one at a time, so as the source of every turn it is slow; for quick
turns a plain model source suits better, with purple called for a task by /purple in the game (copilot/loop.py)."""
import time

from .purple_client import DEFAULT_URL, PurpleClient, PurpleError


class SourceError(Exception):
    """The AI source could not answer, with a sentence a person can act on."""


class Purple:
    def __init__(self, url, key, workspace, client=None, max_wait=3600, busy_wait=600, sleep=time.sleep):
        if not workspace:
            raise SourceError("purple Skippy needs a workspace: the id of a project in purple's registry (COPILOT_WORKSPACE)")
        self.client = client or PurpleClient(url or DEFAULT_URL, key)
        self.url, self.workspace = getattr(self.client, "url", url), workspace
        self.max_wait, self.busy_wait, self.sleep = max_wait, busy_wait, sleep

    def health(self):
        """(ready, a sentence). Never raises."""
        return self.client.health()

    def ask(self, message, conv):
        """One turn. Returns {"text", "steps", "ok", "error"}. Waits while purple is busy with another job."""
        try:
            got = self.client.run_to_completion(message, conv, project=self.workspace, timeout=self.max_wait, busy_wait=self.busy_wait, sleep=self.sleep)
        except PurpleError as e:
            raise SourceError(str(e))
        return {"text": got["text"], "steps": got["steps"], "ok": got["ok"], "error": got["error"]}


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
            stats["calls"] = got["steps"]
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
