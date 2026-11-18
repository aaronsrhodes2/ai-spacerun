#!/usr/bin/env python3
"""Edgerunner FLANKS (the Captain, 2026-11-17: "Arm the flanks"; plan stage 3 in docs/fusion-and-galaxy-edge-plan.md).
Stage 1 (apex stretch) is scripts/edge_ship.py, the ammunition works scripts/edge_works.py, the stern scripts/edge_stern.py.

TURRETS  both slanted sides from row -455 (under the stage-1 stretch) down to row 280, on the stage-1 pattern per 100 rows: gun turrets
         at 5, 20, 35, 50, 65, 80, 95 and rocket turrets at 10, 40, 70, each fed by one bulk inserter from the ammunition belt. NO railguns
         here: the belt has two lanes and each carries one kind (see LANES); railgun ammunition would be a third.
BELTS    the ammunition belt on the strip's third column (as stage 1). The feed reaches a side at its middle (row J, where the spoke from
         the hub wedge arrives) and a splitter sends it both ways: UP to row -456, where it runs into the stage-1 belt, and DOWN to row 280.
         Both ends are dead ends, which cannot clog because of the lanes.
LANES    one kind per lane from the works to the last turret: piercing magazines on one, explosive rockets on the other. At the works:
           piercing assembler (4..6,-36..-34): two new inserters on its north side, (5,-37) and (6,-37), drop on the two feed belts on
             row -38: the WEST feed runs west from x 5, the EAST feed east from x 6. Dropped from the south: the north lane.
           explosive-rocket assembler (-3..-1,-35..-33): two new inserters on its north side, (-3,-36) and (-1,-36). The first drops on a
             stub that side-loads the west feed from the south (south lane). The second drops on a belt that runs east on row -37, goes
             under the bus ends and the piercing inserters by underground belt (0 -> 9) and side-loads the east feed at x 10 from the south.
           Removed: the old explosive-rocket output inserter (-4,-34) and the top tile of both old output belts ((-5,-37), (8,-37): they
             would side-load the feeds). The west output belt now holds railgun ammunition only.
FEED     from row -38 each feed is routed over free deck (shortest path, few turns) along the wedge edge and the diagonal spoke to the splitter.
DECK     tile ghosts for the pads and the two splitter corners; the hub lays them from its foundation stock.
Steps: plan | deck | build [--apply] | status
Usage: edge_flanks.py plan ; edge_flanks.py deck ; edge_flanks.py build --apply ; edge_flanks.py status"""
import heapq
import json
import sys

import edge_ship as ES
import triangle_miner as TM
from _game import tools
from edge_works import T

L = tools["run_lua"]
MAP = "C:/Users/aaron/AppData/Local/Temp/claude/d329ec5d6b30de63/3ba65645-e6d0-4892-b072-cf3a47d3aa43/scratchpad/edge_map.json"
Y_TOP, Y_BOT = -455, 280             # first row under stage 1, last row of the down belt
J_NEAR = -141                        # the spoke arrives about here
BELT, UG, SPLIT = "express-transport-belt", "express-underground-belt", "express-splitter"
N, E, S, W = 0, 4, 8, 12
DIR = {(0, -1): N, (1, 0): E, (0, 1): S, (-1, 0): W}
KEEP_CLEAR = 14                      # no pads within this many rows of the junction (the feed needs the room)


def col(y, side):
    return ES.edge(y, side) + (2 if side < 0 else -2)


def up_cells(side, yb, yt):
    """The ammunition lane from row yb up to row yt, bottom first; a sideways step sits on the lower row (the stage-1 rule)."""
    path = []
    for y in range(yb, yt - 1, -1):
        path.append((col(y, side), y))
        if y > yt and col(y - 1, side) != col(y, side):
            path.append((col(y - 1, side), y))
    return path


def junction(side):
    for d in range(0, 10):
        for j in (J_NEAR + d, J_NEAR - d):
            if col(j - 1, side) == col(j, side) != col(j + 1, side):      # no step above; the step below sits beside the splitter's lower half
                return j
    raise ValueError("no junction row")


def side_plan(side):
    s = 1 if side < 0 else -1
    j = junction(side)
    a = col(j, side)
    up = up_cells(side, j, -456)[:-1]                       # the last cell is the stage-1 belt's bottom tile
    nxt = (col(-456, side), -456)
    down = list(reversed(up_cells(side, Y_BOT, j)[:-1]))   # starts on the step cell (a, j+1), straight out of the splitter
    belts = []
    for path, end in ((up, nxt), (down, (down[-1][0], down[-1][1] + 1))):
        for i, c in enumerate(path):
            n = path[i + 1] if i + 1 < len(path) else end
            belts.append((c[0], c[1], DIR[(n[0] - c[0], n[1] - c[1])]))
    lane = set(up) | set(down)
    split = [(a + s, j), (a + s, j + 1)]
    goal = (a + 2 * s, j)
    used = set(lane) | set(split) | {goal}
    apron = {(a + (2 + k) * s, j + dy) for k in range(0, 4) for dy in (-1, 0, 1)}      # deck for the feed to reach the splitter
    turrets, inserters, tiles = [], [], set(used) | apron
    for y0 in range(Y_TOP, Y_BOT, 100):
        rows = min(100, Y_BOT - y0 + 1)
        _, ts, ins, _ = ES.stretch(y0, rows, side)
        for (name, x0, y, w, h), (ix, iy, d) in zip(ts, ins):
            if name == "railgun-turret" or abs(y - j) < KEEP_CLEAR:
                continue
            cells = {(x0 + i, y + k) for i in range(w) for k in range(h)} | {(ix, iy)}
            if cells & used:
                continue
            used |= cells
            tiles |= cells
            turrets.append((name, x0, y, w, h))
            inserters.append((ix, iy, d))
    return dict(side=side, j=j, a=a, belts=belts, split=split, goal=goal, used=used, turrets=turrets, inserters=inserters, tiles=tiles)


def works():
    """Entities at the works and the two feed starts on row -38. Returns (ents, cells, west start, east start)."""
    e = [T("fast-inserter", -3, -36, S), T("fast-inserter", -1, -36, S), T("fast-inserter", 5, -37, S), T("fast-inserter", 6, -37, S),
         T(BELT, -3, -37, N)]
    # The two bus belts (x 1 and 2) end at row -36 facing north: a belt on (1,-37) or (2,-37) is side-loaded with steel, explosives and plates
    # (it happened on the first build, 2026-11-17). The rocket belt dives at x 0 and comes up at x 9, past the buses and the piercing inserters.
    e += [T(BELT, -1, -37, E), T(UG, 0, -37, E, type="input"), T(UG, 9, -37, E, type="output"), T(BELT, 10, -37, N)]
    e += [T(BELT, x, -38, W) for x in range(5, -11, -1)]
    e += [T(BELT, x, -38, E) for x in range(6, 13)]
    cells = {(round(q["x"] - 0.5), round(q["y"] - 0.5)) for q in e}
    return e, cells, (-11, -38), (13, -38)


def route(start, goal, free, last_dir):
    """Cheapest path of free cells from start to goal (4-connected; a turn costs a little, so it runs straight where it can)."""
    pq = [(0, start, None)]
    best = {(start, None): 0}
    prev = {}
    while pq:
        c, cell, d = heapq.heappop(pq)
        if cell == goal:
            path = [(cell, d)]
            while path[-1] in prev:
                path.append(prev[path[-1]])
            cells = [p[0] for p in reversed(path)]
            out = []
            for i, q in enumerate(cells):
                n = cells[i + 1] if i + 1 < len(cells) else None
                out.append((q[0], q[1], DIR[(n[0] - q[0], n[1] - q[1])] if n else last_dir))
            return out
        if best.get((cell, d), 1e18) < c:
            continue
        for (dx, dy), nd in DIR.items():
            n = (cell[0] + dx, cell[1] + dy)
            if n not in free:
                continue
            nc = c + 1 + (0.3 if d is not None and nd != d else 0)
            if nc < best.get((n, nd), 1e18):
                best[(n, nd)] = nc
                prev[(n, nd)] = (cell, d)
                heapq.heappush(pq, (nc, n, nd))
    raise ValueError("no route from %s to %s" % (start, goal))


def design():
    m = json.load(open(MAP))
    deck = {tuple(c) for c in m["deck"]}
    occ = {(x, y) for x, y, n in m["occ"] if n != "substation"}
    occ -= {(-5, -37), (8, -37), (-4, -34)}
    sides = {sd: side_plan(sd) for sd in (-1, 1)}
    wk, wcells, ws, es = works()
    ents, tiles = list(wk), set()
    for sd, p in sides.items():
        tiles |= p["tiles"]
    # THE SLIT. Each spoke has a one-tile slit at x = -126 / 126 (rows -75..-71): foundation cannot be laid in it (a tile ghost there stayed
    # unbuilt with 737 foundations in the hub) and an underground belt does not pair across open space (tried 2026-11-17: the feed stopped
    # at the entrance). The Captain bridged it with four long-handed inserters (x = -127 / 127, rows -75..-72, picking at 129, dropping at 125,
    # toward the hub); those and their pick and drop tiles are left alone. The feed crosses the same way, one kind per inserter so the lanes
    # survive: a splitter sends the feed to two dead ends on the hub side, (125,-76) and (125,-71); a long-handed inserter at (127,-76) takes
    # magazines across, one at (127,-71) takes rockets. On the far side the two belts side-load one new belt from OPPOSITE sides at (131,-74).
    cross, fixed = {}, set()
    for sg in (-1, 1):
        out, inn = (W, E) if sg < 0 else (E, W)
        occ |= {(sg * x, y) for x in (125, 127, 128, 129) for y in range(-75, -71)}
        tiles |= {(sg * m, -71) for m in (127, 129, 130, 131, 132)} | {(sg * 132, -72), (sg * 132, -73)}
        deck -= {(sg * 126, -76)}
        b = [(124, -72, N), (124, -73, N), (124, -74, N), (124, -75, N), (124, -76, out), (125, -76, out), (124, -71, out), (125, -71, out),
             (129, -76, out), (130, -76, S), (130, -75, S), (130, -74, out),
             (129, -71, out), (130, -71, out), (131, -71, out), (132, -71, N), (132, -72, N), (132, -73, N), (132, -74, inn), (131, -74, N)]
        ce = [T(BELT, sg * m, y, d) for m, y, d in b]
        ce += [T(SPLIT, sg * 123, -72, out, 1, 2), T("long-handed-inserter", sg * 127, -76, inn), T("long-handed-inserter", sg * 127, -71, inn)]
        cross[sg] = ce
        fixed |= {(sg * m, y) for m, y, d in b} | {(sg * 123, -72), (sg * 123, -71), (sg * 127, -76), (sg * 127, -71)}
    free = (deck | tiles) - occ - wcells
    for sd, p in sides.items():
        free -= p["used"]
    feeds = {}
    for sd, start in ((-1, ws), (1, es)):
        p = sides[sd]
        fr = set(free) | {p["goal"], start}
        for other in feeds.values():
            fr -= {(x, y) for x, y, d in other}
        pre, nxt = (sd * 122, -71), (sd * 131, -75)
        way = W if sd < 0 else E
        fr -= fixed
        leg1 = route(start, pre, fr | {pre}, way)
        leg2 = route(nxt, p["goal"], (fr | {nxt}) - {(x, y) for x, y, d in leg1}, way)
        ents += cross[sd]
        feeds[sd] = leg1 + leg2
        ents += [T(BELT, x, y, d) for x, y, d in feeds[sd]]
        ents += [T(SPLIT, p["split"][0][0], p["j"], W if sd < 0 else E, 1, 2)]
        ents += [T(BELT, x, y, d) for x, y, d in p["belts"]]
        ents += [T("bulk-inserter", x, y, d) for x, y, d in p["inserters"]]
        ents += [T(n, x, y, 0, w, h) for n, x, y, w, h in p["turrets"]]
    design.cross = cross
    return sides, feeds, ents, tiles


def cells(ts):
    return "{" + ",".join("{%d,%d}" % c for c in sorted(ts)) + "}"


def ent_cells(ents):
    out = set()
    for q in ents:
        w, h = {"gun-turret": (2, 2), "rocket-turret": (3, 3), SPLIT: (1, 2)}.get(q["name"], (1, 1))
        x0, y0 = round(q["x"] - w / 2), round(q["y"] - h / 2)
        out |= {(x0 + i, y0 + k) for i in range(w) for k in range(h)}
    return out


def plan():
    sides, feeds, ents, tiles = design()
    for sd, p in sides.items():
        kinds = {}
        for t in p["turrets"]:
            kinds[t[0]] = kinds.get(t[0], 0) + 1
        print("side %+d: junction row %d, ammunition belt %d tiles, feed %d tiles, turrets %s" % (sd, p["j"], len(p["belts"]), len(feeds[sd]), kinds))
    all_cells = ent_cells(ents) | tiles
    seen, dup = set(), 0
    for q in ents:
        c = ent_cells([q])
        dup += len(c & seen)
        seen |= c
    print(len(ents), "entities on", len(all_cells), "tiles, overlapping tiles", dup)
    blk, need = {}, 0
    cs = sorted(all_cells)
    for i in range(0, len(cs), 1500):
        r = L(TM.AT + "local need=0 local blk={} for _,q in pairs(" + cells(cs[i:i + 1500]) + ") do if s.get_tile(q[1],q[2]).name~='space-platform-foundation' then need=need+1 end "
              "for _,e in pairs(s.find_entities_filtered{area={{q[1]+0.1,q[2]+0.1},{q[1]+0.9,q[2]+0.9}}}) do if e.type~='tile-ghost' then local k=e.name blk[k]=(blk[k] or 0)+1 end end end "
              "local t={} for k,v in pairs(blk) do t[#t+1]=k..'='..v end rcon.print(need..'|'..table.concat(t,','))")
        a, b = r.strip().split("|")
        need += int(a)
        for kv in b.split(","):
            if kv:
                k, v = kv.split("=")
                blk[k] = blk.get(k, 0) + int(v)
    print("deck missing", need, "| standing on these tiles now:", blk or "nothing")
    return ents, all_cells


def deck():
    ents, all_cells = plan()
    cs = sorted(all_cells)
    n = 0
    for i in range(0, len(cs), 1500):
        n += int(L(TM.AT + "local n=0 for _,q in pairs(" + cells(cs[i:i + 1500]) + ") do if s.get_tile(q[1],q[2]).name~='space-platform-foundation' and "
                   "s.count_entities_filtered{type='tile-ghost',position={q[1]+0.5,q[2]+0.5},radius=0.3}==0 then "
                   "if s.create_entity{name='tile-ghost',inner_name='space-platform-foundation',position={q[1],q[2]},force='player'} then n=n+1 end end end rcon.print(n)"))
    print("tile ghosts laid", n)


def build(apply):
    ents, all_cells = plan()
    if apply:
        print("save:", tools["save_game"]("pre-edge-flanks"))
        cs = sorted(all_cells)
        n = 0
        for i in range(0, len(cs), 1500):
            n += int(L(TM.AT + "local n=0 for _,q in pairs(" + cells(cs[i:i + 1500]) + ") do for _,e in pairs(s.find_entities_filtered{name='substation',area={{q[1]+0.1,q[2]+0.1},{q[1]+0.9,q[2]+0.9}}}) do "
                       "if e.valid then e.destroy() n=n+1 end end end rcon.print(n)"))
        print("substations removed from the lane and pads:", n)
        print(L(TM.AT + "local n=0 for _,q in pairs({{-5,-37,'express-transport-belt'},{8,-37,'express-transport-belt'},{-4,-34,'fast-inserter'}}) do "
                "local e=s.find_entities_filtered{name=q[3],position={q[1]+0.5,q[2]+0.5},radius=0.3}[1] if e then e.destroy() n=n+1 end end rcon.print('old works outlets removed: '..n)"))
    ok, bad = TM.place(ents, apply)
    print("placed" if apply else "dry run: would place", ok, "of", len(ents), "failed", bad)


FILT = (TM.AT + "local n=0 for _,q in pairs({{127,-76,{'piercing-rounds-magazine','firearm-magazine','uranium-rounds-magazine'}},{127,-71,{'explosive-rocket','rocket'}}}) do for _,sg in pairs({-1,1}) do "
        "local e=s.find_entities_filtered{name='long-handed-inserter',position={sg*q[1]+0.5,q[2]+0.5},radius=0.3}[1] if e then e.use_filters=true e.inserter_filter_mode='whitelist' "
        "for i,nm in pairs(q[3]) do e.set_filter(i,{name=nm,quality='normal',comparator='='}) end n=n+1 end end end rcon.print('crossing inserters filtered: '..n)")


def refeed(apply):
    """Places only the feed belts and the slit crossings (the side belts and turrets stand)."""
    sides, feeds, ents, tiles = design()
    part = []
    for sd in (-1, 1):
        part += [T(BELT, x, y, d) for x, y, d in feeds[sd]] + design.cross[sd]
    ok, bad = TM.place(part, apply)
    print("placed" if apply else "dry run: would place", ok, "of", len(part), "failed", bad)
    if apply:
        print(L(FILT))


STATUS = (TM.AT + "local m={} for k,v in pairs(defines.entity_status) do m[v]=k end local c={} for _,e in pairs(s.find_entities_filtered{type='ammo-turret'}) do "
          "local am=0 for _,i in pairs(e.get_inventory(defines.inventory.turret_ammo).get_contents()) do am=am+i.count end local band=e.position.y<-455 and 'apex stretch' or 'flanks' "
          "local k=band..' '..e.name..(am>0 and ' armed' or ' EMPTY') c[k]=(c[k] or 0)+1 end local t={} for k,v in pairs(c) do t[#t+1]=k..' x'..v end table.sort(t) local o={table.concat(t,string.char(10))} "
          "local it={} for _,b in pairs(s.find_entities_filtered{type={'transport-belt','underground-belt','splitter'}}) do for i=1,b.get_max_transport_line_index() do for _,x in pairs(b.get_transport_line(i).get_contents()) do "
          "if not x.name:find('chunk') and not x.name:find('ore') and not x.name:find('plate') then it[x.name]=(it[x.name] or 0)+x.count end end end end local u={} for k,v in pairs(it) do u[#u+1]=k..' '..v end table.sort(u) "
          "o[#o+1]='on belts: '..table.concat(u,', ') local dm=0 for _,e in pairs(s.find_entities_filtered{force='player'}) do if e.health and e.health<e.max_health then dm=dm+1 end end "
          "o[#o+1]='damaged '..dm..', tile ghosts '..s.count_entities_filtered{type='tile-ghost'}..', hub foundations '..p.hub.get_inventory(defines.inventory.hub_main).get_item_count('space-platform-foundation') "
          "rcon.print(table.concat(o,string.char(10)))")


def main():
    step = sys.argv[1] if len(sys.argv) > 1 else "status"
    if step == "plan":
        plan()
    elif step == "deck":
        deck()
    elif step == "build":
        build("--apply" in sys.argv)
    elif step == "refeed":
        refeed("--apply" in sys.argv)
    elif step == "status":
        print(L(STATUS))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
