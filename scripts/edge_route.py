#!/usr/bin/env python3
"""Edgerunner's standing ROUTE round the inner planets (the Captain, 2026-11-18: "Make a route for the edge runner and see it able to run
the circular route continuously. No Aquila trip yet").
  circle    Nauvis -> Vulcanus -> Gleba -> Fulgora -> Nauvis (every leg 15,000 km, about 8.5 minutes at 30 km/s)
  Nauvis    the only place it is supplied. It leaves when the hub holds RESERVE uranium rounds AND 10 minutes have passed. The hub's
            outlet pushes rounds onto the side belts whenever they have room, so "the hub holds RESERVE" also means the belts are full.
  elsewhere 3 minutes (the works make about 150 piercing magazines a minute; nothing is supplied there)
`watch` logs one line a sample to snapshots/edge_route.log, MENDS (a destroyed legendary piece leaves a legendary ghost the hub cannot
build from its normal spares: such ghosts are remade as normal quality), and prints only what needs a look: damage, empty guns, arrivals.
Steps: set [RESERVE] | stop | status | watch [seconds] [samples]
Usage: edge_route.py set 2000 ; edge_route.py watch 60 200 ; edge_route.py stop"""
import sys
import time

import edge_flight as FL
from _game import tools

L = tools["run_lua"]
IDX = 37
CIRCLE = ["nauvis", "vulcanus", "gleba", "fulgora"]
LOG = "D:/Aaron/development/AI-factorio/snapshots/edge_route.log"

SET = ("local p=game.forces.player.platforms[%d] local r={} for _,n in pairs({PLANETS}) do local w if n=='nauvis' then "
       "w={{type='item_count',compare_type='and',condition={first_signal={type='item',name='uranium-rounds-magazine'},comparator='>=',constant=RESERVE}},{type='time',compare_type='and',ticks=36000}} "
       "else w={{type='time',compare_type='and',ticks=10800}} end r[#r+1]={station=n,wait_conditions=w} end "
       "local cur=1 local here=p.space_location and p.space_location.name for i,x in pairs(r) do if x.station==here then cur=i end end "
       "p.schedule={current=cur,records=r} p.paused=false local o={} for i,x in pairs(p.schedule.records) do o[#o+1]=x.station..'('..#x.wait_conditions..' conditions)' end rcon.print('route set: '..table.concat(o,' -> ')..' ; now at '..tostring(here))") % IDX
STOP = ("local p=game.forces.player.platforms[%d] local here=p.space_location and p.space_location.name or 'nauvis' "
        "p.schedule={current=1,records={{station=here,wait_conditions={{type='time',ticks=216000}}}}} rcon.print('route stopped; one stop at '..here)") % IDX
MEND = ("local p=game.forces.player.platforms[%d] local s=p.surface local inv=p.hub.get_inventory(defines.inventory.hub_main) local n=0 for _,g in pairs(s.find_entities_filtered{type='entity-ghost'}) do "
        "if g.quality.name~='normal' then local it=g.ghost_prototype.items_to_place_this local nm=it and it[1] and it[1].name if nm and inv.get_item_count{name=nm,quality='normal'}>0 then "
        "local pos,dir,gn=g.position,g.direction,g.ghost_name g.destroy() if s.create_entity{name='entity-ghost',inner_name=gn,position=pos,direction=dir,force='player',quality='normal'} then n=n+1 end end end end rcon.print(n)") % IDX


def watch(every, most):
    last_place, dmg_seen = None, 0
    for _ in range(most):
        try:
            mended = L(MEND).strip()
            line = L(FL.SAMPLE).strip()
        except Exception as e:
            line, mended = "read failed: %s" % e, "0"
        stamp = time.strftime("%H:%M:%S")
        with open(LOG, "a", encoding="utf-8") as f:
            f.write("%s %s | mended %s\n" % (stamp, line, mended))
        place = line.split(" | ")[0]
        at = place.startswith("at ")
        ghosts = int(line.split("ghosts ")[1].split(" ")[0]) if "ghosts " in line else 0
        empty = line.split("empty: ")[1].split(" | ")[0] if "empty: " in line else ""
        guns_empty = int(empty.split("gun-turret ")[1].split(",")[0]) if "gun-turret " in empty else 0
        if at and place != last_place:
            print(stamp, "ARRIVED", line, flush=True)
        elif ghosts > dmg_seen or guns_empty >= 3 or mended != "0":
            print(stamp, "ALERT", line, "| mended", mended, flush=True)
        dmg_seen = ghosts
        last_place = place
        time.sleep(every)


if __name__ == "__main__":
    a = sys.argv[1:]
    step = a[0] if a else "status"
    if step == "set":
        print(L(SET.replace("PLANETS", ",".join("'%s'" % n for n in CIRCLE)).replace("RESERVE", a[1] if len(a) > 1 else "2000")))
    elif step == "stop":
        print(L(STOP))
    elif step == "status":
        print(L("local p=game.forces.player.platforms[%d] local sc=p.schedule local o={} if sc then for i,x in pairs(sc.records) do o[#o+1]=(i==sc.current and '>' or '')..x.station end end rcon.print('route: '..table.concat(o,' ')..' ; paused '..tostring(p.paused))" % IDX))
        print(L(FL.SAMPLE))
    elif step == "watch":
        watch(int(a[1]) if len(a) > 1 else 60, int(a[2]) if len(a) > 2 else 120)
    else:
        sys.exit(__doc__)
