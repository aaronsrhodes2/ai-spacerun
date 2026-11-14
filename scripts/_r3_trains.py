"""Round 3: trains on Nauvis and train stops near the copper load point at (181,-293): state, schedule, fuel, location."""
from _game import tools

LUA = r'''
local s = game.surfaces.nauvis
local o = {}
local ts = game.train_manager.get_trains{surface = s}
o[#o + 1] = 'trains on nauvis: ' .. #ts
for i, t in pairs(ts) do
  if i <= 12 then
    local st = t.state
    local sch = t.schedule
    local stop = ''
    if sch and sch.records then
      local parts = {}
      for _, r in pairs(sch.records) do parts[#parts + 1] = tostring(r.station or '?') end
      stop = ' sched=[' .. table.concat(parts, ' > ') .. '] current=' .. tostring(sch.current)
    end
    local pos = t.front_stock and t.front_stock.position or {x = 0, y = 0}
    o[#o + 1] = 'TRAIN ' .. i .. ' state=' .. tostring(st) .. ' at ' .. pos.x .. ',' .. pos.y .. stop
  end
end
for _, st in pairs(s.find_entities_filtered{type = 'train-stop', area = {{170, -305}, {200, -280}}}) do
  o[#o + 1] = 'STOP ' .. st.backer_name .. ' ' .. st.position.x .. ',' .. st.position.y .. ' status=' .. tostring(st.status)
end
rcon.print(table.concat(o, '\n'))
'''
if __name__ == "__main__":
    print(tools["run_lua"](LUA))
