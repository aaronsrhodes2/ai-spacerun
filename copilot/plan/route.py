"""Routes for belts and pipes from one tile to another around whatever stands in the way. Pure search over a set of
blocked tiles, which the caller reads from the game. The answer is a list of pieces ready for a Layout.

Belts: a belt tile points at the next tile of the route. Where the way is blocked, the route dives under with a pair
of underground belts. The game's rules for those are kept: the tile before the entrance and the tile after the exit lie
in the same straight line as the dive, so nothing is side-loaded onto an entrance and the exit feeds straight ahead.

Pipes: a pipe joins every pipe next to it, wanted or not. Tiles beside foreign pipes can be given as `avoid` so a new
line does not merge with an old one by accident. Underground pipes only connect at their two ends.

Directions are the game's: 0 north, 4 east, 8 south, 12 west."""
import heapq

from .layout import STEP, LayoutError, opposite

DIRS = (0, 4, 8, 12)
TURN_COST = 0.01            # among routes of equal length, prefer the one with fewer corners
UNDER_COST = 1.5            # an underground pair costs more than plain belt, so it is used only where needed
UNDER_TILE = 0.05           # and a short dive beats a long one over the same ground


class RouteError(LayoutError):
    pass


def _step(pos, d, n=1):
    dx, dy = STEP[d]
    return (pos[0] + dx * n, pos[1] + dy * n)


def _inside(pos, bounds):
    return bounds is None or (bounds[0] <= pos[0] <= bounds[2] and bounds[1] <= pos[1] <= bounds[3])


def _auto_bounds(start, goal, margin):
    return (min(start[0], goal[0]) - margin, min(start[1], goal[1]) - margin, max(start[0], goal[0]) + margin, max(start[1], goal[1]) + margin)


def _search(start, goal, blocked, bounds, max_gap, start_direction, limit):
    """Shortest path as a list of moves: ('step', pos, dir) or ('under', exit_pos, dir, entrance_pos).

    State: (position, direction we arrived in, just_exited). The rules for an underground pair, the same for belts
    and pipes: the entrance is reached moving in the dive's direction (or is the start), the tile after the exit lies
    straight ahead, and an exit cannot be the next pair's entrance."""
    if start in blocked:
        raise RouteError("the start tile %d,%d is not free" % start)
    if goal in blocked:
        raise RouteError("the end tile %d,%d is not free" % goal)
    first = (start, start_direction, False)
    best = {first: 0.0}
    came = {}
    heap = [(0.0, 0, first)]
    n = 0
    done = None
    while heap:
        _, _, state = heapq.heappop(heap)
        cost = best[state]
        pos, arrived, exited = state
        if pos == goal:
            done = state
            break
        n += 1
        if n > limit:
            raise RouteError("no route found within the search limit; give a smaller area or free some tiles")
        for d in DIRS:
            if arrived is not None and d == opposite(arrived):
                continue                                        # no doubling back
            if exited and d != arrived:
                continue                                        # straight ahead out of an exit
            turn = TURN_COST if (arrived is not None and d != arrived) else 0.0
            nxt = _step(pos, d)
            if nxt not in blocked and _inside(nxt, bounds):
                s2 = (nxt, d, False)
                c2 = cost + 1 + turn
                if c2 < best.get(s2, 1e18):
                    best[s2] = c2
                    came[s2] = (state, ("step", nxt, d))
                    n += 1
                    heapq.heappush(heap, (c2 + abs(nxt[0] - goal[0]) + abs(nxt[1] - goal[1]), n, s2))
            if max_gap > 0 and not exited and (arrived is None or arrived == d):
                for gap in range(1, max_gap + 1):
                    out = _step(pos, d, gap + 1)
                    if not _inside(out, bounds):
                        break
                    if out in blocked:
                        continue
                    if all(_step(pos, d, k) not in blocked for k in range(1, gap + 1)):
                        continue                                # nothing in the way: plain pieces are better
                    s2 = (out, d, True)
                    c2 = cost + gap + 1 + UNDER_COST + UNDER_TILE * gap
                    if c2 < best.get(s2, 1e18):
                        best[s2] = c2
                        came[s2] = (state, ("under", out, d, pos))
                        n += 1
                        heapq.heappush(heap, (c2 + abs(out[0] - goal[0]) + abs(out[1] - goal[1]), n, s2))
    if done is None:
        raise RouteError("there is no free way from %d,%d to %d,%d" % (start + goal))
    moves = []
    s = done
    while s in came:
        s, move = came[s]
        moves.append(move)
    moves.reverse()
    return moves


def _length(moves):
    return 1 + sum(1 if m[0] == "step" else abs(m[1][0] - m[3][0]) + abs(m[1][1] - m[3][1]) for m in moves)


def _assemble(start, goal, moves, plain, entrance, exit_piece, last_direction):
    """Turn moves into pieces. `plain(pos, d)`, `entrance(pos, d)` and `exit_piece(pos, d)` build one piece each."""
    pieces, pos, on_exit, under, d = [], start, False, 0, None
    for m in moves:
        d = m[2]
        if m[0] == "step":
            if not on_exit:
                pieces.append(plain(pos, d))
            pos, on_exit = m[1], False
        else:
            pieces.append(entrance(pos, d))
            pos, on_exit = m[1], True
            pieces.append(exit_piece(pos, d))
            under += 1
    if not on_exit:
        pieces.append(plain(goal, last_direction if last_direction is not None else d))
    return {"pieces": pieces, "length": _length(moves), "undergrounds": under}


def belt(start, goal, blocked=(), belt_name="transport-belt", underground_name="underground-belt", max_gap=4,
         end_direction=None, start_direction=None, bounds=None, margin=12, limit=200000):
    """Belt pieces from `start` to `goal` (both tiles included). max_gap is how many tiles an underground pair may pass
    under (4 for the basic belt, 6 fast, 8 express; look it up). end_direction fixes which way the last tile faces, to
    feed something beside the goal; without it the last tile keeps the direction it was reached in. start_direction
    says which way the belt was already moving when it reached the start (so the route does not double back).
    Returns {"pieces": [...], "length": tiles covered, "undergrounds": pairs used}."""
    start, goal = tuple(start), tuple(goal)
    blocked = set(map(tuple, blocked))
    if start == goal:
        d = end_direction if end_direction is not None else (start_direction or 0)
        if start in blocked:
            raise RouteError("the start tile %d,%d is not free" % start)
        return {"pieces": [{"name": belt_name, "x": start[0], "y": start[1], "direction": d}], "length": 1, "undergrounds": 0}
    moves = _search(start, goal, blocked, bounds or _auto_bounds(start, goal, margin), max_gap, start_direction, limit)
    return _assemble(start, goal, moves,
                     lambda pos, d: {"name": belt_name, "x": pos[0], "y": pos[1], "direction": d},
                     lambda pos, d: {"name": underground_name, "x": pos[0], "y": pos[1], "direction": d, "type": "input"},
                     lambda pos, d: {"name": underground_name, "x": pos[0], "y": pos[1], "direction": d, "type": "output"},
                     end_direction)


def pipe(start, goal, blocked=(), avoid=(), pipe_name="pipe", underground_name="pipe-to-ground", max_gap=9, bounds=None, margin=12, limit=200000):
    """Pipe pieces from `start` to `goal`. `avoid` are tiles that are free but must not hold a pipe (next to another
    pipe line, for instance); an underground pair may still pass under them. max_gap is how many tiles a pair passes
    under (9 for the basic pipe-to-ground: look it up). A pipe-to-ground's direction is its OPEN end: the entrance
    opens back toward the pipe before it, the exit opens forward."""
    start, goal = tuple(start), tuple(goal)
    hard = set(map(tuple, blocked)) | set(map(tuple, avoid))
    if start == goal:
        if start in hard:
            raise RouteError("the start tile %d,%d is not free" % start)
        return {"pieces": [{"name": pipe_name, "x": start[0], "y": start[1], "direction": 0}], "length": 1, "undergrounds": 0}
    moves = _search(start, goal, hard, bounds or _auto_bounds(start, goal, margin), max_gap, None, limit)
    return _assemble(start, goal, moves,
                     lambda pos, d: {"name": pipe_name, "x": pos[0], "y": pos[1], "direction": 0},
                     lambda pos, d: {"name": underground_name, "x": pos[0], "y": pos[1], "direction": opposite(d)},
                     lambda pos, d: {"name": underground_name, "x": pos[0], "y": pos[1], "direction": d},
                     0)


def beside_pipes(pipe_tiles):
    """The tiles next to existing pipes: pass them as `avoid` so a new pipe line does not join an old one."""
    out = set()
    for t in pipe_tiles:
        for d in DIRS:
            out.add(_step(tuple(t), d))
    return out - set(map(tuple, pipe_tiles))
