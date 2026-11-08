"""
Re-route the military science packs to the Captain's new input port 1 at the Sandro station.

The old tail (north up x=-100 onto the fast belt) is removed from y=-37 up; the belt turns west at (-100,-37), runs along
y=-37 (north of the solar fields, hopping the link poles) to x=-333 and goes north into port 1's feeder head at (-333,-39).
Ports (feeder belt x): 1 at -333 (military), 2 at -326 (yellow), 3 at -319 (purple). Usage: scripts/build_pack_to_ports.py [--build]
"""
import json
import sys

from _game import tools
from build_pack_route import segment, with_hops

from bridge.factorio.planner import batches


def main():
    build = "--build" in sys.argv
    tiles = segment([(-100, -37), (-333, -37), (-333, -38)])
    if build:
        print(tools["save_game"]("before-pack-ports"))
        n = tools["run_lua"]("local n=0 for _,e in pairs(game.surfaces.nauvis.find_entities_filtered{area={{-100.9,-52.0},{-99.1,-36.9}},type={'transport-belt','underground-belt'}}) do e.destroy() n=n+1 end rcon.print(n)")
        print("old tail removed:", n)
    ents = with_hops(tiles)
    print("entities:", len(ents), "hops:", sum(1 for e in ents if e.get("params", {}).get("type") == "input"))
    for part in batches(ents):
        r = json.loads(tools["place_entities"](json.dumps(part), dry_run=True))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"dry run failed: {json.dumps(r)[:1500]}")
    print("dry run clean")
    if not build:
        return
    for part in batches(ents):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"stopped: {json.dumps(r)[:1500]}")
        print("placed", r["placed"])


if __name__ == "__main__":
    main()
