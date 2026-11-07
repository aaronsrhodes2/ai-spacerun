"""
Second iron smelter: 12 stone furnaces along the ore spoke (x=-20, flows south),
fed by electric inserters. The hub's 5 furnaces were the limit, not the drills.

    x=-25  plate belt, south, west under the copper ore line at x=-29, then down x=-33
           to side-load the science iron belt at (-33,-56) from the north
    x=-24  output inserters
    x=-23..-22  furnaces, one every 3 rows, a pole in each gap row at x=-22
    x=-21  ore inserter (row y) and long-handed coal inserter (row y+1)
    x=-20  the ore spoke, both lanes ore
    x=-19  coal column, south, tapped off the fuel trunk at (-12,-108) and ending
           into the hub's coal path at (-19,-62)

Usage: scripts/build_iron2.py [--build]
"""

import json
import sys

from _game import tools

from bridge.factorio.planner import E, N, S, W, Grid, Plan, batches

FURNACE_YS = [-100 + 3 * k for k in range(12)]   # top rows: -100 .. -67
BOX = (-45, -112, -5, -50)


def build_plan(plan):
    # Coal tap: inserter lifts coal off the trunk, belt down x=-12, west on y=-102, down x=-19.
    plan.machine("inserter", -12, -107, 1, 1, direction=N)
    plan.line((-12, -106), (-12, -102), (-19, -102), (-19, -63), last_direction=S)
    plan.machine("small-electric-pole", -11, -107, 1, 1)
    plan.machine("small-electric-pole", -11, -101, 1, 1)

    for y in FURNACE_YS:
        plan.machine("stone-furnace", -23, y, 2, 2)
        plan.machine("inserter", -21, y, 1, 1, direction=E)
        plan.machine("long-handed-inserter", -21, y + 1, 1, 1, direction=E)
        plan.machine("inserter", -24, y, 1, 1, direction=E)
        plan.machine("small-electric-pole", -22, y + 2, 1, 1)

    # Plate belt: down, round the hub smelter to the west, under the plate belts, east, up.
    plan.line((-25, -100), (-25, -64), (-27, -64), last_direction=W)
    plan.entities.append({"name": "underground-belt", "x": -27.5, "y": -63.5, "direction": W, "params": {"type": "input"}})
    plan.taken[(-28, -64)] = "underground"
    plan.entities.append({"name": "underground-belt", "x": -29.5, "y": -63.5, "direction": W, "params": {"type": "output"}})
    plan.taken[(-30, -64)] = "underground"
    plan.line((-31, -64), (-33, -64), (-33, -57), last_direction=S)   # side-loads the iron belt at (-33, -56)


def main():
    build = "--build" in sys.argv
    snap = json.loads(tools["map_grid"](*BOX))
    plan = Plan(Grid(snap))
    build_plan(plan)
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
