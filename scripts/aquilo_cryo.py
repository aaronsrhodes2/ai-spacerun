#!/usr/bin/env python3
"""Aquilo: ice platform works and the cryogenic science line (the Captain, 2026-11-14: "we need the ice platforms filled in at Aquilo";
cryogenic science unlocks foundation, quantum processor, railgun).

Facts read from the game (2026-11-14):
  - ice-platform = 50 ice + 400 ammonia, 30 s, in a cryogenic plant (epic speed 3.8, 1.5 MW): 7.6 platforms a minute a plant.
    Separation gives 5 ice + 50 ammonia a craft: a platform's ice (10 crafts) brings 500 ammonia, 100 more than it uses. Without a sink
    for that surplus the line starves itself, so the works end in a rocket fuel plant (ammonia-rocket-fuel: 10 solid fuel + 50 water +
    500 ammonia), which also makes the fuel for the rockets that will lift the science packs.
  - Fluid ports: cryogenic plant facing N has its three inputs on the bottom edge (x-2, x, x+2) and outputs on top; the first fluid of a
    recipe uses the first box (x-2). Chemical plant N: inputs top (x-1, x+1), outputs bottom (x-1, x+1).
  - Heat: every machine, inserter and pipe must touch a heat pipe. Two continuous pipe mains wall in whatever lies between them, so the
    solution main runs as underground pipe (a heat pipe passes over the gap); the ammonia main is the bottom edge.
Layout of the platform works (tiles; snow field south-west of the pad, rows -1..11, x -24..13):
  pump (13,0) facing east -> solution main along y=0 (junction at cx-6, underground between) -> per unit a separation plant
  (cx-6..cx-4, 4..6) with a bulk inserter (cx-3,5) handing its ice straight to the cryogenic plant (cx-2..cx+2, 2..6); platforms leave by
  the inserter (cx+1,1) into the red chest (cx+1,0). Ammonia main along y=7 under all units; its west end feeds the rocket fuel plant
  (-21..-19, 9..11), water from the melter (-24..-22, 6..8). Unit centres cx = -12, -2, 8.
Steps: platforms [--apply] | config | status [seconds]
Usage: aquilo_cryo.py platforms --apply"""
import json
import sys
import time
from collections import deque

from _game import tools

SURF = "aquilo"
Q = {"quality": "epic"}
N, E, S, W = 0, 4, 8, 12
NOHEAT = {"passive-provider-chest", "requester-chest", "steel-chest", "storage-chest", "buffer-chest", "substation", "medium-electric-pole",
          "big-electric-pole", "heat-pipe", "offshore-pump", "heat-exchanger", "heating-tower"}
USABLE = set("SCiP")


def lua(code):
    return tools["run_lua"](code)


class Plan:
    def __init__(self):
        self.ents = []
        self.res = set()        # tiles kept free of heat pipes

    def add(self, name, x, y, w=1, h=1, d=N, recipe=None, **params):
        """x, y = top-left tile of the footprint."""
        e = {"name": name, "x": x + w / 2, "y": y + h / 2, "direction": d, "params": dict(Q, **params),
             "tiles": {(x + i, y + j) for i in range(w) for j in range(h)}}
        if recipe:
            e["recipe"] = recipe
        self.ents.append(e)
        return e

    def pipe(self, x, y):
        self.add("pipe", x, y)

    def occupied(self):
        return set().union(*[e["tiles"] for e in self.ents]) if self.ents else set()


def fetch(box):
    """tile -> class char ('S' snow, 'C' concrete, 'i' meltable ice, '~' brash ice, 'P' ice platform, '.' ocean, '#' something stands there)."""
    x0, y0, x1, y1 = box
    code = ("local s=game.surfaces.aquilo local land={['dust-flat']='S',['dust-crests']='S',['dust-lumpy']='S',['dust-patchy']='S',['snow-crests']='S',['snow-flat']='S',['snow-lumpy']='S',['snow-patchy']='S',['frozen-concrete']='C',['concrete']='C',"
            "['refined-concrete']='C',['ice-smooth']='i',['ice-rough']='i',['brash-ice']='~',['ice-platform']='P'} local rows={} for y=%d,%d do local r={} for x=%d,%d do "
            "local c=land[s.get_tile(x,y).name] or '.' for _,e in pairs(s.find_entities_filtered{area={{x+0.05,y+0.05},{x+0.95,y+0.95}}}) do "
            "if e.type~='tile-ghost' and e.type~='logistic-robot' and e.type~='construction-robot' then c='#' break end end r[#r+1]=c end rows[#rows+1]=table.concat(r) end rcon.print(table.concat(rows,'|'))")
    g = {}
    for ya in range(y0, y1 + 1, 40):
        rows = lua(code % (ya, min(y1, ya + 39), x0, x1)).strip().split("|")
        for j, row in enumerate(rows):
            for i, c in enumerate(row):
                g[(x0 + i, ya + j)] = c
    return g


def heat_tiles(box):
    x0, y0, x1, y1 = box
    got = lua("local s=game.surfaces.aquilo local t={} for _,e in pairs(s.find_entities_filtered{name={'heat-pipe','heating-tower','nuclear-reactor'},area={{%d,%d},{%d,%d}}}) do "
              "local bb=e.bounding_box for y=math.floor(bb.left_top.y+0.01),math.ceil(bb.right_bottom.y-0.01)-1 do for x=math.floor(bb.left_top.x+0.01),math.ceil(bb.right_bottom.x-0.01)-1 do "
              "t[#t+1]=x..','..y end end end rcon.print(table.concat(t,' '))" % (x0, y0, x1 + 1, y1 + 1)).split()
    return {tuple(int(v) for v in g.split(",")) for g in got}


def adj(t):
    x, y = t
    return ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))


def heat_plan(P, grid, net, extra=()):
    """Heat pipes: a halo round everything that needs heat, joined to the standing network `net`, dead ends pruned. Returns (tiles, unheated)."""
    occ = P.occupied()
    free = {t for t, c in grid.items() if c in USABLE} - occ - P.res - net
    need = [e for e in P.ents if e["name"] not in NOHEAT]
    need_adj = set()
    for e in need:
        for t in e["tiles"]:
            need_adj.update(adj(t))
    H = (need_adj & free) | (set(extra) & free)
    # join the pieces: breadth first from the standing network (and what is already joined) to each piece that is not
    def comps(tiles):
        seen, out = set(), []
        for t in tiles:
            if t in seen:
                continue
            c, q = {t}, deque([t])
            seen.add(t)
            while q:
                u = q.popleft()
                for n in adj(u):
                    if n in tiles and n not in seen:
                        seen.add(n)
                        c.add(n)
                        q.append(n)
            out.append(c)
        return out
    for _ in range(60):
        cs = comps(H | net)
        main = [c for c in cs if c & net]
        joined = set().union(*main) if main else set()
        loose = [c for c in cs if not (c & net)]
        if not loose:
            break
        prev, q, hit = {t: None for t in joined}, deque(joined), None
        targets = set().union(*loose)
        while q and hit is None:
            u = q.popleft()
            for n in adj(u):
                if n in prev:
                    continue
                if n in targets:
                    prev[n] = u
                    hit = n
                    break
                if n in free:
                    prev[n] = u
                    q.append(n)
        if hit is None:
            print("heat: %d piece(s) cannot be joined, e.g. %s" % (len(loose), sorted(loose[0])[:3]))
            for c in loose:
                H -= c
            break
        c = prev[hit]
        while c is not None and c not in joined:
            H.add(c)
            c = prev[c]
    # prune dead ends that heat nothing
    changed = True
    while changed:
        changed = False
        for t in list(H):
            if t in need_adj:
                continue
            if sum(1 for n in adj(t) if n in H or n in net) <= 1:
                H.discard(t)
                changed = True
    allheat = H | net
    cold = [(e["name"], e["x"], e["y"]) for e in need if not any(n in allheat for t in e["tiles"] for n in adj(t))]
    return H, cold


def build(P, grid, net, apply, extra=()):
    occ = P.occupied()
    bad = [(t, grid.get(t, "?")) for t in occ if grid.get(t, "?") not in USABLE and not any(e["name"] == "offshore-pump" and t in e["tiles"] for e in P.ents)]
    if bad:
        print("footprint on unusable tiles:", sorted(bad)[:20])
    H, cold = heat_plan(P, grid, net, extra)
    print("heat pipes:", len(H), "unheated:", cold)
    for x, y in sorted(H):
        P.add("heat-pipe", x, y)
    pave = sorted(t for t in P.occupied() if grid.get(t) == "i")
    print("entities:", len(P.ents), "ice tiles to pave with concrete:", len(pave))
    out = [{k: v for k, v in e.items() if k != "tiles"} for e in P.ents]
    # leave out what stands
    lst = ",".join("{'%s',%s,%s}" % (e["name"], e["x"], e["y"]) for e in out)
    have = []
    items = lst.split("},{")
    for i in range(0, len(out), 300):
        part = ",".join("{'%s',%s,%s}" % (e["name"], e["x"], e["y"]) for e in out[i:i + 300])
        have += lua("local s=game.surfaces.aquilo local t={} for i,q in pairs({%s}) do t[i]=#s.find_entities_filtered{name=q[1],position={q[2],q[3]},radius=0.3} end rcon.print(table.concat(t,','))" % part).strip().split(",")
    out = [e for e, h in zip(out, have) if h == "0"]
    print("new pieces (not yet standing):", len(out))
    if apply and pave:
        print(lua("local s=game.surfaces.aquilo local t={} for _,p in pairs({%s}) do t[#t+1]={name='concrete',position=p} end s.set_tiles(t) rcon.print('paved '..#t)" % ",".join("{%d,%d}" % t for t in pave)))
    order = {"heat-pipe": 0, "substation": 1}
    out.sort(key=lambda e: order.get(e["name"], 2))
    failed = []
    placed = 0
    for i in range(0, len(out), 150):
        r = json.loads(tools["place_entities"](json.dumps(out[i:i + 150]), surface=SURF, dry_run=not apply, clear_trees=apply))
        placed += r.get("placed") or 0
        failed += r.get("failed") or []
    print("placed" if apply else "dry run ok", placed, "failed", json.dumps(failed)[:1500])
    if apply:
        xs = [t[0] for t in P.occupied()]
        ys = [t[1] for t in P.occupied()]
        print(lua("game.forces.player.chart(game.surfaces.aquilo,{{%d,%d},{%d,%d}}) rcon.print('charted')" % (min(xs) - 16, min(ys) - 16, max(xs) + 16, max(ys) + 16)))


# ---------------------------------------------------------------- ice platform works
CY = 4
CXS = [-12, -2, 8]


def platform_plan():
    P = Plan()
    cy = CY
    for cx in CXS:
        J = cx - 6
        P.add("chemical-plant", cx - 6, cy, 3, 3, N, recipe="ammoniacal-solution-separation")
        P.add("cryogenic-plant", cx - 2, cy - 2, 5, 5, N, recipe="ice-platform")
        for y in (cy - 4, cy - 3, cy - 2, cy - 1):
            P.pipe(J, y)
        P.add("pipe-to-ground", J + 1, cy - 4, d=W)
        P.add("pipe-to-ground", J + 9, cy - 4, d=E)
        P.add("bulk-inserter", cx - 3, cy + 1, d=W)           # ice: separation -> cryogenic plant (direction = the side it picks up from)
        P.add("bulk-inserter", cx + 1, cy - 3, d=S)           # platforms out
        P.add("passive-provider-chest", cx + 1, cy - 4)
        P.add("substation", cx - 5, cy - 2, 2, 2)
    P.pipe(CXS[-1] + 4, cy - 4)
    P.add("offshore-pump", CXS[-1] + 5, cy - 4, d=E)
    c1 = CXS[0]
    for x in range(c1 - 7, CXS[-1] - 1):
        P.pipe(x, cy + 3)                                      # the ammonia main
    P.add("bulk-inserter", c1 - 7, cy + 1, d=E)                # ice for the rest of the base (gated in config)
    P.add("passive-provider-chest", c1 - 8, cy + 1)
    rx = c1 - 8
    P.pipe(rx + 1, cy + 4)                                     # ammonia into the rocket fuel plant
    P.pipe(rx - 1, cy + 4)                                     # water: melter -> rocket fuel plant
    P.add("chemical-plant", rx - 1, cy + 5, 3, 3, N, recipe="ammonia-rocket-fuel")
    P.add("chemical-plant", rx - 4, cy + 2, 3, 3, W, recipe="ice-melting")
    P.add("fast-inserter", rx - 3, cy + 1, d=N)
    P.add("requester-chest", rx - 3, cy)
    P.add("fast-inserter", rx - 2, cy + 6, d=W)
    P.add("requester-chest", rx - 3, cy + 6)
    P.add("fast-inserter", rx + 2, cy + 6, d=W)
    P.add("passive-provider-chest", rx + 3, cy + 6)
    return P


BOX_P = (-30, -14, 20, 14)


def platforms(apply):
    grid = fetch(BOX_P)
    net = heat_tiles(BOX_P)
    P = platform_plan()
    extra = [(x, CY - 5) for x in range(CXS[0] - 6, CXS[-1] + 5)]
    build(P, grid, net, apply, extra)


def cond(x, y, item, comp, n):
    return ("do local e=s.find_entities_filtered{type='inserter',position={%s,%s},radius=0.4}[1] local cb=e.get_or_create_control_behavior() cb.connect_to_logistic_network=true "
            "cb.logistic_condition={comparator='%s',first_signal={type='item',name='%s'},constant=%d} o[#o+1]=e.name..' %s%s%d' end " % (x, y, comp, item, item, comp, n))


def ask(x, y, reqs):
    slots = " ".join("sec.set_slot(%d,{value={type='item',name='%s',quality='normal'},min=%d})" % (i + 1, k, v) for i, (k, v) in enumerate(reqs.items()))
    return ("do local c=s.find_entities_filtered{name='requester-chest',position={%s,%s},radius=0.4}[1] local pt=c.get_logistic_point(defines.logistic_member_index.logistic_container) "
            "local sec=pt.get_section(1) or pt.add_section() %s o[#o+1]='chest %s,%s asks %s' end " % (x, y, slots, x, y, "+".join(reqs)))


def config():
    c1 = CXS[0]
    rx = c1 - 8
    code = "local s=game.surfaces.aquilo local o={} "
    code += ask(rx - 2.5, CY + .5, {"ice": 50})
    code += ask(rx - 2.5, CY + 6.5, {"solid-fuel": 100})
    code += cond(c1 - 6.5, CY + 1.5, "ice", "<", 1500)
    code += cond(40.5, -3.5, "ice", ">", 4000)             # the recycler ice sink runs on true surplus only
    code += "rcon.print(table.concat(o,' | '))"
    print(lua(code))


STATUS = ("local s=game.surfaces.aquilo local f=game.forces.player local o={} local st={} for k,v in pairs(defines.entity_status) do st[v]=k end "
          "for _,e in pairs(s.find_entities_filtered{force=f,type={'assembling-machine','furnace'}}) do local r=e.get_recipe() local fl='' for i=1,e.fluids_count do local fd=e.get_fluid(i) if fd then fl=fl..' '..fd.name..'='..math.floor(fd.amount) end end "
          "o[#o+1]=e.name..' '..e.position.x..','..e.position.y..' '..(r and r.name or '-')..' '..(st[e.status] or '?')..' made '..e.products_finished..fl end "
          "local fr=0 local names={} for _,e in pairs(s.find_entities_filtered{force=f}) do if e.frozen then fr=fr+1 if #names<25 then names[#names+1]=e.name..'@'..e.position.x..','..e.position.y end end end o[#o+1]='frozen '..fr..' '..table.concat(names,' ') "
          "local net=s.find_logistic_network_by_position({4,-11},f) local c={} for _,n in pairs({'ice','ice-platform','solid-fuel','rocket-fuel','lithium','lithium-plate','holmium-plate','cryogenic-science-pack'}) do c[#c+1]=n..'='..net.get_item_count(n) end "
          "o[#o+1]='network '..table.concat(c,' ')..' robots L'..net.available_logistic_robots..'/'..net.all_logistic_robots..' C'..net.available_construction_robots..'/'..net.all_construction_robots "
          "local ps=f.get_item_production_statistics(s) for _,n in pairs({'ice-platform','cryogenic-science-pack','ice','rocket-fuel','solid-fuel'}) do o[#o+1]=n..' made total '..ps.get_input_count(n)..' used '..ps.get_output_count(n) end "
          "o[#o+1]='tile ghosts '..s.count_entities_filtered{type='tile-ghost'}..' tick '..game.tick "
          "local t=s.find_entities_filtered{name='heating-tower'}[1] o[#o+1]='tower T'..math.floor(t.temperature) "
          "for _,g in pairs(s.find_entities_filtered{type='generator'}) do o[#o+1]='turbine '..g.position.x..','..g.position.y..' W '..math.floor(g.energy_generated_last_tick*60) end "
          "rcon.print(table.concat(o,'\\n'))")


def status():
    print(lua(STATUS))


def main():
    step = sys.argv[1]
    apply = "--apply" in sys.argv
    if step == "platforms":
        platforms(apply)
    elif step == "config":
        config()
    elif step == "status":
        status()


if __name__ == "__main__":
    main()
