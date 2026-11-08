"""
Military science plant for the east base (rows on the north-flowing bus).

    Y_S   the shared belt row. Piercing rounds (from the sets row below) and grenades (from the
          flipped row above) land on opposite lanes of it, and it runs east to become belt A of the
          science row. Walls arrive on belt B (row Y_S+1) from the wall row.

          y Y_S-7..Y_S     grenade row, flipped (O at the bottom = Y_S): A = coal, B = iron
          y Y_S..Y_S+7     sets row [firearm magazine -> piercing rounds], O at the top = Y_S
          y Y_S+9..Y_S+16  wall row (stone brick -> stone wall), its O belt runs east then north to Y_S+1
          y Y_S-6..Y_S+1   science row, machines north of A=Y_S, B=Y_S+1, packs out on Y_S-6

Taps (bus trunk -> row belt); normal rows take B from the lower trunk, flipped rows A from the lower:
    sets row  A = trunk 1 (iron|copper lanes), B = trunk 0 (steel)
    grenades  A = trunk 1 (iron), B = trunk 7 (coal)          [flipped]
    walls     A = trunk 5 (stone brick)
"""
from . import bus
from .blocks import AM2, E, N, S, W, ROW_HEIGHT, _belt, _put, assembler_row

X = 98
Y_S = -120
SETS = 2
GRENADE_MACHINES = 3
SCIENCE_MACHINES = 4
SET_PITCH = 8


def sets_row(x, y0, n):
    """n sets of [firearm-magazine][piercing-rounds-magazine] with a direct inserter between."""
    ya, yb = y0 + 6, y0 + 7
    ents = []
    for dx in range(SET_PITCH * n):
        for ty in (ya, yb, y0):
            ents.append(_belt(x + dx, ty))
    for i in range(n):
        xs = x + SET_PITCH * i
        ents.append(_put(AM2, xs, y0 + 2, w=3, h=3, recipe="firearm-magazine"))
        ents.append(_put(AM2, xs + 4, y0 + 2, w=3, h=3, recipe="piercing-rounds-magazine"))
        ents.append(_put("inserter", xs + 3, y0 + 3, W))               # magazine: west machine -> east machine
        ents.append(_put("inserter", xs, y0 + 5, S))                   # iron for the magazine machine (belt A)
        ents.append(_put("inserter", xs + 4, y0 + 5, S))               # copper for piercing (belt A)
        ents.append(_put("long-handed-inserter", xs + 5, y0 + 5, S))   # steel for piercing (belt B)
        ents.append(_put("inserter", xs + 5, y0 + 1, S))               # piercing out onto O
        for px, py in ((xs + 2, y0 + 5), (xs + 7, y0 + 5), (xs + 2, y0 + 1), (xs + 7, y0 + 1)):
            ents.append(_put("small-electric-pole", px, py))
    return ents


def plant():
    """Returns (entities, taps) where taps = [(trunk, branch_row)] for bus.tap(k, row, X)."""
    ents = []
    sets_w = SET_PITCH * SETS
    xs_sci = X + max(sets_w, 3 * GRENADE_MACHINES) + 2          # science row start; x_v = xs_sci - 1
    x_v = xs_sci - 1
    ents += sets_row(X, Y_S, SETS)
    ents += assembler_row(X, Y_S - 7, "grenade", GRENADE_MACHINES, flip=True).entities
    # shared belt from the end of the sets row to the science row's belt A
    for dx in range(sets_w, xs_sci - X):
        ents.append(_belt(X + dx, Y_S))
    sci = assembler_row(xs_sci, Y_S - 6, "military-science-pack", SCIENCE_MACHINES)
    ents += sci.entities
    wall = assembler_row(X, Y_S + 9, "stone-wall", 1)
    ents += wall.entities
    for xx in range(X + 3, x_v):                                   # wall O belt east to the riser
        ents.append(_belt(xx, Y_S + 9))
    ents.append({"name": "transport-belt", "x": x_v + 0.5, "y": Y_S + 9 + 0.5, "direction": N})
    for yy in range(Y_S + 8, Y_S + 1, -1):
        ents.append({"name": "transport-belt", "x": x_v + 0.5, "y": yy + 0.5, "direction": N})
    ents.append(_belt(x_v, Y_S + 1))                               # turns east onto the science row's belt B
    taps = [(1, Y_S + 6), (0, Y_S + 7),                            # sets row A (iron|copper), B (steel)
            (1, Y_S - 6), (7, Y_S - 7),                            # grenade row A (iron), B (coal)
            (5, Y_S + 9 + 6)]                                      # wall row A (stone brick)
    return ents, taps


def dedupe(ents):
    """Drop exact duplicate belts (rows sharing the O belt tile)."""
    seen, out = set(), []
    for e in ents:
        key = (e["name"], e["x"], e["y"])
        if e["name"] == "transport-belt" and key in seen:
            continue
        seen.add(key)
        out.append(e)
    return out
