"""Round 3 survey: copper-cable makers on Nauvis, their status and inputs, and copper-plate furnaces."""
from _game import tools

LUA = r'''
local s = game.surfaces.nauvis
local SN = {}
for k, v in pairs(defines.entity_status) do SN[v] = k end
local o = {}
for _, e in pairs(s.find_entities_filtered{type = 'assembling-machine'}) do
  local r = e.get_recipe()
  if r and r.name == 'copper-cable' then
    local inv = e.get_inventory(defines.inventory.crafter_input)
    local out = e.get_inventory(defines.inventory.crafter_output)
    local cu = inv and inv.get_item_count('copper-plate') or 0
    local oc = out and out.get_item_count('copper-cable') or 0
    o[#o + 1] = 'CABLE ' .. e.position.x .. ',' .. e.position.y .. ' ' .. tostring(SN[e.status]) .. ' cu=' .. cu .. ' out=' .. oc
  end
end
local cnt = {}
for _, e in pairs(s.find_entities_filtered{type = 'furnace'}) do
  local ok, r = pcall(function() return e.previous_recipe end)
  local nm = ok and r and (type(r) == 'userdata' and r.name or r) or 'none'
  if nm == 'copper-plate' then
    local key = tostring(SN[e.status])
    cnt[key] = (cnt[key] or 0) + 1
  end
end
for k, v in pairs(cnt) do o[#o + 1] = 'CUFURNACE ' .. k .. ' ' .. v end
rcon.print(table.concat(o, '\n'))
'''

if __name__ == "__main__":
    print(tools["run_lua"](LUA))
