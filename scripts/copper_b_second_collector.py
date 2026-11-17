#!/usr/bin/env python3
"""Copper B: a second collector belt per smelter column, so each column delivers on BOTH lanes (60/s) instead of one (30/s).

Layout (see copper_b_second_belt.py): smelter columns x=749.5 (west) and 755.5 (east), 36 each, y -36.5..68.5 step 3. Each smelter's output inserter (fast, middle row) drops on the far lane of
a collector (x=746.5 west, x=758.5 east), 30/s a lane. Here: one long-handed epic inserter per smelter in its top row (x=747.5 west, x=757.5 east) picks from the smelter and drops two tiles
out on a NEW belt (x=745.5 west, x=759.5 east), far lane again. Each new belt runs north and side-loads the OTHER side of the old collector's path, filling the empty lane:
  west: new belt x=745 north to y=-40, jog west/north/east, a turbo underground pair under x=746 (y=-43), back west at y=-44 into the x=746 belt from the EAST;
  east: new belt x=759 north to y=-44, west along y=-44 into the trunk x=753 from the EAST (the old east plates enter it from the west).
Everything epic. Usage: scripts/copper_b_second_collector.py [--apply | --revert]   (default: dry run, checks ground)"""
import sys

from _game import tools

HEAD = r'''
local s = game.surfaces.nauvis local f = game.forces.player local D = defines.direction local o = {}
local YS = {} for i = 0, 35 do YS[#YS + 1] = -36.5 + 3 * i end
-- tiles (x, y) of belts: {x, y, dir, kind}  kind: nil belt, 'in'/'out' underground
local T = {}
local function add(x, y, d, k) T[#T + 1] = {x, y, d, k} end
for y = 69, -39, -1 do add(745, y, D.north) end           -- west new belt up to y=-39 (tile)
add(745, -40, D.north) add(745, -41, D.west) add(744, -41, D.north) add(744, -42, D.north) add(744, -43, D.east)
add(745, -43, D.east, 'in') add(747, -43, D.east, 'out') add(748, -43, D.north) add(748, -44, D.west) add(747, -44, D.west)
for y = 69, -43, -1 do add(759, y, D.north) end          -- east new belt
add(759, -44, D.west) for x = 758, 754, -1 do add(x, -44, D.west) end
local L = {}                                              -- long inserters: {x tile, ytile, direction}
for _, yc in ipairs(YS) do L[#L + 1] = {747, yc - 1.5, D.east} L[#L + 1] = {757, yc - 1.5, D.west} end
local function occupant(tx, ty)
  for _, e in pairs(s.find_entities_filtered{area = {{tx + 0.05, ty + 0.05}, {tx + 0.95, ty + 0.95}}}) do
    if e.type ~= 'resource' and e.type ~= 'logistic-robot' and e.type ~= 'construction-robot' then return e end
  end
  return nil
end
'''
CHECK = HEAD + r'''
local bad = {}
for _, t in ipairs(T) do local e = occupant(t[1], t[2]) if e then bad[#bad + 1] = e.name .. '@' .. t[1] .. ',' .. t[2] end end
for _, t in ipairs(L) do local e = occupant(t[1], t[2]) if e then bad[#bad + 1] = e.name .. '@' .. t[1] .. ',' .. t[2] end end
-- junction tiles must hold the expected belts: x=746 belt at y=-44, x=753 trunk at y=-44
local j1 = s.find_entities_filtered{type = 'transport-belt', position = {746.5, -43.5}, radius = 0.3}[1]
local j2 = s.find_entities_filtered{type = 'transport-belt', position = {753.5, -43.5}, radius = 0.3}[1]
rcon.print(#T .. ' belt tiles, ' .. #L .. ' long inserters; blocked: ' .. (#bad == 0 and 'none' or table.concat(bad, ' ', 1, math.min(#bad, 20))) ..
  ' | junction x=746,y=-44: ' .. (j1 and ('d' .. j1.direction) or 'MISSING') .. ' | junction x=753,y=-44: ' .. (j2 and ('d' .. j2.direction) or 'MISSING'))
'''
APPLY = HEAD + r'''
local n, u, li = 0, 0, 0
for _, t in ipairs(T) do
  local pos = {t[1] + 0.5, t[2] + 0.5}
  if t[4] then
    if s.create_entity{name = 'turbo-underground-belt', position = pos, direction = t[3], type = (t[4] == 'in') and 'input' or 'output', force = f, quality = 'epic'} then u = u + 1 end
  else
    if s.create_entity{name = 'turbo-transport-belt', position = pos, direction = t[3], force = f, quality = 'epic'} then n = n + 1 end
  end
end
for _, t in ipairs(L) do
  if s.create_entity{name = 'long-handed-inserter', position = {t[1] + 0.5, t[2] + 0.5}, direction = t[3], force = f, quality = 'epic'} then li = li + 1 end
end
rcon.print('belts ' .. n .. ' of ' .. (#T - 2) .. ', undergrounds ' .. u .. ' of 2, long inserters ' .. li .. ' of ' .. #L)
'''
REVERT = HEAD + r'''
local g = 0
for _, t in ipairs(T) do
  for _, e in pairs(s.find_entities_filtered{type = {'transport-belt', 'underground-belt'}, position = {t[1] + 0.5, t[2] + 0.5}, radius = 0.3}) do e.destroy() g = g + 1 end
end
local h = 0
for _, t in ipairs(L) do
  for _, e in pairs(s.find_entities_filtered{name = 'long-handed-inserter', position = {t[1] + 0.5, t[2] + 0.5}, radius = 0.3}) do e.destroy() h = h + 1 end
end
rcon.print('removed belts ' .. g .. ', long inserters ' .. h)
'''

if __name__ == "__main__":
    if "--apply" in sys.argv:
        print(tools["run_lua"](APPLY))
    elif "--revert" in sys.argv:
        print(tools["run_lua"](REVERT))
    else:
        print("DRY RUN (nothing changed):")
        print(tools["run_lua"](CHECK))
