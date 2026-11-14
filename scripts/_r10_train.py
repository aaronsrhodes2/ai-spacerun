"""Round 10: the Copper Depot train now (state, position, carriages, fuel in each locomotive), the straight-rail extent on y=-149, and chest stock of the fuel it burns."""
from _game import tools

LUA = r'''
local s = game.surfaces.nauvis
local o = {}
local fuels = {}
for _, t in pairs(game.train_manager.get_trains{surface = s}) do
  local sch = t.schedule
  local is = false
  if sch and sch.records then
    for _, r in pairs(sch.records) do if string.find(tostring(r.station), 'Copper Depot') then is = true end end
  end
  if is then
    o[#o + 1] = 'TRAIN state=' .. tostring(t.state) .. ' speed=' .. string.format('%.2f', t.speed) .. ' current=' .. tostring(sch.current)
    for i, c in pairs(t.carriages) do
      local fi = ''
      if c.type == 'locomotive' then
        local inv = c.get_fuel_inventory()
        local parts = {}
        if inv then for _, it in pairs(inv.get_contents()) do parts[#parts + 1] = it.name .. 'x' .. it.count; fuels[it.name] = true end end
        fi = ' fuel=' .. table.concat(parts, ',')
      end
      o[#o + 1] = '  car ' .. i .. ' ' .. c.name .. ' at ' .. string.format('%.1f,%.1f', c.position.x, c.position.y) .. ' ori=' .. string.format('%.2f', c.orientation) .. fi
    end
  end
end
local rails = {}
for _, r in pairs(s.find_entities_filtered{type = 'straight-rail', area = {{80, -150}, {180, -148}}}) do rails[#rails + 1] = r.position.x end
table.sort(rails)
o[#o + 1] = 'rails y=-149 x from ' .. (rails[1] or '?') .. ' to ' .. (rails[#rails] or '?') .. ' count ' .. #rails
for fname in pairs(fuels) do
  local n = 0
  for _, c in pairs(s.find_entities_filtered{type = {'container', 'logistic-container'}}) do
    local inv = c.get_inventory(defines.inventory.chest)
    if inv then n = n + inv.get_item_count(fname) end
  end
  o[#o + 1] = 'chest stock of ' .. fname .. ': ' .. n
end
local sig = #s.find_entities_filtered{type = {'rail-signal', 'rail-chain-signal'}, area = {{80, -155}, {180, -143}}}
o[#o + 1] = 'signals near the run: ' .. sig
rcon.print(table.concat(o, '\n'))
'''
if __name__ == "__main__":
    print(tools["run_lua"](LUA))
