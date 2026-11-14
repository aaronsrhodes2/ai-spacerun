#!/usr/bin/env python3
"""Hooks up the two flank asteroid collectors of the Fulgora-Aquilo 2 Shuttle (the Captain, 2026-11-14: "I added two grabbers ... please cook them
up so we are gathering those resources"). Each sits at (+-24.5,-6.5) behind a one-tile gap in the deck, facing north, with nothing taking its catch.
Route (tile coordinates, planned from the ship's real free tiles): one deck tile in the gap, a fast inserter taking from the collector, an express belt up
the rim column (x=+-22) to y=-20, then in along y=-20 and y=-21 to the chunk belt of the nose collector on that side: it ends beside that belt's
underground entrance at (+-6.5,-20.5) and sideloads into it, so the chunks join the line that already feeds the crushers.
Usage: aquilo_grabbers.py [--apply]"""
import sys

import _wheels
from _game import tools

NAME = "Aquilo 2"
Q = {"quality": "epic"}


def belt(x, y, d):
    return {"name": "express-transport-belt", "x": x + .5, "y": y + .5, "direction": d, "params": Q}


def side(sign):
    """sign -1 = west flank, +1 = east flank."""
    s = sign
    ents = [{"name": "fast-inserter", "x": s * 23 + .5, "y": -6.5, "direction": 4 if s > 0 else 12, "params": Q}]
    rim, top = s * 22, s * 13 if s > 0 else s * 14
    for y in range(-7, -20, -1):                              # up the rim column
        ents.append(belt(rim, y, 0))
    along = 12 if s > 0 else 4                                # heading toward the centre line
    ents.append(belt(rim, -20, along))
    x = rim - s
    while x != top:
        ents.append(belt(x, -20, along))
        x -= s
    ents.append(belt(top, -20, 0))                            # step up to y=-21
    ents.append(belt(top, -21, along))
    x = top - s
    stop = s * 8 if s < 0 else 7                              # last tile beside the underground entrance at +-6.5 (tile 6 / -7)
    while True:
        ents.append(belt(x, -21, along))
        if x == stop:
            break
        x -= s
    return ents, (s * 23, -7)


def main():
    apply = "--apply" in sys.argv
    allents, deck = [], set()
    for s in (-1, 1):
        e, gap = side(s)
        allents += e
        deck.add(gap)
    surf = tools["run_lua"]("for _,q in pairs(game.forces.player.platforms) do if q.name:find('%s',1,true) then rcon.print(q.surface.name) end end" % NAME).strip()
    print("surface", surf, "entities", len(allents), "deck tiles", sorted(deck))
    if apply:
        print("deck", _wheels.lay_foundation(deck, surf))
    ok, bad = _wheels.place_all(allents, surf, apply)
    print("placed" if apply else "dry run", ok, "failures", bad)


if __name__ == "__main__":
    main()
