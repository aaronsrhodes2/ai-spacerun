#!/usr/bin/env python3
"""Edgerunner FLANK RAILGUNS (the Captain, 2026-11-18: "Surround the entire frame with railguns, rocket turrets and gun turrets and give
them the correct target priorities").
The flanks carry guns and rocket turrets on the stage-1 pattern; the pattern's railgun slots (rows 25, 55, 85 of every 100) were left empty
because the side belt has only two lanes. Railgun rounds now have a belt of their own (edge_spoke.py), so:

  INNER BELT  the west / east arm of the spoke's first tier (row -468 / -467) ends beside the first apex railgun. It is turned south there
              and runs down the INSIDE of each flank to row 280: a staircase 9 tiles in from the outer edge, railgun rounds only, one long
              dead end (it cannot clog). Beside a railgun it runs straight (the pad is five rows tall and the staircase would cut into it),
              then catches up sideways on the row below. Where something already stands on its way (the ammunition feed at the side's
              middle) it dives under by underground belt.
  RAILGUNS    one in every free railgun slot of the pattern from row -455 to row 280, 3 x 4 facing north on the pattern's own tiles
              (edge+4 .. edge+6), fed from the inner side by one bulk inserter (filter railgun rounds).
  TARGETS     edge_flight.py targets: railguns huge asteroids only, rocket turrets big and huge, guns everything else.
  KNOWN RISK  a railgun shot goes through our own hull. A flank railgun faces north and turns 36 degrees each way; the flank itself runs
              30 degrees east (west) of north, so a shot at a huge asteroid in the last few degrees of the arc on that side rakes the strip.
Steps: plan | deck | build [--apply] | config | status
Usage: edge_rails.py plan ; edge_rails.py deck ; edge_rails.py build --apply ; edge_rails.py status"""
import json
import sys

import edge_flanks as F
import edge_ship as ES
import triangle_miner as TM
from _game import tools
from edge_works import T

L = tools["run_lua"]
BELT, UG, BULK, RAIL = "express-transport-belt", "express-underground-belt", "bulk-inserter", "railgun-turret"
N, E, S, W = 0, 4, 8, 12
DIR = {(0, -1): N, (1, 0): E, (0, 1): S, (-1, 0): W}
Y_TOP, Y_BOT = -455, 280
START = {-1: (-53, -468), 1: (53, -467)}          # the arm's last belt tile on each side
APEX_PAD = {-1: (-57, -470), 1: (55, -470)}       # the stage-1 railgun beside it: (first tile, top row); five rows tall


def side_plan(side):
    s = 1 if side < 0 else -1
    j = F.junction(side)
    pads = []                                       # (x0, ytop): railgun tiles x0..x0+2, rows ytop..ytop+4
    for y0 in range(Y_TOP, Y_BOT, 100):
        rows = min(100, Y_BOT - y0 + 1)
        _, ts, _, _ = ES.stretch(y0, rows, side)
        for name, x0, y, w, h in ts:
            if name == RAIL and abs(y - j) >= F.KEEP_CLEAR + 6 and y + 5 <= Y_BOT:
                pads.append((x0, y))
    fixed = {}                                      # row -> belt column where a pad forces it
    for x0, y in pads + [APEX_PAD[side]]:
        c = x0 + 4 if side < 0 else x0 - 2
        for r in range(y - 1, y + 5):
            fixed[r] = c
    col = lambda y: fixed.get(y, ES.edge(y, side) + 9 * s)   # 9, not 8: a rocket pad is three rows tall and the edge steps in under it
    cx, cy = START[side]
    path = [(cx, cy)]
    for y in range(cy + 1, Y_BOT + 1):
        path.append((cx, y))                        # one row down in the same column
        t = col(y)
        while cx != t:                              # then sideways on that row to where the next row wants it
            cx += 1 if t > cx else -1
            path.append((cx, y))
    ins = []
    for x0, y in pads:
        ix = x0 + 3 if side < 0 else x0 - 1
        ins.append((ix, y + 1, E if side < 0 else W))
    return dict(side=side, path=path, pads=pads, ins=ins)


def survey(plan):
    """Which path cells and pad cells hold something already (name per cell), and which have no deck."""
    cells = set(plan["path"][1:]) | {(i[0], i[1]) for i in plan["ins"]}
    for x0, y in plan["pads"]:
        cells |= {(x0 + i, y + k) for i in range(3) for k in range(5)}
    lst = "{" + ",".join("{%d,%d}" % c for c in sorted(cells)) + "}"
    r = L(TM.AT + "local o,need={},0 for _,q in pairs(" + lst + ") do if s.get_tile(q[1],q[2]).name~='space-platform-foundation' then need=need+1 end "
          "local e=s.find_entities_filtered{area={{q[1]+0.1,q[2]+0.1},{q[1]+0.9,q[2]+0.9}}}[1] if e and e.type~='tile-ghost' then o[#o+1]={q[1],q[2],e.name} end end rcon.print(helpers.table_to_json({need=need,hit=o}))")
    d = json.loads(r)
    return cells, d["need"], {(h[0], h[1]): h[2] for h in (d["hit"] or [])}


def entities(plan, hits):
    """Belts with underground hops over occupied runs; pads that are clear; their inserters."""
    path = plan["path"]
    e, skipped = [], []
    i = 0
    n = len(path)
    first = True
    while i < n:
        c = path[i]
        nxt = path[i + 1] if i + 1 < n else (c[0], c[1] + 1)
        d = DIR[(nxt[0] - c[0], nxt[1] - c[1])]
        if nxt in hits and i + 1 < n:               # the next cells are taken: dive here, come up after them (must be a straight run)
            k = i + 1
            while k < n and path[k] in hits:
                k += 1
            if k >= n:
                break
            out = path[k]
            straight = all(path[m][0] - path[m - 1][0] == nxt[0] - c[0] and path[m][1] - path[m - 1][1] == nxt[1] - c[1] for m in range(i + 1, k + 1))
            if not straight or k - i > 9:
                skipped.append(("hop not straight or too long", c, out))
                return e, skipped, False
            e.append(T(UG, c[0], c[1], d, type="input"))
            e.append(T(UG, out[0], out[1], d, type="output"))
            i = k + 1
            first = False
            continue
        e.append(T(BELT, c[0], c[1], d))
        i += 1
    for (x0, y), (ix, iy, d) in zip(plan["pads"], plan["ins"]):
        cells = {(x0 + a, y + b) for a in range(3) for b in range(5)} | {(ix, iy)}
        if cells & set(hits):
            skipped.append(("pad taken", x0, y, sorted(hits[c] for c in cells & set(hits))[:2]))
            continue
        e.append(T(RAIL, x0, y, 0, 3, 4))
        e.append(T(BULK, ix, iy, d))
    return e, skipped, True


CONFIG = (TM.AT + "local n=0 for _,q in pairs(INS) do local i=s.find_entities_filtered{type='inserter',position={q[1]+0.5,q[2]+0.5},radius=0.3}[1] if i then i.use_filters=true i.inserter_filter_mode='whitelist' "
          "i.set_filter(1,{name='railgun-ammo',quality='normal',comparator='='}) if i.drop_target and i.drop_target.name=='railgun-turret' then n=n+1 end end end "
          "local t=0 for _,r in pairs(s.find_entities_filtered{name='railgun-turret'}) do r.set_priority_target(1,'huge-metallic-asteroid') r.set_priority_target(2,'huge-carbonic-asteroid') r.set_priority_target(3,'huge-oxide-asteroid') r.ignore_unprioritised_targets=true t=t+1 end "
          "rcon.print('railgun inserters reaching a railgun '..n..' of '..#INS..'; railguns on the ship '..t..', all set to huge asteroids only')")

STATUS = (TM.AT + "local t,armed,rounds=0,0,0 for _,r in pairs(s.find_entities_filtered{name='railgun-turret'}) do t=t+1 local c=r.get_inventory(defines.inventory.turret_ammo).get_item_count() rounds=rounds+c if c>0 then armed=armed+1 end end "
          "local b=0 for _,x in pairs(s.find_entities_filtered{type={'transport-belt','underground-belt','splitter'}}) do for i=1,x.get_max_transport_line_index() do b=b+x.get_transport_line(i).get_item_count('railgun-ammo') end end "
          "rcon.print('railguns '..t..', armed '..armed..', rounds in them '..rounds..', rounds on belts '..b..', tile ghosts '..s.count_entities_filtered{type='tile-ghost'}..', hub foundations '..p.hub.get_inventory(defines.inventory.hub_main).get_item_count('space-platform-foundation'))")


def main():
    a = sys.argv[1:]
    step = a[0] if a else "status"
    if step == "status":
        return print(L(STATUS))
    allins = []
    for side in (-1, 1):
        plan = side_plan(side)
        cells, need, hits = survey(plan)
        start = plan["path"][0]
        hits.pop(start, None)
        ents, skipped, ok = entities(plan, hits)
        allins += [(i[0], i[1]) for (x0, y), i in zip(plan["pads"], plan["ins"])]
        name = "left" if side < 0 else "right"
        if step == "plan":
            kinds = {}
            for v in hits.values():
                kinds[v] = kinds.get(v, 0) + 1
            print(name, "path", len(plan["path"]), "cells, railgun slots", len(plan["pads"]), ", deck missing", need, ", cells taken", kinds, ", entities", len(ents), ", skipped", skipped[:6], "ok" if ok else "PATH BROKEN")
        elif step == "deck":
            lst = "{" + ",".join("{%d,%d}" % c for c in sorted(cells)) + "}"
            print(name, L(TM.AT + "local n=0 for _,q in pairs(" + lst + ") do if s.get_tile(q[1],q[2]).name~='space-platform-foundation' and "
                          "s.count_entities_filtered{type='tile-ghost',position={q[1]+0.5,q[2]+0.5},radius=0.3}==0 then "
                          "if s.create_entity{name='tile-ghost',inner_name='space-platform-foundation',position={q[1],q[2]},force='player'} then n=n+1 end end end rcon.print('tile ghosts laid '..n)").strip())
        elif step == "build":
            apply = "--apply" in a
            if apply:                               # the arm's last tile turns south: take the old one out first (its rounds go to the hub)
                print(L(TM.AT + "local e=s.find_entities_filtered{type='transport-belt',position={%s+0.5,%s+0.5},radius=0.3}[1] if e and e.direction~=8 then e.direction=8 rcon.print('arm end turned south') else rcon.print('arm end already south or missing') end" % start).strip())
                ents = ents[1:]
            ok2, bad = TM.place(ents, apply)
            print(name, "placed" if apply else "dry run: would place", ok2, "of", len(ents), "failed", bad)
    if step in ("build", "config") and (step == "config" or "--apply" in a):
        print(L(CONFIG.replace("INS", "{" + ",".join("{%d,%d}" % c for c in allins) + "}")))


if __name__ == "__main__":
    main()
