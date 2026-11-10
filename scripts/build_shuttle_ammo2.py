"""
Second ammunition line of the "Inner Planets Shuttle" (surface platform-3), built after the first test flight showed one line (two furnaces,
0.78 magazines a second) cannot keep 13 turrets fed. It sits north-west of the north collector belt (tile column x=16) and takes metallic chunks
from that belt:

    crusher 1 -> furnace 1 \
                            assembler (firearm magazine) -> belt south between two turrets -> side-loads onto ammo belt 1 (row -22)
    crusher 2 -> furnace 2 /

Everything legendary. Coordinates are tiles (top-left corner). Usage: scripts/build_shuttle_ammo2.py [--apply]
"""
import json
import sys

from _game import tools

SURFACE = "platform-3"
Q = {"quality": "legendary"}
N, E, S, W = 0, 4, 8, 12
ents = []


def one(name, tx, ty, d=0):
    ents.append({"name": name, "x": tx + 0.5, "y": ty + 0.5, "direction": d, "params": dict(Q)})


def big(name, tx, ty, w, h, d=0, **kw):
    ents.append({"name": name, "x": tx + w / 2, "y": ty + h / 2, "direction": d, "params": dict(Q), **kw})


for cy in (-32, -28):                                   # crusher rows cy..cy+2
    big("crusher", 13, cy, 2, 3, S, recipe="metallic-asteroid-crushing")
    one("fast-inserter", 15, cy + 1, E)                 # chunk in from the collector belt
    one("fast-inserter", 15, cy + 2, W)                 # chunk back out (filtered below)
    one("fast-inserter", 12, cy + 1, E)                 # ore to the furnace
    big("electric-furnace", 9, cy, 3, 3)
big("assembling-machine-3", 5, -30, 3, 3, recipe="firearm-magazine")
one("fast-inserter", 8, -30, E)                         # plates from furnace 1
one("fast-inserter", 8, -28, E)                         # plates from furnace 2
one("fast-inserter", 7, -27, N)                         # magazines out
for ty in (-26, -25, -24, -23):
    one("express-transport-belt", 7, ty, S)

CONFIGURE = ("local s=game.surfaces['%s'] local n=0 for _,p in pairs({{15.5,-29.5},{15.5,-25.5}}) do local i=s.find_entities_filtered{position=p,type='inserter'}[1] "
             "if i then i.use_filters=true i.set_filter(1,{name='metallic-asteroid-chunk',quality='normal'}) n=n+1 end end rcon.print('filtered '..n)" % SURFACE)


def main():
    apply = "--apply" in sys.argv
    r = json.loads(tools["place_entities"](json.dumps(ents), surface=SURFACE, dry_run=not apply, clear_trees=False))
    if isinstance(r.get("result"), str):
        r = json.loads(r["result"])
    print("placed" if apply else "dry", r.get("placed"), "failed", r.get("failed"))
    if apply:
        print(tools["run_lua"](CONFIGURE))


if __name__ == "__main__":
    main()
