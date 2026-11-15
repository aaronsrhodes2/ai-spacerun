"""Trace the ore belt that feeds starved copper smelters, upstream to where the ore runs out.
Usage: _r20_ore_trace.py X Y   (a starved smelter's position, e.g. -28.5 -452.5)"""
import sys

from _game import tools

X, Y = float(sys.argv[1]), float(sys.argv[2])

LUA = r'''
local s = game.surfaces.nauvis
local SN = {}
for k, v in pairs(defines.entity_status) do SN[v] = k end
local o = {}
local e = s.find_entities_filtered{type = 'furnace', position = {PX, PY}, radius = 1.2}[1]
if not e then rcon.print('no furnace there') return end
o[#o + 1] = 'smelter ' .. string.format('%.1f,%.1f', e.position.x, e.position.y) .. ' ' .. tostring(SN[e.status]) .. ' speed ' .. string.format('%.2f', e.crafting_speed)
local feeds = {}
for _, i in pairs(s.find_entities_filtered{type = 'inserter', position = e.position, radius = 4}) do
  if i.drop_target == e and i.pickup_target and i.pickup_target.type == 'transport-belt' then feeds[#feeds + 1] = i.pickup_target end
end
if #feeds == 0 then rcon.print(table.concat(o, '\n') .. '\nno belt feeds it') return end
local cur = feeds[1]
o[#o + 1] = 'fed from belt ' .. string.format('%.1f,%.1f d%d', cur.position.x, cur.position.y, cur.direction)
local function load(b)
  local a, c = 0, 0
  local ore = {}
  for li = 1, 2 do for _, it in pairs(b.get_transport_line(li).get_contents()) do
    if li == 1 then a = a + (it.count or 0) else c = c + (it.count or 0) end
    ore[it.name] = true
  end end
  local names = {}
  for k in pairs(ore) do names[#names + 1] = k end
  table.sort(names)
  return a .. '/' .. c .. ' [' .. table.concat(names, ',') .. ']'
end
local steps, seen = 0, {}
local trail = {}
local last = cur
while cur and steps < 4000 do
  local k = cur.position.x .. ',' .. cur.position.y
  if seen[k] then trail[#trail + 1] = 'LOOP at ' .. k break end
  seen[k] = true
  steps = steps + 1
  last = cur
  if steps == 1 or steps % 60 == 0 or cur.type ~= 'transport-belt' then
    trail[#trail + 1] = string.format('#%d %s(%.0f,%.0f) %s', steps, cur.type:sub(1, 5), cur.position.x, cur.position.y, load(cur))
  end
  local ins = cur.belt_neighbours and cur.belt_neighbours.inputs or {}
  if cur.type == 'underground-belt' and cur.belt_to_ground_type == 'output' then
    -- find the paired input behind it
    local d = cur.direction
    local dx = (d == 4 and -1) or (d == 12 and 1) or 0
    local dy = (d == 8 and -1) or (d == 0 and 1) or 0
    local pair = nil
    for kk = 1, 20 do
      local cand = s.find_entities_filtered{type = 'underground-belt', position = {cur.position.x + dx * kk, cur.position.y + dy * kk}, radius = 0.3}[1]
      if cand and cand.belt_to_ground_type == 'input' then pair = cand break end
    end
    cur = pair
  else
    if #ins >= 2 then trail[#trail + 1] = string.format('MERGE(%.0f,%.0f) %d inputs, load %s', cur.position.x, cur.position.y, #ins, load(cur)) end
    cur = ins[1]
  end
end
o[#o + 1] = 'walked ' .. steps .. ' tiles upstream; trail (step, type, position, lane1/lane2 [ore]): ' .. table.concat(trail, ' | ')
o[#o + 1] = 'belt starts at ' .. string.format('%.1f,%.1f d%d', last.position.x, last.position.y, last.direction)
local near = {}
for _, x in pairs(s.find_entities_filtered{position = last.position, radius = 6, force = game.forces.player}) do
  if x ~= last and x.type ~= 'transport-belt' and x.type ~= 'electric-pole' and x.type ~= 'underground-belt' then near[#near + 1] = x.name .. string.format(' %.1f,%.1f', x.position.x, x.position.y) .. (x.status and (' ' .. tostring(SN[x.status])) or '') end
end
table.sort(near)
o[#o + 1] = 'next to the belt start: ' .. (#near > 0 and table.concat(near, ' | ') or 'nothing of ours')
rcon.print(table.concat(o, '\n'))
'''

if __name__ == "__main__":
    print(tools["run_lua"](LUA.replace("PX", str(X)).replace("PY", str(Y))))
