from _game import tools
LUA = r'''
local o = {}
local f = game.forces.player
for _, sn in pairs({'fulgora','nauvis'}) do
  local s = game.surfaces[sn]
  local tot, n = 0, 0
  for _, c in pairs(s.find_entities_filtered{type={'container','logistic-container'}}) do
    local inv = c.get_inventory(defines.inventory.chest)
    if inv then local k = inv.get_item_count('stone') if k > 0 then tot = tot + k; n = n + 1 end end
  end
  o[#o+1] = sn .. ' stone in chests=' .. tot .. ' in ' .. n .. ' chests'
end
local tot = 0
for _, p in pairs(f.platforms) do if p.hub then local i = p.hub.get_inventory(defines.inventory.hub_main) if i then tot = tot + i.get_item_count('stone') end end end
o[#o+1] = 'stone in platform hubs=' .. tot
local st = f.get_item_production_statistics('fulgora')
o[#o+1] = 'fulgora stone made=' .. tostring(st.get_input_count('stone')) .. ' used=' .. tostring(st.get_output_count('stone'))
local st2 = f.get_item_production_statistics('fulgora')
rcon.print(table.concat(o,'\n'))
'''
print(tools["run_lua"](LUA))
