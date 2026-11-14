from _game import tools
LUA = r'''
local o = {}
local s = game.surfaces['fulgora']
local names = {'electromagnetic-plant','electromagnetic-science-pack','assembling-machine-3','recycler','accumulator'}
local tally = {}
for _, e in pairs(s.find_entities_filtered{name='electromagnetic-plant'}) do
  local st = e.status
  tally['em-plant st=' .. tostring(st)] = (tally['em-plant st=' .. tostring(st)] or 0) + 1
end
for k, v in pairs(tally) do o[#o+1] = k .. ' x' .. v end
local r = prototypes.recipe['electromagnetic-science-pack']
local ing = {}
for _, i in pairs(r.ingredients) do ing[#ing+1] = i.name .. 'x' .. i.amount end
o[#o+1] = 'EM pack recipe: ' .. table.concat(ing, ' ')
local net = {}
for _, p in pairs(game.forces.player.platforms) do end
for _, sn in pairs({'fulgora'}) do
  local f = game.forces.player
  for _, it in pairs({'electromagnetic-plant','electromagnetic-science-pack','holmium-plate','superconductor','supercapacitor','battery','low-density-structure','accumulator','processing-unit','scrap'}) do
    local tot = 0
    for _, c in pairs(s.find_entities_filtered{type={'container','logistic-container'}}) do
      local inv = c.get_inventory(defines.inventory.chest)
      if inv then tot = tot + inv.get_item_count(it) end
    end
    o[#o+1] = it .. ' in chests on fulgora=' .. tot
  end
end
rcon.print(table.concat(o, '\n'))
'''
print(tools["run_lua"](LUA))
