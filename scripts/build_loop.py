"""
Loop v1 (skeleton): one closed rail oval north of the iron patch, in free ground.

    side B  y=-117 running east from x=-70 to x=51, over the free iron strip at the north edge
            of the iron patch (iron stop goes here)
    side A  y=-143 running west; ends x=-83 and x=51 are the four-curve turns
Track is bidirectional until signals set the direction; v1 is one train, one direction.

Stages: rails     Usage: scripts/build_loop.py <stage> [--build]
"""
import json
import sys

from _game import tools

from bridge.factorio import rails
from bridge.factorio.planner import batches

START = (-70, -117, 4)
LEGS = [("N", 51), ("W", -143), ("S", -83), ("E", -117)]


def place(entities, build, label):
    print(label, "count:", len(entities))
    for part in batches(entities):
        r = json.loads(tools["place_entities"](json.dumps(part), dry_run=True))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"dry run failed, nothing built: {json.dumps(r)[:1800]}")
    print(label, "dry run clean")
    if not build:
        return
    placed = 0
    for part in batches(entities):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"{label} stopped after {placed}: {json.dumps(r)[:1800]}")
        placed += r["placed"]
    print(label, "placed", placed)


def main():
    stage, build = sys.argv[1], "--build" in sys.argv
    if stage == "rails":
        pieces, end = rails.route(START, LEGS)
        assert end == START, end
        place([rails.entity(p) for p in pieces], build, "rails")


if __name__ == "__main__":
    main()
