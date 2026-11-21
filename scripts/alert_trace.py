#!/usr/bin/env python3
"""Trace every "missing material" alert from the ghost back to where the item is made (read-only).
Why (the Captain, 2026-11-20): "find every alert in the game and trace back ... from the request all the way to where it's going to
be produced by the replicator to make sure that there's no logistic problem stopping them."

For each planet, every item its entity ghosts, tile ghosts and item-request proxies (modules) wait for, and per item the whole chain:
  NEED     how many, how many of the ghosts stand outside construction range (robots can never build those), network stock
  PAD      the landing pad's request slots for the item (group, min, where from): no slot = nothing ever asks orbit for it
  SHIPS    every platform that holds the item or asks for it, with where it is and its route
  SOURCE   per planet: stock in the logistic networks, made in the last hour and last 10 minutes (production statistics), machines
           standing on that recipe now, and the recipe's ingredients with the stock of each on that planet
  SILOS    per planet: rocket silos, how many hold a finished rocket
The verdict line names the first broken link.
Usage: alert_trace.py [PLANET ...]"""
import json
import sys

from _game import tools

L = tools["run_lua"]

NEEDS = ("local s=game.surfaces['%s'] local f=game.forces.player local need={} local function add(n,q,c,cov) local k=n..'/'..q need[k]=need[k] or {n=n,q=q,c=0,out=0} need[k].c=need[k].c+c if not cov then need[k].out=need[k].out+c end end "
         "local function cov(e) local nw=s.find_logistic_networks_by_construction_area(e.position,f) return #nw>0 end "
         "for _,e in pairs(s.find_entities_filtered{type='entity-ghost'}) do local it=e.ghost_prototype.items_to_place_this if it and it[1] then add(it[1].name,e.quality.name,it[1].count or 1,cov(e)) end end "
         "for _,e in pairs(s.find_entities_filtered{type='tile-ghost'}) do local it=e.ghost_prototype.items_to_place_this if it and it[1] then add(it[1].name,'normal',it[1].count or 1,cov(e)) end end "
         "for _,e in pairs(s.find_entities_filtered{type='item-request-proxy'}) do for _,r in pairs(e.item_requests) do add(r.name,r.quality or 'normal',r.count,cov(e)) end end "
         "local o={} for _,v in pairs(need) do o[#o+1]=v end rcon.print(helpers.table_to_json(o))")

TRACE = ("local f=game.forces.player local item,q,planet='%s','%s','%s' local o={pad={},ships={},src={},silos={}} local id={name=item,quality=q} "
         "local function imp(fl) return fl.import_from and (type(fl.import_from)=='string' and fl.import_from or fl.import_from.name) or 'any' end "
         "local s=game.surfaces[planet] local stock=0 for _,nw in pairs(f.logistic_networks[planet] or {}) do stock=stock+nw.get_item_count(id) end o.stock=stock "
         "for _,pad in pairs(s.find_entities_filtered{type='cargo-landing-pad'}) do o.padstock=(o.padstock or 0)+pad.get_inventory(defines.inventory.cargo_landing_pad_main).get_item_count(id) "
         "for _,pt in pairs(pad.get_logistic_point()) do if pt.mode==defines.logistic_mode.requester then for _,sec in pairs(pt.sections) do for k=1,sec.filters_count do local fl=sec.get_slot(k) "
         "if fl and fl.value and fl.value.name==item then o.pad[#o.pad+1]={g=sec.group,on=sec.active,min=fl.min,q=fl.value.quality,from=imp(fl)} end end end end end end "
         "for i,p in pairs(f.platforms) do if p.hub and p.hub.valid then local has=p.hub.get_inventory(defines.inventory.hub_main).get_item_count(id) local asks={} "
         "for _,pt in pairs(p.hub.get_logistic_point()) do if pt.mode==defines.logistic_mode.requester then for _,sec in pairs(pt.sections) do for k=1,sec.filters_count do local fl=sec.get_slot(k) "
         "if fl and fl.value and fl.value.name==item and (fl.min or 0)>0 then asks[#asks+1]=(sec.group or '')..(sec.active and '' or '(off)')..' '..fl.min..' from '..imp(fl) end end end end end "
         "if has>0 or #asks>0 then local rt={} if p.schedule then for _,r in pairs(p.schedule.records) do rt[#rt+1]=r.station end end "
         "o.ships[#o.ships+1]={n=p.name:gsub('%%[.-%%]',''):gsub('^%%s+',''),has=has,asks=asks,at=p.space_location and p.space_location.name or 'in flight',paused=p.paused,route=table.concat(rt,'>')} end end end "
         "local rec for _,r in pairs(f.recipes) do if r.enabled and not r.hidden and r.name==item then rec=r end end if not rec then for _,r in pairs(f.recipes) do if r.enabled and not r.hidden and r.products[1] and r.products[1].name==item and not r.name:find('recycling') then rec=r break end end end "
         "o.recipe=rec and rec.name or nil "
         "for _,pn in pairs{'nauvis','vulcanus','gleba','fulgora','aquilo'} do local ps=game.surfaces[pn] if ps then local st=0 for _,nw in pairs(f.logistic_networks[pn] or {}) do st=st+nw.get_item_count(id) end "
         "local ip=f.get_item_production_statistics(ps) local h=ip.get_flow_count{name=id,category='input',precision_index=defines.flow_precision_index.one_hour,count=true} local m=ip.get_flow_count{name=id,category='input',precision_index=defines.flow_precision_index.ten_minutes,count=true} "
         "local mach=0 if rec then for _,e in pairs(ps.find_entities_filtered{type={'assembling-machine','furnace'}}) do local r=e.get_recipe() if r and r.name==rec.name then mach=mach+1 end end end "
         "local ing={} if rec then for _,g in pairs(rec.ingredients) do local c=0 if g.type=='item' then for _,nw in pairs(f.logistic_networks[pn] or {}) do c=c+nw.get_item_count(g.name) end else c=-1 end ing[#ing+1]={n=g.name,a=g.amount,c=c} end end "
         "o.src[#o.src+1]={p=pn,stock=st,hour=h,ten=m,mach=mach,ing=ing} local sl=ps.find_entities_filtered{type='rocket-silo'} local rdy=0 for _,e in pairs(sl) do if e.rocket_silo_status==defines.rocket_silo_status.rocket_ready then rdy=rdy+1 end end o.silos[pn]=rdy..'/'..#sl end end "
         "rcon.print(helpers.table_to_json(o))")


PADS = ("local f=game.forces.player local s=game.surfaces['%s'] local need={} for _,pad in pairs(s.find_entities_filtered{type='cargo-landing-pad'}) do local inv=pad.get_inventory(defines.inventory.cargo_landing_pad_main) "
        "for _,pt in pairs(pad.get_logistic_point()) do if pt.mode==defines.logistic_mode.requester then for _,sec in pairs(pt.sections) do if sec.active then for k=1,sec.filters_count do local fl=sec.get_slot(k) "
        "if fl and fl.value and (fl.min or 0)>0 then local id={name=fl.value.name,quality=fl.value.quality or 'normal'} local have=0 for _,nw in pairs(f.logistic_networks['%s'] or {}) do have=have+nw.get_item_count(id) end "
        "local short=fl.min-have if short>0 then local k=id.name..'/'..id.quality need[k]=need[k] or {n=id.name,q=id.quality,c=0,out=0} need[k].c=math.max(need[k].c,short) end end end end end end end end "
        "local o={} for _,v in pairs(need) do o[#o+1]=v end rcon.print(helpers.table_to_json(o))")


def requests(planets):
    """Every landing-pad request that is short, traced like a ghost. Prints one verdict line each."""
    import io
    import contextlib
    for p in planets:
        needs = lst(json.loads(L(PADS % (p, p))))
        needs.sort(key=lambda n: -n["c"])
        print(chr(10) + "== %s: %d pad requests short" % (p, len(needs)))
        for n in needs:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                v = trace(p, n)
            print("  %-34s short %-7d %s" % (n["n"] + ("" if n["q"] == "normal" else "/" + n["q"]), n["c"], v))


def lst(v):
    return v if isinstance(v, list) else []


def trace(planet, n):
    t = json.loads(L(TRACE % (n["n"], n["q"], planet)))
    name = n["n"] + ("" if n["q"] == "normal" else "/" + n["q"])
    print("\n%s x%d on %s%s | in the network %d, on the pad %d" % (name, n["c"], planet, (" (%d OUT of robot range)" % n["out"]) if n["out"] else "", t["stock"], t.get("padstock") or 0))
    pads = lst(t["pad"])
    print("  PAD    " + ("; ".join("%s%s min %s %s from %s" % (p["g"] or "(no group)", "" if p["on"] else " OFF", p["min"], p.get("q") or "", p["from"]) for p in pads) or "NO request slot for it"))
    ships = lst(t["ships"])
    for sh in ships:
        print("  SHIP   %-28s at %-9s%s holds %d%s  route %s" % (sh["n"][:28], sh["at"], " PAUSED" if sh["paused"] else "", sh["has"], ("; asks " + ", ".join(lst(sh["asks"]))) if lst(sh["asks"]) else "", sh["route"]))
    if not ships:
        print("  SHIP   none holds it, none asks for it")
    best = None
    for s in lst(t["src"]):
        if s["stock"] or s["hour"] or s["mach"]:
            ing = ", ".join("%s %s (%s)" % (g["a"], g["n"], "fluid" if g["c"] < 0 else g["c"]) for g in lst(s["ing"]))
            print("  SOURCE %-8s stock %d, made last hour %d, last 10 min %d, machines on the recipe %d, silos ready %s | needs %s" % (s["p"], s["stock"], s["hour"], s["ten"], s["mach"], t["silos"].get(s["p"], "?"), ing))
            if s["p"] != planet and (best is None or s["stock"] > best["stock"]):
                best = s
    print("  RECIPE %s (%s)" % (t.get("recipe"), t.get("cat")))
    short = n["c"] - t["stock"]
    carriers = [sh for sh in ships if planet in sh["route"] or sh["at"] == planet]
    if n["out"] == n["c"]:
        v = "every ghost stands outside construction range: no robot can build it"
    elif short <= 0:
        v = "the network holds enough: robots are busy, out of range, or the item is reserved"
    elif not pads:
        v = "nothing asks orbit for it: no pad request slot"
    elif not carriers:
        v = "the pad asks, but no ship on a route to %s holds it or asks its home for it" % planet
    elif best is None:
        v = "no planet holds it, makes it or has made it in the last hour: nothing is producing it"
    elif best["stock"] < short and best["hour"] == 0:
        v = "%s holds only %d of the %d still needed and made none in the last hour: making is the limit" % (best["p"], best["stock"], short)
    elif not any(sh["has"] for sh in carriers):
        v = "source %s has stock %d; ships ask for it but none carries any yet: waiting on launches or on the ship's turn" % (best["p"], best["stock"])
    else:
        v = "in transit: %d aboard ships on the route" % sum(sh["has"] for sh in carriers)
    print("  VERDICT " + v)
    return v


def main():
    if sys.argv[1:2] == ["requests"]:
        requests(sys.argv[2:] or ["nauvis", "vulcanus", "gleba", "fulgora", "aquilo"])
        return
    planets = sys.argv[1:] or ["nauvis", "vulcanus", "gleba", "fulgora", "aquilo"]
    for p in planets:
        needs = json.loads(L(NEEDS % p))
        needs = sorted(lst(needs), key=lambda n: -n["c"])
        if not needs:
            print("== %s: nothing waits for material" % p)
            continue
        print("\n== %s: %d kinds of item waited for" % (p, len(needs)))
        for n in needs:
            trace(p, n)


if __name__ == "__main__":
    main()
