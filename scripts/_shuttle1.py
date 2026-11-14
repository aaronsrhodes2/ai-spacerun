from _game import tools
LUA = r'''
local o = {}
local f = game.forces.player
local p = nil
for _, q in pairs(f.platforms) do if q.name:sub(-#'Nauvis-Fulgora 1 Shuttle') == 'Nauvis-Fulgora 1 Shuttle' then p = q end end
if p then
  o[#o+1] = 'loc=' .. tostring(p.space_location and p.space_location.name) .. ' state=' .. tostring(p.state) .. ' paused=' .. tostring(p.paused) .. ' sched=' .. tostring(p.schedule and p.schedule.current)
  local inv = p.hub.get_inventory(defines.inventory.hub_main)
  o[#o+1] = 'hub stone=' .. inv.get_item_count('stone') .. ' mags=' .. inv.get_item_count('firearm-magazine')
  local n = #p.surface.find_entities()
  o[#o+1] = 'entities=' .. n

  local ok, a = pcall(function() return game.players[1] and game.players[1].get_alerts{surface=p.surface} end)
  o[#o+1] = 'alerts ok=' .. tostring(ok)
  local miss = #p.surface.find_entities_filtered{type='entity-ghost'}
  o[#o+1] = 'ghosts=' .. miss
end
rcon.print(table.concat(o,'\n'))
'''
print(tools["run_lua"](LUA))
