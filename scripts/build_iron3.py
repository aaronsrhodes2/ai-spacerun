"""
Electric iron field: 12 electric mining drills in two rows around one belt on the
big iron patch's wide middle, joined to the existing ore spoke.

    y=-115..-113  row A, drills facing S
    y=-112        belt, flows east to x=-9
    y=-111..-109  row B, drills facing N          (trunk belt is at y=-108)
    x=-9          belt turns south, goes under the trunk (underground -109 -> -107)
    y=-104        west to x=-11, underground under the coal column at x=-12 to
                  (-13,-104), the old start of the burner row's ore belt, which
                  carries it on to the spoke at x=-20

Poles sit in the gap columns (drills are spaced 4 apart) and join the network at (-11,-107).

Usage: scripts/build_iron3.py [--build]
"""

import json
import sys

from _game import tools

from bridge.factorio.planner import E, N, S, W, Grid, Plan, batches

X0S = [-38, -34, -30, -26, -22, -18]
BOX = (-45, -120, -5, -100)


def build_plan(plan):
    for x in X0S:
        plan.machine("electric-mining-drill", x, -115, 3, 3, direction=S)
        plan.machine("electric-mining-drill", x, -111, 3, 3, direction=N)
        if x != X0S[-1]:
            plan.machine("small-electric-pole", x + 3, -114, 1, 1)
            plan.machine("small-electric-pole", x + 3, -110, 1, 1)
    plan.machine("small-electric-pole", -15, -110, 1, 1)
    plan.machine("small-electric-pole", -15, -114, 1, 1)
    plan.line((-37, -112), (-9, -112), (-9, -110), last_direction=S)
    plan.entities.append({"name": "underground-belt", "x": -8.5, "y": -108.5, "direction": S, "params": {"type": "input"}})
    plan.taken[(-9, -109)] = "underground"
    plan.entities.append({"name": "underground-belt", "x": -8.5, "y": -106.5, "direction": S, "params": {"type": "output"}})
    plan.taken[(-9, -107)] = "underground"
    plan.line((-9, -106), (-9, -105), last_direction=S)
    plan.line((-9, -104), (-10, -104), last_direction=W)
    plan.entities.append({"name": "underground-belt", "x": -10.5, "y": -103.5, "direction": W, "params": {"type": "input"}})
    plan.taken[(-11, -104)] = "underground"
    plan.entities.append({"name": "underground-belt", "x": -12.5, "y": -103.5, "direction": W, "params": {"type": "output"}})
    plan.taken[(-13, -104)] = "underground"


def main():
    build = "--build" in sys.argv
    snap = json.loads(tools["map_grid"](*BOX))
    # The old ore belt start at (-13,-104) is replaced by the underground exit; the
    # coal column, trunk and burner row are real obstacles and stay as they are.
    row = list(snap["rows"][-104 - BOX[1]])
    row[-13 - BOX[0]] = "."
    snap["rows"][-104 - BOX[1]] = "".join(row)
    plan = Plan(Grid(snap))
    build_plan(plan)
    counts = {}
    for e in plan.entities:
        counts[e["name"]] = counts.get(e["name"], 0) + 1
    print("plan:", counts)
    for part in batches(plan.entities):
        r = json.loads(tools["place_entities"](json.dumps(part), dry_run=True))
        if r.get("error") or r["failed"]:
            # the exit tile is still occupied by the old belt in a dry run
            real = [f for f in (r["failed"] if isinstance(r["failed"], list) else []) if not (f["x"] == -12.5 and f["y"] == -103.5)]
            if r.get("error") or real:
                raise SystemExit(f"dry run failed, nothing built: {json.dumps(r)[:1500]}")
    print("dry run clean")
    if not build:
        return
    print(tools["save_game"]("before-iron-field"))
    print("old start:", tools["remove_entities"](-12.7, -103.7, -12.3, -103.3, names="transport-belt"))
    placed = 0
    for part in batches(plan.entities):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"build stopped after {placed}: {json.dumps(r)[:1500]}")
        placed += r["placed"]
    print("placed", placed)


if __name__ == "__main__":
    main()
