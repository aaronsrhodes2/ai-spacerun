#!/usr/bin/env python3
"""Edgerunner THRUSTER BAR: the propulsion moved inside the frame (the Captain, 2026-11-18: "Put the propulsion on the inside of the triangle
frame not the bottom edge").
THE RULE (read from the game, not assumed): a thruster needs deck under itself and EMPTY SPACE for 88 tiles below it (its own four columns,
from 2.7 to 90.3 tiles south of its centre). It does not need a clear path to the bottom of the ship. So the thrusters can stand on a
crossbar inside the triangle as long as nothing is built in the 88 rows under them.

  BAR      rows 154..162 across the south spoke, x -77..77: two banks of 12 thrusters (west tiles -76..-7, east 6..77, pitch 6, top row 158),
           fuel header row 154, oxidizer header row 156, the gap plumbing as on the stern. The middle (x -4..4) carries the spoke belt and
           the two feeds. EXHAUST ZONE: rows 163..251 under both banks stay empty; the propellant plant's deck starts at row 262.
  FEEDS    from the two throttle pumps on row 286 (unchanged) north along the spoke by pipe to ground: oxidizer on x 1, fuel on x -1
           (eleven hops each, under the crushers' inserters and the overflow), to the bar.
  SWITCH   when the bar's thrusters hold both fluids, the 24 stern thrusters and their headers (rows 289..297) are taken out: the bottom
           edge is then free for turrets.
Steps: plan | deck | build [--apply] | switch [--apply] | status
Usage: edge_bar.py plan ; edge_bar.py deck ; edge_bar.py build --apply ; edge_bar.py status ; edge_bar.py switch --apply"""
import sys

import triangle_miner as TM
from _game import tools
from edge_works import T

L = tools["run_lua"]
PIPE, PTG = "pipe", "pipe-to-ground"
N, E, S, W = 0, 4, 8, 12
RT = 158                                  # top row of the thrusters
PITCH, NB = 6, 12                         # per bank
XW, XE = -76, 6                           # first thruster tile of the west and the east bank
HOPS = [(285, 275), (274, 264), (263, 253), (252, 242), (241, 231), (230, 220), (219, 209), (208, 198), (197, 187), (186, 176), (175, 165)]


def layout():
    e, tiles = [], set()

    def put(name, x, y, d=0, w=1, h=1):
        e.append(T(name, x, y, d, w, h))
        tiles.update((x + i, y + j) for i in range(w) for j in range(h))

    def pipes(*cells):
        for x, y in cells:
            put(PIPE, x, y)

    for x0 in (XW, XE):
        last = x0 + PITCH * (NB - 1)
        xw, xe = x0 - 1, last + 5
        for k in range(NB):
            put("thruster", x0 + PITCH * k, RT, 0, 4, 5)
        for k in range(NB - 1):
            a = x0 + PITCH * k + 4
            if k % 2 == 0:                              # oxidizer gap
                pipes((a, RT - 1), (a, RT), (a, RT + 1), (a + 1, RT + 1), (a + 1, RT + 2))
            else:                                       # fuel gap: down from the fuel header under the oxidizer header
                gx = a + 1
                put(PTG, gx, RT - 3, N)
                put(PTG, gx, RT - 1, S)
                pipes((gx, RT), (gx, RT + 1), (gx - 1, RT + 1), (gx - 1, RT + 2))
        pipes(*[(x, RT - 4) for x in range(xw, xe + 1)])                    # fuel header
        pipes(*[(xw, y) for y in range(RT - 3, RT + 1)])                     # west cap: first thruster's west-top fuel port
        pipes(*[(xe, y) for y in range(RT - 3, RT + 3)], (xe - 1, RT + 2))   # east cap: last thruster's east-middle fuel port
        pipes(*[(x, RT - 2) for x in range(x0 + 4, last - 1)])               # oxidizer header
    # the middle: fuel link under the spoke belt, oxidizer link under both caps and the belt
    pipes((-4, RT - 4), (-3, RT - 4), (-2, RT - 4), (2, RT - 4), (3, RT - 4), (4, RT - 4))
    put(PTG, -1, RT - 4, W)
    put(PTG, 1, RT - 4, E)
    pipes(*[(x, RT - 2) for x in range(-11, -6)], (-3, RT - 2), (-2, RT - 2), (2, RT - 2), (3, RT - 2), (7, RT - 2), (8, RT - 2), (9, RT - 2))
    for a, b in ((-6, -4), (-1, 1), (4, 6)):
        put(PTG, a, RT - 2, W)
        put(PTG, b, RT - 2, E)
    # feeds: oxidizer up x 1 into the link at (2, RT-2); fuel up x -1 into the west bank's east cap at (-5, RT+2)
    pipes((2, 286), (1, 286), (-2, 286), (-1, 286))
    for x in (1, -1):
        for a, b in HOPS:
            put(PTG, x, a, S)
            put(PTG, x, b, N)
        pipes(*[(x, y) for y in range(164, RT + 2, -1)])
    pipes(*[(2, y) for y in range(RT + 3, RT - 2, -1)])
    pipes(*[(x, RT + 3) for x in range(-2, -6, -1)])
    bar = {(x, y) for x in range(XW - 1, XE + PITCH * (NB - 1) + 6) for y in range(RT - 4, RT + 5)}
    return e, tiles | bar


def cells(ts):
    return "{" + ",".join("{%d,%d}" % c for c in sorted(ts)) + "}"


ZONE = (TM.AT + "local n,ex=0,{} for _,x0 in pairs({XW,XE}) do for k=0,NB-1 do local a=x0+PITCH*k for _,t in pairs(s.find_tiles_filtered{area={{a,RT+5},{a+4,RT+93}},name='space-platform-foundation'}) do n=n+1 if #ex<6 then ex[#ex+1]=t.position.x..','..t.position.y end end end end "
        "rcon.print('deck tiles in the exhaust zone '..n..(n>0 and (' e.g. '..table.concat(ex,' ')) or ''))").replace("XW", str(XW)).replace("XE", str(XE)).replace("NB", str(NB)).replace("PITCH", str(PITCH)).replace("RT", str(RT))

SWITCH = (TM.AT + "local inv=p.hub.get_inventory(defines.inventory.hub_main) local fed=0 for _,t in pairs(s.find_entities_filtered{name='thruster',area={{-80,RT-1},{80,RT+6}}}) do local c=t.get_fluid_contents() if (c['thruster-fuel'] or 0)>0 and (c['thruster-oxidizer'] or 0)>0 then fed=fed+1 end end "
          "if fed<24 then rcon.print('bar thrusters holding both fluids '..fed..' of 24: stern left alone') return end local n={} "
          "for _,e in pairs(s.find_entities_filtered{area={{-76,288.9},{77,298.1}},name={'thruster','pipe','pipe-to-ground'}}) do n[e.name]=(n[e.name] or 0)+1 e.destroy() end "
          "for _,q in pairs({{3.5,287.5},{-2.5,287.5}}) do local e=s.find_entities_filtered{name='pipe-to-ground',position=q,radius=0.3}[1] if e then e.destroy() n['feed end']=(n['feed end'] or 0)+1 end end "
          "rcon.print('stern removed: '..helpers.table_to_json(n)..' ; thrusters now '..s.count_entities_filtered{name='thruster'})").replace("RT", str(RT))

STATUS = (TM.AT + "local m={} for k,v in pairs(defines.entity_status) do m[v]=k end local function bank(area) local th=s.find_entities_filtered{name='thruster',area=area} local fed,st=0,{} for _,t in pairs(th) do local c=t.get_fluid_contents() "
          "if (c['thruster-fuel'] or 0)>0 and (c['thruster-oxidizer'] or 0)>0 then fed=fed+1 end local k=tostring(m[t.status]) st[k]=(st[k] or 0)+1 end local ts={} for k,v in pairs(st) do ts[#ts+1]=k..' '..v end return #th..', holding both fluids '..fed..' ('..table.concat(ts,', ')..')' end "
          "local fl={} for _,t in pairs(s.find_entities_filtered{type='storage-tank'}) do for k,v in pairs(t.get_fluid_contents()) do fl[k]=(fl[k] or 0)+v end end local f={} for k,v in pairs(fl) do f[#f+1]=k..' '..math.floor(v) end "
          "rcon.print('bar thrusters '..bank({{-80,RT-1},{80,RT+6}})..string.char(10)..'stern thrusters '..bank({{-80,292},{80,299}})..string.char(10)..'tanks '..table.concat(f,', ')..string.char(10).."
          "'speed '..string.format('%.1f',p.speed*60)..' km/s, weight '..math.floor(p.weight/1000)..' t, tile ghosts '..s.count_entities_filtered{type='tile-ghost'}..', hub foundations '..p.hub.get_inventory(defines.inventory.hub_main).get_item_count('space-platform-foundation'))").replace("RT", str(RT))


def main():
    a = sys.argv[1:]
    step = a[0] if a else "status"
    ents, tiles = layout()
    if step == "plan":
        r = L(TM.AT + "local need,blk=0,{} for _,q in pairs(" + cells(tiles) + ") do if s.get_tile(q[1],q[2]).name~='space-platform-foundation' then need=need+1 end "
              "for _,e in pairs(s.find_entities_filtered{area={{q[1]+0.1,q[2]+0.1},{q[1]+0.9,q[2]+0.9}}}) do if e.type~='tile-ghost' then blk[e.name..'@'..q[1]..','..q[2]]=1 end end end "
              "local t={} for k in pairs(blk) do t[#t+1]=k end rcon.print('deck missing '..need..', in the way: '..(#t>0 and table.concat(t,' ') or 'nothing'))")
        print(len(ents), "entities,", len(tiles), "tiles:", r.strip())
        print(L(ZONE).strip())
    elif step == "deck":
        print(L(TM.AT + "local n=0 for _,q in pairs(" + cells(tiles) + ") do if s.get_tile(q[1],q[2]).name~='space-platform-foundation' and "
                "s.count_entities_filtered{type='tile-ghost',position={q[1]+0.5,q[2]+0.5},radius=0.3}==0 then "
                "if s.create_entity{name='tile-ghost',inner_name='space-platform-foundation',position={q[1],q[2]},force='player'} then n=n+1 end end end rcon.print('tile ghosts laid '..n)"))
    elif step == "build":
        ok, bad = TM.place(ents, "--apply" in a)
        print("placed" if "--apply" in a else "dry run: would place", ok, "of", len(ents), "failed", bad)
    elif step == "switch":
        if "--apply" in a:
            print(L(SWITCH))
        else:
            print("would remove the 24 stern thrusters and their headers once all 24 bar thrusters hold both fluids")
    elif step == "status":
        print(L(STATUS))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
