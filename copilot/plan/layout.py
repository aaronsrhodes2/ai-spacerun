"""Layouts as data, checked before the game ever sees them. A layout is a list of pieces on whole tiles; every piece claims
its tiles, and two claims on one tile stop the build with both names in the error. Design once facing north, then turn or
mirror the whole layout in code.

Coordinates: x grows east, y grows south (north is up, as in the game). A piece is placed by its top-left tile and its
size in tiles. Directions are the game's sixteen-step compass: 0 north, 4 east, 8 south, 12 west.
An inserter's direction is the side it PICKS UP from; it drops on the opposite side."""

N, E, S, W = 0, 4, 8, 12
STEP = {N: (0, -1), E: (1, 0), S: (0, 1), W: (-1, 0)}
NAME = {N: "north", E: "east", S: "south", W: "west"}


class LayoutError(Exception):
    """A layout that cannot be built, with a sentence a model can act on."""


def opposite(d):
    return (d + 8) % 16


def turn_right(d, quarters=1):
    return (d + 4 * quarters) % 16


class Layout:
    def __init__(self):
        self.pieces = []            # {"name", "x", "y", "w", "h", "direction", ...extra}
        self.taken = {}             # (x, y) -> index of the piece on that tile

    def put(self, name, x, y, w=1, h=1, direction=N, **extra):
        """Place a piece by its top-left tile. Refused if any of its tiles is taken."""
        x, y, w, h = int(x), int(y), int(w), int(h)
        if w < 1 or h < 1:
            raise LayoutError("'%s' must be at least one tile wide and high" % name)
        if direction not in STEP:
            raise LayoutError("direction must be 0 (north), 4 (east), 8 (south) or 12 (west), not %r" % (direction,))
        for tx in range(x, x + w):
            for ty in range(y, y + h):
                if (tx, ty) in self.taken:
                    other = self.pieces[self.taken[(tx, ty)]]
                    raise LayoutError("'%s' at %d,%d overlaps '%s' on tile %d,%d" % (name, x, y, other["name"], tx, ty))
        piece = dict(extra, name=name, x=x, y=y, w=w, h=h, direction=direction)
        self.pieces.append(piece)
        for tx in range(x, x + w):
            for ty in range(y, y + h):
                self.taken[(tx, ty)] = len(self.pieces) - 1
        return piece

    def free(self, x, y, w=1, h=1):
        return all((tx, ty) not in self.taken for tx in range(x, x + w) for ty in range(y, y + h))

    def at(self, x, y):
        i = self.taken.get((x, y))
        return None if i is None else self.pieces[i]

    def bounds(self):
        """(left, top, right, bottom), inclusive tiles; None for an empty layout."""
        if not self.pieces:
            return None
        return (min(p["x"] for p in self.pieces), min(p["y"] for p in self.pieces),
                max(p["x"] + p["w"] - 1 for p in self.pieces), max(p["y"] + p["h"] - 1 for p in self.pieces))

    def size(self):
        b = self.bounds()
        return (0, 0) if b is None else (b[2] - b[0] + 1, b[3] - b[1] + 1)

    def _rebuilt(self, change):
        out = Layout()
        for p in self.pieces:
            q = change(dict(p))
            extra = {k: v for k, v in q.items() if k not in ("name", "x", "y", "w", "h", "direction")}
            out.put(q["name"], q["x"], q["y"], q["w"], q["h"], q["direction"], **extra)
        return out

    def moved(self, dx, dy):
        def change(p):
            p["x"] += dx
            p["y"] += dy
            return p
        return self._rebuilt(change)

    def turned(self, quarters=1):
        """The layout turned clockwise by quarter turns about the origin; sizes and directions turn with it."""
        def once(p):
            p["x"], p["y"], p["w"], p["h"] = -(p["y"] + p["h"] - 1), p["x"], p["h"], p["w"]
            p["direction"] = turn_right(p["direction"])
            return p

        def change(p):
            for _ in range(quarters % 4):
                p = once(p)
            return p
        return self._rebuilt(change)

    def mirrored(self):
        """The layout flipped left to right about the origin; east and west swap."""
        def change(p):
            p["x"] = -(p["x"] + p["w"] - 1)
            if p["direction"] in (E, W):
                p["direction"] = opposite(p["direction"])
            return p
        return self._rebuilt(change)

    def at_origin(self):
        """The same layout moved so its top-left corner is tile 0,0."""
        b = self.bounds()
        return self if b is None else self.moved(-b[0], -b[1])

    def add(self, other, dx=0, dy=0):
        """Put every piece of another layout into this one, moved by dx,dy. Overlaps are refused."""
        for p in other.pieces:
            extra = {k: v for k, v in p.items() if k not in ("name", "x", "y", "w", "h", "direction")}
            self.put(p["name"], p["x"] + dx, p["y"] + dy, p["w"], p["h"], p["direction"], **extra)
        return self

    def entities(self):
        """What the game's build call wants: each piece by its centre, with direction and any extras (recipe, filter...)."""
        out = []
        for p in self.pieces:
            e = {k: v for k, v in p.items() if k not in ("x", "y", "w", "h")}
            e["x"] = p["x"] + p["w"] / 2
            e["y"] = p["y"] + p["h"] / 2
            out.append(e)
        return out

    def count(self):
        c = {}
        for p in self.pieces:
            c[p["name"]] = c.get(p["name"], 0) + 1
        return c

    def picture(self, chars=None):
        """A small text picture for checking a layout by eye: first letter of each piece, '.' for empty."""
        b = self.bounds()
        if b is None:
            return ""
        rows = []
        for y in range(b[1], b[3] + 1):
            row = []
            for x in range(b[0], b[2] + 1):
                p = self.at(x, y)
                row.append("." if p is None else (chars or {}).get(p["name"], p["name"][0]))
            rows.append("".join(row))
        return "\n".join(rows)
