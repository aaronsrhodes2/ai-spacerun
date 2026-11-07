"""
Plastic: a chemical plant above the refinery, coal by belt, plastic into a chest.

    refinery   top-left (-152,-114), basic-oil-processing; petroleum gas leaves by the
               third output tile (-148,-115) (tested in game)
    plant      chemical plant, centre (-146.5,-117.5), facing S so its inputs face the
               refinery; pipes (-148..-146,-116) join both input tiles to the gas pipe
    coal       the copper row's fuel belt (y=-90, ends at x=-72) is extended west to
               x=-144, then north up x=-144 to y=-118; an inserter at (-145,-118) feeds the plant
    output     inserter (-147,-120) drops plastic into an iron chest at (-147,-121)

Usage: scripts/build_plastic.py [--build]
"""
import json
import sys

from _game import tools

from bridge.factorio.planner import E, N, S, W, Grid, Plan, batches

BOX = (-156, -126, -66, -86)


def build_plan(plan):
    plan.machine("chemical-plant", -148, -119, 3, 3, direction=S, recipe="plastic-bar")
    for x in (-148, -147, -146):
        plan.machine("pipe", x, -116, 1, 1)
    plan.machine("medium-electric-pole", -150, -117, 1, 1)
    plan.machine("medium-electric-pole", -143, -120, 1, 1)
    plan.line((-73, -90), (-144, -90), (-144, -118), last_direction=N)
    plan.machine("inserter", -145, -118, 1, 1, direction=E)     # picks east from the belt end, drops into the plant
    plan.machine("inserter", -147, -120, 1, 1, direction=S)     # picks from the plant, drops north into the chest
    plan.machine("iron-chest", -147, -121, 1, 1)


def main():
    build = "--build" in sys.argv
    snap = json.loads(tools["map_grid"](*BOX))
    # the refinery and its pipes already stand in this box; they are not part of this plan
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
    print("test pipes:", tools["remove_entities"](-151.7, -114.7, -149.3, -114.3, names="pipe"))
    placed = 0
    for part in batches(plan.entities):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"build stopped after {placed}: {json.dumps(r)[:1500]}")
        placed += r["placed"]
    print("placed", placed)


if __name__ == "__main__":
    main()
