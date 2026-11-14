"""Round 4: longest runs of straight rail on the Copper Depot route, between the load stop (165,-295) and the unload (87,-151): run start, length, direction."""
from _game import tools

LUA = r'''
local s = game.surfaces.nauvis
local rails = s.find_entities_filtered{type = 'straight-rail', area = {{80, -300}, {175, -140}}}
local set = {}
for _, r in pairs(rails) do
  set[r.position.x .. ',' .. r.position.y] = r
end
local runs = {}
local used = {}
for k, r in pairs(set) do
  if not used[k] then
    -- walk backward to the start of a straight run in the rail's direction
    local dx, dy = 0, 0
    if r.direction == 0 or r.direction == 8 then dy = 2 else dx = 2 end
    if r.direction == 0 or r.direction == 8 then dx = 0 end
    local x, y = r.position.x, r.position.y
    local len = 1
    local nx, ny = x + dx, y + dy
    local dir = r.direction
    while set[nx .. ',' .. ny] and set[nx .. ',' .. ny].direction == dir do
      used[nx .. ',' .. ny] = true
      len = len + 1
      nx, ny = nx + dx, ny + dy
    end
    if len >= 3 then runs[#runs + 1] = {len = len, x = x, y = y, dir = dir} end
  end
end
table.sort(runs, function(a, b) return a.len > b.len end)
local o = {}
for i = 1, math.min(8, #runs) do
  local r = runs[i]
  o[#o + 1] = 'RUN len=' .. r.len .. ' from ' .. r.x .. ',' .. r.y .. ' dir=' .. r.dir
end
if #o == 0 then o[1] = 'no straight runs of 3+ found' end
rcon.print(table.concat(o, '\n'))
'''
if __name__ == "__main__":
    print(tools["run_lua"](LUA))
