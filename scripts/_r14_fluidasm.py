"""Design survey: the 10 'assembler recipe needs a fluid' items the Replicator cannot make, their recipes (solid + fluid ingredients, time),
whether each fluid has a barrel, and the fluid ports of assembling-machine-3."""
from _game import tools

LUA = r'''
local f = game.forces.player
local o = {}
local bar = {}
for name, r in pairs(f.recipes) do
  if name:find('^empty%-') and r.enabled and #r.ingredients == 1 then
    for _, p in pairs(r.products) do if p.type == 'fluid' then bar[p.name] = r.ingredients[1].name end end
  end
end
local fillbar = {}
for name, r in pairs(f.recipes) do
  if name:find('%-barrel$') and r.enabled then
    for _, i in pairs(r.ingredients) do if i.type == 'fluid' then fillbar[i.name] = name end end
  end
end
local want = {'concrete', 'refined-concrete', 'rocket-fuel', 'express-transport-belt', 'express-underground-belt', 'express-splitter', 'crude-oil-barrel', 'heavy-oil-barrel', 'processing-unit', 'electric-engine-unit'}
for _, it in ipairs(want) do
  local best = nil
  for name, r in pairs(f.recipes) do
    if r.enabled and #r.products == 1 and r.products[1].name == it and not r.prototype.hidden then best = r end
  end
  if best then
    local ing = {}
    for _, i in pairs(best.ingredients) do ing[#ing + 1] = i.type:sub(1, 1) .. ':' .. i.name .. 'x' .. i.amount .. (i.type == 'fluid' and (bar[i.name] and '[barrel ok]' or '[NO BARREL]') or '') end
    local cats = {}
    for _, c in pairs(best.prototype.categories) do cats[#cats + 1] = c end
    o[#o + 1] = it .. ' <- ' .. best.name .. ' (' .. table.concat(cats, '+') .. ', ' .. best.energy .. 's): ' .. table.concat(ing, ', ')
  else
    o[#o + 1] = it .. ' <- (no single-product enabled recipe found)'
  end
end
local am = prototypes.entity['assembling-machine-3']
for i, fb in pairs(am.fluidbox_prototypes) do
  local pcs = {}
  for _, pc in pairs(fb.pipe_connections) do pcs[#pcs + 1] = (pc.position and ('(' .. pc.position.x .. ',' .. pc.position.y .. ')') or (pc.positions and ('dirs ' .. #pc.positions) or '?')) end
  o[#o + 1] = 'AM3 fluidbox ' .. i .. ' ' .. fb.production_type .. ' ' .. table.concat(pcs, ' ')
end
o[#o + 1] = 'AM3 fluid_boxes_off_when_no_fluid_recipe=' .. tostring(am.fluid_boxes_off_when_no_fluid_recipe)
o[#o + 1] = 'barreled fluids: ' .. (function() local t = {} for k in pairs(bar) do t[#t + 1] = k end table.sort(t) return table.concat(t, ',') end)()
rcon.print(table.concat(o, '\n'))
'''
if __name__ == "__main__":
    print(tools["run_lua"](LUA))
