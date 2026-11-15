#!/usr/bin/env python3
"""Copper field at (-28,-440..-520): feed BOTH lanes of the ore trunk.

The 21 big drills (x -59..-25, y -541..-510) drop ore on five collector belts, x = -55.5, -48.5, -41.5, -34.5, -27.5, that run south and all enter the horizontal belt
at y=-505.5 (flowing east, then south down x=-25.5 between the 53 smelters) from the NORTH. A side-load fills only the near lane, so the whole field's ore (the drills
can make about 74/s) rode on ONE lane of the trunk: 30/s at most. The trunk's tail showed ore on one lane and none on the other, with 20 smelters starved.

This sends the collectors at x=-48.5 and x=-41.5 under the horizontal belt (a turbo underground pair, entrance y=-507.5, exit y=-503.5) and back up from the SOUTH
(a one-tile jog east, then three belts north) to side-load onto the empty south lane. Lane budget: north lane = x -27.5, -34.5 (and the end collector x=-55.5),
south lane = x -48.5, -41.5: about 30 ore/s a lane, 60/s on the trunk (a turbo belt's full capacity), double what it carried.

Everything epic. Usage: scripts/copper_field_lane_fix.py [--apply | --revert]   (default: dry run, prints the plan and checks the ground is clear)"""
import sys

from _game import tools

XS = (-48.5, -41.5)

APPLY = r'''
local s = game.surfaces.nauvis
local f = game.forces.player
local XS = {-48.5, -41.5}
local o = {}
local function belt_at(x, y) return s.find_entities_filtered{type = {'transport-belt', 'underground-belt'}, position = {x, y}, radius = 0.3}[1] end
for _, xc in ipairs(XS) do
  local e1, e2 = belt_at(xc, -507.5), belt_at(xc, -506.5)
  if not (e1 and e1.type == 'transport-belt' and e2 and e2.type == 'transport-belt') then o[#o + 1] = 'x=' .. xc .. ': collector tiles not as expected, skipped' goto continue end
  e1.destroy() e2.destroy()
  local a = s.create_entity{name = 'turbo-underground-belt', position = {xc, -507.5}, direction = defines.direction.south, type = 'input', force = f, quality = 'epic'}
  local b = s.create_entity{name = 'turbo-underground-belt', position = {xc, -503.5}, direction = defines.direction.south, type = 'output', force = f, quality = 'epic'}
  local ok = 0
  for _, t in ipairs({{xc, -502.5, defines.direction.east}, {xc + 1, -502.5, defines.direction.north}, {xc + 1, -503.5, defines.direction.north}, {xc + 1, -504.5, defines.direction.north}}) do
    if s.create_entity{name = 'turbo-transport-belt', position = {t[1], t[2]}, direction = t[3], force = f, quality = 'epic'} then ok = ok + 1 end
  end
  o[#o + 1] = 'x=' .. xc .. ': underground in ' .. tostring(a ~= nil) .. ', out ' .. tostring(b ~= nil) .. ', jog belts ' .. ok .. ' of 4'
  ::continue::
end
rcon.print(table.concat(o, '\n'))
'''

REVERT = r'''
local s = game.surfaces.nauvis
local f = game.forces.player
local o = {}
for _, xc in ipairs({-48.5, -41.5}) do
  local gone = 0
  for _, t in ipairs({{xc, -507.5}, {xc, -503.5}, {xc, -502.5}, {xc + 1, -502.5}, {xc + 1, -503.5}, {xc + 1, -504.5}}) do
    for _, e in pairs(s.find_entities_filtered{type = {'transport-belt', 'underground-belt'}, position = {t[1], t[2]}, radius = 0.3}) do e.destroy() gone = gone + 1 end
  end
  local n = 0
  for _, y in ipairs({-507.5, -506.5}) do
    if s.create_entity{name = 'turbo-transport-belt', position = {xc, y}, direction = defines.direction.south, force = f, quality = 'epic'} then n = n + 1 end
  end
  o[#o + 1] = 'x=' .. xc .. ': removed ' .. gone .. ', restored ' .. n .. ' collector tiles'
end
rcon.print(table.concat(o, '\n'))
'''

CHECK = r'''
local s = game.surfaces.nauvis
local o = {}
for _, xc in ipairs({-48.5, -41.5}) do
  local bad = {}
  for _, t in ipairs({{xc, -504.5}, {xc, -503.5}, {xc, -502.5}, {xc + 1, -502.5}, {xc + 1, -503.5}, {xc + 1, -504.5}}) do
    for _, e in pairs(s.find_entities_filtered{area = {{t[1] - 0.45, t[2] - 0.45}, {t[1] + 0.45, t[2] + 0.45}}}) do
      if e.type ~= 'resource' and e.type ~= 'logistic-robot' then bad[#bad + 1] = e.name .. string.format('@%.1f,%.1f', e.position.x, e.position.y) end
    end
  end
  local up = {}
  for _, y in ipairs({-507.5, -506.5}) do
    local b = s.find_entities_filtered{type = 'transport-belt', position = {xc, y}, radius = 0.3}[1]
    up[#up + 1] = string.format('%.1f:%s', y, b and ('belt d' .. b.direction) or 'MISSING')
  end
  local h = s.find_entities_filtered{type = 'transport-belt', position = {xc + 1, -505.5}, radius = 0.3}[1]
  o[#o + 1] = 'x=' .. xc .. ': ground check ' .. (#bad == 0 and 'clear' or ('BLOCKED by ' .. table.concat(bad, ' '))) .. ' | collector tiles ' .. table.concat(up, ' ') .. ' | horizontal belt at x+1 ' .. (h and ('d' .. h.direction) or 'MISSING')
end
rcon.print(table.concat(o, '\n'))
'''

if __name__ == "__main__":
    if "--apply" in sys.argv:
        print(tools["run_lua"](APPLY))
    elif "--revert" in sys.argv:
        print(tools["run_lua"](REVERT))
    else:
        print("DRY RUN (nothing changed):")
        print(tools["run_lua"](CHECK))
