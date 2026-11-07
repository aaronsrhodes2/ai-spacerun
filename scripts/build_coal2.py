"""
Electric coal field feeding the boiler line directly.

    y=-67..-65  five electric drills (x=16..30, 3 wide each) facing south
    y=-64       belt east from x=16 to x=36, south down x=37 to y=-52, then west
                along y=-51 into the boiler line's corner at (33,-51) as a side-load
    poles       medium, above the drills (y=-68), linked via (38,-58) to the pole
                at (29,-57)

Usage: scripts/build_coal2.py [--build]
"""
import json
import sys

from _game import tools

from bridge.factorio.planner import E, N, S, W, Grid, Plan, batches

BOX = (14, -72, 42, -46)
X0S = [16, 19, 22, 25, 28]


def build_plan(plan):
    for x in X0S:
        plan.machine("electric-mining-drill", x, -67, 3, 3, direction=S)
    plan.line((16, -64), (36, -64), (37, -64), (37, -52), last_direction=S)
    plan.line((37, -51), (34, -51), last_direction=W)
    for x in (18, 24, 30):
        plan.machine("medium-electric-pole", x, -68, 1, 1)
    plan.machine("medium-electric-pole", 38, -64, 1, 1)
    plan.machine("medium-electric-pole", 38, -58, 1, 1)


def main():
    build = "--build" in sys.argv
    if build:
        print("stray belt:", tools["remove_entities"](34.3, -64.7, 34.7, -64.3, names="transport-belt"))
    snap = json.loads(tools["map_grid"](*BOX))
    row = list(snap["rows"][-65 - BOX[1]])
    row[34 - BOX[0]] = "."
    snap["rows"][-65 - BOX[1]] = "".join(row)
    plan = Plan(Grid(snap))
    build_plan(plan)
    ore = 0
    for x in X0S:
        n = sum(1 for dx in range(-1, 4) for dy in range(-68, -63) if plan.grid.at(x + dx, dy) == "k")
        ore += n
        print("drill at", x, "covers", n, "coal tiles")
    counts = {}
    for e in plan.entities:
        counts[e["name"]] = counts.get(e["name"], 0) + 1
    print("plan:", counts)
    for part in batches(plan.entities):
        r = json.loads(tools["place_entities"](json.dumps(part), dry_run=True))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"dry run failed, nothing built: {json.dumps(r)[:1500]}")
    print("dry run clean")
    if not build:
        return
    placed = 0
    for part in batches(plan.entities):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"build stopped after {placed}: {json.dumps(r)[:1500]}")
        placed += r["placed"]
    print("placed", placed)


if __name__ == "__main__":
    main()
