"""Round 3: copper smelters on Nauvis, classed by what they hold (copper ore in source or copper plate in result), by status."""
from _game import tools

LUA = r'''
local s = game.surfaces.nauvis
local SN = {}
for k, v in pairs(defines.entity_status) do SN[v] = k end
local byst = {}
local samples = {}
local ore_stock = 0
for _, e in pairs(s.find_entities_filtered{type = 'furnace'}) do
  local src = e.get_inventory(defines.inventory.crafter_input)
  local res = e.get_inventory(defines.inventory.crafter_output)
  local so = src and src.get_item_count('copper-ore') or 0
  local ro = res and res.get_item_count('copper-plate') or 0
  if so > 0 or ro > 0 then
    local st = tostring(SN[e.status])
    byst[st] = (byst[st] or 0) + 1
    if st ~= 'working' and #samples < 12 then
      samples[#samples + 1] = 'CUF ' .. e.position.x .. ',' .. e.position.y .. ' ' .. st .. ' ore=' .. so .. ' plate=' .. ro
    end
  end
end
local o = {}
for k, v in pairs(byst) do o[#o + 1] = 'CUSTATUS ' .. k .. ' ' .. v end
for _, x in ipairs(samples) do o[#o + 1] = x end
for _, c in pairs(s.find_entities_filtered{type = {'container', 'logistic-container'}}) do
  local inv = c.get_inventory(defines.inventory.chest)
  if inv then ore_stock = ore_stock + inv.get_item_count('copper-ore') end
end
o[#o + 1] = 'COPPER_ORE_IN_CHESTS ' .. ore_stock
rcon.print(table.concat(o, '\n'))
'''

if __name__ == "__main__":
    print(tools["run_lua"](LUA))
