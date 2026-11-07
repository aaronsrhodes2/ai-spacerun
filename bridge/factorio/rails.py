"""
Rail routing from the game's own rail geometry.

snapshots/rail-catalog.json (built by scripts/rail_catalog.py) lists, for every rail piece
and direction the game accepts, the two open ends of the piece relative to its position:
(dx, dy, dir), where dir is the way the track leaves the piece at that end (16-way, 0 = N,
4 = E, 8 = S, 12 = W; rails use the even values).

A piece continues a track when one of its ends sits at the track's open end and faces the
other way (dir + 8). That is the whole connection rule, so nothing here knows what a curve
looks like. Pieces sit on the 2-tile rail grid (even coordinates).

    state   (x, y, d)      an open end: where the next piece must join, and the way it points
    piece   (name, dir, position)  a rail entity to place

Long runs are straight rails. Corners are found by breadth-first search over the catalog from
an open end to a target line, so a turn costs a handful of pieces whatever its shape.
"""

import json
from collections import deque
from pathlib import Path

_CATALOG_PATH = Path(__file__).resolve().parent.parent.parent / "snapshots" / "rail-catalog.json"
_catalog = None


def catalog():
    global _catalog
    if _catalog is None:
        raw = json.loads(_CATALOG_PATH.read_text())
        _catalog = {}
        seen = set()
        for name, dirs in raw.items():
            for _, v in dirs.items():
                key = (name, v["dir"])
                if key in seen:
                    continue
                seen.add(key)
                _catalog[key] = [tuple(e) for e in v["ends"]]
    return _catalog


def opposite(d):
    return (d + 8) % 16


def _even(v):
    return abs(v - round(v)) < 1e-9 and round(v) % 2 == 0


def continuations(state, allowed=None):
    """Every piece that can be joined to the open end `state`, as
    (name, dir, (px, py), new_state) with new_state the piece's other end.
    `allowed` optionally limits the piece names."""
    x, y, d = state
    want = opposite(d)
    out = []
    for (name, pdir), ends in catalog().items():
        if allowed is not None and name not in allowed:
            continue
        for i, (ex, ey, ed) in enumerate(ends):
            if ed != want:
                continue
            px, py = x - ex, y - ey
            if not (_even(px) and _even(py)):
                continue
            ox, oy, od = ends[1 - i]
            out.append((name, pdir, (px, py), (px + ox, py + oy, od)))
    return out


def straight(state):
    """The straight-rail that continues the track from `state`, if the heading is straight."""
    for name, pdir, pos, new in continuations(state):
        if name == "straight-rail" and (new[2] == state[2]):
            return name, pdir, pos, new
    return None


def find_turn(state, done, max_pieces=14, allowed=None):
    """Shortest piece sequence from open end `state` to any open end for which `done(end)` is true.
    Returns [(name, dir, pos), ...] and the final open end, or raises."""
    start = state
    queue = deque([(start, [])])
    seen = {start}
    while queue:
        cur, path = queue.popleft()
        if path and done(cur):
            return path, cur
        if len(path) >= max_pieces:
            continue
        for name, pdir, pos, new in continuations(cur, allowed):
            if new in seen:
                continue
            seen.add(new)
            queue.append((new, path + [(name, pdir, pos)]))
    raise ValueError(f"no turn found from {state} within {max_pieces} pieces")


_CURVES = ("curved-rail-a", "curved-rail-b")


def entity(piece):
    name, pdir, (px, py) = piece
    return {"name": name, "x": float(px), "y": float(py), "direction": pdir}


HEADING = {"N": 0, "E": 4, "S": 8, "W": 12}
_STEP = {0: (0, -1), 4: (1, 0), 8: (0, 1), 12: (-1, 0)}


def run_to(state, target, axis_heading):
    """Straight rails from `state` until the open end reaches `target`, a coordinate along the
    heading's axis. Returns (pieces, new_state)."""
    pieces = []
    cur = state
    dx, dy = _STEP[axis_heading]
    guard = 0
    while True:
        along = cur[0] if dx else cur[1]
        sign = dx or dy
        if (target - along) * sign <= 0:
            return pieces, cur
        nxt = straight(cur)
        if nxt is None:
            raise ValueError(f"no straight rail continues {cur}")
        name, pdir, pos, new = nxt
        pieces.append((name, pdir, pos))
        cur = new
        guard += 1
        if guard > 5000:
            raise ValueError("run_to did not converge")


def _axis(d):
    return "x" if d in (4, 12) else "y"


def route(start, legs):
    """Lay a track from the open end `start` through `legs`.

    Each leg is (heading, line) or (heading, line, end_along): turn onto `heading` so that the
    new track lies on `line` (its y for E/W, its x for N/S), then, if given, run on until the
    open end passes `end_along`. Corners are the compact four-curve turn; the straight run
    before it is sized so the turned track lands exactly on `line`. Raises when `line` has the
    wrong parity (rails sit on a 2-tile grid; move it by one) or lies behind the track.

    Returns (pieces, final_open_end).
    """
    pieces = []
    cur = start
    for leg in legs:
        heading, line = leg[0], leg[1]
        end_along = leg[2] if len(leg) > 2 else None
        d = HEADING[heading]
        if d == cur[2]:
            raise ValueError("a leg must change heading")
        # the turn's displacement is the same wherever it starts on the grid, so measure it here
        turn, end = find_turn(cur, lambda s, dd=d: s[2] == dd, max_pieces=4, allowed=_CURVES)
        # position the turn so its end lands on `line`: run straight until start-of-turn coordinate
        if _axis(cur[2]) == "y":
            target = cur[1] + (line - end[1])
        else:
            target = cur[0] + (line - end[0])
        step_sign = -1 if cur[2] in (0, 12) else 1
        along = cur[1] if _axis(cur[2]) == "y" else cur[0]
        run = (target - along) * step_sign
        if run < 0:
            raise ValueError(f"line {line} is behind the track at {cur}: need more room to turn {heading}")
        if run % 2:
            raise ValueError(f"line {line} has the wrong parity from {cur}: move it by one tile")
        more, cur = run_to(cur, target, cur[2]) if run else ([], cur)
        pieces.extend(more)
        turn, end = find_turn(cur, lambda s, dd=d: s[2] == dd, max_pieces=4, allowed=_CURVES)
        pieces.extend(turn)
        cur = end
        if end_along is not None:
            more, cur = run_to(cur, end_along, d)
            pieces.extend(more)
    return pieces, cur
