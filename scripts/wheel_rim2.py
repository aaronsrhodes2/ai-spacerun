#!/usr/bin/env python3
"""A second set of collectors on the rim (the Captain, 2026-11-13: expand what the wheels consume and fill the inside with factories).
Three of the four wheels use every chunk they catch (rim and spoke belts about 2% full), so more factories inside need more chunks
first. scripts/wheel_round.py put a collector every 30 rim tiles; this puts one in every gap, half way, with the same inserter behind
it onto the rim belt. The Gleba Wheel is left out by default: its rim is backed up (18 collectors full), it needs consumers, not chunks.
Steps (--only PLANET, default nauvis, fulgora and vulcanus one after another): check | build [--apply]. Never apply twice.
Usage: wheel_rim2.py check | build [--apply] [--only PLANET]"""
import math
import sys

import wheel_round as R
from _wheels import lay_foundation, place_all, wheels

new, tiles, holes = [], set(), set()


def layout():
    R.layout()
    rim = R.circle(R.RC)
    old = [(e["x"], e["y"]) for e in R.ents if e["name"] == "asteroid-collector"]
    cells = {}
    for (x, y) in old:
        cells.setdefault((int(x) // 16, int(y) // 16), []).append((x, y))

    def near_old(cx, cy, r):
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for (x, y) in cells.get((int(cx) // 16 + dx, int(cy) // 16 + dy), []):
                    if math.hypot(x - cx, y - cy) < r:
                        return True
        return False

    last = -100
    for i, t in enumerate(rim):
        if i - last < 28 or abs(t[0]) < 14 or abs(t[1]) < 14:
            continue
        o = R.outward(t)
        ins = (t[0] + o[0], t[1] + o[1])
        ctr = (t[0] + 3 * o[0], t[1] + 3 * o[1])
        body = [(ctr[0] + a, ctr[1] + b) for a in (-1, 0, 1) for b in (-1, 0, 1)]
        if near_old(ctr[0] + .5, ctr[1] + .5, 9) or not R.free([ins] + body):
            continue
        d = R.DIRS[o]
        new.append({"name": "asteroid-collector", "x": ctr[0] + .5, "y": ctr[1] + .5, "direction": d, "params": dict(R.Q)})
        new.append({"name": "fast-inserter", "x": ins[0] + .5, "y": ins[1] + .5, "direction": d, "params": dict(R.Q)})
        side = (o[1], o[0])
        front = {(ctr[0] + o[0] + k * side[0], ctr[1] + o[1] + k * side[1]) for k in (-1, 0, 1)}
        for c in body + [ins]:
            R.occ[c] = "asteroid-collector"
            if c not in front:                       # a collector's front row must hang over open space (its buildability rule):
                tiles.add(c)                         # deck there and the game refuses it
        holes.update(front)
        last = i
    return {"old collectors": len(old), "new collectors": len(new) // 2, "deck tiles": len(tiles)}


def main():
    step = sys.argv[1]
    print(layout())
    if step == "check":
        return
    apply = "--apply" in sys.argv
    for name, planet, surface, turrets in wheels():
        if "--only" not in sys.argv and planet == "gleba":
            continue
        print("==", name, surface)
        if apply:
            print("deck tiles", lay_foundation(tiles, surface))
        ok, bad = place_all(new, surface, apply)
        print("placed" if apply else "dry run", ok, "failures", bad)


if __name__ == "__main__":
    main()
