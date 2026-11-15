#!/usr/bin/env python3
"""Replicator console (the Captain, 2026-11-14: "visualization so we can easily see what is going on" in the Replicator).
Display panels (icon + two short lines) with a lamp beside each, inside the Replicator's walled area, read-only: `update` reads the
Replicator with one Lua query and writes panel texts, icons and lamp colours. Nothing here is wired to the Replicator's logic.

Where (footprint in scripts/replicator_viz_site.txt):
  north row  tile row y -234, x -366..-289, 26 cells (lamp, panel, one free tile): DEMAND (what the network is missing, top 8, from the
             demand wire of the hub roboport) and MACHINES (the three Replicator CELLS, scripts/replicator_cell.py, shown as CELL1-3: machine 1's status, item and made count,
             all three chests (TOTALS counts every machine); the fluid unit, the furnace unit; three cells each:
             status + item being made + made so far; what the blue requester chest asks for / what the network lacks; red chest contents).
  south row  tile row y -192, same x: ORBITAL (what shuttles ask the silos for that the network cannot cover), STALLS (demanded items the
             Replicator cannot make, with the reason), TOTALS (made, made per minute, robots), STOCK (raw inputs in the network).
Colours: GREEN working / served, AMBER waiting / being made, RED stuck, needs input or cannot make, WHITE heading, GREY idle / empty.

Usage: replicator_viz.py build [--apply]   place the lamps and panels (idempotent; dry run unless --apply), then set icons
       replicator_viz.py update            refresh every cell (one Lua read + one write, ~1 s); the local autopilot runs it every VIZ_EVERY cycles
       replicator_viz.py status            print every cell's reading
"""
import json
import sys
import time
from pathlib import Path

from _game import tools

STATE = Path(__file__).resolve().parent.parent / "snapshots" / "replicator_viz_state.json"
X0, PITCH, NCELL = -354, 2, 26          # pitch 2 (lamp and panel side by side) since the 2026-11-14 repack: the console is 52 wide, was 78
ROW_N, ROW_S = -233.5, -198.5          # tile centres of the north row (y -234) and the south row (y -199; was -192 until the 2026-11-14 repack)
COL = {"green": (.1, 1, .2), "amber": (1, .65, 0), "red": (1, .05, .05), "white": (1, 1, 1), "grey": (.35, .35, .35)}
CI = {c: i + 1 for i, c in enumerate(COL)}
I = lambda n: ("item", n)
SIG = lambda n: ("virtual", n)

OK_WORK = {"working", "normal"}
WAIT = {"item_ingredient_shortage", "fluid_ingredient_shortage", "no_ingredients", "no_input_fluid", "waiting_for_source_items"}
FULL = {"full_output", "waiting_for_space_in_destination"}
POWER = {"no_power", "low_power", "no_fuel"}


def lua(code):
    return tools["run_lua"](" ".join(code.split("\n"))).strip()


def layout():
    """-> list of (key, kind, row_y, slot): kind 'h' heading or 'c' cell. Slots 0..25 along each row."""
    north = [("hd", "h")] + [("d%d" % i, "c") for i in range(8)]
    for u in ("M1", "M2", "M3", "FL", "FU"):
        north += [(u + "s", "c"), (u + "a", "c"), (u + "o", "c")]
    north.insert(9, ("hm", "h"))
    south = [("ho", "h"), ("o0", "c"), ("o1", "c"), ("o2", "c"), ("hs", "h")] + [("s%d" % i, "c") for i in range(4)] + \
            [("ht", "h"), ("t0", "c"), ("t1", "c"), ("t2", "c"), ("hk", "h")] + [("k%d" % i, "c") for i in range(5)]
    out = []
    for row_y, seq in ((ROW_N, north), (ROW_S, south)):
        assert len(seq) <= NCELL, len(seq)
        for i, (k, kind) in enumerate(seq):
            out.append({"key": k, "kind": kind, "y": row_y, "lx": X0 + 0.5 + PITCH * i})
    return out


HEADINGS = {"hd": ("DEMAND", I("logistic-robot")), "hm": ("MACHINES", I("assembling-machine-3")), "ho": ("ORBITAL", I("rocket-silo")),
            "hs": ("STALLS", SIG("signal-skull")), "ht": ("TOTALS", SIG("signal-info")), "hk": ("STOCK", I("iron-plate"))}
STOCK = ["iron-plate", "copper-plate", "steel-plate", "plastic-bar", "electronic-circuit"]


# ------------------------------------------------------------------------------------------------ build
def build(apply):
    cs = layout()
    ents = []
    for c in cs:
        ents.append({"name": "display-panel", "x": c["lx"] + 1, "y": c["y"], "direction": 0})
        if c["kind"] == "c" or c["kind"] == "h":
            ents.append({"name": "small-lamp", "x": c["lx"], "y": c["y"], "direction": 0})
    have = set()
    for ya in (-234.5, -199.0):
        r = lua("local s=game.surfaces.nauvis local o={} for _,e in pairs(s.find_entities_filtered{area={{-367,%s},{-288,%s}},name={'small-lamp','display-panel'}}) do o[#o+1]=e.name..'@'..e.position.x..','..e.position.y end rcon.print(table.concat(o,';'))" % (ya, ya + 1.5))
        have |= set(r.split(";")) if r else set()
    todo = [e for e in ents if "%s@%s,%s" % (e["name"], e["x"], e["y"]) not in have]
    r = json.loads(tools["place_entities"](json.dumps(todo), surface="nauvis", dry_run=not apply))
    print("entities wanted", len(ents), "to place", len(todo), "placed", r.get("placed"), "failed", json.dumps(r.get("failed") or [])[:600])
    if apply:
        print(update(True)["total_s"], "s")


# ------------------------------------------------------------------------------------------------ data
Q = """
local s=game.surfaces.nauvis local f=game.forces.player local W=defines.wire_connector_id local o={}
local X,Y,C,CY=-354,-231,-300,-224
local function at(n,x,y) return s.find_entities_filtered{name=n,position={x,y},radius=0.6}[1] end
local function stn(e) if not e then return 'none' end for a,v in pairs(defines.entity_status) do if v==e.status then return a end end return 'none' end
local function sigs(e,id) local l={} if e then local n=e.get_circuit_network(id) if n and n.signals then for _,x in pairs(n.signals) do if (x.signal.type==nil or x.signal.type=='item') and x.count~=0 then l[#l+1]={x.signal.name,x.count} end end end end table.sort(l,function(a,b) return a[2]>b[2] end) return l end
local function fmt(l,m) local t={} for i,v in ipairs(l) do if i>m then break end t[#t+1]=v[1]..':'..v[2] end return table.concat(t,',') end
local rp=at('roboport',X+2,Y+2) local net=rp and rp.logistic_network
local function stock(n) return net and net.get_item_count(n) or 0 end
local function chest(c) local l={} local tot=0 if c then for _,it in pairs(c.get_inventory(defines.inventory.chest).get_contents()) do l[#l+1]={it.name,it.count} tot=tot+it.count end end return l,tot end
local ms={} local function addset(e) for _,v in ipairs(sigs(e,W.circuit_green)) do ms[v[1]]=true end end
local CELLS={{-352,-213},{-331,-213},{-310,-213}} for _,c in ipairs(CELLS) do addset(at('constant-combinator',c[1]+8.5,c[2]+2.5)) end addset(at('constant-combinator',X+23+5.5,Y+6.5)) addset(at('constant-combinator',C-5.5,CY-5.5))
local prods={} local made=0
local function unit(tag,am,rqs,pvs,sel)
local r=am and am.get_recipe() local rn=r and r.name
if am and not rn then local ok,p=pcall(function() return am.previous_recipe end) if ok and p then rn=(type(p.name)=='string') and p.name or p.name.name end end
local pn,pt='','item' if rn and prototypes.recipe[rn] then local p1=prototypes.recipe[rn].products[1] pn=p1.name pt=p1.type end
local lkn,lkc,an,at1,ac=' ',0,0,' ',0
for _,rq in ipairs(rqs) do local w=sigs(rq,W.circuit_green) local inv=rq.get_inventory(defines.inventory.chest) for _,v in ipairs(w) do an=an+1 if v[2]>ac then ac=v[2] at1=v[1] end local need=v[2]-inv.get_item_count(v[1]) if need>0 then local d=need-stock(v[1]) if d>0 and d>lkc then lkn=v[1] lkc=d end end end end
local rn2,rt=' ',0 for _,pv in ipairs(pvs) do local l,t=chest(pv) rt=rt+t for _,v in ipairs(l) do if rn2==' ' then rn2=v[1] end end end
local mk=am and am.products_finished or 0 made=made+mk
if r and (stn(am)=='working' or stn(am)=='normal') then prods[pn]=true end
local ch=sel and sigs(sel,W.combinator_output_green)[1] or nil
o[#o+1]='U|'..tag..'|'..stn(am)..'|'..(rn or ' ')..'|'..pn..'|'..pt..'|'..mk..'|'..an..'|'..at1..'|'..lkn..'|'..lkc..'|'..rn2..'|'..rt..'|'..(ch and ch[1] or ' ') end
for i,c in ipairs(CELLS) do local rqs,pvs={},{} for k=0,2 do rqs[#rqs+1]=at('requester-chest',c[1]+7*k+1.5,c[2]+4.5) pvs[#pvs+1]=at('passive-provider-chest',c[1]+7*k+1.5,c[2]+10.5) end for k=1,2 do local m=at('assembling-machine-3',c[1]+7*k+1.5,c[2]+7.5) if m then made=made+m.products_finished end end unit('M'..i,at('assembling-machine-3',c[1]+1.5,c[2]+7.5),rqs,pvs,at('selector-combinator',c[1]+4.5,c[2]+5)) end
unit('FU',at('electric-furnace',X+25.5,Y+9.5),{at('requester-chest',X+25.5,Y+6.5)},{at('passive-provider-chest',X+25.5,Y+12.5)},at('selector-combinator',X+29.5,Y+8))
unit('FL',at('chemical-plant',C+0.5,CY+0.5),{at('requester-chest',C-2.5,CY+0.5),at('requester-chest',C-0.5,CY-5.5),at('requester-chest',C+3.5,CY-4.5)},{at('passive-provider-chest',C+3.5,CY+0.5),at('passive-provider-chest',C-3.5,CY+3.5),at('passive-provider-chest',C+6.5,CY+2.5)},at('selector-combinator',C-4.5,CY-3))
local function why(it) local best=nil local bc=nil for name,r in pairs(prototypes.recipe) do if not r.hidden and not name:find('recycling') then for _,p in pairs(r.products) do if p.name==it then local k=r.categories[1] if not k then k=next(r.categories) end for _,i in pairs(r.ingredients) do if i.type=='fluid' then k='fluid' end end if not best or k=='fluid' then best=k end end end end end return best or 'raw' end
local dem=sigs(rp,W.circuit_red) local pos={} for _,v in ipairs(dem) do if v[2]>0 then pos[#pos+1]=v end end
local dl={} for i,v in ipairs(pos) do if i<=8 then dl[#dl+1]=v[1]..':'..v[2]..':'..(ms[v[1]] and 1 or 0)..':'..(prods[v[1]] and 1 or 0) end end
o[#o+1]='D|'..#pos..'|'..table.concat(dl,',')
local un={} for _,si in pairs(s.find_entities_filtered{name='rocket-silo'}) do local l=sigs(si,W.circuit_green) if #l>0 then for _,v in ipairs(l) do if v[2]>0 then un[#un+1]=v end end break end end
table.sort(un,function(a,b) return a[2]>b[2] end) local ul={} for i,v in ipairs(un) do if i<=3 then ul[#ul+1]=v[1]..':'..v[2]..':'..(ms[v[1]] and 1 or 0)..':'..(prods[v[1]] and 1 or 0) end end
o[#o+1]='O|'..#un..'|'..table.concat(ul,',')
local sl={} local nst=0 local seen={} for _,v in ipairs(pos) do if not ms[v[1]] then nst=nst+1 if #sl<4 then sl[#sl+1]=v[1]..':'..v[2]..':'..why(v[1]) end end end
o[#o+1]='S|'..nst..'|'..table.concat(sl,',')
local st={} for _,n in pairs({'iron-plate','copper-plate','steel-plate','plastic-bar','electronic-circuit'}) do st[#st+1]=n..':'..stock(n) end
o[#o+1]='K|'..table.concat(st,',')
o[#o+1]='T|'..made..'|'..(net and net.available_logistic_robots or -1)..'|'..(net and net.all_logistic_robots or -1)
rcon.print(table.concat(o,';'))
"""


def short(n):
    n = float(n)
    return "%.1fk" % (n / 1000) if abs(n) >= 10000 else "%d" % round(n)


def pretty(name):
    return name.replace("-", " ")


def icon_of(name, typ="item"):
    return ("fluid" if typ == "fluid" else "item", name)


def unit_cells(u, p, prefix, label):
    """p = U record fields -> three cells (status, asks, out)."""
    (st, rn, pn, pt, made, asks, top, lk, lkc, red, rt, chosen) = p
    asks, lkc, rt = int(asks), int(float(lkc)), int(float(rt))
    if st in OK_WORK:
        word, col = "work", "green"
    elif st in WAIT:
        word, col = ("wait", "amber") if asks > 0 else ("idle", "grey")
    elif st in FULL:
        word, col = "full", "red"
    elif st in POWER:
        word, col = "power", "red"
    else:
        word, col = "idle", "grey"
    cells = {}
    ic = icon_of(pn, pt) if pn.strip() and st != "no_recipe" else I("assembling-machine-3")
    cells[prefix + "s"] = (ic, "%s %s %s" % (label, word, short(made)), col)
    if lk.strip():
        cells[prefix + "a"] = (I(lk), "lacks~%s" % short(lkc), "red" if col in ("amber", "red") else "amber")
    elif asks > 0:
        cells[prefix + "a"] = (I(top), "asks %d~ok" % asks, "green")
    else:
        cells[prefix + "a"] = (I("requester-chest"), "asks~none", "grey")
    if rt > 0 and red.strip():
        cells[prefix + "o"] = (I(red), "out~%s" % short(rt), "green")
    else:
        cells[prefix + "o"] = (I("passive-provider-chest"), "out~0", "grey")
    return cells, int(made)


def compute():
    t0 = time.time()
    raw = lua(Q)
    qs = time.time() - t0
    rec = {}
    units = {}
    for part in raw.split(";"):
        f = part.split("|")
        if f[0] == "U":
            units[f[1]] = f[2:]
        else:
            rec[f[0]] = f[1:]
    t = {k: (v[0], None, "white") for k, v in HEADINGS.items()}
    t = {k: (HEADINGS[k][1], HEADINGS[k][0], "white") for k in HEADINGS}
    total_made = 0
    for key, label, prefix in (("M1", "CELL1", "M1"), ("M2", "CELL2", "M2"), ("M3", "CELL3", "M3"), ("FL", "FLUID", "FL"), ("FU", "FURN", "FU")):
        cells, mk = unit_cells(key, units[key], prefix, label)
        t.update(cells)
        total_made += mk

    def flagged(entry):
        n, c, m, mk = entry.split(":")[:4]
        return n, int(float(c)), (("green" if mk == "1" else "amber") if m == "1" else "red")
    nd, dl = rec["D"][0], [x for x in rec["D"][1].split(",") if x]
    for i in range(8):
        if i < len(dl):
            n, c, col = flagged(dl[i])
            t["d%d" % i] = (I(n), "need~%s" % short(c), col)
        elif i == 0:
            t["d0"] = (I("logistic-robot"), "nothing~missing", "green")
        else:
            t["d%d" % i] = (None, "", "grey")
    no, ol = int(rec["O"][0]), [x for x in rec["O"][1].split(",") if x]
    cols = [flagged(x)[2] for x in ol]
    t["o0"] = (I("rocket-silo"), "asks %d~items" % no if no else "asks 0~ok", "green" if no == 0 else ("red" if "red" in cols else "amber"))
    for i in (0, 1):
        if i < len(ol):
            n, c, col = flagged(ol[i])
            t["o%d" % (i + 1)] = (I(n), "short~%s" % short(c), col)
        else:
            t["o%d" % (i + 1)] = (None, "", "grey")
    ns, sl = int(rec["S"][0]), [x for x in rec["S"][1].split(",") if x]
    for i in range(4):
        if i < len(sl):
            n, c, why = sl[i].split(":")
            why = "science" if n.endswith("science-pack") else why
            t["s%d" % i] = (I(n), "%s~%s" % (why[:9], short(c)), "red")
        elif i == 0:
            t["s0"] = (SIG("signal-check"), "no stalls", "green")
        else:
            t["s%d" % i] = (None, "", "grey")
    if ns > len(sl):
        t["s3"] = (SIG("signal-skull"), "+%d stalled" % (ns - len(sl) + 1), "red")
    stock = {x.split(":")[0]: int(float(x.split(":")[1])) for x in rec["K"][0].split(",")}
    for i, n in enumerate(STOCK):
        v = stock.get(n, 0)
        t["k%d" % i] = (I(n), "%s" % short(v), "red" if v == 0 else ("amber" if v < 100 else "green"))
    made, avail, allb = (int(float(x)) for x in rec["T"])
    prev = {}
    try:
        prev = json.loads(STATE.read_text())
    except (OSError, ValueError):
        pass
    now = time.time()
    rate = prev.get("rate", 0.0)
    if "made" in prev and now - prev["time"] > 20 and made >= prev["made"]:
        rate = (made - prev["made"]) * 60.0 / (now - prev["time"])
    if "made" not in prev or now - prev["time"] > 20:
        STATE.parent.mkdir(exist_ok=True)
        STATE.write_text(json.dumps({"made": made, "time": now, "rate": rate}))
    t["t0"] = (I("assembling-machine-3"), "%.1f/min" % rate, "green" if rate > 0.05 else "grey")
    t["t1"] = (I("assembling-machine-3"), "%s made" % short(made), "grey")
    t["t2"] = (I("logistic-robot"), "bots %s" % short(avail), "red" if allb <= 0 or avail == 0 else ("amber" if avail < 0.1 * allb else "green"))
    return t, qs


def esc(s):
    return s.replace("\\", "").replace("'", "").replace("\n", " ").replace("~", " ")


def update(set_icons=False):
    t0 = time.time()
    t, qs = compute()
    rows = []
    for c in layout():
        ic, text, col = t.get(c["key"], (None, "", "grey"))
        rows.append("{%s,%s,'%s',%d,'%s','%s'}" % (c["lx"], c["y"], esc(text), CI[col], ic[0] if ic else "", ic[1] if ic else ""))
    pal = "{" + ",".join("{r=%s,g=%s,b=%s}" % COL[k] for k in COL) + "}"
    code = ("local s=game.surfaces.nauvis local pal=%s local n=0 local nl=string.char(10) for _,q in pairs({%s}) do local p=s.find_entities_filtered{name='display-panel',position={q[1]+1,q[2]},radius=0.3}[1] "
            "if p then p.display_panel_text=q[3]:gsub('~',nl) p.display_panel_always_show=true p.display_panel_show_in_chart=false if q[5]=='' then p.display_panel_icon=nil else p.display_panel_icon={type=q[5],name=q[6]} end n=n+1 end "
            "local l=s.find_entities_filtered{name='small-lamp',position={q[1],q[2]},radius=0.3}[1] if l then l.always_on=true l.color=pal[q[4]] end end rcon.print(n)") % (pal, ",".join(rows))
    assert len(code) < 60000, len(code)
    n = lua(code)
    return {"panels": n, "query_s": round(qs, 2), "total_s": round(time.time() - t0, 2), "cells": {k: "%s | %s [%s]" % (v[0][1] if v[0] else "-", v[1].replace("~", " / "), v[2]) for k, v in t.items()}}


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "update"
    if cmd == "build":
        build("--apply" in sys.argv)
    else:
        r = update()
        if cmd == "status":
            print(json.dumps(r, indent=1))
        else:
            print({k: r[k] for k in ("panels", "query_s", "total_s")})
