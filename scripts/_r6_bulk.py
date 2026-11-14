"""Round 6: replace the fast inserters on the copper load row (x 171.5..183.5, y -294.5) with bulk inserters in place, same direction. Dry run unless --apply."""
import sys
from _game import tools

APPLY = "--apply" in sys.argv

LUA = r'''
local s = game.surfaces.nauvis
local f = game.forces.player
local o = {}
o[#o + 1] = 'bulk-inserter recipe enabled=' .. tostring(f.recipes['bulk-inserter'].enabled)
local list = s.find_entities_filtered{name = 'fast-inserter', area = {{170, -295.2}, {185, -293.8}}}
o[#o + 1] = 'fast inserters on row: ' .. #list
if %s and f.recipes['bulk-inserter'].enabled then
  local done = 0
  for _, i in pairs(list) do
    local pos, dir = i.position, i.direction
    local e = s.create_entity{name = 'bulk-inserter', position = pos, direction = dir, force = f, fast_replace = true, spill = false}
    if e then done = done + 1 end
  end
  o[#o + 1] = 'replaced ' .. done
  local n, bad = 0, 0
  for _, i in pairs(s.find_entities_filtered{name = 'bulk-inserter', area = {{170, -295.2}, {185, -293.8}}}) do
    n = n + 1
    if math.abs(i.pickup_position.y + 295.5) > 0.2 then bad = bad + 1 end
  end
  o[#o + 1] = 'bulk inserters now ' .. n .. ', bad pickups ' .. bad
end
rcon.print(table.concat(o, '\n'))
''' % ('true' if APPLY else 'false')

if __name__ == "__main__":
    print('APPLY' if APPLY else 'DRY RUN')
    print(tools["run_lua"](LUA))
