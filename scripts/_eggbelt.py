from _game import tools
LUA = r'''
local o = {}
local s = game.surfaces['gleba']
for x = 60, 90 do
  local b = s.find_entities_filtered{position={x+0.5,17.5}, radius=0.4}
  local t = {}
  for _, e in pairs(b) do t[#t+1] = e.name .. '(d' .. e.direction .. ')' end
  local tl1 = nil
  if #b > 0 and b[1].get_transport_line then
    local ok, l1 = pcall(function() return b[1].get_transport_line(1) end)
    local ok2, l2 = pcall(function() return b[1].get_transport_line(2) end)
    tl1 = (ok and l1 and l1.get_item_count() or '-') .. '/' .. (ok2 and l2 and l2.get_item_count() or '-')
  end
  o[#o+1] = x .. ': ' .. (#t>0 and table.concat(t,' ') or 'NOTHING') .. ' items=' .. tostring(tl1)
end
local tw = s.find_entities_filtered{name='heating-tower', position={61.5,17.5}, radius=1.5}[1]
if tw then local inv = tw.get_inventory(defines.inventory.fuel); o[#o+1] = 'tower fuel: ' .. (inv and table.concat({}, '') or '') .. tostring(inv and inv.get_contents()[1] and inv.get_contents()[1].name) .. ' status=' .. tw.status .. ' temp=' .. tostring(tw.temperature) end
rcon.print(table.concat(o, '\n'))
'''
print(tools["run_lua"](LUA))
