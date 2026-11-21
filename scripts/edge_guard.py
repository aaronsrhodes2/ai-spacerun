#!/usr/bin/env python3
"""Edgerunner flight guard (plan "Solve Space Age": the abort rule). Samples every SECONDS; if a limit is crossed it turns the ship back to HOME
by rewriting the schedule (the ship decelerates and returns), and says why. Read-and-steer only: it moves no goods.
Limits: accumulators under 30 %, more than 10 empty ammunition turrets, fuel cells (reactor + hub) under CELLS, entities destroyed
since the start over LOSS, fuel or oxidizer under 600,000.
Usage: edge_guard.py watch HOME [SECONDS] [MAXSAMPLES] [CELLS] [LOSS]"""
import sys
import time

import edge_flight as F
from _game import tools

L = tools["run_lua"]
S = ("local p=game.forces.player.platforms[37] local s=p.surface local a,c=0,0 for _,e in pairs(s.find_entities_filtered{type='accumulator'}) do a=a+e.energy c=c+e.electric_buffer_size end "
     "local em=0 for _,t in pairs(s.find_entities_filtered{type='ammo-turret'}) do if t.get_inventory(defines.inventory.turret_ammo).is_empty() then em=em+1 end end "
     "local cells=p.hub.get_inventory(defines.inventory.hub_main).get_item_count('fusion-power-cell') for _,r in pairs(s.find_entities_filtered{name='fusion-reactor'}) do cells=cells+r.get_item_count('fusion-power-cell') end "
     "local fl={} for _,t in pairs(s.find_entities_filtered{type='storage-tank'}) do for k,v in pairs(t.get_fluid_contents()) do fl[k]=(fl[k] or 0)+v end end local n=s.count_entities_filtered{force='player'} "
     "local gp=s.count_entities_filtered{type='entity-ghost'} local c2=p.space_connection local where=p.space_location and ('at '..p.space_location.name) or (c2 and string.format('%s %.0f/%d km',c2.name,p.distance*c2.length,c2.length) or '?') "
     "rcon.print(string.format('%.3f|%d|%d|%d|%d|%d|%d|%s|%.1f',a/c,em,cells,fl['thruster-fuel'] or 0,fl['thruster-oxidizer'] or 0,n,gp,where,p.speed*60))")


def main():
    a = sys.argv[1:]
    if not a or a[0] != "watch":
        print(__doc__)
        return
    home = a[1]
    sec = float(a[2]) if len(a) > 2 else 60
    mx = int(a[3]) if len(a) > 3 else 100
    cells_min = int(a[4]) if len(a) > 4 else 30
    loss_max = int(a[5]) if len(a) > 5 else 300
    n0 = None
    for i in range(mx):
        acc, em, cells, fu, ox, n, gh, where, sp = L(S).strip().split("|")
        acc, em, cells, fu, ox, n, gh = float(acc), int(em), int(cells), int(fu), int(ox), int(n), int(gh)
        n0 = n0 or n
        print("%s | %s | %.1f km/s | accumulators %.0f%% | empty %d | cells %d | fuel %d ox %d | lost %d ghosts %d" % (time.strftime("%H:%M:%S"), where, float(sp), acc * 100, em, cells, fu, ox, max(0, n0 - n + gh), gh), flush=True)
        why = None
        if acc < 0.30: why = "accumulators under 30%"
        elif em > 10: why = "%d empty turrets" % em
        elif cells < cells_min: why = "fusion cells %d" % cells
        elif max(0, n0 - n + gh) > loss_max: why = "hull losses over %d" % loss_max
        elif fu < 600000 or ox < 600000: why = "propellant low"
        if why:
            print("ABORT: " + why + " -> turning back to " + home, flush=True)
            print(L(F.GO.replace("PLANET", home)))
            return
        if where.startswith("at ") and i > 0 and "at" in where and where[3:] != home and sp == "0.0":
            print("arrived: " + where)
            return
        time.sleep(sec)


if __name__ == "__main__":
    main()
