#!/usr/bin/env python3
"""Direct-feed electronic-circuit cells (2026-11-15). The robot-fed ec cells (build_cells.py --kind ec) starve for copper cable: an epic circuit assembler burns ~47 cable/s
and a robot carries 4 items a trip, so their requester chests sat at 0-4 cable while 140-380k cable lay in the network. Here the cable never leaves its cell: each new
assembler stands directly east of a cable cell's output chest (the passive provider chest at x=-129.5 on rows -158.5, -149.5, -146.5, -143.5; the rows with the substation at
(-127,-154) are skipped) and an epic bulk inserter moves cable chest -> assembler. Iron plate still comes by robot (1 per circuit, 15/s a cell: it worked), circuits leave by robot.
Per row (yc), going east from the cable chest at x=-129.5:
  bulk inserter (-128.5,yc) [takes from the chest]  ->  epic AM3 electronic-circuit (-126.5,yc)  ->  bulk inserter (-124.5,yc) -> passive provider chest (-123.5,yc)
  requester chest (-123.5,yc-1) with 400 iron plate -> bulk inserter (-124.5,yc-1) -> machine
Everything epic. Usage: ec_direct_cells.py [--apply | --revert]   (default dry run)"""
import json
import sys

from _game import tools

Q = {"quality": "epic"}
ROWS = (-158.5, -149.5, -146.5, -143.5)
if "--rows" in sys.argv:                                 # other cable chests: --rows -167.5,-170.5,...
    ROWS = tuple(float(v) for v in sys.argv[sys.argv.index("--rows") + 1].split(","))
GROUP = "Feed: Electronic Circuit"


def ents():
    out = []
    for yc in ROWS:
        out += [
            {"name": "bulk-inserter", "x": -128.5, "y": yc, "direction": 12, "params": dict(Q)},            # pickup west (the cable chest), drop east
            {"name": "assembling-machine-3", "x": -126.5, "y": yc, "params": dict(Q)},
            {"name": "bulk-inserter", "x": -124.5, "y": yc, "direction": 12, "params": dict(Q)},            # machine -> output chest
            {"name": "passive-provider-chest", "x": -123.5, "y": yc, "params": {}},
            {"name": "bulk-inserter", "x": -124.5, "y": yc - 1, "direction": 4, "params": dict(Q)},        # pickup east (the iron chest), drop west into the machine
            {"name": "requester-chest", "x": -123.5, "y": yc - 1, "params": {}},
            {"name": "bulk-inserter", "x": -124.5, "y": yc + 1, "direction": 4, "params": dict(Q)},        # a second iron point: robots deliver per chest, one chest was not enough
            {"name": "requester-chest", "x": -123.5, "y": yc + 1, "params": {}},
        ]
    return out


CONFIG = r'''
local s = game.surfaces.nauvis
local n, m = 0, 0
for _, yc in ipairs(ROWSLUA) do
  local e = s.find_entities_filtered{name = 'assembling-machine-3', position = {-126.5, yc}, radius = 0.4}[1]
  if e then e.set_recipe('electronic-circuit') m = m + 1 end
  for _, dy in ipairs({-1, 1}) do
    local c = s.find_entities_filtered{name = 'requester-chest', position = {-123.5, yc + dy}, radius = 0.4}[1]
    if c and #c.get_logistic_sections().sections <= 1 and c.get_logistic_point(defines.logistic_member_index.logistic_container).sections_count <= 1 then
      local sec = c.get_logistic_sections().add_section() sec.set_slot(1, {value = {name = 'iron-plate', quality = 'normal'}, min = 400}) sec.group = 'GROUP' n = n + 1 end
  end
  local o = s.find_entities_filtered{name = 'passive-provider-chest', position = {-123.5, yc}, radius = 0.4}[1]
  if o then o.get_inventory(defines.inventory.chest).set_bar(5) end
end
rcon.print('machines ' .. m .. ', iron requests ' .. n)
'''

REVERT = r'''
local s = game.surfaces.nauvis
local n = 0
for _, yc in ipairs(ROWSLUA) do
  for _, e in pairs(s.find_entities_filtered{area = {{-129, yc - 1.6}, {-123, yc + 1.6}}}) do
    if e.name == 'assembling-machine-3' or e.name == 'bulk-inserter' or e.name == 'passive-provider-chest' or e.name == 'requester-chest' then e.destroy() n = n + 1 end
  end
end
rcon.print('removed ' .. n)
'''

if __name__ == "__main__":
    if "--revert" in sys.argv:
        print(tools["run_lua"](REVERT.replace("ROWSLUA", "{" + ",".join(str(v) for v in ROWS) + "}")))
    else:
        apply = "--apply" in sys.argv
        r = json.loads(tools["place_entities"](json.dumps(ents()), surface="nauvis", dry_run=not apply))
        print(("placed " if apply else "dry run, would place ") + str(r.get("placed")), "failed", json.dumps(r.get("failed"))[:800])
        if apply:
            print(tools["run_lua"](CONFIG.replace("GROUP", GROUP).replace("ROWSLUA", "{" + ",".join(str(v) for v in ROWS) + "}")))
