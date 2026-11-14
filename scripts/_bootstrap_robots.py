"""Round 1 bootstrap: the four logistic-robot cells at x -146.5 sit at item_ingredient_shortage because the robot-saturated
network never delivers their advanced circuits. Move 80 advanced circuits per cell from Nauvis storage chests into the machines
(factory-made stock, moved, not spawned). Usage: _bootstrap_robots.py [per_cell]"""
import sys

from _game import tools

PER = int(sys.argv[1]) if len(sys.argv) > 1 else 80

LUA = r'''
local s = game.surfaces.nauvis
local per = %d
local need = {}
for y = -208.5, -199.5, 3 do
  local m = s.find_entities_filtered{name = 'assembling-machine-3', position = {-146.5, y}, radius = 0.4}[1]
  if m then need[#need + 1] = m end
end
local moved = {}
for _, m in pairs(need) do
  local got = 0
  for _, c in pairs(s.find_entities_filtered{type = {'container', 'logistic-container'}}) do
    if got >= per then break end
    local inv = c.get_inventory(defines.inventory.chest)
    if inv and inv.get_item_count('advanced-circuit') > 0 and c.position.x > -200 and c.position.x < -100 then
      local n = math.min(inv.get_item_count('advanced-circuit'), per - got)
      local removed = inv.remove{name = 'advanced-circuit', count = n}
      if removed > 0 then
        got = got + m.insert{name = 'advanced-circuit', count = removed}
      end
    end
  end
  moved[#moved + 1] = m.position.y .. ':' .. got
end
rcon.print('advanced circuits moved: ' .. table.concat(moved, ', '))
'''

if __name__ == "__main__":
    print(tools["run_lua"](LUA % PER))
