#!/usr/bin/env python3
"""Edgerunner URANIUM ROUNDS (the Captain, 2026-11-18: "uranium rounds to protect the frame. It needs to pass undamaged").
Uranium rounds cannot be made from asteroids: they come from Nauvis (ammunition doctrine: uranium rounds are a Nauvis export). The hub asks
Nauvis for them (request group `edge-ammo 37`; the Replicator there makes them from piercing magazines and uranium-238, 25 a rocket) and
this line carries them from the hub to the two ammunition feeds on row -38, onto the magazine lane (the north lane). Guns take piercing and
uranium rounds from the same lane; a gun holds one kind at a time and takes the other when it is empty.

WHY THIS FIXES THE BREACH OF HOP 4: three times the damage a round, and the reserve now sits in the hub, at the SOURCE of the belts, so the
stretch next to each feed junction is the first to get fresh rounds instead of the last.

ROUTE (the hub is boxed in by the station ring; the only free hub face tile is (-5,3) on the west side)
  outlet   bulk inserter (-5,3), hub -> belt (-6,3), filter uranium rounds, created with its filter in the same tick
  inside   west on row 3 to x -8, north; under the ring's inserters and its row -1 belt (pipe to ground 2 -> -5); under the ring's top row
           and the oxide crusher (-7 -> -13); under the water main (-16 -> -18); north on x -8 to row -31
  split    splitter (-8..-7,-32): left goes on north to (-8,-36); inserter (-8,-37) drops on the WEST feed from the south = north lane
           right goes east on row -33, under the output belt, the west column and both buses (-6 -> 3, the full 9 tiles), under the
           column inserter (4 -> 7), east to x 11, north to (11,-36); inserter (11,-37) drops on the EAST feed
Steps: plan | build [--apply] | config | request MIN MAX | status
Usage: edge_uranium.py plan ; edge_uranium.py build --apply ; edge_uranium.py config ; edge_uranium.py request 500 1000 ; edge_uranium.py status"""
import sys

import triangle_miner as TM
from _game import tools
from edge_works import T

L = tools["run_lua"]
BELT, UG, SPLIT, BULK = "express-transport-belt", "express-underground-belt", "express-splitter", "bulk-inserter"
N, E, S, W = 0, 4, 8, 12
ROUND = "uranium-rounds-magazine"
GROUP = "edge-ammo 37"


def layout():
    e = [T(BELT, -6, 3, W), T(BELT, -7, 3, W), T(BELT, -8, 3, N),
         T(UG, -8, 2, N, type="input"), T(UG, -8, -5, N, type="output"), T(BELT, -8, -6, N),
         T(UG, -8, -7, N, type="input"), T(UG, -8, -13, N, type="output"), T(BELT, -8, -14, N), T(BELT, -8, -15, N),
         T(UG, -8, -16, N, type="input"), T(UG, -8, -18, N, type="output")]
    e += [T(BELT, -8, y, N) for y in range(-19, -32, -1)]
    e += [T(SPLIT, -8, -32, N, 2, 1)]
    e += [T(BELT, -8, y, N) for y in range(-33, -37, -1)]
    e += [T(BULK, -8, -37, S)]
    e += [T(BELT, -7, -33, E), T(UG, -6, -33, E, type="input"), T(UG, 3, -33, E, type="output"),
          T(UG, 4, -33, E, type="input"), T(UG, 7, -33, E, type="output")]
    e += [T(BELT, x, -33, E) for x in range(8, 11)]
    e += [T(BELT, 11, y, N) for y in range(-33, -37, -1)]
    e += [T(BULK, 11, -37, S)]
    return e


CONFIG = (TM.AT + "local o={} local function filt(e) e.use_filters=true e.inserter_filter_mode='whitelist' e.set_filter(1,{name='ROUND',quality='normal',comparator='='}) end "
          "local function at(x,y) return s.find_entities_filtered{type='inserter',position={x+0.5,y+0.5},radius=0.3}[1] end "
          "local out=at(-5,3) if not out then out=s.create_entity{name='bulk-inserter',position={-4.5,3.5},direction=4,quality='legendary',force='player'} if out then filt(out) end end "
          "if out then filt(out) o[#o+1]='outlet picks '..out.pickup_position.x..','..out.pickup_position.y..' drops '..out.drop_position.x..','..out.drop_position.y else o[#o+1]='NO outlet' end "
          "for _,q in pairs({{-8,-37},{11,-37}}) do local i=at(q[1],q[2]) if i then filt(i) o[#o+1]='feed inserter '..q[1]..' drops '..i.drop_position.x..','..i.drop_position.y else o[#o+1]='NO feed inserter '..q[1] end end "
          "rcon.print(table.concat(o,' | '))").replace("ROUND", ROUND)

REQUEST = (TM.AT + "local pt=p.hub.get_logistic_point()[1] local sec for _,x in pairs(pt.sections) do if x.group=='GROUP' then sec=x end end if not sec then sec=pt.add_section('GROUP') end "
           "sec.set_slot(1,{value={type='item',name='ROUND',quality='normal',comparator='='},min=MINV,max=MAXV,import_from='nauvis'}) rcon.print('request GROUP: ROUND min MINV max MAXV from nauvis')").replace("ROUND", ROUND).replace("GROUP", GROUP)

STATUS = (TM.AT + "local inv=p.hub.get_inventory(defines.inventory.hub_main) local o={} o[#o+1]='hub holds '..inv.get_item_count('ROUND')..' uranium rounds, '..inv.count_empty_stacks()..' free slots' "
          "local own,feed=0,0 for _,b in pairs(s.find_entities_filtered{type={'transport-belt','underground-belt','splitter'}}) do local n=0 for i=1,b.get_max_transport_line_index() do n=n+b.get_transport_line(i).get_item_count('ROUND') end "
          "if b.position.x>-9 and b.position.x<12 and b.position.y>-37 and b.position.y<4 and b.position.y~=-0.5 then own=own+n else feed=feed+n end end o[#o+1]='on the line from the hub '..own..', on the feeds and side belts '..feed "
          "local t,u,pz,e=0,0,0,0 for _,g in pairs(s.find_entities_filtered{name='gun-turret'}) do t=t+1 local a=g.get_inventory(defines.inventory.turret_ammo) if a.get_item_count('ROUND')>0 then u=u+1 elseif a.is_empty() then e=e+1 else pz=pz+1 end end "
          "o[#o+1]='gun turrets '..t..': uranium '..u..', piercing '..pz..', empty '..e "
          "local out=s.find_entities_filtered{type='inserter',position={4.5,1.5},radius=0.3}[1] local m={} for k,v in pairs(defines.entity_status) do m[v]=k end o[#o+1]='outlet '..(out and tostring(m[out.status]) or 'MISSING') "
          "local st=p.force.get_item_production_statistics('nauvis') o[#o+1]='Nauvis made in the last 10 min: '..string.format('%.0f',st.get_flow_count{name='ROUND',category='input',precision_index=defines.flow_precision_index.ten_minutes,count=true}) "
          "rcon.print(table.concat(o,string.char(10)))").replace("ROUND", ROUND)


def main():
    a = sys.argv[1:]
    step = a[0] if a else "status"
    if step == "plan":
        ok, bad = TM.place(layout(), False)
        print("dry run: would place", ok, "of", len(layout()), "failed", bad)
    elif step == "build":
        ok, bad = TM.place(layout(), "--apply" in a)
        print("placed" if "--apply" in a else "dry run: would place", ok, "of", len(layout()), "failed", bad)
        if "--apply" in a and not bad:
            print(L(CONFIG))
    elif step == "config":
        print(L(CONFIG))
    elif step == "request":
        print(L(REQUEST.replace("MINV", a[1]).replace("MAXV", a[2])))
    elif step == "status":
        print(L(STATUS))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
