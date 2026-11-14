"""Round 11: sample the Copper Depot train every 6 s for ~4 min: state, position, copper plate aboard, plate in the 24 depot smelters' outputs. Writes _r11_sample.log."""
import time

from _game import tools

LUA = r'''
local s = game.surfaces.nauvis
local o = {}
for _, t in pairs(game.train_manager.get_trains{surface = s}) do
  local sch = t.schedule
  local is = false
  if sch and sch.records then
    for _, r in pairs(sch.records) do if string.find(tostring(r.station), 'Copper Depot') then is = true end end
  end
  if is then
    local cargo = 0
    for _, c in pairs(t.carriages) do if c.type == 'cargo-wagon' then cargo = cargo + c.get_item_count('copper-plate') end end
    local p = t.front_stock.position
    o[#o + 1] = 'state=' .. tostring(t.state) .. ' cur=' .. tostring(sch.current) .. ' pos=' .. string.format('%.0f,%.0f', p.x, p.y) .. ' cargo=' .. cargo
  end
end
local plates, n, full = 0, 0, 0
for _, e in pairs(s.find_entities_filtered{type = 'furnace', area = {{128, -310}, {165, -292}}}) do
  local res = e.get_inventory(defines.inventory.crafter_output)
  if res and res.get_item_count('copper-plate') > 0 then
    n = n + 1
    plates = plates + res.get_item_count('copper-plate')
    if e.status == defines.entity_status.full_output then full = full + 1 end
  end
end
o[#o + 1] = 'depot smelters ' .. n .. ' full ' .. full .. ' plate_in_outputs ' .. plates
rcon.print(table.concat(o, ' | '))
'''
with open("_r11_sample.log", "w") as f:
    for i in range(40):
        f.write(f"{i*6:4d}s  {tools['run_lua'](LUA)}\n")
        f.flush()
        time.sleep(6)
