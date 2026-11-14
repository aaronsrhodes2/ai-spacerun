"""Round 7 survey: (1) machines with no power and the nearest electric pole; (2) Fulgora recyclers with no ingredients and what feeds them;
(3) Nauvis roboports holding the most logistic robots (donors) and Fulgora roboport robot capacity."""
from _game import tools

POWER = r'''
local s = game.surfaces.nauvis
local SN = {}
for k, v in pairs(defines.entity_status) do SN[v] = k end
local o = {}
for _, e in pairs(s.find_entities_filtered{type = {'assembling-machine', 'furnace', 'chemical-plant', 'oil-refinery', 'lab'}}) do
  if SN[e.status] == 'no_power' then
    local best, bd = nil, 1e9
    for _, p in pairs(s.find_entities_filtered{type = 'electric-pole', position = e.position, radius = 30}) do
      local d = math.sqrt((p.position.x - e.position.x) ^ 2 + (p.position.y - e.position.y) ^ 2)
      if d < bd then best, bd = p, d end
    end
    o[#o + 1] = 'NOPOWER ' .. e.name .. ' ' .. e.position.x .. ',' .. e.position.y .. ' nearest pole ' .. (best and (best.name .. ' ' .. best.position.x .. ',' .. best.position.y .. ' d=' .. string.format('%.1f', bd)) or 'none within 30')
  end
end
rcon.print(table.concat(o, '\n'))
'''

FULG = r'''
local s = game.surfaces.fulgora
local SN = {}
for k, v in pairs(defines.entity_status) do SN[v] = k end
local o = {}
local n = 0
for _, e in pairs(s.find_entities_filtered{type = 'furnace'}) do
  if SN[e.status] == 'no_ingredients' then
    n = n + 1
    if n <= 5 then
      local feeders = {}
      for _, i in pairs(s.find_entities_filtered{type = 'inserter', position = e.position, radius = 3}) do
        local pk = i.pickup_target
        feeders[#feeders + 1] = i.name .. '(' .. tostring(SN[i.status]) .. ') <- ' .. (pk and pk.name or 'none')
      end
      o[#o + 1] = 'REC ' .. e.name .. ' ' .. e.position.x .. ',' .. e.position.y .. ' feeders: ' .. table.concat(feeders, '; ')
    end
  end
end
o[#o + 1] = 'fulgora idle furnaces: ' .. n
local rp = s.find_entities_filtered{name = 'roboport'}
o[#o + 1] = 'fulgora roboports ' .. #rp
local req = 0
for _, c in pairs(s.find_entities_filtered{name = 'requester-chest'}) do req = req + 1 end
o[#o + 1] = 'fulgora requester chests ' .. req
rcon.print(table.concat(o, '\n'))
'''

DONORS = r'''
local s = game.surfaces.nauvis
local list = {}
local total = 0
for _, p in pairs(s.find_entities_filtered{name = 'roboport'}) do
  local inv = p.get_inventory(defines.inventory.roboport_robot)
  local n = inv and inv.get_item_count('logistic-robot') or 0
  total = total + n
  if n >= 40 then list[#list + 1] = {n = n, x = p.position.x, y = p.position.y} end
end
table.sort(list, function(a, b) return a.n > b.n end)
local o = {'nauvis logistic robots stored in roboports: ' .. total .. '; donors with 40+: ' .. #list}
for i = 1, math.min(8, #list) do o[#o + 1] = 'DONOR ' .. list[i].n .. ' at ' .. list[i].x .. ',' .. list[i].y end
local cap = s.find_entities_filtered{name = 'roboport'}[1]
o[#o + 1] = 'robot slots per roboport: ' .. #cap.get_inventory(defines.inventory.roboport_robot)
rcon.print(table.concat(o, '\n'))
'''

if __name__ == "__main__":
    for name, lua in (("POWER", POWER), ("FULGORA", FULG), ("DONORS", DONORS)):
        print("==", name)
        print(tools["run_lua"](lua))
