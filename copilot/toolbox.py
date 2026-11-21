"""The tools an assistant is offered, in one place: the mod's own (read over the game link) and the bridge's planning
tools, minus the ones the bridge keeps for itself. Whoever does the thinking reaches them through this: the bridge's own
loop with a plain model, or an outside agent over MCP (copilot/mcp_server.py)."""
import json
import time

BRIDGE_ONLY = {"chat_read", "say", "set_state", "events_read", "goal_state", "hear", "cron_report",   # cron_report: for scripts
               "panel_type", "panel_read"}                                     # panel_*: tests type as the player      # the bridge runs the channel; the model gets the rest
PLAN_ONLY = {"build", "occupancy", "frames", "avatar_walk", "avatar_mine", "avatar_travel", "progress", "lock_mode",
             "research_available", "spider_tend_step"}                          # spider_tend_step: run by spider_tend's timer                                              # reached through the planning tools, never called raw


# Tool groups (the Captain, 2026-11-20: the low bar is Qwen3 8B on a 12 GB card beside the game). A small model
# carries the core always and opens a group when a turn needs it, so the descriptions it carries stay short and the
# list it picks from stays small. A tool in no group is core. A grouped tool called by name opens its group by itself.
GROUPS = {
    "designs": ("save, edit, deploy, tile and redeploy blueprint designs; what a tile was built from",
                ["design_save", "design_edit", "design_export", "design_deploy", "design_tile", "deployments", "design_redeploy",
                 "design_undeploy", "what_is"]),
    "places": ("name a place on the map, or remove one of our names", ["mark_place", "forget_place"]),
    "cron": ("put a job on the timer, or pause, run or retire one", ["cron_add", "cron_change"]),
    "joints": ("where lines meet or cross, and how a building can be connected", ["joints", "connections", "plan_joint"]),
    "character": ("the avatar's hands and feet: walk, mine, craft, carry, travel to a planet",
                  ["avatar_craft", "avatar_carry", "walk_to", "mine", "travel_to"]),
    "goals": ("standing goals ('solve Nauvis', 'blue science'), science per minute, the run's numbers", ["set_goal", "science", "run_stats"]),
    "tidy": ("surplus, compacting a block, keeping every machine busy", ["surplus", "footprint", "utilisation"]),
    "ghosts": ("unbuilt ghosts: what they lack, and turning it into requests", ["ghost_needs", "ghost_requests"]),
    "rules": ("the rules this game relaxes and their switches", ["allowances", "set_allowance"]),
    "exploring": ("reveal more of the map", ["reveal_map"]),
    "spiders": ("the spidertrons the commander's body rides: list, send or follow, tend stranded ghosts",
                ["spiders", "spider_go", "spider_tend"]),
}
GROUP_OF = {name: g for g, (_, names) in GROUPS.items() for name in names}


def open_tools_spec(present):
    """The menu tool: one line per group that has tools here."""
    menu = ["%s (%s)" % (g, what) for g, (what, names) in GROUPS.items() if any(n in present for n in names)]
    return {"name": "open_tools",
            "description": "Open a group of tools for this turn; their descriptions arrive with your next step. Groups: " + "; ".join(menu) + ".",
            "parameters": {"group": {"type": "string", "required": True, "default": None, "description": "the group's name"}}}


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
