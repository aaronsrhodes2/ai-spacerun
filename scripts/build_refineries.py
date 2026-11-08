"""
Refinery 2, from the blueprint: facing south just under the crude pipe row (y=-109) so it shares
refinery 1's crude inputs, gas piped round the east side into the gas line at (-147,-116).

Usage: scripts/build_refineries.py [--build]
"""
import json
import sys

from _game import tools

from bridge.factorio import blueprints as bp
from bridge.factorio.planner import Grid, Plan, PlanError, pipe_route
from build_feeds import place

TX, TY = -152, -108


def main():
    build = "--build" in sys.argv
    r2 = bp.refinery_s(TX, TY)
    plan = Plan(Grid(json.loads(tools["map_grid"](-175, -125, -135, -95))))
    plan.machine("oil-refinery", TX, TY, 5, 5, direction=8, recipe="basic-oil-processing")
    start = r2["gas_out"]
    plan.machine("pipe", start[0], start[1], 1, 1)
    try:
        path = pipe_route(plan, (start[0] + 1, start[1]), [(-147, -116)])
    except PlanError as e:
        raise SystemExit(f"gas route failed: {e}")
    for t in path:
        plan.machine("pipe", t[0], t[1], 1, 1)
    print("gas pipe:", len(path) + 1, "tiles to", path[-1])
    place(plan.entities, build, "refinery 2")


if __name__ == "__main__":
    main()
