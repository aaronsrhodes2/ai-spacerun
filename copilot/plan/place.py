"""Pointing with words (the Captain, 2026-11-13: a player with no mouse says "in the middle of the screen", "in the east
of the main base", "the upper right corner of my view"). A spoken place is a frame (the view, the base, the map, or
around the player) and a part of it (middle, a side, a corner). The frame's rectangle comes from the game; this module
only cuts it up. Pure functions.

A rectangle is (left, top, right, bottom) in tiles, right and bottom included. North is up: smaller y."""

# every way of saying a part -> (column, row) in a three by three grid; 0 is west / north, 2 is east / south
_COL = {"west": 0, "left": 0, "east": 2, "right": 2}
_ROW = {"north": 0, "top": 0, "upper": 0, "up": 0, "south": 2, "bottom": 2, "lower": 2, "down": 2}
_MIDDLE = {"middle", "centre", "center", "central", "mid"}
_NOISE = {"the", "of", "in", "at", "on", "to", "side", "part", "corner", "edge", "half", "area", "hand", "most", "-"}
FRAMES = ("view", "base", "map", "player")


class PlaceError(Exception):
    pass


def part_of(words):
    """(column, row) for words such as 'upper right', 'north-east', 'middle', 'bottom', 'the east side'. A side alone
    means the middle of that side: 'east' is the middle-east cell; 'top' is the top-middle cell."""
    col = row = None
    saw_middle = False
    for w in str(words).lower().replace("-", " ").replace("_", " ").split():
        if w in _NOISE:
            continue
        if w in _MIDDLE:
            saw_middle = True
        elif w in _COL:
            col = _COL[w]
        elif w in _ROW:
            row = _ROW[w]
        elif w.startswith("north") or w.startswith("south"):          # northeast, southwest written as one word
            row = _ROW[w[:5]]
            rest = w[5:]
            if rest in _COL:
                col = _COL[rest]
            elif rest:
                raise PlaceError("'%s' is not a part I know" % w)
        else:
            raise PlaceError("'%s' is not a part I know" % w, )
    if col is None and row is None and not saw_middle:
        raise PlaceError("say which part: middle, north, south, east, west, or a corner such as upper right")
    return (1 if col is None else col, 1 if row is None else row)


def cut(rect, col, row):
    """The cell (col, row) of a rectangle cut three by three. Cells share no tiles and cover the whole rectangle."""
    left, top, right, bottom = rect
    if right < left or bottom < top:
        raise PlaceError("the frame is empty")
    w, h = right - left + 1, bottom - top + 1
    xs = [left, left + w // 3, left + w - w // 3, right + 1] if w >= 3 else [left, left, right + 1, right + 1]
    ys = [top, top + h // 3, top + h - h // 3, bottom + 1] if h >= 3 else [top, top, bottom + 1, bottom + 1]
    x0, x1 = xs[col], xs[col + 1] - 1
    y0, y1 = ys[row], ys[row + 1] - 1
    if x1 < x0:                                        # a frame under three tiles wide: every cell is the whole width
        x0, x1 = left, right
    if y1 < y0:
        y0, y1 = top, bottom
    return (x0, y0, x1, y1)


def centre(rect):
    return ((rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2)


def around(x, y, radius):
    return (int(x) - radius, int(y) - radius, int(x) + radius, int(y) + radius)


def locate(frames, frame, part="middle"):
    """frames: {"view": rect, "base": rect, "map": rect, "player": rect} as the game gave them (any may be missing).
    Returns the rectangle meant, its centre and its size."""
    if frame not in FRAMES:
        raise PlaceError("the frame must be one of: view (what is on screen), base, map, player (around the player)")
    rect = frames.get(frame)
    if not rect:
        raise PlaceError("the game gave no rectangle for '%s'" % frame)
    col, row = part_of(part)
    r = cut(tuple(rect), col, row)
    cx, cy = centre(r)
    return {"frame": frame, "part": part, "from_x": r[0], "from_y": r[1], "to_x": r[2], "to_y": r[3], "centre_x": cx, "centre_y": cy,
            "width": r[2] - r[0] + 1, "height": r[3] - r[1] + 1}


def ring(rect, depth):
    """The four strips just outside a rectangle, `depth` tiles deep: what 'go round the edge of the map' should reveal.
    Returned in walking order: north, east, south, west."""
    left, top, right, bottom = rect
    return [(left - depth, top - depth, right + depth, top - 1), (right + 1, top, right + depth, bottom),
            (left - depth, bottom + 1, right + depth, bottom + depth), (left - depth, top, left - 1, bottom)]
