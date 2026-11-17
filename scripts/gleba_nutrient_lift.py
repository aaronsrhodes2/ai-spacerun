#!/usr/bin/env python3
"""Gleba nutrients: fill the EMPTY lane of the egg-feed path (2026-11-14).

The nutrient belt y=9 (east) -> x=124 (south) -> y=11 (west, feeding the 8 egg chambers and the biochambers' fuel) carries nutrients on ONE lane (30/s) because every producer on y=9
sits north of it and drops on the far (south) lane. The idle chamber at (89.5,14.5) puts up to 45 nutrients/s on y=11 west of x=89, where they pile up. Here 3 epic bulk inserters at
(85.5, 86.5, 87.5; 10.5) lift them from y=11 onto y=9 from the SOUTH side, which fills y=9's empty north lane (and, after the turns, y=11's empty south lane at the egg chambers).
The bioflux belt y=10 passes under the three inserter tiles (turbo underground pair, entrance 88.5, exit 84.5).
Usage: scripts/gleba_nutrient_lift.py [--apply | --revert]   (default: dry run)"""
import sys

from _game import tools

HEAD = r'''
local s = game.surfaces.gleba local f = game.forces.player local D = defines.direction
local function belt(x, y) return s.find_entities_filtered{type = {'transport-belt', 'underground-belt'}, position = {x, y}, radius = 0.3}[1] end
'''
CHECK = HEAD + r'''
local o = {}
for _, x in ipairs({84.5, 85.5, 86.5, 87.5, 88.5}) do local b = belt(x, 10.5) o[#o + 1] = x .. ':' .. (b and (b.name .. ' d' .. b.direction) or 'none') end
for _, x in ipairs({85.5, 86.5, 87.5}) do local b = belt(x, 11.5) local n = b and b.get_transport_line(2).get_contents()[1] o[#o + 1] = 'y11 ' .. x .. ':' .. (b and ('d' .. b.direction) or 'none') .. ' ' .. (n and n.name or 'empty') local c = belt(x, 9.5) o[#o + 1] = 'y9 ' .. x .. ':' .. (c and ('d' .. c.direction) or 'none') end
rcon.print(table.concat(o, ' | '))
'''
APPLY = HEAD + r'''
local o = {}
for _, x in ipairs({85.5, 86.5, 87.5}) do local b = belt(x, 10.5) if b then b.destroy() end end
local b88, b84 = belt(88.5, 10.5), belt(84.5, 10.5)
if b88 then b88.destroy() end if b84 then b84.destroy() end
local a = s.create_entity{name = 'turbo-underground-belt', position = {88.5, 10.5}, direction = D.west, type = 'input', force = f, quality = 'epic'}
local e = s.create_entity{name = 'turbo-underground-belt', position = {84.5, 10.5}, direction = D.west, type = 'output', force = f, quality = 'epic'}
local n = 0
for _, x in ipairs({85.5, 86.5, 87.5}) do
  local i = s.create_entity{name = 'bulk-inserter', position = {x, 10.5}, direction = D.south, force = f, quality = 'epic'}
  if i then n = n + 1 pcall(function() i.set_filter(1, {name = 'nutrients', quality = 'normal', comparator = '='}) end) end
end
rcon.print('underground in ' .. tostring(a ~= nil) .. ' out ' .. tostring(e ~= nil) .. ', inserters ' .. n .. ' of 3')
'''
REVERT = HEAD + r'''
for _, x in ipairs({84.5, 85.5, 86.5, 87.5, 88.5}) do
  for _, en in pairs(s.find_entities_filtered{type = {'transport-belt', 'underground-belt', 'inserter'}, position = {x, 10.5}, radius = 0.3}) do en.destroy() end
  s.create_entity{name = 'turbo-transport-belt', position = {x, 10.5}, direction = D.west, force = f, quality = 'epic'}
end
rcon.print('restored 5 belt tiles on y=10')
'''
if __name__ == "__main__":
    if "--apply" in sys.argv: print(tools["run_lua"](APPLY))
    elif "--revert" in sys.argv: print(tools["run_lua"](REVERT))
    else:
        print("DRY RUN:"); print(tools["run_lua"](CHECK))
