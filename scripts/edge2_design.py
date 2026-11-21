#!/usr/bin/env python3
"""Edgerunner 2, STAGE 1: the layout on paper (plan "Edgerunner 2", approved by the Captain 2026-11-21). READ-ONLY: it places nothing and touches no game.
The Captain's choice: the triangle INVERTED, flat front toward the flight, apex at the rear; a dense railgun line on the flat face for the
running damage, a moderate array round the rest of the perimeter for rest.

Coordinates: tiles, x east, y SOUTH, the ship flies NORTH (toward y = 0 and beyond). The flat face is the row y = 0; the apex is at y = DEPTH.
  hull       every tile (x, y) with |x + 0.5| <= HALF * (1 - y / DEPTH)  (half width HALF at the front, 0 at the apex)
  front line railguns 3 wide x 4 deep, side by side along the face, tiles y 0..3, facing NORTH; their feed inserters on y = 4, the rounds belt on y = 5.
             Every railgun's 36-degree arc opens forward over open space: nothing of ours stands in front of the face, so no own entity is on any
             shot line (checked below by `arcs`).
  sides      railgun "ears" facing SOUTH-WEST (west edge) / SOUTH-EAST (east edge), straight out from the slanted edge (its outward normal is about 132 degrees
             off north), every EAR_PITCH tiles down each edge, gun turrets between them. Facing north-west, as first tried, put the front line inside the
             arcs of the ears near the face: 10 shot lines were fouled, so the facing was turned outward
  spine      a 3-wide column x -1..1 from y 6 to the hub carrying the rounds belt from the works to the front belt's middle, where a splitter sends it both ways
  hub        8 x 8 at (-4..3, HUB_Y..HUB_Y+7); works west and east of the spine; tanks, fusion, accumulators toward the apex
Steps: plan | map | arcs | json     Usage: edge2_design.py plan ; edge2_design.py map ; edge2_design.py arcs"""
import json
import math
import os
import sys

HALF = 80            # half width of the flat front, tiles
DEPTH = 120          # front to apex (90 left the rear too narrow for fusion and the bank: the check below found it)
RW, RH = 3, 4        # railgun footprint
EAR_PITCH = 14       # railgun ear every this many rows down each slanted side
GUN_PITCH = 7
HUB_Y = 40
ARC = math.radians(36)
RANGE = 50           # a railgun shot is a line this long
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "snapshots", "edge2_layout.json")


def half(y):
    return HALF * (1 - y / DEPTH)


def hull_rows():
    return {y: (math.ceil(-half(y + 0.5) - 0.5), math.floor(half(y + 0.5) - 0.5)) for y in range(DEPTH)}


def build():
    rows = hull_rows()
    ents = []          # (kind, x0, y0, w, h, facing or None)
    # front line: as many railguns as fit on the face
    n = (2 * HALF) // RW
    x0 = -HALF
    for i in range(n):
        x = x0 + i * RW
        ents.append(("railgun", x, 0, RW, RH, "N"))
        ents.append(("inserter", x + 1, 4, 1, 1, None))
    ents.append(("belt-rounds-front", -HALF, 5, 2 * HALF, 1, None))
    # slanted sides: ears at 45 degrees outward, guns between
    for side in (-1, 1):
        y = 10
        while y < DEPTH - 12:
            lo, hi = rows[y]
            edge = lo if side < 0 else hi
            ents.append(("railgun-ear", edge + (-5 if side < 0 else 2), y, 4, 4, "SW" if side < 0 else "SE"))
            gy = y + EAR_PITCH // 2
            if gy < DEPTH - 12:
                lo2, hi2 = rows[gy]
                e2 = lo2 if side < 0 else hi2
                ents.append(("gun", e2 + (-3 if side < 0 else 1), gy, 2, 2, None))
            y += EAR_PITCH
    # apex array
    ents.append(("railgun-ear", -2, DEPTH - 6, 4, 4, "S"))
    ents.append(("gun", -4, DEPTH - 8, 2, 2, None))
    ents.append(("gun", 2, DEPTH - 8, 2, 2, None))
    # the big blocks (rectangles, contents come at stage 2)
    blocks = [
        ("spine (rounds belt)", -1, 6, 3, 26),
        ("hub", -4, 32, 8, 8),
        ("rounds works west", -50, 8, 44, 22),
        ("rounds works east", 6, 8, 44, 22),
        ("cargo bays + ore smelting west", -36, 42, 29, 12),
        ("cargo bays + ore smelting east", 6, 42, 29, 12),
        ("tanks fuel and oxidizer (4 + 4)", -20, 56, 40, 4),
        ("fusion: 4 reactors, 8 generators, 2 coolers", -28, 62, 56, 16),
        ("accumulator bank (320)", -16, 80, 32, 10),
        ("thrusters (8)", -12, 92, 24, 6),
    ]
    return rows, ents, blocks


def fit(blocks, rows):
    """Every block's four corners must lie on the hull, and no two blocks may overlap."""
    bad = []
    for name, x, y, w, h in blocks:
        for cx, cy in ((x, y), (x + w - 1, y), (x, y + h - 1), (x + w - 1, y + h - 1)):
            lo, hi = rows.get(cy, (1, 0))
            if not lo <= cx <= hi:
                bad.append("%s: corner (%d,%d) is off the hull" % (name, cx, cy))
                break
    for i, a in enumerate(blocks):
        for b in blocks[i + 1:]:
            if a[1] < b[1] + b[3] and b[1] < a[1] + a[3] and a[2] < b[2] + b[4] and b[2] < a[2] + a[4]:
                bad.append("%s overlaps %s" % (a[0], b[0]))
    return bad


def tiles(e):
    _, x, y, w, h, _ = e
    return {(x + i, y + j) for i in range(w) for j in range(h)}


def arcs(ents, rows):
    """For each railgun, the own entities (other than itself and its feed) lying inside its 50-tile, 36-degree arc."""
    face = {"N": 0.0, "NW": -math.pi / 4, "NE": math.pi / 4, "S": math.pi, "SW": -3 * math.pi / 4, "SE": 3 * math.pi / 4}    # angle measured from north, clockwise (east positive)
    occ = {}
    for e in ents:
        for t in tiles(e):
            occ[t] = e
    bad = {}
    for e in ents:
        if e[0] not in ("railgun", "railgun-ear") or e[5] not in face:
            continue
        cx, cy = e[1] + e[3] / 2, e[2] + e[4] / 2
        a0 = face[e[5]]
        hit = set()
        for (tx, ty), o in occ.items():
            if o is e or (o[0] == "inserter" and o[1] // 1 in range(e[1], e[1] + e[3])):
                continue
            dx, dy = tx + 0.5 - cx, ty + 0.5 - cy
            d = math.hypot(dx, dy)
            if d < 2.5 or d > RANGE:
                continue
            ang = math.atan2(dx, -dy)          # from north, clockwise
            diff = abs((ang - a0 + math.pi) % (2 * math.pi) - math.pi)
            if diff <= ARC:
                hit.add(o[0])
        if hit:
            bad[(e[0], e[1], e[2])] = sorted(hit)
    return bad


def summary(rows, ents, blocks):
    area = sum(hi - lo + 1 for lo, hi in rows.values())
    by = {}
    for e in ents:
        by[e[0]] = by.get(e[0], 0) + 1
    return area, by


def draw(rows, ents, blocks):
    W = 2 * HALF + 4
    g = [[" "] * W for _ in range(DEPTH + 2)]
    for y, (lo, hi) in rows.items():
        for x in range(lo, hi + 1):
            g[y][x + HALF + 2] = "."
    ch = {"railgun": "R", "railgun-ear": "E", "inserter": "i", "gun": "g", "belt-rounds-front": "="}
    for e in ents:
        for (tx, ty) in tiles(e):
            if 0 <= ty < len(g) and 0 <= tx + HALF + 2 < W:
                g[ty][tx + HALF + 2] = ch.get(e[0], "?")
    for k, (name, x, y, w, h) in enumerate(blocks):
        c = "ABCDEFGHI"[k]
        for i in range(w):
            for j in range(h):
                if 0 <= y + j < len(g) and 0 <= x + i + HALF + 2 < W and g[y + j][x + i + HALF + 2] in ".":
                    g[y + j][x + i + HALF + 2] = c
    return "\n".join("".join(r).rstrip() for r in g) + "\n" + "\n".join("%s = %s" % ("ABCDEFGHI"[k], b[0]) for k, b in enumerate(blocks))


def main():
    step = sys.argv[1] if len(sys.argv) > 1 else "plan"
    rows, ents, blocks = build()
    area, by = summary(rows, ents, blocks)
    if step == "map":
        print(draw(rows, ents, blocks))
        return
    bad = arcs(ents, rows)
    if step == "arcs":
        print("railguns with own entities in their arc: %d" % len(bad))
        for k, v in list(bad.items())[:20]:
            print("  ", k, v)
        return
    if step == "json":
        json.dump({"half": HALF, "depth": DEPTH, "ents": ents, "blocks": blocks}, open(OUT, "w", encoding="utf-8"))
        print("written", OUT)
        return
    off = fit(blocks, rows)
    print("blocks fit the hull: " + ("yes" if not off else "NO"))
    for o in off:
        print("   " + o)
    foundation_launches = math.ceil(area / 50.0)
    print("Edgerunner 2 (inverted triangle): front %d wide, depth %d, %d deck tiles = %d foundation = %d rocket launches (50 a rocket)" % (2 * HALF, DEPTH, area, area, foundation_launches))
    print("armament: " + ", ".join("%s %d" % (k, v) for k, v in sorted(by.items())))
    print("railguns total %d (front %d, ears %d); shot lines with own entities in the arc: %d" % (by.get("railgun", 0) + by.get("railgun-ear", 0), by.get("railgun", 0), by.get("railgun-ear", 0), len(bad)))
    R = by.get("railgun", 0) + by.get("railgun-ear", 0)
    print("power: %d railguns x 3.9 MW firing = %.0f MW if ALL fire at once, plus about 30 MW for the ship; fusion 4 reactors / 8 generators = 500 MW nameplate (margin %.0f MW); the bank (320 x 30 MJ = 9.6 GJ) alone would carry a full volley for %.0f s if the plant tripped" % (R, R * 3.9, 500 - R * 3.9 - 30, 9600 / (R * 3.9 + 30)))
    print("rounds: a kill = 1 round; reserve 30,000 rounds carried (about 2.8 h at one kill a second); on-board works make what asteroid chunks allow (a few a minute from chunks alone), so the reserve is the doctrine")
    print("blocks:")
    for name, x, y, w, h in blocks:
        print("   %-48s x %4d..%4d  y %3d..%3d  (%d x %d)" % (name, x, x + w - 1, y, y + h - 1, w, h))


if __name__ == "__main__":
    main()
