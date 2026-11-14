from _game import tools
LUA = r'''
local o = {}
local s = game.surfaces['fulgora']
for _, e in pairs(s.find_entities_filtered{type={'assembling-machine','chemical-plant','foundry'}}) do
  local r = e.get_recipe()
  local rn = r and r.name or 'none'
  if rn:find('electrolyte') or rn:find('holmium') or rn:find('electromagnetic') or rn:find('supercapacitor') or rn:find('superconductor') or rn:find('cracking') or rn:find('ice-melt') or rn:find('solution') or rn:find('separation') then
    local inv = e.get_inventory(defines.inventory.crafter_input)
    local have = {}
    if inv then for _, it in pairs(inv.get_contents()) do have[#have+1] = it.name:sub(1,12) .. '=' .. it.count end end
    local fl = {}
    local ok, fc = pcall(function() return e.get_fluid_contents() end)
    if ok and fc then for k, v in pairs(fc) do fl[#fl+1] = k:sub(1,14) .. '=' .. math.floor(v) end end
    o[#o+1] = e.name:sub(1,10) .. ' ' .. e.position.x .. ',' .. e.position.y .. ' ' .. rn .. ' st=' .. e.status .. ' items[' .. table.concat(have,' ') .. '] fluids[' .. table.concat(fl,' ') .. ']'
  end
end
rcon.print(table.concat(o, '\n'))
'''
print(tools["run_lua"](LUA))
