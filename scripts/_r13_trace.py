"""Round 13: follow the Copper Depot unload belt downstream from (97.5,-146.5): path summary, where it ends or merges, and the contents of the last belts."""
from _game import tools

LUA = r'''
local s = game.surfaces.nauvis
local b = s.find_entities_filtered{type = 'transport-belt', position = {97.5, -146.5}, radius = 0.4}[1]
local o = {}
if not b then rcon.print('no belt') return end
local steps, last, visited, reason = 0, b, {}, 'max steps'
local turns = {}
local function contents(e)
  local parts = {}
  for li = 1, 2 do
    local ok, c = pcall(function() return e.get_transport_line(li).get_contents() end)
    if ok then
      local pp = {}
      for n, v in pairs(c) do pp[#pp + 1] = (type(v) == 'table' and (v.name .. '=' .. v.count) or (n .. '=' .. v)) end
      parts[#parts + 1] = 'L' .. li .. '[' .. table.concat(pp, ',') .. ']'
    end
  end
  return table.concat(parts, ' ')
end
local cur = b
while cur and steps < 3000 do
  local key = cur.position.x .. ',' .. cur.position.y
  if visited[key] then reason = 'loop at ' .. key; break end
  visited[key] = true
  last = cur
  steps = steps + 1
  if cur.type == 'splitter' or cur.type == 'underground-belt' then turns[#turns + 1] = cur.name .. ' ' .. key end
  local nxt = nil
  local pair = nil
  if cur.type == 'underground-belt' and cur.belt_to_ground_type == 'input' then
    local d = cur.direction
    local dx = (d == 4 and 1) or (d == 12 and -1) or 0
    local dy = (d == 8 and 1) or (d == 0 and -1) or 0
    for k = 1, 20 do
      local cand = s.find_entities_filtered{type = 'underground-belt', position = {cur.position.x + dx * k, cur.position.y + dy * k}, radius = 0.3}[1]
      if cand and cand.belt_to_ground_type == 'output' and cand.name == cur.name then pair = cand; break end
    end
  end
  if pair then
    nxt = pair
    visited[nxt.position.x .. ',' .. nxt.position.y] = true
    steps = steps + 1
    last = nxt
    cur = nxt
    local outs2 = cur.belt_neighbours and cur.belt_neighbours.outputs or {}
    nxt = outs2[1]
  else
    local outs = cur.belt_neighbours and cur.belt_neighbours.outputs or {}
    nxt = outs[1]
  end
  if not nxt then reason = 'end'; break end
  cur = nxt
end
o[#o + 1] = 'steps ' .. steps .. ' reason ' .. reason
o[#o + 1] = 'last ' .. last.name .. ' ' .. last.position.x .. ',' .. last.position.y .. ' dir=' .. last.direction .. ' ' .. contents(last)
for _, e in pairs(s.find_entities_filtered{position = last.position, radius = 3.5}) do
  if e ~= last and e.type ~= 'transport-belt' then
    local extra = ''
    if e.type == 'inserter' then extra = ' status=' .. tostring(e.status) end
    o[#o + 1] = 'near-end ' .. e.name .. ' ' .. e.position.x .. ',' .. e.position.y .. extra
  end
end
o[#o + 1] = 'landmarks on path: ' .. #turns
for i = math.max(1, #turns - 12), #turns do o[#o + 1] = '  ' .. turns[i] end
rcon.print(table.concat(o, '\n'))
'''
if __name__ == "__main__":
    print(tools["run_lua"](LUA))
