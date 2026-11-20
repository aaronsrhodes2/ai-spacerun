#!/usr/bin/env python3
"""Edgerunner: join the four thruster rows to the fuel and oxidizer tanks (the Captain, 2026-11-20: "Yes, hook them up").

What stood on 2026-11-20: two fuel plants and two oxidizer plants at the stern, each pair on a small pipe ring; two blocks of 75 tanks
(west x -50..-15, east x 15..51, y 163..185), empty and joined to nothing; four stepped rows of 12 thrusters (stern east and west,
flank east and west), each with one pipe run per fluid, joined to nothing.

The feed, per fluid (fuel = west block, oxidizer = east block; the fuel ring is beside the west block, the oxidizer ring beside the east):
  ring -> tank block -> one manifold of pipes -> at each row a PUMP -> the row's own pipe run.
  * Each pump is wired green to the hub and runs while signal-V < VMAX (the ship's speed limiter, as the two old pumps at y 286).
  * The pump also cuts the pipeline: a pipeline may span 320 tiles at most, and tanks-to-flank-thrusters is 440.
The route is found on a tile grid read from the game (Dijkstra): free deck is cheap, new deck costs more, obstacles are passed by
underground pipe (up to 9 tiles between the ends, every one of them deck: an underground pipe does not join across open space). A new pipe never stands beside a pipe, tank, thruster or fluid machine that is not its
own (pipes join anything they touch). New deck is refused behind a thruster (88 tiles south of it) and near an asteroid collector.

Steps: plan (routes, saved to snapshots/edge_feed_plan.json) | deck (tile ghosts for the new deck) | build [--apply] | wire | status | undo (takes the saved plan's pieces out again)
Usage: edge_feed.py plan ; edge_feed.py deck ; edge_feed.py build --apply ; edge_feed.py wire ; edge_feed.py status"""
import heapq
import json
import os
import sys

import triangle_miner as TM
from _game import tools

L = tools["run_lua"]
X0, X1, Y0, Y1 = -270, 270, -150, 200
VMAX = 30
PLAN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "snapshots", "edge_feed_plan.json")
DIRS = ((0, -1), (1, 0), (0, 1), (-1, 0))            # N E S W
FDIR = (0, 4, 8, 12)                                 # the game's direction numbers for the same
MAXGAP = 9                                           # tiles between the two ends of an underground pipe
FL = {"thruster-fuel": "f", "thruster-oxidizer": "x"}

# one row of the grid per line, each line led by '|' so that leading blanks survive.
# ' ' open space, '.' free deck, '#' something stands there, 'K' collector, 'F' a machine with a fluid box, 'H' thruster,
# pipes, undergrounds and tanks are not in the grid: they come as a list with their segment id.
GRID = (TM.AT + "local x0,y0,x1,y1=%d,%d,%d,%d local g={} for y=y0,y1 do g[y]={} for x=x0,x1 do g[y][x]=(s.get_tile(x,y).name=='empty-space') and ' ' or '.' end end "
        "for _,e in pairs(s.find_entities_filtered{area={{x0,y0},{x1+1,y1+1}}}) do local ty=e.type if ty~='item-entity' and ty~='tile-ghost' and ty~='pipe' and ty~='pipe-to-ground' and ty~='storage-tank' then "
        "local c='#' if ty=='thruster' then c='H' elseif ty=='asteroid-collector' then c='K' elseif e.fluids_count>0 then c='F' end local b=e.bounding_box "
        "for y=math.floor(b.left_top.y+0.01),math.ceil(b.right_bottom.y-0.01)-1 do for x=math.floor(b.left_top.x+0.01),math.ceil(b.right_bottom.x-0.01)-1 do if g[y] and g[y][x] then g[y][x]=c end end end end end "
        "local o={} for y=y0,y1 do local r={} for x=x0,x1 do r[#r+1]=g[y][x] end o[#o+1]='|'..table.concat(r) end rcon.print(table.concat(o,string.char(10)))")

# every pipe, underground pipe and tank: "kind,x0,y0,x1,y1,segment,fluid;" (tile box)
PIPES = (TM.AT + "local o={} for _,e in pairs(s.find_entities_filtered{type={'pipe','pipe-to-ground','storage-tank'}}) do local ok,id=pcall(function() return e.get_fluid_segment_id(1) end) local f=e.get_fluid(1) local ff=e.get_fluid_filter(1) local b=e.bounding_box "
         "o[#o+1]=((e.type=='pipe' and 'p') or (e.type=='pipe-to-ground' and 'u') or 't')..','..math.floor(b.left_top.x+0.01)..','..math.floor(b.left_top.y+0.01)..','..(math.ceil(b.right_bottom.x-0.01)-1)..','..(math.ceil(b.right_bottom.y-0.01)-1)..','..tostring(ok and id or 0)..','..((f and f.name) or (ff and ff.name) or '-') end rcon.print(table.concat(o,';'))")

THR = TM.AT + "local o={} for _,t in pairs(s.find_entities_filtered{type='thruster'}) do local a,b=0,0 pcall(function() a=t.get_fluid_segment_id(1) b=t.get_fluid_segment_id(2) end) o[#o+1]=t.position.x..','..t.position.y..','..a..','..b end rcon.print(table.concat(o,';'))"


def read():
    rows = []
    for y in range(Y0, Y1 + 1, 30):
        r = L(GRID % (X0, y, X1, min(Y1, y + 29)))
        rows += [ln[1:] for ln in r.split("\n") if ln.startswith("|")]
    grid = {}
    for j, row in enumerate(rows):
        for i, c in enumerate(row):
            grid[(X0 + i, Y0 + j)] = c
    pipes = []
    for rec in L(PIPES).strip().split(";"):
        if rec:
            k, a, b, c, d, seg, fl = rec.split(",")
            pipes.append((k, int(a), int(b), int(c), int(d), int(seg), fl))
    thr = [tuple(float(v) for v in t.split(",")) for t in L(THR).strip().split(";") if t]
    return grid, pipes, thr


class World:
    def __init__(self):
        self.grid, pipes, self.thr = read()
        self.ugends = set()                  # tiles of underground pipe ends, standing or planned: no new underground may pass over one
        self.owner = {}                      # tile -> segment id of the pipe / tank on it
        self.segtiles = {}                   # segment -> pipe tiles (not tanks)
        self.segfluid = {}
        for k, a, b, c, d, seg, fl in pipes:
            for x in range(a, c + 1):
                for y in range(b, d + 1):
                    self.owner[(x, y)] = seg
            if k == "p":
                self.segtiles.setdefault(seg, []).append((a, b))
            elif k == "u":
                self.ugends.add((a, b))
            if fl != "-":
                self.segfluid[seg] = fl
        self.new = {}                        # tile -> net name, for what this plan adds (pipes, undergrounds, pumps)
        self.span = set()                    # (tile, axis) under an underground run of this plan
        self.nodeck = set()                  # open space where deck must not be laid
        for x, y, _, _ in self.thr:
            for tx in range(int(x - 2), int(x + 2)):
                for ty in range(int(y + 2.5), int(y + 2.5) + 89):
                    self.nodeck.add((tx, ty))
        for (x, y), c in self.grid.items():
            if c == "K":
                for dx in range(-6, 7):
                    for dy in range(-6, 7):
                        self.nodeck.add((x + dx, y + dy))

    def seg_at(self, x, y):
        return self.owner.get((int(x - 0.5) if x % 1 else int(x), int(y - 0.5) if y % 1 else int(y)))

    def free(self, t, own, net):
        """May a pipe of `net` (whose own segments are `own`) stand on tile t? Returns 0 no, 1 on deck, 2 on new deck."""
        c = self.grid.get(t)
        if c is None or t in self.owner or t in self.new:
            return 0
        if c == " ":                     # new deck (a bridge across open space rings it: the hub refuses the closing tile, `deck` forces it,
            if t in self.nodeck:         #  which the Captain allows, 2026-11-20)
                return 0
        elif c != ".":
            return 0
        for dx, dy in DIRS:
            n = (t[0] + dx, t[1] + dy)
            o = self.owner.get(n)
            if o is not None and o not in own:
                return 0
            if self.new.get(n, net) != net:
                return 0
            if self.grid.get(n) in ("H", "F"):
                return 0
        return 2 if c == " " else 1

    def route(self, net, own, starts, goals):
        """Dijkstra from the tiles `starts` (free tiles beside the net) to any tile of `goals`. State (tile, dir, must-go-straight)."""
        pq, best, prev = [], {}, {}
        for t, d in starts:
            k = self.free(t, own, net)
            if k:
                st = (t, d, 0)
                best[st] = 1 if k == 1 else 3
                heapq.heappush(pq, (best[st], st))
        while pq:
            cost, st = heapq.heappop(pq)
            if cost > best.get(st, 1e18):
                continue
            t, d, straight = st
            if t in goals and not straight:
                path = [st]
                while st in prev:
                    st = prev[st]
                    path.append(st)
                return cost, path[::-1]
            for nd in range(4):
                if straight and nd != d:
                    continue
                if (nd + 2) % 4 == d:
                    continue
                dx, dy = DIRS[nd]
                n = (t[0] + dx, t[1] + dy)
                k = self.free(n, own, net)
                if k:
                    c2 = cost + (1 if k == 1 else 3) + (0.2 if nd != d else 0)
                    s2 = (n, nd, 0)
                    if c2 < best.get(s2, 1e18):
                        best[s2] = c2
                        prev[s2] = st
                        heapq.heappush(pq, (c2, s2))
                elif nd == d and not straight and self.grid.get(t) == ".":
                    # underground: this tile becomes the entrance, the far end must be free standing deck
                    for gap in range(1, MAXGAP + 1):
                        mid = (t[0] + dx * gap, t[1] + dy * gap)
                        if (mid, nd % 2) in self.span or mid in self.ugends or self.grid.get(mid) in (None, " "):      # an underground pipe does not cross open space
                            break
                        far = (t[0] + dx * (gap + 1), t[1] + dy * (gap + 1))
                        if self.grid.get(far) == "." and self.free(far, own, net) == 1:
                            c2 = cost + gap + 3
                            s2 = (far, nd, 1)
                            if c2 < best.get(s2, 1e18):
                                best[s2] = c2
                                prev[s2] = ("hop", st)
                                prev[("hop", st)] = st
                                heapq.heappush(pq, (c2, s2))
        return None, None


def beside(tiles):
    out = []
    for t in tiles:
        for d, (dx, dy) in enumerate(DIRS):
            out.append(((t[0] + dx, t[1] + dy), d))
    return out


def plan():
    w = World()
    # the segments: thrusters tell which row run carries what; tank blocks by place
    rows = {}                                            # (row name, fluid) -> segment
    for x, y, fseg, oseg in w.thr:
        name = ("stern" if y > 0 else "flank") + (" east" if x > 0 else " west")
        rows[(name, "f")] = int(fseg)
        rows[(name, "x")] = int(oseg)
    blocks = {"f": w.seg_at(-49.5, 165.5), "x": w.seg_at(49.5, 165.5)}
    rings = {}
    for seg, fl in w.segfluid.items():
        ts = w.segtiles.get(seg, [])
        if ts and all(160 <= t[1] <= 190 and 5 <= abs(t[0]) <= 14 for t in ts) and fl in FL and len(ts) >= 20:
            rings[FL[fl]] = seg
    print("tank blocks", blocks, "plant rings", rings)
    out = {"pipes": [], "ptg": [], "pumps": [], "deck": []}
    jobs = []
    for fl in ("f", "x"):
        jobs.append((fl, "ring", None))
    for name in ("stern west", "stern east", "flank east", "flank west"):
        for fl in (("x", "f") if name == "flank west" else ("f", "x")):      # the run nearer the hull first, or the other boxes it in
            jobs.append((fl, name, rows[(name, fl)]))
    net_tiles = {"f": set(), "x": set()}
    own = {"f": {blocks["f"], rings["f"]}, "x": {blocks["x"], rings["x"]}}
    for fl, name, rowseg in jobs:
        net = fl
        base = [t for t in w.segtiles[blocks[fl]]] + list(net_tiles[fl])
        if name == "ring":
            starts = beside(w.segtiles[rings[fl]])
            goals = {t for t, _ in beside(w.segtiles[blocks[fl]])}
            cost, path = w.route(net, own[fl], starts, goals)
            pump = None
        else:
            # where a pump can stand at the row's run: its outlet end beside a pipe T of the run, the route ends on the tile behind it
            cands = {}
            for T in w.segtiles[rowseg]:
                if name.startswith("flank") and abs(T[0]) > 140:
                    continue
                for d, (dx, dy) in enumerate(DIRS):
                    a, b, g = (T[0] + dx, T[1] + dy), (T[0] + 2 * dx, T[1] + 2 * dy), (T[0] + 3 * dx, T[1] + 3 * dy)
                    if w.grid.get(a) == "." and w.grid.get(b) == "." and a not in w.owner and b not in w.owner and a not in w.new and b not in w.new:
                        ok = True
                        for q in (a, b):                 # nothing of the other fluid in line with the pump's ends
                            for ex, ey in DIRS:
                                n = (q[0] + ex, q[1] + ey)
                                if w.new.get(n, net) != net:
                                    ok = False
                        if ok and w.free(g, own[fl] | {rowseg}, net) and w.owner.get((b[0] + dx, b[1] + dy)) is None:
                            cands[g] = (T, d, a, b)
            while True:                                  # a route may not run over the tiles of its own pump
                cost, path = w.route(net, own[fl], beside(base), set(cands))
                pump = cands.get(path[-1][0]) if path else None
                if not pump or not ({pump[2], pump[3]} & {st[0] for st in path if st[0] != "hop"}):
                    break
                del cands[path[-1][0]]
        if not path:
            print("NO ROUTE: %s %s" % (name, fl))
            continue
        npipe = nug = ndeck = 0
        i = 0
        steps = [s for s in path if s[0] != "hop"]
        hops = {id(s) for s in path if s[0] == "hop"}
        for j, st in enumerate(path):
            if st[0] == "hop":
                continue
            t, d, straight = st
            w.new[t] = net
            net_tiles[fl].add(t)
            enters = j + 1 < len(path) and path[j + 1][0] == "hop"
            if straight:                                  # far end of an underground: open side forward
                out["ptg"].append({"x": t[0] + 0.5, "y": t[1] + 0.5, "direction": FDIR[d], "net": net})
                nug += 1
                w.ugends.add(t)
                e = path[j - 2][0]
                dx, dy = DIRS[d]
                q = (e[0] + dx, e[1] + dy)
                while q != t:
                    w.span.add((q, d % 2))
                    q = (q[0] + dx, q[1] + dy)
            elif enters:                                  # entrance: open side back
                out["ptg"].append({"x": t[0] + 0.5, "y": t[1] + 0.5, "direction": FDIR[(d + 2) % 4], "net": net})
                nug += 1
                w.ugends.add(t)
            else:
                out["pipes"].append({"x": t[0] + 0.5, "y": t[1] + 0.5, "net": net})
                npipe += 1
            if w.grid[t] == " ":
                out["deck"].append(list(t))
                ndeck += 1
                w.grid[t] = "."
        if pump:
            T, d, a, b = pump
            dx, dy = DIRS[d]
            w.new[a] = net
            w.new[b] = net
            out["pumps"].append({"x": T[0] + 0.5 + 1.5 * dx, "y": T[1] + 0.5 + 1.5 * dy, "direction": FDIR[(d + 2) % 4], "net": net, "row": name})
        print("%-11s %s: cost %.0f, pipes %d, underground ends %d, new deck %d%s" % (name, "fuel" if fl == "f" else "oxidizer", cost, npipe, nug, ndeck,
                                                                                    (", pump at %.1f,%.1f" % (out["pumps"][-1]["x"], out["pumps"][-1]["y"])) if pump else ""))
    with open(PLAN, "w") as f:
        json.dump(out, f)
    print("total: pipes %d, underground ends %d, pumps %d, new deck %d -> %s" % (len(out["pipes"]), len(out["ptg"]), len(out["pumps"]), len(out["deck"]), os.path.normpath(PLAN)))
    return out


def load():
    with open(PLAN) as f:
        return json.load(f)


WIRE = (TM.AT + "local G=defines.wire_connector_id.circuit_green local n=0 for _,q in pairs({%s}) do local e=s.find_entities_filtered{type='pump',position={q[1],q[2]},radius=0.6}[1] if e then "
        "local a,b=p.hub.get_wire_connector(G,true),e.get_wire_connector(G,true) if not a.is_connected_to(b) then a.connect_to(b,false) end local cb=e.get_or_create_control_behavior() cb.circuit_enable_disable=true "
        "cb.circuit_condition={first_signal={type='virtual',name='signal-V'},comparator='<',constant=%d} n=n+1 end end rcon.print('pumps wired to the hub, run while signal-V < %d: '..n)")

STATUS = (TM.AT + "local m={} for k,v in pairs(defines.entity_status) do m[v]=k end local o={} local function sid(e,i) local ok,id=pcall(function() return e.get_fluid_segment_id(i) end) return ok and id or 0 end "
          "local tot={} for _,e in pairs(s.find_entities_filtered{type={'storage-tank','pipe','pipe-to-ground','pump','thruster'}}) do for k,v in pairs(e.get_fluid_contents()) do tot[k]=(tot[k] or 0)+v end end "
          "for k,v in pairs(tot) do o[#o+1]=k..' aboard '..math.floor(v) end "
          "for _,q in pairs({%s}) do local e=s.find_entities_filtered{type='pump',position={q[1],q[2]},radius=0.6}[1] if e then local f=e.get_fluid(1) o[#o+1]='pump '..q[1]..','..q[2]..' '..m[e.status]..' '..tostring(f and f.name)..' '..tostring(f and math.floor(f.amount)) else o[#o+1]='pump '..q[1]..','..q[2]..' MISSING' end end "
          "local h={} for _,t in pairs(s.find_entities_filtered{type='thruster'}) do local c=t.get_fluid_contents() local k=((t.position.y>0) and 'stern' or 'flank')..((t.position.x>0) and ' east' or ' west') local g=h[k] or {n=0,f=0,x=0,fs={},xs={}} h[k]=g g.n=g.n+1 "
          "if (c['thruster-fuel'] or 0)>0 then g.f=g.f+1 end if (c['thruster-oxidizer'] or 0)>0 then g.x=g.x+1 end end for k,g in pairs(h) do o[#o+1]=k..': '..g.n..' thrusters, holding fuel '..g.f..', holding oxidizer '..g.x end rcon.print(table.concat(o,string.char(10)))")


UNDO = (TM.AT + "local n=0 for _,q in pairs({%s}) do for _,e in pairs(s.find_entities_filtered{name=q[1],position={q[2],q[3]},radius=0.3}) do e.destroy() n=n+1 end end rcon.print(n)")
UNDECK = (TM.AT + "local inv=p.hub.get_inventory(defines.inventory.hub_main) local t={} for _,q in pairs({%s}) do if s.get_tile(q[1],q[2]).name=='space-platform-foundation' and s.count_entities_filtered{area={{q[1]+0.05,q[2]+0.05},{q[1]+0.95,q[2]+0.95}}}==0 then t[#t+1]={name='empty-space',position=q} end end "
          "s.set_tiles(t) local back=0 for _,x in pairs(t) do if s.get_tile(x.position[1],x.position[2]).name=='empty-space' then back=back+1 end end if back>0 then inv.insert{name='space-platform-foundation',count=back} end "
          "for _,g in pairs(s.find_entities_filtered{type='tile-ghost'}) do g.destroy() end rcon.print(back)")


def undo():
    """Takes out what the saved plan placed: its pipes, undergrounds and pumps (placed entities), then the deck laid for it where nothing
    stands, with the foundation put back in the hub (the ship's own goods, moved by script)."""
    pl = load()
    ents = [("pipe", e) for e in pl["pipes"]] + [("pipe-to-ground", e) for e in pl["ptg"]] + [("pump", e) for e in pl["pumps"]]
    n = 0
    for i in range(0, len(ents), 300):
        n += int(L(UNDO % ",".join("{'%s',%s,%s}" % (k, e["x"], e["y"]) for k, e in ents[i:i + 300])).strip())
    back = 0
    tiles = [tuple(t) for t in pl["deck"]]
    for i in range(0, len(tiles), 1500):
        back += int(L(UNDECK % ",".join("{%d,%d}" % t for t in tiles[i:i + 1500])).strip())
    print("entities removed %d, deck tiles lifted %d (foundation back in the hub)" % (n, back))


def main():
    a = sys.argv[1:]
    step = a[0] if a else "plan"
    apply = "--apply" in a
    if step == "plan":
        plan()
        return
    if step == "undo":
        undo()
        return
    pl = load()
    pumps = ",".join("{%s,%s}" % (q["x"], q["y"]) for q in pl["pumps"])
    if step == "deck":
        import edge_mirror_thrusters as M
        tiles = [tuple(t) for t in pl["deck"]]
        n = had = 0
        for i in range(0, len(tiles), 1500):
            r = L(M.GHOST % ",".join("{%d,%d}" % t for t in tiles[i:i + 1500])).split()
            n, had = n + int(r[0]), had + int(r[1])
        print("tile ghosts laid %d (already deck %d)" % (n, had))
    elif step == "build":
        q = {"quality": "legendary"}
        ents = [{"name": "pipe", "x": e["x"], "y": e["y"], "direction": 0, "params": q} for e in pl["pipes"]]
        ents += [{"name": "pipe-to-ground", "x": e["x"], "y": e["y"], "direction": e["direction"], "params": q} for e in pl["ptg"]]
        ents += [{"name": "pump", "x": e["x"], "y": e["y"], "direction": e["direction"], "params": q} for e in pl["pumps"]]
        ok, bad = TM.place(ents, apply)
        print("%s %d, refused %d" % ("placed" if apply else "would place", ok, bad))
    elif step == "wire":
        print(L(WIRE % (pumps, VMAX, VMAX)).strip())
    elif step == "status":
        print(L(STATUS % pumps).strip())
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
