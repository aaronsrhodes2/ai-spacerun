#!/usr/bin/env python3
"""Fulgora electromagnetic science: one read-only status page. Changes nothing.

Answers "why are the pack plants idle" in the order that found the cause on 2026-11-14:
  1. demand   where the packs are (Fulgora network, every landing pad, every platform hub), Nauvis use per minute, lab states
  2. gate     the logistic conditions on inserters (the unload gate at y -106.5 is `packs < 6000`), the scrap train
  3. chain    every machine of the pack chain with status, items and fluids inside
  4. stock    what the base logistic network holds; made and used per minute on Fulgora
  5. power    accumulator charge on the base network

Reading it: plants in fluid_ingredient_shortage with the gate closed (packs >= 6000 in the network) is the factory resting, not a
fault: no scrap means no stone, so no electrolyte. The silo side of the gate is `fulgora_silo_gate.py status`.

Usage: fulgora_em_status.py"""
from _game import tools

LUA = r'''
local o = {}
local s = game.surfaces['fulgora']
local f = game.forces.player
local E = defines.entity_status
local SN = {}
for k, v in pairs(E) do SN[v] = k end
local PACK = 'electromagnetic-science-pack'
o[#o + 1] = '== demand'
for _, sn in pairs({'nauvis', 'fulgora', 'gleba', 'vulcanus', 'aquilo'}) do
  local su = game.surfaces[sn]
  if su then
    local tot, pads = 0, 0
    for _, n in pairs(f.logistic_networks[sn] or {}) do tot = tot + n.get_item_count(PACK) end
    for _, pad in pairs(su.find_entities_filtered{type = 'cargo-landing-pad'}) do pads = pads + pad.get_item_count(PACK) end
    o[#o + 1] = sn .. ' packs in networks=' .. tot .. ' of which on pads=' .. pads
  end
end
for _, p in pairs(f.platforms) do
  local hub = p.hub
  if hub and hub.valid then
    local n = hub.get_item_count(PACK)
    if n > 0 or p.name:find('Fulgora') then o[#o + 1] = 'platform ' .. p.index .. ' ' .. p.name .. ' at=' .. (p.space_location and p.space_location.name or 'transit') .. ' packs=' .. n end
  end
end
local pn = f.get_item_production_statistics(game.surfaces.nauvis)
o[#o + 1] = 'nauvis packs used/min: 1h=' .. string.format('%.1f', pn.get_flow_count{name = PACK, category = 'output', precision_index = defines.flow_precision_index.one_hour}) .. ' 10h=' .. string.format('%.1f', pn.get_flow_count{name = PACK, category = 'output', precision_index = defines.flow_precision_index.ten_hours})
local labs = {}
for _, l in pairs(game.surfaces.nauvis.find_entities_filtered{type = 'lab'}) do local k = SN[l.status] or l.status labs[k] = (labs[k] or 0) + 1 end
for k, v in pairs(labs) do o[#o + 1] = 'nauvis labs ' .. k .. ' x' .. v end
o[#o + 1] = '== gate'
local seen = {}
for _, e in pairs(s.find_entities_filtered{type = 'inserter'}) do
  local cb = e.get_control_behavior()
  if cb and cb.connect_to_logistic_network then
    local c = cb.logistic_condition
    local k = (c and c.first_signal and c.first_signal.name or '?') .. ' ' .. (c and c.comparator or '?') .. ' ' .. (c and c.constant or '?') .. ' at y=' .. e.position.y .. ' ' .. (SN[e.status] or e.status)
    seen[k] = (seen[k] or 0) + 1
  end
end
for k, v in pairs(seen) do o[#o + 1] = v .. 'x inserter runs while ' .. k end
local trains = {}
for _, t in pairs(s.find_entities_filtered{type = 'locomotive'}) do
  local tr = t.train
  if not trains[tr.id] then
    trains[tr.id] = true
    o[#o + 1] = 'train ' .. tr.id .. ' state=' .. tr.state .. ' station=' .. (tr.station and tr.station.backer_name or '-') .. ' scrap=' .. tr.get_item_count('scrap')
  end
end
o[#o + 1] = '== chain'
for _, rn in pairs({'electromagnetic-science-pack', 'electrolyte', 'holmium-solution', 'supercapacitor'}) do
  local ing = {}
  for _, i in pairs(prototypes.recipe[rn].ingredients) do ing[#ing + 1] = i.name .. 'x' .. i.amount end
  o[#o + 1] = 'recipe ' .. rn .. ': ' .. table.concat(ing, ' ')
end
local t = {}
for _, e in pairs(s.find_entities_filtered{type = {'assembling-machine', 'recycler', 'mining-drill'}}) do
  local rn = e.type
  if e.type == 'assembling-machine' then local r = e.get_recipe() rn = r and r.name or 'none' end
  local k = rn .. ' ' .. (SN[e.status] or e.status)
  t[k] = (t[k] or 0) + 1
  if rn == 'electromagnetic-science-pack' or rn == 'electrolyte' or rn == 'holmium-solution' or rn == 'supercapacitor' then
    local have, fl = {}, {}
    local inv = e.get_inventory(defines.inventory.crafter_input)
    if inv then for _, it in pairs(inv.get_contents()) do have[#have + 1] = it.name .. '=' .. it.count end end
    for k2, v in pairs(e.get_fluid_contents()) do fl[#fl + 1] = k2 .. '=' .. math.floor(v) end
    o[#o + 1] = rn .. ' ' .. e.position.x .. ',' .. e.position.y .. ' ' .. (SN[e.status] or e.status) .. ' items[' .. table.concat(have, ' ') .. '] fluids[' .. table.concat(fl, ' ') .. ']'
  end
end
o[#o + 1] = '== machine states'
for k, v in pairs(t) do o[#o + 1] = v .. 'x ' .. k end
o[#o + 1] = '== stock (base network) and flows'
local n = s.find_logistic_network_by_position({150, -146}, 'player')
if n then
  local c = {}
  for _, w in pairs({PACK, 'scrap', 'stone', 'ice', 'holmium-ore', 'holmium-plate', 'battery', 'accumulator', 'supercapacitor', 'superconductor', 'solid-fuel', 'rocket-fuel', 'low-density-structure', 'processing-unit', 'steel-plate', 'copper-cable'}) do c[#c + 1] = w .. '=' .. n.get_item_count(w) end
  o[#o + 1] = table.concat(c, ' ')
  o[#o + 1] = 'robots ' .. n.all_logistic_robots .. ' idle ' .. n.available_logistic_robots
end
local ps = f.get_item_production_statistics(s)
for _, w in pairs({PACK, 'scrap', 'stone', 'holmium-ore', 'battery', 'steel-plate'}) do
  local function fl(cat, pi) return string.format('%.1f', ps.get_flow_count{name = w, category = cat, precision_index = pi}) end
  o[#o + 1] = w .. ' made/min 10m=' .. fl('input', defines.flow_precision_index.ten_minutes) .. ' 1h=' .. fl('input', defines.flow_precision_index.one_hour) .. ' used/min 1h=' .. fl('output', defines.flow_precision_index.one_hour)
end
o[#o + 1] = '== power'
local p = s.find_entities_filtered{type = 'electric-pole', position = {160, -140}, radius = 1}[1]
if p then
  local acc, cap = 0, 0
  for _, a in pairs(s.find_entities_filtered{type = 'accumulator'}) do if a.electric_network_id == p.electric_network_id then acc = acc + a.energy cap = cap + a.electric_buffer_size end end
  o[#o + 1] = 'base accumulators MJ ' .. math.floor(acc / 1e6) .. ' of ' .. math.floor(cap / 1e6)
end
rcon.print(table.concat(o, '\n'))
'''

if __name__ == "__main__":
    print(tools["run_lua"](LUA))
