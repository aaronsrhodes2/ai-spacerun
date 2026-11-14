"""The milestone list: a fixed road from the first iron plate to the edge of the solar system, each step with a test code
can run against facts the mod reports (its `progress` tool). The model is told what comes next; the harness uses the same
list to see whether a run is moving or stalled. Nothing here says HOW to reach a milestone: that is the model's work.

A test is a dict; every key in it must hold:
  produced    {item: at least this many ever made}
  researched  [technology, ...] all researched
  built       {building: at least this many standing}
  launched    at least this many rockets launched
  platforms   at least this many space platforms
  reached     [planet, ...] each has something of ours on its surface
  platform_at a space location with a platform at it
  won         the game reports the win

The order is the order a game is normally played in. A milestone counts as done whenever its test holds, in any order.

Each milestone belongs to a place: a planet, "space" (the first platform), "edge" (the run to the win) or "beyond". "Solve
Nauvis" means every milestone of that place."""

PLACES = ("nauvis", "space", "vulcanus", "fulgora", "gleba", "aquilo", "edge", "beyond")


def of_place(place, milestones=None):
    """The milestones that belong to a place, in order."""
    return [m for m in (milestones or MILESTONES) if m.get("place") == place]

MILESTONES = [
    # ---- Nauvis: by hand, then machines
    {"id": "first-plates", "place": "nauvis", "title": "Smelt the first iron and copper plates", "test": {"produced": {"iron-plate": 50, "copper-plate": 10}},
     "hint": "mine ore and coal by hand, place stone furnaces"},
    {"id": "power", "place": "nauvis", "title": "Make electricity", "test": {"researched": ["steam-power"], "built": {"steam-engine": 1}},
     "hint": "an offshore pump, a boiler and a steam engine by water, burning coal"},
    {"id": "first-machines", "place": "nauvis", "title": "Automate mining and assembling", "test": {"researched": ["automation"], "built": {"electric-mining-drill": 2, "assembling-machine-1": 2}},
     "hint": "drills on ore feeding furnaces; assemblers for gears and science"},
    {"id": "red-science", "place": "nauvis", "title": "Research with red science", "test": {"produced": {"automation-science-pack": 20}, "built": {"lab": 1}},
     "hint": "automation science packs into a lab"},
    {"id": "green-science", "place": "nauvis", "title": "Make green science", "test": {"researched": ["logistic-science-pack"], "produced": {"logistic-science-pack": 20}},
     "hint": "inserters and belts made by machines, then logistic science packs"},
    {"id": "steel", "place": "nauvis", "title": "Make steel", "test": {"researched": ["steel-processing"], "produced": {"steel-plate": 50}},
     "hint": "furnaces fed with iron plates"},
    {"id": "oil", "place": "nauvis", "title": "Process oil into plastic", "test": {"researched": ["oil-processing", "plastics"], "produced": {"plastic-bar": 50}},
     "hint": "pumpjacks, a refinery, a chemical plant"},
    {"id": "blue-science", "place": "nauvis", "title": "Make blue science", "test": {"researched": ["chemical-science-pack"], "produced": {"chemical-science-pack": 20}},
     "hint": "engines, red circuits and sulfur"},
    {"id": "robots", "place": "nauvis", "title": "Get robots building and carrying", "test": {"researched": ["construction-robotics", "logistic-robotics"], "built": {"roboport": 1}},
     "hint": "roboports and robots; from here plans can be built as ghosts"},
    {"id": "rocket-silo", "place": "nauvis", "title": "Build a rocket silo", "test": {"researched": ["rocket-silo"], "built": {"rocket-silo": 1}},
     "hint": "the silo's three rocket ingredients are each a large line"},
    {"id": "first-rocket", "place": "nauvis", "title": "Launch a rocket", "test": {"launched": 1}, "hint": "fill the silo with rocket parts"},
    # ---- space
    {"id": "platform", "place": "space", "title": "Put a platform in orbit", "test": {"researched": ["space-platform"], "platforms": 1},
     "hint": "launch a platform starter pack, then build the platform out"},
    {"id": "space-science", "place": "space", "title": "Make space science on a platform", "test": {"researched": ["space-science-pack"], "produced": {"space-science-pack": 20}},
     "hint": "asteroid collectors, crushers and assemblers on the platform"},
    # ---- the inner planets, in any order
    {"id": "vulcanus", "place": "vulcanus", "title": "Land on Vulcanus and make metallurgic science", "test": {"researched": ["planet-discovery-vulcanus"], "reached": ["vulcanus"], "produced": {"metallurgic-science-pack": 20}},
     "hint": "lava and calcite give metal in foundries; tungsten needs big mining drills"},
    {"id": "fulgora", "place": "fulgora", "title": "Land on Fulgora and make electromagnetic science", "test": {"researched": ["planet-discovery-fulgora"], "reached": ["fulgora"], "produced": {"electromagnetic-science-pack": 20}},
     "hint": "everything comes from recycling scrap; lightning gives power and needs rods"},
    {"id": "gleba", "place": "gleba", "title": "Land on Gleba and make agricultural science", "test": {"researched": ["planet-discovery-gleba"], "reached": ["gleba"], "produced": {"agricultural-science-pack": 20}},
     "hint": "everything spoils: build so nothing sits still, and research where the packs are made"},
    # ---- the outer system
    {"id": "aquilo", "place": "aquilo", "title": "Land on Aquilo and make cryogenic science", "test": {"researched": ["planet-discovery-aquilo"], "reached": ["aquilo"], "produced": {"cryogenic-science-pack": 20}},
     "hint": "everything freezes without heat pipes; the ship there must break big asteroids with rockets"},
    {"id": "railgun-and-fusion", "place": "edge", "title": "Research railguns and fusion power", "test": {"researched": ["railgun", "fusion-reactor"]},
     "hint": "both need cryogenic science and quantum processors"},
    {"id": "edge", "place": "edge", "title": "Reach the edge of the solar system", "test": {"platform_at": "solar-system-edge"},
     "hint": "a ship with railguns for the huge asteroids past Aquilo"},
    {"id": "won", "place": "edge", "title": "The game is won", "test": {"won": True}, "hint": "arriving at the edge is the win"},
    # ---- beyond the win
    {"id": "promethium", "place": "beyond", "title": "Make promethium science beyond the edge", "test": {"researched": ["promethium-science-pack"], "produced": {"promethium-science-pack": 1}},
     "hint": "promethium asteroids lie past the edge; the science is made on the ship"},
]


def wanted(milestones=MILESTONES):
    """The items and buildings the mod must count for these milestones."""
    items, entities = set(), set()
    for m in milestones:
        items.update(m["test"].get("produced") or {})
        entities.update(m["test"].get("built") or {})
    return sorted(items), sorted(entities)


def missing(test, facts):
    """What a milestone's test still lacks, as short phrases; empty when it holds."""
    out = []
    produced, built = facts.get("produced") or {}, facts.get("built") or {}
    researched = set(facts.get("researched") or [])
    for item, n in (test.get("produced") or {}).items():
        have = produced.get(item) or 0
        if have < n:
            out.append("%d more %s made (%d of %d)" % (n - have, item, have, n))
    for tech in test.get("researched") or []:
        if tech not in researched:
            out.append("research %s" % tech)
    for name, n in (test.get("built") or {}).items():
        have = built.get(name) or 0
        if have < n:
            out.append("%d more %s built (%d of %d)" % (n - have, name, have, n))
    if (facts.get("rockets_launched") or 0) < (test.get("launched") or 0):
        out.append("launch a rocket")
    platforms = facts.get("platforms") or []
    if len(platforms) < (test.get("platforms") or 0):
        out.append("a space platform")
    for planet in test.get("reached") or []:
        if planet not in (facts.get("planets_reached") or []):
            out.append("something of ours on %s" % planet)
    if test.get("platform_at") and not any(p.get("at") == test["platform_at"] for p in platforms):
        out.append("a platform at %s" % test["platform_at"])
    if test.get("won") and not facts.get("won"):
        out.append("the game's win")
    return out


def evaluate(facts, milestones=MILESTONES):
    """Every milestone with whether it is done and what it lacks."""
    return [{"id": m["id"], "title": m["title"], "hint": m.get("hint"), "missing": missing(m["test"], facts)} for m in milestones]


def summary(facts, milestones=MILESTONES, ahead=2):
    """What the model is told: how far the game is, the next milestone not yet done with what it lacks, and a look ahead."""
    state = evaluate(facts, milestones)
    for s in state:
        s["done"] = not s["missing"]
    done = [s["id"] for s in state if s["done"]]
    todo = [s for s in state if not s["done"]]
    nxt = todo[:1 + ahead]
    return {"done": len(done), "of": len(state), "done_ids": done, "won": bool(facts.get("won")),
            "next": [{"id": s["id"], "goal": s["title"], "still_needs": s["missing"], "hint": s["hint"]} for s in nxt[:1]],
            "after_that": [s["title"] for s in nxt[1:]],
            "hours_played": facts.get("hours_played")}


class Watch:
    """Notices a stall: no new milestone and no growth in what the next milestone counts, for too long in game time.
    Feed it the facts now and then; it answers with None or a sentence for the log."""

    def __init__(self, patience_hours=2.0, milestones=MILESTONES):
        self.patience, self.milestones = patience_hours, milestones
        self.mark = None                    # (done count, progress measure) at the last sign of life
        self.mark_hours = None

    @staticmethod
    def _measure(facts, milestones):
        """A number that grows whenever the game moves toward any milestone: counts toward tests, capped at each target."""
        total = 0.0
        produced, built = facts.get("produced") or {}, facts.get("built") or {}
        for m in milestones:
            t = m["test"]
            for item, n in (t.get("produced") or {}).items():
                total += min(produced.get(item) or 0, n) / n
            for name, n in (t.get("built") or {}).items():
                total += min(built.get(name) or 0, n) / n
        total += len(facts.get("researched") or [])
        total += min(facts.get("rockets_launched") or 0, 1)
        total += len(facts.get("planets_reached") or [])
        return total

    def check(self, facts):
        hours = facts.get("hours_played") or 0.0
        state = (sum(1 for s in evaluate(facts, self.milestones) if not s["missing"]), self._measure(facts, self.milestones))
        if self.mark is None or state[0] > self.mark[0] or state[1] > self.mark[1] + 1e-9:
            self.mark, self.mark_hours = state, hours
            return None
        idle = hours - self.mark_hours
        if idle >= self.patience:
            return "stalled: nothing counted toward any milestone for %.1f game hours" % idle
        return None
