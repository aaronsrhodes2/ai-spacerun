#!/usr/bin/env python3
"""Watches the Fulgora-Aquilo shuttle: one line a minute; exits when it reaches Aquilo, when it is hurt in flight, or after MAX minutes.
A local loop with one short RCON call per pass (never a loop inside the game).
Usage: watch_aquilo.py [MAX_MINUTES]"""
import sys
import time

from _game import tools

LUA = ("local s=game.surfaces['platform-14'] local p=s.platform local inv=p.hub.get_inventory(defines.inventory.hub_main) local r=inv.get_item_count('rocket') "
       "for _,t in pairs(s.find_entities_filtered{name='rocket-turret'}) do r=r+t.get_inventory(defines.inventory.turret_ammo).get_item_count() end "
       "for _,e in pairs(s.find_entities_filtered{type={'transport-belt','underground-belt'}}) do for l=1,2 do r=r+e.get_transport_line(l).get_item_count('rocket') end end "
       "local hurt,n=0,0 for _,e in pairs(s.find_entities_filtered{force='player'}) do if e.health and e.max_health and e.max_health>0 then n=n+1 if e.health<e.max_health*0.99 then hurt=hurt+1 end end end "
       "local big=0 for _,a in pairs(s.find_entities_filtered{type='asteroid'}) do if a.name:find('big') or a.name:find('huge') then big=big+1 end end local fl=0 for _,t in pairs(s.find_entities_filtered{name='storage-tank'}) do fl=fl+(t.get_fluid_contents()['thruster-fuel'] or 0) end "
       "rcon.print((p.space_location and p.space_location.name or 'flight')..'|'..string.format('%.3f',p.distance or -1)..'|'..string.format('%.0f',(p.speed or 0)*60)..'|'..r..'|'..inv.get_item_count('carbon')..'|'..hurt..'|'..n..'|'..big..'|'..string.format('%.0f',fl))")

limit = int(sys.argv[1]) if len(sys.argv) > 1 else 120
start_n = None
for i in range(limit * 2):
    try:
        loc, dist, speed, rockets, carbon, hurt, n, big, fuel = tools["run_lua"](LUA).strip().split("|")
    except Exception as e:                       # a dropped tunnel: try again next pass
        print("read failed", str(e)[:80], flush=True)
        time.sleep(30)
        continue
    start_n = start_n or int(n)
    if i % 2 == 0 or loc == "flight":
        print(time.strftime("%H:%M:%S"), loc, "dist", dist, "km/s", speed, "rockets", rockets, "carbon", carbon, "hurt", hurt, "entities", n, "big asteroids", big, "fuel", fuel, flush=True)
    if loc == "aquilo":
        print("ARRIVED at Aquilo", flush=True)
        break
    if loc == "flight" and (int(hurt) > 8 or int(n) < start_n - 2 or int(rockets) < 40):
        print("TROUBLE in flight", flush=True)
        break
    time.sleep(30)
