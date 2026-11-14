from _game import tools
LUA = r'''
local o = {}
local f = game.forces.player
for i, p in pairs(f.platforms) do
  local n = p.name:lower()
  if n:find('aquilo',1,true) or (p.space_location and tostring(p.space_location.name):find('aquilo',1,true)) then
    o[#o+1] = i .. ' ' .. p.name .. ' surf=' .. (p.surface and p.surface.name or 'none') .. ' loc=' .. tostring(p.space_location and p.space_location.name) .. ' state=' .. tostring(p.state) .. ' paused=' .. tostring(p.paused)
  end
end
o[#o+1] = 'platforms total=' .. #f.platforms
o[#o+1] = 'aquilo surface=' .. tostring(game.surfaces['aquilo'] ~= nil)
o[#o+1] = 'current research=' .. tostring(f.current_research and f.current_research.name or 'none')
local q = {}
for _, t in pairs(f.research_queue or {}) do q[#q+1] = t.name end
o[#o+1] = 'queue=' .. table.concat(q, ',')
rcon.print(table.concat(o, '\n'))
'''
print(tools["run_lua"](LUA))
