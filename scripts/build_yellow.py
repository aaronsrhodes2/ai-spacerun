"""
Yellow science block (bridge/factorio/yellow.py) and its five bus taps (mirrored west-side taps).
Usage: scripts/build_yellow.py [--build]
"""
import json
import sys

from _game import tools

from bridge.factorio import bus, westbus, yellow
from bridge.factorio.planner import batches

X = 98
R = westbus.real_k
TAPS = [(R(1), -120), (R(0), -109), (R(0), -123), (R(2), -117), (R(1), -106)]   # virtual trunk numbers: T1 N1, T0 S2, T0 steel, T2 plastic|EC, T1 iron


def belt(x, y, d):
    return yellow.belt(x, y, d)


def tap_extension():
    """Plain belts from the bus edge (x=67) to the first block belt on the rows that need them."""
    e = []
    for x in (67, 66, 65):
        e.append(belt(x, -123, 12))
    for x in (67, 66, 65, 64):
        e.append(belt(x, -117, 12))
    for x in (67, 66, 65, 64):
        e.append(belt(x, -106, 12))
    return e


def plan():
    taps = []
    for kv, y in TAPS:
        taps += bus.tap(kv, y, X)
    split = [e for e in bus.trunk_entities(TAPS) if e["name"] == "splitter"]
    return yellow.all_entities() + tap_extension() + westbus.mirror(taps), westbus.mirror(split)


def main():
    build = "--build" in sys.argv
    ents, bus_split = plan()
    counts = {}
    for e in ents + bus_split:
        counts[e["name"]] = counts.get(e["name"], 0) + 1
    print(counts)
    if "--resume" not in sys.argv:
        for part in batches(ents):
            r = json.loads(tools["place_entities"](json.dumps(part), dry_run=True))
            if r.get("error") or r["failed"]:
                raise SystemExit(f"dry run failed: {json.dumps(r)[:2500]}")
        print("dry run clean")
    if not build:
        return
    if "--resume" not in sys.argv:
        print(tools["save_game"]("before-yellow"))
    for kv, y in TAPS if "--resume" not in sys.argv else []:
        x, ty = westbus.real_splitter_tile(kv, y)
        tools["remove_entities"](x + 0.2, ty + 0.2, x + 0.8, ty + 0.8, names="transport-belt")
    for part in batches(ents + bus_split):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        if r.get("error"):
            raise SystemExit(f"stopped: {json.dumps(r)[:2500]}")
        if r["failed"] and "--resume" not in sys.argv:
            raise SystemExit(f"stopped: {json.dumps(r)[:2500]}")
        print("placed", r["placed"], "failed", len(r["failed"]) if r["failed"] else 0)
    for x, y, item, prio in yellow.SPLITTERS:
        print(tools["run_lua"](f"local sp=game.surfaces.nauvis.find_entity('splitter',{{{x + 0.5},{y + 1.0}}}) sp.splitter_filter={{name='{item}'}} sp.splitter_output_priority='{prio}' rcon.print('{item} '..tostring(sp.splitter_filter and sp.splitter_filter.name)..' '..sp.splitter_output_priority)"))


if __name__ == "__main__":
    main()
