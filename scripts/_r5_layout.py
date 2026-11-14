"""Round 5: everything in the copper load area (x 160..190, y -299..-288): entities with positions, plus free tiles on the inserter row y=-294.5."""
from _game import tools

LUA = r'''
local s = game.surfaces.nauvis
local o = {}
local occ = {}
for _, e in pairs(s.find_entities_filtered{area = {{160, -299}, {190, -288}}}) do
  o[#o + 1] = e.name .. ' ' .. e.position.x .. ',' .. e.position.y .. ' dir=' .. tostring(e.direction)
  if e.tile_width then
    -- mark occupied tiles
    local tw, th = e.tile_width or 1, e.tile_height or 1
    local l, t = e.bounding_box.left_top.x, e.bounding_box.left_top.y
    for x = math.floor(e.bounding_box.left_top.x), math.ceil(e.bounding_box.right_bottom.x) - 1 do
      for y = math.floor(e.bounding_box.left_top.y), math.ceil(e.bounding_box.right_bottom.y) - 1 do
        occ[x .. ',' .. y] = e.name
      end
    end
  end
end
local free = {}
for x = 160, 189 do
  local k = x .. ',-295'
  local k2 = (x + 0.5) .. ''
  if not occ[x .. ',-295'] and not occ[x .. ',-294'] then free[#free + 1] = x end
end
o[#o + 1] = 'free x on rows -295/-294: ' .. table.concat(free, ' ')
rcon.print(table.concat(o, '\n'))
'''
if __name__ == "__main__":
    print(tools["run_lua"](LUA))
