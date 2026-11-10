"""
Oil outpost by fluid train.

  pumpjacks on every well in a box, pipes routed tile by tile (BFS) from each jack's output to one network that ends in a header beside the load stop,
  three pumps (one per fluid wagon) pushing from the header into the wagons, a rail stub (dead end north of the stop), the stop itself, power.
Station frame: rail on x = RAIL_X (odd), train arrives heading north and stops with its front at STOP_Y; cars lie south of the stop: locomotive +2, wagons +9 +16 +23, locomotive +30.

Usage: scripts/build_oil_train.py --area X1 Y1 X2 Y2 --rail X STOP_Y [--apply]
"""
import argparse
import json
from collections import deque

import fx
from _game import tools

from bridge.factorio.planner import batches

OUT = {"N": (1, -2), "E": (2, 1), "S": (-1, 2), "W": (-2, -1)}
DIRNUM = {"N": 0, "E": 4, "S": 8, "W": 12}


def wells(box):
    x1, y1, x2, y2 = box
    r = fx.lua("local s=game.surfaces.nauvis local w={} for _,e in pairs(s.find_entities_filtered{name='crude-oil',area={{%d,%d},{%d,%d}}}) do w[#w+1]={e.position.x,e.position.y} end rcon.print(helpers.table_to_json(w))" % (x1, y1, x2, y2))
    return json.loads(r)


def blocked_tiles(box):
    x1, y1, x2, y2 = box
    r = fx.lua("local s=game.surfaces.nauvis local b={} for _,e in pairs(s.find_entities_filtered{area={{%d,%d},{%d,%d}},force='player'}) do local bb=e.bounding_box for x=math.floor(bb.left_top.x),math.floor(bb.right_bottom.x-0.01) do for y=math.floor(bb.left_top.y),math.floor(bb.right_bottom.y-0.01) do b[#b+1]={x,y} end end end "
               "for x=%d,%d do for y=%d,%d do local t=s.get_tile(x,y) if t.collides_with('player') or t.name:find('water') then b[#b+1]={x,y} end end end rcon.print(helpers.table_to_json(b))" % (x1, y1, x2, y2, x1, x2, y1, y2))
    return {tuple(p) for p in json.loads(r)}


def tile(x, y):
    return (int(x // 1), int(y // 1))


def plan(box, rail_x, stop_y):
    ws = wells(box)
    block = blocked_tiles((box[0] - 10, box[1] - 10, box[2] + 10, stop_y + 40))
    block = {t for t in block}
    ents = []
    foot = set()
    for (x, y) in ws:                                   # pumpjack footprints
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                foot.add(tile(x + dx, y + dy))
        for dx in (-2, -1, 0, 1, 2):                    # keep pipes off the wells' surroundings too
            for dy in (-2, -1, 0, 1, 2):
                foot.add(tile(x + dx, y + dy))
    rail_tiles = {(rx, ry) for rx in range(rail_x - 1, rail_x + 2) for ry in range(box[1] - 30, stop_y + 45)}
    rail_tiles |= {(rail_x + 1, stop_y - 2), (rail_x + 2, stop_y - 2), (rail_x + 1, stop_y - 1), (rail_x + 2, stop_y - 1), (rail_x + 1, stop_y), (rail_x + 2, stop_y)}   # the train stop beside the rail
    # header and pumps
    cars = [stop_y + 9, stop_y + 16, stop_y + 23]
    header_x = rail_x + 3.5
    hy0, hy1 = stop_y + 6.5, stop_y + 25.5
    net = set()
    y = hy0
    while y <= hy1:
        ents.append({"name": "pipe", "x": header_x, "y": y})
        net.add(tile(header_x, y))
        y += 1
    for c in cars:
        ents.append({"name": "pump", "x": rail_x + 2.0, "y": c - 0.5, "direction": 12})
    ents.append({"name": "medium-electric-pole", "x": header_x + 1, "y": stop_y + 12.5})
    ents.append({"name": "medium-electric-pole", "x": header_x + 1, "y": stop_y + 8.5})
    ents.append({"name": "medium-electric-pole", "x": header_x + 1, "y": stop_y + 20.5})
    obstacles = block | foot | rail_tiles
    pumpjacks = []
    for (x, y) in ws:
        best = None
        for d in ("S", "E", "W", "N"):
            ox, oy = OUT[d]
            t = tile(x + ox, y + oy)
            if t in block or t in net:
                continue
            best = best or (d, t)
        if not best:
            continue
        pumpjacks.append((x, y, best[0], best[1]))
    for x, y, d, t in pumpjacks:
        ents.append({"name": "pumpjack", "x": x, "y": y, "direction": DIRNUM[d]})
    foot_only = set()
    for (x, y) in ws:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                foot_only.add(tile(x + dx, y + dy))
    pipes = set(net)
    lo = (box[0] - 10, box[1] - 10)
    hi = (box[2] + 10, stop_y + 40)
    for x, y, d, t in sorted(pumpjacks, key=lambda p: -p[1]):          # nearest to the header first
        if t in pipes:
            continue
        free = lambda c: c not in foot_only and c not in rail_tiles and c not in block and lo[0] <= c[0] <= hi[0] and lo[1] <= c[1] <= hi[1]
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
                if not (free(n) or n in pipes):
                    continue
                prev[n] = c
                dq.append(n)
        if goal is None:
            print("no pipe path for the jack at", x, y)
            continue
        c = t
        path = []
        while c is not None:
            path.append(c)
            c = prev[c]
        c = goal
        while c is not None:
            path.append(c)
            c = prev[c]
        for c in path:
            if c not in pipes:
                pipes.add(c)
                ents.append({"name": "pipe", "x": c[0] + 0.5, "y": c[1] + 0.5})
    # the header sits at x.5? header_x is a tile centre (rail_x - 3.5): make sure
    return ents, pumpjacks


def clear(box, rail_x, stop_y):
    x1, y1, x2, y2 = box[0] - 12, box[1] - 12, box[2] + 12, stop_y + 50
    return fx.lua("local s=game.surfaces.nauvis local n=0 for _,e in pairs(s.find_entities_filtered{area={{%d,%d},{%d,%d}}}) do if e.force.name~='player' and (e.type=='tree' or e.type=='simple-entity' or e.type=='cliff' or e.force.name=='enemy') then e.destroy() n=n+1 elseif e.force.name=='player' and (e.name=='substation' or e.name=='solar-panel' or e.name=='accumulator' or e.name=='roboport') then e.destroy() n=n+1 end end rcon.print('cleared '..n)" % (x1, y1, x2, y2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--area", nargs=4, type=int, required=True)
    ap.add_argument("--rail", nargs=2, type=int, required=True, metavar=("X", "STOP_Y"))
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    rail_x, stop_y = a.rail
    if a.apply:
        print(tools["save_game"]("before-oil"))
        print(clear(a.area, rail_x, stop_y))
    ents, jacks = plan(a.area, rail_x, stop_y)
    print("pumpjacks:", len(jacks), "entities:", len(ents), {n: sum(1 for e in ents if e["name"] == n) for n in sorted({e["name"] for e in ents})})
    for part in batches(ents):
        r = json.loads(tools["place_entities"](json.dumps(part), dry_run=not a.apply))
        if r.get("failed"):
            print("failed:", json.dumps(r["failed"])[:900])
    if a.apply:
        import build_outpost as bo
        box = (a.area[0] - 12, a.area[1] - 12, a.area[2] + 12, stop_y + 40)
        for _ in range(3):
            bo.connect_power(box)
        print(bo.cover_unpowered_drills(box))


if __name__ == "__main__":
    main()
