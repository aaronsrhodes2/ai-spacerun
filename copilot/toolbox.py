"""The tools an assistant is offered, in one place: the mod's own (read over the game link) and the bridge's planning
tools, minus the ones the bridge keeps for itself. Whoever does the thinking reaches them through this: the bridge's own
loop with a plain model, or an outside agent over MCP (copilot/mcp_server.py)."""
import json
import time

BRIDGE_ONLY = {"chat_read", "say", "set_state", "events_read", "goal_state"}      # the bridge runs the channel; the model gets the rest
PLAN_ONLY = {"build", "occupancy", "frames", "avatar_walk", "avatar_mine", "avatar_travel", "progress", "lock_mode",
             "research_available"}                                              # reached through the planning tools, never called raw


class Toolbox:
    def __init__(self, game, local=None, log_path=None):
        self.game, self.local, self.log_path = game, local, log_path
        mod_tools = game.tools()
        self.mod_names = {t["name"] for t in mod_tools}
        self.offered = [t for t in mod_tools if t["name"] not in BRIDGE_ONLY and t["name"] not in PLAN_ONLY] + (local.specs() if local else [])
        self.names = {t["name"] for t in self.offered}

    def log(self, **entry):
        if self.log_path:
            entry["time"] = time.strftime("%Y-%m-%d %H:%M:%S")
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")

    def call(self, name, args):
        """One tool call from whoever is thinking. Always returns a dict with 'ok'."""
        args = args if isinstance(args, dict) else {}
        if name not in self.names:
            return {"ok": False, "error": "there is no tool named '%s'" % name, "tools": sorted(self.names)}
        if self.local and name in self.local.names:
            return self.local.call(name, args)
        return self.game.call(name, args)
