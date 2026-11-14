"""power_thin.py - thin out electric poles and substations that the larger supply area and wire
reach of high-quality substations make redundant, and cut the wires of poles that supply nothing.

The Captain's order (2026-11-14): epic substations cover a much larger area, so spread the poles
apart and free the ground; do it again at the next quality (legendary). Idle poles: disconnect them
(leave them standing, wires cut, recorded) until they are needed.

Subcommands (dry run is `plan`; everything else changes the game except study/verify):
  study  [--surface S]          export poles + consumers to scripts/_power_thin_<S>.json, print counts
                                by pole type/quality, supply area, wire reach, baseline no_power;
                                writes snapshots/power_thin_baseline.json (no_power, network ids)
  plan   [--surface S] [--quality Q] [--idle cut|remove|off] [--refresh]
                                set-cover + connectivity analysis on the cached export; prints per
                                region: poles removable, idle poles / wires cut, wires to add, land
                                freed (tiles, boxes), plus the projection for the NEXT quality.
                                --quality Q projects: "if every substation were Q" (analysis only)
  apply  --surface S [--region X0 Y0 X1 Y1] [--idle cut|remove|off] [--only thin|idle|both] [--batch N] [--max-batches N]
                                re-exports the region LIVE (so new builds count), re-plans, then removes
                                in batches. Per batch: undo record first, bridging wires added BEFORE
                                the destroy (no transient split), verification (consumers still
                                covered, network ids unchanged and not split/merged, no new no_power
                                entity); any failure puts the batch back and stops the region.
  verify [--surface S]          current no_power / low_power counts and network ids vs the baseline
  undo   [--surface S] [--last N]   put removed poles back (position, quality, wires) from the log
  reconnect [--surface S] [--region X0 Y0 X1 Y1]   restore the wires of idle poles that were cut

SAFETY RULES (hard): only electric poles are ever touched. A pole is removable only if (a) every
consumer (anything with an electric energy source, accumulators, solar panels, generators,
lightning attractors, ghosts of those) it covers is still covered by another pole of the SAME
network, and (b) its neighbours stay connected through wires of the remaining poles (proof by BFS on
the geometric reach graph, then the missing wires are really created and read back). Never touched:
Aquilo, space platforms, FROZEN surfaces (Fulgora while the rod/collector swap is on), poles with a
circuit wire or a non-pole copper wire, and the skip boxes below.

Quality: geometry (supply_area_distance, max_wire_distance) is read from the prototype per pole
instance quality. Re-run `study`, `plan`, `apply` after a better quality is researched AND the kept
substations have been upgraded (scripts/upgrade_quality.py); `plan --quality legendary` shows what
that round would free before you spend the items.

Run:  cd /d/Aaron/development/AI-factorio && export PYTHONIOENCODING=utf-8 PYTHONPATH=scripts
      python -u scripts/power_thin.py plan --surface nauvis 2>&1 | grep -v -E "INFO|tunnel|aaron_s|27015"
"""
import argparse
import json
import math
import sys
import time
from collections import defaultdict, deque
from pathlib import Path

from _game import tools

HERE = Path(__file__).resolve().parent
SNAP = HERE.parent / "snapshots"
WIRES = SNAP / "power_thin_wires.json"
UNDO = SNAP / "power_thin_undo.json"
BASE = SNAP / "power_thin_baseline.json"

EPS = 0.05          # overlap needed between supply area and a collision box
REACH_MARGIN = 0.4  # planned wires must be this much shorter than the reach
BFS_LIMIT = 4000    # connectivity proof gives up (pole kept) beyond this many poles
EDIT_SURFACES = ["nauvis", "vulcanus", "gleba"]
FROZEN = {"fulgora"}                       # analysis only until the coordinator says otherwise
NEVER_PREFIX = ("platform", "aquilo")      # read-only always
SKIP_BOXES = {                             # (x0, y0, x1, y1), padded by SKIP_PAD
    "nauvis": [(-367, -235, -288, -190, "replicator"), (-231, -186, -219, -148, "status wall")],
}
SKIP_PAD = 14
EXTRA_SKIP = []     # filled from --skip
CRITICAL_TYPES = "'generator','solar-panel','accumulator','lightning-attractor','fusion-generator','fusion-reactor','electric-energy-interface'"


def L(code):
    assert "\n" not in code and len(code) < 65000, len(code)
    return tools["run_lua"](code).strip()


def log(*a):
    print(*a, flush=True)


# ----------------------------------------------------------------------------- export
def get_geom():
    code = ("local o={} for n,p in pairs(prototypes.get_entity_filtered{{filter='type',type='electric-pole'}}) do "
            "for q,_ in pairs(prototypes.quality) do o[#o+1]=n..' '..q..' '..p.get_supply_area_distance(q)..' '..p.get_max_wire_distance(q)..' '..p.tile_width..' '..p.tile_height end end "
            "rcon.print(table.concat(o,'\\n'))")
    g = {}
    lv = {}
    for ln in L(code).split("\n"):
        t = ln.split()
        if len(t) == 6:
            g[(t[0], t[1])] = dict(d=float(t[2]), w=float(t[3]), tw=int(t[4]), th=int(t[5]))
    code = "local o={} for q,p in pairs(prototypes.quality) do o[#o+1]=q..' '..p.level end rcon.print(table.concat(o,'\\n'))"
    for ln in L(code).split("\n"):
        t = ln.split()
        if len(t) == 2:
            lv[t[0]] = int(t[1])
    return g, lv


def fetch_poles(surf, x0, y0, x1, y1, strict=True):
    cond = "if p.x>=%s and p.x<%s and p.y>=%s and p.y<%s then " % (x0, x1, y0, y1) if strict else "do "
    code = ("local s=game.surfaces['%s'] local o={} for _,e in pairs(s.find_entities_filtered{type='electric-pole',area={{%s,%s},{%s,%s}}}) do local p=e.position %s"
            "local nb={} local fx=0 local c=e.get_wire_connector(defines.wire_connector_id.pole_copper,false) "
            "if c then for _,cn in pairs(c.connections) do local t=cn.target.owner if t.type=='electric-pole' then nb[#nb+1]=t.unit_number else fx=1 end end end "
            "for _,id in pairs({defines.wire_connector_id.circuit_red,defines.wire_connector_id.circuit_green}) do local cc=e.get_wire_connector(id,false) if cc and cc.connection_count>0 then fx=1 end end "
            "o[#o+1]=string.format('%%d %%s %%s %%.1f %%.1f %%d %%d %%s',e.unit_number,e.name,e.quality.name,p.x,p.y,e.electric_network_id,fx,table.concat(nb,',')) end end "
            "rcon.print(table.concat(o,'\\n'))") % (surf, x0, y0, x1, y1, cond)
    res = {}
    out = L(code)
    for ln in out.split("\n"):
        t = ln.split(" ")
        if len(t) < 7:
            continue
        nbs = [int(v) for v in t[7].split(",") if v] if len(t) > 7 else []
        res[int(t[0])] = dict(u=int(t[0]), name=t[1], q=t[2], x=float(t[3]), y=float(t[4]), net=int(t[5]), fixed=int(t[6]), nbs=nbs)
    return res


def fetch_cons(surf, x0, y0, x1, y1, strict=True):
    """consumers in the box; returns (list of (x0,y0,x1,y1,ghost), n, no_power_units, low_power_n)"""
    cond = "local q=e.position if q.x>=%s and q.x<%s and q.y>=%s and q.y<%s then " % (x0, x1, y0, y1) if strict else "do "
    code = ("local s=game.surfaces['%s'] local o={} local c={} local n,np,lp=0,0,0 local npl={} "
            "local ex={} for _,k in pairs({%s}) do ex[k]=1 end "
            "for _,e in pairs(s.find_entities_filtered{area={{%s,%s},{%s,%s}}}) do %s "
            "local nm=e.name local pr=e.prototype local g=0 if e.type=='entity-ghost' then nm=e.ghost_name pr=e.ghost_prototype g=1 end "
            "local v=c[nm] if v==nil then v=(pr.type~='electric-pole') and (pr.electric_energy_source_prototype~=nil or ex[pr.type]~=nil) c[nm]=v end "
            "if v then local b=e.bounding_box o[#o+1]=string.format('%%.2f %%.2f %%.2f %%.2f %%d',b.left_top.x,b.left_top.y,b.right_bottom.x,b.right_bottom.y,g) "
            "if g==0 then n=n+1 local st=e.status if st==defines.entity_status.no_power then np=np+1 if #npl<400 then npl[#npl+1]=e.unit_number or 0 end elseif st==defines.entity_status.low_power then lp=lp+1 end end end end end "
            "rcon.print('S '..n..' '..np..' '..lp..' '..table.concat(npl,',')) rcon.print(table.concat(o,'\\n'))") % (
        surf, CRITICAL_TYPES.replace("'", "'"), x0, y0, x1, y1, cond)
    out = L(code).split("\n")
    s = out[0].split(" ")
    cons = []
    for ln in out[1:]:
        t = ln.split(" ")
        if len(t) == 5:
            cons.append((float(t[0]), float(t[1]), float(t[2]), float(t[3]), int(t[4])))
    npu = set(int(v) for v in (s[4].split(",") if len(s) > 4 else []) if v)
    return cons, int(s[1]), int(s[2]), int(s[3]), npu


def tiles(x0, y0, x1, y1, size):
    xs = list(range(int(math.floor(x0 / size)) * size, int(x1), size))
    ys = list(range(int(math.floor(y0 / size)) * size, int(y1), size))
    return [(a, b, a + size, b + size) for a in xs for b in ys]


def export_surface(surf, geom):
    """whole-surface export in 200x200 poles blocks and 100x100 consumer blocks"""
    out = L("local s=game.surfaces['%s'] local x0,y0,x1,y1=1e9,1e9,-1e9,-1e9 for _,e in pairs(s.find_entities_filtered{type='electric-pole'}) do local p=e.position "
            "if p.x<x0 then x0=p.x end if p.x>x1 then x1=p.x end if p.y<y0 then y0=p.y end if p.y>y1 then y1=p.y end end rcon.print(x0..' '..y0..' '..x1..' '..y1)" % surf)
    bx0, by0, bx1, by1 = [float(v) for v in out.split()]
    if bx0 > 1e8:
        return None
    poles = {}
    for (a, b, c, d) in tiles(bx0, by0, bx1 + 1, by1 + 1, 200):
        poles.update(fetch_poles(surf, a, b, c, d))
    cons = []
    tot = [0, 0, 0]
    npu = set()
    boxes = tiles(bx0 - 16, by0 - 16, bx1 + 17, by1 + 17, 100)
    for i, (a, b, c, d) in enumerate(boxes):
        cs, n, np_, lp, npl = fetch_cons(surf, a, b, c, d)
        cons.extend(cs)
        tot[0] += n
        tot[1] += np_
        tot[2] += lp
        npu |= npl
    return dict(surface=surf, poles=list(poles.values()), cons=cons, n_consumers=tot[0], no_power=tot[1], low_power=tot[2], no_power_units=sorted(npu), t=time.time())


def cache_path(surf):
    return HERE / ("_power_thin_%s.json" % surf)


def load_cache(surf):
    p = cache_path(surf)
    if not p.exists():
        return None
    return json.loads(p.read_text())


# ----------------------------------------------------------------------------- model
def box_skipped(surf, x, y):
    for b in SKIP_BOXES.get(surf, []) + EXTRA_SKIP:
        if b[0] - SKIP_PAD <= x <= b[2] + SKIP_PAD and b[1] - SKIP_PAD <= y <= b[3] + SKIP_PAD:
            return True
    return False


class Model:
    def __init__(self, surf, poles, cons, geom, quality=None, levels=None, candidates=None):
        self.surf = surf
        self.poles = {p["u"]: dict(p) for p in poles}
        self.cons = cons
        self.geom = geom
        for p in self.poles.values():
            q = p["q"]
            if quality and p["name"] in ("substation", "medium-electric-pole", "big-electric-pole", "small-electric-pole"):
                if levels.get(quality, 0) > levels.get(q, 0):
                    q = quality
            g = geom[(p["name"], q)]
            p["d"], p["w"], p["tw"], p["th"] = g["d"], g["w"], g["tw"], g["th"]
        self.candidates = candidates
        self._cover()
        self._adj()

    def _cover(self):
        CELL = 8
        grid = defaultdict(list)
        for i, c in enumerate(self.cons):
            for cx in range(int(c[0] // CELL), int(c[2] // CELL) + 1):
                for cy in range(int(c[1] // CELL), int(c[3] // CELL) + 1):
                    grid[(cx, cy)].append(i)
        self.cover = {}
        self.ccnt = defaultdict(lambda: defaultdict(int))
        for u, p in self.poles.items():
            ax0, ax1, ay0, ay1 = p["x"] - p["d"], p["x"] + p["d"], p["y"] - p["d"], p["y"] + p["d"]
            seen = set()
            lst = []
            for cx in range(int(ax0 // CELL), int(ax1 // CELL) + 1):
                for cy in range(int(ay0 // CELL), int(ay1 // CELL) + 1):
                    for i in grid.get((cx, cy), ()):
                        if i in seen:
                            continue
                        seen.add(i)
                        c = self.cons[i]
                        if c[0] < ax1 - EPS and c[2] > ax0 + EPS and c[1] < ay1 - EPS and c[3] > ay0 + EPS:
                            lst.append(i)
            self.cover[u] = lst
            for i in lst:
                self.ccnt[i][p["net"]] += 1

    def _adj(self):
        CELL = 24.0
        g = defaultdict(list)
        for u, p in self.poles.items():
            g[(int(p["x"] // CELL), int(p["y"] // CELL))].append(u)
        self.adj = {u: set() for u in self.poles}
        for u, p in self.poles.items():
            r = int(p["w"] // CELL) + 2
            cx, cy = int(p["x"] // CELL), int(p["y"] // CELL)
            for ax in range(cx - r, cx + r + 1):
                for ay in range(cy - r, cy + r + 1):
                    for v in g.get((ax, ay), ()):
                        if v <= u:
                            continue
                        q = self.poles[v]
                        if q["net"] != p["net"]:
                            continue
                        if math.hypot(p["x"] - q["x"], p["y"] - q["y"]) <= min(p["w"], q["w"]) - REACH_MARGIN:
                            self.adj[u].add(v)
                            self.adj[v].add(u)
            for v in p["nbs"]:
                if v in self.poles:
                    self.adj[u].add(v)
                    self.adj[v].add(u)

    def conn_ok(self, u, alive):
        nb = [v for v in self.adj[u] if v in alive]
        if len(nb) <= 1:
            return True
        target = set(nb[1:])
        seen = {nb[0], u}
        dq = deque([nb[0]])
        while dq and target:
            x = dq.popleft()
            for y in self.adj[x]:
                if y in alive and y not in seen:
                    seen.add(y)
                    target.discard(y)
                    dq.append(y)
            if len(seen) > BFS_LIMIT:
                return False
        return not target

    def protected(self, u):
        p = self.poles[u]
        if p["fixed"]:
            return "fixed-wire"
        if self.candidates is not None and u not in self.candidates:
            return "outside"
        if box_skipped(self.surf, p["x"], p["y"]):
            return "skip-box"
        return None

    def run(self, idle_mode="cut", thin=True):
        alive = set(self.poles)
        removed, idle, reasons = [], [], defaultdict(int)
        order = sorted(self.poles, key=lambda u: (self.poles[u]["d"], int(self.poles[u]["y"] // 60), int(self.poles[u]["x"] // 60), len(self.cover[u]), u))
        for u in order:
            p = self.poles[u]
            if not self.cover[u] or not thin:
                continue
            why = self.protected(u)
            if why:
                reasons[why] += 1
                continue
            if not all(self.ccnt[i][p["net"]] >= 2 for i in self.cover[u]):
                reasons["sole-cover"] += 1
                continue
            if not self.conn_ok(u, alive):
                reasons["trunk/bridge"] += 1
                continue
            alive.discard(u)
            removed.append(u)
            for i in self.cover[u]:
                self.ccnt[i][p["net"]] -= 1
        if idle_mode != "off":
            for u in order:
                p = self.poles[u]
                if self.cover[u] or u not in alive:
                    continue
                if self.protected(u):
                    continue
                if not p["nbs"]:
                    continue
                if not self.conn_ok(u, alive):
                    reasons["idle-bridge"] += 1
                    continue
                alive.discard(u)
                idle.append(u)
        self.alive = alive
        self.removed, self.idle, self.reasons = removed, idle, dict(reasons)
        return removed, idle

    def edges_to_add(self, gone):
        """actual wires among the poles that remain (not in gone) plus the wires needed to keep each
        original wire-component whole: Kruskal over the potential reach edges."""
        rem = [u for u in self.poles if u not in gone]
        parent = {u: u for u in rem}

        def find(a):
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a
        actual = set()
        for u in rem:
            for v in self.poles[u]["nbs"]:
                if v in parent and v not in gone:
                    actual.add((min(u, v), max(u, v)))
                    parent[find(u)] = find(v)
        # components as they were before (all poles, actual wires)
        p0 = {u: u for u in self.poles}

        def f0(a):
            while p0[a] != a:
                p0[a] = p0[p0[a]]
                a = p0[a]
            return a
        for u, p in self.poles.items():
            for v in p["nbs"]:
                if v in p0:
                    p0[f0(u)] = f0(v)
        cand = []
        for u in rem:
            for v in self.adj[u]:
                if v > u and v in parent and (u, v) not in actual:
                    a, b = self.poles[u], self.poles[v]
                    cand.append((math.hypot(a["x"] - b["x"], a["y"] - b["y"]), u, v))
        cand.sort()
        add = []
        for dist, u, v in cand:
            if find(u) != find(v) and f0(u) == f0(v):
                parent[find(u)] = find(v)
                add.append((u, v))
        return add


# ----------------------------------------------------------------------------- reporting
def summarize(m, removed, idle, add):
    by = defaultdict(int)
    freed = 0
    blocks = defaultdict(lambda: [1e9, 1e9, -1e9, -1e9, 0, 0])
    for u in removed:
        p = m.poles[u]
        by[(p["name"], p["q"])] += 1
        t = p["tw"] * p["th"]
        freed += t
        b = blocks[(int(p["x"] // 200) * 200, int(p["y"] // 200) * 200)]
        b[0], b[1] = min(b[0], p["x"] - p["tw"] / 2.0), min(b[1], p["y"] - p["th"] / 2.0)
        b[2], b[3] = max(b[2], p["x"] + p["tw"] / 2.0), max(b[3], p["y"] + p["th"] / 2.0)
        b[4] += 1
        b[5] += t
    return by, freed, blocks


def cmd_study(a):
    geom, lv = get_geom()
    surfs = [a.surface] if a.surface else EDIT_SURFACES + sorted(FROZEN)
    log("quality levels:", lv)
    log("%-22s %-10s %6s %6s %5s" % ("pole", "quality", "area", "reach", "tiles"))
    for (n, q), g in sorted(geom.items()):
        if q in ("normal", "uncommon", "rare", "epic", "legendary"):
            log("%-22s %-10s %6.1f %6.1f %3dx%d" % (n, q, g["d"] * 2, g["w"], g["tw"], g["th"]))
    base = json.loads(BASE.read_text()) if BASE.exists() else {}
    for s in surfs:
        t0 = time.time()
        d = export_surface(s, geom)
        if not d:
            log(s, "no poles")
            continue
        cache_path(s).write_text(json.dumps(d))
        cnt = defaultdict(int)
        nets = defaultdict(int)
        for p in d["poles"]:
            cnt[(p["name"], p["q"])] += 1
            nets[p["net"]] += 1
        log("%s: %d poles, %d consumers, no_power %d, low_power %d (%.0fs)" % (s, len(d["poles"]), d["n_consumers"], d["no_power"], d["low_power"], time.time() - t0))
        log("   by type:", dict(("%s/%s" % k, v) for k, v in cnt.items()))
        big = sorted(nets.items(), key=lambda kv: -kv[1])[:8]
        log("   networks (id:poles):", big)
        if s not in base:
            base[s] = dict(no_power=d["no_power"], low_power=d["low_power"], consumers=d["n_consumers"], nets=dict((str(k), v) for k, v in nets.items() if v >= 5), t=d["t"])
    SNAP.mkdir(exist_ok=True)
    BASE.write_text(json.dumps(base))
    log("baseline kept in", BASE)


def plan_surface(s, a, geom, lv):
    d = load_cache(s)
    if d is None or a.refresh:
        d = export_surface(s, geom)
        if d:
            cache_path(s).write_text(json.dumps(d))
    if not d:
        log(s, "nothing")
        return
    cons = [tuple(c) for c in d["cons"]]
    m = Model(s, d["poles"], cons, geom, quality=a.quality, levels=lv)
    removed, idle, = m.run(a.idle)
    gone = set(removed) | set(idle)
    add = m.edges_to_add(gone)
    by, freed, blocks = summarize(m, removed, idle, add)
    n = len(m.poles)
    log("== %s%s: %d poles (%d fixed-wire)" % (s, " (FROZEN: analysis only)" if s in FROZEN else "", n, sum(1 for p in m.poles.values() if p["fixed"])))
    log("   removable: %d (%.1f%%)  by type: %s" % (len(removed), 100.0 * len(removed) / max(1, n), dict(("%s/%s" % k, v) for k, v in by.items())))
    cutw = sum(1 for u in idle for v in m.poles[u]["nbs"])
    log("   idle poles: %d, wires cut: %d (mode %s); bridging wires to add: %d" % (len(idle), cutw, a.idle, len(add)))
    log("   land freed by removals: %d tiles; kept reasons: %s" % (freed, m.reasons))
    for k, b in sorted(blocks.items()):
        log("      block %s: %d poles, %d tiles, box (%.0f,%.0f)-(%.0f,%.0f)" % (k, b[4], b[5], b[0], b[1], b[2], b[3]))
    # next quality projection from the post-removal state
    if not a.quality:
        nxt = [q for q in sorted(lv, key=lambda q: lv[q]) if lv[q] > lv.get("epic", 3) and q != "quality-unknown"][:1]
        if nxt:
            rest = [p for u, p in m.poles.items() if u not in gone]
            m2 = Model(s, rest, cons, geom, quality=nxt[0], levels=lv)
            r2, i2 = m2.run("off")
            by2, f2, _ = summarize(m2, r2, [], [])
            log("   NEXT ROUND (%s substations everywhere, after this round): %d more removable, %d tiles" % (nxt[0], len(r2), f2))
    return m, removed, idle, add


def cmd_plan(a):
    geom, lv = get_geom()
    surfs = [a.surface] if a.surface else EDIT_SURFACES + sorted(FROZEN)
    for s in surfs:
        plan_surface(s, a, geom, lv)


# ----------------------------------------------------------------------------- apply
def lua_apply(surf, add, rm, cut, P):
    """add: [(ua,ub)] wires first; rm: [unit] destroy; cut: [unit] disconnect_all (returns pairs).
    Poles are looked up by position (game.get_entity_by_unit_number does not find them)."""
    def pos(us):
        return ",".join("%s,%s" % (P[u]["x"], P[u]["y"]) for u in us)
    adds = ",".join("%s,%s,%s,%s" % (P[a]["x"], P[a]["y"], P[b]["x"], P[b]["y"]) for a, b in add)
    code = ("local s=game.surfaces['%s'] local function fp(x,y) return s.find_entities_filtered{type='electric-pole',position={x,y},radius=0.3}[1] end "
            "local add={%s} local rm={%s} local cut={%s} local bad=0 "
            "for i=1,#add,4 do local a=fp(add[i],add[i+1]) local b=fp(add[i+2],add[i+3]) if a and b then "
            "local ca=a.get_wire_connector(defines.wire_connector_id.pole_copper,true) local cb=b.get_wire_connector(defines.wire_connector_id.pole_copper,true) "
            "if not ca.is_connected_to(cb) then if not ca.connect_to(cb,true,defines.wire_origin.script) then bad=bad+1 end end else bad=bad+1 end end "
            "if bad>0 then rcon.print('FAIL wires '..bad) return end "
            "local d=0 for i=1,#rm,2 do local e=fp(rm[i],rm[i+1]) if e then e.destroy() d=d+1 end end "
            "local cc={} for i=1,#cut,2 do local e=fp(cut[i],cut[i+1]) if e then local c=e.get_wire_connector(defines.wire_connector_id.pole_copper,false) "
            "if c then local l={} for _,cn in pairs(c.connections) do l[#l+1]=cn.target.owner.unit_number end for _,x in pairs(l) do cc[#cc+1]=e.unit_number..':'..x end c.disconnect_all(defines.wire_origin.script) c.disconnect_all(defines.wire_origin.player) end end end "
            "rcon.print('OK '..d..' '..table.concat(cc,','))") % (surf, adds, pos(rm), pos(cut))
    return L(code)


def describe(surf, box, units):
    code = ("local s=game.surfaces['%s'] local o={} for _,e in pairs(s.find_entities_filtered{area={{%s,%s},{%s,%s}}}) do if e.status==defines.entity_status.no_power then "
            "o[#o+1]=e.name..'@'..e.position.x..','..e.position.y end end rcon.print(table.concat(o,';'))") % (surf, box[0], box[1], box[2], box[3])
    return L(code)[:600]


def health(surf, box):
    cs, n, npc, lp, npu = fetch_cons(surf, box[0], box[1], box[2], box[3], strict=False)
    return n, npu, lp


def netmap(poles, skip=()):
    return dict((u, p["net"]) for u, p in poles.items() if u not in skip)


def mapping_ok(before, after):
    """no id split into two, no two ids merged"""
    fwd, bwd = defaultdict(set), defaultdict(set)
    for u, n0 in before.items():
        if u in after:
            fwd[n0].add(after[u])
            bwd[after[u]].add(n0)
    return all(len(v) == 1 for v in fwd.values()) and all(len(v) == 1 for v in bwd.values())


def put_back(surf, rows):
    """rows: dicts name,q,x,y,nbpos [(x,y)]"""
    ents = [{"name": r["name"], "x": r["x"], "y": r["y"], "direction": 0, "params": {"quality": r["q"]}} for r in rows]
    res = tools["place_entities"](json.dumps(ents), surface=surf, dry_run=False)
    wires = 0
    for r in rows:
        pts = ",".join("{%s,%s}" % (x, y) for x, y in r["nbpos"])
        code = ("local s=game.surfaces['%s'] local e=s.find_entities_filtered{type='electric-pole',position={%s,%s},radius=0.3}[1] local n=0 if e then "
                "local c=e.get_wire_connector(defines.wire_connector_id.pole_copper,true) for _,p in pairs({%s}) do local t=s.find_entities_filtered{type='electric-pole',position=p,radius=0.3}[1] "
                "if t then local ct=t.get_wire_connector(defines.wire_connector_id.pole_copper,true) if c.is_connected_to(ct) or c.connect_to(ct,true,defines.wire_origin.script) then n=n+1 end end end end rcon.print(n)") % (
            surf, r["x"], r["y"], pts)
        try:
            wires += int(L(code))
        except ValueError:
            pass
    return res[:200], wires


def log_undo(rows):
    SNAP.mkdir(exist_ok=True)
    data = json.loads(UNDO.read_text()) if UNDO.exists() else []
    data.append(rows)
    UNDO.write_text(json.dumps(data))


def pop_undo():
    data = json.loads(UNDO.read_text())
    UNDO.write_text(json.dumps(data[:-1]))


def apply_region(surf, region, geom, lv, a):
    M = 60
    win = (region[0] - M, region[1] - M, region[2] + M, region[3] + M)
    poles = fetch_poles(surf, *win, strict=False)
    cons, n, npc, lp, npu = fetch_cons(surf, win[0] - 16, win[1] - 16, win[2] + 16, win[3] + 16, strict=False)
    cand = set(u for u, p in poles.items() if region[0] <= p["x"] < region[2] and region[1] <= p["y"] < region[3])
    if not cand:
        return 0, 0, 0
    m = Model(surf, list(poles.values()), cons, geom, quality=None, levels=lv, candidates=cand)
    removed, idle = m.run("off" if a.only == "thin" else a.idle, thin=(a.only != "idle"))
    log("  region %s: %d poles, %d consumers, plan: remove %d, idle %d (no_power now %d)" % (region, len(cand), n, len(removed), len(idle), len(npu)))
    if a.dry:
        return len(removed), len(idle), 0
    done_rm, done_cut, wires_cut = 0, 0, 0
    work = ([("rm", u) for u in removed] if a.only in ("thin", "both") else []) + ([("cut", u) for u in idle] if a.only in ("idle", "both") else [])
    gone = set()
    batch_no = 0
    for i in range(0, len(work), a.batch):
        chunk = work[i:i + a.batch]
        if a.max_batches and batch_no >= a.max_batches:
            break
        batch_no += 1
        rm = [u for k, u in chunk if k == "rm"]
        cut = [u for k, u in chunk if k == "cut"]
        if a.idle == "remove":
            rm, cut = rm + cut, []
        gone_next = gone | set(rm) | set(cut)
        # nothing left to do for poles that other work already removed
        add = m.edges_to_add(gone_next)
        # only wires not yet present in game: filter against the live state via lua (is_connected_to check)
        bx = [m.poles[u]["x"] for u in rm + cut]
        by_ = [m.poles[u]["y"] for u in rm + cut]
        hb = (min(bx) - 40, min(by_) - 40, max(bx) + 40, max(by_) + 40)
        n0, np0, lp0 = health(surf, hb)
        before = fetch_poles(surf, *hb, strict=False)
        cutset = set(cut)
        nm0 = netmap(before, cutset)
        rows = []
        for u in rm:
            p = m.poles[u]
            rows.append(dict(name=p["name"], q=p["q"], x=p["x"], y=p["y"], nbpos=[(m.poles[v]["x"], m.poles[v]["y"]) for v in p["nbs"] if v in m.poles and v not in gone_next]))
        log_undo(rows)
        # keep only wire additions touching this batch's neighbourhood (others were added by earlier batches)
        add_new = [e for e in add if e not in getattr(m, "_added", set())]
        res = lua_apply(surf, add_new, rm, cut, m.poles)
        if not res.startswith("OK"):
            log("  batch FAILED before changes:", res)
            pop_undo()
            return done_rm, done_cut, wires_cut
        m._added = getattr(m, "_added", set()) | set(add_new)
        for e in add_new:
            m.poles[e[0]]["nbs"].append(e[1])
            m.poles[e[1]]["nbs"].append(e[0])
        parts = res.split(" ", 2)
        cutrec = [tuple(int(v) for v in s.split(":")) for s in (parts[2].split(",") if len(parts) > 2 and parts[2] else [])]
        time.sleep(1.5)
        after = fetch_poles(surf, *hb, strict=False)
        n1, np1, lp1 = health(surf, hb)
        ok = True
        why = []
        if len(after) != len(before) - len(rm):
            ok = False
            why.append("pole count %d->%d (expected -%d)" % (len(before), len(after), len(rm)))
        if not mapping_ok(nm0, netmap(after, cutset)):
            ok = False
            why.append("network ids split/merged")
        if np1 - np0:
            ok = False
            why.append("new no_power entities: %s" % describe(surf, hb, np1 - np0))
        # geometric proof on the live state: every consumer covered before is still covered
        if ok:
            c2, _, _, _, _ = fetch_cons(surf, hb[0], hb[1], hb[2], hb[3], strict=False)
            m3 = Model(surf, [p for u, p in after.items() if u not in cutset], c2, geom, candidates=set())
            uncovered = [i for i, c in enumerate(c2) if not m3.ccnt[i]]
            m_before = Model(surf, list(before.values()), c2, geom, candidates=set())
            lost = [i for i in range(len(c2)) if m_before.ccnt[i] and not m3.ccnt[i]]
            if lost:
                ok = False
                why.append("%d consumers lost coverage" % len(lost))
        if not ok:
            log("  batch ROLLBACK:", why, "| lua said:", res[:160])
            if rm:
                r, w = put_back(surf, rows)
                log("   put back", len(rows), "poles,", w, "wires")
            for x, y in cutrec:
                pass
            if cutrec:
                reconnect_pairs(surf, cutrec, m.poles)
            pop_undo()
            return done_rm, done_cut, wires_cut
        gone = gone_next
        done_rm += len(rm)
        done_cut += len(cut)
        wires_cut += len(cutrec)
        if cutrec:
            rec = json.loads(WIRES.read_text()) if WIRES.exists() else []
            for ua, ub in cutrec:
                rec.append(dict(surface=surf, a=[m.poles[ua]["x"], m.poles[ua]["y"]], b=[m.poles[ub]["x"], m.poles[ub]["y"]], na=m.poles[ua]["name"], q=m.poles[ua]["q"]))
            WIRES.write_text(json.dumps(rec))
        log("   batch %d ok: removed %d, idle-cut %d (wires cut %d), wires added %d, no_power %d->%d, low %d->%d" % (batch_no, len(rm), len(cut), len(cutrec), len(add_new), len(np0), len(np1), lp0, lp1))
    return done_rm, done_cut, wires_cut


def reconnect_pairs(surf, pairs_by_unit, P=None):
    """pairs of unit numbers (cut wires of this run); poles are found by position through the model P
    (unit numbers of cut poles are in P)"""
    pts = []
    for a, b in pairs_by_unit:
        if a in P and b in P:
            pts.append("{%s,%s,%s,%s}" % (P[a]["x"], P[a]["y"], P[b]["x"], P[b]["y"]))
    code = ("local s=game.surfaces['%s'] local function fp(x,y) return s.find_entities_filtered{type='electric-pole',position={x,y},radius=0.3}[1] end "
            "local ok=0 for _,pr in pairs({%s}) do local a=fp(pr[1],pr[2]) local b=fp(pr[3],pr[4]) if a and b then "
            "local ca=a.get_wire_connector(defines.wire_connector_id.pole_copper,true) local cb=b.get_wire_connector(defines.wire_connector_id.pole_copper,true) "
            "if ca.is_connected_to(cb) or ca.connect_to(cb,true,defines.wire_origin.script) then ok=ok+1 end end end rcon.print(ok)") % (surf, ",".join(pts))
    return L(code)


def refuse(surf):
    if surf in FROZEN:
        log("REFUSED: %s is frozen (analysis only until the coordinator releases it)" % surf)
        return True
    if surf.startswith(NEVER_PREFIX) or surf not in EDIT_SURFACES:
        log("REFUSED: %s is read-only for this script" % surf)
        return True
    return False


def cmd_apply(a):
    if refuse(a.surface):
        return
    geom, lv = get_geom()
    if a.skip:
        for b in a.skip:
            EXTRA_SKIP.append(tuple(b) + ("cli",))
    pl = L("local o={} for _,p in pairs(game.players) do if p.surface.name=='%s' then o[#o+1]=p.position.x..' '..p.position.y end end rcon.print(table.concat(o,';'))" % a.surface)
    for ln in pl.split(";"):
        t = ln.split()
        if len(t) == 2:
            x, y = float(t[0]), float(t[1])
            EXTRA_SKIP.append((x - 30, y - 30, x + 30, y + 30, "player"))
            log("skipping around a player at", x, y)
    d = load_cache(a.surface) or export_surface(a.surface, geom)
    xs = [p["x"] for p in d["poles"]]
    ys = [p["y"] for p in d["poles"]]
    regs = [tuple(a.region)] if a.region else [t for t in tiles(min(xs), min(ys), max(xs) + 1, max(ys) + 1, 200)]
    dens = defaultdict(int)
    for p in d["poles"]:
        for r in regs:
            if r[0] <= p["x"] < r[2] and r[1] <= p["y"] < r[3]:
                dens[r] += 1
    regs = [r for r in regs if dens[r] > 0]
    tot = [0, 0, 0]
    for r in regs:
        log("saving game before region", r)
        if not a.dry:
            log(tools["save_game"]("skippy")[:100])
        x = apply_region(a.surface, r, geom, lv, a)
        for i in range(3):
            tot[i] += x[i]
    log("TOTAL removed %d, idle-cut %d, wires cut %d" % tuple(tot))


def cmd_verify(a):
    base = json.loads(BASE.read_text()) if BASE.exists() else {}
    for s in ([a.surface] if a.surface else EDIT_SURFACES + sorted(FROZEN)):
        d = export_surface(s, get_geom()[0])
        if not d:
            continue
        nets = defaultdict(int)
        for p in d["poles"]:
            nets[p["net"]] += 1
        b = base.get(s, {})
        log("%s: poles %d, consumers %d (base %s), no_power %d (base %s), low_power %d (base %s)" % (
            s, len(d["poles"]), d["n_consumers"], b.get("consumers"), d["no_power"], b.get("no_power"), d["low_power"], b.get("low_power")))
        old = set(b.get("nets", {}))
        now = set(str(k) for k, v in nets.items() if v >= 5)
        log("   network ids with >=5 poles: now %d, baseline %d; new ids: %s; vanished ids: %s" % (len(now), len(old), sorted(now - old)[:10], sorted(old - now)[:10]))
        log("   biggest:", sorted(nets.items(), key=lambda kv: -kv[1])[:6])


def cmd_undo(a):
    if not UNDO.exists():
        log("no undo log")
        return
    data = json.loads(UNDO.read_text())
    n = a.last or 1
    for rows in reversed(data[-n:]):
        r, w = put_back(a.surface, rows)
        log("put back", len(rows), "poles", w, "wires", r[:80])
    UNDO.write_text(json.dumps(data[:-n]))


def cmd_reconnect(a):
    if not WIRES.exists():
        log("no wire record")
        return
    rec = json.loads(WIRES.read_text())
    keep, ok = [], 0
    for r in rec:
        inside = True
        if a.region:
            x0, y0, x1, y1 = a.region
            inside = x0 <= r["a"][0] <= x1 and y0 <= r["a"][1] <= y1
        if r["surface"] != a.surface or not inside:
            keep.append(r)
            continue
        code = ("local s=game.surfaces['%s'] local a=s.find_entities_filtered{type='electric-pole',position={%s,%s},radius=0.3}[1] local b=s.find_entities_filtered{type='electric-pole',position={%s,%s},radius=0.3}[1] "
                "if a and b then local ca=a.get_wire_connector(defines.wire_connector_id.pole_copper,true) local cb=b.get_wire_connector(defines.wire_connector_id.pole_copper,true) "
                "rcon.print((ca.is_connected_to(cb) or ca.connect_to(cb,true,defines.wire_origin.script)) and 1 or 0) else rcon.print(0) end") % (
            r["surface"], r["a"][0], r["a"][1], r["b"][0], r["b"][1])
        if L(code) == "1":
            ok += 1
        else:
            keep.append(r)
    WIRES.write_text(json.dumps(keep))
    log("reconnected %d wires, %d left in the record" % (ok, len(keep)))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["study", "plan", "apply", "verify", "undo", "reconnect"])
    ap.add_argument("--surface")
    ap.add_argument("--region", nargs=4, type=float)
    ap.add_argument("--quality")
    ap.add_argument("--idle", default="cut", choices=["cut", "remove", "off"])
    ap.add_argument("--batch", type=int, default=20)
    ap.add_argument("--max-batches", type=int, default=0)
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--only", default="both", choices=["thin", "idle", "both"])
    ap.add_argument("--last", type=int, default=1)
    ap.add_argument("--skip", nargs=4, type=float, action="append")
    a = ap.parse_args()
    if a.skip:
        for b in a.skip:
            EXTRA_SKIP.append(tuple(b) + ("cli",))
    if a.cmd in ("undo", "reconnect") and not a.surface:
        sys.exit("--surface required")
    {"study": cmd_study, "plan": cmd_plan, "apply": cmd_apply, "verify": cmd_verify, "undo": cmd_undo, "reconnect": cmd_reconnect}[a.cmd](a)


if __name__ == "__main__":
    main()
