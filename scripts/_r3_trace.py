"""Round 3: follow the copper-plate belt downstream from a full smelter's drop tile; report the path length, where it stops, and the lane contents at the end."""
from _game import tools

LUA = r'''
local s = game.surfaces.nauvis
local start = s.find_entities_filtered{type = 'transport-belt', position = {132.5, -307.5}, radius = 0.6}[1]
local o = {}
if not start then
  rcon.print('no belt at 132.5,-307.5')
else
  local b = start
  local steps = 0
  local last = nil
  local visited = {}
  local reason = 'max steps'
  while b and steps < 1500 do
    local key = b.position.x .. ',' .. b.position.y
    if visited[key] then reason = 'loop at ' .. key; break end
    visited[key] = true
    last = b
    steps = steps + 1
    local outs = b.belt_neighbours.outputs
    if #outs == 0 then reason = 'dead end'; break end
    b = outs[1]
  end
  o[#o + 1] = 'steps ' .. steps .. ' reason ' .. reason
  if last then
    o[#o + 1] = 'last ' .. last.position.x .. ',' .. last.position.y .. ' dir=' .. last.direction
    for li = 1, 2 do
      local c = last.get_transport_line(li).get_contents()
      local parts = {}
      for n, v in pairs(c) do if type(v) == 'table' then parts[#parts + 1] = (v.name or n) .. '=' .. (v.count or 0) else parts[#parts + 1] = n .. '=' .. v end end
      o[#o + 1] = 'L' .. li .. ' [' .. table.concat(parts, ',') .. ']'
    end
  end
  local ents = s.find_entities_filtered{position = last and last.position or {0, 0}, radius = 3}
  for _, e in pairs(ents) do o[#o + 1] = 'near-end ' .. e.name .. ' ' .. e.position.x .. ',' .. e.position.y end
end
rcon.print(table.concat(o, '\n'))
'''
if __name__ == "__main__":
    print(tools["run_lua"](LUA))
