"""
West side of the bus, built as a mirror image of the east side.

Design in the east-side ("virtual") coordinates exactly as for bus.tap / bus.give / assembler_row, then mirror every entity
about the bus centre: a virtual tile x becomes 165 - x, a centre x becomes 166 - x, E and W swap. Virtual trunk kv is the
real trunk 7 - kv, so a virtual row sits next to real trunk 0, and the virtual riser (x=96) lands on real x=69 where
nothing runs. Lanes mirror too: a virtual give lands on the real WEST lane of its trunk.
"""
from . import bus

E, W = 4, 12
MIRROR_SUM = 166        # centre x -> 166 - x


def real_k(kv):
    return bus.TRUNKS - 1 - kv


def mirror_entity(e):
    e = dict(e)
    e["x"] = MIRROR_SUM - e["x"]
    if e["direction"] == E:
        e["direction"] = W
    elif e["direction"] == W:
        e["direction"] = E
    return e


def mirror(entities):
    return [mirror_entity(e) for e in entities]


def real_splitter_tile(kv, y):
    """The real trunk tile a virtual tap's splitter replaces."""
    x, ty = bus.splitter_tile(kv, y)
    return 165 - x, ty
