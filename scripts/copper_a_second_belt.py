#!/usr/bin/env python3
"""Copper A Load (stop (327,111), rails x=329, wagons y 80/87/94/101): give the WEST branch its own loader row, as copper_b_second_belt.py did for B.

Before: three branches (x=325.5 west, x=331.5 middle, x=337.5 east) meet at (331.5,116.5) and ONE turbo belt (x=331.5, ~60 items/s) feeds the loaders on the east side
of the track (x=330.5). 50 of the 62 smelters sat at full output (2026-11-15): the field could make more than the belt carries.
After: the west branch turns north at (326.5,116.5) and runs up x=326.5 along the west side of the track; 24 epic bulk inserters at x=327.5 (six a wagon, mirror of the east
row) load the four wagons from that side. The old jog (327.5..330.5, 116.5) is removed. Two epic substations at (324,82) and (324,98) power the new row.

Usage: scripts/copper_a_second_belt.py [--apply | --revert]   (default dry run)"""
import json
import sys

from _game import tools

Q = {"quality": "epic"}
N, E, S, W = 0, 4, 8, 12
BELT = "turbo-transport-belt"
WAGONS = (80, 87, 94, 101)


def new_entities():
    ents = []
    y = 115.5
    while y >= 109.5:                                      # x=325.5 north past the train stop (326..328, 110..112); (325.5,116.5) is re-laid by the apply step
        ents.append({"name": BELT, "x": 325.5, "y": y, "direction": N, "params": dict(Q)})
        y -= 1
    ents.append({"name": BELT, "x": 325.5, "y": 108.5, "direction": E, "params": dict(Q)})
    y = 108.5
    while y >= 75.5:                                       # x=326.5 north along the west side of the track
        ents.append({"name": BELT, "x": 326.5, "y": y, "direction": N, "params": dict(Q)})
        y -= 1
    for wy in WAGONS:
        for k in range(-3, 3):
            ents.append({"name": "bulk-inserter", "x": 327.5, "y": wy + k + 0.5, "direction": W, "params": dict(Q)})
    for sy in (82, 98):
        ents.append({"name": "substation", "x": 324, "y": sy, "params": dict(Q)})
    return ents


TURN = r'''
local s = game.surfaces.nauvis
local f = game.forces.player
for _, x in ipairs({325.5, 326.5, 327.5, 328.5, 329.5, 330.5}) do
  for _, e in pairs(s.find_entities_filtered{type = 'transport-belt', position = {x, 116.5}, radius = 0.3}) do e.destroy() end
end
local b = s.create_entity{name = 'turbo-transport-belt', position = {325.5, 116.5}, direction = defines.direction.north, force = f, quality = 'epic'}
rcon.print('west branch now turns north at 325.5,116.5: ' .. tostring(b ~= nil) .. '; old jog 326.5..330.5 removed')
'''

REVERT = r'''
local s = game.surfaces.nauvis
local f = game.forces.player
local n = 0
for _, e in pairs(s.find_entities_filtered{area = {{323, 75}, {328.1, 117}}}) do
  if (e.name == 'turbo-transport-belt' and (e.position.x == 326.5 or (e.position.x == 325.5 and e.position.y < 116))) or (e.name == 'bulk-inserter' and e.position.x == 327.5) or (e.name == 'substation' and e.position.x == 324) then e.destroy() n = n + 1 end
end
for _, x in ipairs({325.5, 326.5, 327.5, 328.5, 329.5, 330.5}) do
  for _, e in pairs(s.find_entities_filtered{type = 'transport-belt', position = {x, 116.5}, radius = 0.3}) do e.destroy() end
  s.create_entity{name = 'turbo-transport-belt', position = {x, 116.5}, direction = defines.direction.east, force = f, quality = 'epic'}
end
rcon.print('reverted: removed ' .. n .. ' new entities, old jog rebuilt')
'''

if __name__ == "__main__":
    if "--revert" in sys.argv:
        print(tools["run_lua"](REVERT))
    else:
        apply = "--apply" in sys.argv
        ents = new_entities()
        if apply:
            print(tools["run_lua"](TURN))
        r = json.loads(tools["place_entities"](json.dumps(ents), surface="nauvis", dry_run=not apply))
        print(("placed " if apply else "dry run, would place ") + str(r.get("placed")), "failed", json.dumps(r.get("failed"))[:600])
