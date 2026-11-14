"""Round 9: Nauvis smelters classed by what they hold (iron-ore / copper-ore / iron-plate for steel, or their plate output), grouped by 50-tile area and status."""
from _game import tools

LUA = r'''
local s = game.surfaces.nauvis
local SN = {}
for k, v in pairs(defines.entity_status) do SN[v] = k end
local g, first = {}, {}
for _, e in pairs(s.find_entities_filtered{type = 'furnace'}) do
  local src = e.get_inventory(defines.inventory.crafter_input)
  local res = e.get_inventory(defines.inventory.crafter_output)
  local kind = nil
  if src then
    if src.get_item_count('iron-ore') > 0 then kind = 'iron' elseif src.get_item_count('copper-ore') > 0 then kind = 'copper'
    elseif src.get_item_count('iron-plate') > 0 then kind = 'steel' end
  end
  if not kind and res then
    if res.get_item_count('iron-plate') > 0 then kind = 'iron' elseif res.get_item_count('copper-plate') > 0 then kind = 'copper'
    elseif res.get_item_count('steel-plate') > 0 then kind = 'steel' end
  end
  if kind then
    local area = math.floor(e.position.x / 100) * 100 .. ',' .. math.floor(e.position.y / 100) * 100
    local k = kind .. ' @' .. area .. ' ' .. tostring(SN[e.status])
    g[k] = (g[k] or 0) + 1
    first[k] = first[k] or (e.position.x .. ',' .. e.position.y)
  end
end
local o = {}
for k, v in pairs(g) do o[#o + 1] = v .. 'x ' .. k .. ' e.g. ' .. first[k] end
table.sort(o)
rcon.print(table.concat(o, '\n'))
'''
if __name__ == "__main__":
    print(tools["run_lua"](LUA))
