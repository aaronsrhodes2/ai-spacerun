#!/usr/bin/env python3
"""Swap the productivity modules in a copper smelter field for speed modules taken from stock (moved, not spawned; the removed modules go back to the chests).
Why: a smelter field that is supply-limited (its train always waits to be loaded) makes plates in proportion to crafting speed; an epic electric furnace with two
productivity-module-2 runs at speed 3.04 and +23% productivity, with two speed-module-3 at about 7.6 and no productivity (about twice the plates, 2.5 times the ore).
Measure first, apply to one field, measure again; the old modules are put back by `--revert`.

Usage: scripts/copper_speed_swap.py X1 Y1 X2 Y2 [--apply | --revert]     (a box of Nauvis tiles; only furnaces holding copper ore or plate are touched)
Example, the Copper Depot field: copper_speed_swap.py 120 -320 170 -285"""
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
local smelters = {}
for _, e in pairs(s.find_entities_filtered{type = 'furnace', area = {{X1, Y1}, {X2, Y2}}}) do
  local src = e.get_inventory(defines.inventory.crafter_input)
  local res = e.get_inventory(defines.inventory.crafter_output)
  if (src and src.get_item_count('copper-ore') > 0) or (res and res.get_item_count('copper-plate') > 0) then smelters[#smelters + 1] = e end
end
local need = 0
for _, e in ipairs(smelters) do
  local mi = e.get_module_inventory()
  if mi then for _, it in pairs(mi.get_contents()) do if it.name == FROM then need = need + it.count end end end
end
local o = {}
o[#o + 1] = mode .. ': ' .. #smelters .. ' copper smelters in the box, ' .. need .. ' x ' .. FROM .. ' installed'
-- stock of TO (any quality) in chests
local chests, have = {}, 0
for _, c in pairs(s.find_entities_filtered{type = {'container', 'logistic-container'}}) do
  local inv = c.get_inventory(defines.inventory.chest)
  if inv then
    local n = inv.get_item_count(TO)
    if n > 0 then chests[#chests + 1] = {c = c, n = n} have = have + n end
  end
end
o[#o + 1] = 'stock of ' .. TO .. ' in chests: ' .. have .. (have >= need and ' (enough)' or ' (NOT enough)')
if mode ~= 'dry' and have >= need then
  local swapped, moved = 0, 0
  local back = {}
  for _, e in ipairs(smelters) do
    local mi = e.get_module_inventory()
    for i = 1, #mi do
      local st = mi[i]
      if st.valid_for_read and st.name == FROM then
        local q, cnt = st.quality.name, st.count
        -- take one TO from a chest
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
          local put = mi[i].set_stack{name = TO, count = got.n}
          back[#back + 1] = {name = FROM, count = cnt, quality = q, chest = got.chest}
          swapped = swapped + 1
        end
      end
    end
  end
  for _, b in ipairs(back) do
    local inv = b.chest.get_inventory(defines.inventory.chest)
    local ins = inv.insert{name = b.name, count = b.count, quality = b.quality}
    if ins < b.count then moved = moved + (b.count - ins) end
  end
  o[#o + 1] = 'swapped ' .. swapped .. ' module stacks; ' .. moved .. ' removed modules did not fit back in their chest'
end
rcon.print(table.concat(o, '\n'))
'''

if __name__ == "__main__":
    code = LUA.replace("MODE", MODE).replace("X1", str(X1)).replace("Y1", str(Y1)).replace("X2", str(X2)).replace("Y2", str(Y2))
    print(tools["run_lua"](code))
