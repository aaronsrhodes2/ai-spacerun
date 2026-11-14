"""Round 10: copper-cable makers on Nauvis by status and by what feeds them (pickup source type of nearby inserters); copper plate/cable stock in chests."""
from _game import tools

LUA = r'''
local s = game.surfaces.nauvis
local SN = {}
for k, v in pairs(defines.entity_status) do SN[v] = k end
local g = {}
local starved_pos = {}
for _, e in pairs(s.find_entities_filtered{type = 'assembling-machine'}) do
  local r = e.get_recipe()
  if r and r.name == 'copper-cable' then
    local st = tostring(SN[e.status])
    local feeds = {}
    for _, i in pairs(s.find_entities_filtered{type = 'inserter', position = e.position, radius = 3}) do
      local d = i.drop_target
      if d and d == e then
        local p = i.pickup_target
        feeds[#feeds + 1] = p and p.name or 'none'
      end
    end
    table.sort(feeds)
    local k = st .. ' <- ' .. table.concat(feeds, ',')
    g[k] = (g[k] or 0) + 1
    if st == 'item_ingredient_shortage' and #starved_pos < 6 then starved_pos[#starved_pos + 1] = e.position.x .. ',' .. e.position.y end
  end
end
local o = {}
for k, v in pairs(g) do o[#o + 1] = v .. 'x ' .. k end
table.sort(o)
local cu, cab = 0, 0
for _, c in pairs(s.find_entities_filtered{type = {'container', 'logistic-container'}}) do
  local inv = c.get_inventory(defines.inventory.chest)
  if inv then cu = cu + inv.get_item_count('copper-plate'); cab = cab + inv.get_item_count('copper-cable') end
end
o[#o + 1] = 'chest stock: copper-plate ' .. cu .. ', copper-cable ' .. cab
o[#o + 1] = 'starved samples: ' .. table.concat(starved_pos, ' | ')
rcon.print(table.concat(o, '\n'))
'''
if __name__ == "__main__":
    print(tools["run_lua"](LUA))
