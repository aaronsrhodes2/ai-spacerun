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


def place(entities, build, label):
    counts = {}
    for e in entities:
        counts[e["name"]] = counts.get(e["name"], 0) + 1
    print(label, "plan:", counts)
    for part in batches(entities):
        r = json.loads(tools["place_entities"](json.dumps(part), dry_run=True))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"{label} dry run failed, nothing built: {json.dumps(r)[:1800]}")
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

if __name__ == "__main__":
    STAGES[sys.argv[1]]("--build" in sys.argv)
