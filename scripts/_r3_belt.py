"""Round 3: the copper-plate belts at the full smelters. Contents per belt tile sampled along the drop row, plus where the belt ends."""
from _game import tools

LUA = r'''
local s = game.surfaces.nauvis
local o = {}
local belts = s.find_entities_filtered{type = {'transport-belt', 'underground-belt', 'splitter'}, area = {{128, -312}, {162, -290}}}
o[#o + 1] = 'belts in box: ' .. #belts
local ends = 0
for _, b in pairs(belts) do
  if b.type == 'transport-belt' then
    local nxt = b.belt_neighbours and b.belt_neighbours.outputs or {}
    if #nxt == 0 then
      ends = ends + 1
      local lines = {}
      for li = 1, 2 do
        local l = b.get_transport_line(li)
        local c = l.get_contents()
        local parts = {}
        for n, v in pairs(c) do parts[#parts + 1] = n .. '=' .. v end
        lines[#lines + 1] = 'L' .. li .. '[' .. table.concat(parts, ',') .. ']'
      end
      o[#o + 1] = 'END ' .. b.position.x .. ',' .. b.position.y .. ' dir=' .. b.direction .. ' ' .. table.concat(lines, ' ')
    end
  end
end
o[#o + 1] = 'belt ends: ' .. ends
rcon.print(table.concat(o, '\n'))
'''
if __name__ == "__main__":
    print(tools["run_lua"](LUA))
