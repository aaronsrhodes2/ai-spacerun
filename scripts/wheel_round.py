#!/usr/bin/env python3
"""Gleba Wheel, the round outer rim (the Captain, 2026-11-13: bigger, as round as possible, grabbers spread out).
A circle of radius RC tiles round the hub of the first wheel (scripts/wheel.py):
  rim belt     a 4-connected circle of belt at radius RC; each quarter flows to the nearest of the four spokes (N, E, S, W axes)
  collectors   one every COLLECT tiles of rim, outside the belt, facing outward, an inserter behind each onto the rim belt
  ammunition   a second belt circle two tiles inside, one closed loop (it dives under each spoke), fed from the hub up the north spoke
  turrets      one gun turret every TURRET tiles of that loop on the inside, a substation between them every POLE tiles
  spokes       straight belts along the axes down to the first wheel's rim, with a substation line and solar panels beside them
Everything is generated from the two circles, checked for overlaps here (run `check`), and placed in batches.
Usage: wheel_round.py check | found | build [--apply] | config | arm | solar [--apply] | lasers"""
import json
import math
import sys

from _game import tools

NAME = "Gleba Wheel"
Q = {"quality": "rare"}
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
        for y in range(-RC - 1, -30):                # one tile beyond the rim: the circle's tile on an axis is off by one on two of the four sides
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
        for y in range(-RC - 1, -30):
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
    for i, t in enumerate(ammo):
        nx = ammo[(i + 1) % m]
        d = DIRS[(nx[0] - t[0], nx[1] - t[1])]
        if t in under:
            if under[t]:
                one("express-underground-belt", t, d, type=under[t])
        else:
            one("express-transport-belt", t, d)
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
                put("gun-turret", body, sum(c[0] for c in body) / 4 + .5, sum(c[1] for c in body) / 4 + .5)
                one("fast-inserter", ins, DIRS[o], filt=["firearm-magazine"])   # picks from the loop (outward side)
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
    # ammunition feed: from the first wheel's column at x=-2 (it ends at y=-32 heading north) up to the loop
    for y in range(-32, -RA, -1):
        one("express-transport-belt", (-2, y), 0)
    for c in holes:
        tiles.discard(c)
    return {"rim": len(rim), "ammo": len(ammo), "collectors": placed, "turrets": nt, "substations": npole, "entities": len(ents), "tiles": len(tiles)}


WHERE = "local f=game.forces.player for i,p in pairs(f.platforms) do if p.name=='" + NAME + "' then rcon.print(i..' '..p.surface.name) return end end rcon.print('none')"
CONFIG = ("local s=game.surfaces['SURF'] local n=0 for _,q in pairs(FILT) do local i=s.find_entities_filtered{type='inserter',position={q[1],q[2]},radius=0.3}[1] if i then i.use_filters=true i.inserter_filter_mode='whitelist' "
          "for k,name in pairs(q[3]) do i.set_filter(k,name) end n=n+1 end end rcon.print('inserters filtered '..n)")
LASERS = ("local f=game.forces.player local s=game.surfaces['SURF'] if not f.recipes['laser-turret'].enabled then rcon.print('laser turret not researched') return end local n,ins=0,0 "
          "for _,t in pairs(s.find_entities_filtered{name='gun-turret'}) do local pos,q=t.position,t.quality.name for _,i in pairs(s.find_entities_filtered{type='inserter',position=pos,radius=2.2}) do if i.drop_target==t then i.destroy() ins=ins+1 end end "
          "t.destroy() if s.create_entity{name='laser-turret',position=pos,force=f,quality=q} then n=n+1 end end rcon.print('gun turrets replaced by lasers '..n..', feed inserters removed '..ins)")
ARM = ("local f=game.forces.player local s=game.surfaces['SURF'] local p for i,q in pairs(f.platforms) do if q.surface==s then p=q end end local hub=p.hub.get_inventory(defines.inventory.hub_main) local n,a=0,0 "
       "for _,t in pairs(s.find_entities_filtered{type='ammo-turret'}) do local inv=t.get_inventory(defines.inventory.turret_ammo) local need=10-inv.get_item_count() if need>0 then local got=hub.remove{name='firearm-magazine',count=need} "
       "if got>0 then inv.insert{name='firearm-magazine',count=got} a=a+got end end n=n+1 end rcon.print('turrets '..n..', magazines handed out '..a..', hub magazines left '..hub.get_item_count('firearm-magazine'))")


def main():
    step = sys.argv[1]
    info = layout()
    print(info)
    if step == "check":
        return
    surface = tools["run_lua"](WHERE).split()[1]
    apply = "--apply" in sys.argv
    if step == "found":
        ts = sorted(tiles)
        for i in range(0, len(ts), 4000):
            part = ",".join("{%d,%d}" % t for t in ts[i:i + 4000])
            print(tools["run_lua"]("local s=game.surfaces['%s'] local add={} for _,p in pairs({%s}) do add[#add+1]={name='space-platform-foundation',position=p} end s.set_tiles(add) rcon.print('foundation '..#add)" % (surface, part)))
    elif step == "build":
        bad = 0
        for i in range(0, len(ents), 400):
            r = json.loads(tools["place_entities"](json.dumps(ents[i:i + 400]), surface=surface, dry_run=not apply))
            f = r.get("failed") or []
            bad += len(f)
            if f:
                print("failed", json.dumps(f)[:260])
        print("batches done, failures", bad)
    elif step == "config":
        for i in range(0, len(cfg), 300):
            filt = "{" + ",".join("{%s,%s,{%s}}" % (x, y, ",".join("'%s'" % f for f in fl)) for x, y, fl in cfg[i:i + 300]) + "}"
            print(tools["run_lua"](CONFIG.replace("SURF", surface).replace("FILT", filt)))
    elif step == "solar":                            # only the panels (the rest already stands)
        add = [e for e in ents if e["name"] == "solar-panel"]
        r = json.loads(tools["place_entities"](json.dumps(add[:400]), surface=surface, dry_run=not apply))
        r2 = json.loads(tools["place_entities"](json.dumps(add[400:]), surface=surface, dry_run=not apply)) if len(add) > 400 else {"placed": 0}
        print("panels placed", r.get("placed", 0) + r2.get("placed", 0), "(already standing ones are refused)")
    elif step == "lasers":
        print(tools["run_lua"](LASERS.replace("SURF", surface)))
    elif step == "arm":
        print(tools["run_lua"](ARM.replace("SURF", surface)))


if __name__ == "__main__":
    main()
