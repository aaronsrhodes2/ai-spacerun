"""
Fly a space platform one leg and record what happens: sends it to --to, then every few seconds rebuilds what asteroids destroyed (free in friendly
build mode) and prints speed, route, magazines per turret, magazines on belts, what was rebuilt, water, thruster fuel and oxidizer.
The last line is the leg's summary. The platform stays parked at the destination (long wait in the schedule).

It refuses to launch unless the pre-flight guard passes (turrets armed, magazine stock, propellant; water and reactor heat only matter on a nuclear ship) and saves the game first.

Usage: scripts/shuttle_trial.py --to fulgora [--platform 5] [--every 5] [--minutes 30] [--mags 1500] [--water 0] [--propellant 40000]
"""
import sys
import time

from _game import tools

GO = ("local p=game.forces.player.platforms[%d] p.schedule={current=1,records={{station='%s',wait_conditions={{type='time',ticks=360000,compare_type='and'}}}}} "
      "p.paused=false rcon.print('go '..game.tick)")

LUA = ("local p=game.forces.player.platforms[%d] local s=p.surface local t,e=0,0 for pass=1,12 do local did=0 "
       "for _,g in pairs(s.find_entities_filtered{type='tile-ghost'}) do if g.valid and g.revive() then t=t+1 did=did+1 end end "
       "for _,g in pairs(s.find_entities_filtered{type='entity-ghost'}) do if g.valid and g.revive() then e=e+1 did=did+1 end end if did==0 then break end end "
       "local tu={} for _,x in pairs(s.find_entities_filtered{name='gun-turret'}) do tu[#tu+1]=x.get_item_count('firearm-magazine') end "
       "local belt=0 for _,b in pairs(s.find_entities_filtered{type={'transport-belt','underground-belt','splitter'}}) do belt=belt+b.get_item_count('firearm-magazine') end "
       "local w,fu,ox=0,0,0 for _,k in pairs(s.find_entities_filtered{type='storage-tank'}) do local c=k.get_fluid_contents() w=w+(c.water or 0) fu=fu+(c['thruster-fuel'] or 0) ox=ox+(c['thruster-oxidizer'] or 0) end "
       "local made=0 for _,a in pairs(s.find_entities_filtered{name='assembling-machine-3'}) do made=made+a.products_finished end "
       "rcon.print((p.space_location and p.space_location.name or '-')..'|'..string.format('%%.1f',p.speed*60)..'|'..string.format('%%.3f',p.distance or -1)..'|'..t..'|'..e..'|'..table.concat(tu,',')"
       "..'|'..belt..'|'..made..'|'..math.floor(w)..'|'..math.floor(fu)..'|'..math.floor(ox)..'|'..game.tick)")


# Pre-flight guard, added after the first shuttle was lost flying with empty turrets (2026-11-10). No launch unless every line passes.
GUARD = ("local p=game.forces.player.platforms[%d] local s=p.surface local low,n=1e9,0 for _,x in pairs(s.find_entities_filtered{name='gun-turret'}) do n=n+1 "
         "low=math.min(low,x.get_item_count('firearm-magazine')) end local w,fu,ox=0,0,0 for _,k in pairs(s.find_entities_filtered{type='storage-tank'}) do "
         "local c=k.get_fluid_contents() w=w+(c.water or 0) fu=fu+(c['thruster-fuel'] or 0) ox=ox+(c['thruster-oxidizer'] or 0) end "
         "local r=s.find_entities_filtered{name='nuclear-reactor'}[1] "
         "rcon.print(n..'|'..low..'|'..p.hub.get_item_count('firearm-magazine')..'|'..math.floor(w)..'|'..math.floor(fu)..'|'..math.floor(ox)..'|'..(r and math.floor(r.temperature) or 999)"
         "..'|'..#s.find_entities_filtered{type={'entity-ghost','tile-ghost'}})")


def guard(platform, mags, water, propellant):
    f = [int(x) for x in tools["run_lua"](GUARD % platform).strip().split("|")]
    checks = [("turrets on board", f[0] > 0, f[0]), ("every turret holds 8+ magazines", f[1] >= 8, f[1]), (f"hub magazines >= {mags}", f[2] >= mags, f[2]),
              (f"water >= {water}", f[3] >= water, f[3]), (f"thruster fuel >= {propellant}", f[4] >= propellant, f[4]),
              (f"oxidizer >= {propellant}", f[5] >= propellant, f[5]), ("reactor at 500 C or more", f[6] >= 500, f[6]), ("nothing waiting to be rebuilt", f[7] == 0, f[7])]
    for name, ok, val in checks:
        print(f"  {'ok  ' if ok else 'FAIL'} {name}: {val}", flush=True)
    return all(ok for _, ok, _ in checks)


def arg(name, default):
    return type(default)(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def main():
    platform, to, every, minutes = arg("--platform", 5), arg("--to", "fulgora"), arg("--every", 5), arg("--minutes", 30)
    if not guard(platform, arg("--mags", 1500), arg("--water", 0), arg("--propellant", 40000)):
        print("NOT LAUNCHED: pre-flight guard failed", flush=True)
        sys.exit(1)
    print(tools["run_lua"]("game.server_save('before-flight-p%d') rcon.print('saved before-flight-p%d')" % (platform, platform)).strip(), flush=True)
    print(tools["run_lua"](GO % (platform, to)).strip(), flush=True)
    print("km/s | route | rebuilt tiles,entities | turret magazines | belt | made | water | fuel | oxidizer", flush=True)
    end = time.time() + minutes * 60
    tiles = ents = 0
    first = last = None
    left = False
    while time.time() < end:
        f = tools["run_lua"](LUA % platform).strip().split("|")
        if len(f) == 12:
            tiles, ents = tiles + int(f[3]), ents + int(f[4])
            first = first or f
            last = f
            print(f"{f[1]} | {f[2]} | {f[3]},{f[4]} | {f[5]} | {f[6]} | {f[7]} | {f[8]} | {f[9]} | {f[10]}", flush=True)
            left = left or f[0] == "-"
            if left and f[0] == to:
                break
        time.sleep(every)
    if first and last:
        secs = (int(last[11]) - int(first[11])) / 60
        used = lambda i: int(first[i]) - int(last[i])
        print(f"LEG to {to}: {secs:.0f} s, rebuilt {tiles} tiles {ents} entities, magazines made {-used(7)}, "
              f"water {first[8]}->{last[8]}, fuel used {used(9)}, oxidizer used {used(10)}, arrived={last[0] == to}", flush=True)


if __name__ == "__main__":
    main()
