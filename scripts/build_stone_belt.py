"""
Raw stone to bus trunk 4's west lane (for rails). Two drills at the stone patch's west edge put stone on a belt that runs
west to x=81, south down x=81 (hopping the brick belt and the copper unload belt), east along y=-144, south down x=83
(hopping the brick row at y=-142) and side-loads trunk 4 at (84,-138) from the west: the west lane.

Usage: scripts/build_stone_belt.py [--build]
"""
import json
import sys

from _game import tools
from build_pack_route import segment, with_hops

from bridge.factorio.planner import batches


def main():
    build = "--build" in sys.argv
    drills = [{"name": "electric-mining-drill", "x": 84.5, "y": -426.5, "direction": 12},
              {"name": "electric-mining-drill", "x": 84.5, "y": -422.5, "direction": 12},
              {"name": "medium-electric-pole", "x": 86.5, "y": -424.5}]
    # drill outputs: (82,-427) and (82,-423); belt starts at the northern one
    tiles = segment([(82, -427), (81, -427), (81, -144), (83, -144), (83, -138), (84, -138)])
    tiles[-1] = (84 - 1, -138, 4)                          # last belt tile is (83,-138) facing east into trunk 4
    # segment() ends one tile short of trunk; rebuild the tail explicitly
    tiles = [t for t in tiles if not (t[0] == 83 and t[1] == -138)] + [(83, -138, 4)]
    ents = with_hops(tiles)
    print("entities:", len(ents), "hops:", sum(1 for e in ents if e.get("params", {}).get("type") == "input"))
    for part in batches(drills + ents):
        r = json.loads(tools["place_entities"](json.dumps(part), dry_run=True))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"dry run failed: {json.dumps(r)[:1500]}")
    print("dry run clean")
    if not build:
        return
    print(tools["save_game"]("before-stone-belt"))
    for part in batches(drills + ents):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"stopped: {json.dumps(r)[:1500]}")
        print("placed", r["placed"])


if __name__ == "__main__":
    main()
