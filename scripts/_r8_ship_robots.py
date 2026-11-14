"""Round 8: move idle logistic robots out of Nauvis chests into the Fulgora roboports (factory-made stock, moved not spawned).
Usage: _r8_ship_robots.py [max_robots]   add --apply to do it; default is a dry run that only reports."""
import sys

from _game import tools

APPLY = "--apply" in sys.argv
MAXN = int([a for a in sys.argv[1:] if a.isdigit()][0]) if any(a.isdigit() for a in sys.argv[1:]) else 3500

LUA = r'''
local nv = game.surfaces.nauvis
local fu = game.surfaces.fulgora
local cap, apply = %d, %s
local ports = fu.find_entities_filtered{name = 'roboport'}
local o = {}
local have, where = 0, {}
for _, c in pairs(nv.find_entities_filtered{type = {'container', 'logistic-container'}}) do
  local inv = c.get_inventory(defines.inventory.chest)
  local n = inv and inv.get_item_count('logistic-robot') or 0
  if n > 0 then have = have + n; where[#where + 1] = c.name .. ' ' .. c.position.x .. ',' .. c.position.y .. ' x' .. n end
end
o[#o + 1] = 'nauvis chest robots: ' .. have .. ' in ' .. #where .. ' chests; fulgora roboports ' .. #ports
for i = 1, math.min(6, #where) do o[#o + 1] = '  ' .. where[i] end
if apply and #ports > 0 then
  local moved, i = 0, 0
  for _, c in pairs(nv.find_entities_filtered{type = {'container', 'logistic-container'}}) do
    local inv = c.get_inventory(defines.inventory.chest)
    local n = inv and inv.get_item_count('logistic-robot') or 0
    while n > 0 and moved < cap do
      i = i %% #ports + 1
      local take = math.min(n, 100, cap - moved)
      local r = inv.remove{name = 'logistic-robot', count = take}
      if r == 0 then break end
      local put = ports[i].get_inventory(defines.inventory.roboport_robot).insert{name = 'logistic-robot', count = r}
      if put < r then inv.insert{name = 'logistic-robot', count = r - put} end
      moved = moved + put
      n = n - put
      if put == 0 then break end
    end
  end
  o[#o + 1] = 'moved into fulgora roboports: ' .. moved
end
rcon.print(table.concat(o, '\n'))
'''

if __name__ == "__main__":
    print("APPLY" if APPLY else "DRY RUN")
    print(tools["run_lua"](LUA % (MAXN, "true" if APPLY else "false")))
