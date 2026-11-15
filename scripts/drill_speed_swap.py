#!/usr/bin/env python3
"""Swap the productivity modules in the mining drills of an ore patch for speed modules taken from stock (moved, not spawned; the removed modules go back to the chests).
Why: a drill's output per second = its mining speed x (1 + productivity). On a patch that is effectively unlimited (the copper patch at (-57..-25, -541..-510) holds 1.4 trillion ore)
productivity only saves ore nobody is short of, and every productivity-module-2 costs the drill 10% speed; four of them are -40%. Four speed-module-3 are +200%, about five times the speed
for about four times the ore after the lost productivity, at nearly the same power (prod-2 +60% and speed-3 +70% consumption each).

Usage: scripts/drill_speed_swap.py X1 Y1 X2 Y2 [--apply | --revert]     (a box of Nauvis tiles; only mining drills inside are touched)
Example, the Nauvis copper patch: drill_speed_swap.py -110 -600 50 -490"""
import sys

from _game import tools

args = [a for a in sys.argv[1:] if not a.startswith("--")]
X1, Y1, X2, Y2 = (float(v) for v in args[:4])
MODE = "revert" if "--revert" in sys.argv else ("apply" if "--apply" in sys.argv else "dry")

LUA = r'''
local s = game.surfaces.nauvis
local mode = 'MODE'
local FROM, TO = 'productivity-module-2', 'speed-module-3'
if mode == 'revert' then FROM, TO = TO, FROM end
local drills = s.find_entities_filtered{type = 'mining-drill', force = game.forces.player, area = {{X1, Y1}, {X2, Y2}}}
local need = 0
for _, e in ipairs(drills) do
  local mi = e.get_module_inventory()
  if mi then for _, it in pairs(mi.get_contents()) do if it.name == FROM then need = need + it.count end end end
end
local o = {}
o[#o + 1] = mode .. ': ' .. #drills .. ' mining drills in the box, ' .. need .. ' x ' .. FROM .. ' installed'
local chests, have = {}, 0
for _, c in pairs(s.find_entities_filtered{type = {'container', 'logistic-container'}}) do
  local inv = c.get_inventory(defines.inventory.chest)
  if inv then
    local n = inv.get_item_count(TO)
    if n > 0 then chests[#chests + 1] = {c = c, n = n} have = have + n end
  end
end
o[#o + 1] = 'stock of ' .. TO .. ' (normal quality) in chests: ' .. have .. (have >= need and ' (enough)' or ' (NOT enough)')
if mode ~= 'dry' and have >= need then
  local swapped, lost = 0, 0
  local back = {}
  for _, e in ipairs(drills) do
    local mi = e.get_module_inventory()
    for i = 1, #mi do
      local st = mi[i]
      if st.valid_for_read and st.name == FROM then
        local q, cnt = st.quality.name, st.count
        local got = nil
        for _, ch in ipairs(chests) do
          if ch.n > 0 then
            local inv = ch.c.get_inventory(defines.inventory.chest)
            local r = inv.remove{name = TO, count = cnt}
            if r > 0 then ch.n = ch.n - r got = {n = r, chest = ch.c} break end
          end
        end
        if got then
          st.clear()
          mi[i].set_stack{name = TO, count = got.n}
          back[#back + 1] = {name = FROM, count = cnt, quality = q, chest = got.chest}
          swapped = swapped + 1
        end
      end
    end
  end
  for _, b in ipairs(back) do
    local inv = b.chest.get_inventory(defines.inventory.chest)
    local ins = inv.insert{name = b.name, count = b.count, quality = b.quality}
    if ins < b.count then lost = lost + (b.count - ins) end
  end
  o[#o + 1] = 'swapped ' .. swapped .. ' module stacks; ' .. lost .. ' removed modules did not fit back in their chest'
end
rcon.print(table.concat(o, '\n'))
'''

if __name__ == "__main__":
    code = LUA.replace("MODE", MODE).replace("X1", str(X1)).replace("Y1", str(Y1)).replace("X2", str(X2)).replace("Y2", str(Y2))
    print(tools["run_lua"](code))
