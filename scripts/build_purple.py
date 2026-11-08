"""
Purple (production) science on the bus.

East rows (south end of the east side):
    iron stick  y0=-72  iron from trunk 1 (A)                          -> trunk 4 east lane (stone is on its west lane)
    prod module y0=-64  EC from trunk 2 (A), AC from trunk 0 (B)         -> trunk 6 east lane
West rows (designed east-side, mirrored; virtual trunk kv = real 7-kv, gives land on the real WEST lane):
    rail        y0=-128 steel trunk 0 (A), stone|sticks trunk 4 (B)      -> trunk 7 west lane (coal is on its east lane)
    electric furnace y0=-120 steel+AC trunk 0 (A), brick trunk 5 (B)     -> trunk 6 west lane (module is on the east lane)
    purple pack y0=-112 module|furnace trunk 6 (A), coal|rail trunk 7 (B) -> output belt flows west (not yet routed)

Usage: scripts/build_purple.py [--build]
"""
import json
import sys

from _game import tools

from bridge.factorio import bus, westbus
from bridge.factorio.blocks import assembler_row
from bridge.factorio.planner import batches

X = 98
EAST = [  # recipe, n, y0, A trunk, B trunk or None, give trunk
    ("iron-stick", 1, -72, 1, None, 4),
    ("productivity-module", 1, -64, 2, 0, 6),
]
WEST = [  # recipe, n, y0, virtual A, virtual B, virtual give (None: output flows away from the bus)
    ("rail", 2, -128, 7, 3, 0),
    ("electric-furnace", 1, -120, 7, 2, 1),
    ("production-science-pack", 2, -112, 1, 0, None),
]


def plan():
    east, west, e_taps, w_taps = [], [], [], []
    for recipe, n, y0, ka, kb, kg in EAST:
        east += assembler_row(X, y0, recipe, n, o_west=True).entities
        e_taps.append((ka, y0 + 6))
        if kb is not None:
            e_taps.append((kb, y0 + 7))
        east += bus.give(kg, y0, X - 1)
    for recipe, n, y0, ka, kb, kg in WEST:
        west += assembler_row(X, y0, recipe, n, o_west=kg is not None).entities
        w_taps.append((ka, y0 + 6))
        w_taps.append((kb, y0 + 7))
        if kg is not None:
            west += bus.give(kg, y0, X - 1)
    east += [e for k, y in e_taps for e in bus.tap(k, y, X)]
    west += [e for k, y in w_taps for e in bus.tap(k, y, X)]
    e_split = [e for e in bus.trunk_entities(e_taps) if e["name"] == "splitter"]
    w_split = [e for e in bus.trunk_entities(w_taps) if e["name"] == "splitter"]
    # west spine poles (mirror of the east spine) and a link pole to the grid
    w_poles = [{"name": "medium-electric-pole", "x": 68.5, "y": -132.5 + 8 * k, "direction": 0} for k in range(0, 4)]
    link = [{"name": "medium-electric-pole", "x": 69.5, "y": -138.5, "direction": 0}]
    return east, e_taps, e_split, westbus.mirror(west), w_taps, westbus.mirror(w_split), w_poles + link


def main():
    build = "--build" in sys.argv
    east, e_taps, e_split, west, w_taps, w_split, poles = plan()
    ents = east + west + poles
    splitters = e_split + w_split
    for group in (east + e_split, west + w_split):
        bus.tiles([e for e in group if e["name"] in ("underground-belt", "splitter")])
    counts = {}
    for e in ents + splitters:
        counts[e["name"]] = counts.get(e["name"], 0) + 1
    print(counts)
    for part in batches(ents):
        r = json.loads(tools["place_entities"](json.dumps(part), dry_run=True))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"dry run failed: {json.dumps(r)[:1800]}")
    print("dry run clean")
    if not build:
        return
    print(tools["save_game"]("before-purple"))
    for k, y in e_taps:
        x, ty = bus.splitter_tile(k, y)
        tools["remove_entities"](x + 0.2, ty + 0.2, x + 0.8, ty + 0.8, names="transport-belt")
    for kv, y in w_taps:
        x, ty = westbus.real_splitter_tile(kv, y)
        tools["remove_entities"](x + 0.2, ty + 0.2, x + 0.8, ty + 0.8, names="transport-belt")
    for part in batches(ents + splitters):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"stopped: {json.dumps(r)[:1800]}")
        print("placed", r["placed"])


if __name__ == "__main__":
    main()
