"""Terrain and entity grid for the planned west oil field pipeline (read-only). Saves rows to the scratch file given as argv[1].

'.' free, '#' our entity, 'F' our fluid entity (pipe, tank, pump, machine with a fluid box), '~' water or unbuildable tile, 'c' cliff, 't' tree or rock, 'o' crude oil well, 'e' other.
"""
import json
import sys

from _game import tools

X0, Y0, X1, Y1 = -735, -445, -265, -265

LUA = r'''
local s = game.surfaces.nauvis
local X0, Y0, X1, Y1 = %d, %d, %d, %d
local g = {}
for y = Y0, Y1 do
  local row = {}
  for x = X0, X1 do
    local t = s.get_tile(x, y)
    row[x - X0 + 1] = (t.collides_with('water_tile') or t.collides_with('player')) and '~' or '.'
  end
  g[y - Y0 + 1] = row
end
local FL = {['pipe'] = 1, ['pipe-to-ground'] = 1, ['storage-tank'] = 1, ['pump'] = 1, ['offshore-pump'] = 1, ['assembling-machine'] = 1, ['furnace'] = 1, ['mining-drill'] = 1, ['boiler'] = 1, ['generator'] = 1, ['fluid-turret'] = 1}
for _, e in pairs(s.find_entities_filtered{area = {{X0, Y0}, {X1 + 1, Y1 + 1}}}) do
  local ch
  if e.type == 'cliff' then ch = 'c'
  elseif e.type == 'tree' or e.type == 'simple-entity' then ch = 't'
  elseif e.name == 'crude-oil' then ch = 'o'
  elseif e.type == 'resource' or e.type == 'corpse' or e.type == 'item-entity' or e.type == 'fish' or e.type == 'logistic-robot' or e.type == 'construction-robot' or e.type == 'character' or e.type == 'smoke-with-trigger' or e.type == 'entity-ghost' and false then ch = nil
  elseif e.force.name == 'player' then ch = FL[e.type] and 'F' or '#'
  else ch = nil end
  if ch then
    local bb = e.bounding_box
    for x = math.floor(bb.left_top.x), math.floor(bb.right_bottom.x - 0.01) do
      for y = math.floor(bb.left_top.y), math.floor(bb.right_bottom.y - 0.01) do
        if x >= X0 and x <= X1 and y >= Y0 and y <= Y1 then
          local cur = g[y - Y0 + 1][x - X0 + 1]
          if cur == '.' or (cur == 't' and ch ~= 't') or ch == 'F' then g[y - Y0 + 1][x - X0 + 1] = ch end
        end
      end
    end
  end
end
local rows = {}
for i = 1, #g do rows[i] = table.concat(g[i]) end
rcon.print(table.concat(rows, '\n'))
'''


def fetch(x0, y0, x1, y1):
    lua = " ".join(l.strip() for l in (LUA % (x0, y0, x1, y1)).splitlines() if l.strip())
    return tools["run_lua"](lua).split("\n")


if __name__ == "__main__":
    rows = None
    step = 120
    for xa in range(X0, X1 + 1, step):
        xb = min(xa + step - 1, X1)
        part = fetch(xa, Y0, xb, Y1)
        assert len(part) == Y1 - Y0 + 1, (len(part), part[:2])
        rows = part if rows is None else [a + b for a, b in zip(rows, part)]
    json.dump({"x0": X0, "y0": Y0, "rows": rows}, open(sys.argv[1], "w"))
    from collections import Counter
    print(Counter("".join(rows)))
