"""
A* belt router with underground hops for the rocket-fuel line (scripts/build_fuel_line.py uses it).
Reads scripts/_fuelgrid.json (blocked-tile grid exported by _fuelgrid.py). Directions: 0 N, 4 E, 8 S, 12 W.
"""
import heapq
import json
import sys

DV = {0: (0, -1), 4: (1, 0), 8: (0, 1), 12: (-1, 0)}
MAXHOP = 7          # fast underground belt: exit up to 7 tiles away


def load():
    g = json.load(open("scripts/_fuelgrid.json"))
    x1 = g["x1"]
    rows = {int(y): r for y, r in g["rows"].items()}
    return x1, rows


def make_free(x1, rows, extra_blocked=(), extra_free=()):
    blocked = set(extra_blocked)
    freeset = set(extra_free)

    def free(x, y):
        if (x, y) in blocked:
            return False
        if (x, y) in freeset:
            return True
        r = rows.get(y)
        if r is None:
            return False
        i = x - x1
        return 0 <= i < len(r) and r[i] == "."
    return free


def route(free, start, start_d, goal, goal_d, max_nodes=2_000_000, must=()):
    """start: first belt tile (placed with incoming direction start_d). goal: tile that must be reached with incoming direction goal_d
    (the goal tile itself is NOT placed). Returns list of ('belt', x, y, d) / ('ug_in', x, y, d) / ('ug_out', x, y, d)."""
    def h(x, y):
        return abs(x - goal[0]) + abs(y - goal[1])
    pq = [(h(*start), 0, start[0], start[1], start_d)]
    best = {}
    prev = {}
    nodes = 0
    while pq:
        f, g, x, y, d = heapq.heappop(pq)
        if (x, y) == goal and d == goal_d:
            out = []
            key = (x, y, d)
            while key in prev:
                pk, act = prev[key]
                out.append(act)
                key = pk
            return list(reversed(out))
        if best.get((x, y, d), 1e18) < g:
            continue
        nodes += 1
        if nodes > max_nodes:
            return None
        if not free(x, y):
            continue
        # belt here, leaving in direction d2
        for d2 in DV:
            if (d2 - d) % 16 == 8:
                continue
            nx, ny = x + DV[d2][0], y + DV[d2][1]
            cost = g + 1 + (0.6 if d2 != d else 0)
            k = (nx, ny, d2)
            if cost < best.get(k, 1e18):
                best[k] = cost
                prev[k] = ((x, y, d), ("belt", x, y, d2))
                heapq.heappush(pq, (cost + h(nx, ny), cost, nx, ny, d2))
        # underground hop straight ahead (input must face d)
        dx, dy = DV[d]
        for k_ in (range(2, MAXHOP + 1) if (x, y) not in must else ()):
            ex, ey = x + dx * k_, y + dy * k_
            if any((x + dx * j, y + dy * j) in must for j in range(1, k_)):
                break
            if free(ex, ey) and (ex, ey) not in must:
                cost = g + 4 + k_ * 0.1
                nk = (ex + dx, ey + dy, d)
                if cost < best.get(nk, 1e18):
                    best[nk] = cost
                    prev[nk] = ((x, y, d), ("ug", x, y, ex, ey, d))
                    heapq.heappush(pq, (cost + h(ex + dx, ey + dy), cost, ex + dx, ey + dy, d))
    return None


def to_entities(actions, belt="fast-transport-belt", ug="fast-underground-belt"):
    ents = []
    for a in actions:
        if a[0] == "belt":
            ents.append({"name": belt, "x": a[1] + 0.5, "y": a[2] + 0.5, "direction": a[3]})
        else:
            _, x, y, ex, ey, d = a
            ents.append({"name": ug, "x": x + 0.5, "y": y + 0.5, "direction": d, "params": {"type": "input"}})
            ents.append({"name": ug, "x": ex + 0.5, "y": ey + 0.5, "direction": d, "params": {"type": "output"}})
    return ents


if __name__ == "__main__":
    x1, rows = load()
    free = make_free(x1, rows)
    for s in [(-253, -132), (-255, -132)]:
        print(s, [free(s[0] + dx, s[1] + dy) for dx in (0,) for dy in (-1, 0, 1)])
