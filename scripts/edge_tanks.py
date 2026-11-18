#!/usr/bin/env python3
"""Edgerunner TANK FARM: massive storage for fluids (the Captain, 2026-11-18: "Give the ship massive storage for fluids and consumables").
The propellant plant (edge_stern.py) has 16 legendary tanks a fluid (1,000,000 each). This adds UNITS more blocks of 16 on each side, in the
same rows (262..285) further out along the inside of the base: oxidizer east, fuel west.
  unit     a pipe column (rows 261..285) with eight tanks on each side of it; unit j has its column at x 17 + 8j (west: mirrored)
  link     one pipe row on new deck above the tanks (row 261) from the plant's own tank column (x 17) to the last unit's column
  rows     everything stands at rows 261..285: clear of the thruster bar's exhaust zone (rows 163..251)
Steps: plan | deck | build [--apply] | status
Usage: edge_tanks.py plan ; edge_tanks.py deck ; edge_tanks.py build --apply ; edge_tanks.py status"""
import sys

import triangle_miner as TM
from _game import tools
from edge_works import T

L = tools["run_lua"]
UNITS = 4                                 # per side: 4 x 16 tanks = 4,000,000 more of each fluid
ROW_L, ROW_0, ROW_1 = 261, 262, 285


def layout():
    e, tiles = [], set()
    for side in (1, -1):
        def X(x, w=1):
            return x if side > 0 else -(x + w - 1)

        def put(name, x, y, w=1, h=1):
            e.append(T(name, X(x, w), y, 0, w, h))
            tiles.update((X(x, w) + i, y + j) for i in range(w) for j in range(h))

        for x in range(17, 17 + 8 * UNITS + 1):
            put("pipe", x, ROW_L)
        for j in range(1, UNITS + 1):
            c = 17 + 8 * j
            for y in range(ROW_0, ROW_1 + 1):
                put("pipe", c, y)
            for y0 in range(ROW_0, ROW_1, 3):
                put("storage-tank", c - 3, y0, 3, 3)
                put("storage-tank", c + 1, y0, 3, 3)
    return e, tiles


def cells(ts):
    return "{" + ",".join("{%d,%d}" % c for c in sorted(ts)) + "}"


STATUS = (TM.AT + "local n,cap,fl=0,0,{} for _,t in pairs(s.find_entities_filtered{type='storage-tank',area={{-60,255},{60,290}}}) do n=n+1 for k,v in pairs(t.get_fluid_contents()) do fl[k]=(fl[k] or 0)+v end end "
          "local f={} for k,v in pairs(fl) do f[#f+1]=k..' '..math.floor(v) end rcon.print('tanks '..n..', holding '..table.concat(f,', ')..' | tile ghosts '..s.count_entities_filtered{type='tile-ghost'})")


def main():
    a = sys.argv[1:]
    step = a[0] if a else "status"
    ents, tiles = layout()
    if step == "plan":
        r = L(TM.AT + "local need,blk=0,{} for _,q in pairs(" + cells(tiles) + ") do if s.get_tile(q[1],q[2]).name~='space-platform-foundation' then need=need+1 end "
              "for _,e in pairs(s.find_entities_filtered{area={{q[1]+0.1,q[2]+0.1},{q[1]+0.9,q[2]+0.9}}}) do if e.type~='tile-ghost' then blk[e.name..'@'..q[1]..','..q[2]]=1 end end end "
              "local t={} for k in pairs(blk) do t[#t+1]=k end rcon.print('deck missing '..need..', in the way: '..(#t>0 and table.concat(t,' ') or 'nothing'))")
        print(len(ents), "entities,", len(tiles), "tiles:", r.strip()[:600])
    elif step == "deck":
        print(L(TM.AT + "local n=0 for _,q in pairs(" + cells(tiles) + ") do if s.get_tile(q[1],q[2]).name~='space-platform-foundation' and "
                "s.count_entities_filtered{type='tile-ghost',position={q[1]+0.5,q[2]+0.5},radius=0.3}==0 then "
                "if s.create_entity{name='tile-ghost',inner_name='space-platform-foundation',position={q[1],q[2]},force='player'} then n=n+1 end end end rcon.print('tile ghosts laid '..n)"))
    elif step == "build":
        ok, bad = TM.place(ents, "--apply" in a)
        print("placed" if "--apply" in a else "dry run: would place", ok, "of", len(ents), "failed", bad)
    elif step == "status":
        print(L(STATUS))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
