"""
Pure planning code for `scripts/fx.py compact` (no game connection, unit-tested).

A factory area is compacted by deleting whole empty tile columns and rows (a column is empty when no entity footprint covers it anywhere inside
the area) and shifting everything beyond them. Nothing is rotated or re-routed, so belts, pipes and wires keep their shape; only the gaps between
blocks shrink. `keep` leaves that many empty tiles in every gap so blocks do not fuse into a wall.

Footprints are tile rectangles (x1, y1, x2, y2), inclusive.
"""
from bisect import bisect_left


def occupied(footprints, axis, passthrough=None):
    """Set of tile coordinates (axis 0 = x, 1 = y) covered by at least one footprint.
    passthrough[i] = (px, py): a straight belt that runs ACROSS the gap does not block deleting that column (px) / row (py); the
    deleted tile of such a belt is simply removed, which shortens the belt line without cutting it."""
    out = set()
    for i, fp in enumerate(footprints):
        if passthrough is not None and passthrough[i][axis]:
            continue
        lo, hi = (fp[0], fp[2]) if axis == 0 else (fp[1], fp[3])
        out.update(range(lo, hi + 1))
    return out


def empty_runs(occ, lo, hi):
    """Runs (start, end) inclusive of tile coordinates in [lo, hi] that are not occupied."""
    runs, start = [], None
    for c in range(lo, hi + 1):
        if c in occ:
            if start is not None:
                runs.append((start, c - 1))
                start = None
        elif start is None:
            start = c
    if start is not None:
        runs.append((start, hi))
    return runs


def removable(runs, lo, hi, keep=1):
    """Coordinates to delete: from every empty run strictly between occupied tiles keep `keep` tiles and delete the rest.
    Runs touching the area edge are left alone (the edge is not a gap between two blocks)."""
    out = []
    for a, b in runs:
        if a == lo or b == hi:
            continue
        length = b - a + 1
        n = max(0, length - keep)
        out.extend(range(b - n + 1, b + 1))
    return out


def shift_of(coord, removed_sorted):
    """How far a tile at `coord` moves toward lower coordinates (number of deleted tiles below it)."""
    return bisect_left(removed_sorted, coord)


def plan(footprints, area, keep=1, passthrough=None):
    """footprints: list of (x1,y1,x2,y2). area: (x1,y1,x2,y2) tiles inclusive. passthrough: optional list of (px, py) flags parallel to
    footprints (see occupied). Returns dict with the deleted columns/rows, the new size and `destroy` = indices of pass-through belts
    that sit in a deleted column/row (they are removed, everything else moves)."""
    ax1, ay1, ax2, ay2 = area
    xs = removable(empty_runs(occupied(footprints, 0, passthrough), ax1, ax2), ax1, ax2, keep)
    ys = removable(empty_runs(occupied(footprints, 1, passthrough), ay1, ay2), ay1, ay2, keep)
    xset, yset = set(xs), set(ys)
    destroy = []
    if passthrough is not None:
        for i, fp in enumerate(footprints):
            if (passthrough[i][0] and fp[0] in xset) or (passthrough[i][1] and fp[1] in yset):
                destroy.append(i)
    return {"destroy": destroy,
        "xs": sorted(xs), "ys": sorted(ys),
        "width_before": ax2 - ax1 + 1, "height_before": ay2 - ay1 + 1,
        "width_after": ax2 - ax1 + 1 - len(xs), "height_after": ay2 - ay1 + 1 - len(ys),
    }


def moves(items, xs, ys, skip=()):
    """items: list of (key, x1, y1) with the footprint's top-left tile. Returns [(key, dx, dy)] for entities that move (dx, dy <= 0),
    ordered so that an entity moves before anything that would land on its old tiles (ascending x + y). `skip` = indices not to move."""
    out = []
    skip = set(skip)
    for idx, (key, x1, y1) in enumerate(items):
        if idx in skip:
            continue
        dx, dy = -shift_of(x1, xs), -shift_of(y1, ys)
        if dx or dy:
            out.append((x1 + y1, key, dx, dy))
    out.sort(key=lambda t: t[0])
    return [(k, dx, dy) for _, k, dx, dy in out]


def fits_after(footprints, xs, ys, skip=()):
    """Check that no two footprints overlap after the shifts (a sanity check on the plan itself)."""
    seen = {}
    skip = set(skip)
    for i, (x1, y1, x2, y2) in enumerate(footprints):
        if i in skip:
            continue
        dx, dy = shift_of(x1, xs), shift_of(y1, ys)
        for x in range(x1 - dx, x2 - dx + 1):
            for y in range(y1 - dy, y2 - dy + 1):
                if (x, y) in seen and seen[(x, y)] != i:
                    return False
                seen[(x, y)] = i
    return True
