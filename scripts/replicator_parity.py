#!/usr/bin/env python3
"""Parity test for the Nauvis Replicator (the Captain, 2026-11-16: the Replicator work is a loop - analyze, simplify, edit, compact, TEST FOR PARITY, repeat).
Each round of the loop must leave the Replicator making the same things, with the same class of machine, about as fast. This script orders a fixed list of
items the way a real order arrives and records what happened.

How an order is placed: a temporary constant combinator (description `replicator-parity`) is wired to the red wire of the hub demand roboport (-352,-229), where
every unit reads the missing requests. It is removed after each order, also on error (`clean` removes a leftover one). Cells take the SMALLEST order first, so a
cell order is injected as 1; the furnace, fluid-assembler and chemical units take the LARGEST, so theirs is injected above whatever real demand is on the wire.
Products are real items made from real ingredients and stay in the network. Nothing is spawned. The pipe flush of the chemical unit (omni_fluid.cycle) runs
before each order, as the autopilot does.

ORDERS (chosen 2026-11-16 from what was in stock on Nauvis; nothing here needs biter eggs):
  cell1   arithmetic-combinator      partition 0 of 3; copper cable + electronic circuits
  cell2   assembling-machine-1       partition 1; iron plate, gears, circuits
  cell3   constant-combinator        partition 2; copper cable + circuits
  nested  piercing-shotgun-shell     a cell1 item whose sub-part, shotgun-shell, is a cell2 item with none in stock: another machine must make it first
  furnace stone-brick                the furnace unit (stone in stock)
  fasm    electric-engine-unit       fluid-assembler unit, lubricant
  fasm    processing-unit            fluid-assembler unit, sulfuric acid (a change of fluid)
  chem    sulfur                     chemical unit, two fluid inputs (water + petroleum gas), solid product
  chem    sulfuric-acid-barrel       chemical unit, fluid product (the filler C makes the barrel)
  chem    plastic-bar                chemical unit, one non-primary fluid, solid product
  BATCH   arithmetic-combinator + electric-engine-unit + plastic-bar at once (three units together: stalls, double-making)

Recorded per order: the unit and machine that took it, the recipe set, what its blue chest asked for, game ticks to the first product and to TARGET crafts,
crafts made, how many machines held the recipe at once (more than one = double-making), pass/fail (timeout TIMEOUT ticks).
Box counts (machines, combinators by kind, constants, chests, inserters, roboports, substations, built-on tiles) are stored with every run.

Usage: replicator_parity.py run        run the list and store the BASELINE (snapshots/replicator_parity.json)
       replicator_parity.py compare    run the list again and print a table against the baseline (snapshots/replicator_parity_last.json keeps the run)
       replicator_parity.py counts     only the box counts
       replicator_parity.py clean      remove a leftover injection combinator
       options: --only NAME[,NAME]  run only these orders (not stored as baseline)   --timeout TICKS"""
import datetime
import json
import sys
import time
from pathlib import Path

import omni_fluid
from _game import tools

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "snapshots" / "replicator_parity.json"
LAST = ROOT / "snapshots" / "replicator_parity_last.json"
BOX = (-355, -235, -289, -198)             # inside the wall
HUB = (-352, -229)
INJ = (-347.5, -230.5)                     # free tile east of the hub for the temporary constant combinator
TARGET = 3                                 # crafts to wait for
TIMEOUT = int(sys.argv[sys.argv.index("--timeout") + 1]) if "--timeout" in sys.argv else 18000      # game ticks (5 minutes)
SLACK = 900                                # compare: time differences under this many ticks are not a failure (robot flight noise)

ORDERS = [
    {"name": "cell1", "items": ["arithmetic-combinator"], "unit": "cell1", "inject": "small"},
    {"name": "cell2", "items": ["assembling-machine-1"], "unit": "cell2", "inject": "small"},
    {"name": "cell3", "items": ["constant-combinator"], "unit": "cell3", "inject": "small"},
    {"name": "nested", "items": ["piercing-shotgun-shell"], "unit": "cell1", "inject": "small", "sub": "shotgun-shell"},
    {"name": "furnace", "items": ["stone-brick"], "unit": "furnace", "inject": "big"},
    {"name": "fasm-lubricant", "items": ["electric-engine-unit"], "unit": "fasm", "inject": "big"},
    {"name": "fasm-acid", "items": ["processing-unit"], "unit": "fasm", "inject": "big"},
    {"name": "chem-two-fluid", "items": ["sulfur"], "unit": "chem", "inject": "big"},
    {"name": "chem-fluid-product", "items": ["sulfuric-acid-barrel"], "unit": "chem", "inject": "big"},
    {"name": "chem-solid", "items": ["plastic-bar"], "unit": "chem", "inject": "big"},
    {"name": "batch", "items": ["arithmetic-combinator", "electric-engine-unit", "plastic-bar"], "unit": "cell1+fasm+chem", "inject": "mixed",
     "kinds": {"arithmetic-combinator": "small", "electric-engine-unit": "big", "plastic-bar": "big"}},
]

L = tools["run_lua"]


def lua(code):
    return L(" ".join(code.split("\n")))


INJECT = r'''
local s=game.surfaces.nauvis local W=defines.wire_connector_id
local hub=s.find_entities_filtered{type='roboport',position={HUBX,HUBY},radius=1}[1]
if not hub then rcon.print('ERR no hub roboport') return end
local t=s.find_entities_filtered{name='constant-combinator',position={INJX,INJY},radius=0.4}[1]
if t and t.combinator_description~='replicator-parity' then rcon.print('ERR the injection tile holds another combinator') return end
if not t then if not s.can_place_entity{name='constant-combinator',position={INJX,INJY},force='player',build_check_type=defines.build_check_type.manual} then rcon.print('ERR the injection tile is not free') return end
  t=s.create_entity{name='constant-combinator',position={INJX,INJY},force='player',raise_built=true} t.combinator_description='replicator-parity' end
local big=0 local n=hub.get_circuit_network(W.circuit_red) if n and n.signals then for _,sg in pairs(n.signals) do if sg.count>big then big=sg.count end end end
local cb=t.get_or_create_control_behavior() while cb.sections_count>0 do cb.remove_section(1) end local sec=cb.add_section()
local k=0 for _,it in ipairs(ITEMS) do k=k+1 sec.set_slot(k,{value={type='item',name=it[1],quality='normal'},min=(it[2]=='small') and 1 or (big+1000)}) end
local c=t.get_wire_connector(W.circuit_red,true) c.disconnect_all() c.disconnect_all(defines.wire_origin.script)
c.connect_to(hub.get_wire_connector(W.circuit_red,true),false,defines.wire_origin.script)
rcon.print('OK '..game.tick..' '..big)
'''

REMOVE = ("local s=game.surfaces.nauvis local n=0 for _,t in pairs(s.find_entities_filtered{name='constant-combinator',position={INJX,INJY},radius=0.4}) do "
          "if t.combinator_description=='replicator-parity' then t.destroy() n=n+1 end end rcon.print('removed '..n)")

POLL = r'''
local s=game.surfaces.nauvis local f=game.forces.player local m={} for k,v in pairs(defines.entity_status) do m[v]=k end
local want={WANT} local out={tick=game.tick,paused=game.tick_paused,all={},takers={},net={}}
local hub=s.find_entities_filtered{type='roboport',position={HUBX,HUBY},radius=1}[1] local net=hub and hub.logistic_network
for it,_ in pairs(want) do out.net[it]=net and net.get_item_count(it) or -1 end
local function rname(e) local ok,r=pcall(function() if e.type=='furnace' then return e.previous_recipe end return e.get_recipe() end) if not ok or not r then return nil end
  local nm=r.name if type(nm)~='string' then nm=nm and nm.name end return nm end
local function asks(e) local best,bd=nil,1e9 for _,c in pairs(s.find_entities_filtered{name='requester-chest',position=e.position,radius=4.3,force=f}) do local d=(c.position.x-e.position.x)^2+(c.position.y-e.position.y)^2 if d<bd then bd=d best=c end end
  local t={} if best then local pt=best.get_logistic_point(defines.logistic_member_index.logistic_container) for _,fl in pairs(pt.filters or {}) do t[#t+1]=(fl.name or '?')..' '..tostring(fl.count) end end table.sort(t) return table.concat(t,', ') end
for _,e in pairs(s.find_entities_filtered{area={{BX1,BY1},{BX2,BY2}},force=f,type={'assembling-machine','furnace'}}) do
  local id=tostring(e.unit_number) out.all[id]=e.products_finished
  local rn=rname(e) if rn then local pr=prototypes.recipe[rn] if pr then for _,p in pairs(pr.products) do if p.type=='item' and want[p.name] and (e.type~='furnace' or e.status==defines.entity_status.working or e.is_crafting()) then
    out.takers[#out.takers+1]={id=id,item=p.name,name=e.name,x=e.position.x,y=e.position.y,recipe=rn,status=m[e.status] or '?',asks=asks(e)} end end end end
end
rcon.print(helpers.table_to_json(out))
'''

COUNTS = r'''
local s=game.surfaces.nauvis local f=game.forces.player local c={} local tiles=0 local n=0
for _,e in pairs(s.find_entities_filtered{area={{BX1,BY1},{BX2,BY2}},force=f}) do local t=e.type if t~='logistic-robot' and t~='construction-robot' and t~='wall' and t~='entity-ghost' and t~='item-request-proxy' then
  local k=t if t=='logistic-container' then k=e.name end c[k]=(c[k] or 0)+1 n=n+1 local b=e.bounding_box tiles=tiles+math.ceil(b.right_bottom.x-b.left_top.x-0.01)*math.ceil(b.right_bottom.y-b.left_top.y-0.01) end end
c.entities=n c.built_tiles=tiles c.box_tiles=((BX2)-(BX1))*((BY2)-(BY1))
c.combinators=(c['decider-combinator'] or 0)+(c['arithmetic-combinator'] or 0)+(c['selector-combinator'] or 0)
c.machines=(c['assembling-machine'] or 0)+(c['furnace'] or 0)
rcon.print(helpers.table_to_json(c))
'''


def fill(code, **kw):
    rep = {"HUBX": HUB[0], "HUBY": HUB[1], "INJX": INJ[0], "INJY": INJ[1], "BX1": BOX[0], "BY1": BOX[1], "BX2": BOX[2], "BY2": BOX[3]}
    rep.update(kw)
    for k, v in rep.items():
        code = code.replace(k, str(v))
    return code


def unit_table():
    """Where each unit's machines stand now, read from the scripts' own registries (so a compaction that moves a unit does not break the labels)."""
    out = []
    reg = json.loads((ROOT / "snapshots" / "replicator_cells.json").read_text())
    for name, c in reg.items():
        if c.get("surface", "nauvis") == "nauvis":
            for k in range(3):
                out.append((name, "m%d" % (k + 1), c["x"] + 7 * k + 1.5, c["y"] + 7.5))
    import omni_fluid_asm
    import omni_maker
    import repack_fasm
    fx, fy = repack_fasm.NEW
    out.append(("fasm", "P", fx + 0.5, fy + 0.5))
    out.append(("fasm", "E", fx + 0.5, fy - 2.5))
    cx, cy = omni_fluid.SITES["replicator"]["c"]
    for lab, dx, dy in (("plant", 0.5, 0.5), ("A", -0.5, -2.5), ("B", 3.5, -1.5), ("C", -0.5, 3.5), ("D", 3.5, 2.5)):
        out.append(("chem", lab, cx + dx, cy + dy))
    ox, oy = omni_maker.SITES["replicator"]
    out.append(("furnace", "F", ox + omni_maker.FX + 2.5, oy + 9.5))
    return out


def label(units, x, y):
    best = min(units, key=lambda u: (u[2] - x) ** 2 + (u[3] - y) ** 2)
    if (best[2] - x) ** 2 + (best[3] - y) ** 2 > 2.5:
        return "unknown", "@%s,%s" % (x, y)
    return best[0], best[1]


def counts():
    return json.loads(lua(fill(COUNTS)))


def poll(items):
    return json.loads(lua(fill(POLL, WANT=",".join("['%s']=true" % i for i in items))))


def remove():
    return lua(fill(REMOVE)).strip()


def run_order(order, units):
    items = order["items"]
    kinds = order.get("kinds") or {i: order["inject"] for i in items}
    res = {"name": order["name"], "items": {}, "ok": True}
    flush = omni_fluid.cycle("replicator")
    before = poll(items)
    if before.get("paused"):
        raise RuntimeError("the game is paused: nothing would be made")
    sub0 = poll([order["sub"]])["net"][order["sub"]] if order.get("sub") else None
    r = lua(fill(INJECT, ITEMS="{" + ",".join("{'%s','%s'}" % (i, kinds[i]) for i in items) + "}")).strip()
    if not r.startswith("OK"):
        raise RuntimeError("injection failed: " + r)
    t0 = int(r.split()[1])
    st = {i: {"takers": {}, "first": None, "done": None, "made": 0, "max_at_once": 0, "recipes": set(), "asks": set()} for i in items}
    try:
        tick = t0
        n = 0
        while tick - t0 < TIMEOUT:
            time.sleep(1.5)
            n += 1
            if n % 20 == 0:
                omni_fluid.cycle("replicator")
            p = poll(items)
            tick = p["tick"]
            now = {i: 0 for i in items}
            for t in p["takers"] or []:
                s = st[t["item"]]
                now[t["item"]] += 1
                s["takers"][t["id"]] = label(units, t["x"], t["y"])
                s["recipes"].add(t["recipe"])
                if t["asks"]:
                    s["asks"].add(t["asks"])
            for i in items:
                s = st[i]
                s["max_at_once"] = max(s["max_at_once"], now[i])
                s["made"] = sum((p["all"].get(u, 0) - before["all"].get(u, 0)) for u in s["takers"])
                if s["made"] >= 1 and s["first"] is None:
                    s["first"] = tick - t0
                if s["made"] >= TARGET and s["done"] is None:
                    s["done"] = tick - t0
            if all(st[i]["done"] is not None for i in items):
                break
    finally:
        remove()
    for i in items:
        s = st[i]
        ok = s["done"] is not None
        res["ok"] = res["ok"] and ok
        res["items"][i] = {"units": sorted({u for u, _ in s["takers"].values()}), "machines": sorted({"%s.%s" % um for um in s["takers"].values()}), "recipes": sorted(s["recipes"]),
                           "asks": sorted(s["asks"])[:3], "first_ticks": s["first"], "done_ticks": s["done"], "made": s["made"], "max_at_once": s["max_at_once"], "pass": ok}
    if order.get("sub"):
        res["sub"] = {"item": order["sub"], "stock_before": sub0, "nested": sub0 == 0}
    res["flush"] = flush
    # let the machines drop the recipe before the next order
    for _ in range(12):
        time.sleep(1.5)
        if not (poll(items)["takers"] or []):
            break
    return res


def run_all(only=None):
    print("clean:", remove())
    units = unit_table()
    out = {"when": datetime.datetime.now().isoformat(timespec="seconds"), "target_crafts": TARGET, "timeout_ticks": TIMEOUT, "counts": counts(), "orders": []}
    for order in ORDERS:
        if only and order["name"] not in only:
            continue
        try:
            res = run_order(order, units)
        except Exception as exc:  # noqa: BLE001
            remove()
            res = {"name": order["name"], "ok": False, "error": repr(exc), "items": {}}
        out["orders"].append(res)
        for i, d in res["items"].items():
            print("%-18s %-22s %-4s unit %-10s machines %-18s first %6s done %6s made %3d at-once %d" % (
                res["name"], i, "PASS" if d["pass"] else "FAIL", "+".join(d["units"]) or "-", ",".join(d["machines"]) or "-", d["first_ticks"], d["done_ticks"], d["made"], d["max_at_once"]), flush=True)
        if res.get("error"):
            print("%-18s ERROR %s" % (res["name"], res["error"]), flush=True)
    return out


def compare(base, new):
    fails = 0
    print("%-18s %-22s %-28s %-28s %s" % ("order", "item", "baseline (unit, made, done)", "now (unit, made, done)", "verdict"))
    old = {o["name"]: o for o in base["orders"]}
    for o in new["orders"]:
        b = old.get(o["name"])
        for i, d in o["items"].items():
            bd = (b or {}).get("items", {}).get(i)
            why = []
            if not bd:
                why.append("no baseline")
            else:
                if d["units"] != bd["units"]:
                    why.append("unit %s -> %s" % ("+".join(bd["units"]), "+".join(d["units"])))
                if d["recipes"] != bd["recipes"]:
                    why.append("recipe changed")
                if d["made"] < min(bd["made"], base.get("target_crafts", TARGET)):
                    why.append("made %d < %d" % (d["made"], bd["made"]))
                if bd["pass"] and not d["pass"]:
                    why.append("timed out")
                if bd["done_ticks"] and d["done_ticks"] and d["done_ticks"] > 1.5 * bd["done_ticks"] and d["done_ticks"] - bd["done_ticks"] > SLACK:
                    why.append("slower: %d vs %d ticks" % (d["done_ticks"], bd["done_ticks"]))
                if d["max_at_once"] > max(1, bd["max_at_once"]):
                    why.append("double-making: %d machines" % d["max_at_once"])
            fails += 1 if why else 0
            fmt = lambda x: "%s, %s, %s" % ("+".join(x["units"]) or "-", x["made"], x["done_ticks"]) if x else "-"
            print("%-18s %-22s %-28s %-28s %s" % (o["name"], i, fmt(bd), fmt(d), "FAIL: " + "; ".join(why) if why else "same"))
    bc, nc = base["counts"], new["counts"]
    print("box counts (baseline -> now): " + ", ".join("%s %s -> %s" % (k, bc.get(k), nc.get(k)) for k in ("machines", "combinators", "constant-combinator", "entities", "built_tiles", "box_tiles")))
    print("RESULT: %d difference(s)" % fails)
    return fails


def main():
    step = sys.argv[1] if len(sys.argv) > 1 else ""
    only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None
    if step == "clean":
        print(remove())
    elif step == "counts":
        print(json.dumps(counts(), indent=1, sort_keys=True))
    elif step == "run":
        out = run_all(only)
        if only:
            print("partial run: baseline not stored")
        else:
            BASE.write_text(json.dumps(out, indent=1, sort_keys=True))
            print("baseline stored:", BASE)
        print("counts:", json.dumps(out["counts"], sort_keys=True))
    elif step == "compare":
        if not BASE.exists():
            sys.exit("no baseline: run `replicator_parity.py run` first")
        new = run_all(only)
        LAST.write_text(json.dumps(new, indent=1, sort_keys=True))
        sys.exit(1 if compare(json.loads(BASE.read_text()), new) else 0)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
