"""
Rebuild whatever is missing from every build plan. Standing entities report
"blocked", so only the gaps get filled. The map is read with existing entities
treated as free ground, which is what lets a plan be laid over its own build.

Plans that put drills on ore need the snapshot taken before they were built (the
live grid shows an entity, not the ore under it), so pass that file as MINES_GRID.

Usage: scripts/restore.py [MINES_GRID.json]
"""

import json
import sys

from _game import tools

import build_first_mines
import build_power
import build_science
import build_smelting
from bridge.factorio.planner import Grid, Plan, batches


def grid_for(box):
    snap = json.loads(tools["map_grid"](*box))
    snap["rows"] = [r.replace("E", ".") for r in snap["rows"]]
    return Grid(snap)


def restore(label, plan):
    placed, standing, other = 0, 0, []
    for part in batches(plan.entities):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        if r.get("error"):
            other.append(r["error"])
            continue
        placed += r["placed"]
        for f in (r["failed"] if isinstance(r["failed"], list) else []):
            if f["why"] == "blocked at this position":
                standing += 1
            else:
                other.append(f)
    print(f"{label}: restored {placed}, standing {standing}, other {other[:4]}")


def main():
    if len(sys.argv) > 1:
        restore("mines", build_first_mines.build_plan(Grid(json.load(open(sys.argv[1])))))
    else:
        print("mines: skipped, pass the pre-build grid snapshot to restore them")
    restore("smelting", build_smelting.build_plan(grid_for(build_smelting.BOX)))
    restore("power", build_power.build_plan(grid_for(build_power.BOX)))
    for stage, fn in (("labs", build_science.labs_plan), ("labs2", build_science.labs2_plan),
                      ("assemblers", build_science.assemblers_plan)):
        plan = Plan(grid_for(build_science.BOX))
        fn(plan)
        restore(f"science {stage}", plan)
    print("fuel:", tools["seed_starter_fuel"](-90, -120, 45, 56))


if __name__ == "__main__":
    main()
