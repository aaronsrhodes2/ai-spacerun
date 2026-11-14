"""Read only: what the White Science collectors hold, sampled twice (default 180 s apart), to estimate chunk income while their
inserters are blocked. Prints per kind the total at both times, the tick span, and how many collectors' inserters were blocked.
Usage: _white_income.py [seconds]"""
import sys
import time

from _game import tools

SECS = int(sys.argv[1]) if len(sys.argv) > 1 else 180
LUA = ("local s=game.surfaces['platform-1'] local t={} local full,blocked,n=0,0,0 for _,c in pairs(s.find_entities_filtered{type='asteroid-collector'}) do n=n+1 local inv=c.get_output_inventory() "
       "for _,it in pairs(inv.get_contents()) do t[it.name:sub(1,3)]=(t[it.name:sub(1,3)] or 0)+it.count end if inv.count_empty_stacks()==0 then full=full+1 end end "
       "for _,i in pairs(s.find_entities_filtered{type='inserter'}) do local pt=i.pickup_target if pt and pt.type=='asteroid-collector' and i.status==defines.entity_status.waiting_for_space_in_destination then blocked=blocked+1 end end "
       "local inv=s.find_entities_filtered{type='asteroid-collector'}[1].get_output_inventory() "
       "rcon.print(game.tick..' met '..(t.met or 0)..' car '..(t.car or 0)..' oxi '..(t.oxi or 0)..' collectors '..n..' full '..full..' blocked inserters '..blocked..' slots each '..#inv..' free chunks in space '..s.count_entities_filtered{type='asteroid-chunk'})")
a = tools["run_lua"](LUA).strip()
print(a)
time.sleep(SECS)
b = tools["run_lua"](LUA).strip()
print(b)
pa, pb = a.split(), b.split()
mins = (int(pb[0]) - int(pa[0])) / 3600.0
print("game minutes %.2f: metallic %+.1f/min, carbonic %+.1f/min, oxide %+.1f/min (held in collectors; chunks that left by inserter are not counted)"
      % (mins, (int(pb[2]) - int(pa[2])) / mins, (int(pb[4]) - int(pa[4])) / mins, (int(pb[6]) - int(pa[6])) / mins))
