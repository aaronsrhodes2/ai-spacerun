"""
Feed belts from the refinery site to the blue block's N belts, and the finished-pack belt
to the labs.

Lane rule used throughout: an inserter drops on the FAR lane of a belt; a lane is left or
right of the direction of travel and stays that way through turns. N1/N2 flow west, where
the south lane is the left lane, so each feed must be loaded onto its LEFT lane: stand the
loading inserter on the belt's right side.

    plastic   chest (-147,-121) -> inserter (-147,-122) -> belt y=-123 flowing east (inserter
              south of the belt = right side = loads the left lane) -> routed to (-214,-64),
              which points south into N1's first tile (-214,-63).

Stages: plastic | sulfur | packs     Usage: scripts/build_feeds.py <stage> [--build]
"""
import json
import sys

from _game import tools

from bridge.factorio.planner import E, N, S, W, Grid, Plan, PlanError, batches


def lua(code):
    return tools["run_lua"](" ".join(code.splitlines()))


def place(entities, build, label, ignore=()):
    counts = {}
    for e in entities:
        counts[e["name"]] = counts.get(e["name"], 0) + 1
    print(label, "plan:", counts)
    for part in batches(entities):
        r = json.loads(tools["place_entities"](json.dumps(part), dry_run=True))
        failed = [f for f in (r["failed"] if isinstance(r["failed"], list) else []) if (f["x"], f["y"]) not in set(ignore)]
        if r.get("error") or failed:
            raise SystemExit(f"{label} dry run failed, nothing built: {json.dumps(failed or r)[:1800]}")
    print(label, "dry run clean")
    if not build:
        return
    placed = 0
    for part in batches(entities):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"{label} stopped after {placed}: {json.dumps(r)[:1800]}")
        placed += r["placed"]
    print(label, "placed", placed)


def plastic_stage(build):
    box = (-230, -130, -136, -60)
    plan = Plan(Grid(json.loads(tools["map_grid"](*box))))
    plan.machine("inserter", -147, -122, 1, 1, direction=S)
    plan.machine("small-electric-pole", -148, -122, 1, 1)
    plan.belt(-147, -123, E)
    try:
        path = plan.route((-146, -123), E, (-214, -64), S)
    except PlanError as e:
        raise SystemExit(f"plastic route failed: {e}")
    print("plastic belt:", len(path) + 1, "tiles")
    place(plan.entities, build, "plastic")
    if build:
        print(tools["place_entities"](json.dumps([{"name": "small-electric-pole", "x": -347.5, "y": -64.5}]))[:200])


STAGES = {"plastic": plastic_stage}


def packs_stage(build):
    """Blue pack belt: y=-70 runs east to x=-217, turns north up x=-216 to y=-78, then one
    underground (-215,-78) -> (-210,-78) passes under the sulfur belt (x=-214) and the plastic
    belt (x=-211), and the belt runs along y=-78 to the labs, where long inserters on the third
    lab row take packs from it; a chest at the end stockpiles the rest."""
    box = (-360, -92, -36, -58)
    plan = Plan(Grid(json.loads(tools["map_grid"](*box))))
    if build:
        print("old end:", tools["remove_entities"](-216.4, -70.4, -211.6, -69.6, names="transport-belt"))
    g = plan.grid
    rows = list(g.rows)
    for x in range(-216, -211):                  # these tiles are about to be cleared of the old belt end
        row = list(rows[-70 - g.y1]); row[x - g.x1] = "."; rows[-70 - g.y1] = "".join(row)
    g.rows = rows
    for y in range(-70, -78, -1):
        plan.belt(-216, y, N)
    plan.belt(-216, -78, E)
    plan.entities.append({"name": "underground-belt", "x": -214.5, "y": -77.5, "direction": E, "params": {"type": "input"}})
    plan.taken[(-215, -78)] = "underground"
    plan.entities.append({"name": "underground-belt", "x": -209.5, "y": -77.5, "direction": E, "params": {"type": "output"}})
    plan.taken[(-210, -78)] = "underground"
    plan.line((-209, -78), (-44, -78), last_direction=E)
    lab_cols = [-66, -62, -58, -54, -50, -46, -70, -74, -78]
    for x in lab_cols:
        plan.machine("long-handed-inserter", x + 2, -76, 1, 1, direction=N)
    plan.machine("inserter", -43, -78, 1, 1, direction=W)
    plan.machine("iron-chest", -42, -78, 1, 1)
    plan.machine("small-electric-pole", -43, -79, 1, 1)
    place(plan.entities, build, "blue pack belt", ignore=[(-216.0 + 0.5, -69.5)])


STAGES["packs"] = packs_stage


if __name__ == "__main__":
    STAGES[sys.argv[1]]("--build" in sys.argv)
