"""
Bus supply. Stage `coal`: a splitter on the coal belt at y=-63 (flowing west, x=66) sends half of the coal
down x=65 to y=-56, east along y=-56 (under the coal belt at x=68) to x=84, then north up x=84 into the head of trunk 4 (coal).
When the bus backs up the splitter sends everything on west, so the old base never loses coal.

Usage: scripts/build_bus_supply.py coal [--build]
"""
import json
import sys

from _game import tools

from bridge.factorio.planner import batches

N, E, S, W = 0, 4, 8, 12


def belt(x, y, d):
    return {"name": "transport-belt", "x": x + 0.5, "y": y + 0.5, "direction": d}


def coal_entities():
    ents = [{"name": "splitter", "x": 66.5, "y": -62.0, "direction": W}]
    ents += [belt(65, y, S) for y in range(-62, -56)]
    ents += [belt(x, -56, E) for x in (65, 66)]
    ents.append({"name": "underground-belt", "x": 67.5, "y": -55.5, "direction": E, "params": {"type": "input"}})
    ents.append({"name": "underground-belt", "x": 69.5, "y": -55.5, "direction": E, "params": {"type": "output"}})
    ents += [belt(x, -56, E) for x in range(70, 84)]
    ents += [belt(84, y, N) for y in range(-56, -61, -1)]
    return ents


def main():
    build = "--build" in sys.argv
    ents = coal_entities()
    probe = [e for e in ents if e["name"] != "splitter"]
    for part in batches(probe):
        r = json.loads(tools["place_entities"](json.dumps(part), dry_run=True))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"dry run failed: {json.dumps(r)[:1200]}")
    print("dry run clean for", len(probe), "belts")
    if not build:
        return
    print(tools["save_game"]("before-bus-coal"))
    print("old belt:", tools["remove_entities"](66.3, -63.7, 66.7, -63.3, names="transport-belt"))
    for part in batches(ents):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"stopped: {json.dumps(r)[:1200]}")
        print("placed", r["placed"])


if __name__ == "__main__":
    main()
