#!/usr/bin/env python3
"""Copper A and Copper B ore feeds: use BOTH lanes of the ore trunk (same bug as the big copper field, scripts/copper_field_lane_fix.py).

Each field's ore comes up as branch belts (flowing north) that side-load an east-flowing feeder row from the SOUTH, so everything rides the south lane (30/s on a turbo belt)
and the north lane stays empty. For the two branches nearest the trunk this sends the branch under the row (turbo underground, entrance at the first branch tile y_e, exit y_e-2),
then a one-tile jog east and two belts south so it side-loads the row from the NORTH, onto the empty lane.
  Copper B: row y=73 (x 720..751, then north up x=752), branches x=743, 750, entrance y=74.
  Copper A: row y=214 (x 301..330, then north up x=331), branches x=322, 329, entrance y=215.
Everything epic. Usage: scripts/copper_ab_lane_fix.py [--apply | --revert]   (default: dry run, checks the ground)"""
import sys

from _game import tools

SITES = [("B", 74, (743, 750)), ("A", 215, (322, 329))]      # (name, entrance tile y, branch tile xs)

LUA_HEAD = "local s=game.surfaces.nauvis local f=game.forces.player local SITES={" + ",".join("{'%s',%d,{%s}}" % (n, y, ",".join(map(str, xs))) for n, y, xs in SITES) + "} local o={}\n"
LUA_HELP = r'''
local function belt_at(x, y) return s.find_entities_filtered{type = {'transport-belt', 'underground-belt'}, position = {x + 0.5, y + 0.5}, radius = 0.3}[1] end
local function clear(x, y)
  for _, e in pairs(s.find_entities_filtered{area = {{x + 0.05, y + 0.05}, {x + 0.95, y + 0.95}}}) do
    if e.type ~= 'resource' and e.type ~= 'logistic-robot' and e.type ~= 'construction-robot' then return e.name end
  end
  return nil
end
'''
CHECK = LUA_HEAD + LUA_HELP + r'''
for _, st in ipairs(SITES) do
  local ye = st[2]
  for _, x in ipairs(st[3]) do
    local msgs = {}
    for _, t in ipairs({{x, ye}, {x, ye + 1}}) do
      local b = belt_at(t[1], t[2])
      if not (b and b.type == 'transport-belt' and b.direction == defines.direction.north) then msgs[#msgs + 1] = 'branch tile ' .. t[1] .. ',' .. t[2] .. ' not a north belt' end
    end
    local rw = belt_at(x + 1, ye - 1)
    if not (rw and rw.direction == defines.direction.east) then msgs[#msgs + 1] = 'row tile ' .. (x + 1) .. ',' .. (ye - 1) .. ' not an east belt' end
    for _, t in ipairs({{x, ye - 2}, {x, ye - 3}, {x + 1, ye - 3}, {x + 1, ye - 2}}) do
      local c = clear(t[1], t[2])
      if c then msgs[#msgs + 1] = 'blocked ' .. t[1] .. ',' .. t[2] .. ' by ' .. c end
    end
    local nm = belt_at(x, ye) and belt_at(x, ye).name or '?'
    o[#o + 1] = st[1] .. ' x=' .. x .. ' (belt ' .. nm .. '): ' .. (#msgs == 0 and 'OK' or table.concat(msgs, '; '))
  end
end
rcon.print(table.concat(o, '\n'))
'''
APPLY = LUA_HEAD + LUA_HELP + r'''
local D = defines.direction
for _, st in ipairs(SITES) do
  local ye = st[2]
  for _, x in ipairs(st[3]) do
    local b = belt_at(x, ye)
    if not (b and b.type == 'transport-belt' and not clear(x, ye - 2) and not clear(x, ye - 3) and not clear(x + 1, ye - 3) and not clear(x + 1, ye - 2)) then
      o[#o + 1] = st[1] .. ' x=' .. x .. ': not as expected, skipped'
    else
      b.destroy()
      local a = s.create_entity{name = 'turbo-underground-belt', position = {x + 0.5, ye + 0.5}, direction = D.north, type = 'input', force = f, quality = 'epic'}
      local e = s.create_entity{name = 'turbo-underground-belt', position = {x + 0.5, ye - 1.5}, direction = D.north, type = 'output', force = f, quality = 'epic'}
      local ok = 0
      for _, t in ipairs({{x, ye - 3, D.east}, {x + 1, ye - 3, D.south}, {x + 1, ye - 2, D.south}}) do
        if s.create_entity{name = 'turbo-transport-belt', position = {t[1] + 0.5, t[2] + 0.5}, direction = t[3], force = f, quality = 'epic'} then ok = ok + 1 end
      end
      o[#o + 1] = st[1] .. ' x=' .. x .. ': underground in ' .. tostring(a ~= nil) .. ', out ' .. tostring(e ~= nil) .. ', jog belts ' .. ok .. ' of 3'
    end
  end
end
rcon.print(table.concat(o, '\n'))
'''
REVERT = LUA_HEAD + LUA_HELP + r'''
local D = defines.direction
for _, st in ipairs(SITES) do
  local ye = st[2]
  for _, x in ipairs(st[3]) do
    local gone = 0
    for _, t in ipairs({{x, ye}, {x, ye - 2}, {x, ye - 3}, {x + 1, ye - 3}, {x + 1, ye - 2}}) do
      for _, e in pairs(s.find_entities_filtered{type = {'transport-belt', 'underground-belt'}, position = {t[1] + 0.5, t[2] + 0.5}, radius = 0.3}) do e.destroy() gone = gone + 1 end
    end
    local n = 0
    if s.create_entity{name = 'turbo-transport-belt', position = {x + 0.5, ye + 0.5}, direction = D.north, force = f, quality = 'epic'} then n = 1 end
    o[#o + 1] = st[1] .. ' x=' .. x .. ': removed ' .. gone .. ', restored ' .. n .. ' branch tile'
  end
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
