"""Universal shuttle: flight log. One line every SECONDS (default 20) with place, speed, tanks, ammunition aboard (hub, belts, turrets), damaged and
missing pieces, power, asteroids in view; appended to snapshots/universal_shuttle_flight.log. Read-only.
Usage: _us_flightlog.py [MINUTES] [SECONDS]"""
import sys
import time
from pathlib import Path

import universal_shuttle as U

LOG = Path(__file__).resolve().parent.parent / "snapshots" / "universal_shuttle_flight.log"
LINE = (U.AT + "local fl={} for _,t in pairs(s.find_entities_filtered{name='storage-tank'}) do for k,v in pairs(t.get_fluid_contents()) do fl[k]=(fl[k] or 0)+v end end "
        "local inv=hub.get_inventory(defines.inventory.hub_main) local function all(n) local c=inv.get_item_count(n) for _,b in pairs(s.find_entities_filtered{type={'transport-belt','underground-belt','splitter'}}) do for li=1,b.get_max_transport_line_index() do c=c+b.get_transport_line(li).get_item_count(n) end end "
        "for _,t in pairs(s.find_entities_filtered{type='ammo-turret'}) do c=c+t.get_item_count(n) end return c end "
        "local dmg,n=0,0 for _,e in pairs(s.find_entities_filtered{force='player'}) do if e.type~='entity-ghost' and e.type~='tile-ghost' then n=n+1 if e.is_entity_with_health and e.health<e.max_health then dmg=dmg+1 end end end "
        "local a,cap=0,0 for _,e in pairs(s.find_entities_filtered{name='accumulator'}) do a=a+e.energy cap=cap+e.electric_buffer_size end local rocks={} for _,r in pairs(s.find_entities_filtered{type='asteroid'}) do local k=r.name:match('^(%a+)') rocks[k]=(rocks[k] or 0)+1 end "
        "local rk={} for k,v in pairs(rocks) do rk[#rk+1]=k..' '..v end local empty=0 for _,t in pairs(s.find_entities_filtered{type='ammo-turret'}) do if t.get_inventory(defines.inventory.turret_ammo).is_empty() then empty=empty+1 end end "
        "local sc=p.schedule rcon.print(string.format('tick %d | %s | %.0f km/s | dist %.3f | fuel %d ox %d | mags hub %d all %d | rockets hub %d all %d | entities %d damaged %d ghosts %d | turrets empty %d | acc %.0f%% | stop %s wait %s s | asteroids %s',"
        "game.tick,p.space_location and p.space_location.name or ('flying to '..(p.space_connection and p.space_connection.to.name or '?')..'/'..(p.space_connection and p.space_connection.from.name or '?')),p.speed*60,p.distance or -1,fl['thruster-fuel'] or 0,fl['thruster-oxidizer'] or 0,"
        "inv.get_item_count('firearm-magazine'),all('firearm-magazine'),inv.get_item_count('explosive-rocket'),all('explosive-rocket'),n,dmg,s.count_entities_filtered{type='entity-ghost'},empty,cap>0 and 100*a/cap or 0,"
        "tostring(sc and sc.current),tostring(sc and math.floor(p.get_schedule().ticks_in_station/60)),table.concat(rk,' ')))")


def main():
    mins = float(sys.argv[1]) if len(sys.argv) > 1 else 30
    step = float(sys.argv[2]) if len(sys.argv) > 2 else 20
    end = time.time() + mins * 60
    with open(LOG, "a", encoding="utf-8") as f:
        while time.time() < end:
            try:
                line = U.L(LINE).strip()
            except Exception as e:                                # the tunnel may drop for a moment
                line = "read failed: %s" % e
            f.write(line + "\n")
            f.flush()
            time.sleep(step)


if __name__ == "__main__":
    main()
