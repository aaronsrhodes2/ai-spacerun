"""
Smelting. Each smelter belt carries ore on one lane and coal on the other, so one
burner inserter per furnace brings both, and refuels itself whenever it carries coal.

  Iron:   the ore line carries on through the hub center onto row y=-61, under the
          copper line. Coal side-loads from the opposite side, so the lanes stay apart.
  Copper: drills fill only one lane. An inserter from the fuel trunk drops coal on the
          far lane at x=-50, and furnaces sit on the vertical at x=-29.

Stage 1 makes plates that stay in the furnaces, which is enough for the steam-power and
electronics triggers. Outputs need electric inserters, since a burner inserter carrying
only plates can never refuel. Those come with power.

Usage: scripts/build_smelting.py [--build]
"""

import json
import sys

from _game import tools

from bridge.factorio.planner import E, N, S, W, Grid, Plan, batches, overlay

IRON_XS = [-31, -29, -27, -25, -23]        # left column of each iron furnace, south of y=-61
COPPER_YS = [-84, -82, -80, -78, -76, -74]  # top row of each copper furnace, west of x=-29
BOX = (-80, -95, -5, -45)


def build_plan(grid):
    plan = Plan(grid)

    # Iron through the hub, coal in from the other side.
    plan.line((-20, -63), (-20, -62), last_direction=S)
    plan.line((-19, -62), (-19, -60), last_direction=W)
    plan.belt(-20, -60, N)
    plan.line((-20, -61), (-32, -61), last_direction=W)
    for x in IRON_XS:
        plan.inserter(x, -60, N)
        plan.machine("stone-furnace", x, -59, 2, 2)

    # Coal onto copper's free lane.
    plan.inserter(-50, -89, N)
    plan.belt(-50, -88, S)
    plan.inserter(-50, -87, N)
    for y in COPPER_YS:
        plan.inserter(-30, y, E)
        plan.machine("stone-furnace", -32, y, 2, 2)
    return plan


def main():
    build = "--build" in sys.argv
    if build:
        # Stone stops short so it can't feed the coal tile that replaces it.
        print("stone end trimmed:", tools["remove_entities"](-20.4, -60.4, -19.6, -58.6, names="transport-belt"))
    x1, y1, x2, y2 = BOX
    snap = json.loads(tools["map_grid"](x1, y1, x2, y2))
    if not build:
        # Treat the two stone tiles as already gone when only previewing.
        for y in (-60, -59):
            row = list(snap["rows"][y - y1])
            row[-20 - x1] = "."
            snap["rows"][y - y1] = "".join(row)
    plan = build_plan(Grid(snap))
    if not build:
        print(overlay(plan, -55, -92, -10, -50))
        return
    print(tools["save_game"]("before-smelting"))
    for part in batches(plan.entities):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"build stopped: {json.dumps(r)[:1500]}")
        print("placed", r["placed"])
    print(tools["seed_starter_fuel"](-55, -92, -18, -50))
    print(tools["tell_player"]("Smelting going in by the hub. Iron and copper plates will unlock steam power and electronics.", x=-27, y=-58))


if __name__ == "__main__":
    main()
