#!/usr/bin/env python3
"""Station lights for every wheel (the Captain, 2026-11-13: "Add lots of lights to the space station, make the colors meaningful, but
scatter them about and make it look more like a proper space station. We can eat the power cost easily").
What a colour means, the same on every wheel:
  orange   metallic chunks (iron, copper)        green   carbonic chunks (carbon, sulfur)       blue   oxide chunks (ice, calcite)
  white    storage: the cargo-bay disc, the avenues to the hub, the deck round it
  yellow   transport: the four spokes, like runway lights
  cyan     collection: the rim and its collectors
  red      defence: laser turrets (only on a wheel that has them)
Where they stand: one beside every crusher and along its flat in the crusher's colour; white down the avenues and scattered over the open
deck; yellow down both sides of each spoke at uneven spacing; cyan behind each collector and scattered round the rim; red by each laser.
Positions are jittered from a fixed seed, so a rerun proposes the same lamps. A lamp that would stand on something is dropped (the dry
run finds those), so the script is safe to run again: lamps already there are simply skipped.
Usage: wheel_lights.py [--apply] [--only PLANET]"""
import json
import math
import random
import sys

import wheel_hub
import wheel_round
from wheel import turn
from _game import tools
from _wheels import wheels

COLOURS = {"orange": (1, .45, 0), "green": (.1, 1, .2), "blue": (.15, .35, 1), "white": (1, 1, 1), "yellow": (1, .85, 0), "cyan": (0, .8, 1), "red": (1, .05, .05)}
KIND = {"metallic": "orange", "carbonic": "green", "oxide": "blue"}
lamps = {}                                           # (tx, ty) -> (colour, needs turrets)


def lamp(tx, ty, colour, k=0, turrets=False):
    tx, ty = turn(tx, ty, 1, 1, 0, k)[:2]
    lamps.setdefault((tx, ty), (colour, turrets))


def layout():
    rnd = random.Random(20261113)
    wheel_hub.layout()
    occ = wheel_hub.occ
    for k in range(4):
        for tx, kind in zip(wheel_hub.XS, wheel_hub.KINDS):
            lamp(tx + 2, -wheel_hub.RL + 3, KIND[kind], k)                       # beside the crusher
            for x in (tx, tx + 2):
                lamp(x, -wheel_hub.RB + 2, KIND[kind], k)                        # along the flat, on the empty rows below the product belt
        for y in range(-wheel_hub.RB + 2, -6, 4):
            lamp(1, y, "white", k)                                               # down the avenue
    n = 0
    while n < 260:                                                               # scattered over the open deck
        x, y = rnd.randint(-wheel_hub.RF, wheel_hub.RF), rnd.randint(-wheel_hub.RF, wheel_hub.RF)
        if math.hypot(x + .5, y + .5) < wheel_hub.RF - 1 and (x, y) not in occ and (x, y) not in lamps and abs(x) > 4 and abs(y) > 4:
            lamp(x, y, "white")
            n += 1
    for e in wheel_hub.ents:                                                     # by each inner laser
        if e["name"] == "laser-turret":
            x, y = e["x"], e["y"]
            r = math.hypot(x, y)
            lamp(math.floor(x + 2 * x / r), math.floor(y + 2 * y / r), "red", turrets=True)
    for k in range(4):                                                           # spokes: runway lights at uneven spacing, both sides
        for sx in (-2, 2):
            y = -wheel_round.RC + 8
            while y < -wheel_hub.RF - 2:
                lamp(sx, y, "yellow", k)
                y += rnd.choice((5, 6, 7, 8, 9, 11))
    wheel_round.layout()
    for e in wheel_round.ents:
        x, y = e["x"], e["y"]
        r = math.hypot(x, y)
        if e["name"] == "asteroid-collector":                                    # behind each collector, inside the rim belt
            lamp(math.floor(x - 4 * x / r), math.floor(y - 4 * y / r), "cyan")
        elif e["name"] == "laser-turret":
            lamp(math.floor(x - 2.5 * x / r), math.floor(y - 2.5 * y / r), "red", turrets=True)
    a = 0.0
    while a < 2 * math.pi:                                                       # scattered round the rim, between the belt and the turret row
        r = wheel_round.RC - rnd.choice((1, 1, 1, 4, 5, 6))
        lamp(math.floor(r * math.sin(a)), math.floor(-r * math.cos(a)), "cyan")
        a += rnd.uniform(6, 16) / wheel_round.RC
    return {c: sum(1 for v in lamps.values() if v[0] == c) for c in COLOURS}


def place(todo, surface, apply):
    """Dry run in batches, drop what would collide, then (with --apply) place the rest. Returns (placed or placeable, dropped)."""
    good = []
    for i in range(0, len(todo), 400):
        part = todo[i:i + 400]
        r = json.loads(tools["place_entities"](json.dumps(part), surface=surface, dry_run=True))
        bad = {f["i"] for f in (r.get("failed") or [])}
        good += [e for j, e in enumerate(part) if j not in bad]
    if apply:
        for i in range(0, len(good), 400):
            tools["place_entities"](json.dumps(good[i:i + 400]), surface=surface, dry_run=False)
    return len(good), len(todo) - len(good)


COLOUR = ("local s=game.surfaces['SURF'] local pal=PAL local n=0 for _,q in pairs(LIST) do local e=s.find_entities_filtered{name='small-lamp',position={q[1],q[2]},radius=0.3}[1] "
          "if e then e.always_on=true e.color=pal[q[3]] n=n+1 end end rcon.print(n)")


def main():
    apply = "--apply" in sys.argv
    print(layout())
    names = list(COLOURS)
    pal = "{" + ",".join("{r=%s,g=%s,b=%s}" % COLOURS[c] for c in names) + "}"
    for name, planet, surface, turrets in wheels():
        if not surface:
            continue
        mine = [(p, c) for p, (c, t) in sorted(lamps.items()) if turrets or not t]
        todo = [{"name": "small-lamp", "x": p[0] + .5, "y": p[1] + .5, "direction": 0, "params": {"quality": "rare"}} for p, c in mine]
        ok, dropped = place(todo, surface, apply)
        lit = 0
        if apply:
            for i in range(0, len(mine), 1500):
                lst = "{" + ",".join("{%s,%s,%d}" % (p[0] + .5, p[1] + .5, names.index(c) + 1) for p, c in mine[i:i + 1500]) + "}"
                lit += int(tools["run_lua"](COLOUR.replace("SURF", surface).replace("PAL", pal).replace("LIST", lst)).strip())
        print("==", name, "placed" if apply else "placeable", ok, "dropped (something stands there)", dropped, "coloured", lit)


if __name__ == "__main__":
    main()
