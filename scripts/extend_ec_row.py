"""Extend the east electronic-circuit row (y0=-88) from 2 to N machines: places only the entities the larger row adds.
Usage: scripts/extend_ec_row.py [N] [--build]"""
import json
import sys

from _game import tools

from bridge import factorio  # noqa: F401
from bridge.factorio.blocks import assembler_row
from bridge.factorio.planner import batches

X, Y0, OLD = 98, -88, 2
N = int([a for a in sys.argv[1:] if a.isdigit()][0]) if any(a.isdigit() for a in sys.argv[1:]) else 4


def key(e):
    return (e["name"], e["x"], e["y"], e.get("direction"))


def main():
    old = {key(e) for e in assembler_row(X, Y0, "electronic-circuit", OLD, o_west=True).entities}
    new = [e for e in assembler_row(X, Y0, "electronic-circuit", N, o_west=True).entities if key(e) not in old]
    print(len(new), "new entities")
    for part in batches(new):
        r = json.loads(tools["place_entities"](json.dumps(part), dry_run="--build" not in sys.argv))
        print(r.get("placed"), r.get("failed"))


main()
