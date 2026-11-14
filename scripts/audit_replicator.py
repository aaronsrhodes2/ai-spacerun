#!/usr/bin/env python3
"""Audit of the Replicator (the make-anything block: scripts/omni_maker.py site `replicator` + scripts/omni_fluid.py --site replicator).
Question: can it create every item the game offers that Nauvis can make from its own resources with the recipes researched?
READ-ONLY: nothing is placed, removed, ordered or configured. Writes docs/replicator-audit.md.

Part 1, coverage (static, from the game's own recipes):
  biome   closure of Nauvis raw inputs (iron/copper/uranium ore, coal, stone, wood, raw fish, crude oil, water) under every ENABLED recipe
  rules   the same selection rules the Replicator's config uses, mirrored from omni_maker.py (assembler list, furnace list) and omni_fluid.py (LIST)
  result  every biome item is covered by a unit or listed with the reason it is not
Part 2, the live build (is what stands wired for what is covered?):
  recipe tables  the decider at every table slot must name the item it should (a recipe enabled since the last `config` shifts the list and
                 leaves the table stale)
  units          machines, chests and combinators exist, are powered, and the demand roboport is in the logistic network
  stock          raw stock the units draw on (it can only transform what the network holds)

Usage: scripts/audit_replicator.py [--no-write]"""
import json
import sys
from pathlib import Path

import omni_fluid
import omni_maker
from _game import tools

ROOT = Path(__file__).resolve().parent.parent

RAW = ["iron-ore", "copper-ore", "uranium-ore", "coal", "stone", "wood", "raw-fish", "crude-oil", "water"]

ANALYSIS = r'''
local f = game.forces.player
local am3 = prototypes.entity['assembling-machine-3'].crafting_categories
local fur = prototypes.entity['electric-furnace'].crafting_categories
local raw = {RAWSET}
local function has_cat(p, set) for _, c in pairs(p.categories) do if set[c] then return true end end return false end
local function is_chem(p) for _, c in pairs(p.categories) do if c:find('chemistry') then return true end end return false end
local function is_recycling(p) for _, c in pairs(p.categories) do if c:find('recycling') then return true end end return false end
local function cats(p) local t = {} for _, c in pairs(p.categories) do t[#t + 1] = c end return table.concat(t, '+') end
local feas = {}
for k in pairs(raw) do feas[k] = true end
local live = {}
for name, r in pairs(f.recipes) do
  local p = r.prototype
  if r.enabled and not p.hidden and not is_recycling(p) then live[#live + 1] = r end
end
local feasrec, changed, iter = {}, true, 0
while changed and iter < 80 do
  changed = false
  iter = iter + 1
  for _, r in ipairs(live) do
    if not feasrec[r.name] then
      local ok = true
      for _, i in ipairs(r.ingredients) do if not feas[i.name] then ok = false break end end
      if ok then
        feasrec[r.name] = true
        changed = true
        for _, pr in ipairs(r.products) do feas[pr.name] = true end
      end
    end
  end
end
local seen, list, makerrec = {}, {}, {}
for name, r in pairs(f.recipes) do
  local p = r.prototype
  if r.enabled and has_cat(p, am3) and not p.hidden and #r.products == 1 and r.products[1].type == 'item' and not name:find('science%-pack') and not name:find('recycling') then
    local solid = true
    for _, i in pairs(r.ingredients) do if i.type ~= 'item' then solid = false end end
    local it = r.products[1].name
    if solid then
      if seen[it] then seen[it] = 2 else seen[it] = 1 list[#list + 1] = it makerrec[it] = r end
    end
  end
end
local mk = {}
for _, it in pairs(list) do if seen[it] == 1 then mk[#mk + 1] = it end end
local smelt, srec = {}, {}
for name, r in pairs(f.recipes) do
  local p = r.prototype
  if r.enabled and has_cat(p, fur) and not p.hidden and #r.products == 1 and r.products[1].type == 'item' and #r.ingredients == 1 and r.ingredients[1].type == 'item' and not srec[r.products[1].name] then
    smelt[#smelt + 1] = r.products[1].name
    srec[r.products[1].name] = r
  end
end
local bar = {}
for name, r in pairs(f.recipes) do
  if name:find('^empty%-') and r.enabled and #r.ingredients == 1 then
    for _, p in pairs(r.products) do if p.type == 'fluid' then bar[p.name] = r.ingredients[1].name end end
  end
end
local fl, fseen = {}, {}
local names = {}
for name, _ in pairs(f.recipes) do names[#names + 1] = name end
table.sort(names)
for _, name in pairs(names) do
  local r = f.recipes[name]
  local pr = r.prototype
  if r.enabled and is_chem(pr) and not pr.hidden then
    local nfi, nfo, key, ok = 0, 0, nil, true
    local firstfo = nil
    for _, i in pairs(r.ingredients) do if i.type == 'fluid' then if bar[i.name] then nfi = nfi + 1 else ok = false end end end
    for _, p in pairs(r.products) do
      if p.type == 'fluid' then
        if bar[p.name] then nfo = nfo + 1 firstfo = firstfo or p.name else ok = false end
      elseif not key then key = p.name end
    end
    if not key and firstfo then key = bar[firstfo] end
    if ok and key and nfi <= 2 and nfo <= 2 and (nfi > 0 or nfo > 0) and not fseen[key] then fseen[key] = true fl[#fl + 1] = {name = name, key = key} end
  end
end
local covered = {}
for _, it in pairs(mk) do covered[it] = 'assembler' end
for _, it in pairs(smelt) do if not covered[it] then covered[it] = 'furnace' end end
for _, e in pairs(fl) do if not covered[e.key] then covered[e.key] = 'fluid unit' end end
local prod = {}
for _, r in ipairs(live) do
  if feasrec[r.name] then
    for _, pr in ipairs(r.products) do
      if pr.type == 'item' then
        prod[pr.name] = prod[pr.name] or {}
        table.insert(prod[pr.name], r)
      end
    end
  end
end
local depth_memo, visiting = {}, {}
local function depth(it)
  if depth_memo[it] then return depth_memo[it] end
  if not makerrec[it] or seen[it] ~= 1 or visiting[it] then return 0 end
  visiting[it] = true
  local d = 0
  for _, i in pairs(makerrec[it].ingredients) do d = math.max(d, depth(i.name)) end
  visiting[it] = nil
  depth_memo[it] = d + 1
  return d + 1
end
local out = {covered = {assembler = {}, furnace = {}, ['fluid unit'] = {}}, uncovered = {}, raw_items = {}, deep = {}, nfeas = 0}
for it, _ in pairs(feas) do
  local proto = prototypes.item[it]
  if proto and not proto.hidden then
    out.nfeas = out.nfeas + 1
    if raw[it] then
      out.raw_items[#out.raw_items + 1] = it
    elseif covered[it] then
      table.insert(out.covered[covered[it]], it)
      if covered[it] == 'assembler' and depth(it) > 3 then out.deep[#out.deep + 1] = it .. ' (' .. depth(it) .. ')' end
    elseif prod[it] then
      local reason
      local r = prod[it][1]
      local p = r.prototype
      if it:find('science%-pack') then reason = 'science pack (left out of the assembler list by design)'
      elseif seen[it] == 2 then reason = 'two or more assembler recipes (ambiguous, left out)'
      elseif #r.products > 1 then reason = 'recipe has several products (' .. r.name .. ')'
      elseif has_cat(p, am3) and not is_chem(p) then
        local fluid = false
        for _, i in pairs(r.ingredients) do if i.type == 'fluid' then fluid = true end end
        if fluid then reason = 'assembler recipe needs a fluid (' .. r.name .. ')' else reason = 'other assembler case (' .. r.name .. ')' end
      elseif is_chem(p) then reason = 'chemistry recipe whose fluid has no barrel or has more than 2 fluid ports (' .. r.name .. ')'
      else reason = 'needs a machine the Replicator lacks: ' .. cats(p) .. ' (' .. r.name .. ')' end
      out.uncovered[reason] = out.uncovered[reason] or {}
      table.insert(out.uncovered[reason], it)
    else
      out.uncovered['feasible but no live recipe produces it'] = out.uncovered['feasible but no live recipe produces it'] or {}
      table.insert(out.uncovered['feasible but no live recipe produces it'], it)
    end
  end
end
local outside, unres = {}, {}
local haveenabled = {}
for _, r in pairs(f.recipes) do
  if r.enabled and not r.prototype.hidden then for _, pr in ipairs(r.products) do haveenabled[pr.name] = true end end
end
for _, r in ipairs(live) do
  if not feasrec[r.name] then for _, pr in ipairs(r.products) do if pr.type == 'item' and not feas[pr.name] then outside[pr.name] = true end end end
end
for name, r in pairs(f.recipes) do
  if not r.enabled and not r.prototype.hidden and not is_recycling(r.prototype) then
    for _, pr in ipairs(r.products) do if pr.type == 'item' and not haveenabled[pr.name] then unres[pr.name] = true end end
  end
end
local function keys(t) local k = {} for n in pairs(t) do k[#k + 1] = n end table.sort(k) return k end
out.outside = keys(outside)
out.unresearched = keys(unres)
out.mk = mk
out.smelt = smelt
out.fluid = fl
for k, v in pairs(out.covered) do table.sort(v) end
for k, v in pairs(out.uncovered) do table.sort(v) end
table.sort(out.raw_items)
table.sort(out.deep)
rcon.print(helpers.table_to_json(out))
'''.replace("RAWSET", ",".join(f"['{r}']=true" for r in RAW))


def live_check(analysis):
    """Part 2: the build as it stands, against what the analysis says it should hold."""
    n = len(analysis["mk"])
    sl = omni_maker.rom_slots("replicator", n)
    fsl = omni_maker.furnace_slots("replicator", len(analysis["smelt"]))
    flsl = None
    omni_fluid.use("replicator")
    nfl = len(analysis["fluid"])
    flsl = omni_fluid.slots(nfl)
    flat = ",".join(f"{x},{y}" for x, y in sl)
    fflat = ",".join(f"{x},{y}" for x, y in fsl)
    flflat = ",".join(f"{x},{y}" for x, y in flsl)
    mk = "{" + ",".join(f"'{i}'" for i in analysis["mk"]) + "}"
    sm = "{" + ",".join(f"'{i}'" for i in analysis["smelt"]) + "}"
    fk = "{" + ",".join(f"'{e['key']}'" for e in analysis["fluid"]) + "}"
    lua = r'''
local s = game.surfaces.nauvis
local o = {}
local mk, sm, fk = MK, SM, FK
local P, FP, FLP = {PFLAT}, {FFLAT}, {FLFLAT}
local D = 3
local function dec_at(x, y) return s.find_entities_filtered{name = 'decider-combinator', position = {x + 0.5, y + 1}, radius = 0.3}[1] end
local function cond_name(d)
  local cb = d.get_control_behavior()
  local ok, params = pcall(function() return cb.parameters end)
  if not ok or not params or not params.conditions or not params.conditions[1] then return nil end
  local fs = params.conditions[1].first_signal
  return fs and fs.name or nil
end
local n = #mk
local present, wrong, missing = 0, 0, 0
local badex = {}
for u = 0, D - 1 do
  for i = 1, n do
    local idx = (u * n + i - 1) * 2 + 1
    local d = dec_at(P[idx], P[idx + 1])
    if not d then missing = missing + 1
    else
      present = present + 1
      local cn = cond_name(d)
      if cn ~= mk[i] then wrong = wrong + 1 if #badex < 6 then badex[#badex + 1] = 'slot ' .. i .. ' wants ' .. mk[i] .. ' has ' .. tostring(cn) end end
    end
  end
end
o[#o + 1] = 'ROM ' .. n .. ' items x ' .. D .. ' machines: present ' .. present .. ', missing ' .. missing .. ', naming the wrong item ' .. wrong .. (#badex > 0 and (' [' .. table.concat(badex, '; ') .. ']') or '')
local fp, fw, fm, fex = 0, 0, 0, {}
for i = 1, #sm do
  local d = dec_at(FP[2 * i - 1], FP[2 * i])
  if not d then fm = fm + 1 else fp = fp + 1 local cn = cond_name(d) if cn ~= sm[i] then fw = fw + 1 if #fex < 4 then fex[#fex + 1] = 'slot ' .. i .. ' wants ' .. sm[i] .. ' has ' .. tostring(cn) end end end
end
o[#o + 1] = 'FURNACE table ' .. #sm .. ' items: present ' .. fp .. ', missing ' .. fm .. ', wrong ' .. fw .. (#fex > 0 and (' [' .. table.concat(fex, '; ') .. ']') or '')
local lp, lw, lm, lex = 0, 0, 0, {}
for i = 1, #fk do
  for j = 0, 7 do
    local idx = (8 * (i - 1) + j) * 2 + 1
    local d = dec_at(FLP[idx], FLP[idx + 1])
    if not d then lm = lm + 1 else lp = lp + 1 end
  end
end
o[#o + 1] = 'FLUID table ' .. #fk .. ' recipes x 8 deciders: present ' .. lp .. ', missing ' .. lm
local SN = {}
for k, v in pairs(defines.entity_status) do SN[v] = k end
local function inbox(name, x1, y1, x2, y2) return s.find_entities_filtered{name = name, area = {{x1, y1}, {x2, y2}}} end
for k = 0, 2 do
  local am = s.find_entities_filtered{name = 'assembling-machine-3', position = {-351.5 + 7 * k, -221.5}, radius = 0.6}[1]
  if am then
    local r = am.get_recipe()
    o[#o + 1] = 'MAKER ' .. (k + 1) .. ': ' .. tostring(SN[am.status]) .. ', recipe ' .. (r and r.name or 'none') .. ', made ' .. am.products_finished .. ', quality ' .. tostring(am.quality.name)
  else
    o[#o + 1] = 'MAKER ' .. (k + 1) .. ': MISSING'
  end
end
local fu = s.find_entities_filtered{name = 'electric-furnace', position = {-328.5, -221.5}, radius = 0.6}[1]
o[#o + 1] = 'FURNACE UNIT: ' .. (fu and tostring(SN[fu.status]) or 'MISSING')
local cp = inbox('chemical-plant', -308, -232, -292, -216)[1]
o[#o + 1] = 'FLUID PLANT: ' .. (cp and tostring(SN[cp.status]) or 'MISSING') .. ', barrel machines ' .. #inbox('assembling-machine-3', -308, -232, -292, -216)
local rp = s.find_entities_filtered{name = 'roboport', position = {-352, -229}, radius = 0.6}[1]
local net = rp and rp.logistic_network
o[#o + 1] = 'DEMAND ROBOPORT: ' .. (rp and (tostring(SN[rp.status]) .. ', network ' .. (net and ('robots ' .. net.all_logistic_robots) or 'NONE')) or 'MISSING')
local cc = s.find_entities_filtered{name = 'constant-combinator', position = {-348.5, -224.5}, radius = 0.6}[1]
if cc then
  local cb = cc.get_control_behavior()
  local cnt = 0
  for si = 1, cb.sections_count do local sec = cb.get_section(si) if sec then for _, sl in pairs(sec.filters) do cnt = cnt + 1 end end end
  o[#o + 1] = 'ITEM LIST (constant combinator) holds ' .. cnt .. ' items; the audit counts ' .. n .. ' makeable'
else o[#o + 1] = 'ITEM LIST combinator MISSING' end
local stock = {}
if net then
  for _, it in pairs({'iron-plate', 'copper-plate', 'steel-plate', 'stone-brick', 'coal', 'plastic-bar', 'sulfur', 'iron-ore', 'copper-ore', 'stone', 'wood', 'uranium-ore', 'electronic-circuit', 'advanced-circuit', 'barrel'}) do
    stock[#stock + 1] = it .. '=' .. net.get_item_count(it)
  end
end
o[#o + 1] = 'STOCK ' .. table.concat(stock, ', ')
rcon.print(table.concat(o, '\n'))
'''.replace("MK", mk).replace("SM", sm).replace("FK", fk).replace("PFLAT", flat).replace("FFLAT", fflat).replace("FLFLAT", flflat)
    return tools["run_lua"](lua)


def report(a, live):
    cov = a["covered"]
    ncov = sum(len(v) for v in cov.values())
    lines = [f"# Replicator audit ({'read-only'}, game tick via RCON)", "",
             "Question: can the Replicator make every item that Nauvis can make from its own resources, with the recipes researched?", "",
             f"Biome inputs: {', '.join(RAW)}.", "",
             "## Coverage", "",
             f"- Items reachable from the biome with researched recipes: **{a['nfeas']}** ({len(a['raw_items'])} are raw inputs)",
             f"- Covered by the Replicator: **{ncov}** (assemblers {len(cov['assembler'])}, furnace unit {len(cov['furnace'])}, fluid unit {len(cov['fluid unit'])})",
             f"- Not covered, makeable elsewhere in the factory: **{sum(len(v) for v in a['uncovered'].values())}**", ""]
    lines.append("### Not covered, by reason")
    for reason, items in sorted(a["uncovered"].items(), key=lambda kv: -len(kv[1])):
        lines.append(f"- **{reason}**: {len(items)}: " + ", ".join(items))
    lines += ["", f"### Assembler items nested deeper than 3 levels ({len(a['deep'])})", ", ".join(a["deep"]) or "none", "",
              f"### Outside the biome: needs imports, {len(a['outside'])} items", ", ".join(a["outside"]) or "none", "",
              f"### Recipes not researched yet: {len(a['unresearched'])} items", ", ".join(a["unresearched"]) or "none", "",
              "## Live build", "", "```", live, "```", ""]
    return "\n".join(lines)


def main():
    a = json.loads(tools["run_lua"](ANALYSIS))
    live = live_check(a)
    text = report(a, live)
    print(text)
    if "--no-write" not in sys.argv:
        (ROOT / "docs" / "replicator-audit.md").write_text(text, encoding="utf-8")
        print("\nwritten docs/replicator-audit.md")


if __name__ == "__main__":
    main()
