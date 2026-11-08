"""
Rebuild the east base bus flowing SOUTH (bridge/factorio/bus.py), with the coal riser at x=96 and the
military taps. Clears the old north-flowing trunks, taps and branches (x 71..97, y -145..-60; poles stay)
and the old coal feed's tail at x=84, then lays the new bus and extends the coal feed along y=-56 to the riser.

Usage: scripts/build_bus2.py [--build]
"""
import json
import sys

from _game import tools

from bridge.factorio import bus, military
from bridge.factorio.planner import batches


def main():
    build = "--build" in sys.argv
    plant, taps = military.plant()
    branch = []
    for k, y in taps:
        branch += bus.tap(k, y, military.X)
    trunk = bus.trunk_entities(taps)
    feed = [{"name": "transport-belt", "x": x + 0.5, "y": -55.5, "direction": 4} for x in range(84, 96)]
    feed.append({"name": "transport-belt", "x": 96.5, "y": -55.5, "direction": 0})
    ents = trunk + branch + feed
    counts = {}
    for e in ents:
        counts[e["name"]] = counts.get(e["name"], 0) + 1
    print(counts)
    if not build:
        return
    print(tools["save_game"]("before-bus-flip"))
    n = tools["run_lua"](" ".join("""
local n=0
for _,e in pairs(game.surfaces.nauvis.find_entities_filtered{area={{71,-145},{97.9,-60}},name={'transport-belt','splitter','underground-belt'}}) do e.destroy() n=n+1 end
for _,e in pairs(game.surfaces.nauvis.find_entities_filtered{area={{83.5,-62},{84.9,-55}},name='transport-belt'}) do e.destroy() n=n+1 end
rcon.print(n)""".splitlines()))
    print("cleared", n)
    for part in batches(ents):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"stopped: {json.dumps(r)[:1500]}")
        print("placed", r["placed"])


if __name__ == "__main__":
    main()
