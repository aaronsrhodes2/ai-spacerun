"""
Damage control for a space platform in flight: every few seconds rebuild what asteroids destroyed (the ghosts the game leaves behind, tiles first so
the entities have ground to stand on). Free building in friendly build mode; it does not touch ammunition, fuel or research.
Stops when the platform is parked at a planet, or after --minutes.

Usage: scripts/shuttle_repair.py [--platform 4] [--minutes 60] [--every 10]
"""
import sys
import time

from _game import tools

LUA = ("local p=game.forces.player.platforms[%d] local s=p.surface local t,e=0,0 for pass=1,12 do local did=0 "
       "for _,g in pairs(s.find_entities_filtered{type='tile-ghost'}) do if g.valid and g.revive() then t=t+1 did=did+1 end end "
       "for _,g in pairs(s.find_entities_filtered{type='entity-ghost'}) do if g.valid and g.revive() then e=e+1 did=did+1 end end if did==0 then break end end "
       "rcon.print((p.space_location and p.space_location.name or '-')..'|'..string.format('%%.3f',p.distance or -1)..'|'..string.format('%%.1f',p.speed*60)..'|'..t..'|'..e"
       "..'|'..#s.find_entities_filtered{type='tile-ghost'}+#s.find_entities_filtered{type='entity-ghost'})")


def arg(name, default):
    return type(default)(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def main():
    platform, minutes, every = arg("--platform", 4), arg("--minutes", 60), arg("--every", 10)
    end = time.time() + minutes * 60
    tiles = ents = n = 0
    while time.time() < end:
        f = tools["run_lua"](LUA % platform).strip().split("|")
        if len(f) == 6:
            tiles, ents, n = tiles + int(f[3]), ents + int(f[4]), n + 1
            if n % 6 == 0 or f[0] != "-":
                print(f"at {f[0]} route {f[1]} km/s {f[2]} rebuilt so far: {tiles} tiles, {ents} entities; ghosts left {f[5]}", flush=True)
            if f[0] != "-":
                return
        time.sleep(every)
    print("TIME UP")


if __name__ == "__main__":
    main()
