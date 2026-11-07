"""
Electric copper field on the south part of the copper patch (the burner row is at y=-88).

    y=-85..-83  row A, electric drills facing S, at x=-74, -70, -66
    y=-82       belt east to x=-53
    y=-81..-79  row B, facing N, same x
    x=-53       north to y=-84, then under the old ore belt (y=-86) by underground
                (-85 -> -87), east two tiles, south one, side-loading onto the ore
                lane (north lane) at (-51,-86). The south lane carries coal for the
                smelters; ore must never share it or the furnaces deadlock.
    poles       medium, in the drill gaps (x=-71, -67), then east along y=-84 to the
                copper furnaces' small pole near (-35,-82)

Usage: scripts/build_copper2.py [--build]
"""
import json
import sys

from _game import tools

from bridge.factorio.planner import E, N, S, W, Grid, Plan, batches

BOX = (-82, -96, -30, -70)
X0S = [-74, -70, -66]


def build_plan(plan):
    for x in X0S:
        plan.machine("electric-mining-drill", x, -85, 3, 3, direction=S)
        plan.machine("electric-mining-drill", x, -81, 3, 3, direction=N)
    plan.line((-73, -82), (-53, -82), (-53, -84), last_direction=N)
    plan.entities.append({"name": "underground-belt", "x": -52.5, "y": -84.5, "direction": N, "params": {"type": "input"}})
    plan.taken[(-53, -85)] = "underground"
    plan.entities.append({"name": "underground-belt", "x": -52.5, "y": -86.5, "direction": N, "params": {"type": "output"}})
    plan.taken[(-53, -87)] = "underground"
    plan.line((-53, -88), (-52, -88), last_direction=E)
    plan.line((-51, -88), (-51, -87), last_direction=S)
    for x in (-71, -67):
        plan.machine("medium-electric-pole", x, -83, 1, 1)
    for x in (-60, -52, -44, -37):
        plan.machine("medium-electric-pole", x, -84, 1, 1)


def main():
    build = "--build" in sys.argv
    plan = Plan(Grid(json.loads(tools["map_grid"](*BOX))))
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
