#!/usr/bin/env python3
"""A field of buffer chests inside the Replicator, so the basic materials its requests use most are close at hand (the Captain, 2026-11-14:
"like how I have for the nuclear centrifuge block": 9 buffer chests at (-328.5..-326.5, -91.5..-89.5), each requesting the same fixed set).

Same pattern here: a 5 x 3 block of epic buffer chests (15) at tile (-340,-228), beside the three maker machines. Every chest requests the same list,
so the field holds 15 x the per-chest amount, and a chest also offers its stock to the requester chests of the makers and fluid units.
Items = the solid ingredients the Replicator's own recipes use most (see scripts/_r15_basics.py: counted over the assembler list, the furnace unit and the
fluid units), left out when the network is short of them: electronic-circuit, copper-plate, copper-cable, engine-unit, plastic-bar, speed-module sit at or
below zero in the network, so asking for a buffer of them would only deepen the shortage (the Replicator makes them on demand anyway). `--scarce` adds them.

Steps (read-only unless --apply): plan | build [--apply] | config | status
  plan    the per-chest list, field totals and the network's stock of each
  build   places the 15 chests (dry run without --apply), then `config`
  config  sets each chest's requests to the list (re-run after editing ITEMS)"""
import json
import sys

from _game import tools

ORIGIN = (-340, -228)          # top-left tile of the field
COLS, ROWS = 5, 3
Q = {"quality": "epic"}
DEMAND = (-352, -229)          # the Replicator's roboport (to read network stock)

# per-chest request minimum; field total = this x 15
ITEMS = {
    "steel-plate": 150,             # 70 recipes use it
    "iron-plate": 400,              # 41
    "iron-gear-wheel": 60,          # 40
    "advanced-circuit": 60,         # 35
    "processing-unit": 30,          # 35
    "pipe": 25,                     # 14
    "low-density-structure": 30,    # 8
    "stone-brick": 30,              # 5 (network holds about 3,000)
    "iron-stick": 40,               # 5
    "explosives": 20,               # 9
    "battery": 10,                  # 5 (network holds about 970)
}
SCARCE = {                          # only with --scarce
    "electronic-circuit": 60,       # 47
    "copper-plate": 60,             # 15
    "copper-cable": 100,            # 15
    "engine-unit": 6,               # 6
    "plastic-bar": 20,              # 4
}


def items():
    d = dict(ITEMS)
    if "--scarce" in sys.argv:
        d.update(SCARCE)
    return d


def chests():
    x0, y0 = ORIGIN
    return [{"name": "buffer-chest", "x": x0 + c + 0.5, "y": y0 + r + 0.5, "direction": 0, "params": dict(Q)} for r in range(ROWS) for c in range(COLS)]


STOCK = r'''
local rp = game.surfaces.nauvis.find_entities_filtered{name = 'roboport', position = {DX, DY}, radius = 0.6}[1]
local net = rp.logistic_network
local o = {}
for _, it in pairs({LIST}) do o[#o + 1] = it .. '=' .. net.get_item_count(it) end
rcon.print(table.concat(o, ','))
'''

CONFIG = r'''
local s = game.surfaces.nauvis
local X0, Y0, COLS, ROWS = X0V, Y0V, COLSV, ROWSV
local want = {WANT}
local n, bad = 0, 0
for r = 0, ROWS - 1 do
  for c = 0, COLS - 1 do
    local ch = s.find_entities_filtered{name = 'buffer-chest', position = {X0 + c + 0.5, Y0 + r + 0.5}, radius = 0.4}[1]
    if ch then
      local pt = ch.get_logistic_point(defines.logistic_member_index.logistic_container)
      while pt.sections_count > 0 do pt.remove_section(1) end
      local sec = pt.add_section()
      local k = 0
      for name, amount in pairs(want) do k = k + 1 sec.set_slot(k, {value = {type = 'item', name = name, quality = 'normal'}, min = amount}) end
      n = n + 1
    else bad = bad + 1 end
  end
end
rcon.print('buffer chests configured ' .. n .. ', missing ' .. bad .. ', items each ' .. (function() local c = 0 for _ in pairs(want) do c = c + 1 end return c end)())
'''

STATUS = r'''
local s = game.surfaces.nauvis
local X0, Y0, COLS, ROWS = X0V, Y0V, COLSV, ROWSV
local tot, got, per = 0, 0, {}
local n = 0
for r = 0, ROWS - 1 do
  for c = 0, COLS - 1 do
    local ch = s.find_entities_filtered{name = 'buffer-chest', position = {X0 + c + 0.5, Y0 + r + 0.5}, radius = 0.4}[1]
    if ch then
      n = n + 1
      local inv = ch.get_inventory(defines.inventory.chest)
      for _, it in pairs(inv.get_contents()) do per[it.name] = (per[it.name] or 0) + it.count end
    end
  end
end
local o = {}
for k, v in pairs(per) do o[#o + 1] = k .. '=' .. v end
table.sort(o)
rcon.print('chests ' .. n .. ' holding: ' .. table.concat(o, ', '))
'''


def sub(code, want):
    return (code.replace("X0V", str(ORIGIN[0])).replace("Y0V", str(ORIGIN[1])).replace("COLSV", str(COLS)).replace("ROWSV", str(ROWS))
            .replace("WANT", ",".join(f"['{k}']={v}" for k, v in want.items())).replace("DX", str(DEMAND[0])).replace("DY", str(DEMAND[1]))
            .replace("LIST", ",".join(f"'{k}'" for k in want)))


def main():
    step = sys.argv[1] if len(sys.argv) > 1 else "plan"
    apply = "--apply" in sys.argv
    want = items()
    n = COLS * ROWS
    if step == "plan":
        stock = dict(kv.split("=") for kv in tools["run_lua"](sub(STOCK, want)).strip().split(","))
        print(f"{n} buffer chests at tile {ORIGIN}; every chest requests:")
        for k, v in want.items():
            print(f"  {k:24s} {v:5d} per chest   field {v * n:6d}   network stock {stock.get(k, '?')}")
    elif step == "build":
        r = json.loads(tools["place_entities"](json.dumps(chests()), surface="nauvis", dry_run=not apply))
        print("placed" if apply else "dry run", r.get("placed"), "failed", json.dumps(r.get("failed") or [])[:300])
        if apply:
            print(tools["run_lua"](sub(CONFIG, want)))
    elif step == "config":
        print(tools["run_lua"](sub(CONFIG, want)))
    elif step == "status":
        print(tools["run_lua"](sub(STATUS, want)))


if __name__ == "__main__":
    main()
