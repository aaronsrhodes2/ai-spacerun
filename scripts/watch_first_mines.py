"""Sample the first mines over time: are drills fuelled and is ore reaching the hub?"""
import json
import sys
import time

from _game import tools

LUA = """
local s = game.surfaces.nauvis
local status = {}
for k, v in pairs(defines.entity_status) do status[v] = k end
local out = {tick=game.tick, online=#game.connected_players, patches={}, hub={}}
local function ore_of(e)
  local r = s.find_entities_filtered{type='resource', area=e.bounding_box, limit=1}[1]
  return r and r.name or 'none'
end
for _, e in pairs(s.find_entities_filtered{force='player', type='mining-drill'}) do
  local p = ore_of(e)
  local row = out.patches[p] or {drills=0, statuses={}, min_fuel=999, fuel=0}
  out.patches[p] = row
  row.drills = row.drills + 1
  local st = status[e.status] or '?'
  row.statuses[st] = (row.statuses[st] or 0) + 1
  local c = e.get_fuel_inventory().get_item_count('coal')
  row.fuel = row.fuel + c
  row.min_fuel = math.min(row.min_fuel, c)
end
local ins = {statuses={}, min_fuel=999}
for _, e in pairs(s.find_entities_filtered{force='player', name='burner-inserter'}) do
  local st = status[e.status] or '?'
  ins.statuses[st] = (ins.statuses[st] or 0) + 1
  ins.min_fuel = math.min(ins.min_fuel, e.get_fuel_inventory().get_item_count('coal') )
end
out.inserters = ins
for name, pos in pairs({iron={-20,-64}, coal={-18,-62}, copper={-22,-62}, stone={-20,-60}}) do
  local b = s.find_entity('transport-belt', {pos[1]+0.5, pos[2]+0.5})
  local items = {}
  if b then
    for i = 1, 2 do
      for _, c in pairs(b.get_transport_line(i).get_contents()) do items[c.name] = (items[c.name] or 0) + c.count end
    end
  end
  out.hub[name] = items
end
rcon.print(helpers.table_to_json(out))
""".replace("\n", " ")

minutes = int(sys.argv[1]) if len(sys.argv) > 1 else 10
for i in range(minutes + 1):
    print(tools["run_lua"](LUA), flush=True)
    if i < minutes:
        time.sleep(60)
