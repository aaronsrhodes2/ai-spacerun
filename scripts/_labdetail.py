from _game import tools
LUA = r'''
local o = {}
local f = game.forces.player
local t = f.technologies['plastic-bar-productivity']
local ing = {}
for _, i in pairs(t.prototype.research_unit_ingredients) do ing[#ing+1] = i.name .. 'x' .. i.amount end
o[#o+1] = 'tech ingredients: ' .. table.concat(ing, ' ') .. ' units=' .. t.prototype.research_unit_count .. ' time=' .. t.prototype.research_unit_energy
local s = game.surfaces['gleba']
for _, e in pairs(s.find_entities_filtered{type = 'lab'}) do
  local inv = e.get_inventory(defines.inventory.lab_input)
  local have = {}
  for _, it in pairs(inv.get_contents()) do have[#have+1] = it.name:sub(1,6) .. '=' .. it.count end
  o[#o+1] = e.position.x .. ',' .. e.position.y .. ' st=' .. e.status .. ' ' .. table.concat(have, ' ')
end
rcon.print(table.concat(o, '\n'))
'''
print(tools["run_lua"](LUA))
