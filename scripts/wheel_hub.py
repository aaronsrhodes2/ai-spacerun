#!/usr/bin/env python3
"""The bigger, round centre of every wheel (the Captain, 2026-11-13: "build the bigger hub on both wheels ... make it stylish",
"all of the inner area the asteroids should be extinct, so all of that is protected factory real estate").
The first centre was a square: eight crushers against the hub (no hub edge left for cargo bays: 59 slots, full in minutes) inside a
square ring of 56 collectors. All of that goes. The new centre, from the hub outward:
  bays      a disc of cargo bays, radius RB tiles, every bay touching the hub or another bay
  crushers  six on each of the four flats of the disc (2 metallic, 2 carbonic, 2 oxide a side). An inserter cannot reach into a cargo bay,
            only into the hub itself (the Captain, and measured: 24 crushers stood at full output), so their products ride a belt down
            one of four avenues through the disc to four bulk inserters at the hub
  loop      a closed, round belt at RL tiles, flattened for the crushers; the four spokes side-load onto it, every chunk passes every
            crusher, the returned chunk goes back on
  lasers    (Gleba only) 24 on a circle outside the loop, a last line behind the rim
  deck      a solid disc of foundation, radius RF
Steps, each on every wheel in scripts/_wheels.py (--only gleba|nauvis for one):
  check     the layout only, no game
  clear     removes the old centre (everything of ours inside the loop except the hub and bays) and writes what it held to a temp file
  build     dry run; build --apply lays the deck and places. Never apply twice on the same wheel.
  restock   puts what `clear` took out of belts, collectors and crushers into the bigger hub
  config    inserter filters and crusher recipes
  refit     for a wheel built before the avenues: removes the bays in their way, places the product belts (dry run, or --apply)
Usage: wheel_hub.py check | clear | build [--apply] | refit [--apply] | restock | config  [--only PLANET]"""
import json
import math
import os
import sys
import tempfile

from wheel import CHUNKS, CONFIG, CRUSH, Q, turn
from wheel_round import DIRS, circle
from _game import tools
from _wheels import lay_foundation, place_all, wheels

RB, RL, RF, FLAT = 40, 46, 52, 13
XS = (-12, -8, -4, 2, 6, 10)
KINDS = ("metallic", "carbonic", "oxide", "metallic", "carbonic", "oxide")
N, S = 0, 8
ents, tiles, cfg, recipes, occ = [], set(), [], [], {}
late, removed = [], []                              # the product belts (added in the refit) and the bay cells they replaced
crushers = []                                        # (x, y, kind) for the lights


def put(name, tx, ty, w=1, h=1, d=N, filt=None, recipe=None, k=0):
    tx, ty, w, h, d = turn(tx, ty, w, h, d, k)
    for c in [(tx + i, ty + j) for i in range(w) for j in range(h)]:
        assert c not in occ and not (-4 <= c[0] < 4 and -4 <= c[1] < 4), "%s at %s overlaps %s" % (name, c, occ.get(c, "the hub"))
        occ[c] = name
    e = {"name": name, "x": tx + w / 2, "y": ty + h / 2, "direction": d, "params": dict(Q)}
    ents.append(e)
    if filt:
        cfg.append((e["x"], e["y"], filt))
    if recipe:
        recipes.append((e["x"], e["y"], recipe))
    return e


def loop_path():
    """The round loop, dead straight for FLAT tiles either side of each axis so the crushers can stand against it."""
    flat = []
    for (x, y) in circle(RL):
        if abs(x + .5) < FLAT:
            y = -RL if y < 0 else RL - 1
        elif abs(y + .5) < FLAT:
            x = -RL if x < 0 else RL - 1
        if (x, y) not in flat:
            flat.append((x, y))
    out = []
    for i, t in enumerate(flat):
        out.append(t)
        nx, cur = flat[(i + 1) % len(flat)], t
        while abs(nx[0] - cur[0]) + abs(nx[1] - cur[1]) > 1:      # where flattening opened a gap, walk it by the outer tiles
            c = []
            if nx[0] != cur[0]:
                c.append((cur[0] + (1 if nx[0] > cur[0] else -1), cur[1]))
            if nx[1] != cur[1]:
                c.append((cur[0], cur[1] + (1 if nx[1] > cur[1] else -1)))
            cur = max(c, key=lambda q: (q[0] + .5) ** 2 + (q[1] + .5) ** 2)
            out.append(cur)
    return out


def layout():
    for x in range(-RF - 1, RF + 1):
        for y in range(-RF - 1, RF + 1):
            if math.hypot(x + .5, y + .5) <= RF:
                tiles.add((x, y))
    cells = [(tx, ty) for tx in range(-RB - 4, RB + 4, 4) for ty in range(-RB - 4, RB + 4, 4)
             if math.hypot(tx + 2, ty + 2) <= RB and not (tx in (-4, 0) and ty in (-4, 0))]
    cells.sort(key=lambda c: math.hypot(c[0] + 2, c[1] + 2))      # inside out: a bay must touch the hub or a bay already there
    gone = set()                                     # no bay on the flats (product belts) or on the four avenues that carry them to the hub
    for k in range(4):
        for c in [(tx, -RB) for tx in range(-12, 12, 4)] + [(0, ty) for ty in range(-RB + 4, -4, 4)]:
            gone.add(turn(c[0], c[1], 4, 4, 0, k)[:2])
    cells = [c for c in cells if c not in gone]
    removed.extend((tx + 2, ty + 2) for tx, ty in gone)
    for tx, ty in cells:
        put("cargo-bay", tx, ty, 4, 4)
    first = len(ents)
    for k in range(4):                               # an inserter cannot reach into a bay, only into the hub: products ride a belt to it
        for x in range(-12, 3):
            put("express-transport-belt", x, -RB, d=4, k=k)
        for x in range(4, 12):
            put("express-transport-belt", x, -RB, d=12, k=k)
        for y in range(-RB, -6):
            put("express-transport-belt", 3, y, d=S, k=k)
        for x in range(0, 4):
            put("express-transport-belt", x, -6, d=12, k=k)
            put("bulk-inserter", x, -5, d=N, k=k)
    late.extend(ents[first:])
    path = loop_path()
    for i, t in enumerate(path):
        nx = path[(i + 1) % len(path)]
        put("express-transport-belt", t[0], t[1], d=DIRS[(nx[0] - t[0], nx[1] - t[1])])
    for k in range(4):
        for tx, kind in zip(XS, KINDS):
            rec, chunk, prods = CRUSH[kind]
            e = put("crusher", tx, -RL + 2, 2, 3, N, recipe=rec, k=k)
            crushers.append((e["x"], e["y"], kind))
            put("fast-inserter", tx, -RL + 1, d=N, filt=[chunk], k=k)
            put("fast-inserter", tx + 1, -RL + 1, d=S, filt=CHUNKS, k=k)
            put("fast-inserter", tx, -RB - 1, d=N, filt=prods, k=k)
            put("fast-inserter", tx + 1, -RB - 1, d=N, filt=prods, k=k)
    for i in (j for j in range(24) if j % 6):         # Gleba only (the caller drops them); none on the axes, where the spokes come in
        a = math.radians(15 * i)
        put("laser-turret", math.floor(49.5 * math.sin(a)) - 1, math.floor(-49.5 * math.cos(a)) - 1, 2, 2)
    return {"bays": len(cells), "loop": len(path), "crushers": len(crushers), "entities": len(ents), "tiles": len(tiles)}


CLEAR = ("local s=game.surfaces['SURF'] local hub=s.platform.hub local t={} local n=0 local function add(it) local k=it.name..'|'..(it.quality or 'normal') t[k]=(t[k] or 0)+it.count end "
         "for _,e in pairs(s.find_entities_filtered{area={{-RL.9,-RL.9},{RL.9,RL.9}},force='player'}) do if e.valid and e~=hub and e.name~='cargo-bay' and e.type~='character' then "
         "if e.type=='transport-belt' or e.type=='underground-belt' then for l=1,e.get_max_transport_line_index() do for _,it in pairs(e.get_transport_line(l).get_contents()) do add(it) end end "
         "else if e.type=='inserter' and e.held_stack.valid_for_read then add({name=e.held_stack.name,count=e.held_stack.count,quality=e.held_stack.quality.name}) end "
         "for i=1,e.get_max_inventory_index() do local inv=e.get_inventory(i) if inv then for _,it in pairs(inv.get_contents()) do add(it) end end end end e.destroy() n=n+1 end end "
         "local o={} for k,v in pairs(t) do o[#o+1]=k..'='..v end rcon.print(n..';'..table.concat(o,','))").replace("RL", str(RL - 1))
RESTOCK = ("local hub=game.surfaces['SURF'].platform.hub local o={} for _,q in pairs(ITEMS) do local n=hub.insert{name=q[1],quality=q[2],count=q[3]} o[#o+1]=q[1]..' '..n..'/'..q[3] end "
           "local inv=hub.get_inventory(defines.inventory.hub_main) rcon.print(table.concat(o,', ')..' | hub slots '..#inv..' free '..inv.count_empty_stacks())")


def salvage_file(planet):
    return os.path.join(tempfile.gettempdir(), "wheel_hub_salvage_%s.json" % planet)


def main():
    step = sys.argv[1]
    apply = "--apply" in sys.argv
    print(layout())
    if step == "check":
        return
    for name, planet, surface, turrets in wheels():
        print("==", name, surface or "(not created)")
        if not surface:
            continue
        if step == "clear":
            n, _, items = tools["run_lua"](CLEAR.replace("SURF", surface)).strip().partition(";")
            held = [kv.split("=") for kv in items.split(",") if kv]
            json.dump(held, open(salvage_file(planet), "w"))
            print("removed", n, "held", held)
        elif step == "build":
            mine = [e for e in ents if e["name"] != "laser-turret"]   # no lasers inside the rim: nothing reaches there (0 kills on Gleba, removed)
            if apply:
                print("foundation tiles", lay_foundation(tiles, surface))
            ok, bad = place_all(mine, surface, apply)
            print("placed" if apply else "dry run", ok, "failed", bad)
        elif step == "refit":                        # for a wheel built before the product belts: bays out, belts in
            pos = "{" + ",".join("{%s,%s}" % c for c in removed) + "}"
            print(tools["run_lua"]("local s=game.surfaces['%s'] local n=0 for _,p in pairs(%s) do local b=s.find_entities_filtered{name='cargo-bay',position=p,radius=0.5}[1] if b then b.destroy() n=n+1 end end "
                                   "local inv=s.platform.hub.get_inventory(defines.inventory.hub_main) rcon.print('bays removed '..n..', hub slots '..#inv..' free '..inv.count_empty_stacks())" % (surface, pos)))
            ok, bad = place_all(late, surface, apply)
            print("placed" if apply else "dry run", ok, "failed", bad)
        elif step == "restock":
            held = json.load(open(salvage_file(planet)))
            items = "{" + ",".join("{'%s','%s',%s}" % (k.split("|")[0], k.split("|")[1], v) for k, v in held) + "}"
            print(tools["run_lua"](RESTOCK.replace("SURF", surface).replace("ITEMS", items)))
        elif step == "config":
            filt = "{" + ",".join("{%s,%s,{%s}}" % (x, y, ",".join("'%s'" % f for f in fl)) for x, y, fl in cfg) + "}"
            rec = "{" + ",".join("{%s,%s,'%s'}" % r for r in recipes) + "}"
            print(tools["run_lua"](CONFIG.replace("SURF", surface).replace("FILT", filt).replace("REC", rec)))


if __name__ == "__main__":
    main()
