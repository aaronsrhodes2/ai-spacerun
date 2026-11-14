#!/usr/bin/env python3
"""The Aquilo fuel works (the Captain, 2026-11-13: the way to power Aquilo, and to get rid of its ice, is the ocean and the oil):
  ocean pump -> ammoniacal solution -> separation plant (5 ice + 50 ammonia a second at full speed) -> ammonia
  crude oil (9 wells, the nearest at 35.5,-2.5) -> pumpjack -> pipe
  ammonia + crude -> solid fuel plant (15 ammonia + 6 crude -> 1 solid fuel, 12 MJ) -> chest -> the heating tower's chest
So the heat of Aquilo comes from the ocean and the oil, not from shipped cells; the ice that the separation makes goes to the melter (steam),
to cryogenic science and to ice platforms. Everything stands on paved ground (concrete over ice-smooth: `set_tiles`, the item is the same
as the pad's) and every part touches a heat pipe (aquilo_base.heat_all lays them).
Layout (tile coordinates, south of the power block, north of the pond at 28..32,0..3):
  pump         offshore pump at (29.5,-0.5) facing south, its port tile (29,-2) is a pipe
  separation   chemical plant facing south, centre (28.5,-3.5): solution in at (29,-2), ammonia out at (29,-6)
  solid fuel   chemical plant facing south, centre (28.5,-7.5): ammonia in at (29,-6), crude in at (27,-6)
  oil          pumpjack on the well at 35.5,-2.5; a pipe from its port to (27,-6)
  chests       inserters take ice out of the separation plant and solid fuel out of the fuel plant into provider chests
Steps: build [--apply] | status. Never apply twice (it skips what stands).
Usage: aquilo_fuel.py build --apply"""
import json
import sys
from collections import deque

import aquilo_base as base
from _game import tools

SURF = "aquilo"
N, E, S, W = 0, 4, 8, 12
PIPES = []


DIRV = {N: (0, -1), E: (1, 0), S: (0, 1), W: (-1, 0)}
# connection points read from the game's prototypes (2026-11-13), relative to the centre tile, listed for facing N, E, S, W:
CHEM = {"in": [[(-1, -1), (1, -1)], [(1, -1), (1, 1)], [(1, 1), (-1, 1)], [(-1, 1), (-1, -1)]],       # fluid input 1 and 2 by facing
        "out": [[(-1, 1), (1, 1)], [(-1, -1), (-1, 1)], [(1, -1), (-1, -1)], [(1, 1), (1, -1)]]}
PUMPJACK_OUT = {N: (1, -2), E: (2, -1), S: (-1, 2), W: (-2, 1)}


def chem_port(cx, cy, facing, kind, k):
    """The tile a pipe must stand on to meet the chemical plant's input or output k (0 or 1) when it faces `facing` (centre TILE cx, cy)."""
    idx = {N: 0, E: 1, S: 2, W: 3}[facing]
    dx, dy = CHEM[kind][idx][k]
    out = DIRV[facing] if kind == "in" else (-DIRV[facing][0], -DIRV[facing][1])
    return (cx + dx + out[0], cy + dy + out[1])


def plan(sf_pos=None, sf_face=S, pj_face=N):
    base.ents[:] = []
    put = base.put
    put("offshore-pump", 29.5, -0.5, S)
    put("chemical-plant", 28.5, -3.5, S, recipe="ammoniacal-solution-separation")
    sx, sy = sf_pos
    put("chemical-plant", sx + .5, sy + .5, sf_face, recipe="solid-fuel-from-ammonia")
    put("pumpjack", 35.5, -2.5, pj_face)
    base.ents.append({"name": "pipe", "x": 29.5, "y": -1.5, "direction": 0, "params": dict(base.Q)})
    return len(base.ents)


def free_tiles(box):
    return base.free_grid(*box)


def route(src, dst, free, blocked):
    """Shortest 4-connected path of free tiles from src to dst (both included)."""
    q, prev = deque([src]), {src: None}
    while q:
        c = q.popleft()
        if c == dst:
            break
        for n in ((c[0], c[1] - 1), (c[0] - 1, c[1]), (c[0] + 1, c[1]), (c[0], c[1] + 1)):      # north first: keeps the lower tiles free for heat pipes
            if n in prev or (n not in free and n != dst) or n in blocked:
                continue
            prev[n] = c
            q.append(n)
    if dst not in prev:
        return []
    out, c = [], dst
    while c is not None:
        out.append(c)
        c = prev[c]
    return out[::-1]


def adjacent(a, b):
    return any(abs(p[0] - q[0]) + abs(p[1] - q[1]) == 1 for p in a for q in b)


def search(box):
    free0 = free_tiles(box)
    best = None
    sep_amm = chem_port(28, -4, S, "out", 0)          # the separation plant, south facing at tile (28,-4): ammonia (first fluid output)
    for pj in (N, E, S, W):
        pj_port = (35 + PUMPJACK_OUT[pj][0], -3 + PUMPJACK_OUT[pj][1])
        for face in (N, E, S, W):
            for cx in range(30, 47):
                for cy in range(-10, 3):
                    plan((cx, cy), face, pj)
                    occ = set()
                    for e in base.ents:
                        occ |= base.tiles_of(e)
                    tiles = {(cx + a, cy + b) for a in (-1, 0, 1) for b in (-1, 0, 1)}
                    if len(base.tiles_of(base.ents[2]) & occ) < 9 or not tiles <= free0:
                        continue
                    free = free0 - occ
                    amm = chem_port(cx, cy, face, "in", 0)
                    cru = chem_port(cx, cy, face, "in", 1)
                    if amm not in free or cru not in free or pj_port not in free or sep_amm not in free:
                        continue
                    p1 = route(sep_amm, amm, free, set())
                    if not p1:
                        continue
                    p2 = route(pj_port, cru, free - set(p1), {n for t in p1 for n in ((t[0] + 1, t[1]), (t[0] - 1, t[1]), (t[0], t[1] + 1), (t[0], t[1] - 1))} - {cru, pj_port})
                    if not p2 or adjacent(p1, p2):
                        continue
                    score = len(p1) + len(p2) + abs(cx - 33) * 0.1
                    if best is None or score < best[0]:
                        best = (score, (cx, cy), face, pj, p1, p2)
    return best


def main():
    step = sys.argv[1]
    apply = "--apply" in sys.argv
    box = (10, -12, 46, 6)
    best = search(box)
    if not best:
        sys.exit("no layout found")
    score, pos, face, pj, p1, p2 = best
    print("layout: fuel plant at", pos, "facing", face, "pumpjack facing", pj, "ammonia pipe", len(p1), "crude pipe", len(p2))
    plan(pos, face, pj)
    for x, y in p1 + p2:
        base.ents.append({"name": "pipe", "x": x + .5, "y": y + .5, "direction": 0, "params": dict(base.Q)})
    base.HEATED.add("pumpjack")
    # the two output inserters and chests go where the heat can reach: beside the plants, on free tiles
    free = free_tiles(box) - set().union(*[base.tiles_of(e) for e in base.ents])
    for mx, my, nm in ((28, -4, "sep"), (pos[0], pos[1], "fuel")):
        for dx, dy, d in ((-2, 0, W), (2, 0, E), (0, -2, N), (0, 2, S)):
            ix, iy = mx + dx, my + dy
            cx2, cy2 = ix + dx // 2 if dx else ix, iy + dy // 2 if dy else iy
            nb = [(ix + 1, iy), (ix - 1, iy), (ix, iy + 1), (ix, iy - 1)]
            if (ix, iy) in free and (cx2, cy2) in free and sum(1 for t in nb if t in free and t != (cx2, cy2)) >= 1:
                pick = {W: E, E: W, N: S, S: N}[d]          # an inserter's direction is the side it picks up from
                base.put("fast-inserter", ix + .5, iy + .5, pick)
                base.put("passive-provider-chest", cx2 + .5, cy2 + .5)
                free -= {(ix, iy), (cx2, cy2)}
                break
    print("heat pipes added by heat_all:", base.heat_all(box))
    print("new pieces (not yet standing):", base.drop_existing())
    if step == "build":
        r = json.loads(tools["place_entities"](json.dumps(base.ents), surface=SURF, dry_run=not apply))
        print("placed" if apply else "dry run", r.get("placed"), "failed", json.dumps(r.get("failed") or [])[:900])


if __name__ == "__main__":
    main()
