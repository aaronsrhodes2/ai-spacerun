"""
Four more steel furnaces on the iron unload belt (y=-155), south side, steel on a belt at y=-149 flowing east into the existing
steel belt at x=69 (side-load at (69,-149)). Usage: scripts/build_steel2.py [--build]
"""
import json
import sys

from _game import tools
from build_iron_depot import belt, ins, place, pole

N_, E_, S_, W_ = 0, 4, 8, 12
XS = (53, 57, 61, 65)


def main():
    build = "--build" in sys.argv
    ents = []
    for x in XS:
        ents.append({"name": "electric-furnace", "x": x + 1.5, "y": -151.5, "direction": 0})      # rows -153..-151
        ents.append(ins("inserter", x + 1, -154, S_))        # picks the iron belt (north, y=-155), drops into the furnace
        ents.append(ins("inserter", x, -150, S_))            # picks the furnace (north), drops on the steel belt (south, y=-149)
    for x in range(XS[0], 69):
        ents.append(belt(x, -149, E_))
    ents += [pole(55, -150), pole(63, -150), pole(60, -154), pole(52, -154)]
    place(ents, build, "steel2")


if __name__ == "__main__":
    main()
