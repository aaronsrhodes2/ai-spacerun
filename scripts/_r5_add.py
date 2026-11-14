"""Round 5: add one fast inserter at (177.5,-294.5) on the copper load row, same orientation as its neighbours (176.5 and 178.5). Reports pickup and drop of the new one."""
import sys
from _game import tools

DRY = "--apply" not in sys.argv

LUA = r'''
local s = game.surfaces.nauvis
local ref = s.find_entities_filtered{name = 'fast-inserter', position = {176.5, -294.5}, radius = 0.5}[1]
local o = {}
if not ref then rcon.print('no reference inserter at 176.5,-294.5'); return end
o[#o + 1] = 'ref dir=' .. ref.direction .. ' pickup=' .. ref.pickup_position.x .. ',' .. ref.pickup_position.y .. ' drop=' .. ref.drop_position.x .. ',' .. ref.drop_position.y
local free = s.find_entities_filtered{position = {177.5, -294.5}, radius = 0.5}
o[#o + 1] = 'occupants at 177.5,-294.5: ' .. #free
if #free == 0 and %s then
  local e = s.create_entity{name = 'fast-inserter', position = {177.5, -294.5}, direction = ref.direction, force = ref.force}
  if e then o[#o + 1] = 'PLACED pickup=' .. e.pickup_position.x .. ',' .. e.pickup_position.y .. ' drop=' .. e.drop_position.x .. ',' .. e.drop_position.y end
end
rcon.print(table.concat(o, '\n'))
''' % ('true' if not DRY else 'false')

if __name__ == "__main__":
    print(('DRY RUN (no --apply)' if DRY else 'APPLY'))
    print(tools["run_lua"](LUA))
