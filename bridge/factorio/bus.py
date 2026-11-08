"""
The east base bus: eight trunk belts running SOUTH from the north end, one every 3 tiles, with two free
tiles beside each, plus a coal riser at x=96 running NORTH that feeds trunk 7's head.

    trunk k at x = BUS_X0 + 3k, from NORTH_Y (supplied from the north) down to SOUTH_Y
    riser  x = RISER_X: coal comes up from y=-56, turns west at y=-141 and drops into trunk 7
    tap(k, y, x_end)  splits trunk k at row y-1 and runs a branch EAST along row y to the tile just west of
                      x_end, under every later trunk and the riser (undergrounds: entrance on the second free
                      tile of a gap, exit on the first free tile after the trunk)

Order rule: a normal row takes belt B from a LOWER trunk than belt A; a flipped row takes A from a lower
trunk than B. Splitters then never land on another branch's tiles (the tests check every tile).
"""
N, E, S, W = 0, 4, 8, 12
BUS_X0 = 72
SPACING = 3
TRUNKS = 8
SOUTH_Y = -46
NORTH_Y = -139
RISER_X = 96
TRUNK_ITEMS = ["steel-plate", "iron-plate|copper-plate", "plastic-bar", "spare",
               "spare", "stone-brick", "sulfur", "coal"]


def trunk_x(k):
    return BUS_X0 + SPACING * k


def last_x():
    return trunk_x(TRUNKS - 1)


def _belt(x, y, d):
    return {"name": "transport-belt", "x": x + 0.5, "y": y + 0.5, "direction": d}


def _ug(x, y, kind):
    return {"name": "underground-belt", "x": x + 0.5, "y": y + 0.5, "direction": E, "params": {"type": kind}}


def splitter_tile(k, y):
    return (trunk_x(k), y - 1)


def trunk_entities(taps=()):
    """Trunks flowing south with a splitter replacing the belt at each tap's splitter tile, and the coal riser."""
    skip = {splitter_tile(k, y) for k, y in taps}
    ents = []
    for k in range(TRUNKS):
        top = NORTH_Y - 2 if k == TRUNKS - 1 else NORTH_Y
        for y in range(top, SOUTH_Y + 1):
            if (trunk_x(k), y) not in skip:
                ents.append(_belt(trunk_x(k), y, S))
    for y in range(-56, -141, -1):                       # riser, north-flowing
        ents.append(_belt(RISER_X, y, N))
    for xx in range(RISER_X, trunk_x(TRUNKS - 1), -1):   # west along y=-141 to x=94
        ents.append(_belt(xx, -141, W))
    for k, y in taps:
        ents.append({"name": "splitter", "x": trunk_x(k) + 1.0, "y": y - 0.5, "direction": S})
    return ents


def tap(k, y, x_end):
    """Branch entities (not the trunk): the first branch tile, undergrounds under trunks k+1.., belts to x_end-1.
    x_end is the row's west face X; the last branch belt is at X-1."""
    ents = [_belt(trunk_x(k) + 1, y, E)]
    x = trunk_x(k) + 1
    for j in list(range(k + 1, TRUNKS)) + [None]:
        jx = RISER_X if j is None else trunk_x(j)
        ents.append(_ug(jx - 1, y, "input"))                # second free tile of the previous gap
        ents.append(_ug(jx + 1, y, "output"))               # first free tile after trunk j (or the riser)
        x = jx + 1
    # tiles between the last tile used and x_end - 1
    start = x + 1 if k < TRUNKS - 1 else x + 1
    for xx in range(start, x_end):
        ents.append(_belt(xx, y, E))
    return ents


def _ug_w(x, y, kind):
    return {"name": "underground-belt", "x": x + 0.5, "y": y + 0.5, "direction": W, "params": {"type": kind}}


def give(k, y, x_from):
    """Branch flowing WEST along row y from tile x_from to trunk k, side-loading it from the east, so the items take
    the east (line 1) lane. Crosses the riser and trunks TRUNKS-1..k+1 by underground. Used by rows whose output
    belt flows west and which put their product back on the bus."""
    ents = []
    x = x_from
    for jx in [RISER_X] + [trunk_x(j) for j in range(TRUNKS - 1, k, -1)]:
        # belts up to the entrance tile (jx + 1), entrance, exit at jx - 1
        while x > jx + 1:
            ents.append(_belt(x, y, W))
            x -= 1
        ents.append(_ug_w(jx + 1, y, "input"))
        ents.append(_ug_w(jx - 1, y, "output"))
        x = jx - 2
    while x > trunk_x(k):
        ents.append(_belt(x, y, W))
        x -= 1
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
