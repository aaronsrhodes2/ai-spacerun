#!/usr/bin/env python3
"""Gleba Wheel, the round outer rim (the Captain, 2026-11-13: bigger, as round as possible, grabbers spread out).
A circle of radius RC tiles round the hub of the first wheel (scripts/wheel.py):
  rim belt     a 4-connected circle of belt at radius RC; each quarter flows to the nearest of the four spokes (N, E, S, W axes)
  collectors   one every COLLECT tiles of rim, outside the belt, facing outward, an inserter behind each onto the rim belt
  ammunition   a second belt circle two tiles inside, one closed loop (it dives under each spoke), fed from the hub up the north spoke
  turrets      one gun turret every TURRET tiles of that loop on the inside, a substation between them every POLE tiles
  spokes       straight belts along the axes down to the round centre's loop at 46 tiles (scripts/wheel_hub.py), with a substation line and solar panels beside them
Everything is generated from the two circles, checked for overlaps here (run `check`), and placed in batches.
Runs on every wheel in scripts/_wheels.py; --only gleba|nauvis for one. Never run `build --apply` twice on the same wheel.
Usage: wheel_round.py check | found | build [--apply]  [--only PLANET]"""
import json
import math
import sys

from _game import tools
from _wheels import lay_foundation, place_all, wheels

Q = {"quality": "epic"}
RC, RA = 600, 598
COLLECT, TURRET, POLE = 30, 24, 16
DIRS = {(0, -1): 0, (1, 0): 4, (0, 1): 8, (-1, 0): 12}
ents, tiles, cfg = [], set(), []
occ = {}


def circle(r):
    """Ordered closed 4-connected path of tiles at radius r, clockwise on screen starting just east of north."""
    out = []
    n = int(r * 16)
    for i in range(n):
        a = 2 * math.pi * i / n
        t = (math.floor(r * math.sin(a)), math.floor(-r * math.cos(a)))
        if out and t == out[-1]:
            continue
        if out and abs(t[0] - out[-1][0]) + abs(t[1] - out[-1][1]) == 2:      # diagonal step: go through the outer of the two corner tiles
            c1, c2 = (t[0], out[-1][1]), (out[-1][0], t[1])
            out.append(max(c1, c2, key=lambda c: (c[0] + .5) ** 2 + (c[1] + .5) ** 2))
        out.append(t)
    while out[-1] == out[0]:
        out.pop()
    if abs(out[0][0] - out[-1][0]) + abs(out[0][1] - out[-1][1]) == 2:
        c1, c2 = (out[0][0], out[-1][1]), (out[-1][0], out[0][1])
        out.append(max(c1, c2, key=lambda c: (c[0] + .5) ** 2 + (c[1] + .5) ** 2))
    return out


def outward(t):
    x, y = t[0] + .5, t[1] + .5
    return (0, -1 if y < 0 else 1) if abs(y) >= abs(x) else (1 if x > 0 else -1, 0)


def free(cells):
    return all(c not in occ for c in cells)


def put(name, cells, x, y, d=0, filt=None, **params):
    for c in cells:
        occ[c] = name
        tiles.add(c)
    p = dict(Q)
    p.update(params)
    ents.append({"name": name, "x": x, "y": y, "direction": d, "params": p})
    if filt:
        cfg.append((x, y, filt))


def one(name, t, d=0, filt=None, **params):
    put(name, [t], t[0] + .5, t[1] + .5, d, filt, **params)


def block(name, t, w, h, d=0, **params):
    put(name, [(t[0] + i, t[1] + j) for i in range(w) for j in range(h)], t[0] + w / 2, t[1] + h / 2, d, **params)


def layout():
    rim, ammo = circle(RC), circle(RA)
    flat = []                                        # the loop runs dead straight for five tiles either side of each axis, so it can dive under the spoke
    for (x, y) in ammo:
        if abs(x + .5) < 5:
            y = -RA if y < 0 else RA - 1
        elif abs(y + .5) < 5:
            x = -RA if x < 0 else RA - 1
        if not flat or flat[-1] != (x, y):
            flat.append((x, y))
    ammo = flat
    assert not set(rim) & set(ammo), "the two circles share tiles"
    holes = set()
    # annulus of foundation under both belts and the turret row
    for x in range(-RC - 3, RC + 3):
        for y in range(-RC - 3, RC + 3):
            d = math.hypot(x + .5, y + .5)
            if RA - 5.5 <= d <= RC + 1.2:
                tiles.add((x, y))
    # spokes first (they own the axis columns): north x=0, and the same turned
    def turn(t, k):
        for _ in range(k):
            t = (-t[1] - 1, t[0])
        return t
    spoke_cells = set()
    for k in range(4):
        d = [8, 12, 0, 4][k]                         # flow toward the hub
        for y in range(-RC - 1, -46):                # one tile beyond the rim: the circle's tile on an axis is off by one on two of the four sides
            c = turn((0, y), k)
            spoke_cells.add(c)
        for x in range(-3, 10):
            for y in range(-RC + 2, -33):
                tiles.add(turn((x, y), k))
    rimset = set(rim)
    # rim belt: every tile points along the path toward the nearest axis
    n = len(rim)
    for i, t in enumerate(rim):
        if t in spoke_cells:
            continue
        a = math.atan2(t[0] + .5, -(t[1] + .5)) % (2 * math.pi)          # 0 = north, clockwise
        ax = round(a / (math.pi / 2)) * (math.pi / 2)
        step = 1 if ((ax - a + math.pi) % (2 * math.pi)) - math.pi > 0 else -1
        nx = rim[(i + step) % n]
        one("express-transport-belt", t, DIRS[(nx[0] - t[0], nx[1] - t[1])])
    for k in range(4):
        d = [8, 12, 0, 4][k]
        for y in range(-RC - 1, -46):
            if turn((0, y), k) in rimset or y > -RC:
                one("express-transport-belt", turn((0, y), k), d)
    # ammunition loop, clockwise, diving under each spoke
    m = len(ammo)
    under = {}
    for i, t in enumerate(ammo):                     # where the loop meets a spoke: underground from the tile before to the tile after
        if t in spoke_cells:
            under[t] = None
            under[ammo[(i - 1) % m]] = "input"
            under[ammo[(i + 1) % m]] = "output"
    # (the inner circle carried ammunition on Gleba's first build; with lasers it only marks where the turrets stand)
    # collectors on the outside of the rim
    placed = 0
    last = -COLLECT
    for i, t in enumerate(rim):
        if i - last < COLLECT or t in spoke_cells:
            continue
        o = outward(t)
        ins = (t[0] + o[0], t[1] + o[1])
        ctr = (t[0] + 3 * o[0], t[1] + 3 * o[1])
        body = [(ctr[0] + a, ctr[1] + b) for a in (-1, 0, 1) for b in (-1, 0, 1)]
        side = (o[1], o[0])                                                # perpendicular
        front = [(t[0] + r * o[0] + s * side[0], t[1] + r * o[1] + s * side[1]) for r in (4, 5, 6, 7) for s in (-1, 0, 1)]
        if abs(t[0]) < 12 or abs(t[1]) < 12 or not free([ins] + body + front) or any(c in holes for c in [ins] + body):
            continue
        d = DIRS[o]
        put("asteroid-collector", body, ctr[0] + .5, ctr[1] + .5, d)
        one("fast-inserter", ins, d)                                       # picks from the collector (outward side), drops on the rim
        for c in front:
            holes.add(c)
        last = i
        placed += 1
    # turrets and substations on the inside of the ammunition loop
    lt, lp, nt, npole = -TURRET, -POLE // 2, 0, 0
    for i, t in enumerate(ammo):
        o = outward(t)
        inn = (-o[0], -o[1])
        side = (o[1], o[0])
        if t in under or abs(t[0]) < 12 or abs(t[1]) < 12:
            continue
        if i - lt >= TURRET:
            ins = (t[0] + inn[0], t[1] + inn[1])
            a = (t[0] + 2 * inn[0], t[1] + 2 * inn[1])
            b = (t[0] + 3 * inn[0], t[1] + 3 * inn[1])
            body = [a, b, (a[0] + side[0], a[1] + side[1]), (b[0] + side[0], b[1] + side[1])]
            if free([ins] + body):
                put("laser-turret", body, sum(c[0] for c in body) / 4 + .5, sum(c[1] for c in body) / 4 + .5)
                lt = i
                nt += 1
                continue
        if False and i - lp >= POLE:                 # no substations: a space platform powers everything standing on it
            a = (t[0] + inn[0], t[1] + inn[1])
            b = (t[0] + 2 * inn[0], t[1] + 2 * inn[1])
            body = [a, b, (a[0] + side[0], a[1] + side[1]), (b[0] + side[0], b[1] + side[1])]
            if free(body):
                put("substation", body, sum(c[0] for c in body) / 4 + .5, sum(c[1] for c in body) / 4 + .5)
                lp = i
                npole += 1
    # spoke furniture: substations every 18 at x 4..5, a panel every 9 at x 6..8
    for k in range(4):
        for y in range(-RC + 12, -36, 18):
            c = [turn((x, yy), k) for x in (4, 5) for yy in (y, y + 1)]
            if False and free(c):
                put("substation", c, sum(q[0] for q in c) / 4 + .5, sum(q[1] for q in c) / 4 + .5)
        for y in range(-RC + 16, -40, 3):            # every 3 tiles since the turrets became lasers (about 5 MW standing draw, more when firing)
            c = [turn((x, yy), k) for x in (6, 7, 8) for yy in (y, y + 1, y + 2)]
            if free(c):
                put("solar-panel", c, sum(q[0] for q in c) / 9 + .5, sum(q[1] for q in c) / 9 + .5)
    for c in holes:
        tiles.discard(c)
    return {"rim": len(rim), "ammo": len(ammo), "collectors": placed, "turrets": nt, "substations": npole, "entities": len(ents), "tiles": len(tiles)}


def main():
    step = sys.argv[1]
    info = layout()
    print(info)
    if step == "check":
        return
    apply = "--apply" in sys.argv
    for name, planet, surface, turrets in wheels():
        print("==", name, surface or "(not created)")
        if not surface:
            continue
        mine = [e for e in ents if turrets or e["name"] != "laser-turret"]
        if step == "found":
            print("foundation tiles", lay_foundation(tiles, surface))
        elif step == "build":
            ok, bad = place_all(mine, surface, apply)
            print("placed" if apply else "dry run", ok, "failures", bad)


if __name__ == "__main__":
    main()
