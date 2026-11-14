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
Layout of the platform works (tiles; north field, x -17..20, y -36..-16):
  pump (-16,-33) facing west on the inlet -> solution main along y=-33 (junction at u+4, underground between) -> per unit (origin u = -15,
  -3, 9) a separation plant (u+4..u+6, -29..-27) with a bulk inserter on each side handing its ice straight to an assembler (u..u+2 and
  u+8..u+10): six makers; platforms leave by inserters at y=-30 into red chests at y=-31. Ammonia main along y=-26 under all of them; a
  branch at x=8 feeds the rocket fuel plant (3..5, -21..-19), water from the melter (0..2, -24..-22).
The other sections (science line, second power set, lithium from brine) carry their own layout notes below.
Steps: platforms | config | causeway | science | science_config | power | brine [--lay] | status   (add --apply to build; all skip what
stands). `brine` first lists the ocean tiles that need a platform: lay them with `_aq_lay.py scripts/aquilo_brine_water.json`.
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
USABLE = set("SCiP~")        # brash ice (~) takes concrete like ice does


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
    nohalo = getattr(P, "nohalo", set())
    for e in need:
        for t in e["tiles"]:
            if t not in nohalo:
                need_adj.update(adj(t))
    H = (need_adj & free) | (set(extra) & free)
    real = set(net)
    virt = set()            # (a tower is NOT treated as a conductor: it joins pipes only at its four side middles)
    net = net | virt
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
        main = [c for c in cs if c & real]
        joined = set().union(*main) if main else set()
        loose = [c for c in cs if not (c & real)]
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
                H -= c - virt
            break
        c = prev[hit]
        while c is not None and c not in joined:
            if c not in virt:
                H.add(c)
            c = prev[c]
    # prune dead ends that heat nothing
    keepers = need_adj | {n for t in nohalo for n in adj(t)}
    changed = True
    while changed:
        changed = False
        for t in list(H):
            if t in keepers:
                continue
            if sum(1 for n in adj(t) if n in H or n in net) <= 1:
                H.discard(t)
                changed = True
    allheat = H | net
    cold = [(e["name"], e["x"], e["y"]) for e in need if not any(n in allheat for t in e["tiles"] for n in adj(t))]
    return H, cold


def build(P, grid, net, apply, extra=(), clear=True):
    occ = P.occupied()
    bad = [(t, grid.get(t, "?")) for t in occ if grid.get(t, "?") not in USABLE and not any(e["name"] == "offshore-pump" and t in e["tiles"] for e in P.ents)]
    if bad:
        print("footprint on unusable tiles:", sorted(bad)[:20])
    H, cold = heat_plan(P, grid, net, extra)
    print("heat pipes:", len(H), "unheated:", cold)
    for x, y in sorted(H):
        P.add("heat-pipe", x, y)
    pave = sorted(t for t in P.occupied() if grid.get(t) in ("i", "P", "~"))      # ice and ice platform are meltable: nothing heated stands on them without concrete
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
        r = json.loads(tools["place_entities"](json.dumps(out[i:i + 150]), surface=SURF, dry_run=not apply, clear_trees=apply and clear))
        placed += r.get("placed") or 0
        failed += r.get("failed") or []
    pv = set(pave)
    failed = [f for f in failed if apply or (int(f["x"] // 1), int(f["y"] // 1)) not in pv]
    print("placed" if apply else "dry run ok", placed, "failed (ice tiles to be paved left out)", json.dumps(failed)[:1500])
    if apply:
        xs = [t[0] for t in P.occupied()]
        ys = [t[1] for t in P.occupied()]
        print(lua("game.forces.player.chart(game.surfaces.aquilo,{{%d,%d},{%d,%d}}) rcon.print('charted')" % (min(xs) - 16, min(ys) - 16, max(xs) + 16, max(ys) + 16)))


# ---------------------------------------------------------------- ice platform works
CY = -29
US = [-15, -3, 9]          # unit origins (pitch 12): assembler u..u+2 | inserter | separation u+4..u+6 | inserter | assembler u+8..u+10 | heat column
RX = 4


def platform_plan():
    P = Plan()
    cy = CY
    for u in US:
        J = u + 4
        P.add("chemical-plant", u + 4, cy, 3, 3, N, recipe="ammoniacal-solution-separation")
        for y in (cy - 4, cy - 3, cy - 2, cy - 1):
            P.pipe(J, y)                                       # junction on the solution main and the stub down into the plant
        if u != US[-1]:
            P.add("pipe-to-ground", J + 1, cy - 4, d=W)        # the main dives so the heat line can cross it
            P.add("pipe-to-ground", J + 11, cy - 4, d=E)
        for a, pick in ((u, E), (u + 8, W)):
            # ice-platform is crafting-with-fluid: an assembler; facing south its fluid port (a+1, cy+3) sits on the ammonia main
            P.add("assembling-machine-3", a, cy, 3, 3, S, recipe="ice-platform")
            P.add("bulk-inserter", u + 3 if pick == E else u + 7, cy + 1, d=pick)     # ice straight from the separation plant
            P.add("fast-inserter", a + 1, cy - 1, d=S)         # platforms out
            P.add("passive-provider-chest", a + 1, cy - 2)
    for u in US[1:]:
        P.add("substation", u + 5, cy - 2, 2, 2)
    P.add("substation", US[0] + 2, cy - 7, 2, 2)
    P.add("fast-inserter", US[0] + 6, cy - 1, d=S)             # ice for the rest of the base (gated in config)
    P.add("passive-provider-chest", US[0] + 6, cy - 2)
    P.add("offshore-pump", US[0] - 1, cy - 4, d=W)             # needs ocean 3 wide and 2 deep in front: the inlet at -20..-17, -34..-31
    for x in range(US[0], US[0] + 4):
        P.pipe(x, cy - 4)
    for x in range(US[0] + 1, US[-1] + 10):
        P.pipe(x, cy + 3)                                      # the ammonia main
    rx = RX
    bx = US[1] + 11                                            # the branch leaves the main under a heat column (a T under a machine has no heat)
    for t in [(bx, cy + 4), (bx, cy + 5)] + [(x, cy + 5) for x in range(rx + 1, bx)] + [(rx + 1, cy + 6), (rx + 1, cy + 7)]:
        P.pipe(*t)                                             # ammonia branch down into the rocket fuel plant
    P.pipe(rx - 1, cy + 7)                                     # water: melter -> rocket fuel plant (one tile, both ports)
    P.add("chemical-plant", rx - 1, cy + 8, 3, 3, N, recipe="ammonia-rocket-fuel")
    P.add("chemical-plant", rx - 4, cy + 5, 3, 3, W, recipe="ice-melting")
    P.add("fast-inserter", rx - 5, cy + 6, d=W)                # ice for the melter
    P.add("requester-chest", rx - 6, cy + 6)
    P.add("fast-inserter", rx - 2, cy + 9, d=W)                # solid fuel for the rocket fuel plant
    P.add("requester-chest", rx - 3, cy + 9)
    P.add("substation", rx - 4, cy + 11, 2, 2)                 # without it the three inserters here stood at no_power and the whole works starved
    P.add("fast-inserter", rx, cy + 11, d=N)                   # rocket fuel out (south side: the landing pad is east)
    P.add("passive-provider-chest", rx, cy + 12)
    return P


def clear_first_layout():
    """One-off (2026-11-14): the first layout (pitch 10, one maker a separation plant) is taken down for the pitch 12 one. Only pieces this
    script placed stand in the box; chest contents go to the ice chest at (-15.5,-27.5), which stays."""
    print(lua("local s=game.surfaces.aquilo local keep=s.find_entities_filtered{name='passive-provider-chest',position={-15.5,-27.5},radius=0.4}[1] local n=0 "
              "local names={'heat-pipe','pipe','pipe-to-ground','chemical-plant','assembling-machine-3','bulk-inserter','fast-inserter','substation','passive-provider-chest'} "
              "for _,a in pairs({{{-15.1,-34.5},{20,-25.6}},{{5.2,-24.8},{6.8,-23.2}}}) do for _,e in pairs(s.find_entities_filtered{area=a,name=names,force='player'}) do "
              "if e.type=='logistic-container' and keep then for _,it in pairs(e.get_inventory(defines.inventory.chest).get_contents()) do keep.insert{name=it.name,count=it.count,quality=it.quality} end end "
              "if e.type=='assembling-machine' then for _,inv in pairs({defines.inventory.crafter_input,defines.inventory.crafter_output}) do for _,it in pairs(e.get_inventory(inv).get_contents()) do if keep then keep.insert{name=it.name,count=it.count,quality=it.quality} end end end end "
              "e.destroy{raise_destroy=true} n=n+1 end end rcon.print('removed '..n)"))


BOX_P = (-24, -40, 34, -8)


def platforms(apply):
    grid = fetch(BOX_P)
    net = heat_tiles(BOX_P)
    P = platform_plan()
    extra = [(x, CY - 5) for x in range(US[0], US[-1] + 12)]
    build(P, grid, net, apply, extra)


# ---------------------------------------------------------------- cryogenic science line
# North-west field. Stack facing north: science plant (-27..-23, -41..-37) straight on top of the cooling plant (-27..-23, -36..-32): the
# cooler's cold output (top, x-2) meets the science plant's input (bottom, x-2) with no pipe. The hot fluoroketone returns by the pipe
# column x=-28 (science top-left -> cooler bottom-left); the fluoroketone plant (-35..-31, -42..-38, facing east) feeds the top of that
# column. Fluorine comes down the column x=-36 from the pumpjack on the vent (-36..-34, -72..-70) over an ice platform causeway
# (x -36..-35, y -64..-49) with its heat pipe at x=-35; ammonia comes by pipe from the west end of the platform works' main.
SX, SY = -25, -39          # centre tile of the science plant
FLX = -36                  # fluorine column
CAUSEWAY = [(x, y) for y in range(-64, -48) for x in (FLX, FLX + 1)]
BOX_S = (-46, -76, -8, -20)


def route(grid, start, goal, blocked, shy):
    """Cheapest 4-connected pipe path over usable free tiles; never beside a tile in `shy` (other fluids) except at its two ends."""
    import heapq
    shy_adj = {n for t in shy for n in adj(t)} | set(shy)
    best, prev, heap = {start: 0}, {start: None}, [(0, start)]
    while heap:
        d, u = heapq.heappop(heap)
        if u == goal:
            break
        if d > best[u]:
            continue
        for n in adj(u):
            c = grid.get(n)
            if n != goal and (c not in USABLE or n in blocked or n in shy_adj):
                continue
            nd = d + (1.3 if c == "i" else 1)
            if nd < best.get(n, 1e9):
                best[n] = nd
                prev[n] = u
                heapq.heappush(heap, (nd, n))
    if goal not in prev:
        return []
    out, c = [], goal
    while c is not None:
        out.append(c)
        c = prev[c]
    return out[::-1]


def science_plan(grid):
    P = Plan()
    sx, sy = SX, SY
    P.add("cryogenic-plant", sx - 2, sy - 2, 5, 5, N, recipe="cryogenic-science-pack")
    P.add("cryogenic-plant", sx - 2, sy + 3, 5, 5, N, recipe="fluoroketone-cooling")
    fx, fy = sx - 8, sy - 1
    P.add("cryogenic-plant", fx - 2, fy - 2, 5, 5, E, recipe="fluoroketone")
    hot = [(x, sy - 3) for x in range(fx + 3, sx - 1)] + [(sx - 3, y) for y in range(sy - 2, sy + 9)] + [(sx - 2, sy + 8)]
    for t in hot:
        P.pipe(*t)
    P.add("fast-inserter", sx + 3, sy, d=E)                    # ice and lithium plate in (rows sy-2, sy-1 stay open for the heat line)
    P.add("requester-chest", sx + 4, sy)
    P.add("fast-inserter", sx + 3, sy + 2, d=W)                # packs out
    P.add("passive-provider-chest", sx + 4, sy + 2)
    P.add("fast-inserter", fx, fy + 3, d=S)                    # solid fuel and lithium for the fluoroketone
    P.add("requester-chest", fx, fy + 4)
    P.add("heating-tower", fx, fy + 7, 3, 3)                   # a second heat source at this end of the network
    P.add("fast-inserter", fx + 1, fy + 6, d=N)
    P.add("requester-chest", fx + 1, fy + 5)
    P.add("roboport", sx - 3, sy + 10, 4, 4)
    P.add("substation", sx - 6, sy - 6, 2, 2)                  # not on rows sy-5, sy-4 east of x=sx-3: the heat line to the hot run passes there
    P.add("substation", sx + 2, sy + 10, 2, 2)
    P.add("substation", FLX + 2, -47, 2, 2)
    P.add("substation", FLX + 2, -68, 2, 2)
    P.add("pumpjack", FLX, -72, 3, 3, S)                       # the vent at (-34.5,-70.5); facing south its output is the tile (-36,-69)
    fl = [(FLX, y) for y in range(-69, fy - 1)]
    for t in fl:                                               # one underground hop (-47 to -45): the fluorine and ammonia columns would
        if t[1] == -47:                                        # otherwise wall off everything west of x=-36 from the heat network
            P.add("pipe-to-ground", t[0], t[1], d=N)
        elif t[1] == -45:
            P.add("pipe-to-ground", t[0], t[1], d=S)
        elif t[1] != -46:
            P.pipe(*t)
    start, goal = (US[0], CY + 3), (fx - 3, fy)
    path = route(grid, start, goal, P.occupied() | {(US[0], CY + 4), (FLX, fy + 10), (FLX, fy + 9)}, set(hot) | set(fl))     # (FLX, fy+10): a corner no heat pipe can reach
    if not path:
        print("no ammonia route found: taken as standing (the router sees the pipes of an earlier run as obstacles)")
    hop = [(fx + 1, fy + 11), (fx + 1, fy + 12), (fx + 1, fy + 13)]      # the ammonia column cuts the science block off from the hot side: one hop
    P.add("pipe-to-ground", hop[0][0], hop[0][1], d=N)
    P.add("pipe-to-ground", hop[2][0], hop[2][1], d=S)
    for t in path:
        if t not in hop:
            P.pipe(*t)
    # a heating tower passes heat only at the middle of each side (the tile two out from its centre), not along its whole edge
    extra = [(FLX + 1, y) for y in range(-69, fy - 2)] + [(FLX, -46), hop[1], (fx + 3, fy + 8)]
    return P, extra


def causeway(apply):
    """Lay the Captain's own ice platform ghosts on the causeway tiles, paying one ice platform from the works' chests for each."""
    tiles = ",".join("{%d,%d}" % t for t in CAUSEWAY)
    print(lua("local s=game.surfaces.aquilo local src={} for _,e in pairs(s.find_entities_filtered{name={'passive-provider-chest','assembling-machine-3'},area={{%d,%d},{%d,%d}}}) do "
              "src[#src+1]=e.type=='assembling-machine' and e.get_inventory(defines.inventory.crafter_output) or e.get_inventory(defines.inventory.chest) end "
              "local function take() for _,inv in pairs(src) do if inv.remove({name='ice-platform',count=1})==1 then return true end end return false end "
              "local done,nog,short=0,0,0 for _,p in pairs({%s}) do local t=s.get_tile(p[1],p[2]) if t.name=='ice-platform' then done=done+1 else "
              "local g=s.find_entities_filtered{type='tile-ghost',position={p[1]+0.5,p[2]+0.5},radius=0.3}[1] if not g then nog=nog+1 "
              "elseif %s and take() then g.revive{raise_revive=true} done=done+1 else short=short+1 end end end "
              "rcon.print('causeway tiles laid '..done..' of %d, no ghost '..nog..', waiting for platforms '..short)"
              % (US[0], CY - 3, US[-1] + 11, CY + 3, tiles, "true" if apply else "false", len(CAUSEWAY))))


def science(apply):
    lua("local h=game.surfaces.aquilo.find_entities_filtered{name='heat-pipe',position={%s,%s},radius=0.3}[1] if h and %s then h.destroy{raise_destroy=true} end rcon.print('ok')" % (US[0] + .5, CY + 3.5, "true" if apply else "false"))
    grid = fetch(BOX_S)
    grid[(US[0], CY + 3)] = "S"
    net = heat_tiles(BOX_S)
    net.discard((US[0], CY + 3))
    P, extra = science_plan(grid)
    build(P, grid, net, apply, extra)


def science_config():
    sx, sy = SX, SY
    fx, fy = sx - 8, sy - 1
    code = "local s=game.surfaces.aquilo local o={} "
    code += ask(sx + 4.5, sy + .5, {"ice": 100, "lithium-plate": 40})
    code += ask(fx + .5, fy + 4.5, {"solid-fuel": 10, "lithium": 6})
    code += ask(fx + 1.5, fy + 5.5, {"solid-fuel": 100})
    # a tower burns flat out until the whole network (1 MJ a degree a heat pipe) stands at 1,000 degrees: the two extra towers only get
    # fuel while the stock is comfortable, so the rocket fuel plant (the ammonia sink) and the first tower are served first
    code += cond(fx + 1.5, fy + 6.5, "solid-fuel", ">", 2500)
    # place_entities leaves a machine facing north and it does not turn without a recipe: turn the fluoroketone plant east now
    code += "do local e=s.find_entities_filtered{name='cryogenic-plant',position={%s,%s},radius=1}[1] e.direction=defines.direction.east o[#o+1]='fluoroketone plant faces '..e.direction end " % (fx + .5, fy + .5)
    code += "rcon.print(table.concat(o,' | '))"
    print(lua(code))


# ---------------------------------------------------------------- second power set
# One turbine (11 MW epic) carried the base; the works and the science line need more. A third heating tower (-20..-18, -23..-21) with a
# heat exchanger (-16..-14, -22..-21, facing south, heat in from the pipe above its middle), the turbine straight under it and its own
# ice melter (-12..-10, -22..-20) whose water meets the exchanger's east port at the pipe (-13,-22). Same arrangement as aquilo_base.
PX, PY = -16, -22
BOX_W = (-26, -28, 0, -12)


def power_plan():
    P = Plan()
    ex, ey = PX, PY
    P.add("heating-tower", ex - 4, ey - 1, 3, 3)
    P.add("fast-inserter", ex - 3, ey + 2, d=S)
    P.add("requester-chest", ex - 3, ey + 3)
    P.add("heat-exchanger", ex, ey, 3, 2, S)
    P.add("steam-turbine", ex, ey + 2, 3, 5, N)
    P.pipe(ex + 3, ey)
    P.add("chemical-plant", ex + 4, ey, 3, 3, E, recipe="ice-melting")
    P.add("fast-inserter", ex + 7, ey + 1, d=E)
    P.add("requester-chest", ex + 8, ey + 1)
    P.add("substation", ex + 4, ey + 4, 2, 2)
    return P, [(ex - 1, ey), (ex - 1, ey - 1), (ex, ey - 1), (ex + 1, ey - 1), (ex - 3, ey - 2)]     # the last: the tower's north middle, onto the hot row


def power(apply):
    grid = fetch(BOX_W)
    net = heat_tiles(BOX_W)
    P, extra = power_plan()
    build(P, grid, net, apply, extra)
    if apply:
        code = "local s=game.surfaces.aquilo local o={} " + ask(PX - 2.5, PY + 3.5, {"solid-fuel": 100}) + ask(PX + 8.5, PY + 1.5, {"ice": 200})
        code += cond(PX - 2.5, PY + 2.5, "solid-fuel", ">", 1000)
        code += ("for _,q in pairs({{'heat-exchanger',%s,%s,defines.direction.south},{'chemical-plant',%s,%s,defines.direction.east}}) do local e=s.find_entities_filtered{name=q[1],position={q[2],q[3]},radius=0.6}[1] "
                 "e.direction=q[4] o[#o+1]=q[1]..' faces '..e.direction end rcon.print(table.concat(o,' | '))" % (PX + 1.5, PY + 1, PX + 5.5, PY + 1.5))
        print(lua(code))


# ---------------------------------------------------------------- lithium from brine
# Pumpjack on the brine well (-52.5,58.5) on the south-west island -> pipe north (over ice platform stepping stones laid like the fluorine
# causeway, heat pipe beside it all the way) -> lithium plant (chemical plant, -23..-21, -20..-18, facing north: brine in at (-23,-21),
# ammonia in at (-21,-21) by a branch from the science line's ammonia pipe at (-21,-26)). Holmium plate comes by robot from the pad
# (chest (-23,-16)), lithium leaves by the red chest (-21,-16) for the furnace (plates) and the fluoroketone plant.
BRINE = (-54, 57)          # top-left tile of the pumpjack: the well at (-52.5,58.5); the one at (-44.5,59.5) has two lithium icebergs on it
LIX, LIY = -23, -20        # top-left tile of the lithium plant
BOX_B = (-62, -30, -8, 64)
ROUTE_FILE = __file__.replace("aquilo_cryo.py", "aquilo_brine_route.json")


def brine_route(grid):
    """The pipe path, computed once and kept in aquilo_brine_route.json (a later run sees its own pipes as obstacles). Turns are dear:
    long straight legs, because every right turn needs an underground hop four tiles before it (see brine_plan)."""
    import heapq
    import os
    if os.path.exists(ROUTE_FILE):
        return [tuple(t) for t in json.load(open(ROUTE_FILE))]
    start, goal = (BRINE[0], BRINE[1] + 3), (LIX, LIY - 1)
    keep_off = {(LIX + 2, y) for y in range(-26, LIY)} | {(LIX + 1, LIY - 1)}
    keep_off |= {n for t in keep_off for n in adj(t)}
    keep_off |= {(LIX + a, LIY + b) for a in range(-1, 4) for b in range(0, 6)}        # the plant, its inserters and chests
    keep_off |= {(BRINE[0] + a, BRINE[1] + b) for a in range(3) for b in range(3)}
    s0 = (start, (0, 0))
    best, prev, heap = {s0: 0}, {s0: None}, [(0, s0)]
    end = None
    while heap:
        d, st = heapq.heappop(heap)
        u, du = st
        if u == goal:
            end = st
            break
        if d > best[st]:
            continue
        for n in adj(u):
            c = grid.get(n)
            if n != goal and (c is None or c == "#" or n in keep_off):
                continue
            dn = (n[0] - u[0], n[1] - u[1])
            nd = d + (5 if c == "." else 1.2 if c in "i~" else 1) + (0 if du in ((0, 0), dn) else 14)
            ns = (n, dn)
            if nd < best.get(ns, 1e9):
                best[ns] = nd
                prev[ns] = st
                heapq.heappush(heap, (nd, ns))
    if end is None:
        return []
    out, c = [], end
    while c is not None:
        out.append(c[0])
        c = prev[c]
    out = out[::-1]
    json.dump(out, open(ROUTE_FILE, "w"))
    return out


DIRC = {(0, -1): N, (1, 0): E, (0, 1): S, (-1, 0): W}


def brine_plan(grid):
    """Heat runs on the RIGHT of the pipe (seen along the flow). A left turn is fine (the heat goes round the outside); at a right turn the
    corner pipe has no heat pipe beside it, so four tiles before it the pipe dives for one tile and the heat crosses to the left side."""
    P = Plan()
    path = brine_route(grid)
    if not path:
        print("no brine route")
        return P, [], []
    P.add("pumpjack", BRINE[0], BRINE[1], 3, 3, S)             # facing south its output is the tile (x, y+3)
    P.nohalo = set(path)                                       # the line gets its heat pipe on one side only (below), not a halo on both
    pset = set(path)
    step = [(b[0] - a[0], b[1] - a[1]) for a, b in zip(path, path[1:])]
    right = lambda d: (-d[1], d[0])
    heat, ptg, gaps, bad = set(), {}, set(), []
    for k, p in enumerate(path):
        din = step[k - 1] if k > 0 else step[0]
        dout = step[k] if k < len(step) else step[-1]
        n1, n2 = right(din), right(dout)
        heat |= {(p[0] + n1[0], p[1] + n1[1]), (p[0] + n2[0], p[1] + n2[1])}
        if n1 != n2:
            if dout == n1:                                      # right turn: the hop
                if k < 4 or any(step[k - m] != din for m in (1, 2, 3, 4)):
                    bad.append(p)
                    continue
                a, g, b = path[k - 3], path[k - 2], path[k - 1]
                ptg[a] = DIRC[(-din[0], -din[1])]
                ptg[b] = DIRC[din]
                gaps.add(g)
                heat |= {g, (g[0] - n1[0], g[1] - n1[1]), (b[0] - n1[0], b[1] - n1[1]), (p[0] - n1[0], p[1] - n1[1])}
            else:                                               # left turn: round the outside
                heat.add((p[0] + n1[0] + n2[0], p[1] + n1[1] + n2[1]))
    if bad:
        print("right turns with a leg shorter than four tiles before them (no room for the hop):", bad)
    for t in path:
        if t in ptg:
            P.add("pipe-to-ground", t[0], t[1], d=ptg[t])
        elif t not in gaps:
            P.pipe(*t)
    heat -= pset - gaps
    heat.add((BRINE[0] - 1, BRINE[1] + 2))                     # the pumpjack's own heat pipe, beside the line's first one
    comp = heat
    water = sorted(t for t in pset | comp if grid.get(t) == ".")
    P.add("chemical-plant", LIX, LIY, 3, 3, N, recipe="lithium")
    for y in range(-25, LIY):
        P.pipe(LIX + 2, y)                                     # ammonia branch from the T at (LIX+2, -26)
    P.add("fast-inserter", LIX, LIY + 3, d=S)                  # holmium plate in
    P.add("requester-chest", LIX, LIY + 4)
    P.add("fast-inserter", LIX + 2, LIY + 3, d=N)              # lithium out
    P.add("passive-provider-chest", LIX + 2, LIY + 4)
    # a substation every 18 tiles of pipe, on land on the left of it
    occ = P.occupied() | comp
    last = None
    for k, (x, y) in enumerate(path):
        if last is not None and k - last < 18 and k != 3:
            continue
        for dx, dy in ((2, 0), (-3, 0), (0, 2), (0, -3), (2, 2), (-3, -3), (3, 0), (-4, 0), (0, 3), (0, -4)):
            sq = {(x + dx + a, y + dy + b) for a in (0, 1) for b in (0, 1)}
            if all(grid.get(t) in USABLE for t in sq) and not (sq & occ) and not any(n in pset for t in sq for n in adj(t)):
                P.add("substation", x + dx, y + dy, 2, 2)
                occ |= sq
                last = k
                break
    return P, sorted(comp), water


def brine(apply, lay):
    grid = fetch(BOX_B)
    P, comp, water = brine_plan(grid)
    print("pipe tiles:", len([e for e in P.ents if e["name"] == "pipe"]), "ocean tiles that need an ice platform first:", len(water))
    json.dump(water, open(ROUTE_FILE.replace("route", "water"), "w"))       # for _aq_lay.py (cheap polling; a map fetch every few seconds stalls the server)
    if water:
        tiles = ",".join("{%d,%d}" % t for t in water)
        print(lua("local s=game.surfaces.aquilo local src={} for _,e in pairs(s.find_entities_filtered{name={'passive-provider-chest','assembling-machine-3'},area={{%d,%d},{%d,%d}}}) do "
                  "src[#src+1]=e.type=='assembling-machine' and e.get_inventory(defines.inventory.crafter_output) or e.get_inventory(defines.inventory.chest) end "
                  "local function take() for _,inv in pairs(src) do if inv.remove({name='ice-platform',count=1})==1 then return true end end return false end "
                  "local done,nog,short=0,0,0 for _,p in pairs({%s}) do local g=s.find_entities_filtered{type='tile-ghost',position={p[1]+0.5,p[2]+0.5},radius=0.3}[1] "
                  "if not g then nog=nog+1 elseif %s and take() then g.revive{raise_revive=true} done=done+1 else short=short+1 end end "
                  "rcon.print('stepping stones laid now '..done..', no ghost '..nog..', waiting for platforms '..short)"
                  % (US[0], CY - 3, US[-1] + 11, CY + 3, tiles, "true" if lay else "false")))
        return
    if apply:
        print(lua("local s=game.surfaces.aquilo local t={} for x=%d,%d do for y=%d,%d do if s.get_tile(x,y).name:find('ice',1,true) then t[#t+1]={name='concrete',position={x,y}} end end end s.set_tiles(t) rcon.print('paved under the pumpjack '..#t)"
                  % (BRINE[0], BRINE[0] + 2, BRINE[1], BRINE[1] + 2)))
        print(lua("local s=game.surfaces.aquilo local n=0 for _,p in pairs({{%s,-24.5},{%s,-23.5}}) do local h=s.find_entities_filtered{name='heat-pipe',position=p,radius=0.3}[1] if h then h.destroy{raise_destroy=true} n=n+1 end end rcon.print('heat pipes lifted for the ammonia branch '..n)"
                  % (LIX + 2.5, LIX + 2.5)))
        grid = fetch(BOX_B)
    net = heat_tiles(BOX_B)
    build(P, grid, net, apply, comp, clear=False)          # never clear here: lithium icebergs stand beside the well
    if apply:
        code = "local s=game.surfaces.aquilo local o={} " + ask(LIX + .5, LIY + 4.5, {"holmium-plate": 20})
        code += "rcon.print(table.concat(o,' | '))"
        print(lua(code))


def cond(x, y, item, comp, n):
    return ("do local e=s.find_entities_filtered{type='inserter',position={%s,%s},radius=0.4}[1] local cb=e.get_or_create_control_behavior() cb.connect_to_logistic_network=true "
            "cb.logistic_condition={comparator='%s',first_signal={type='item',name='%s'},constant=%d} o[#o+1]=e.name..' %s %s %d' end " % (x, y, comp, item, n, item, comp, n))


def ask(x, y, reqs):
    slots = " ".join("sec.set_slot(%d,{value={type='item',name='%s',quality='normal'},min=%d})" % (i + 1, k, v) for i, (k, v) in enumerate(reqs.items()))
    return ("do local c=s.find_entities_filtered{name='requester-chest',position={%s,%s},radius=0.4}[1] local pt=c.get_logistic_point(defines.logistic_member_index.logistic_container) "
            "local sec=pt.get_section(1) or pt.add_section() %s o[#o+1]='chest %s,%s asks %s' end " % (x, y, slots, x, y, "+".join(reqs)))


def config():
    rx = RX
    code = "local s=game.surfaces.aquilo local o={} "
    code += ask(rx - 5.5, CY + 6.5, {"ice": 50})
    code += ask(rx - 2.5, CY + 9.5, {"solid-fuel": 100})
    code += cond(US[0] + 6.5, CY - .5, "ice", "<", 1500)
    code += cond(40.5, -3.5, "ice", ">", 4000)             # the recycler ice sink runs on true surplus only
    code += ("for _,e in pairs(s.find_entities_filtered{name='assembling-machine-3',area={{%d,%d},{%d,%d}}}) do e.direction=defines.direction.south o[#o+1]='assembler '..e.position.x..' faces '..e.direction end "
             % (US[0], CY, US[-1] + 11, CY + 3))            # place_entities leaves a fluid assembler facing north: turn it after the recipe is set
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
    if step == "clear_first_layout":
        clear_first_layout()
    elif step == "platforms":
        platforms(apply)
    elif step == "config":
        config()
    elif step == "causeway":
        causeway(apply)
    elif step == "science":
        science(apply)
    elif step == "power":
        power(apply)
    elif step == "brine":
        brine(apply, "--lay" in sys.argv)
    elif step == "science_config":
        science_config()
    elif step == "status":
        status()


if __name__ == "__main__":
    main()
