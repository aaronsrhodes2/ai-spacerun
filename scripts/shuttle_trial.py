"""
Fly a space platform one leg and record what happens: sends it to --to, then every few seconds rebuilds what asteroids destroyed (free in friendly
build mode) and prints speed, route, magazines per turret, magazines on belts, what was rebuilt, water, thruster fuel and oxidizer.
The last line is the leg's summary. The platform stays parked at the destination (long wait in the schedule).

Usage: scripts/shuttle_trial.py --to fulgora [--platform 4] [--every 5] [--minutes 30]
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


def arg(name, default):
    return type(default)(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def main():
    platform, to, every, minutes = arg("--platform", 4), arg("--to", "fulgora"), arg("--every", 5), arg("--minutes", 30)
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
