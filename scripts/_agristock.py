from _game import tools
LUA = r'''
local o = {}
local f = game.forces.player
local st = f.get_item_production_statistics('gleba')
o[#o+1] = 'gleba agri made(total)=' .. tostring(st.get_input_count('agricultural-science-pack')) .. ' used=' .. tostring(st.get_output_count('agricultural-science-pack'))
for _, sn in pairs({'gleba','nauvis'}) do
  local s = game.surfaces[sn]
  local tot = 0
  local where = {}
  for _, e in pairs(s.find_entities_filtered{type={'container','logistic-container'}}) do
    local inv = e.get_inventory(defines.inventory.chest)
    if inv then
      local c = inv.get_item_count('agricultural-science-pack')
      if c > 0 then tot = tot + c; if #where < 8 then where[#where+1] = e.name .. '@' .. e.position.x .. ',' .. e.position.y .. '=' .. c end end
    end
  end
  o[#o+1] = sn .. ' agri in chests=' .. tot .. ' : ' .. table.concat(where, ' ')
  local asm = {}
  for _, e in pairs(s.find_entities_filtered{name={'assembling-machine-1','assembling-machine-2','assembling-machine-3','biochamber'}}) do
    local r = e.get_recipe()
    if r and r.name == 'agricultural-science-pack' then
      asm[#asm+1] = e.position.x .. ',' .. e.position.y .. ' st=' .. e.status
    end
  end
  o[#o+1] = sn .. ' agri makers: ' .. #asm .. ' ' .. table.concat(asm, ' | ')
end
for _, p in pairs(f.platforms) do
  local h = p.hub
  if h then
    local c = h.get_inventory and h.get_inventory(defines.inventory.hub_main)
    local n = c and c.get_item_count('agricultural-science-pack') or 0
    if n > 0 then o[#o+1] = p.name .. ' hub holds agri=' .. n end
  end
end
rcon.print(table.concat(o, '\n'))
'''
print(tools["run_lua"](LUA))
