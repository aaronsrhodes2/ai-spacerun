"""
First landing on a planet: when a shuttle is in orbit there, its hub drops one cargo pod (a stack of the ship's own iron ore) to the surface.
That is the arrival that opens the planet for building. The shuttle keeps flying its normal schedule; nothing is paused.

Polls every --every seconds until every listed ship has dropped its pod, or --minutes pass.

Usage: scripts/planet_landing.py [--ships 5:fulgora,6:gleba,7:vulcanus] [--every 10] [--minutes 45]
"""
import sys
import time

from _game import tools

DROP = ("local p=game.forces.player.platforms[%d] local want='%s' if not (p.space_location and p.space_location.name==want) then rcon.print('wait '..(p.space_location and p.space_location.name or 'flying')) return end "
        "local hub=p.hub local took=hub.get_inventory(defines.inventory.hub_main).remove{name='iron-ore',count=50} local pod=hub.create_cargo_pod() "
        "if took>0 then pod.get_inventory(defines.inventory.cargo_unit).insert{name='iron-ore',count=took} end "
        "pod.cargo_pod_destination={type=defines.cargo_destination.surface,surface=game.surfaces[want]} rcon.print('dropped pod with '..took..' iron ore on '..want..' tick '..game.tick)")


def arg(name, default):
    return type(default)(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def main():
    ships = dict((int(a), b) for a, b in (s.split(":") for s in arg("--ships", "5:fulgora,6:gleba,7:vulcanus").split(",")))
    every, end = arg("--every", 10), time.time() + arg("--minutes", 45) * 60
    while ships and time.time() < end:
        for i, planet in list(ships.items()):
            out = tools["run_lua"](DROP % (i, planet)).strip()
            if "dropped" in out:
                print(f"platform {i}: {out}", flush=True)
                del ships[i]
        time.sleep(every)
    print("all landed" if not ships else f"not landed: {ships}", flush=True)


if __name__ == "__main__":
    main()
