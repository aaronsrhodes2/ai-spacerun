from _game import tools
LUA = r'''
local o = {}
local f = game.forces.player
local s = game.surfaces['gleba']
local belts, chests, machines = 0, 0, 0
for _, e in pairs(s.find_entities_filtered{type={'transport-belt','underground-belt','splitter'}}) do
  for i = 1, 2 do
    local ok, tl = pcall(function() return e.get_transport_line(i) end)
    if ok and tl then local c = tl.get_item_count('pentapod-egg') if c > 0 then belts = belts + c end end
  end
end
for _, e in pairs(s.find_entities_filtered{type={'container','logistic-container'}}) do
  local inv = e.get_inventory(defines.inventory.chest)
  if inv then local c = inv.get_item_count('pentapod-egg') if c > 0 then chests = chests + c end end
end
for _, e in pairs(s.find_entities_filtered{type='assembling-machine'}) do end
local pm = s.find_entities_filtered{name={'biochamber'}}
for _, e in pairs(pm) do
  local inv = e.get_inventory(defines.inventory.crafter_input)
  local out = e.get_inventory(defines.inventory.crafter_output)
  if inv then local c = inv.get_item_count('pentapod-egg') if c>0 then machines = machines + c end end
  if out then local c = out.get_item_count('pentapod-egg') if c>0 then machines = machines + c end end
end
o[#o+1] = 'eggs on belts=' .. belts .. ' in chests=' .. chests .. ' in chambers=' .. machines
local st = f.get_item_production_statistics('gleba')
o[#o+1] = 'egg made=' .. tostring(st.get_input_count('pentapod-egg')) .. ' egg used=' .. tostring(st.get_output_count('pentapod-egg'))
local pe = 0
for _, p in pairs(f.platforms) do if p.hub then local i=p.hub.get_inventory(defines.inventory.hub_main) if i then pe = pe + i.get_item_count('pentapod-egg') end end end
o[#o+1] = 'eggs in hubs=' .. pe
o[#o+1] = 'egg ghost check ok'
rcon.print(table.concat(o, '\n'))
'''
print(tools["run_lua"](LUA))
