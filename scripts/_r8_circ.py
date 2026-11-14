"""Round 8: electronic-circuit makers on Nauvis grouped by area and status, with the missing ingredient, plus where circuits are consumed."""
from _game import tools

LUA = r'''
local s = game.surfaces.nauvis
local SN = {}
for k, v in pairs(defines.entity_status) do SN[v] = k end
local groups = {}
local firstpos = {}
local total = 0
for _, e in pairs(s.find_entities_filtered{type = 'assembling-machine'}) do
  local r = e.get_recipe()
  if r and r.name == 'electronic-circuit' then
    total = total + 1
    local inv = e.get_inventory(defines.inventory.crafter_input)
    local miss = {}
    for _, ing in pairs(r.ingredients) do
      local have = inv and inv.get_item_count(ing.name) or 0
      if have < ing.amount then miss[#miss + 1] = ing.name end
    end
    local area = math.floor(e.position.x / 50) * 50 .. ',' .. math.floor(e.position.y / 50) * 50
    local k = area .. ' ' .. tostring(SN[e.status]) .. ' miss=' .. table.concat(miss, '+')
    groups[k] = (groups[k] or 0) + 1
    firstpos[k] = firstpos[k] or (e.position.x .. ',' .. e.position.y)
  end
end
local o = {'electronic-circuit makers: ' .. total}
for k, v in pairs(groups) do o[#o + 1] = v .. 'x ' .. k .. ' e.g. ' .. firstpos[k] end
rcon.print(table.concat(o, '\n'))
'''
if __name__ == "__main__":
    print(tools["run_lua"](LUA))
