"""Round 6: what sits east of the copper belt dead end and around the curved rail at (189,-291): rails with directions, belts, and free space."""
from _game import tools

LUA = r'''
local s = game.surfaces.nauvis
local o = {}
for _, e in pairs(s.find_entities_filtered{area = {{182, -300}, {202, -284}}}) do
  if e.type ~= 'tree' and e.name ~= 'tree-07' and e.name ~= 'tree-08' then
    o[#o + 1] = e.name .. ' ' .. e.position.x .. ',' .. e.position.y .. ' dir=' .. tostring(e.direction)
  end
end
rcon.print(table.concat(o, '\n'))
'''
if __name__ == "__main__":
    print(tools["run_lua"](LUA))
