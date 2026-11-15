#!/usr/bin/env python3
"""Copper B Load (stop (749,-45), rails x=751, train y -83..-48): give the WEST collector belt its own loader row so the field is no longer capped by one belt.

Before: the 72 smelters in two columns (x 749.5 and 755.5) drop plates on two collector belts, x=746.5 (west column) and x=758.5 (east column). They meet at one
tile, (752.5,-39.5): the west one runs east along y=-39.5 (x 746.5..751.5) and side-loads, the east one side-loads from the other side; the merged belt goes up
x=753.5 to 24 loaders on the east side of the track. One turbo belt = about 60 items/s for 72 smelters that could make over 100.
After: the west collector keeps going north on x=746.5 to y=-47.5, jogs east to x=748.5 and runs north to y=-80.5 along the west side of the track; 24 epic bulk
inserters at x=749.5 (mirror of the east row at x=752.5) load the four wagons from that side. The old jog (x 747.5..751.5 on y=-39.5) is removed.
Everything is epic. Two substations at (746,-56) and (746,-72) power the new row.

Usage: scripts/copper_b_second_belt.py [--apply | --revert]
  dry run (default)  prints what it would place and what it would change
  --apply            places the new belts, inserters and substation, turns (746.5,-39.5) north, removes the old jog
  --revert           turns (746.5,-39.5) back east, rebuilds the old jog, removes the new belts, inserters and substation (plates on them are lost: a few dozen)"""
import json
import sys

from _game import tools

Q = {"quality": "epic"}
N, E, S, W = 0, 4, 8, 12
BELT = "turbo-transport-belt"


def new_entities():
    ents = []
    for i in range(7):                                    # x=746.5, y -40.5 .. -46.5, north
        ents.append({"name": BELT, "x": 746.5, "y": -40.5 - i, "direction": N, "params": dict(Q)})
    ents.append({"name": BELT, "x": 746.5, "y": -47.5, "direction": E, "params": dict(Q)})
    ents.append({"name": BELT, "x": 747.5, "y": -47.5, "direction": E, "params": dict(Q)})
    y = -47.5
    while y >= -80.5:                                     # the loader column x=748.5, north
        ents.append({"name": BELT, "x": 748.5, "y": y, "direction": N, "params": dict(Q)})
        y -= 1
    for wy in (-55, -62, -69, -76):                       # wagon centres; six loaders a wagon, picking from the belt on their west
        for k in range(-3, 3):
            ents.append({"name": "bulk-inserter", "x": 749.5, "y": wy + k + 0.5, "direction": W, "params": dict(Q)})
    for sy in (-56, -72):                                 # a substation covers 18 tiles: two to reach all four wagons
        ents.append({"name": "substation", "x": 746, "y": sy, "params": dict(Q)})
    return ents


def old_jog():
    return [{"name": BELT, "x": 747.5 + i, "y": -39.5, "direction": E, "params": dict(Q)} for i in range(5)]      # x 747.5 .. 751.5


TURN = r'''
local s = game.surfaces.nauvis
local b = s.find_entities_filtered{name = 'turbo-transport-belt', position = {746.5, -39.5}, radius = 0.3}[1]
b.direction = defines.direction.DIR
rcon.print('belt (746.5,-39.5) now direction ' .. tostring(b.direction))
'''

REMOVE_NEW = r'''
local s = game.surfaces.nauvis
local n = 0
for _, e in pairs(s.find_entities_filtered{area = {{746, -81}, {750, -40}}, force = game.forces.player}) do
  if (e.name == 'turbo-transport-belt' and ((e.position.x == 746.5 and e.position.y < -40) or e.position.x == 747.5 and e.position.y == -47.5 or e.position.x == 748.5)) or
     (e.name == 'bulk-inserter' and e.position.x == 749.5) or (e.name == 'substation' and e.position.x == 746 and e.position.y < -50) then
    e.destroy() n = n + 1
  end
end
rcon.print('removed ' .. n .. ' new entities')
'''

REMOVE_JOG = r'''
local s = game.surfaces.nauvis
local n = 0
for _, e in pairs(s.find_entities_filtered{name = 'turbo-transport-belt', area = {{747, -40}, {752, -39}}}) do
  if e.position.y == -39.5 and e.position.x >= 747.5 and e.position.x <= 751.5 then e.destroy() n = n + 1 end
end
rcon.print('removed ' .. n .. ' old jog belts')
'''


def place(ents, dry):
    r = json.loads(tools["place_entities"](json.dumps(ents), surface="nauvis", dry_run=dry))
    return r


def main():
    if "--revert" in sys.argv:
        print(place(old_jog(), False))
        print(tools["run_lua"](TURN.replace("DIR", "east")))
        print(tools["run_lua"](REMOVE_NEW))
        return
    ents = new_entities()
    dry = "--apply" not in sys.argv
    r = place(ents, True)
    print(f"{len(ents)} entities planned (belts {sum(1 for e in ents if e['name'] == BELT)}, bulk inserters {sum(1 for e in ents if e['name'] == 'bulk-inserter')}, substations 2):",
          "dry run placed", r.get("placed"), "failed", json.dumps(r.get("failed") or [])[:400])
    if dry or r.get("failed"):
        return
    r2 = place(ents, False)
    print("APPLIED: placed", r2.get("placed"), "failed", json.dumps(r2.get("failed") or [])[:300])
    print(tools["run_lua"](REMOVE_JOG))
    print(tools["run_lua"](TURN.replace("DIR", "north")))


if __name__ == "__main__":
    main()
