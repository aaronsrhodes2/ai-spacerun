"""Planning tools the bridge adds to the mod's own: the arithmetic and geometry a small model gets wrong. Each one reads
its facts from the game through the mod (never from memory), plans in code, and hands back a short result. Nothing is
built by planning: a plan gets an id, and `build_plan` sends it to the game, as a dry run unless told otherwise.

The model sees these beside the mod's tools, in the same shape, and cannot tell the difference."""
import time

from . import milestones as ms
from .goals import Goal, GoalError
from .plan import calc, cells, joints, place, route
from .plan.layout import Layout, LayoutError

FACING = {"north": 0, "east": 1, "south": 2, "west": 3}            # quarter turns from the cell's own facing (inputs north)
MAX_ROUTE_WINDOW = 100


def _param(type_, description, required=False, default=None):
    return {"type": type_, "required": required, "default": default, "description": description}


SPECS = [
    {"name": "locate",
     "description": "Turn a place said in words into tiles. frame is what the words refer to: 'view' (what is on the player's screen), 'base' (where our buildings stand), 'map' (all the revealed map) or 'player' (around the player). part is the part of it: middle, north, south, east, west, or a corner such as 'upper right' or 'south-west'. Example: 'the east of the main base' is frame base, part east. Returns the rectangle and its centre.",
     "parameters": {"frame": _param("string", "view, base, map or player", True),
                    "part": _param("string", "middle, a side (north, top, left...) or a corner (upper right, south-west...)", default="middle")}},
    {"name": "plan_production",
     "description": "The whole factory behind one product: for a target such as 'two per second' or '90 a minute' it gives, for each recipe in the chain, how many machines, and the raw inputs and belts needed. Answers 'how many assemblers do I need to make this many of that'. Reads recipes and machine speeds from the game. Use it before building any production line; never work these numbers out yourself.",
     "parameters": {"item": _param("string", "internal name of the item to make", True),
                    "per_minute": _param("number", "how many per minute (give this or per_second)"),
                    "per_second": _param("number", "how many per second (give this or per_minute)"),
                    "machine": _param("string", "machine to use for assembling recipes, such as assembling-machine-2; leave out for the slowest that can make each recipe"),
                    "stop_at": _param("string", "comma-separated items to treat as supplied, not made here, such as 'iron-plate,copper-plate'")}},
    {"name": "plan_row",
     "description": "Lay out a row of identical machines, each fed and emptied the same way, at a place on the map. feed 'belt' gives an input belt along one side and an output belt along the other; feed 'robots' gives each machine a requester chest and a provider chest. Returns a picture of the plan and a plan_id; nothing is built until build_plan.",
     "parameters": {"machine": _param("string", "internal name of the machine", True),
                    "count": _param("number", "how many machines", True),
                    "x": _param("number", "x of the top-left tile of the row", True),
                    "y": _param("number", "y of the top-left tile of the row", True),
                    "feed": _param("string", "'belt' or 'robots'", default="belt"),
                    "recipe": _param("string", "recipe to set on every machine"),
                    "facing": _param("string", "side the inputs come from: north, east, south or west", default="north"),
                    "belt": _param("string", "belt to use", default="transport-belt"),
                    "inserter": _param("string", "inserter to use", default="inserter")}},
    {"name": "joints",
     "description": "The small patterns for where supply lines meet and cross, each with the problem it solves: belts crossing, pipes crossing belts, a splitter as a filter, merging with one side first, an overflow valve, a balancer, feeding one lane, picking one item off a mixed belt, fitting pipes to a machine's fluid connections, handing a belt to robots and back, long pipe runs, pole lines, the inserters beside a train wagon, and the rules for rail signals. Read this when a layout has such a meeting; then build it with plan_joint.",
     "parameters": {}},
    {"name": "connections",
     "description": "Every way one building can be connected, worked out from the game's own facts about it: its size, which side each fluid connection is on and whether it takes or gives, where heat connects, how many tiles of each side are free for inserters, and, with a recipe, how many belts its ingredients need and which joints fit. A building has only so many ways to meet its lines; read them here before laying one out.",
     "parameters": {"machine": _param("string", "internal name of the building", True),
                    "recipe": _param("string", "the recipe it will run, to see what that recipe needs of the connections")}},
    {"name": "plan_joint",
     "description": "Lay out one joint at a place on the map. Every joint is designed with its main flow running north; facing turns it (the direction the main flow runs). Returns a picture and a plan_id; nothing is built until build_plan.",
     "parameters": {"joint": _param("string", "the joint's name, from the joints tool", True),
                    "x": _param("number", "x of the joint's top-left tile", True),
                    "y": _param("number", "y of the joint's top-left tile", True),
                    "facing": _param("string", "the direction the main flow runs: north, east, south or west", default="north"),
                    "item": _param("string", "for filter_splitter and filtered_pick: the item to filter. For barrel_station: the fluid. For fluid_machine_on_belts and robot_machine: the recipe to set"),
                    "side": _param("string", "for filter_splitter (the side the item leaves), priority_merge (the input served first) and side_load: 'left' or 'right'"),
                    "width": _param("number", "for the crossings: how many belts side by side are crossed"),
                    "action": _param("string", "for wagon_side: 'unload' or 'load'. For barrel_station: 'fill' or 'empty'"),
                    "wagons": _param("number", "for wagon_side: how many wagons"),
                    "lanes": _param("number", "for balancer: 2 or 4 belts"),
                    "machine": _param("string", "for machine_ports and reach_over: the machine; its size and fluid connections are read from the game"),
                    "length": _param("number", "for long_pipe and pole_line: tiles from end to end"),
                    "spacing": _param("number", "for pole_line: tiles from pole to pole; leave out to use the pole's own reach"),
                    "pole": _param("string", "for pole_line: which pole"),
                    "belt": _param("string", "belt to use", default="transport-belt")}},
    {"name": "plan_route",
     "description": "Find a way for a belt or a pipe from one tile to another around everything that stands between, going underground where it must. Reads what is in the way from the game. Returns the length and a plan_id; nothing is built until build_plan.",
     "parameters": {"kind": _param("string", "'belt' or 'pipe'", True),
                    "from_x": _param("number", "x of the first tile", True), "from_y": _param("number", "y of the first tile", True),
                    "to_x": _param("number", "x of the last tile", True), "to_y": _param("number", "y of the last tile", True),
                    "item": _param("string", "which belt or pipe to lay; leave out for the basic one"),
                    "end_facing": _param("string", "for a belt: which way the last tile should face (north, east, south, west) to feed what is beside it"),
                    "surface": _param("string", "surface name; leave out for where the player is")}},
    {"name": "build_plan",
     "description": "Send a plan to the game. With dry_run true (the default) nothing is placed: the game says whether every piece could be placed and why not. Always dry-run first; build with dry_run false only after a clean dry run.",
     "parameters": {"plan_id": _param("string", "the id a plan_ tool returned", True),
                    "dry_run": _param("boolean", "true to only check, false to build", default=True),
                    "surface": _param("string", "surface name; leave out for where the player is")}},
]

AVATAR_SPECS = [
    {"name": "walk_to",
     "description": "Walk the avatar (the character) to a tile and wait until it gets there. It walks by the game's own pathfinder, round whatever is in the way; nothing is teleported. Says where it ended up, or why it could not get there.",
     "parameters": {"x": _param("number", "tile x to walk to", True), "y": _param("number", "tile y to walk to", True),
                    "near": _param("number", "how many tiles from the spot count as arrived", default=1)}},
    {"name": "mine",
     "description": "Have the avatar mine by hand at a tile (ore, a tree, a rock) until it carries `count` more, and wait for it. It walks there first. Use it early in the game, before there are mining drills.",
     "parameters": {"x": _param("number", "tile x of what to mine", True), "y": _param("number", "tile y of what to mine", True),
                    "count": _param("number", "how many to gather", default=10)}},
    {"name": "travel_to",
     "description": "Send the avatar to another planet the way a player travels, and wait until it has landed: it walks to a rocket silo with a rocket ready, rides the rocket to a ship in orbit whose schedule goes there, rides the ship, and drops to the surface. The avatar must carry nothing. The trip takes many minutes of game time. Says where it ended up, or why it could not go and where it is now.",
     "parameters": {"planet": _param("string", "internal name of the planet, such as 'vulcanus'", True),
                    "ship": _param("string", "name of the platform to ride; leave out for any ship in orbit that goes there")}},
    {"name": "set_goal",
     "description": "Take on a standing goal: something the player asks for once that you then keep working toward on your own, turn after turn, without further prompts, until it is reached or the player says stop. kind 'win' plays the game to its end; 'place' finishes everything for one place (give place: nauvis, space, vulcanus, fulgora, gleba, aquilo or edge); 'milestone' reaches one milestone (give its id, from the milestones tool); 'science' makes at least per_minute of every science pack a minute. Use it when the player says things like 'solve Nauvis', 'finish the game', 'get us to blue science', or 'I want 1,000 science a minute'.",
     "parameters": {"kind": _param("string", "'win', 'place', 'milestone' or 'science'", True),
                    "place": _param("string", "for kind place: nauvis, space (the first platform), vulcanus, fulgora, gleba, aquilo or edge"),
                    "milestone": _param("string", "for kind milestone: its id, such as 'rocket-silo'"),
                    "per_minute": _param("number", "for kind science: packs a minute wanted of each science")}},
    {"name": "clear_goal",
     "description": "Drop the standing goal, so you stop working on your own. Use it when the player says stop, or changes their mind.",
     "parameters": {}},
    {"name": "milestones",
     "description": "How far the game has come and what to do next: how many milestones are done, the next one not yet done with exactly what it still needs, and what comes after. Call it when asked 'what should we do next' or when deciding what to work on.",
     "parameters": {}},
]
SPECS = SPECS + AVATAR_SPECS

UNDERGROUND = {"transport-belt": "underground-belt", "fast-transport-belt": "fast-underground-belt",
               "express-transport-belt": "express-underground-belt", "turbo-transport-belt": "turbo-underground-belt", "pipe": "pipe-to-ground"}


class ToolError(Exception):
    def __init__(self, error, hint=None):
        super().__init__(error)
        self.error, self.hint = error, hint


class LocalTools:
    def __init__(self, game, sleep=time.sleep, poll=0.5, patience=600):
        """sleep and poll set how the bridge waits for the avatar; patience is how many polls before it stops waiting
        (the job itself goes on in the game)."""
        self.game = game
        self.sleep, self.poll, self.patience = sleep, poll, patience
        self.plans = {}
        self.goal = None                    # the standing goal, if the player gave one
        self.goal_paused = False            # true while the assistant is stuck on it and waiting for the player
        self.next_id = 1
        self.names = {s["name"] for s in SPECS}

    def specs(self):
        return SPECS

    # ---- facts from the game -------------------------------------------------------------------------------------
    def fact(self, name, kind):
        r = self.game.call("lookup", {"name": name, "kind": kind})
        if not r.get("ok"):
            raise ToolError(r.get("error") or "lookup failed", r.get("hint"))
        return r["result"][0]

    def maybe(self, name, kind):
        r = self.game.call("lookup", {"name": name, "kind": kind})
        return r["result"][0] if r.get("ok") and r.get("result") else None

    # ---- the tools -----------------------------------------------------------------------------------------------
    def call(self, name, args):
        args = dict(args or {})
        spec = next(s for s in SPECS if s["name"] == name)
        for key in args:
            if key not in spec["parameters"]:
                return {"ok": False, "error": "'%s' has no parameter '%s'" % (name, key), "tool": spec}
        for key, p in spec["parameters"].items():
            if key not in args or args[key] is None:
                if p["required"]:
                    return {"ok": False, "error": "'%s' needs the parameter '%s'" % (name, key), "tool": spec}
                args[key] = p["default"]
        try:
            return {"ok": True, "result": getattr(self, name)(**args)}
        except ToolError as e:
            return {"ok": False, "error": e.error, "hint": e.hint}
        except (calc.PlanError, LayoutError, place.PlaceError, GoalError) as e:    # RouteError is a LayoutError
            return {"ok": False, "error": str(e)}

    def locate(self, frame, part="middle"):
        r = self.game.call("frames")
        if not r.get("ok"):
            raise ToolError(r.get("error") or "the game could not say where things are", r.get("hint"))
        out = place.locate(r["result"], frame, part)
        out["surface"] = r["result"].get("surface")
        return out

    def plan_production(self, item, per_minute=None, per_second=None, machine=None, stop_at=None):
        if (per_minute is None) == (per_second is None):
            raise ToolError("give the rate as per_minute or as per_second, one of the two")
        if per_second is not None:
            per_minute = per_second * 60.0
        if per_minute <= 0:
            raise ToolError("the rate must be above zero")
        stop = {s.strip() for s in (stop_at or "").split(",") if s.strip()}
        recipes, machines = {}, {}

        def recipe_for(name):
            if name in recipes:
                return recipes[name]
            found = None
            info = self.maybe(name, "item")
            if info:                                                  # fluids have no item entry: they are treated as supplied
                made_by = info.get("made_by_recipes") or []
                pick = name if name in made_by else (made_by[0] if made_by else None)
                if pick:
                    found = self.maybe(pick, "recipe")
            recipes[name] = found
            return found

        def speed_for(recipe):
            made_in = recipe.get("made_in") or []
            choice = machine if (machine and machine in made_in) else (made_in[0] if made_in else None)
            if not choice:
                raise ToolError("no machine in the game can run the recipe '%s'" % recipe["name"])
            if choice not in machines:
                machines[choice] = self.fact(choice, "entity").get("crafting_speed") or 1
            recipe["_machine"] = choice
            return machines[choice]

        if recipe_for(item) is None:
            raise ToolError("'%s' is not made by any recipe: it is a raw input or a fluid" % item, "use 'search' to check the name")
        plan = calc.chain(item, per_minute / 60.0, recipe_for, speed_for, raw=stop)
        steps = []
        for s in plan["steps"]:
            r = recipes[s["product"]]
            steps.append({"make": s["product"], "recipe": s["recipe"], "machine": r["_machine"], "machines": s["machines"],
                          "per_minute": round(s["per_second"] * 60, 2),
                          "available_now": bool(r.get("available_now")),
                          "inputs_per_minute": {k: round(v * 60, 2) for k, v in s["inputs_per_second"].items()}})
        raw = {k: round(v * 60, 2) for k, v in plan["raw_per_second"].items()}
        belts = {k: calc.belts_for(v / 60.0)["fills_one_belt"] for k, v in raw.items()}
        return {"item": item, "per_minute": round(per_minute, 2), "per_second": round(per_minute / 60.0, 3), "steps": steps, "supplied_per_minute": raw,
                "basic_belts_needed": {k: round(v, 2) for k, v in belts.items()},
                "not_yet_researched": [s["recipe"] for s in steps if not s["available_now"]] or None}

    def plan_row(self, machine, count, x, y, feed="belt", recipe=None, facing="north", belt="transport-belt", inserter="inserter"):
        if facing not in FACING:
            raise ToolError("facing must be north, east, south or west")
        if feed not in ("belt", "robots"):
            raise ToolError("feed must be 'belt' or 'robots'")
        count = int(count)
        if not 1 <= count <= 50:
            raise ToolError("count must be between 1 and 50")
        m = self.fact(machine, "entity")
        w, h = m.get("tiles_wide"), m.get("tiles_high")
        if not w or not h:
            raise ToolError("the game gave no size for '%s'" % machine)
        if recipe:
            r = self.fact(recipe, "recipe")
            if machine not in (r.get("made_in") or []):
                raise ToolError("'%s' cannot run the recipe '%s'" % (machine, recipe), "it can be made in: %s" % ", ".join(r.get("made_in") or []))
        cell = cells.belt_cell(machine, w, h, belt, inserter, recipe) if feed == "belt" else cells.robot_cell(machine, w, h, inserter, recipe)
        lay = cells.row(cell, count, gap=0 if feed == "belt" else 0).turned(FACING[facing]).at_origin().moved(int(x), int(y))
        chars = {machine: "M", belt: "b", inserter: "i", "requester-chest": "R", "passive-provider-chest": "P"}
        b = lay.bounds()
        return {"plan_id": self._keep(lay.entities(), "row of %d %s" % (count, machine)), "pieces": lay.count(),
                "covers": {"from_x": b[0], "from_y": b[1], "to_x": b[2], "to_y": b[3]},
                "picture": lay.picture(chars), "legend": "M machine, b belt, i inserter, R requester chest, P provider chest",
                "next": "call build_plan with this plan_id to check it against the map (dry run)"}

    def connections(self, machine, recipe=None):
        m = self.fact(machine, "entity")
        w, h = m.get("tiles_wide"), m.get("tiles_high")
        if not w or not h:
            raise ToolError("the game gave no size for '%s'" % machine)
        ports = m.get("fluid_ports") if isinstance(m.get("fluid_ports"), list) else []
        heat = (m.get("heat") or {}).get("connections") if isinstance(m.get("heat"), dict) else None
        length = {"north": w, "south": w, "east": h, "west": h}
        sides = {}
        for side in ("north", "east", "south", "west"):
            here = [p for p in ports if p.get("direction") == side]
            sides[side] = {"tiles": length[side], "fluid_connections": [{"flow": p.get("flow"), "fluid": p.get("fluid")} for p in here],
                           "tiles_free_for_inserters": max(0, length[side] - len(here))}
        ways = [{"way": "items by belt", "how": "plan_row with feed 'belt': a belt along one side, a belt along the opposite side, an inserter each"},
                {"way": "items by robots", "how": "plan_joint robot_machine: a requester chest in, a provider chest out"},
                {"way": "items straight from a neighbouring machine", "how": "an inserter between the two machines, picking up from the one that makes the item"}]
        if ports:
            ways.append({"way": "fluids by pipe", "how": "plan_joint machine_ports shows a pipe stub on each connection"})
            ways.append({"way": "items by belt and fluids by pipe together", "how": "plan_joint fluid_machine_on_belts: pipes on the belt sides tunnel under the belts"})
        if heat:
            ways.append({"way": "heat", "how": "a heat pipe touching one of its %d heat connections" % len(heat)})
        out = {"machine": machine, "tiles_wide": w, "tiles_high": h, "sides": sides, "heat_connections": len(heat) if heat else None, "ways": ways,
               "note": "sides are for the building facing north; turning the building turns them with it"}
        if recipe:
            r = self.fact(recipe, "recipe")
            if machine not in (r.get("made_in") or []):
                raise ToolError("'%s' cannot run the recipe '%s'" % (machine, recipe), "it can be made in: %s" % ", ".join(r.get("made_in") or []))
            items_in = [i["name"] for i in r.get("ingredients") or [] if i.get("type") != "fluid"]
            fluids_in = [i["name"] for i in r.get("ingredients") or [] if i.get("type") == "fluid"]
            fluids_out = [i["name"] for i in r.get("products") or [] if i.get("type") == "fluid"]
            takes = len([p for p in ports if p.get("flow") in ("input", "input-output")])
            gives = len([p for p in ports if p.get("flow") in ("output", "input-output")])
            problems = []
            if len(fluids_in) > takes:
                problems.append("the recipe takes %d fluids and the building has %d fluid inputs" % (len(fluids_in), takes))
            if len(fluids_out) > gives:
                problems.append("the recipe gives %d fluids and the building has %d fluid outputs" % (len(fluids_out), gives))
            if len(items_in) <= 2:
                belts = "one belt, a lane for each item (plan_joint lane_pair makes such a belt)" if len(items_in) == 2 else "one belt"
            elif len(items_in) <= 4:
                belts = "two belts, two items on each; the far belt is reached with a long-handed inserter (plan_joint reach_over)"
            else:
                belts = "more than two belts' worth: feed it by robots (plan_joint robot_machine)"
            fits = "fluid_machine_on_belts" if (fluids_in or fluids_out) and items_in else ("machine_ports" if (fluids_in or fluids_out) else "plan_row, or robot_machine for small numbers")
            out["for_recipe"] = {"recipe": recipe, "items_in": items_in, "fluids_in": fluids_in, "fluids_out": fluids_out,
                                 "belts_needed_for_items": belts if items_in else "none", "joint_that_fits": fits, "problems": problems or None}
        return out

    def joints(self):
        return {"joints": joints.catalogue(), "note": "every joint is designed with its main flow running north; plan_joint turns it"}

    def plan_joint(self, joint, x, y, facing="north", item=None, side=None, width=None, action=None, wagons=None, lanes=None, machine=None,
                   length=None, spacing=None, pole=None, belt="transport-belt"):
        if facing not in FACING:
            raise ToolError("facing must be north, east, south or west")
        options = {"belt": belt}
        if joint == "pipe_crossing":
            options = {"belt": belt}
        if item is not None and joint in ("filter_splitter", "filtered_pick"):
            if not self.maybe(item, "item"):
                raise ToolError("there is no item named '%s'" % item, "use 'search' to find the name")
            options["item"] = item
        elif item is not None:
            options["item"] = item                                  # other joints give it their own meaning below
        if side is not None:
            options[{"filter_splitter": "to", "priority_merge": "first"}.get(joint, "side")] = side
        if width is not None:
            options["width"] = int(width)
        if action is not None:
            options["action"] = action
        if wagons is not None:
            options["wagons"] = int(wagons)
        if lanes is not None:
            options["lanes"] = int(lanes)
        if length is not None:
            options["length"] = int(length)
        if side is not None and joint == "overflow_valve":
            options.pop("side", None)
            options["keep"] = side
        if joint == "barrel_station":
            if not item:
                raise ToolError("the joint 'barrel_station' needs 'item': the fluid to barrel, such as 'crude-oil'")
            options.pop("item", None)
            recipe = ("%s-barrel" % item) if (action or "fill") == "fill" else ("empty-%s-barrel" % item)
            if action not in (None, "fill", "empty"):
                raise ToolError("for barrel_station, action is 'fill' or 'empty'")
            options.pop("action", None)
            r = self.maybe(recipe, "recipe")
            if not r:
                raise ToolError("the game has no barrel recipe for '%s'" % item, "not every fluid can be barrelled; use 'search' with 'barrel'")
            machine = machine or next((m for m in (r.get("made_in") or []) if m.startswith("assembling-machine")), None) or (r.get("made_in") or [None])[0]
            if not machine or machine not in (r.get("made_in") or []):
                raise ToolError("'%s' cannot run the recipe '%s'" % (machine, recipe), "it can be made in: %s" % ", ".join(r.get("made_in") or []))
            options["recipe"] = recipe
        if joint in ("machine_ports", "reach_over", "fluid_machine_on_belts", "barrel_station", "robot_machine"):
            if not machine:
                raise ToolError("the joint '%s' needs the parameter 'machine'" % joint)
            m = self.fact(machine, "entity")
            options.update(machine=machine, width=m.get("tiles_wide"), height=m.get("tiles_high"))
            options.pop("width", None) if not m.get("tiles_wide") else None
            if joint in ("machine_ports", "fluid_machine_on_belts", "barrel_station"):
                ports = m.get("fluid_ports")
                if not isinstance(ports, list) or not ports:
                    raise ToolError("'%s' has no fluid connections" % machine, "this joint is for machines that take or give fluids")
                options["ports"] = ports
        if joint == "pole_line":
            name = pole or "medium-electric-pole"
            p = self.fact(name, "entity")
            reach, supply = p.get("pole_wire_reach"), p.get("pole_supply_tiles")
            if not reach:
                raise ToolError("'%s' is not a power pole" % name)
            options["pole"] = name
            options["spacing"] = int(spacing) if spacing is not None else max(1, int(min(reach, supply or reach)))
            if options["spacing"] > reach:
                raise ToolError("poles %d tiles apart are out of wire reach: a %s reaches %s" % (options["spacing"], name, reach))
        if joint == "long_pipe":
            options.pop("belt", None)
        if joint in ("fluid_machine_on_belts", "robot_machine") and item is not None:      # for these, item names the recipe to set
            options.pop("item", None)
            r = self.fact(item, "recipe")
            if machine not in (r.get("made_in") or []):
                raise ToolError("'%s' cannot run the recipe '%s'" % (machine, item), "it can be made in: %s" % ", ".join(r.get("made_in") or []))
            options["recipe"] = item
        lay = joints.make(joint, **options).turned(FACING[facing]).at_origin().moved(int(x), int(y))
        b = lay.bounds()
        chars = {belt: "b", "splitter": "S", "inserter": "i", "long-handed-inserter": "L", "pipe": "p", "pipe-to-ground": "q", "steel-chest": "C",
                 "passive-provider-chest": "C", "requester-chest": "C"}
        if machine:
            chars[machine] = "M"
        if joint == "pole_line":
            chars[options["pole"]] = "P"
        for u in joints.UNDERGROUND.values():
            chars[u] = "U"
        return {"plan_id": self._keep(lay.entities(), "%s joint" % joint), "pieces": lay.count(), "solves": joints.JOINTS[joint]["solves"],
                "covers": {"from_x": b[0], "from_y": b[1], "to_x": b[2], "to_y": b[3]},
                "picture": lay.picture(chars), "legend": "b belt, U underground belt, S splitter, i inserter, L long-handed inserter, p pipe, q underground pipe, C chest, M machine, P pole",
                "next": "call build_plan with this plan_id to check it against the map (dry run)"}

    def plan_route(self, kind, from_x, from_y, to_x, to_y, item=None, end_facing=None, surface=None):
        if kind not in ("belt", "pipe"):
            raise ToolError("kind must be 'belt' or 'pipe'")
        start, goal = (int(from_x), int(from_y)), (int(to_x), int(to_y))
        margin = 12
        left, top = min(start[0], goal[0]) - margin, min(start[1], goal[1]) - margin
        width, height = abs(start[0] - goal[0]) + 2 * margin + 1, abs(start[1] - goal[1]) + 2 * margin + 1
        if width > MAX_ROUTE_WINDOW or height > MAX_ROUTE_WINDOW:
            raise ToolError("the two ends are too far apart for one route", "route it in stages of at most %d tiles" % (MAX_ROUTE_WINDOW - 2 * margin - 1))
        args = {"x": left, "y": top, "width": width, "height": height}
        if surface:
            args["surface"] = surface
        occ = self.game.call("occupancy", args)
        if not occ.get("ok"):
            raise ToolError(occ.get("error") or "the map could not be read", occ.get("hint"))
        blocked, pipes = set(), set()
        for j, row in enumerate(occ["result"]["rows"]):
            for i, ch in enumerate(row):
                if ch != ".":
                    blocked.add((left + i, top + j))
                if ch == "p":
                    pipes.add((left + i, top + j))
        bounds = (left, top, left + width - 1, top + height - 1)
        name = item or ("transport-belt" if kind == "belt" else "pipe")
        under = UNDERGROUND.get(name)
        if not under:
            raise ToolError("no underground piece is known for '%s'" % name, "use one of: %s" % ", ".join(sorted(UNDERGROUND)))
        if kind == "belt":
            if end_facing is not None and end_facing not in FACING:
                raise ToolError("end_facing must be north, east, south or west")
            reach = {"underground-belt": 4, "fast-underground-belt": 6, "express-underground-belt": 8, "turbo-underground-belt": 10}[under]
            r = route.belt(start, goal, blocked, name, under, reach, None if end_facing is None else FACING[end_facing] * 4, bounds=bounds)
        else:
            r = route.pipe(start, goal, blocked, route.beside_pipes(pipes) - {start, goal}, name, under, 9, bounds=bounds)
        pieces = [dict(p, x=p["x"] + 0.5, y=p["y"] + 0.5) for p in r["pieces"]]
        return {"plan_id": self._keep(pieces, "%s route from %d,%d to %d,%d" % ((kind,) + start + goal)), "tiles": r["length"],
                "pieces": len(pieces), "underground_pairs": r["undergrounds"],
                "next": "call build_plan with this plan_id to check it against the map (dry run)"}

    # ---- the avatar: start a job in the game, then wait for it ----------------------------------------------------
    def _wait(self, job_id):
        """Poll the avatar until the job with this id has ended. Returns its result as the mod recorded it."""
        for _ in range(self.patience):
            r = self.game.call("avatar")
            if not r.get("ok"):
                raise ToolError(r.get("error") or "the avatar could not be read")
            state = r["result"]
            last = state.get("last_job") or {}
            if last.get("id") == job_id and not state.get("job"):
                return last, state
            self.sleep(self.poll)
        raise ToolError("the avatar is still working after a long wait", "call 'avatar' to see how far it is, or 'avatar_stop' to stop it")

    def _start(self, tool, args):
        r = self.game.call(tool, args)
        if not r.get("ok"):
            raise ToolError(r.get("error") or "the avatar could not start", r.get("hint"))
        return r["result"]

    def walk_to(self, x, y, near=1):
        started = self._start("avatar_walk", {"x": x, "y": y, "near": near})
        last, state = self._wait(started["job"])
        if not last.get("ok"):
            raise ToolError("the avatar did not get there: %s" % (last.get("reason") or "no reason given"),
                            "it is at %s,%s now" % (state.get("x"), state.get("y")))
        return {"arrived": True, "x": state.get("x"), "y": state.get("y"), "game_seconds": round((last.get("ticks") or 0) / 60.0, 1)}

    def mine(self, x, y, count=10):
        started = self._start("avatar_mine", {"x": x, "y": y, "count": count})
        last, state = self._wait(started["job"])
        out = {"item": started.get("gives"), "mined": last.get("mined") or 0, "asked": count, "carries": state.get("carries"),
               "game_seconds": round((last.get("ticks") or 0) / 60.0, 1)}
        if not last.get("ok"):
            raise ToolError("the avatar could not mine there: %s" % (last.get("reason") or "no reason given"))
        if last.get("reason"):
            out["note"] = last["reason"]
        return out

    def travel_to(self, planet, ship=None):
        args = {"planet": planet}
        if ship:
            args["ship"] = ship
        started = self._start("avatar_travel", args)
        last, state = self._wait(started["job"])
        if not last.get("ok"):
            raise ToolError("the avatar did not reach %s: %s" % (planet, last.get("reason") or "no reason given"),
                            "it is on %s now (stopped while: %s)" % (state.get("surface"), last.get("stage") or "setting off"))
        return {"arrived": True, "planet": planet, "ship": started.get("ship"), "surface": state.get("surface"),
                "game_minutes": round((last.get("ticks") or 0) / 3600.0, 1)}

    def facts(self):
        """The facts milestones are tested against, read from the game."""
        items, entities = ms.wanted()
        r = self.game.call("progress", {"items": items, "entities": entities})
        if not r.get("ok"):
            raise ToolError(r.get("error") or "the game's progress could not be read", r.get("hint"))
        f = r["result"]
        for key in ("researched", "platforms", "planets_reached"):       # an empty list arrives as an empty object
            if not isinstance(f.get(key), list):
                f[key] = []
        for key in ("produced", "built"):
            if not isinstance(f.get(key), dict):
                f[key] = {}
        return f

    def milestones(self):
        out = ms.summary(self.facts())
        if self.goal:
            out["standing_goal"] = self.goal.describe()
        return out

    def set_goal(self, kind, place=None, milestone=None, per_minute=None):
        goal = Goal(kind, {"place": place, "milestone": milestone, "science": per_minute}.get(kind))
        self.goal, self.goal_paused = goal, False
        return {"goal": goal.describe(), "note": "you will be asked to carry on by yourself until it is reached; say so to the player in one sentence"}

    def clear_goal(self):
        had = self.goal.describe() if self.goal else None
        self.goal, self.goal_paused = None, False
        return {"cleared": had is not None, "was": had}

    def build_plan(self, plan_id, dry_run=True, surface=None):
        plan = self.plans.get(plan_id)
        if not plan:
            raise ToolError("there is no plan with the id '%s'" % plan_id, "plans made so far: %s" % (", ".join(sorted(self.plans)) or "none"))
        if not dry_run and not plan["checked"]:
            raise ToolError("this plan has not passed a dry run yet", "call build_plan with dry_run true first and fix what it reports")
        args = {"entities": plan["entities"], "dry_run": bool(dry_run)}
        if surface:
            args["surface"] = surface
        r = self.game.call("build", args)
        if not r.get("ok"):
            raise ToolError(r.get("error") or "the game refused the build", r.get("hint"))
        result = r["result"]
        if dry_run:
            plan["checked"] = not result.get("failed") and not result.get("avatar_lacks")
        elif result.get("job"):                                       # the avatar builds it: wait for the walk and the placing
            last, state = self._wait(result["job"])
            plan["checked"] = False
            plan["built"] = bool(last.get("ok"))
            result = {"placed": last.get("placed") or 0, "of": last.get("of"), "executor": "avatar", "finished": bool(last.get("ok")),
                      "stopped_because": last.get("reason"), "stopped_at": last.get("stopped_at"), "avatar_carries": state.get("carries"),
                      "game_seconds": round((last.get("ticks") or 0) / 60.0, 1)}
        else:
            plan["checked"] = False                                   # built: the same plan cannot go down twice
            plan["built"] = True
        return dict(result, plan=plan["what"], dry_run=bool(dry_run))

    def _keep(self, entities, what):
        pid = "plan-%d" % self.next_id
        self.next_id += 1
        self.plans[pid] = {"entities": entities, "what": what, "checked": False}
        return pid
