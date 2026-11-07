"""
Second power plant: 3 boilers and 6 steam engines (5.4 MW) east of the lake, on a
coal branch split off the main boiler line.

    splitter at (33..34, 20) on the boiler line (x=33, flowing south)
    coal belt  y=21, east from x=34 to x=47
    inserters  y=20 under each boiler (burner, so power can restart from cold)
    boilers    y=18..19 at x=37, 41, 45 (north-facing), 1-tile pipe gaps between
    engines    two per boiler stacked north: y=13..17 and y=8..12
    poles      medium, in the gap columns x=40 and 44, linked to the grid by a
               line down x=40 to the pole at (35,44)
    water      offshore pump at (40,55) facing west, pipe east to x=48, north
               along x=48 to the east end of the boiler row

Usage: scripts/build_plant2.py [--build]
"""

import json
import sys

from _game import tools

from bridge.factorio.planner import E, N, S, W, Grid, Plan, batches

BOX = (30, 6, 52, 58)
BOILER_XS = [37, 41, 45]
PUMP = (40, 55)


def build_plan(plan):
    # Coal branch.
    plan.machine("splitter", 33, 20, 2, 1, direction=S)
    plan.line((34, 21), (47, 21), last_direction=E)
    for x in BOILER_XS:
        plan.machine("burner-inserter", x + 1, 20, 1, 1, direction=S)
        plan.machine("boiler", x, 18, 3, 2)
        plan.machine("steam-engine", x, 13, 3, 5)
        plan.machine("steam-engine", x, 8, 3, 5)
    # Water between boilers, and from the pump.
    plan.machine("pipe", 40, 19, 1, 1)
    plan.machine("pipe", 44, 19, 1, 1)
    plan.entities.append({"name": "offshore-pump", "x": PUMP[0] + 0.5, "y": PUMP[1] + 0.5, "direction": W})
    plan.taken[PUMP] = "offshore-pump"
    for x in range(41, 49):
        plan.machine("pipe", x, 55, 1, 1)
    for y in range(54, 18, -1):
        plan.machine("pipe", 48, y, 1, 1)
    # Poles: in the gaps between engine stacks, and a line back to the grid.
    for y in (15, 10):
        for x in (40, 44):
            plan.machine("medium-electric-pole", x, y, 1, 1)
    for y in (42, 34, 27, 22):
        plan.machine("medium-electric-pole", 40, y, 1, 1)


def main():
    build = "--build" in sys.argv
    snap = json.loads(tools["map_grid"](*BOX))
    # the main belt tile that the splitter replaces
    row = list(snap["rows"][20 - BOX[1]])
    row[33 - BOX[0]] = "."
    snap["rows"][20 - BOX[1]] = "".join(row)
    plan = Plan(Grid(snap))
    build_plan(plan)
    counts = {}
    for e in plan.entities:
        counts[e["name"]] = counts.get(e["name"], 0) + 1
    print("plan:", counts)
    for part in batches(plan.entities):
        r = json.loads(tools["place_entities"](json.dumps(part), dry_run=True))
        if r.get("error"):
            raise SystemExit(f"dry run error: {r}")
        real = [f for f in r["failed"] if not (f["x"] == 34.0 and f["y"] == 20.5)] if isinstance(r["failed"], list) else []
        if real:
            raise SystemExit(f"dry run failed, nothing built: {json.dumps(real)[:1500]}")
    print("dry run clean")
    if not build:
        return
    print(tools["save_game"]("before-plant2"))
    print("old belt tile:", tools["remove_entities"](33.3, 20.3, 33.7, 20.7, names="transport-belt"))
    placed = 0
    for part in batches(plan.entities):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"build stopped after {placed}: {json.dumps(r)[:1500]}")
        placed += r["placed"]
    print("placed", placed)
    print("fuel:", tools["seed_starter_fuel"](36, 18, 48, 22))


if __name__ == "__main__":
    main()
