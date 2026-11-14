from _game import tools
LUA = r'''
local o = {}
local f = game.forces.player
for i, p in pairs(f.platforms) do
  if i >= 26 and i <= 31 and #p.surface.find_entities() == 1 then
    local ok, r = pcall(function() return p.destroy(60) end)
    o[#o+1] = i .. ' ' .. p.name .. ' ok=' .. tostring(ok) .. ' r=' .. tostring(r)
  end
end
rcon.print(table.concat(o, '\n'))
'''
print(tools["run_lua"](LUA))
