#!/usr/bin/env python3
"""Edgerunner NORTH SPOKE: railgun rounds from the works to the six apex railguns (the Captain, 2026-11-18: "Make the railgun rounds on the ship").
The works have made railgun rounds from chunks since stage 2, but their output belt (x -5, rows -36..-19) went nowhere: the side belts have
two lanes and both are taken (magazines, rockets), and a third kind on a dead-end lane clogs it. So the rounds get a belt of their own, the
short way: straight north through the open middle of the frame, one tile of deck wide.

  start    the works' output belt ends at (-5,-36); it dives under the west ammunition feed (row -38) by underground belt (-37 -> -39)
  spoke    x -5, rows -40 .. -526, flowing north. Railgun rounds only, so its dead ends cannot clog.
  taps     at each pair of railguns two splitters in a row on the spoke: the first sends half east (arm row R+1), the second half west
           (arm row R), the rest goes on north. Tiers R = -468, -499, -527 (the railguns' centre rows are -467.5, -498.5, -526.5).
  arms     one belt from the spoke to the inner side of each railgun pad, one bulk inserter (filter railgun rounds) into the turret.
The six stage-1 inserters that fed the railguns from the old mixed side belts stay; those belts no longer carry railgun rounds.
DECK     tile ghosts, laid by the hub from its foundation stock (about 710; request `foundation-works 37` raised while this is built).
Steps: plan | deck | build [--apply] | config | status
Usage: edge_spoke.py plan ; edge_spoke.py deck ; edge_spoke.py build --apply ; edge_spoke.py status"""
import sys

import triangle_miner as TM
from _game import tools
from edge_works import T

L = tools["run_lua"]
BELT, UG, SPLIT, BULK = "express-transport-belt", "express-underground-belt", "express-splitter", "bulk-inserter"
N, E, S, W = 0, 4, 8, 12
C = -5                                                  # the spoke's column
TIERS = [(-468, 54), (-499, 36), (-527, 20)]            # (west arm row, |x| of the arm's inserter): going north
ROUND = "railgun-ammo"


def layout():
    e = [T(UG, C, -37, N, type="input"), T(UG, C, -39, N, type="output")]
    tiles = {(C, -39)}
    y = -40
    ins = []
    for k, (r, xi) in enumerate(TIERS):
        last = k == len(TIERS) - 1
        while y > r + 2:                                # plain spoke up to the east splitter's row
            e.append(T(BELT, C, y, N))
            tiles.add((C, y))
            y -= 1
        e.append(T(SPLIT, C, r + 2, N, 2, 1))           # east tap: tiles (C, r+2), (C+1, r+2)
        e.append(T(SPLIT, C - 1, r + 1, N, 2, 1))       # west tap: tiles (C-1, r+1), (C, r+1)
        tiles |= {(C, r + 2), (C + 1, r + 2), (C - 1, r + 1), (C, r + 1)}
        for x in range(C + 1, xi):                      # east arm on row r+1
            e.append(T(BELT, x, r + 1, E))
            tiles.add((x, r + 1))
        e.append(T(BULK, xi, r + 1, W))
        tiles.add((xi, r + 1))
        ins.append((xi, r + 1))
        for x in range(C - 1, -xi, -1):                 # west arm on row r
            e.append(T(BELT, x, r, W))
            tiles.add((x, r))
        e.append(T(BULK, -xi, r, E))
        tiles.add((-xi, r))
        ins.append((-xi, r))
        if not last:
            e.append(T(BELT, C, r, N))
            tiles.add((C, r))
        y = r - 1
    return e, tiles, ins


def cells(ts):
    return "{" + ",".join("{%d,%d}" % c for c in sorted(ts)) + "}"


CONFIG = (TM.AT + "local o={} local n=0 for _,q in pairs(INS) do local i=s.find_entities_filtered{type='inserter',position={q[1]+0.5,q[2]+0.5},radius=0.3}[1] if i then i.use_filters=true i.inserter_filter_mode='whitelist' "
          "i.set_filter(1,{name='railgun-ammo',quality='normal',comparator='='}) local t=i.drop_target if t and t.name=='railgun-turret' then n=n+1 else o[#o+1]='inserter '..q[1]..','..q[2]..' does NOT reach a railgun' end "
          "else o[#o+1]='NO inserter '..q[1]..','..q[2] end end rcon.print('arm inserters reaching a railgun '..n..' of '..#INS..(#o>0 and (' | '..table.concat(o,' ; ')) or ''))")

STATUS = (TM.AT + "local o={} local n=0 for _,b in pairs(s.find_entities_filtered{type={'transport-belt','underground-belt','splitter'},area={{-56,-530},{56,-36}}}) do if b.position.y<-36 and (math.abs(b.position.x+4.5)<1.6 or true) then "
          "for i=1,b.get_max_transport_line_index() do n=n+b.get_transport_line(i).get_item_count('railgun-ammo') end end end o[#o+1]='railgun rounds on belts north of the works '..n "
          "local r={} for _,t in pairs(s.find_entities_filtered{name='railgun-turret'}) do r[#r+1]=t.position.x..':'..t.get_inventory(defines.inventory.turret_ammo).get_item_count() end table.sort(r) o[#o+1]='railguns (x:rounds) '..table.concat(r,' ') "
          "o[#o+1]='tile ghosts '..s.count_entities_filtered{type='tile-ghost'}..', hub foundations '..p.hub.get_inventory(defines.inventory.hub_main).get_item_count('space-platform-foundation') rcon.print(table.concat(o,string.char(10)))")


def main():
    a = sys.argv[1:]
    step = a[0] if a else "status"
    ents, tiles, ins = layout()
    if step == "plan":
        r = L(TM.AT + "local need,blk=0,{} for _,q in pairs(" + cells(tiles) + ") do if s.get_tile(q[1],q[2]).name~='space-platform-foundation' then need=need+1 end "
              "for _,e in pairs(s.find_entities_filtered{area={{q[1]+0.1,q[2]+0.1},{q[1]+0.9,q[2]+0.9}}}) do if e.type~='tile-ghost' then blk[e.name]=(blk[e.name] or 0)+1 end end end "
              "local t={} for k,v in pairs(blk) do t[#t+1]=k..' '..v end rcon.print('deck missing '..need..', in the way: '..(#t>0 and table.concat(t,', ') or 'nothing'))")
        print(len(ents), "entities,", len(tiles), "tiles:", r.strip())
    elif step == "deck":
        print(L(TM.AT + "local n=0 for _,q in pairs(" + cells(tiles) + ") do if s.get_tile(q[1],q[2]).name~='space-platform-foundation' and "
                "s.count_entities_filtered{type='tile-ghost',position={q[1]+0.5,q[2]+0.5},radius=0.3}==0 then "
                "if s.create_entity{name='tile-ghost',inner_name='space-platform-foundation',position={q[1],q[2]},force='player'} then n=n+1 end end end rcon.print('tile ghosts laid '..n)"))
    elif step == "build":
        ok, bad = TM.place(ents, "--apply" in a)
        print("placed" if "--apply" in a else "dry run: would place", ok, "of", len(ents), "failed", bad)
        if "--apply" in a:
            print(L(CONFIG.replace("INS", cells(ins))))
    elif step == "config":
        print(L(CONFIG.replace("INS", cells(ins))))
    elif step == "status":
        print(L(STATUS))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
