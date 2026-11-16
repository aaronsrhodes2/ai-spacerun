#!/usr/bin/env python3
"""Quantum-processor line on Aquilo (the Captain, 2026-11-15: "start on processors"; fusion only makes sense on Aquilo). Plan: docs/fusion-and-galaxy-edge-plan.md.
One UNIT = a cooling plant K (cryogenic-plant, recipe fluoroketone-cooling, dir 8) with an electromagnetic plant E (quantum-processor, dir 4) hanging off its south-east corner:
  K takes hot fluoroketone on its north edge and gives cold at its south-east corner tile, which is E's cold input (plant-to-plant, no pipe); E gives hot on its west edge.
  A closed hot loop of pipe joins E's hot output to K's hot input, and a routed link (plain pipe, pipe-to-ground where a tunnel is needed) joins that loop to the shared hot trunk
  (traced by scripts/aquilo_fluid_map.py), so the loop's losses (5 hot per processor) are made up by the fluoroketone plant.
  E is fed by one requester chest and an inserter, and its processors go to a provider chest. Heat: heat pipes from the existing network to K and E.
Geometry derived from the prototypes (positions[] per direction N,E,S,W; normal pipe-to-ground connection is on the entity's direction side).
Usage: aquilo_qp.py plan | dry | build | status"""
import heapq
import json
import re
import subprocess
import sys
from pathlib import Path

from _game import tools

L = tools["run_lua"]
X0, Y0, X1, Y1 = -54, -54, -6, -6          # working window (tiles)
Q = "legendary"
V = {0: (0, -1), 4: (1, 0), 8: (0, 1), 12: (-1, 0)}
REQUEST = {"processing-unit": 20, "tungsten-carbide": 20, "superconductor": 20, "carbon-fiber": 20, "lithium-plate": 40}

GRID = r'''
local s=game.surfaces.aquilo local X0,Y0,X1,Y1=%d,%d,%d,%d local DI={[0]=1,[4]=2,[8]=3,[12]=4} local V={[0]={0,-1},[4]={1,0},[8]={0,1},[12]={-1,0}}
local g={} for y=Y0,Y1 do local r={} for x=X0,X1 do local t=s.get_tile(x,y) r[#r+1]=(t.name:find('ocean') or t.name:find('water')) and '~' or ((not s.can_place_entity{name='pipe',position={x+0.5,y+0.5},force='player'}) and '?' or '.') end g[#g+1]=r end
local function mark(e,ch) local bb=e.bounding_box for x=math.floor(bb.left_top.x+0.01),math.ceil(bb.right_bottom.x-0.01)-1 do for y=math.floor(bb.left_top.y+0.01),math.ceil(bb.right_bottom.y-0.01)-1 do if x>=X0 and x<=X1 and y>=Y0 and y<=Y1 then g[y-Y0+1][x-X0+1]=ch end end end end
for _,e in pairs(s.find_entities_filtered{area={{X0,Y0},{X1+1,Y1+1}}}) do local t=e.type if t~='logistic-robot' and t~='construction-robot' and t~='resource' and e.name~='character' then
  if t=='pipe' or t=='pipe-to-ground' then mark(e,'p') elseif t=='heat-pipe' then mark(e,'h') else mark(e,'#') end end end
for _,e in pairs(s.find_entities_filtered{area={{X0,Y0},{X1+1,Y1+1}},type='assembling-machine'}) do local pro=prototypes.entity[e.name]
  for fbi,b in ipairs(pro.fluidbox_prototypes) do for _,c in ipairs(b.pipe_connections) do local pos=c.positions[DI[e.direction]] if pos then local cd=(c.direction+e.direction)%%16
    local x=math.floor(e.position.x+pos.x)+V[cd][1] local y=math.floor(e.position.y+pos.y)+V[cd][2] if x>=X0 and x<=X1 and y>=Y0 and y<=Y1 and g[y-Y0+1][x-X0+1]=='.' then g[y-Y0+1][x-X0+1]='T' end end end end end
local rows={} for i,r in ipairs(g) do rows[i]=table.concat(r) end rcon.print(table.concat(rows,'\n'))
'''


def grid():
    out = L(" ".join((GRID % (X0, Y0, X1, Y1)).split("\n")))
    rows = [r for r in out.split("\n") if len(r) == X1 - X0 + 1]
    return {(X0 + i, Y0 + j): ch for j, r in enumerate(rows) for i, ch in enumerate(r)}


def hot_tiles():
    here = Path(__file__).resolve().parent
    out = subprocess.run([sys.executable, str(here / "aquilo_fluid_map.py"), str(X0), str(Y0), str(X1), str(Y1), "tiles"],
                         capture_output=True, text=True, cwd=str(here)).stdout.split("\n")
    for i, line in enumerate(out):
        if "fluid=fluoroketone-hot" in line and i + 1 < len(out) and "tiles:" in out[i + 1]:
            return {tuple(int(v) for v in m) for m in re.findall(r"(-?\d+),(-?\d+)", out[i + 1])}
    return set()


def tiles_of(cx, cy, w, h):
    x0, y0 = int(round(cx - w / 2.0)), int(round(cy - h / 2.0))
    return {(x0 + i, y0 + j) for i in range(w) for j in range(h)}


def tile(px, py):
    import math
    return (math.floor(px), math.floor(py))


def unit(kx, ky):
    """Entities (tile-keyed) of one unit with K centre (kx, ky) (both x.5) and its loop. Returns dict."""
    ex, ey = kx + 2.5, ky + 4.5
    ents = []
    ents.append({"name": "cryogenic-plant", "x": kx, "y": ky, "direction": 8, "recipe": "fluoroketone-cooling", "params": {"quality": Q}})
    ents.append({"name": "electromagnetic-plant", "x": ex, "y": ey, "direction": 4, "recipe": "quantum-processor", "params": {"quality": Q}})
    ents.append({"name": "requester-chest", "x": kx + 6, "y": ky + 6, "direction": 0, "cfg": {"request": REQUEST}})
    ents.append({"name": "fast-inserter", "x": kx + 5, "y": ky + 6, "direction": 4})
    ents.append({"name": "fast-inserter", "x": kx + 5, "y": ky + 3, "direction": 12})
    ents.append({"name": "passive-provider-chest", "x": kx + 6, "y": ky + 3, "direction": 0})
    ents.append({"name": "medium-electric-pole", "x": kx + 5, "y": ky + 5, "direction": 0, "params": {"quality": Q}})
    t0, t1 = tile(kx, ky + 5), tile(kx + 2, ky - 3)             # E's hot output tile and K's hot input tile: the loop joins them
    loop = []
    cold_target = tile(kx + 2, ky + 3)                              # K's cold output tile = E's cold input (inside E's top edge)
    unused = [tile(kx, ky + 3), tile(kx - 2, ky + 3), tile(ex + 2.5, ey - 0.5), tile(ex + 0.5, ey + 2.5)]
    foot = tiles_of(kx, ky, 5, 5) | tiles_of(ex, ey, 4, 4) | {tile(e["x"], e["y"]) for e in ents[2:]}
    return {"t0": t0, "t1": t1, "ents": ents, "loop": loop, "foot": foot, "kx": kx, "ky": ky, "ex": ex, "ey": ey, "cold": cold_target, "unused": unused}


def loop_path(G, hot, u):
    """Plain-pipe path from E's hot output tile to K's hot input tile through free tiles that touch no foreign pipe or port tile."""
    danger = {t for t, c in G.items() if (c == "p" and t not in hot) or c == "T"} | set(u["unused"]) | {u["cold"]}
    ok = lambda t: G.get(t) == "." and t not in u["foot"] and t not in danger and not any((t[0] + dx, t[1] + dy) in danger for dx, dy in V.values())
    t0, t1 = u["t0"], u["t1"]
    if not (ok(t0) and ok(t1)): return None
    prev, q = {t0: None}, [t0]
    for t in q:
        if t == t1: break
        for dx, dy in V.values():
            n = (t[0] + dx, t[1] + dy)
            if n not in prev and ok(n): prev[n] = t; q.append(n)
    if t1 not in prev: return None
    out, t = [], t1
    while t is not None: out.append(t); t = prev[t]
    return out


def route(G, hot, u):
    """Dijkstra from the unit's loop to the hot network. State = (tile, heading, f): f=1 means this tile is a tunnel exit, which only connects straight ahead.
    Plain steps need a free tile touching no foreign pipe or machine port tile; a tunnel (pipe-to-ground pair, 2..10 apart) runs straight, its entrance placed on a plain
    step's tile (arrival heading = tunnel heading) and its exit followed by a straight step or by the hot network itself."""
    blocked = set(u["foot"]) | set(u["loop"])
    danger = {t for t, c in G.items() if (c == "p" and t not in hot) or c == "T"} | set(u["unused"]) | {u["cold"]}
    def free(t): return G.get(t) == "." and t not in blocked
    def safe(t): return free(t) and t not in danger and not any((t[0] + dx, t[1] + dy) in danger for dx, dy in V.values())
    def hot_at(t): return t in hot
    start = list(u["loop"])
    pq, best, prev = [], {}, {}
    for t in start:
        for h in V:
            best[(t, h, 0)] = 0; heapq.heappush(pq, (0, t, h, 0))
    while pq:
        c, t, h, f = heapq.heappop(pq)
        if best.get((t, h, f), 1e9) < c: continue
        if t not in u["loop"]:
            ahead = (t[0] + V[h][0], t[1] + V[h][1])
            if (f == 0 and any((t[0] + dx, t[1] + dy) in hot for dx, dy in V.values())) or (f == 1 and hot_at(ahead)):
                path, key = [], (t, h, f)
                while key in prev: path.append(key); key = prev[key]
                return [(k[0], k[1]) for k in reversed(path)], start, (key[0], key[1])
        dirs = [h] if f == 1 else [d for d in V if d != (h + 8) % 16]      # no U-turns (a step back onto the tile just left)
        for d in dirs:
            n = (t[0] + V[d][0], t[1] + V[d][1])
            if safe(n) and c + 1 < best.get((n, d, 0), 1e9):
                best[(n, d, 0)] = c + 1; prev[(n, d, 0)] = (t, h, f); heapq.heappush(pq, (c + 1, n, d, 0))
        pt = prev.get((t, h, f))
        if f == 0 and t not in u["loop"] and pt is not None and abs(pt[0][0] - t[0]) + abs(pt[0][1] - t[1]) == 1 and pt[1] == h:
            for k in range(2, 11):
                n = (t[0] + V[h][0] * k, t[1] + V[h][1] * k)
                if free(n) and c + 3 + k * 0.1 < best.get((n, h, 1), 1e9):
                    best[(n, h, 1)] = c + 3 + k * 0.1; prev[(n, h, 1)] = (t, h, f); heapq.heappush(pq, (c + 3 + k * 0.1, n, h, 1))
    return None, start, None


def link_entities(path, start_key):
    """Turn the Dijkstra chain into entities: plain pipes, and a pipe-to-ground at each tunnel end (entrance replaces the plain pipe on its tile)."""
    plain, ent, ext = [], {}, {}
    pts = [start_key] + path
    for a, b in zip(pts, pts[1:]):
        (ta, ha), (tb, hb) = a, b
        if abs(tb[0] - ta[0]) + abs(tb[1] - ta[1]) > 1:
            ent[ta] = (hb + 8) % 16
            ext[tb] = hb
        else:
            plain.append(tb)
    out = []
    for t in dict.fromkeys(plain + list(ent) + list(ext)):
        c = {"x": t[0] + 0.5, "y": t[1] + 0.5}
        if t in ent: out.append({"name": "pipe-to-ground", **c, "direction": ent[t]})
        elif t in ext: out.append({"name": "pipe-to-ground", **c, "direction": ext[t]})
        else: out.append({"name": "pipe", **c, "direction": 0})
    return out


def heat_path(G, u):
    """Plain BFS of heat pipes from any existing heat pipe to a tile touching K and one touching E (4-neighbour of their footprint)."""
    kt, et = tiles_of(u["kx"], u["ky"], 5, 5), tiles_of(u["ex"], u["ey"], 4, 4)
    taken = set(u["foot"]) | set(u["loop"])
    def free(t): return G.get(t) == "." and t not in taken
    def adj(t, S): return any((t[0] + dx, t[1] + dy) in S for dx, dy in V.values())
    hs = {t for t, c in G.items() if c == "h"}
    out, need = [], [kt, et]
    for S in need:
        if any(adj(h, S) or h in S for h in hs): continue
        frontier, seen, par = list(hs), set(hs), {}
        goal = None
        while frontier and goal is None:
            nxt = []
            for t in frontier:
                for dx, dy in V.values():
                    n = (t[0] + dx, t[1] + dy)
                    if n in seen or not free(n): continue
                    seen.add(n); par[n] = t; nxt.append(n)
                    if adj(n, S): goal = n; break
                if goal: break
            frontier = nxt
        if goal is None: return None
        t = goal
        while t in par:
            out.append(t); taken.add(t); hs.add(t); t = par[t]
    return out


def choose(G, hot):
    best = None
    for kx in [x + 0.5 for x in range(-44, -20)]:
        for ky in [y + 0.5 for y in range(-23, -9)]:
            u = unit(kx, ky)
            if not all(G.get(t) == "." for t in u["foot"]): continue
            lp = loop_path(G, hot, u)
            if lp is None: continue
            u["loop"] = lp
            r, start, key = route(G, hot, u)
            if r is None: continue
            h = heat_path(G, u)
            if h is None: continue
            cost = len(r) + len(h)
            if best is None or cost < best[0]: best = (cost, u, r, key, h)
    return best


def build_all(apply):
    G, hot = grid(), hot_tiles()
    print("grid", len(G), "tiles; hot network tiles", len(hot))
    ch = choose(G, hot)
    if not ch:
        print("no site found"); return None
    cost, u, path, key, heat = ch
    link = link_entities(path, key)
    ents = list(u["ents"]) + [{"name": "pipe", "x": t[0] + 0.5, "y": t[1] + 0.5, "direction": 0} for t in u["loop"]] + link + \
           [{"name": "heat-pipe", "x": t[0] + 0.5, "y": t[1] + 0.5, "direction": 0} for t in heat]
    print("site K centre (%s,%s), E (%s,%s); link %d pieces (%d tunnels), heat pipes %d, entities %d" %
          (u["kx"], u["ky"], u["ex"], u["ey"], len(link), sum(1 for e in link if e["name"] == "pipe-to-ground") // 2, len(heat), len(ents)))
    return u, ents


def place(ents, dry):
    out = [{k: v for k, v in e.items() if k not in ("cfg", "tunnel")} for e in ents]
    placed, failed = 0, []
    for i in range(0, len(out), 120):
        r = json.loads(tools["place_entities"](json.dumps(out[i:i + 120]), surface="aquilo", dry_run=dry))
        placed += r.get("placed") or 0
        failed += r.get("failed") or []
    return placed, failed


def configure(u):
    sec = "".join("sec.set_slot(%d,{value={type='item',name='%s',quality='normal',comparator='='},min=%d}) " % (k + 1, n, m) for k, (n, m) in enumerate(REQUEST.items()))
    code = ("local s=game.surfaces.aquilo local e=s.find_entities_filtered{name='requester-chest',position={%s,%s},radius=0.3}[1] if not e then rcon.print('no requester chest') return end "
            "local rp=e.get_requester_point() rp.trash_not_requested=true local sec=rp.sections_count>0 and rp.get_section(1) or rp.add_section() %s rcon.print('requests set')") % (u["kx"] + 6, u["ky"] + 6, sec)
    return L(code)


def status():
    code = ("local s=game.surfaces.aquilo local m={} for k,v in pairs(defines.entity_status) do m[v]=k end local o={} "
            "for _,e in pairs(s.find_entities_filtered{name={'electromagnetic-plant','cryogenic-plant'},force='player'}) do local r=e.get_recipe() if r and (r.name=='quantum-processor' or (r.name=='fluoroketone-cooling')) then "
            "o[#o+1]=r.name..' @'..e.position.x..','..e.position.y..' '..(m[e.status] or '?') end end rcon.print(table.concat(o,'\\n'))")
    print(L(code))


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "plan"
    if cmd == "status":
        return status()
    r = build_all(cmd == "build")
    if not r: return
    u, ents = r
    if cmd == "plan":
        return
    placed, failed = place(ents, cmd == "dry")
    print(("dry run" if cmd == "dry" else "built"), "placed", placed, "failed", json.dumps(failed)[:1500])
    if cmd == "build":
        print(configure(u))
        print(L("local s=game.surfaces.aquilo local k=s.find_entities_filtered{name='cryogenic-plant',position={%s,%s},radius=0.5}[1] local e=s.find_entities_filtered{name='electromagnetic-plant',position={%s,%s},radius=0.5}[1] "
                "k.direction=defines.direction.south e.direction=defines.direction.east rcon.print('rotated '..k.direction..' '..e.direction)" % (u["kx"], u["ky"], u["ex"], u["ey"])))    # place_entities ignores plant facing
        Path(__file__).resolve().parent.parent.joinpath("snapshots", "aquilo_qp_unit.json").write_text(json.dumps({"kx": u["kx"], "ky": u["ky"], "ents": ents}, indent=1))


if __name__ == "__main__":
    main()
