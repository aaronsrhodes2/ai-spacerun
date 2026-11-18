#!/usr/bin/env python3
"""Edgerunner BASE EDGE: turrets along the bottom side (the Captain, 2026-11-18: "Surround the entire frame with railguns, rocket turrets
and gun turrets"). With the thrusters moved inside (edge_bar.py) the bottom edge is free. It lies in the lee of the ship, so this is the
last line, not the first; it gets the same three kinds as the flanks.

The base strip, north to south: rows 286, 287 free deck; row 288 the chunk belt; row 289 the collectors' inserters; rows 290..292 the
collectors (facing south, every 30 tiles). The two ammunition belts come down the flanks and have to get past the chunk belt:
  belt A  (magazines + rockets, one kind a lane) is the flank's down belt, which ended at row 280. It goes on down its staircase to row 286,
          dives under the chunk belt and row 289 (287 -> 289) and turns toward the middle on ROW 290.
  belt B  (railgun rounds) is the inner flank belt of edge_rails.py, which also ended at row 280: down to row 286, under to row 290, and
          toward the middle on ROW 291. Belt A hops under the tile where B comes up.
  both    hop under every collector (underground, c-1 -> c+3) and dead-end beside the south spoke.
  turrets south of the belts, between the collectors (offsets from a collector's first tile): gun +6, rocket turret +11, railgun +17,
          gun +23. Guns and rocket turrets take from belt A with a LONG-HANDED inserter on row 292 (over belt B) and stand on rows 294...;
          railguns take from belt B with a bulk inserter on row 292 and stand on rows 293..296 facing SOUTH.
Steps: plan | deck | build [--apply] | config | status
Usage: edge_base.py plan ; edge_base.py deck ; edge_base.py build --apply ; edge_base.py config"""
import json
import sys

import edge_flanks as F
import edge_rails as R
import edge_ship as ES
import triangle_miner as TM
from _game import tools
from edge_works import T

L = tools["run_lua"]
BELT, UG, BULK, LONG = "express-transport-belt", "express-underground-belt", "bulk-inserter", "long-handed-inserter"
N, E, S, W = 0, 4, 8, 12
DIR = {(0, -1): N, (1, 0): E, (0, 1): S, (-1, 0): W}
ROW_A, ROW_B, ROW_I = 290, 291, 292
X_END = 3                                  # the belts stop this far from the ship's centre line


def collectors():
    r = L(TM.AT + "local o={} for _,c in pairs(s.find_entities_filtered{name='asteroid-collector',area={{-510,289},{510,294}}}) do o[#o+1]=math.floor(c.position.x-1) end rcon.print(helpers.table_to_json(o))")
    return sorted(json.loads(r))


def down(start, col, y_to):
    """Staircase from the dead end `start` down to row y_to: one row down, then sideways to that row's column."""
    cx, cy = start
    path = []
    for y in range(cy + 1, y_to + 1):
        path.append((cx, y))
        t = col(y)
        while cx != t:
            cx += 1 if t > cx else -1
            path.append((cx, y))
    return path


def row_belt(x_from, x_to, y, blocked):
    """Belt along row y from x_from to x_to (inclusive), with underground hops over blocked tiles."""
    step = 1 if x_to > x_from else -1
    d = E if step > 0 else W
    e, x = [], x_from
    while x != x_to + step:
        if (x + step) in blocked and x != x_to:
            k = x + step
            while k in blocked:
                k += step
            e += [T(UG, x, y, d, type="input"), T(UG, k, y, d, type="output")]
            x = k + step
        else:
            e.append(T(BELT, x, y, d))
            x += step
    return e


def plan(side, cols):
    s = 1 if side < 0 else -1
    ents, tiles, ins = [], set(), []
    a_start = (F.col(F.Y_BOT, side), F.Y_BOT)
    b_start = R.side_plan(side)["path"][-1]
    xs = {}
    for name, start, col, row in (("A", a_start, lambda y: ES.edge(y, side) + 2 * s, ROW_A), ("B", b_start, lambda y: ES.edge(y, side) + 9 * s, ROW_B)):
        path = [start] + down(start, col, 286)
        for i in range(1, len(path)):
            c = path[i]
            nxt = path[i + 1] if i + 1 < len(path) else (c[0], c[1] + 1)
            ents.append(T(BELT, c[0], c[1], DIR[(nxt[0] - c[0], nxt[1] - c[1])]))
            tiles.add(c)
        x = path[-1][0]
        xs[name] = x
        ents += [T(UG, x, 287, S, type="input"), T(UG, x, row - 1, S, type="output")]
        tiles |= {(x, 287), (x, row - 1)}
    blocked = set()
    for c in cols:
        blocked |= {c, c + 1, c + 2}
    x_to = -X_END if side < 0 else X_END
    ents += row_belt(xs["A"], x_to, ROW_A, blocked | {xs["B"]})
    ents += row_belt(xs["B"], x_to, ROW_B, blocked)
    lo, hi = (xs["B"] + 2, -X_END - 1) if side < 0 else (X_END + 1, xs["B"] - 2)
    tiles |= {(x, y) for x in range(min(xs["A"], x_to), max(xs["A"], x_to) + 1) for y in (ROW_A, ROW_B)}
    for c in cols:
        for name, off, w, h, ammo in (("gun-turret", 6, 2, 2, "A"), ("rocket-turret", 11, 3, 3, "A"), ("railgun-turret", 17, 3, 4, "B"), ("gun-turret", 23, 2, 2, "A")):
            x0 = c + off
            if x0 < lo or x0 + w - 1 > hi or any((x0 + i) in blocked or (x0 + i + 30) in () for i in range(-1, w + 1)):
                continue
            ix = x0 + (0 if w == 2 else 1)
            if ammo == "A":
                ents.append(T(LONG, ix, ROW_I, N))
                ents.append(T(name, x0, 294, 0, w, h))
                cells = {(x0 + i, 294 + k) for i in range(w) for k in range(h)}
            else:
                ents.append(T(BULK, ix, ROW_I, N))
                ents.append(T(name, x0, 293, S, w, h))
                cells = {(x0 + i, 292 + k) for i in range(w) for k in range(6)}
            tiles |= cells | {(ix, ROW_I), (ix, 293)}
            ins.append((ix, ROW_I, "railgun-ammo" if ammo == "B" else None))
    return ents, tiles, ins


def cells(ts):
    return "{" + ",".join("{%d,%d}" % c for c in sorted(ts)) + "}"


CONFIG = (TM.AT + "local rail,ok,bad=0,0,0 for _,q in pairs(INS) do local i=s.find_entities_filtered{type='inserter',position={q[1]+0.5,q[2]+0.5},radius=0.3}[1] if i then "
          "if q[3]==1 then i.use_filters=true i.inserter_filter_mode='whitelist' i.set_filter(1,{name='railgun-ammo',quality='normal',comparator='='}) rail=rail+1 end "
          "if i.drop_target and i.drop_target.type=='ammo-turret' then ok=ok+1 else bad=bad+1 end end end rcon.print('base inserters reaching a turret '..ok..', not reaching '..bad..', railgun filters set '..rail)")


def main():
    a = sys.argv[1:]
    step = a[0] if a else "plan"
    cols = collectors()
    allins = []
    for side in (-1, 1):
        mine = [c for c in cols if (c < 0) == (side < 0)]
        ents, tiles, ins = plan(side, mine)
        allins += ins
        name = "left" if side < 0 else "right"
        if step == "plan":
            r = L(TM.AT + "local need=0 for _,q in pairs(" + cells(tiles) + ") do if s.get_tile(q[1],q[2]).name~='space-platform-foundation' then need=need+1 end end rcon.print(need)")
            kinds = {}
            for e in ents:
                kinds[e["name"]] = kinds.get(e["name"], 0) + 1
            print(name, "collectors", len(mine), "entities", len(ents), kinds, "deck missing", r.strip())
        elif step == "deck":
            print(name, L(TM.AT + "local n=0 for _,q in pairs(" + cells(tiles) + ") do if s.get_tile(q[1],q[2]).name~='space-platform-foundation' and "
                          "s.count_entities_filtered{type='tile-ghost',position={q[1]+0.5,q[2]+0.5},radius=0.3}==0 then "
                          "if s.create_entity{name='tile-ghost',inner_name='space-platform-foundation',position={q[1],q[2]},force='player'} then n=n+1 end end end rcon.print('tile ghosts laid '..n)").strip())
        elif step == "build":
            ok, bad = TM.place(ents, "--apply" in a)
            print(name, "placed" if "--apply" in a else "dry run: would place", ok, "of", len(ents), "failed", bad)
    if step == "config" or (step == "build" and "--apply" in a):
        lst = "{" + ",".join("{%d,%d,%d}" % (x, y, 1 if k else 0) for x, y, k in allins) + "}"
        print(L(CONFIG.replace("INS", lst)))
        import edge_flight
        print(L(edge_flight.TARGETS))


if __name__ == "__main__":
    main()
