"""
Steam power at the lake, poles to the base, and electric outputs for the furnaces.

Fluid connections, from the game's own prototypes, with a building's top-left at (x, y):
  boiler 3x2 facing N: water on the lower row at (x-1, y+1) and (x+3, y+1), steam out at (x+1, y-1)
  steam engine 3x5 facing N: ends at (x+1, y-1) and (x+1, y+5), so it stacks straight on a boiler

The boiler's fuel inserter is a burner inserter, so power can start from nothing.

Usage: scripts/build_power.py [--build]
"""

import json
import math
import sys

from _game import tools

from bridge.factorio.planner import E, N, S, W, Grid, Plan, batches, overlay
from build_smelting import COPPER_YS, IRON_XS

BOX = (-70, -95, 60, 60)
SCIENCE_WEST = -66


def pole(plan, x, y):
    plan.machine("small-electric-pole", x, y, 1, 1)


def pole_chain(plan, start, end, step=6.5):
    """Poles from start to end, within wire reach, nudged off anything in the way."""
    (x1, y1), (x2, y2) = start, end
    dist = math.hypot(x2 - x1, y2 - y1)
    count = max(1, math.ceil(dist / step))
    for i in range(1, count):
        x = round(x1 + (x2 - x1) * i / count)
        y = round(y1 + (y2 - y1) * i / count)
        for dx, dy in [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1)]:
            if (x + dx, y + dy) not in plan.taken and plan.grid.at(x + dx, y + dy) in ".TikcsR":
                pole(plan, x + dx, y + dy)
                break
        else:
            raise SystemExit(f"no room for a pole near {x},{y}")


def build_plan(grid):
    plan = Plan(grid)

    # Water, steam, engines.
    plan.entities.append({"name": "offshore-pump", "x": 28.5, "y": 51.5, "direction": S})
    plan.taken[(28, 51)] = "offshore-pump"
    plan.machine("pipe", 28, 50, 1, 1)
    plan.machine("pipe", 28, 49, 1, 1)
    plan.machine("boiler", 29, 48, 3, 2)
    plan.machine("steam-engine", 29, 43, 3, 5)
    plan.machine("steam-engine", 29, 38, 3, 5)

    # Coal: lifted off the ring's bottom belt, then all the way down to the boiler.
    plan.inserter(32, 48, E)
    plan.inserter(30, -58, N)
    plan.route((30, -57), S, (33, 48), S)

    # Poles to the base.
    pole(plan, 28, 40)
    pole(plan, -28, -55)
    pole_chain(plan, (28, 40), (-28, -55))
    pole(plan, -24, -55)
    pole(plan, -32, -55)
    pole(plan, -35, -55)
    pole(plan, -35, -60)
    pole(plan, -35, -66)
    pole(plan, -35, -72)
    pole(plan, -35, -77)
    pole(plan, -35, -82)

    # Electric outputs and plate belts.
    for x in IRON_XS:
        plan.machine("inserter", x, -57, 1, 1, direction=N)
    for y in COPPER_YS:
        plan.machine("inserter", -33, y, 1, 1, direction=E)
    plan.line((-34, COPPER_YS[0]), (-34, -57), (SCIENCE_WEST, -57), last_direction=W)
    plan.line((IRON_XS[-1] + 1, -56), (SCIENCE_WEST, -56), last_direction=W)
    return plan


def main():
    build = "--build" in sys.argv
    x1, y1, x2, y2 = BOX
    plan = build_plan(Grid(json.loads(tools["map_grid"](x1, y1, x2, y2))))
    counts = {}
    for e in plan.entities:
        counts[e["name"]] = counts.get(e["name"], 0) + 1
    print("plan:", counts)
    if not build:
        print(overlay(plan, 20, 36, 40, 53))
    for part in batches(plan.entities):
        r = json.loads(tools["place_entities"](json.dumps(part), dry_run=True))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"dry run failed, nothing built: {json.dumps(r)[:1500]}")
    print("dry run clean")
    if not build:
        return
    print(tools["save_game"]("before-power"))
    placed = 0
    for part in batches(plan.entities):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"build stopped after {placed}: {json.dumps(r)[:1500]}")
        placed += r["placed"]
    print("placed", placed)
    print(tools["seed_starter_fuel"](25, -60, 36, 52, drill_coal=1))
    print(tools["tell_player"]("Steam power going in at the lake, with poles and plate belts back to the base.", x=30, y=43))


if __name__ == "__main__":
    main()
