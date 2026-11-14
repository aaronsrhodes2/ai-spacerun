"""Furnaces per surface grouped by what is in their output and by status (FULL / work / starve / other)."""
from _game import tools

LUA = r'''
local E = defines.entity_status
local o = {}
for _, s in pairs(game.surfaces) do
  local c = {}
  for _, f in pairs(s.find_entities_filtered{type = 'furnace'}) do
    local k = 'empty'
    local res = f.get_output_inventory()
    if res then
      for _, it in pairs(res.get_contents()) do k = it.name end
    end
    local st = 'other'
    if f.status == E.full_output then st = 'FULL'
    elseif f.status == E.working then st = 'work'
    elseif f.status == E.no_ingredients then st = 'starve' end
    local key = k .. '|' .. st
    c[key] = (c[key] or 0) + 1
  end
  local t = {}
  for k, v in pairs(c) do t[#t + 1] = k .. '=' .. v end
  if #t > 0 then o[#o + 1] = s.name .. ': ' .. table.concat(t, ', ') end
end
rcon.print(table.concat(o, '\n'))
'''

if __name__ == "__main__":
    print(tools["run_lua"](LUA))
