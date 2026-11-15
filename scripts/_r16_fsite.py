"""Fulgora site survey: silo and roboports, logistic network and its stock of the menu's ingredients, EM plants and pipes carrying electrolyte / holmium solution, power."""
from _game import tools

LUA = r'''
local s = game.surfaces.fulgora
local f = game.forces.player
local SN = {}
for k, v in pairs(defines.entity_status) do SN[v] = k end
local o = {}
local silo = s.find_entities_filtered{type = 'rocket-silo'}[1]
o[#o + 1] = 'silo ' .. (silo and (silo.position.x .. ',' .. silo.position.y .. ' ' .. tostring(SN[silo.status])) or 'none')
local rps = s.find_entities_filtered{name = 'roboport'}
local nets, seen = {}, {}
for _, rp in pairs(rps) do local n = rp.logistic_network if n and not seen[n.network_id] then seen[n.network_id] = true nets[#nets + 1] = n end end
o[#o + 1] = 'roboports ' .. #rps .. ', logistic networks ' .. #nets
for _, n in ipairs(nets) do o[#o + 1] = '  net cells ' .. #n.cells .. ' robots ' .. n.all_logistic_robots .. ' available ' .. n.available_logistic_robots end
local main = nets[1]
for _, n in ipairs(nets) do if #n.cells > #main.cells then main = n end end
local stock = {}
for _, it in pairs({'steel-plate', 'iron-gear-wheel', 'processing-unit', 'concrete', 'copper-cable', 'stone-brick', 'supercapacitor', 'superconductor', 'holmium-plate', 'battery', 'electronic-circuit', 'advanced-circuit', 'plastic-bar', 'accumulator', 'copper-plate', 'iron-plate', 'refined-concrete', 'power-armor-mk2', 'battery-mk2-equipment', 'personal-roboport-equipment', 'quality-module-2', 'lightning-rod', 'barrel', 'light-oil-barrel', 'sulfuric-acid-barrel'}) do
  stock[#stock + 1] = it .. '=' .. main.get_item_count(it)
end
o[#o + 1] = 'main network stock: ' .. table.concat(stock, ', ')
local em = s.find_entities_filtered{name = 'electromagnetic-plant'}
local emst = {}
for _, e in pairs(em) do
  local r = e.get_recipe()
  local k = (r and r.name or 'none') .. ':' .. tostring(SN[e.status])
  emst[k] = (emst[k] or 0) + 1
end
local parts = {}
for k, v in pairs(emst) do parts[#parts + 1] = v .. 'x ' .. k end
o[#o + 1] = 'EM plants ' .. #em .. ': ' .. table.concat(parts, ', ')
local fl = {}
for _, p in pairs(s.find_entities_filtered{type = {'pipe', 'pipe-to-ground', 'storage-tank'}}) do
  local ok, cont = pcall(function() return p.get_fluid_contents() end)
  if ok and cont then for n, v in pairs(cont) do fl[n] = (fl[n] or 0) + 1 end end
end
local fp = {}
for n, c in pairs(fl) do fp[#fp + 1] = n .. ' in ' .. c .. ' pipes/tanks' end
table.sort(fp)
o[#o + 1] = 'fluids in pipes: ' .. table.concat(fp, ', ')
local tanks = s.find_entities_filtered{type = 'storage-tank'}
local tk = {}
for _, t in pairs(tanks) do
  local c = t.get_fluid_contents()
  for n, v in pairs(c) do tk[#tk + 1] = n .. ' ' .. math.floor(v) .. ' @' .. string.format('%.0f,%.0f', t.position.x, t.position.y) if #tk >= 12 then break end end
  if #tk >= 12 then break end
end
o[#o + 1] = 'tanks: ' .. table.concat(tk, ' | ')
o[#o + 1] = 'substations ' .. #s.find_entities_filtered{name = 'substation'} .. ', accumulators ' .. #s.find_entities_filtered{name = 'accumulator'} .. ', lightning-rods ' .. #s.find_entities_filtered{name = 'lightning-rod'} .. ', lightning-collectors ' .. #s.find_entities_filtered{name = 'lightning-collector'}
rcon.print(table.concat(o, '\n'))
'''
if __name__ == "__main__":
    print(tools["run_lua"](LUA))
