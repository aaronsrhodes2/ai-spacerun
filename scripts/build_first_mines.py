"""
First order: iron, copper, coal and stone by belt to one hub, with every burner
machine fed coal by belt. Nothing but burner tech, belts and no undergrounds, so the
layout has to work without any belt crossing:

    iron from the north, coal from the east, copper from the west, stone from the south.

  - Coal band: a ring of two belts. Drills take turns outputting to one and being fed
    from the other. An inserter lifts the hub's coal off the top belt, and the rest
    carries on as the fuel trunk.
  - The fuel trunk runs north of the coal spoke, along the iron row, then the copper row.
  - The stone row's fuel is lifted off the coal spoke by one burner inserter.

Usage: scripts/build_first_mines.py            prints the plan and dry-runs it
       scripts/build_first_mines.py --build    saves first, then builds
"""

import json
import sys

from _game import tools

from bridge.factorio.planner import E, N, S, W, Grid, Plan, batches, overlay

HUB = (-20, -62)
BOX = (-105, -135, 50, -30)
IRON_DRILLS, COPPER_DRILLS, STONE_DRILLS, COAL_PAIRS = 10, 8, 5, 4


def pure_columns(grid, ore, y, xs, want):
    """Left columns from xs where a drill at row y is fully on `ore`, up to `want`."""
    found = [x for x in xs if grid.all_ore(ore, x, y)]
    if len(found) < want:
        raise SystemExit(f"only {len(found)} clean drill spots for '{ore}' at y={y}, wanted {want}")
    return sorted(found[:want])


def coal_band(plan, grid):
    top, bottom = -63, -59
    xs = [x for x in range(18, 40, 4)
          if grid.all_ore("k", x, top + 1) and grid.all_ore("k", x + 2, top + 2)][:COAL_PAIRS]
    if len(xs) < COAL_PAIRS:
        raise SystemExit(f"only {len(xs)} coal pairs fit")
    # A ring, so no drill's fuel depends on a drop downstream of it. The bottom belt
    # flows east and loops into the head of the top belt, which flows west. The first
    # top-row drill is left out: nothing would be upstream of its inserter.
    for x in xs:
        if x != xs[0]:
            plan.drill(x, top + 1, N, "k")   # outputs to the top belt, fed from the bottom
            plan.inserter(x, top + 3, S)
        plan.drill(x + 2, top + 2, S, "k")   # outputs to the bottom belt, fed from the top
        plan.inserter(x + 2, top + 1, N)
    east = xs[-1] + 4
    plan.line((xs[0] + 2, bottom), (east, bottom), (east, top), (18, top), last_direction=W)
    # The hub's coal is lifted off the top belt, the rest carries on as the fuel trunk.
    plan.inserter(16, top + 1, N)
    plan.line((16, top + 2), (16, bottom - 1), last_direction=S)


def hub(plan):
    x, y = HUB
    plan.reserve(x - 1, y - 1, x + 1, y + 1, "hub")


def coal_spoke(plan):
    plan.line((16, -59), (1, -59), last_direction=W)
    plan.route((0, -59), W, (HUB[0] + 2, HUB[1]), W)


def stone_row(plan, grid):
    fuel_y, inserter_y, drill_y, out_y = -54, -53, -52, -50
    xs = pure_columns(grid, "s", drill_y, range(12, 30, 2), STONE_DRILLS)
    plan.inserter(9, -58, N)                  # coal spoke at (9,-59) into the stone fuel line
    plan.line((9, -57), (9, fuel_y), (xs[-1], fuel_y), last_direction=E)
    for x in xs:
        plan.inserter(x, inserter_y, N)
        plan.drill(x, drill_y, S, "s")
    plan.line((xs[-1] + 1, out_y), (10, out_y), last_direction=W)
    plan.route((9, out_y), W, (HUB[0], HUB[1] + 2), N)


def iron_row(plan, grid):
    fuel_y, inserter_y, drill_y, out_y = -108, -107, -106, -104
    xs = pure_columns(grid, "i", drill_y, range(-32, -10, 2), IRON_DRILLS)
    spoke_x = HUB[0]
    plan.line((xs[-1] + 1, fuel_y), (-33, fuel_y), last_direction=W)
    for x in xs:
        plan.inserter(x, inserter_y, N)
        plan.drill(x, drill_y, S, "i")
    plan.line((xs[-1] + 1, out_y), (spoke_x + 1, out_y), last_direction=W)
    plan.line((xs[0] + 1, out_y), (spoke_x - 1, out_y), last_direction=E)
    plan.line((spoke_x, out_y), (spoke_x, HUB[1] - 2), last_direction=S)
    return (xs[-1] + 2, fuel_y)


def copper_row(plan, grid):
    fuel_y, inserter_y, drill_y, out_y = -90, -89, -88, -86
    xs = pure_columns(grid, "c", drill_y, range(-58, -76, -2), COPPER_DRILLS)
    plan.line((xs[-1] + 2, fuel_y), (xs[0], fuel_y), last_direction=W)
    for x in xs:
        plan.inserter(x, inserter_y, N)
        plan.drill(x, drill_y, S, "c")
    plan.line((xs[0] + 1, out_y), (xs[-1] + 3, out_y), last_direction=E)
    plan.route((xs[-1] + 4, out_y), E, (HUB[0] - 2, HUB[1]), E)
    return (xs[-1] + 3, fuel_y)


def build_plan(grid):
    plan = Plan(grid)
    hub(plan)
    coal_band(plan, grid)
    coal_spoke(plan)
    stone_row(plan, grid)
    iron_join = iron_row(plan, grid)
    copper_join = copper_row(plan, grid)
    plan.route((17, -63), W, iron_join, W)      # trunk: coal band to the iron row
    plan.route((-34, -108), W, copper_join, W)  # trunk continues to the copper row
    return plan


def main():
    build = "--build" in sys.argv
    x1, y1, x2, y2 = BOX
    snap = json.loads(tools["map_grid"](x1, y1, x2, y2))
    if "error" in snap:
        raise SystemExit(snap)
    plan = build_plan(Grid(snap))
    counts = {}
    for e in plan.entities:
        counts[e["name"]] = counts.get(e["name"], 0) + 1
    print("plan:", counts)
    if not build:
        print(overlay(plan, -80, -112, 42, -44))

    parts = batches(plan.entities)
    for part in parts:
        r = json.loads(tools["place_entities"](json.dumps(part), dry_run=True))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"dry run failed, nothing built: {json.dumps(r)[:1500]}")
    print("dry run clean")
    if not build:
        return

    print(tools["save_game"]("before-first-mines"))
    placed = 0
    for part in parts:
        r = json.loads(tools["place_entities"](json.dumps(part)))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"build stopped after {placed} placed: {json.dumps(r)[:1500]}")
        placed += r["placed"]
    print("placed", placed)


if __name__ == "__main__":
    main()
