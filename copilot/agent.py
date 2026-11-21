"""One request from start to finish: the model thinks, calls tools, and answers. Every step is written to a log so a run
can be scored afterwards (tool misses, repeated failures, steps used)."""
import json
import pathlib
import time

from .models import schema

PROMPT = (pathlib.Path(__file__).parent / "prompt.md").read_text(encoding="utf-8")
from .toolbox import BRIDGE_ONLY, GROUP_OF, GROUPS, PLAN_ONLY, open_tools_spec   # noqa: F401  (BRIDGE_ONLY, PLAN_ONLY kept for callers)
MEMORY_TURNS = 6                                                    # how many earlier exchanges a model is reminded of
MEMORY_CHARS = 500                                                  # of each side of an exchange
MAX_RESULT = 6000                                                   # characters of one tool result shown to the model


NEWS = "News from the game: "


def light_note(text, limit=60):
    """The few words the working light shows beside 'thinking' (found live 2026-11-21: the Captain could not tell what
    'News from the game: an obvious bottlenec' meant). News the bridge brings up on its own reads as what Skippy noticed;
    a player's line reads as itself; either is cut at a word, never mid-word."""
    if text.startswith(NEWS):
        text = "noticed " + text[len(NEWS):].split(". ")[0].rstrip(".")
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return cut + "..."


class Agent:
    """groups True: the model carries the core tools and opens a group when a turn needs it (for small models);
    False: every tool, every step."""

    def __init__(self, game, model, log_path=None, max_steps=12, local=None, groups=True):
        self.game, self.model, self.max_steps, self.local = game, model, max_steps, local
        mod_tools = game.tools()
        self.has_alerts = any(t["name"] == "alerts" for t in mod_tools)
        offered = [t for t in mod_tools if t["name"] not in BRIDGE_ONLY and t["name"] not in PLAN_ONLY] + (local.specs() if local else [])
        self.by_name = {t["function"]["name"]: t for t in schema(offered)}
        self.names = set(self.by_name)
        self.groups = groups and any(n in GROUP_OF for n in self.names)
        if self.groups:
            self.menu = schema([open_tools_spec(self.names)])[0]
            self.core = [t for n, t in self.by_name.items() if n not in GROUP_OF] + [self.menu]
        else:
            self.core = list(self.by_name.values())
        self.tools = self.core                          # what a turn starts with
        self.log_path = log_path
        self.memory = []                                # the last few exchanges, words only: (who, what was asked, what was answered)

    def offer(self, opened):
        """The tools for the next step: the core and every group opened this turn."""
        return self.core + [t for n, t in self.by_name.items() if GROUP_OF.get(n) in opened]

    def open_group(self, group, opened):
        if group not in GROUPS:
            return {"ok": False, "error": "there is no group named '%s'" % group, "groups": sorted(GROUPS)}
        names = [n for n in GROUPS[group][1] if n in self.names]
        opened.add(group)
        return {"ok": True, "result": {"opened": group, "tools": names, "note": "their descriptions come with your next step"}}

    def alerts(self):
        """The game's alerts right now, as a short text for the model, and the set of alert kinds (for noticing new ones)."""
        if not self.has_alerts:
            return "", set()
        r = self.game.call("alerts")
        found = (r.get("result") or {}).get("alerts") or [] if r.get("ok") else []
        if not found:
            return "", set()
        parts = ["%s x%d on %s%s" % (a.get("kind"), a.get("count") or 1, a.get("surface"), (" (%s)" % a["means"]) if a.get("means") else "") for a in found]
        return "Alerts showing in the game right now: " + "; ".join(parts) + ".", {(a.get("surface"), a.get("kind")) for a in found}

    def log(self, **entry):
        if self.log_path:
            entry["time"] = time.strftime("%Y-%m-%d %H:%M:%S")
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")

    def remembered(self):
        """The last few exchanges as a short note for the model: words only, never tool results, so it costs little.
        Each turn otherwise starts fresh, which keeps a long game from filling the model's context."""
        if not self.memory:
            return ""
        lines = ["", "", "Earlier in this conversation (most recent last):"]
        for who, asked, answered in self.memory:
            lines.append("- %s: %s" % ("the player said" if who not in ("game", "goal", "leg", "check") else "you were told (%s)" % who, asked.replace(chr(10), " ")))
            lines.append("  you answered: %s" % answered.replace(chr(10), " "))
        return chr(10).join(lines)

    def handle(self, text, who="player", light=True):
        """Returns (answer, outcome, stats) for one request. `light` drives the working light in the game."""
        started = time.time()
        stats = {"steps": 0, "calls": 0, "misses": 0, "tokens_in": 0, "tokens_out": 0}
        self.log(event="request", who=who, text=text)
        if light:
            self.game.call("set_state", {"state": "thinking", "note": light_note(text)})
        alert_text, _ = self.alerts()                   # every turn starts from what the game itself is warning about
        messages = [{"role": "system", "content": PROMPT + self.remembered()}, {"role": "user", "content": text + ((chr(10) * 2 + alert_text) if alert_text else "")}]
        answer, seen, opened = None, {}, set()          # groups open for this turn only: each turn starts small
        try:
            for step in range(self.max_steps):
                stats["steps"] = step + 1
                reply = self.model.chat(messages, self.offer(opened))
                stats["tokens_in"] += reply.get("tokens_in") or 0
                stats["tokens_out"] += reply.get("tokens_out") or 0
                if not reply["tool_calls"]:
                    answer = reply["content"]
                    break
                messages.append({"role": "assistant", "content": reply["content"], "tool_calls": reply["tool_calls"], "blocks": reply.get("blocks")})
                if light:
                    self.game.call("set_state", {"state": "working", "note": reply["tool_calls"][0]["name"]})
                for c in reply["tool_calls"]:
                    stats["calls"] += 1
                    key = c["name"] + json.dumps(c["args"], sort_keys=True)
                    seen[key] = seen.get(key, 0) + 1
                    group = GROUP_OF.get(c["name"]) if self.groups else None
                    if self.groups and c["name"] == "open_tools":
                        result = self.open_group((c["args"] or {}).get("group"), opened)
                    elif c["name"] not in self.names:
                        result = {"ok": False, "error": "there is no tool named '%s'" % c["name"], "tools": sorted(self.names)}
                    elif seen[key] > 2:
                        result = {"ok": False, "error": "you have made this exact call %d times; it will not answer differently. Use what you have or try something else." % seen[key]}
                    elif self.local and c["name"] in self.local.names:
                        result = self.local.call(c["name"], c["args"])
                    else:
                        result = self.game.call(c["name"], c["args"])
                    if group and group not in opened:       # called by name from the rules: open its group for what follows
                        opened.add(group)
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
        if answer:                                      # so "yes, do that" next turn means something
            self.memory.append((who, text[:MEMORY_CHARS], answer[:MEMORY_CHARS]))
            del self.memory[:-MEMORY_TURNS]
        stats["seconds"] = round(time.time() - started, 1)
        self.log(event="answer", outcome=outcome, text=answer, **stats)
        if light:
            self.game.call("set_state", {"state": "idle" if answer else "failed", "note": "" if answer else outcome})
        return answer, outcome, stats
