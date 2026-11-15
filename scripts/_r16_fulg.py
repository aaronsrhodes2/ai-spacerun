"""Fulgora Replicator survey: for each menu item, the enabled recipe, its crafting categories, ingredients (solid/fluid, barrel-able?), and which machine types can run it."""
from _game import tools

ITEMS = ["holmium-plate", "lightning-rod", "recycler", "electromagnetic-science-pack", "lightning-collector", "supercapacitor", "superconductor",
         "tesla-ammo", "tesla-turret", "teslagun", "battery-mk3-equipment", "mech-armor", "personal-roboport-mk2-equipment", "electromagnetic-plant",
         "quality-module-3", "processing-unit", "holmium-ore", "ice"]

LUA = r'''
local f = game.forces.player
local want = WANT
local bar = {}
for name, r in pairs(f.recipes) do
  if name:find('^empty%-') and r.enabled and #r.ingredients == 1 then
    for _, p in pairs(r.products) do if p.type == 'fluid' then bar[p.name] = true end end
  end
end
local machines = {'assembling-machine-3', 'electromagnetic-plant', 'foundry', 'chemical-plant', 'recycler', 'biochamber', 'cryogenic-plant'}
local function can(mn, p)
  local e = prototypes.entity[mn]
  if not e or not e.crafting_categories then return false end
  for _, c in pairs(p.categories) do if e.crafting_categories[c] then return true end end
  return false
end
local o = {}
for _, it in ipairs(want) do
  local found = {}
  for name, r in pairs(f.recipes) do
    if r.enabled and not r.prototype.hidden then
      for _, p in pairs(r.products) do
        if p.name == it and not name:find('recycling') or (p.name == it and name == 'scrap-recycling') then found[#found + 1] = r end
      end
    end
  end
  if #found == 0 then o[#o + 1] = it .. ': NO ENABLED RECIPE' end
  for _, r in ipairs(found) do
    local ing = {}
    for _, i in pairs(r.ingredients) do ing[#ing + 1] = (i.type == 'fluid' and ('FLUID ' .. i.name .. (bar[i.name] and '[barrel]' or '[NO barrel]')) or i.name) .. 'x' .. i.amount end
    local cats = {}
    for _, c in pairs(r.prototype.categories) do cats[#cats + 1] = c end
    local ms = {}
    for _, mn in ipairs(machines) do if can(mn, r.prototype) then ms[#ms + 1] = mn end end
    local prods = {}
    for _, p in pairs(r.products) do prods[#prods + 1] = p.name end
    o[#o + 1] = it .. ' <- ' .. r.name .. ' [' .. table.concat(cats, '+') .. '] machines: ' .. table.concat(ms, ',') .. ' | ' .. table.concat(ing, ', ') .. ' | makes ' .. table.concat(prods, ',')
  end
end
rcon.print(table.concat(o, '\n'))
'''.replace("WANT", "{" + ",".join(f"'{i}'" for i in ITEMS) + "}")

if __name__ == "__main__":
    print(tools["run_lua"](LUA))
