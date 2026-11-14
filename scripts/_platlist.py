from _game import tools
LUA = r'''
local o = {}
for i, p in pairs(game.forces.player.platforms) do
  local n = 0
  if p.surface then n = #p.surface.find_entities() end
  o[#o+1] = i .. ' idx ' .. p.name .. ' | surf=' .. (p.surface and p.surface.name or 'none') .. ' ents=' .. n .. ' state=' .. tostring(p.state) .. ' sched=' .. tostring(p.schedule and #p.schedule.records or 0)
end
rcon.print(table.concat(o, '\n'))
'''
print(tools["run_lua"](LUA))
