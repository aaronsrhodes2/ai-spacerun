from _game import tools
LUA = r'''
local o = {}
local f = game.forces.player
local dup = {['Nauvis-Gleba 2 Shuttle']=1,['Nauvis-Vulcanus 2 Shuttle']=1,['Nauvis-Fulgora 2 Shuttle']=1,['Nauvis-Gleba 3 Shuttle']=1,['Nauvis-Gleba 4 Shuttle']=1,['Nauvis-Gleba 5 Shuttle']=1}
local kill = {}
for i, p in pairs(f.platforms) do
  if i >= 26 and dup[p.name] and #p.surface.find_entities() == 1 then kill[#kill+1] = p end
end
for _, p in pairs(kill) do o[#o+1] = 'destroy ' .. p.name .. ' ' .. p.surface.name; p.destroy() end
local ren = {['Nauvis-Gleba 6 Shuttle']='[virtual-signal=signal-rightwards-leftwards-arrow] Nauvis-Gleba 6 Shuttle', ['Nauvis-Vulcanus 3 Shuttle']='[virtual-signal=signal-rightwards-leftwards-arrow] Nauvis-Vulcanus 3 Shuttle', ['Nauvis-Fulgora 3 Shuttle']='[virtual-signal=signal-rightwards-leftwards-arrow] Nauvis-Fulgora 3 Shuttle'}
for _, p in pairs(f.platforms) do if ren[p.name] then o[#o+1] = 'rename ' .. p.name; p.name = ren[p.name] end end
rcon.print(table.concat(o, '\n'))
'''
print(tools["run_lua"](LUA))
