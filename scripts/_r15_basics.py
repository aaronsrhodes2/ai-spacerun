"""Which solid ingredients the Replicator's recipes use most (assembler list, furnace unit, fluid unit, fluid-assembler unit), with network stock and
whether the Replicator can itself make that ingredient; plus free ground for a chest field near the makers."""
import json

from _game import tools

LUA = r'''
local f = game.forces.player
local s = game.surfaces.nauvis
local am3 = prototypes.entity['assembling-machine-3'].crafting_categories
local fur = prototypes.entity['electric-furnace'].crafting_categories
local function has_cat(p, set) for _, c in pairs(p.categories) do if set[c] then return true end end return false end
local function is_chem(p) for _, c in pairs(p.categories) do if c:find('chemistry') then return true end end return false end
local freq, uses = {}, {}
local seenp = {}
local covered = {}
local function count(r)
  for _, i in pairs(r.ingredients) do
    if i.type == 'item' then freq[i.name] = (freq[i.name] or 0) + 1 uses[i.name] = (uses[i.name] or 0) + i.amount end
  end
end
local plain = {}
for name, r in pairs(f.recipes) do
  local p = r.prototype
  if r.enabled and has_cat(p, am3) and not p.hidden and #r.products == 1 and r.products[1].type == 'item' and not name:find('science%-pack') and not name:find('recycling') then
    local solid = true
    for _, i in pairs(r.ingredients) do if i.type ~= 'item' then solid = false end end
    local it = r.products[1].name
    if solid then
      if seenp[it] then seenp[it] = 2 else seenp[it] = 1 plain[it] = r end
    end
  end
end
for it, r in pairs(plain) do if seenp[it] == 1 then covered[it] = true count(r) end end
local srec = {}
for name, r in pairs(f.recipes) do
  local p = r.prototype
  if r.enabled and has_cat(p, fur) and not p.hidden and #r.products == 1 and r.products[1].type == 'item' and #r.ingredients == 1 and r.ingredients[1].type == 'item' and not srec[r.products[1].name] then
    srec[r.products[1].name] = true covered[r.products[1].name] = true count(r)
  end
end
local rp = s.find_entities_filtered{name = 'roboport', position = {-352, -229}, radius = 0.6}[1]
local net = rp.logistic_network
local rows = {}
for n, c in pairs(freq) do rows[#rows + 1] = {n = n, c = c, u = uses[n]} end
table.sort(rows, function(a, b) if a.c ~= b.c then return a.c > b.c end return a.n < b.n end)
local o = {}
for i = 1, math.min(45, #rows) do
  local r = rows[i]
  o[#o + 1] = {name = r.n, recipes = r.c, per_batch = r.u, stock = net.get_item_count(r.n), covered = covered[r.n] or false}
end
rcon.print(helpers.table_to_json(o))
'''

FREE = r'''
local s = game.surfaces.nauvis
local f = game.forces.player
local ok = {}
for x = -372, -280 do
  for y = -238, -170 do
    ok[x .. ',' .. y] = s.can_place_entity{name = 'buffer-chest', position = {x + 0.5, y + 0.5}, force = f, build_check_type = defines.build_check_type.manual}
  end
end
local best = {}
for x = -372, -283 do
  for y = -238, -173 do
    local all = true
    for dx = 0, 4 do for dy = 0, 2 do if not ok[(x + dx) .. ',' .. (y + dy)] then all = false end end end
    if all then
      local d = math.sqrt((x + 2 - (-340)) ^ 2 + (y + 1 - (-224)) ^ 2)
      best[#best + 1] = {x = x, y = y, d = d}
    end
  end
end
table.sort(best, function(a, b) return a.d < b.d end)
local o = {}
for i = 1, math.min(10, #best) do o[#o + 1] = '5x3 free block at ' .. best[i].x .. ',' .. best[i].y .. ' (distance from the makers ' .. string.format('%.0f', best[i].d) .. ')' end
if #o == 0 then o[1] = 'no free 5x3 block in the scanned area' end
rcon.print(table.concat(o, '\n'))
'''

if __name__ == "__main__":
    rows = json.loads(tools["run_lua"](LUA))
    print(f"{'ingredient':26s} recipes  per-batch-units  network stock  replicator-makes-it")
    for r in rows:
        print(f"{r['name']:26s} {r['recipes']:5d}    {r['per_batch']:8d}        {r['stock']:9d}      {'yes' if r['covered'] else 'no'}")
    print()
    print(tools["run_lua"](FREE))
