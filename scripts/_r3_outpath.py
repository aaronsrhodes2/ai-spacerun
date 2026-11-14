"""Round 3: what takes copper plate away from the full-output copper smelters: inserters and containers near them, with status."""
from _game import tools

LUA = r'''
local s = game.surfaces.nauvis
local SN = {}
for k, v in pairs(defines.entity_status) do SN[v] = k end
local o = {}
local seen = 0
local ins_st = {}
for _, f in pairs(s.find_entities_filtered{type = 'furnace', area = {{120, -310}, {160, -292}}}) do
  if f.status == defines.entity_status.full_output then
    seen = seen + 1
    for _, i in pairs(s.find_entities_filtered{type = 'inserter', position = f.position, radius = 3}) do
      local k = tostring(SN[i.status]) .. ' pickup=' .. i.pickup_position.x .. ',' .. i.pickup_position.y .. ' drop=' .. i.drop_position.x .. ',' .. i.drop_position.y
      ins_st[k] = (ins_st[k] or 0) + 1
    end
  end
end
o[#o + 1] = 'full furnaces in box: ' .. seen
for k, v in pairs(ins_st) do o[#o + 1] = 'INS ' .. v .. 'x ' .. k end
for _, c in pairs(s.find_entities_filtered{type = {'container', 'logistic-container'}, area = {{110, -320}, {170, -285}}}) do
  local inv = c.get_inventory(defines.inventory.chest)
  o[#o + 1] = 'CHEST ' .. c.position.x .. ',' .. c.position.y .. ' cu_plate=' .. (inv and inv.get_item_count('copper-plate') or 0) .. ' slots_free=' .. (inv and #inv - inv.count_empty_stacks() or -1)
end
rcon.print(table.concat(o, '\n'))
'''
if __name__ == "__main__":
    print(tools["run_lua"](LUA))
