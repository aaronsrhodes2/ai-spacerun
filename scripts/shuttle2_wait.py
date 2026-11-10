"""
Waits for parked build_shuttle2 ships to fill up: prints one row per ship every --every seconds (water, fuel, oxidizer, hub magazines, lowest turret)
and stops when the first ship named in --platforms passes the limits, or after --minutes. The rows give the refill rate at the planet it is parked at.

Usage: scripts/shuttle2_wait.py --platforms 5,6,7 [--water 15000] [--propellant 25000] [--mags 1200] [--every 120] [--minutes 120]
"""
import sys
import time

from _game import tools

LUA = ("local o={} for _,i in pairs({%s}) do local p=game.forces.player.platforms[i] local s=p.surface local w,fu,ox=0,0,0 "
       "for _,k in pairs(s.find_entities_filtered{type='storage-tank'}) do local c=k.get_fluid_contents() w=w+(c.water or 0) fu=fu+(c['thruster-fuel'] or 0) ox=ox+(c['thruster-oxidizer'] or 0) end "
       "local low=1e9 for _,x in pairs(s.find_entities_filtered{name='gun-turret'}) do low=math.min(low,x.get_item_count('firearm-magazine')) end "
       "o[#o+1]=i..','..math.floor(w)..','..math.floor(fu)..','..math.floor(ox)..','..p.hub.get_item_count('firearm-magazine')..','..low..','..p.hub.get_item_count('iron-plate') end "
       "rcon.print(game.tick..';'..table.concat(o,';'))")


def arg(name, default):
    return type(default)(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def main():
    platforms = arg("--platforms", "5,6,7")
    water, prop, mags, every, minutes = arg("--water", 15000), arg("--propellant", 25000), arg("--mags", 1200), arg("--every", 120), arg("--minutes", 120)
    end = time.time() + minutes * 60
    print("tick | per ship: platform,water,fuel,oxidizer,hub magazines,lowest turret,hub plates", flush=True)
    while time.time() < end:
        parts = tools["run_lua"](LUA % platforms).strip().split(";")
        if len(parts) > 1:
            print(" | ".join(parts), flush=True)
            f = [int(x) for x in parts[1].split(",")]
            if f[1] >= water and f[2] >= prop and f[3] >= prop and f[4] >= mags and f[5] >= 8:
                print(f"READY platform {f[0]}", flush=True)
                return
        time.sleep(every)
    print("NOT READY in time", flush=True)


if __name__ == "__main__":
    main()
