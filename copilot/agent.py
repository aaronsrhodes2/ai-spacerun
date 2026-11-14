"""One request from start to finish: the model thinks, calls tools, and answers. Every step is written to a log so a run
can be scored afterwards (tool misses, repeated failures, steps used)."""
import json
import pathlib
import time

from .models import schema

PROMPT = (pathlib.Path(__file__).parent / "prompt.md").read_text(encoding="utf-8")
BRIDGE_ONLY = {"chat_read", "say", "set_state", "events_read"}      # the bridge runs the channel; the model gets the rest
MAX_RESULT = 6000                                                   # characters of one tool result shown to the model


class Agent:
    def __init__(self, game, model, log_path=None, max_steps=12):
        self.game, self.model, self.max_steps = game, model, max_steps
        self.tools = schema([t for t in game.tools() if t["name"] not in BRIDGE_ONLY])
        self.names = {t["function"]["name"] for t in self.tools}
        self.log_path = log_path

    def log(self, **entry):
        if self.log_path:
            entry["time"] = time.strftime("%Y-%m-%d %H:%M:%S")
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")

    def handle(self, text, who="player", light=True):
        """Returns (answer, outcome, stats) for one request. `light` drives the working light in the game."""
        started = time.time()
        stats = {"steps": 0, "calls": 0, "misses": 0, "tokens_in": 0, "tokens_out": 0}
        self.log(event="request", who=who, text=text)
        if light:
            self.game.call("set_state", {"state": "thinking", "note": text[:40]})
        messages = [{"role": "system", "content": PROMPT}, {"role": "user", "content": text}]
        answer, seen = None, {}
        try:
            for step in range(self.max_steps):
                stats["steps"] = step + 1
                reply = self.model.chat(messages, self.tools)
                stats["tokens_in"] += reply.get("tokens_in") or 0
                stats["tokens_out"] += reply.get("tokens_out") or 0
                if not reply["tool_calls"]:
                    answer = reply["content"]
                    break
                messages.append({"role": "assistant", "content": reply["content"], "tool_calls": reply["tool_calls"]})
                if light:
                    self.game.call("set_state", {"state": "working", "note": reply["tool_calls"][0]["name"]})
                for c in reply["tool_calls"]:
                    stats["calls"] += 1
                    key = c["name"] + json.dumps(c["args"], sort_keys=True)
                    seen[key] = seen.get(key, 0) + 1
                    if c["name"] not in self.names:
                        result = {"ok": False, "error": "there is no tool named '%s'" % c["name"], "tools": sorted(self.names)}
                    elif seen[key] > 2:
                        result = {"ok": False, "error": "you have made this exact call %d times; it will not answer differently. Use what you have or try something else." % seen[key]}
                    else:
                        result = self.game.call(c["name"], c["args"])
                    if not result.get("ok"):
                        stats["misses"] += 1
                    self.log(event="tool", step=step + 1, name=c["name"], args=c["args"], ok=bool(result.get("ok")), error=result.get("error"))
                    shown = json.dumps(result)
                    if len(shown) > MAX_RESULT:
                        shown = shown[:MAX_RESULT] + " ...(cut: ask for less at a time)"
                    messages.append({"role": "tool", "name": c["name"], "tool_call_id": c["id"], "content": shown})
            outcome = "answered" if answer else "ran out of steps"
        except Exception as e:                          # the model server failing is a result too
            outcome, answer = "model error", None
            self.log(event="error", error=str(e)[:300])
        stats["seconds"] = round(time.time() - started, 1)
        self.log(event="answer", outcome=outcome, text=answer, **stats)
        if light:
            self.game.call("set_state", {"state": "idle" if answer else "failed", "note": "" if answer else outcome})
        return answer, outcome, stats
