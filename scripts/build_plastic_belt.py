"""
Plastic from the refinery to the east base bus (trunk 2), by belt.

An inserter takes plastic out of the plant's buffer chest at (-146.5,-120.5) onto a new belt, which runs east to
x=-140, north to y=-137, then east along y=-137 (hopping under the oval's rails and under trunks 0 and 1) and
side-loads trunk 2 at (78,-137) from the west, so plastic takes trunk 2's west lane.

Usage: scripts/build_plastic_belt.py [--build]
"""
import json
import sys

from _game import tools
from build_pack_route import belt, segment, with_hops

from bridge.factorio.planner import batches

E_ = 4


def main():
    build = "--build" in sys.argv
    pts = [(-145, -121), (-140, -121), (-140, -137), (77, -137)]
    ents = with_hops(segment(pts))
    inserter = {"name": "inserter", "x": -145.5, "y": -120.5, "direction": 12}      # picks the chest (west), drops east
    hops = sum(1 for e in ents if e.get("params", {}).get("type") == "input")
    print("entities:", len(ents) + 1, "hops:", hops)
    for part in batches(ents + [inserter]):
        r = json.loads(tools["place_entities"](json.dumps(part), dry_run=True))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"dry run failed: {json.dumps(r)[:1500]}")
    print("dry run clean")
    if not build:
        return
    print(tools["save_game"]("before-plastic-belt"))
    tools["run_lua"]("local n=0 for _,e in pairs(game.surfaces.nauvis.find_entities_filtered{area={{-146,-122},{-143,-119}},type='tree'}) do e.destroy() end rcon.print('ok')")
    for part in batches(ents + [inserter]):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"stopped: {json.dumps(r)[:1500]}")
        print("placed", r["placed"])


if __name__ == "__main__":
    main()
