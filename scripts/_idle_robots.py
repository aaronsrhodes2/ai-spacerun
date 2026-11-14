"""Round 2: robots idle in chests near the robot cells go into the Nauvis roboports nearby, so the network can use them.
Robots held in roboports are the only ones that serve requests; the chests hold them uselessly.
Usage: _idle_robots.py [per_port] [max_robots]"""
import sys

from _game import tools

PER = int(sys.argv[1]) if len(sys.argv) > 1 else 25
MAX = int(sys.argv[2]) if len(sys.argv) > 2 else 1200

LUA = r'''
local s = game.surfaces.nauvis
local per, cap = %d, %d
local chests = s.find_entities_filtered{name = 'passive-provider-chest', area = {{-152, -214}, {-141, -195}}}
local ports = s.find_entities_filtered{type = 'roboport', area = {{-230, -260}, {-60, -170}}}
local have = 0
for _, c in pairs(chests) do have = have + c.get_inventory(defines.inventory.chest).get_item_count('logistic-robot') end
local moved, i = 0, 0
for _, c in pairs(chests) do
  local inv = c.get_inventory(defines.inventory.chest)
  local n = inv.get_item_count('logistic-robot')
  while n > 0 and moved < cap and #ports > 0 do
    i = i %% #ports + 1
    local take = math.min(n, per, cap - moved)
    local r = inv.remove{name = 'logistic-robot', count = take}
    local put = ports[i].get_inventory(defines.inventory.roboport_robot).insert{name = 'logistic-robot', count = r}
    if put < r then inv.insert{name = 'logistic-robot', count = r - put} end
    moved = moved + put
    n = n - put
    if put == 0 then break end
  end
end
rcon.print('robots in chests before ' .. have .. ', ports ' .. #ports .. ', moved into roboports ' .. moved)
'''

if __name__ == "__main__":
    print(tools["run_lua"](LUA % (PER, MAX)))
