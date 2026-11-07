"""
Electric coal lift for the boilers: a medium-pole line from the base to the coal ring,
then two electric inserters replace the single burner inserter that capped the
boilers at about 2.4 MW (0.6 coal/s).

Usage: scripts/build_power3.py [--build]
"""
import json
import math
import sys

from _game import tools

from bridge.factorio.planner import Grid, Plan, batches

BOX = (-35, -66, 40, -44)
START = (-28, -55)          # existing small pole near the hub
END = (29, -57)
OFFSETS = [(0, 0), (0, 1), (0, -1), (1, 0), (-1, 0), (0, 2), (0, -2), (1, 1), (-1, 1), (1, -1), (-1, -1), (2, 0), (-2, 0)]


def build_plan(plan):
    prev = (START[0] + 0.5, START[1] + 0.5)
    x = START[0]
    while True:
        x = min(x + 7, END[0])
        placed = False
        for dx, dy in OFFSETS:
            tx, ty = x + dx, END[1] + dy if x == END[0] else -56 + dy
            if (tx, ty) in plan.taken or plan.grid.at(tx, ty) in "~K?E":
                continue
            if math.hypot(tx + 0.5 - prev[0], ty + 0.5 - prev[1]) > 7.4:
                continue
            plan.machine("medium-electric-pole", tx, ty, 1, 1)
            prev = (tx + 0.5, ty + 0.5)
            x = tx
            placed = True
            break
        if not placed:
            raise SystemExit(f"no free tile for a pole near {x},-56")
        if x >= END[0]:
            break
    plan.machine("inserter", 30, -58, 1, 1, direction=0)
    plan.machine("inserter", 31, -58, 1, 1, direction=0)
    plan.belt(31, -57, 12)


def main():
    build = "--build" in sys.argv
    snap = json.loads(tools["map_grid"](*BOX))
    # the burner lift inserter at (30,-58) is replaced
    row = list(snap["rows"][-58 - BOX[1]])
    row[30 - BOX[0]] = "."
    snap["rows"][-58 - BOX[1]] = "".join(row)
    plan = Plan(Grid(snap))
    build_plan(plan)
    counts = {}
    for e in plan.entities:
        counts[e["name"]] = counts.get(e["name"], 0) + 1
    print("plan:", counts, [(e["x"], e["y"]) for e in plan.entities if e["name"] == "medium-electric-pole"])
    if not build:
        return
    print("old lift:", tools["remove_entities"](30.3, -57.7, 30.7, -57.3, names="burner-inserter"))
    for part in batches(plan.entities):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"build stopped: {json.dumps(r)[:1500]}")
        print("placed", r["placed"])


if __name__ == "__main__":
    main()
