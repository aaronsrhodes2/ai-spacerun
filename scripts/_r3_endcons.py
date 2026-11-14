"""Round 3: the consumers at the copper belt's dead end (fast inserters around 181-184,-294): status, pickup and drop targets, and what the drop target holds."""
from _game import tools

LUA = r'''
local s = game.surfaces.nauvis
local SN = {}
for k, v in pairs(defines.entity_status) do SN[v] = k end
local o = {}
for _, i in pairs(s.find_entities_filtered{type = 'inserter', area = {{178, -297}, {188, -292}}}) do
  local d = i.drop_target
  local dn = d and (d.name .. ' ' .. d.position.x .. ',' .. d.position.y) or 'none'
  local ds = ''
  if d and d.get_inventory and d.get_inventory(defines.inventory.chest) then
    local inv = d.get_inventory(defines.inventory.chest)
    ds = ' contents=' .. inv.get_item_count('copper-plate') .. ' cu-plate, free=' .. inv.count_empty_stacks()
  end
  o[#o + 1] = i.name .. ' ' .. i.position.x .. ',' .. i.position.y .. ' ' .. tostring(SN[i.status]) .. ' drop->' .. dn .. ds
end
for _, e in pairs(s.find_entities_filtered{area = {{178, -300}, {192, -288}}}) do
  if e.type ~= 'transport-belt' and e.type ~= 'inserter' then
    o[#o + 1] = 'other ' .. e.name .. ' ' .. e.position.x .. ',' .. e.position.y .. ' ' .. tostring(SN[e.status])
  end
end
rcon.print(table.concat(o, '\n'))
'''
if __name__ == "__main__":
    print(tools["run_lua"](LUA))
