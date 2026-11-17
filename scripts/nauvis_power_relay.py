#!/usr/bin/env python3
"""Re-lay the Nauvis power grid, coverage only (the Captain, 2026-11-16: "remove the entire power network ... re-place the grid, but only cover areas that need
coverage; long distance bases, use the big electric pole"). Make-before-break, so there is never a blackout:
  plan     export every powered entity, sweep a lattice of legendary substations over them (an area of 24 tiles per substation, supply 28), print the count
  place    place that new grid next to the old one (the new poles join the live network by wire), cover what is left, join separate clusters: short gaps with
           substations, gaps over BIG_GAP tiles with big electric poles (wire 42, but a pole-to-substation wire is limited to the substation's 28)
  verify   every powered entity is inside a NEW (or kept) pole's supply area and the new poles form one network with the generators
  remove   (after verify is clean) saves the undo record, removes the OLD poles in batches; after each batch no powered entity may have lost its network,
           otherwise the batch is put back and the run stops
  undo     put the removed poles back (position, name, quality) from snapshots/nauvis_relay_removed.json
Kept as they are: poles with a circuit (signal) wire or a copper wire to something that is not a pole (the Captain's rule), and everything outside Nauvis.
Safe to repeat: place only adds what is still uncovered; new poles are recorded in snapshots/nauvis_relay_new.json.
Usage: nauvis_power_relay.py plan | place [--limit N] | verify | remove [--batch N] [--max-batches N] | undo [--last N] | status"""
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

from _game import tools

SNAP = Path(__file__).resolve().parent.parent / "snapshots"
NEW = SNAP / "nauvis_relay_new.json"
REMOVED = SNAP / "nauvis_relay_removed.json"
SUPPLY = 14.0            # legendary substation half area (read from the prototype 2026-11-16)
WIRE = 28.0
BIG_SUPPLY, BIG_WIRE = 7.0, 42.0
STRIP = 24.0             # sweep square: 4 tiles of slack inside the 28-wide area, for the shift to a free spot
JOIN = 26.5              # planned wire length between substations (reach 28)
BIG_GAP = 80.0           # gaps longer than this are bridged with big poles
SHIFT = 4
Q = "legendary"

EXPORT = """
local s=game.surfaces.nauvis local f=game.forces.player local W=defines.wire_connector_id local o={} local gens=0
for _,e in pairs(s.find_entities_filtered{force=f}) do if e.type~='electric-pole' and e.prototype.electric_energy_source_prototype then local b=e.bounding_box
  o[#o+1]={b.left_top.x,b.left_top.y,b.right_bottom.x,b.right_bottom.y,e.type=='generator' and 1 or (e.type=='solar-panel' and 2 or 0)} end end
local poles={}
for _,e in pairs(s.find_entities_filtered{force=f,type='electric-pole'}) do local fixed=0
  for _,id in pairs{W.circuit_red,W.circuit_green} do local c=e.get_wire_connector(id,false) if c and c.connection_count>0 then fixed=1 end end
  local c=e.get_wire_connector(W.pole_copper,false) if c then for _,cn in pairs(c.connections) do if cn.target.owner.type~='electric-pole' then fixed=1 end end end
  poles[#poles+1]={e.name,e.position.x,e.position.y,e.quality.name,fixed} end
rcon.print(helpers.table_to_json({cons=o,poles=poles}))
"""

PLACE = """
local s=game.surfaces.nauvis local f=game.forces.player local R=SHIFT local pts={PTS} local out={}
local function land(x,y) return not s.get_tile(x,y).collides_with('player') end
local function clear(x,y) for _,e in pairs(s.find_entities_filtered{area={{x-2,y-2},{x+2,y+2}},type={'tree','cliff','simple-entity','item-entity','corpse'}}) do if e.force.name~='player' then e.destroy() end end end
for _,p in pairs(pts) do local cx,cy,nm=p[1],p[2],p[3] local cand={} for dx=-R,R do for dy=-R,R do cand[#cand+1]={dx,dy,dx*dx+dy*dy} end end
  table.sort(cand,function(a,b) return a[3]<b[3] end)
  for _,c in pairs(cand) do local x,y=cx+c[1],cy+c[2]
    if land(x,y) and (nm=='medium-electric-pole' or (land(x+1,y) and land(x,y+1) and land(x+1,y+1))) then clear(x,y)
      if s.can_place_entity{name=nm,position={x,y},force=f,quality='legendary'} then local e=s.create_entity{name=nm,position={x,y},force=f,quality='legendary'} if e then out[#out+1]={nm,e.position.x,e.position.y} end break end end end end
rcon.print(helpers.table_to_json(out))
"""


def jl(code):
    out = tools["run_lua"](" ".join(l for l in code.split("\n") if not l.lstrip().startswith("--"))).strip()
    if "Cannot execute command" in out:
        raise SystemExit("Lua error: " + out[:500])
    return json.loads(out) if out.startswith(("[", "{")) else out


def export():
    d = jl(EXPORT)
    return d["cons"], d["poles"]


def covers(sx, sy, box, half=SUPPLY):
    return box[0] < sx + half and box[2] > sx - half and box[1] < sy + half and box[3] > sy - half


def sweep(boxes, w=STRIP):
    """Strip cover: columns of width w along x, then squares of height w along y. Returns centres."""
    pts = sorted(boxes, key=lambda b: b[0])
    out, i = [], 0
    while i < len(pts):
        x0 = pts[i][0]
        strip = [b for b in pts if x0 <= b[0] < x0 + w]
        i += len(strip)
        strip.sort(key=lambda b: b[1])
        j = 0
        while j < len(strip):
            y0 = strip[j][1]
            k = j
            while k < len(strip) and strip[k][1] < y0 + w:
                k += 1
            out.append((x0 + w / 2.0, y0 + w / 2.0))
            j = k
    return out


def uncovered(boxes, subs, kept):
    grid = defaultdict(list)
    for x, y, half in subs + kept:
        grid[(int(x // 30), int(y // 30))].append((x, y, half))
    bad = []
    for b in boxes:
        cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        gx, gy = int(cx // 30), int(cy // 30)
        ok = False
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for x, y, half in grid.get((gx + dx, gy + dy), ()):
                    if covers(x, y, b, half):
                        ok = True
                        break
                if ok:
                    break
            if ok:
                break
        if not ok:
            bad.append(b)
    return bad


def place_points(pts, batch=40):
    placed = []
    for i in range(0, len(pts), batch):
        part = pts[i:i + batch]
        txt = ",".join("{%.1f,%.1f,'%s'}" % p for p in part)
        res = jl(PLACE.replace("SHIFT", str(SHIFT)).replace("PTS", txt))
        placed += [tuple(p) for p in res] if isinstance(res, list) else []
        if (i // batch) % 10 == 0:
            print("  %d/%d points, %d placed" % (min(i + batch, len(pts)), len(pts), len(placed)), flush=True)
    return placed


def half(name):
    return SUPPLY if name == "substation" else (8.5 if name == "medium-electric-pole" else BIG_SUPPLY)


def load_new():
    try:
        return [tuple(p) for p in json.loads(NEW.read_text())]
    except Exception:  # noqa: BLE001
        return []


def components(nodes, reach):
    """Union-find over nodes (x, y, half-reach) by geometric wire reach. Returns list of index lists."""
    n = len(nodes)
    par = list(range(n))

    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a
    grid = defaultdict(list)
    for i, nd in enumerate(nodes):
        grid[(int(nd[0] // 30), int(nd[1] // 30))].append(i)
    for i, nd in enumerate(nodes):
        gx, gy = int(nd[0] // 30), int(nd[1] // 30)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for j in grid.get((gx + dx, gy + dy), ()):
                    if j > i and math.hypot(nd[0] - nodes[j][0], nd[1] - nodes[j][1]) <= min(nd[2], nodes[j][2], reach):
                        par[find(i)] = find(j)
    comp = defaultdict(list)
    for i in range(n):
        comp[find(i)].append(i)
    return list(comp.values())


def node_of(p):
    name, x, y = p[0], p[1], p[2]
    return (x, y, BIG_WIRE if name == "big-electric-pole" else (WIRE if name == "substation" else 19.0))


def cmd_plan():
    cons, poles = export()
    kept = [(p[1], p[2], SUPPLY if p[0] == "substation" else (8.5 if p[0] == "medium-electric-pole" else BIG_SUPPLY)) for p in poles if p[4]]
    boxes = [b for b in cons if not any(covers(x, y, b, h) for x, y, h in kept)]
    centres = sweep(boxes)
    print("powered entities %d (generators %d, solar %d); old poles %d (kept by rule %d); new substations needed about %d; old substations %d"
          % (len(cons), sum(1 for b in cons if b[4] == 1), sum(1 for b in cons if b[4] == 2), len(poles), len(kept), len(centres), sum(1 for p in poles if p[0] == "substation")))


def cmd_place(limit=None):
    global SHIFT
    cons, poles = export()
    kept = [(p[1], p[2], SUPPLY if p[0] == "substation" else (8.5 if p[0] == "medium-electric-pole" else BIG_SUPPLY)) for p in poles if p[4]]
    new = load_new()
    newsubs = [(p[1], p[2], half(p[0])) for p in new]
    bad = uncovered(cons, newsubs, kept)
    print("entities not yet covered by the new grid: %d of %d" % (len(bad), len(cons)))
    todo = sweep(bad) if not new else sweep(bad, 12.0)
    if limit:
        todo = todo[:limit]
    placed = place_points([(x, y, "substation") for x, y in todo])
    new += placed
    NEW.write_text(json.dumps(new))
    print("placed %d substations (%d in the new grid)" % (len(placed), len(new)))
    # second pass: whatever the shift left uncovered, tight squares on the entities themselves
    for rnd in range(3):
        newsubs = [(p[1], p[2], half(p[0])) for p in new]
        bad = uncovered(cons, newsubs, kept)
        if not bad:
            break
        extra = place_points([((b[0] + b[2]) / 2, (b[1] + b[3]) / 2, "substation") for b in bad[:400:max(1, len(bad[:400]) // 400)]])
        if not extra:                                                  # packed areas (solar fields, plants): a 1x1 medium pole fits the gaps, supply 8.5
            keep, SHIFT = SHIFT, 7
            extra = place_points([((b[0] + b[2]) / 2, (b[1] + b[3]) / 2, "medium-electric-pole") for b in bad[:400]])
            SHIFT = keep
        new += extra
        NEW.write_text(json.dumps(new))
        print("round %d: %d uncovered, placed %d" % (rnd + 1, len(bad), len(extra)))
    bridge(new, poles, cons)


def bridge(new, poles, cons):
    """Join the clusters of the new grid (plus the kept poles) into one network; long gaps with big poles."""
    keptp = [p for p in poles if p[4]]
    for rnd in range(6):
        nodes = [node_of(p) for p in new] + [node_of(p) for p in keptp]
        comps = components(nodes, 27.5)
        print("clusters %d" % len(comps))
        if len(comps) <= 1:
            return
        # connect the nearest pair of clusters, repeatedly (Prim over clusters, from the biggest)
        comps.sort(key=len, reverse=True)
        main = set(comps[0])
        adds = []
        for comp in comps[1:]:
            best = None
            for i in comp:
                for j in main:
                    d = math.hypot(nodes[i][0] - nodes[j][0], nodes[i][1] - nodes[j][1])
                    if best is None or d < best[0]:
                        best = (d, i, j)
            d, i, j = best
            ax, ay, bx, by = nodes[j][0], nodes[j][1], nodes[i][0], nodes[i][1]
            ux, uy = (bx - ax) / d, (by - ay) / d
            if d > BIG_GAP:
                n_mid = max(0, math.ceil((d - 2 * 26.0) / 40.0))
                cnt = n_mid + 2
                seq = [26.0] + [26.0 + (d - 52.0) * k / (cnt - 1) for k in range(1, cnt - 1)] + [d - 26.0]
                adds += [(ax + ux * t, ay + uy * t, "big-electric-pole") for t in seq]
            else:
                k = int(d // JOIN)
                adds += [(ax + ux * JOIN * t, ay + uy * JOIN * t, "substation") for t in range(1, k + 1)]
            main |= set(comp)
        placed = place_points(adds)
        new += placed
        NEW.write_text(json.dumps(new))
        print("bridge round %d: placed %d (big poles %d)" % (rnd + 1, len(placed), sum(1 for p in placed if p[0] == "big-electric-pole")))


def plan_keeps(cons, poles, new):
    """Old poles that must stay: the sole cover of entities no new pole reaches (packed solar fields and plants have no free tile for a new pole).
    Greedy: the old pole that covers most of the remaining uncovered entities, until none is left."""
    kept = [(p[1], p[2], half(p[0])) for p in poles if p[4]]
    newp = [(p[1], p[2], half(p[0])) for p in new]
    bad = uncovered(cons, newp, kept)
    newset = {(round(p[1], 1), round(p[2], 1)) for p in new}
    old = [p for p in poles if not p[4] and (round(p[1], 1), round(p[2], 1)) not in newset]
    keeps = []
    while bad:
        best, cov = None, []
        for p in old:
            c = [b for b in bad if covers(p[1], p[2], b, half(p[0]))]
            if len(c) > len(cov):
                best, cov = p, c
        if not best:
            break
        keeps.append(best)
        ids = {id(b) for b in cov}
        bad = [b for b in bad if id(b) not in ids]
        old.remove(best)
    return keeps, bad


VERIFY_KEEPS = []


def cmd_verify():
    cons, poles = export()
    new = load_new()
    keeps, bad = plan_keeps(cons, poles, new)
    keptp = [p for p in poles if p[4]] + keeps
    nodes = [node_of(p) for p in new] + [node_of(p) for p in keptp]
    comps = components(nodes, 27.5)
    gens = [b for b in cons if b[4] == 1]
    VERIFY_KEEPS[:] = [(p[0], round(p[1], 1), round(p[2], 1)) for p in keeps]
    print("new poles %d (substations %d, big %d, medium %d), kept %d (%d old poles as sole cover) | uncovered entities %d | clusters in the new grid %d | generators %d"
          % (len(new), sum(1 for p in new if p[0] == "substation"), sum(1 for p in new if p[0] == "big-electric-pole"), sum(1 for p in new if p[0] == "medium-electric-pole"),
             len(keptp), len(keeps), len(bad), len(comps), len(gens)))
    for b in bad[:10]:
        print("   uncovered", [round(v, 1) for v in b])
    return len(bad) == 0 and len(comps) == 1



WIRE_LUA = """
local s=game.surfaces.nauvis local f=game.forces.player local WC=defines.wire_connector_id.pole_copper
local recs=storage.relay_s or {} local P={} local inS={}
local function key(e) return string.format('%.1f,%.1f',e.position.x,e.position.y) end
for _,r in pairs(recs) do local e=s.find_entities_filtered{name=r[1],position={r[2],r[3]},radius=0.4,force=f,type='electric-pole'}[1] if e then P[#P+1]={e=e,r=(r[1]=='big-electric-pole' and 42 or (r[1]=='substation' and 28 or 19)),k=key(e)} inS[key(e)]=true end end
local H={} for i,p in pairs(P) do local k=math.floor(p.e.position.x/30)..','..math.floor(p.e.position.y/30) H[k]=H[k] or {} H[k][#H[k]+1]=i end
local function near(i,maxr)
  local p=P[i] local gx,gy=math.floor(p.e.position.x/30),math.floor(p.e.position.y/30) local o={}
  for dx=-1,1 do for dy=-1,1 do for _,j in pairs(H[(gx+dx)..','..(gy+dy)] or {}) do if j~=i then local q=P[j] local d=math.sqrt((p.e.position.x-q.e.position.x)^2+(p.e.position.y-q.e.position.y)^2) if d<=math.min(p.r,q.r,maxr)-0.2 then o[#o+1]={j,d} end end end end end
  table.sort(o,function(a,b) return a[2]<b[2] end) return o end
local function linked(a,b) for _,cn in pairs(a.connections) do if cn.target.owner.position.x==b.owner.position.x and cn.target.owner.position.y==b.owner.position.y then return true end end return false end
local function free(c) for _,cn in pairs(c.connections) do local o=cn.target.owner if not inS[key(o)] then c.disconnect_from(cn.target,cn.origin) return true end end return false end
local function join(a,b) if linked(a,b) then return true end if a.connect_to(b,false) then return true end free(a) free(b) return a.connect_to(b,false) end
local made,fail=0,0
for i,p in pairs(P) do local pc=p.e.get_wire_connector(WC,true) local n=0 for _,nb in pairs(near(i,27.9)) do if n>=4 then break end local q=P[nb[1]] local qc=q.e.get_wire_connector(WC,true) if join(pc,qc) then made=made+1 n=n+1 else fail=fail+1 end end end
local function comps() local seen={} local list={} for i,p in pairs(P) do if not seen[p.k] then local comp={} local stack={i} seen[p.k]=true while #stack>0 do local a=table.remove(stack) comp[#comp+1]=a local ac=P[a].e.get_wire_connector(WC,true) for _,cn in pairs(ac.connections) do local o=cn.target.owner local k=key(o) if inS[k] and not seen[k] then seen[k]=true for j,q in pairs(P) do end stack[#stack+1]=P_by[k] end end end list[#list+1]=comp end end return list end
P_by={} for i,p in pairs(P) do P_by[p.k]=i end
local cl=comps() local rounds=0
while #cl>1 and rounds<6 do rounds=rounds+1 table.sort(cl,function(a,b) return #a>#b end) local main={} for _,i in pairs(cl[1]) do main[i]=true end
  for ci=2,#cl do local best=nil for _,i in pairs(cl[ci]) do for _,nb in pairs(near(i,41.9)) do if main[nb[1]] then if not best or nb[2]<best[3] then best={i,nb[1],nb[2]} end end end end
    if best then local a=P[best[1]].e.get_wire_connector(WC,true) local b=P[best[2]].e.get_wire_connector(WC,true) if join(a,b) then for _,i in pairs(cl[ci]) do main[i]=true end end end end
  cl=comps() end
local sizes={} for i=1,math.min(6,#cl) do sizes[#sizes+1]=#cl[i] end
local small={} for ci=2,#cl do for _,i in pairs(cl[ci]) do small[#small+1]=P[i].e.name:sub(1,3)..'@'..P[i].k end end rcon.print('poles '..#P..' wires made '..made..' failed '..fail..' clusters '..#cl..' sizes '..table.concat(sizes,',')..' small: '..table.concat(small,' ; '))
"""

NETCOUNT = """
local s=game.surfaces.nauvis local f=game.forces.player local n,t=0,0
for _,e in pairs(s.find_entities_filtered{force=f}) do if e.type~='electric-pole' and e.prototype.electric_energy_source_prototype then t=t+1 if e.electric_network_id==nil then n=n+1 end end end
rcon.print(n..','..t)
"""


NOPOWER = """
local s=game.surfaces.nauvis local f=game.forces.player local n=0 for _,e in pairs(s.find_entities_filtered{force=f}) do if e.type~='electric-pole' and e.type~='solar-panel' and e.type~='accumulator' and e.prototype.electric_energy_source_prototype and e.status==defines.entity_status.no_power then n=n+1 end end rcon.print(n)
"""


def nopower():
    return int(tools["run_lua"](" ".join(NOPOWER.split(chr(10)))).strip())


def netcount():
    a, b = tools["run_lua"](" ".join(NETCOUNT.split("\n"))).strip().split(",")
    return int(a), int(b)


REMOVE = """
local s=game.surfaces.nauvis local f=game.forces.player local out={} for _,p in pairs({PTS}) do local e=s.find_entities_filtered{name=p[1],position={p[2],p[3]},radius=0.3,force=f}[1] if e and e.type=='electric-pole' then out[#out+1]={e.name,e.position.x,e.position.y,e.quality.name} e.destroy() end end rcon.print(helpers.table_to_json(out))
"""
RESTORE = """
local s=game.surfaces.nauvis local f=game.forces.player local n=0 for _,p in pairs({PTS}) do if s.create_entity{name=p[1],position={p[2],p[3]},force=f,quality=p[4]} then n=n+1 end end rcon.print(n)
"""


def cmd_wire():
    """Wire the new grid to itself (and to the kept poles) by really connecting copper wires, freeing slots by cutting wires to OLD poles: a pole holds only 5 wires,
    and the live ones may all go to old poles that are about to disappear. Needed before `remove`."""
    cons, poles = export()
    new = load_new()
    keeps, bad = plan_keeps(cons, poles, new)
    allp = [(p[0], p[1], p[2]) for p in new] + [(p[0], p[1], p[2]) for p in poles if p[4]] + [(p[0], p[1], p[2]) for p in keeps]
    tools["run_lua"]("storage.relay_s={}")
    for i in range(0, len(allp), 1200):
        txt = ",".join("{'%s',%.2f,%.2f}" % p for p in allp[i:i + 1200])
        tools["run_lua"]("local t=storage.relay_s for _,r in pairs({%s}) do t[#t+1]=r end rcon.print(#t)" % txt)
    out = tools["run_lua"](" ".join(l for l in WIRE_LUA.split(chr(10)) if not l.lstrip().startswith("--"))).strip()
    print(out)
    tools["run_lua"]("storage.relay_s=nil")
    return out


def cmd_remove(batch=150, max_batches=None):
    if not cmd_verify():
        raise SystemExit("verify is not clean: nothing removed")
    cons, poles = export()
    newset = {(round(p[1], 1), round(p[2], 1)) for p in load_new()}
    keepset = {(k[1], k[2]) for k in VERIFY_KEEPS}
    old = [p for p in poles if not p[4] and (round(p[1], 1), round(p[2], 1)) not in newset and (round(p[1], 1), round(p[2], 1)) not in keepset]
    print("old poles to remove: %d (kept as sole cover: %d)" % (len(old), len(keepset)))
    base_nop = nopower()
    base_bad, total = netcount()
    print("baseline: %d of %d powered entities without a network" % (base_bad, total))
    log = json.loads(REMOVED.read_text()) if REMOVED.exists() else []
    done = 0
    for bi, i in enumerate(range(0, len(old), batch)):
        if max_batches and bi >= max_batches:
            break
        part = old[i:i + batch]
        txt = ",".join("{'%s',%.2f,%.2f}" % (p[0], p[1], p[2]) for p in part)
        res = jl(REMOVE.replace("PTS", txt))
        res = res if isinstance(res, list) else []
        log += res
        REMOVED.write_text(json.dumps(log))
        bad, total = netcount()
        nop = nopower()
        if bad > base_bad or nop > base_nop:
            print("batch %d: %d entities lost their network, %d without power (baselines %d / %d): putting the batch back" % (bi + 1, bad - base_bad, nop, base_bad, base_nop))
            jl(RESTORE.replace("PTS", ",".join("{'%s',%.2f,%.2f,'%s'}" % tuple(r) for r in res)))
            log = log[:-len(res)] if res else log
            REMOVED.write_text(json.dumps(log))
            return
        done += len(res)
        print("batch %d: removed %d (total %d), entities without network %d, without power %d" % (bi + 1, len(res), done, bad, nop), flush=True)


def cmd_undo(last=None):
    log = json.loads(REMOVED.read_text()) if REMOVED.exists() else []
    part = log[-last:] if last else log
    for i in range(0, len(part), 200):
        jl(RESTORE.replace("PTS", ",".join("{'%s',%.2f,%.2f,'%s'}" % tuple(r) for r in part[i:i + 200])))
    REMOVED.write_text(json.dumps(log[:-len(part)] if part else log))
    print("restored %d poles (wires reconnect by reach; run power_thin.py reconnect if a chain is split)" % len(part))


def main():
    global SHIFT
    step = sys.argv[1] if len(sys.argv) > 1 else "plan"
    arg = lambda k, d=None: int(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d  # noqa: E731
    if step == "plan":
        cmd_plan()
    elif step == "place":
        SHIFT = arg("--shift", SHIFT)                       # the first run uses 4; dense areas (solar fields, plants) need a free 2x2 up to about 11 tiles away
        cmd_place(arg("--limit"))
    elif step == "verify":
        print("VERIFY", "clean" if cmd_verify() else "NOT clean")
    elif step == "wire":
        cmd_wire()
    elif step == "remove":
        cmd_remove(arg("--batch", 150), arg("--max-batches"))
    elif step == "undo":
        cmd_undo(arg("--last"))
    elif step == "status":
        bad, total = netcount()
        print("powered entities without a network: %d of %d | new poles recorded %d | removed %d"
              % (bad, total, len(load_new()), len(json.loads(REMOVED.read_text())) if REMOVED.exists() else 0))


if __name__ == "__main__":
    main()
