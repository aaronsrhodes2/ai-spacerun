"""
Water for sulfur: offshore pump on the lake's west shore, an underground pipeline round the
base, and a sulfur plant beside the plastic plant.

    pump     offshore pump (-10,53) facing south, first pipe (-10,52)
    leg A    west along y=52 to x=-217, corner pipe (-218,52)
    leg B    north along x=-218 to y=-115, corner pipe (-218,-116)
    leg C    east along y=-116 to (-170,-116), plain pipes (-169,-116),(-168,-116)
    plant    chemical plant top-left (-168,-119), facing S, recipe sulfur. Its south inputs
             are (-168,-116) and (-166,-116): water arrives at the west one, petroleum gas
             comes underground west from the refinery's gas row to (-166,-116). The tile
             (-167,-116) stays empty so the two never join. (Which input takes which fluid
             is checked in game; swap if the plant reports a missing fluid.)
    output   inserter (-167,-120) onto a belt that loads the LEFT lane and runs to N2.

Stages: water | sulfur       Usage: scripts/build_water.py <stage> [--build]
"""
import json
import sys

from _game import tools

from bridge.factorio.planner import E, N, S, W, Grid, Plan, PlanError, batches, underground_run
from build_feeds import place


def grid(x1, y1, x2, y2):
    return Grid(json.loads(tools["map_grid"](x1, y1, x2, y2)))


def pipe(plan, x, y):
    plan.machine("pipe", x, y, 1, 1)


def water_stage(build):
    a = Plan(grid(-224, 46, -4, 60))
    a.entities.append({"name": "offshore-pump", "x": -9.5, "y": 53.5, "direction": S})
    a.taken[(-10, 53)] = "offshore-pump"
    pipe(a, -10, 52)
    underground_run(a, (-11, 52), (-217, 52))
    pipe(a, -218, 52)
    b = Plan(grid(-226, -122, -210, 56))
    underground_run(b, (-218, 51), (-218, -115))
    pipe(b, -218, -116)
    c = Plan(grid(-224, -124, -150, -108))
    underground_run(c, (-217, -116), (-170, -116))
    pipe(c, -169, -116)
    pipe(c, -168, -116)            # the plant's west input tile
    place(a.entities + b.entities + c.entities, build, "water")


def sulfur_stage(build):
    plan = Plan(grid(-232, -135, -136, -60))
    plan.machine("chemical-plant", -168, -119, 3, 3, direction=S, recipe="sulfur")
    underground_run(plan, (-149, -116), (-165, -116))      # gas, west from the refinery's gas row
    plan.machine("pipe", -166, -116, 1, 1)                 # the plant's east input tile
    plan.machine("inserter", -167, -120, 1, 1, direction=S)
    plan.machine("medium-electric-pole", -164, -118, 1, 1)
    plan.machine("medium-electric-pole", -163, -113, 1, 1)
    plan.belt(-167, -121, E)
    try:
        path = plan.route((-166, -121), E, (-215, -73), S)
    except PlanError as e:
        raise SystemExit(f"sulfur route failed: {e}")
    # the finished-pack belt (y=-70) is in the way: go under it, then finish into N2 at (-215,-64)
    plan.entities.append({"name": "underground-belt", "x": -214.5, "y": -71.5, "direction": S, "params": {"type": "input"}})
    plan.taken[(-215, -72)] = "underground"
    plan.entities.append({"name": "underground-belt", "x": -214.5, "y": -67.5, "direction": S, "params": {"type": "output"}})
    plan.taken[(-215, -68)] = "underground"
    for y in (-67, -66, -65):
        plan.belt(-215, y, S)
    print("sulfur belt:", len(path) + 1, "tiles + crossing")
    place(plan.entities, build, "sulfur")


STAGES = {"water": water_stage, "sulfur": sulfur_stage}

if __name__ == "__main__":
    STAGES[sys.argv[1]]("--build" in sys.argv)
