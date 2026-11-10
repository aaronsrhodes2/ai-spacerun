"""
Watch a space platform in flight: one line a minute with speed, distance along the route, armed turrets, magazines, damaged entities, ghosts
(a ghost on a platform is something an asteroid destroyed), thruster fuel and oxidizer, and the asteroids in view.
Stops when the platform reaches --until (a planet name), when --max-damaged entities are damaged, or after --minutes.

Usage: scripts/shuttle_watch.py [--platform 4] [--until fulgora] [--minutes 40] [--max-damaged 25] [--every 60]
"""
import sys
import time

from _game import tools

LUA = ("local p=game.forces.player.platforms[%d] local s=p.surface local tot,have,nt=0,0,0 for _,t in pairs(s.find_entities_filtered{name='gun-turret'}) do nt=nt+1 "
       "local n=t.get_item_count('firearm-magazine') tot=tot+n if n>0 then have=have+1 end end local dmg,cnt=0,0 "
       "for _,e in pairs(s.find_entities_filtered{force='player'}) do cnt=cnt+1 if e.health and e.max_health and e.health<e.max_health then dmg=dmg+1 end end "
       "local fu,ox=0,0 for _,e in pairs(s.find_entities_filtered{type='storage-tank'}) do local c=e.get_fluid_contents() fu=fu+(c['thruster-fuel'] or 0) ox=ox+(c['thruster-oxidizer'] or 0) end "
       "local made=0 for _,a in pairs(s.find_entities_filtered{name='assembling-machine-3'}) do made=made+a.products_finished end "
       "local ast=0 for _,e in pairs(s.find_entities_filtered{type='asteroid'}) do ast=ast+1 end "
       "rcon.print((p.space_location and p.space_location.name or '-')..'|'..string.format('%%.1f',p.speed*60)..'|'..string.format('%%.3f',p.distance or -1)..'|'..have..'/'..nt..'|'..tot..'|'..made..'|'..cnt..'|'..dmg"
       "..'|'..#s.find_entities_filtered{type='entity-ghost'}..'|'..math.floor(fu)..'|'..math.floor(ox)..'|'..ast..'|'..game.tick)")


def arg(name, default):
    return type(default)(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def main():
    platform, until = arg("--platform", 4), arg("--until", "fulgora")
    minutes, max_damaged, every = arg("--minutes", 40), arg("--max-damaged", 25), arg("--every", 60)
    print("at | km/s | route | armed | magazines | made | entities | damaged | ghosts | fuel | oxidizer | asteroids | tick", flush=True)
    end = time.time() + minutes * 60
    while time.time() < end:
        out = tools["run_lua"](LUA % platform).strip()
        print(out.replace("|", " | "), flush=True)
        f = out.split("|")
        if len(f) > 8:
            if f[0] == until:
                print("ARRIVED at", until)
                return
            if int(f[7]) + int(f[8]) >= max_damaged:
                print("STOP: damage limit reached")
                return
        time.sleep(every)
    print("TIME UP")


if __name__ == "__main__":
    main()
