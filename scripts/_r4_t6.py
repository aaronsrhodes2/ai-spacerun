"""Round 4: the Copper Depot train's carriages (positions, orientation, type) and the rail tiles right after its rear."""
from _game import tools

LUA = r'''
local s = game.surfaces.nauvis
local o = {}
for _, t in pairs(game.train_manager.get_trains{surface = s}) do
  local sch = t.schedule
  local is = false
  if sch and sch.records then
    for _, r in pairs(sch.records) do if string.find(tostring(r.station), 'Copper Depot') then is = true end end
  end
  if is then
    o[#o + 1] = 'TRAIN state=' .. tostring(t.state) .. ' speed=' .. t.speed .. ' current=' .. tostring(sch.current)
    for i, c in pairs(t.carriages) do
      o[#o + 1] = '  car ' .. i .. ' ' .. c.name .. ' at ' .. string.format('%.1f,%.1f', c.position.x, c.position.y) .. ' ori=' .. string.format('%.2f', c.orientation)
    end
  end
end
local ex = {}
for _, r in pairs(s.find_entities_filtered{type = 'straight-rail', area = {{110, -152}, {140, -146}}}) do
  ex[#ex + 1] = r.position.x .. ',' .. r.position.y
end
o[#o + 1] = 'rails x110-140 y-152..-146: ' .. table.concat(ex, ' ')
rcon.print(table.concat(o, '\n'))
'''
if __name__ == "__main__":
    print(tools["run_lua"](LUA))
