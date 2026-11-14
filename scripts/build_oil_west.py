"""
West oil field for Nauvis (2026-11-14): the two tapped fields are worn down to 20-45% a well (about 173 crude a second in all) and the nine
refineries sit idle for lack of crude, so plastic, advanced circuits and with them production and chemical science starve.

  15 fresh wells at x -716..-678, y -425..-383 (2,905% in all) get pumpjacks, substations on the free points of the 16-pitch lattice, a pipe net,
  and one trunk of underground pipe to the refinery's crude network (the pipe at -322.5,-301.5), with a pump halfway and a pump at the join
  (a pipeline may not span more than 320 tiles).

Built 2026-11-14. Two things the plan did not know, fixed by hand afterwards (a re-lay must repeat them):
  - tile (-566,-378) on the trunk refuses a pipe (a cliff's edge): the pair before it ends at y -379.5, the next pair runs -378.5 to -368.5,
    plain pipes at -367.5 and -366.5;
  - the well at (-696.5,-407.5) sits on the lattice point, so its substation stands at (-700,-410).
The two ends of an underground pipe pair may be at most 10 tiles apart (11 does not connect, and nothing warns).

Usage: scripts/build_oil_west.py GRID.json [--apply]      (GRID.json comes from scripts/_oilwest_map.py; dry run without --apply)
"""
import heapq
import json
import sys
from collections import deque

from _game import tools

from bridge.factorio.planner import batches

Q = {"quality": "epic"}
OUT = {"S": (-1, 2), "E": (2, 1), "W": (-2, -1), "N": (1, -2)}
DIRNUM = {"N": 0, "E": 4, "S": 8, "W": 12}
WELLS = [(-704.5, -424.5), (-690.5, -414.5), (-715.5, -413.5), (-709.5, -412.5), (-696.5, -407.5), (-678.5, -404.5), (-715.5, -402.5),
         (-704.5, -402.5), (-708.5, -401.5), (-708.5, -398.5), (-687.5, -398.5), (-708.5, -394.5), (-684.5, -395.5), (-708.5, -383.5), (-705.5, -383.5)]
LATTICE = [(x, y) for x in (-680, -696, -712) for y in (-392, -408, -424)]
JOIN_PUMP = (-324.0, -301.5)          # covers tiles -325 and -324 on row -302, pumps east into the existing pipe on tile (-323,-302)
GOAL = (-326, -302)                   # the trunk's last tile, the join pump's inlet
SEED = (-676, -400)                   # where the field net meets the trunk


def tile(x, y):
    return (int(x // 1), int(y // 1))


def load(path):
    g = json.load(open(path))
    rows, x0, y0 = g["rows"], g["x0"], g["y0"]
    hard, fluid = set(), set()
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch in "#F~co":
                hard.add((x0 + i, y0 + j))
            if ch == "F":
                fluid.add((x0 + i, y0 + j))
    near = set()
    for (x, y) in fluid:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                near.add((x + dx, y + dy))
    bounds = (x0, y0, x0 + len(rows[0]) - 1, y0 + len(rows) - 1)
    return hard, near, bounds


def astar(start, goal, blocked, bounds):
    """Tile path with a turn penalty, so the runs are long and straight enough for underground pipe."""
    x0, y0, x1, y1 = bounds
    best = {}
    pq = [(0, 0, start, (0, 0), None)]
    prev = {}
    while pq:
        f, g, c, d, p = heapq.heappop(pq)
        if (c, d) in best:
            continue
        best[(c, d)] = g
        prev[(c, d)] = p
        if c == goal:
            path = []
            k = (c, d)
            while k is not None:
                path.append(k[0])
                k = prev[k]
            return path[::-1]
        for nd in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (c[0] + nd[0], c[1] + nd[1])
            if n in blocked or not (x0 <= n[0] <= x1 and y0 <= n[1] <= y1):
                continue
            ng = g + 1 + (6 if d != (0, 0) and nd != d else 0)
            if (n, nd) in best:
                continue
            h = abs(n[0] - goal[0]) + abs(n[1] - goal[1])
            heapq.heappush(pq, (ng + h, ng, n, nd, (c, d)))
    return None


def trunk_entities(path, pump_at):
    """Plain pipe on the ends and corners, underground pairs (entry, up to 9 hidden, exit: the two ends at most 10 tiles apart) on straight runs. pump_at: index of the first of the two tiles a pump takes."""
    ents = []
    n = len(path)
    dirs = [(path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1]) for i in range(n - 1)]
    fwd = {(1, 0): 4, (-1, 0): 12, (0, 1): 8, (0, -1): 0}
    back = {(1, 0): 12, (-1, 0): 4, (0, 1): 0, (0, -1): 8}

    def straight(i):
        return 0 < i < n - 1 and dirs[i - 1] == dirs[i] and (pump_at is None or i not in (pump_at, pump_at + 1))

    def pipe(i):
        ents.append({"name": "pipe", "x": path[i][0] + 0.5, "y": path[i][1] + 0.5, "params": Q})

    i = 0
    while i < n:
        if pump_at is not None and i == pump_at:
            a, b = path[i], path[i + 1]
            ents.append({"name": "pump", "x": (a[0] + b[0]) / 2 + 0.5, "y": (a[1] + b[1]) / 2 + 0.5, "direction": fwd[dirs[i]], "params": Q})
            i += 2
            continue
        if not straight(i):
            pipe(i)
            i += 1
            continue
        j = i
        while j + 1 < n and straight(j + 1) and j - i < 10:
            j += 1
        if j == i:
            pipe(i)
        else:
            d = dirs[i]
            ents.append({"name": "pipe-to-ground", "x": path[i][0] + 0.5, "y": path[i][1] + 0.5, "direction": back[d], "params": Q})
            ents.append({"name": "pipe-to-ground", "x": path[j][0] + 0.5, "y": path[j][1] + 0.5, "direction": fwd[d], "params": Q})
        i = j + 1
    return ents


def plan(grid):
    hard, near, bounds = load(grid)
    foot = set()
    for (x, y) in WELLS:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                foot.add(tile(x + dx, y + dy))
    ents = []
    subs = set()
    for (x, y) in LATTICE:
        t = {(x - 1, y - 1), (x, y - 1), (x - 1, y), (x, y)}
        if t & (foot | hard):
            print("lattice point skipped (occupied):", x, y)
            continue
        subs |= t
        ents.append({"name": "substation", "x": x, "y": y, "params": Q})
    # the join pump's two tiles and the goal lie beside the old pumpjack: allowed by hand
    pump_tiles = {(-325, -302), (-324, -302)}
    blocked = (hard | near | foot | subs | pump_tiles) - {GOAL}
    # pumpjacks: an output tile that is free
    jacks = []
    outs = set()
    for (x, y) in WELLS:
        pick = None
        for d in ("E", "S", "N", "W"):
            ox, oy = OUT[d]
            t = tile(x + ox, y + oy)
            if t in blocked:
                continue
            pick = (d, t)
            break
        if not pick:
            print("no free output for the well at", x, y)
            continue
        jacks.append((x, y, pick[0], pick[1]))
        outs.add(pick[1])
        ents.append({"name": "pumpjack", "x": x, "y": y, "direction": DIRNUM[pick[0]], "params": Q})
    # trunk first, so the field net can join it anywhere
    path = astar(SEED, GOAL, blocked, bounds)
    if not path:
        raise SystemExit("no trunk path")
    # pump halfway: on a straight stretch near the middle
    mid = None
    half = len(path) // 2
    for k in range(0, len(path) // 3):
        for i in (half + k, half - k):
            if 1 < i < len(path) - 3 and path[i + 2][0] - path[i - 2][0] in (4, -4) and path[i + 2][1] == path[i - 2][1]:
                mid = i
                break
        if mid:
            break
    tr = trunk_entities(path, mid)
    ents += tr
    ents.append({"name": "pump", "x": JOIN_PUMP[0], "y": JOIN_PUMP[1], "direction": 4, "params": Q})
    # field net: plain pipes, BFS from every output to what is already laid; it meets the trunk only on the seed tile (a plain pipe)
    trunk_tiles = set(path)
    pipes = {SEED}
    field_block = blocked | trunk_tiles
    for x, y, d, t in sorted(jacks, key=lambda p: abs(p[3][0] - SEED[0]) + abs(p[3][1] - SEED[1])):
        if t in pipes:
            continue
        prev = {t: None}
        dq = deque([t])
        goal = None
        while dq:
            c = dq.popleft()
            if c in pipes and c != t:
                goal = c
                break
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (c[0] + dx, c[1] + dy)
                if n in prev:
                    continue
                if n in pipes or (n not in field_block and bounds[0] <= n[0] <= bounds[2] and bounds[1] <= n[1] <= bounds[3]):
                    prev[n] = c
                    dq.append(n)
        if goal is None:
            print("no pipe path for the jack at", x, y)
            continue
        c = goal
        while c is not None:
            if c not in pipes:
                pipes.add(c)
                ents.append({"name": "pipe", "x": c[0] + 0.5, "y": c[1] + 0.5, "params": Q})
            c = prev[c]
    return ents, path, mid, jacks


def main():
    grid = sys.argv[1]
    apply = "--apply" in sys.argv
    ents, path, mid, jacks = plan(grid)
    # the seed tile is both the trunk's first tile and the field net's root: keep one entity per tile
    seen, uniq = {}, []
    for e in ents:
        k = (e["x"], e["y"])
        if e["name"] in ("pipe", "pipe-to-ground") and k in seen:
            continue
        seen[k] = 1
        uniq.append(e)
    ents = uniq
    names = {}
    for e in ents:
        names[e["name"]] = names.get(e["name"], 0) + 1
    print("jacks", len(jacks), "trunk tiles", len(path), "mid pump at", path[mid] if mid else None, names)
    corners = [path[0]] + [path[i] for i in range(1, len(path) - 1) if (path[i][0] - path[i - 1][0], path[i][1] - path[i - 1][1]) != (path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1])] + [path[-1]]
    print("trunk corners:", corners)
    json.dump(ents, open(grid.replace("grid.json", "plan.json"), "w"))
    if apply:
        print(tools["save_game"]("skippy"))
    bad = 0
    for part in batches(ents):
        r = json.loads(tools["place_entities"](json.dumps(part), dry_run=not apply))
        print("placed", r.get("placed"), "failed", len(r.get("failed") or []))
        if r.get("failed"):
            bad += len(r["failed"])
            print(json.dumps(r["failed"])[:1500])
    if apply:
        xs = [p[0] for p in path]
        ys = [p[1] for p in path]
        print(tools["run_lua"]("game.forces.player.chart(game.surfaces.nauvis,{{%d,%d},{%d,%d}}) rcon.print('charted')" % (min(xs + [-730]) - 16, min(ys + [-440]) - 16, max(xs) + 16, max(ys + [-370]) + 16)))
    print("failures:", bad)


if __name__ == "__main__":
    main()
