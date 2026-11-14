from _game import tools
LUA = r'''
local o = {}
for i, p in pairs(game.forces.player.platforms) do
  if i >= 26 then
    local loc = p.space_location and (p.space_location.name or tostring(p.space_location)) or 'none'
    o[#o+1] = i .. ' ' .. p.name .. ' loc=' .. tostring(loc) .. ' state=' .. tostring(p.state) .. ' paused=' .. tostring(p.paused) .. ' ents=' .. #p.surface.find_entities()
  end
end
rcon.print(table.concat(o, '\n'))
'''
print(tools["run_lua"](LUA))
