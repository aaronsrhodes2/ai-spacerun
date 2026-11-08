"""
Electronics rows for the east base: copper cable, electronic circuits and advanced circuits, each putting its product
back on the bus (rows whose output belt flows west, then bus.give onto a trunk's east lane).

    cable row  y0=-96  copper from trunk 1 (A)               -> trunk 3 (cable)
    EC row     y0=-88  cable from trunk 3 (A), iron trunk 1 (B) -> trunk 2 east lane (EC; plastic is on the west lane)
    AC row     y0=-80  cable trunk 3 (A), plastic|EC trunk 2 (B) -> trunk 0 east lane (AC; steel is on the west lane)

Normal rows take B from a lower trunk than A. Usage: scripts/build_electronics.py [--build]
"""
import json
import sys

from _game import tools

from bridge import factorio  # noqa: F401
from bridge.factorio import bus
from bridge.factorio.blocks import assembler_row
from bridge.factorio.planner import batches

X = 98
ROWS = [
    # recipe, machines, y0, (A trunk, B trunk or None), give trunk
    ("copper-cable", 2, -96, (1, None), 3),
    ("electronic-circuit", 2, -88, (3, 1), 2),
    ("advanced-circuit", 3, -80, (3, 2), 0),
]


def plan():
    ents, taps = [], []
    for recipe, n, y0, (ka, kb), kg in ROWS:
        row = assembler_row(X, y0, recipe, n, o_west=True)
        ents += row.entities
        taps.append((ka, y0 + 6))
        if kb is not None:
            taps.append((kb, y0 + 7))
        ents += bus.give(kg, y0, X - 1)
    branch = []
    for k, y in taps:
        branch += bus.tap(k, y, X)
    return ents + branch, taps


def main():
    build = "--build" in sys.argv
    ents, taps = plan()
    splitters = [e for e in bus.trunk_entities(taps) if e["name"] == "splitter"]
    counts = {}
    for e in ents + splitters:
        counts[e["name"]] = counts.get(e["name"], 0) + 1
    print(counts)
    bus.tiles([e for e in ents + splitters if e["name"] in ("transport-belt", "underground-belt", "splitter")] if False else
              [e for e in ents + splitters if e["name"] in ("underground-belt", "splitter")])
    for part in batches(ents):
        r = json.loads(tools["place_entities"](json.dumps(part), dry_run=True))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"dry run failed: {json.dumps(r)[:1800]}")
    print("dry run clean")
    if not build:
        return
    print(tools["save_game"]("before-electronics"))
    for k, y in taps:
        x, ty = bus.splitter_tile(k, y)
        tools["remove_entities"](x + 0.2, ty + 0.2, x + 0.8, ty + 0.8, names="transport-belt")
    for part in batches(ents + splitters):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"stopped: {json.dumps(r)[:1800]}")
        print("placed", r["placed"])


if __name__ == "__main__":
    main()
