#!/usr/bin/env python3
"""Moves the rim's divide between the north and the west spoke (2026-11-13). Every rim tile flows to the nearest of the four spokes
(scripts/wheel_round.py), so a spoke gets only its own quarter of the rim's collectors. The spiral district (scripts/wheel_spiral.py)
lives off the WEST spoke alone, and on the Gleba Wheel (155 collectors, a rim backed up with 4,600 chunks elsewhere) that quarter carried
about 45 chunks a minute, mostly carbonic: the spiral's crushers stood idle and green science fell to 0. This turns the rim tiles between
315 and END degrees (0 = north, clockwise) round, so they flow west instead of north. Measured on the Gleba Wheel (2026-11-13): the chunks arrive on its north and east spokes
(north 2,145 on the belt, east 2,743, south 7, west 135), so the whole north-west eighth of the rim is turned west (END 358): the west spoke gets
half of the north quarter and the spiral its metallic chunks. Belts are only turned; nothing is placed or removed. Safe to run twice (it sets, it does not toggle).
Usage: wheel_rim_shift.py check | apply  [--only PLANET]   (default gleba; the other wheels do not need it)"""
import math
import sys

import wheel_round as R
from _game import tools
from _wheels import wheels

END = 358.0


def arc():
    rim = R.circle(R.RC)
    n = len(rim)
    out = []
    for i, t in enumerate(rim):
        a = math.degrees(math.atan2(t[0] + .5, -(t[1] + .5))) % 360
        if 315.0 <= a < END and abs(t[0]) > 2:
            prev = rim[(i - 1) % n]
            out.append((t[0], t[1], R.DIRS[(prev[0] - t[0], prev[1] - t[1])]))
    return out


SET = ("local s=game.surfaces['SURF'] local n,bad=0,0 for _,q in pairs(LIST) do local b=s.find_entities_filtered{type='transport-belt',position={q[1]+0.5,q[2]+0.5},radius=0.3}[1] if b then if b.direction~=q[3] then b.direction=q[3] end n=n+1 else bad=bad+1 end end "
       "rcon.print('rim tiles turned west '..n..', not a belt '..bad)")


def main():
    step = sys.argv[1]
    tiles = arc()
    print({"tiles in the arc": len(tiles), "from": 315, "to": END})
    if step == "check":
        return
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else "gleba"
    sys.argv = [sys.argv[0], "x", "--only", only]
    lst = "{" + ",".join("{%d,%d,%d}" % t for t in tiles) + "}"
    for name, planet, surface, turrets in wheels():
        if surface:
            print(name, tools["run_lua"](SET.replace("SURF", surface).replace("LIST", lst)))


if __name__ == "__main__":
    main()
