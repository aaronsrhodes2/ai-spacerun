"""Replace Fulgora's lightning rods with lightning collectors (the Captain's order, 2026-11-14).

    python scripts/fulgora_collectors.py study              # prototype numbers, rods per network, power state (read-only)
    python scripts/fulgora_collectors.py plan               # sites, clusters, coverage proof -> fulgora_collectors_plan.json (read-only)
    python scripts/fulgora_collectors.py apply [--cluster N] [--dry]   # one cluster at a time, saves first, rolls back on failure
    python scripts/fulgora_collectors.py storm [--seconds 125]          # measure strikes captured over one day (rods + collectors)
    python scripts/fulgora_collectors.py verify             # accumulators, no_power, damage, counts vs the snapshot taken at apply
    python scripts/fulgora_collectors.py undo [--cluster N] # remove that cluster's collectors, put its recorded rods back

Rules (the Captain's): only tools["place_entities"] places things; nothing is spawned; only the rods a collector replaces
are removed; a cluster's collectors are placed FIRST (so the area is never unprotected), checked on the same electric
network as the rods they replace, and only then are the rods removed. Any check failing destroys that cluster's new
collectors again and leaves the rods. State is kept in scripts/fulgora_collectors_state.json, so apply is idempotent per cluster.

Why fewer collectors than rods: a strike goes to an attractor when the strike point is within its range. Epic rod range
28.5, epic collector 47.5 (wiki table, Space Age; efficiency 38% vs 76%). A collector within 17 tiles of a rod has a disc
(47.5) that contains the rod's whole disc (28.5 + 17 = 45.5), so protection area, strike catchment and every structure's
protection margin can only grow. Greedy set cover picks the fewest sites; each must lie in the supply area of a pole of
the same electric network as the rods it replaces. Drain is per entity, so fewer entities also lose less to drain.
"""
import json
import math
import sys
import time
from pathlib import Path

from _game import tools

HERE = Path(__file__).resolve().parent
PLAN = HERE / "fulgora_collectors_plan.json"
STATE = HERE / "fulgora_collectors_state.json"
ROD_R, COL_R, COVER = 28.5, 47.5, 17.0   # epic ranges (wiki), max rod-to-collector distance
SURF = "fulgora"


def L(s):
    """Collapse a Lua snippet to one line (RCON takes one line; no Lua string literal below holds a space)."""
    return " ".join(s.split())


def lua(s):
    return tools["run_lua"](L(s))


def load(p, default):
    return json.loads(p.read_text()) if p.exists() else default


def save(p, d):
    p.write_text(json.dumps(d, indent=1))


# ---------------------------------------------------------------- queries
def rods():
    r = lua("""local s=game.surfaces.fulgora local o={} for _,e in ipairs(s.find_entities_filtered{name='lightning-rod'}) do
      o[#o+1]=string.format('%.1f,%.1f,%s,%s,%d',e.position.x,e.position.y,e.quality.name,tostring(e.electric_network_id),e.health) end
      rcon.print(table.concat(o,';'))""")
    out = []
    for x in r.split(";"):
        a = x.split(",")
        out.append(dict(x=float(a[0]), y=float(a[1]), q=a[2], net=int(a[3]) if a[3] != "nil" else None, hp=int(a[4])))
    return out


def structures():
    pts = []
    for part in range(4):
        r = lua("""local s=game.surfaces.fulgora local o={} local i=0 for _,e in ipairs(s.find_entities_filtered{force='player'}) do i=i+1
          if i%4==""" + str(part) + """ and e.type~='lightning-attractor' and e.type~='transport-belt' and e.type~='pipe' then
          o[#o+1]=string.format('%.1f,%.1f',e.position.x,e.position.y) end end rcon.print(table.concat(o,';'))""")
        pts += [tuple(map(float, x.split(","))) for x in r.split(";") if x]
    return pts


def snapshot():
    """Power and health state: accumulators per network, no_power count, damaged count, entity counts."""
    r = lua("""local s=game.surfaces.fulgora local acc={} local accn={} for _,e in ipairs(s.find_entities_filtered{name='accumulator',force='player'}) do
      local k=tostring(e.electric_network_id) acc[k]=(acc[k] or 0)+e.energy/1e6 accn[k]=(accn[k] or 0)+1 end
      local np,lp,dam,tot,att=0,0,0,0,{} local ct={}
      for _,e in ipairs(s.find_entities_filtered{force='player'}) do tot=tot+1 ct[e.type]=(ct[e.type] or 0)+1
        if e.type=='lightning-attractor' then att[e.name]=(att[e.name] or 0)+1 end
        if e.status==defines.entity_status.no_power then np=np+1 elseif e.status==defines.entity_status.low_power then lp=lp+1 end
        if e.health and e.prototype.get_max_health(e.quality)>e.health then dam=dam+1 end end
      local ids={} for k,v in pairs(accn) do ids[#ids+1]=k..':'..v end table.sort(ids)
      rcon.print(helpers.table_to_json({tick=game.tick,day=s.daytime,acc=acc,accn=ids,no_power=np,low_power=lp,damaged=dam,total=tot,att=att,types=ct}))""")
    return json.loads(r)


def pole_nets():
    return lua("""local s=game.surfaces.fulgora local o={} for _,e in ipairs(s.find_entities_filtered{name='lightning-collector',force='player'}) do
      o[#o+1]=string.format('%.1f,%.1f,%s,%s',e.position.x,e.position.y,e.quality.name,tostring(e.electric_network_id)) end rcon.print(table.concat(o,';'))""")


# ---------------------------------------------------------------- study
def study():
    print(lua("""local o={} for _,n in ipairs({'lightning-rod','lightning-collector'}) do local p=prototypes.entity[n]
      o[#o+1]=n..' tiles='..p.tile_width..'x'..p.tile_height..' collision='..serpent.line(p.collision_box)..' group='..tostring(p.fast_replaceable_group)..
      ' buffer_MJ='..(p.electric_energy_source_prototype.buffer_capacity/1e6)..' layers='..serpent.line(p.collision_mask.layers) end
      rcon.print(table.concat(o,string.char(10)))"""))
    print("Range, efficiency and drain are not exposed by LuaEntityPrototype in 2.1.24; wiki epic values used: "
          "rod range 28.5 / efficiency 38% (1 GJ per strike -> ~380 MJ), collector range 47.5 / 76% (~760 MJ). Different "
          "fast_replaceable_group, so no fast replace: place then remove.")
    rs = rods()
    by = {}
    for r in rs:
        by.setdefault(r["net"], []).append(r)
    print(len(rs), "rods; per electric network:", {k: len(v) for k, v in by.items()})
    print(json.dumps({k: v for k, v in snapshot().items() if k != "types"}))


# ---------------------------------------------------------------- plan
def candidates_near(cx, cy):
    r = lua("""local s=game.surfaces.fulgora local out={} for dx=-""" + "20" + """,20 do for dy=-20,20 do local x,y=""" + f"{cx}" + """+dx,""" + f"{cy}" + """+dy
      if s.can_place_entity{name='lightning-collector',position={x,y},force='player',build_check_type=defines.build_check_type.manual} then
      local nets={} for _,p in ipairs(s.find_entities_filtered{type='electric-pole',position={x,y},radius=25,force='player'}) do
      local ok,d=pcall(function() return p.prototype.get_supply_area_distance(p.quality) end) if not ok or not d then d=p.prototype.supply_area_distance end
      if math.abs(p.position.x-x)<=d+0.7 and math.abs(p.position.y-y)<=d+0.7 then nets[p.electric_network_id]=true end end
      local l={} for k,_ in pairs(nets) do l[#l+1]=k end if #l>0 then out[#out+1]=x..','..y..','..table.concat(l,'/') end end end end
      rcon.print(table.concat(out,';'))""")
    res = []
    for t in r.split(";"):
        if t:
            x, y, n = t.split(",")
            res.append((float(x), float(y), {int(i) for i in n.split("/")}))
    return res


def split_big(chosen, k, size=9):
    """Batches stay small: a cluster of more than `size` collectors is cut into x-ordered slices of about `size`."""
    for cl in range(k):
        cs = sorted([c for c in chosen if c["cluster"] == cl], key=lambda c: (c["x"], c["y"]))
        if len(cs) > size:
            parts = math.ceil(len(cs) / size)
            for i, c in enumerate(cs):
                j = i * parts // len(cs)
                if j:
                    c["cluster"] = k + j - 1
            k += parts - 1
    return k


def plan():
    rs = rods()
    cand = {}
    for i, r in enumerate(rs):
        for (x, y, nets) in candidates_near(round(r["x"]), round(r["y"])):
            if math.hypot(x - r["x"], y - r["y"]) <= COVER:
                cand[(x, y)] = nets
        if i % 20 == 0:
            print("candidates scanned", i, "of", len(rs), "sites so far", len(cand), flush=True)
    chosen = []
    unc = {}
    for i, r in enumerate(rs):
        unc.setdefault(r["net"], set()).add(i)
    for net, left in unc.items():
        left = set(left)
        while left:
            best = None
            for (x, y), nets in cand.items():
                if net not in nets:
                    continue
                if any(abs(x - c["x"]) < 2 and abs(y - c["y"]) < 2 for c in chosen):
                    continue
                cov = [i for i in left if math.hypot(x - rs[i]["x"], y - rs[i]["y"]) <= COVER]
                if not cov:
                    continue
                score = (len(cov), -sum(math.hypot(x - rs[i]["x"], y - rs[i]["y"]) for i in cov))
                if best is None or score > best[0]:
                    best = (score, x, y, cov)
            if best is None:
                print("NO SITE for rods", [(rs[i]["x"], rs[i]["y"]) for i in left], "net", net)
                break
            _, x, y, cov = best
            chosen.append(dict(x=x, y=y, net=net, rods=[(rs[i]["x"], rs[i]["y"]) for i in cov]))
            left -= set(cov)
    # clusters: connected groups of chosen collectors in one network, linked when within 45 tiles
    n = len(chosen)
    lab = [-1] * n
    k = 0
    for i in range(n):
        if lab[i] >= 0:
            continue
        stack = [i]
        lab[i] = k
        while stack:
            a = stack.pop()
            for b in range(n):
                if lab[b] < 0 and chosen[b]["net"] == chosen[a]["net"] and math.hypot(chosen[a]["x"] - chosen[b]["x"], chosen[a]["y"] - chosen[b]["y"]) <= 45:
                    lab[b] = k
                    stack.append(b)
        k += 1
    for c, l in zip(chosen, lab):
        c["cluster"] = l
    k = split_big(chosen, k)
    # coverage proof against structures (rods as the old reference)
    pts = structures()
    worse = 0
    far = 0
    for (x, y) in pts:
        old = min(math.hypot(x - r["x"], y - r["y"]) for r in rs)
        new = min(math.hypot(x - c["x"], y - c["y"]) for c in chosen)
        if (COL_R - new) < (ROD_R - old) - 1e-6:
            worse += 1
        if new > COL_R - 5:
            far += 1
    plan_d = dict(rods=len(rs), collectors=chosen, structures=len(pts), margin_worse=worse, within5_of_edge=far)
    save(PLAN, plan_d)
    print(f"{len(rs)} rods -> {len(chosen)} collectors in {k} clusters; structures checked {len(pts)}; "
          f"margin(range - distance) worse than with rods: {worse}; within 5 of a collector's edge: {far}")
    for c in range(k):
        cs = [x for x in chosen if x["cluster"] == c]
        print(" cluster", c, "net", cs[0]["net"], "collectors", len(cs), "replaces", sum(len(x["rods"]) for x in cs), "rods")


# ---------------------------------------------------------------- apply / undo
def place(specs, dry):
    j = json.dumps(specs)
    r = json.loads(tools["place_entities"](j, surface=SURF, dry_run=dry, clear_trees=False))
    if not isinstance(r.get("failed"), list):
        r["failed"] = list(r["failed"].values()) if r.get("failed") else []
    return r


def apply(cluster, dry):
    p = load(PLAN, None)
    if not p:
        sys.exit("run plan first")
    st = load(STATE, dict(saved=False, done={}, before=None))
    if cluster is None:
        todo = sorted({c["cluster"] for c in p["collectors"]})
    else:
        todo = [cluster]
    for cl in todo:
        if str(cl) in st["done"] and st["done"][str(cl)].get("status") == "done":
            print("cluster", cl, "already done")
            continue
        cs = [c for c in p["collectors"] if c["cluster"] == cl]
        specs = [dict(name="lightning-collector", x=c["x"], y=c["y"], params=dict(quality="epic")) for c in cs]
        d = place(specs, True)
        print("cluster", cl, "dry run:", d["placed"], "placeable", d["failed"][:3])
        if d["failed"] or dry:
            if d["failed"]:
                print("  blocked; replan")
            if dry or d["failed"]:
                continue
        if not st["saved"]:
            print(tools["save_game"]("skippy"))
            st["saved"] = True
            st["before"] = snapshot()
            save(STATE, st)
        before = snapshot()
        r = place(specs, False)
        print("  placed", r["placed"], r["failed"])
        # same-network check: each collector's network must equal the network of one of the rods it replaces
        ok = r["placed"] == len(specs)
        bad = []
        for c in cs:
            q = lua("""local s=game.surfaces.fulgora local e=s.find_entities_filtered{name='lightning-collector',position={""" + f"{c['x']},{c['y']}" + """},radius=0.5}[1]
              rcon.print(e and (tostring(e.electric_network_id)..','..e.quality.name) or 'none')""")
            nid, qual = (q.split(",") + [""])[:2]
            rodnets = lua("""local s=game.surfaces.fulgora local o={} """ + "".join(
                f"local e=s.find_entities_filtered{{name='lightning-rod',position={{{rx},{ry}}},radius=0.5}}[1] o[#o+1]=e and tostring(e.electric_network_id) or 'x' "
                for rx, ry in c["rods"][:30]) + """rcon.print(table.concat(o,','))""").split(",")
            if nid == "none" or nid not in rodnets or qual != "epic":
                bad.append((c["x"], c["y"], nid, qual))
        if bad or not ok:
            print("  ROLLBACK cluster", cl, "bad:", bad)
            destroy_collectors(cs)
            st["done"][str(cl)] = dict(status="rolled-back", bad=bad)
            save(STATE, st)
            continue
        removed = remove_rods(cs)
        after = snapshot()
        same_acc = before["accn"] == after["accn"]
        degrade = after["no_power"] > before["no_power"]
        print(f"  removed {len(removed)} rods; accumulators/network unchanged: {same_acc}; no_power {before['no_power']} -> {after['no_power']}; "
              f"total entities {before['total']} -> {after['total']} (expected {-len(removed)+len(cs)})")
        if not same_acc or degrade:
            print("  REVERT cluster", cl)
            undo_cluster(st, cl, removed, cs)
            continue
        st["done"][str(cl)] = dict(status="done", collectors=[(c["x"], c["y"]) for c in cs], rods=removed, t=time.time())
        save(STATE, st)


def destroy_collectors(cs):
    for c in cs:
        lua("""local s=game.surfaces.fulgora local e=s.find_entities_filtered{name='lightning-collector',position={""" + f"{c['x']},{c['y']}" + """},radius=0.5}[1] if e then e.destroy{raise_destroy=true} end rcon.print('ok')""")


def remove_rods(cs):
    seen = set()
    removed = []
    for c in cs:
        for (rx, ry) in c["rods"]:
            if (rx, ry) in seen:
                continue
            seen.add((rx, ry))
            r = lua("""local s=game.surfaces.fulgora local e=s.find_entities_filtered{name='lightning-rod',position={""" + f"{rx},{ry}" + """},radius=0.3}[1]
              if e and e.force.name=='player' then local q=e.quality.name local n=e.electric_network_id e.destroy{raise_destroy=true} rcon.print(q..','..tostring(n)) else rcon.print('none') end""")
            if r != "none":
                q, n = r.split(",")
                removed.append(dict(x=rx, y=ry, quality=q, net=n))
    return removed


def undo_cluster(st, cl, removed, cs):
    if removed:
        specs = [dict(name="lightning-rod", x=r["x"], y=r["y"], params=dict(quality=r["quality"])) for r in removed]
        print("  rods back:", place(specs, False))
    destroy_collectors(cs)
    st["done"][str(cl)] = dict(status="undone")
    save(STATE, st)


def undo(cluster):
    st = load(STATE, None)
    p = load(PLAN, None)
    if not st:
        sys.exit("nothing applied")
    for k, v in list(st["done"].items()):
        if v.get("status") != "done" or (cluster is not None and int(k) != cluster):
            continue
        cs = [c for c in p["collectors"] if c["cluster"] == int(k)]
        undo_cluster(st, int(k), v["rods"], cs)


# ---------------------------------------------------------------- measure
def storm(seconds):
    """Poll attractor buffers about every 1.5 s of real time over `seconds`; count jumps of 100 MJ or more as strikes."""
    q = L("""local s=game.surfaces.fulgora local o={} for _,e in ipairs(s.find_entities_filtered{type='lightning-attractor',force='player'}) do
      if e.name~='fulgoran-ruin-attractor' then o[#o+1]=string.format('%s,%.1f,%.1f,%d',string.sub(e.name,11,11),e.position.x,e.position.y,e.energy/1e6) end end
      local a=0 for _,e in ipairs(s.find_entities_filtered{name='accumulator',force='player'}) do a=a+e.energy end
      rcon.print(game.tick..'|'..string.format('%.3f',s.daytime)..'|'..math.floor(a/1e6)..'|'..table.concat(o,';'))""")
    prev, strikes = {}, {"r": [], "c": []}
    t_end = time.time() + seconds
    first = last = None
    acc = []
    while time.time() < t_end:
        tick, day, a, body = tools["run_lua"](q).split("|")
        cur = {}
        for it in body.split(";"):
            k, x, y, e = it.split(",")
            cur[(k, x, y)] = int(e)
        for key, e in cur.items():
            if key in prev and e - prev[key] >= 100:
                strikes[key[0]].append(e - prev[key])
        prev = cur
        first = first or int(tick)
        last = int(tick)
        acc.append(int(a))
        time.sleep(1.2)
    mins = (last - first) / 3600
    for k, name in (("r", "rod"), ("c", "collector")):
        v = strikes[k]
        n_att = sum(1 for key in prev if key[0] == k)
        print(f"{name}: {n_att} on the map, {len(v)} strikes seen, mean {sum(v)/len(v) if v else 0:.0f} MJ, total {sum(v)} MJ over {mins:.2f} game minutes "
              f"= {sum(v)/mins if mins else 0:.0f} MJ/min")
    print("accumulators MJ min/max over the window:", min(acc), max(acc))


def verify():
    st = load(STATE, {})
    now = snapshot()
    b = st.get("before")
    print("now:", json.dumps({k: v for k, v in now.items() if k not in ("types", "acc")}))
    if b:
        print("before:", json.dumps({k: v for k, v in b.items() if k not in ("types", "acc")}))
        lost = {t: b["types"].get(t, 0) - now["types"].get(t, 0) for t in b["types"] if b["types"].get(t, 0) > now["types"].get(t, 0) and t != "lightning-attractor"}
        print("entity types that LOST members since the snapshot (destroyed by lightning?):", lost or "none")
    print("collectors:", pole_nets()[:400])


if __name__ == "__main__":
    a = sys.argv[1:]
    cmd = a[0] if a else "study"
    cl = int(a[a.index("--cluster") + 1]) if "--cluster" in a else None
    if cmd == "study":
        study()
    elif cmd == "plan":
        plan()
    elif cmd == "apply":
        apply(cl, "--dry" in a)
    elif cmd == "undo":
        undo(cl)
    elif cmd == "storm":
        storm(int(a[a.index("--seconds") + 1]) if "--seconds" in a else 125)
    elif cmd == "verify":
        verify()
    else:
        sys.exit(__doc__)
