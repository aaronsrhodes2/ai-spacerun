"""Round 3: space-science-pack makers on Nauvis: status, recipe, and missing ingredients."""
from _game import tools

LUA = r'''
local s = game.surfaces.nauvis
local SN = {}
for k, v in pairs(defines.entity_status) do SN[v] = k end
local o = {}
for _, e in pairs(s.find_entities_filtered{type = 'assembling-machine'}) do
  local r = e.get_recipe()
  if r and r.name == 'space-science-pack' then
    local inv = e.get_inventory(defines.inventory.crafter_input)
    local miss = {}
    for _, ing in pairs(r.ingredients) do
      local have = inv and inv.get_item_count(ing.name) or 0
      if have < ing.amount then miss[#miss + 1] = ing.name .. '(' .. have .. '/' .. ing.amount .. ')' end
    end
    o[#o + 1] = 'SSP ' .. e.position.x .. ',' .. e.position.y .. ' ' .. tostring(SN[e.status]) .. ' short=' .. table.concat(miss, '+')
  end
end
if #o == 0 then o[1] = 'no space-science-pack makers on nauvis' end
rcon.print(table.concat(o, '\n'))
'''
if __name__ == "__main__":
    print(tools["run_lua"](LUA))
