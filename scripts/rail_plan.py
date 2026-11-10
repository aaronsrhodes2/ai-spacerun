"""
Plan and lay a rail line between two open rail ends, around water, buildings and existing rails.

Works on the 2-tile rail grid. Free cells come from the game (water, any player entity that is not a rail, existing rail cells, all inflated by one cell).
A* over (cell, heading, run) with a turn penalty and a minimum straight run before and after every corner (the corner pieces need room), then the corner
list is handed to bridge.factorio.rails.route, which turns it into straight and curved rail pieces from the game's own catalog.

    start  X Y H   the open end of the existing track (rail centre line coordinates are odd), H one of N E S W: the way the new track leaves it
    goal   X Y H   the open end to join: the new track arrives here moving in direction H (the existing piece continues the other way)

Usage: scripts/rail_plan.py --start X Y H --goal X Y H [--pad 40] [--min-run 5] [--apply]
"""
import argparse
import heapq
import json

import fx
from _game import tools

from bridge.factorio import rails
from bridge.factorio.planner import batches

DIRS = {"N": (0, -1), "E": (1, 0), "S": (0, 1), "W": (-1, 0)}
ORDER = ["N", "E", "S", "W"]


def blocked_cells(x1, y1, x2, y2):
    """Set of (i, j) rail cells (2x2 tiles, cell (i, j) covers tiles 2i..2i+1, 2j..2j+1) that cannot hold track."""
    i1, j1, i2, j2 = x1 // 2, y1 // 2, x2 // 2, y2 // 2
    code = (
        "local s=game.surfaces.nauvis local f=game.forces.player local I1,J1,I2,J2=%d,%d,%d,%d local rows={} "
        "local bad={} local soft={} for _,e in pairs(s.find_entities_filtered{area={{I1*2,J1*2},{I2*2+2,J2*2+2}},force=f}) do local n=e.name "
        "if not (n=='logistic-robot' or n=='construction-robot') then local b=e.bounding_box local g=(n=='substation' or n=='roboport' or n=='solar-panel' or n=='accumulator') "
        "for i=math.floor(b.left_top.x/2),math.floor((b.right_bottom.x-0.01)/2) do for j=math.floor(b.left_top.y/2),math.floor((b.right_bottom.y-0.01)/2) do if g then soft[i..','..j]=true else bad[i..','..j]=true end end end end end "
        "for j=J1,J2 do local r={} for i=I1,I2 do local c='0' if bad[i..','..j] then c='1' elseif soft[i..','..j] then c='2' else "
        "for _,o in pairs({{0,0},{1,0},{0,1},{1,1}}) do local t=s.get_tile(i*2+o[1],j*2+o[2]) if t.collides_with('player') or t.name:find('water') then c='1' end end end r[#r+1]=c end rows[#rows+1]=table.concat(r) end "
        "rcon.print(table.concat(rows,'/'))" % (i1, j1, i2, j2))
    raw = fx.lua(code).strip().split("/")
    blocked, soft = set(), set()
    for dj, row in enumerate(raw):
        for di, c in enumerate(row):
            if c == "1":
                blocked.add((i1 + di, j1 + dj))
            elif c == "2":
                soft.add((i1 + di, j1 + dj))
    return blocked, soft


def inflate(blocked, r=1):
    out = set()
    for (i, j) in blocked:
        for di in range(-r, r + 1):
            for dj in range(-r, r + 1):
                out.add((i + di, j + dj))
    return out


def astar(start, goal, blocked, box, min_run, turn_cost=25, soft=frozenset(), soft_cost=25):
    """start/goal = (i, j, dir). Returns the list of corner cells [(i, j, dir_out), ...]: path as (cell, dir) pairs at each turn."""
    (si, sj, sd), (gi, gj, gd) = start, goal
    cap = min_run
    i1, j1, i2, j2 = box
    sdir = ORDER.index(sd)
    gdir = ORDER.index(gd)
    h = lambda i, j: abs(i - gi) + abs(j - gj)
    first = (si, sj, sdir, 1)
    best = {first: 0}
    prev = {}
    pq = [(h(si, sj), 0, first)]
    while pq:
        f_, g, cur = heapq.heappop(pq)
        if best.get(cur, 1e18) < g:
            continue
        i, j, d, run = cur
        if (i, j) == (gi, gj) and d == gdir and run >= cap:
            path = [cur]
            while cur in prev:
                cur = prev[cur]
                path.append(cur)
            return path[::-1]
        for nd in range(4):
            if nd == (d + 2) % 4:
                continue
            if nd != d and run < cap:
                continue
            di, dj = DIRS[ORDER[nd]]
            ni, nj = i + di, j + dj
            if not (i1 <= ni <= i2 and j1 <= nj <= j2) or (ni, nj) in blocked:
                continue
            nrun = min(cap, run + 1) if nd == d else 1
            cost = g + 1 + (turn_cost if nd != d else 0) + (soft_cost if (ni, nj) in soft else 0)
            st = (ni, nj, nd, nrun)
            if cost < best.get(st, 1e18):
                best[st] = cost
                prev[st] = cur
                heapq.heappush(pq, (cost + h(ni, nj), cost, st))
    return None


def legs_from_path(path):
    legs = []
    for a, b in zip(path, path[1:]):
        if b[2] != a[2]:
            legs.append([ORDER[b[2]], (b[1] if ORDER[b[2]] in "EW" else b[0]) * 2 + 1])
    last = path[-1]
    return legs, last


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", nargs=3, required=True)
    ap.add_argument("--goal", nargs=3, required=True)
    ap.add_argument("--pad", type=int, default=60)
    ap.add_argument("--min-run", type=int, default=8)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sx, sy, sh = int(a.start[0]), int(a.start[1]), a.start[2]
    gx, gy, gh = int(a.goal[0]), int(a.goal[1]), a.goal[2]
    x1, x2 = min(sx, gx) - a.pad, max(sx, gx) + a.pad
    y1, y2 = min(sy, gy) - a.pad, max(sy, gy) + a.pad
    blocked, soft = set(), set()
    for yy in range(y1, y2 + 1, 120):                        # fetch in horizontal strips so one RCON reply stays small
        b_, s_ = blocked_cells(x1, yy, x2, min(yy + 119, y2))
        blocked |= b_
        soft |= s_
    box = (x1 // 2, y1 // 2, x2 // 2, y2 // 2)
    def cell(x, y, h, arriving):
        """Rail cell of the first new piece after the open end (leaving) or of the last new piece before it (arriving)."""
        dx, dy = DIRS[h]
        if arriving:                                   # the last piece lies behind the open end, against the way we travel
            x, y = x - dx, y - dy
        # across the heading the line is odd (cell = (c-1)//2); along it, the open end is even
        if h in "EW":
            i = (x - 1) // 2 if (h == "W" and not arriving) or (h == "E" and arriving) else x // 2
            if arriving:
                i = (x // 2) if h == "W" else ((x - 1) // 2)
            return i, (y - 1) // 2
        j = (y - 1) // 2 if (h == "N" and not arriving) or (h == "S" and arriving) else y // 2
        if arriving:
            j = (y // 2) if h == "N" else ((y - 1) // 2)
        return (x - 1) // 2, j
    s_i, s_j = cell(sx, sy, sh, False)
    g_i, g_j = cell(gx, gy, gh, True)
    start = (s_i, s_j, sh)
    goal = (g_i, g_j, gh)
    grown = inflate(blocked, 2)
    soft = inflate(soft, 1)
    for c in [(start[0] + k * DIRS[sh][0], start[1] + k * DIRS[sh][1]) for k in range(-1, a.min_run + 1)]:
        grown.discard(c)
    for c in [(goal[0] - k * DIRS[gh][0], goal[1] - k * DIRS[gh][1]) for k in range(-1, a.min_run + 1)]:
        grown.discard(c)
    path = astar(start, goal, grown, box, a.min_run, soft=soft)
    if not path:
        raise SystemExit("no route found (try a larger --pad or smaller --min-run)")
    legs, last = legs_from_path(path)
    print(f"{len(path)} cells, {len(legs)} turns; legs: {legs}")
    open_end = (sx, sy, rails.HEADING[sh])
    legs[-1] = legs[-1] + [gx if gh in "EW" else gy] if legs else legs
    pieces, end = rails.route(open_end, legs)
    print(f"{len(pieces)} rail pieces, ends at {end}")
    if not a.apply:
        return
    pts = ",".join("{%s,%s}" % (p[2][0], p[2][1]) for p in pieces)
    print(tools["save_game"]("before-rail-line"))
    print(fx.lua("local s=game.surfaces.nauvis local n=0 for _,p in pairs({%s}) do for _,c in pairs(s.find_entities_filtered{position=p,radius=5,type={'tree','cliff','simple-entity','item-entity','corpse'}}) do if c.force.name~='player' then c.destroy() n=n+1 end end for _,c in pairs(s.find_entities_filtered{position=p,radius=5,name={'substation','solar-panel','accumulator','roboport'},force='player'}) do c.destroy() n=n+1 end end rcon.print('cleared '..n..' pieces (natural and grid)')" % pts))
    ents = [rails.entity(p) for p in pieces]
    for part in batches(ents):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        if r.get("failed"):
            raise SystemExit(f"rail placement stopped: {json.dumps(r)[:1500]}")
    print("rail line laid:", len(ents), "pieces")


if __name__ == "__main__":
    main()
