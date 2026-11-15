#!/usr/bin/env python3
"""Trace an ore (or any) belt UPSTREAM through all its branches from a start tile and report the tree: every merge (a belt with two or more inputs) with the
side each input joins from (back = straight in, left/right = side-load) and the lane loads, every source end, and the total length.
Why: a side-load puts items on ONE lane (30/s on a turbo belt), so a trunk fed only from one side carries half what it could (the big copper field's bug,
fixed by scripts/copper_field_lane_fix.py). Use this to find those merges before building.

Usage: scripts/ore_trace.py X Y [max_tiles]      X, Y = a belt tile (centre coordinates, e.g. 752.5 0.5) on the trunk, near the consumers
Output: one line per merge (nearest the start first), source ends, and lane counts at the start. Read-only."""
import sys

from _game import tools

X, Y = float(sys.argv[1]), float(sys.argv[2])
LIMIT = int(sys.argv[3]) if len(sys.argv) > 3 else 6000

LUA = r'''
local s = game.surfaces.nauvis
local start = s.find_entities_filtered{type = {'transport-belt', 'underground-belt', 'splitter'}, position = {SX, SY}, radius = 0.6}[1]
if not start then rcon.print('no belt at SX,SY') return end
local DIRV = {[0] = {0, -1}, [4] = {1, 0}, [8] = {0, 1}, [12] = {-1, 0}}
local function lanes(b)
  local a, c = 0, 0
  for _, it in pairs(b.get_transport_line(1).get_contents()) do a = a + (it.count or 0) end
  for _, it in pairs(b.get_transport_line(2).get_contents()) do c = c + (it.count or 0) end
  return a .. '/' .. c
end
local function side(belt, inp)
  -- where does inp sit relative to belt: back, left, right, front (all in belt's own frame)
  local d = DIRV[belt.direction]
  if not d then return '?' end
  local rx, ry = inp.position.x - belt.position.x, inp.position.y - belt.position.y
  local fwd = rx * d[1] + ry * d[2]
  local left = rx * d[2] + ry * -d[1]          -- left of travel: rotate forward vector by +90 degrees (x,y)->(y,-x)
  if fwd < -0.4 then return 'back' end
  if left > 0.4 then return 'left' end
  if left < -0.4 then return 'right' end
  return 'front'
end
local out = {}
local seen = {}
local queue = {start}
local head, tiles, sources, merges = 1, 0, 0, 0
local srcpos = {}
while head <= #queue and tiles < MAXTILES do
  local cur = queue[head]
  head = head + 1
  local k = cur.position.x .. ',' .. cur.position.y
  if not seen[k] then
    seen[k] = true
    tiles = tiles + 1
    local ins = {}
    if cur.type == 'underground-belt' and cur.belt_to_ground_type == 'output' then
      local d = DIRV[cur.direction]
      for kk = 1, 20 do
        local cand = s.find_entities_filtered{type = 'underground-belt', position = {cur.position.x - d[1] * kk, cur.position.y - d[2] * kk}, radius = 0.3}[1]
        if cand and cand.belt_to_ground_type == 'input' then ins[#ins + 1] = cand break end
      end
      for _, b in pairs(cur.belt_neighbours and cur.belt_neighbours.inputs or {}) do ins[#ins + 1] = b end
    else
      ins = cur.belt_neighbours and cur.belt_neighbours.inputs or {}
    end
    if #ins == 0 then
      sources = sources + 1
      if #srcpos < 12 then srcpos[#srcpos + 1] = string.format('(%.0f,%.0f)', cur.position.x, cur.position.y) end
    end
    if #ins >= 2 then
      merges = merges + 1
      local parts = {}
      for _, b in ipairs(ins) do parts[#parts + 1] = string.format('%s(%.0f,%.0f) %s', side(cur, b), b.position.x, b.position.y, lanes(b)) end
      if #out < 40 then out[#out + 1] = string.format('MERGE at (%.1f,%.1f) dir %d own lanes %s <- %s', cur.position.x, cur.position.y, cur.direction, lanes(cur), table.concat(parts, ' ; ')) end
    end
    for _, b in ipairs(ins) do queue[#queue + 1] = b end
  end
end
rcon.print('start (' .. SX .. ',' .. SY .. ') dir ' .. start.direction .. ' lanes ' .. lanes(start) .. ' | belt tiles in the tree: ' .. tiles .. (tiles >= MAXTILES and ' (LIMIT REACHED)' or '') .. ' | merges ' .. merges .. ' | source ends ' .. sources .. ' e.g. ' .. table.concat(srcpos, ' ') .. '\n' .. table.concat(out, '\n'))
'''

if __name__ == "__main__":
    print(tools["run_lua"](LUA.replace("SX", str(X)).replace("SY", str(Y)).replace("MAXTILES", str(LIMIT))))
