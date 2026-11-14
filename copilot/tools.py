"""Planning tools the bridge adds to the mod's own: the arithmetic and geometry a small model gets wrong. Each one reads
its facts from the game through the mod (never from memory), plans in code, and hands back a short result. Nothing is
built by planning: a plan gets an id, and `build_plan` sends it to the game, as a dry run unless told otherwise.

The model sees these beside the mod's tools, in the same shape, and cannot tell the difference."""
from .plan import calc, cells, route
from .plan.layout import Layout, LayoutError

FACING = {"north": 0, "east": 1, "south": 2, "west": 3}            # quarter turns from the cell's own facing (inputs north)
MAX_ROUTE_WINDOW = 100


def _param(type_, description, required=False, default=None):
    return {"type": type_, "required": required, "default": default, "description": description}


SPECS = [
    {"name": "plan_production",
     "description": "Work out everything needed to make an item at a rate: for each recipe in the chain how many machines, and the raw inputs and belts needed. Reads recipes and machine speeds from the game. Use it before building any production line; never work these numbers out yourself.",
     "parameters": {"item": _param("string", "internal name of the item to make", True),
                    "per_minute": _param("number", "how many per minute", True),
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

UNDERGROUND = {"transport-belt": "underground-belt", "fast-transport-belt": "fast-underground-belt",
               "express-transport-belt": "express-underground-belt", "turbo-transport-belt": "turbo-underground-belt", "pipe": "pipe-to-ground"}


class ToolError(Exception):
    def __init__(self, error, hint=None):
        super().__init__(error)
        self.error, self.hint = error, hint


class LocalTools:
    def __init__(self, game):
        self.game = game
        self.plans = {}
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
        except (calc.PlanError, LayoutError) as e:                 # RouteError is a LayoutError
            return {"ok": False, "error": str(e)}

    def plan_production(self, item, per_minute, machine=None, stop_at=None):
        if per_minute <= 0:
            raise ToolError("per_minute must be above zero")
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
        return {"item": item, "per_minute": per_minute, "steps": steps, "supplied_per_minute": raw,
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
            plan["checked"] = not result.get("failed")
        else:
            plan["checked"] = False                                   # built: the same plan cannot go down twice
            plan["built"] = True
        return dict(result, plan=plan["what"], dry_run=bool(dry_run))

    def _keep(self, entities, what):
        pid = "plan-%d" % self.next_id
        self.next_id += 1
        self.plans[pid] = {"entities": entities, "what": what, "checked": False}
        return pid
