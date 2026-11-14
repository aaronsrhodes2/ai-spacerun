from _game import tools
LUA = r'''
local o = {}
local s = game.surfaces['gleba']
local function row(y, x0, x1)
  local t = {}
  for x = x0, x1, 4 do
    local b = s.find_entities_filtered{position={x+0.5,y}, radius=0.4}
    local n = '-'
    for _, e in pairs(b) do if e.type == 'transport-belt' or e.type=='underground-belt' then
      local a = e.get_transport_line(1).get_contents(); local c = e.get_transport_line(2).get_contents()
      local s1, s2 = 0, 0
      for _, it in pairs(a) do if it.name=='nutrients' then s1 = s1 + it.count end end
      for _, it in pairs(c) do if it.name=='nutrients' then s2 = s2 + it.count end end
      n = 'd' .. e.direction .. ':' .. s1 .. '/' .. s2
    end end
    t[#t+1] = x .. '=' .. n
  end
  return table.concat(t, ' ')
end
o[#o+1] = 'head row y9.5: ' .. row(9.5, 76, 123)
o[#o+1] = 'tail row y11.5: ' .. row(11.5, 67, 123)
o[#o+1] = 'fruit row y2.5: ' .. row(2.5, 74, 122)
rcon.print(table.concat(o, '\n'))
'''
print(tools["run_lua"](LUA))
