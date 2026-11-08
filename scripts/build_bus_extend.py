"""
Extend the east base bus south from y=-62 to y=-46 (the coal hub stop sits at (72..73,-44..-43)) for more rows.

  1. power first: a big pole at (96,-52) replaces the one at (94,-60) (it sat on trunk 7's path); spine poles at y=-52.5
  2. the coal feed row y=-56 (x 71..94) hops every trunk by underground belt instead of ending at them
  3. new trunk belts for y -61..-32

Usage: scripts/build_bus_extend.py [--build]
"""
import json
import sys

from _game import tools

from bridge.factorio import bus
from bridge.factorio.planner import batches


def main():
    build = "--build" in sys.argv
    poles = [{"name": "big-electric-pole", "x": 96.0, "y": -52.0}] + \
            [{"name": "medium-electric-pole", "x": 97.5, "y": y} for y in (-52.5,)]
    feed = []
    for k in range(bus.TRUNKS):
        x = bus.trunk_x(k)
        feed.append({"name": "underground-belt", "x": x - 1 + 0.5, "y": -55.5, "direction": 4, "params": {"type": "input"}})
        feed.append({"name": "underground-belt", "x": x + 1 + 0.5, "y": -55.5, "direction": 4, "params": {"type": "output"}})
    trunk = [{"name": "transport-belt", "x": bus.trunk_x(k) + 0.5, "y": y + 0.5, "direction": 8}
             for k in range(bus.TRUNKS) for y in range(-61, -45) if y != -56]
    print("poles", len(poles), "feed", len(feed), "trunk belts", len(trunk))
    if not build:
        for part in batches(poles + trunk):
            r = json.loads(tools["place_entities"](json.dumps(part), dry_run=True))
            print("dry", r.get("placed"), [f for f in r.get("failed", [])][:5])
        return
    print(tools["save_game"]("before-bus-extend"))
    print("poles:", tools["place_entities"](json.dumps(poles)))
    n = tools["run_lua"](" ".join("""
local s=game.surfaces.nauvis
local ids={}
for _,p in pairs(s.find_entities_filtered{type='electric-pole',area={{60,-145},{135,-30}}}) do local k=tostring(p.electric_network_id) ids[k]=(ids[k] or 0)+1 end
rcon.print(helpers.table_to_json(ids))""".splitlines()))
    print("networks before removing old pole:", n)
    print(tools["remove_entities"](93.0, -61.0, 95.0, -59.0, names="big-electric-pole"))
    n = tools["run_lua"](" ".join("""
local n=0
for _,e in pairs(game.surfaces.nauvis.find_entities_filtered{area={{70.9,-56.9},{94.9,-55.1}},type='transport-belt'}) do e.destroy() n=n+1 end
rcon.print(n)""".splitlines()))
    print("feed belts removed:", n)
    for part in batches(feed + trunk):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"stopped: {json.dumps(r)[:1500]}")
        print("placed", r["placed"])
    for k in range(bus.TRUNKS):              # the trunk tile at y=-56 itself
        pass
    r = json.loads(tools["place_entities"](json.dumps([{"name": "transport-belt", "x": bus.trunk_x(k) + 0.5, "y": -55.5, "direction": 8} for k in range(bus.TRUNKS)])))
    print("trunk tiles at y=-56:", r)


if __name__ == "__main__":
    main()
