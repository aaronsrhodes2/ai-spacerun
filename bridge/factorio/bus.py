"""
The east base bus: eight trunk belts running NORTH, one every 3 tiles, with two free tiles beside each.

    trunk k at x = BUS_X0 + 3k, from y = SOUTH_Y (south end, supplied from there) to NORTH_Y
    tap(k, y, x_end)  splits trunk k at row y+1 and runs a branch EAST along row y to the tile just
                      west of x_end, passing under each trunk it crosses with a chain of underground belts
                      (entrance on the second free tile, exit on the first free tile of the next gap)

A row takes belt A from trunk ka and belt B from trunk kb with ka < kb, so B's branch never lands on
A's splitter. Splitters sit at row y+1 and branches at row y; a row's two belts are adjacent rows
(y0+6 and y0+7), so splitters at y0+7 and y0+8.
"""
N, E, S, W = 0, 4, 8, 12
BUS_X0 = 72
SPACING = 3
TRUNKS = 8
SOUTH_Y = -62
NORTH_Y = -139
TRUNK_ITEMS = ["iron-plate", "copper-plate", "steel-plate", "plastic-bar",
               "coal", "stone-brick", "sulfur", "spare"]


def trunk_x(k):
    return BUS_X0 + SPACING * k


def last_x():
    return trunk_x(TRUNKS - 1)


def _belt(x, y, d):
    return {"name": "transport-belt", "x": x + 0.5, "y": y + 0.5, "direction": d}


def _ug(x, y, kind):
    return {"name": "underground-belt", "x": x + 0.5, "y": y + 0.5, "direction": E, "params": {"type": kind}}


def splitter_tile(k, y):
    return (trunk_x(k), y + 1)


def trunk_entities(taps=()):
    """All trunk belts flowing north, with a splitter replacing the belt at each tap's splitter row."""
    skip = {splitter_tile(k, y) for k, y in taps}
    ents = []
    for k in range(TRUNKS):
        for y in range(SOUTH_Y, NORTH_Y - 1, -1):
            if (trunk_x(k), y) not in skip:
                ents.append(_belt(trunk_x(k), y, N))
    for k, y in taps:
        ents.append({"name": "splitter", "x": trunk_x(k) + 1.0, "y": y + 1.5, "direction": N})
    return ents


def tap(k, y, x_end):
    """Branch entities (not the trunk): the first branch tile, undergrounds under trunks k+1.., belts to x_end-1.
    x_end is the row's west face X; the last branch belt is at X-1."""
    ents = [_belt(trunk_x(k) + 1, y, E)]
    x = trunk_x(k) + 1
    for j in range(k + 1, TRUNKS):
        ents.append(_ug(trunk_x(j) - 1, y, "input"))        # second free tile of the previous gap
        ents.append(_ug(trunk_x(j) + 1, y, "output"))       # first free tile after trunk j
        x = trunk_x(j) + 1
    # tiles between the last tile used and x_end - 1
    start = x + 1 if k < TRUNKS - 1 else x + 1
    for xx in range(start, x_end):
        ents.append(_belt(xx, y, E))
    return ents


def tiles(entities):
    out = {}
    for e in entities:
        w = 2 if e["name"] == "splitter" else 1
        x0 = int(e["x"] - w / 2) if w == 2 else int(e["x"] - 0.5)
        y0 = int(e["y"] - 0.5) if w == 2 else int(e["y"] - 0.5)
        for i in range(w):
            t = (x0 + i, y0)
            if t in out:
                raise ValueError(f"{e['name']} overlaps {out[t]} at {t}")
            out[t] = e["name"]
    return out
