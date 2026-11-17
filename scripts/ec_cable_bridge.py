#!/usr/bin/env python3
"""Cable bridge for the robot-fed circuit cells at x=-122.5 (rows -164.5 .. -188.5, step 3), 2026-11-15.
Each of those cells has its cable source 4 tiles west: the cable cell's output chest (-129.5,y) holds up to 24,000 cable, but the cell's own requester chest (-125.5,y) waits on
robots that carry 4 items a trip (cable 0-4 in the machines while 192k circuits sat in their full output chests: they idle now, and will starve the moment those drain).
Bridge per row: epic bulk inserter (-128.5,y) cable chest -> steel chest (-127.5,y), 2 slots -> epic bulk inserter (-126.5,y) -> the requester chest (-125.5,y).
The second inserter is wired (green) to the requester chest and enabled only while the chest holds < 600 cable, so cable can never crowd out the iron plates the robots bring.
Usage: ec_cable_bridge.py [--apply | --revert]   (default dry run)"""
import json
import sys

from _game import tools

Q = {"quality": "epic"}
ROWS = [-164.5 - 3 * i for i in range(9)]


def ents():
    out = []
    for y in ROWS:
        out += [
            {"name": "bulk-inserter", "x": -128.5, "y": y, "direction": 12, "params": dict(Q)},
            {"name": "steel-chest", "x": -127.5, "y": y, "params": {}},
            {"name": "bulk-inserter", "x": -126.5, "y": y, "direction": 12, "params": dict(Q)},
        ]
    return out


CONFIG = r'''
local s = game.surfaces.nauvis
local W = defines.wire_connector_id
local ok, n = 0, 0
for _, y in ipairs(ROWSLUA) do
  local mid = s.find_entities_filtered{name = 'steel-chest', position = {-127.5, y}, radius = 0.4}[1]
  if mid then mid.get_inventory(defines.inventory.chest).set_bar(3) end
  local ins = s.find_entities_filtered{name = 'bulk-inserter', position = {-126.5, y}, radius = 0.4}[1]
  local rq = s.find_entities_filtered{name = 'requester-chest', position = {-125.5, y}, radius = 0.4}[1]
  if ins and rq then
    ins.get_wire_connector(W.circuit_green, true).connect_to(rq.get_wire_connector(W.circuit_green, true), false)
    local cb = ins.get_or_create_control_behavior()
    cb.circuit_enable_disable = true
    cb.circuit_condition = {first_signal = {type = 'item', name = 'copper-cable'}, comparator = '<', constant = 600}
    ok = ok + 1
  end
  n = n + 1
end
rcon.print('wired ' .. ok .. ' of ' .. n .. ' rows')
'''

REVERT = r'''
local s = game.surfaces.nauvis
local n = 0
for _, y in ipairs(ROWSLUA) do
  for _, e in pairs(s.find_entities_filtered{area = {{-129, y - 0.4}, {-126, y + 0.4}}}) do
    if e.name == 'bulk-inserter' or e.name == 'steel-chest' then e.destroy() n = n + 1 end
  end
end
rcon.print('removed ' .. n)
'''

if __name__ == "__main__":
    rows = "{" + ",".join(str(v) for v in ROWS) + "}"
    if "--revert" in sys.argv:
        print(tools["run_lua"](REVERT.replace("ROWSLUA", rows)))
    else:
        apply = "--apply" in sys.argv
        r = json.loads(tools["place_entities"](json.dumps(ents()), surface="nauvis", dry_run=not apply))
        print(("placed " if apply else "dry run, would place ") + str(r.get("placed")), "failed", json.dumps(r.get("failed"))[:600])
        if apply:
            print(tools["run_lua"](CONFIG.replace("ROWSLUA", rows)))
