from _game import tools
LUA = r'''
local o = {}
local s = game.surfaces['gleba']
local r = prototypes.recipe['agricultural-science-pack']
local ing = {}
for _, i in pairs(r.ingredients) do ing[#ing+1] = i.name .. 'x' .. i.amount end
o[#o+1] = 'recipe: ' .. table.concat(ing, ' ') .. ' time=' .. r.energy
for _, e in pairs(s.find_entities_filtered{name={'biochamber'}, position={x=0,y=0}, radius=1000}) do
  local rc = e.get_recipe()
  local inv = e.get_inventory(defines.inventory.crafter_input)
  local have = {}
  if inv then for _, it in pairs(inv.get_contents()) do have[#have+1] = it.name:sub(1,10) .. '=' .. it.count end end
  o[#o+1] = e.position.x .. ',' .. e.position.y .. ' ' .. (rc and rc.name or 'none') .. ' st=' .. e.status .. ' in: ' .. table.concat(have, ' ')
end
rcon.print(table.concat(o, '\n'))
'''
print(tools["run_lua"](LUA))
