#!/usr/bin/env python3
"""Surplus-seed sink on Gleba (2026-11-16, the Captain: "seed sink"). Seeds are a by-product of fruit processing; when their output chests filled up the processors
stopped and the whole cell starved (docs/gleba-stable-cell.md). The processors' output rows are packed, so the sink stands apart and robots feed it:
  requester chest (asks SEED_ASK seeds) -> bulk inserter (filter: the seed; runs only while the network holds more than SEED_OVER of it, so the farms and the
  vault always have first call) -> recycler (keeps 25%, retires 75% of each pass) -> bulk inserter -> passive provider chest (the residue; robots carry it back
  to the requester, so nothing piles up in a dead end).
Seeds are 4 MJ of fuel each and the soil recipes use them: a heat or soil consumer can take from the same provider chests first, and that is better than recycling.
One unit per seed kind; yumako first (the one that filled up). Site: free, powered, in the main logistic network, found by search.
Usage: gleba_seed_sink.py [seed ...] [--apply]     (default seed: yumako-seed; dry run prints the site)"""
import json
import sys

from _game import tools

APPLY = "--apply" in sys.argv
SEEDS = [a for a in sys.argv[1:] if not a.startswith("--")] or ["yumako-seed"]
SEED_OVER, SEED_ASK = 1000, 400

SITE = ("local s=game.surfaces.gleba local f=game.forces.player local M=defines.build_check_type.manual local function ok(n,x,y,d) return s.can_place_entity{name=n,position={x,y},direction=d,force=f,build_check_type=M} end "
        "local main=s.find_logistic_network_by_position({90,26},f) local res=nil "
        "for cx=60.5,140.5 do for cy=14.5,70.5 do if not res then local net=s.find_logistic_network_by_position({cx,cy},f) if net and main and net.network_id==main.network_id and ok('requester-chest',cx,cy,0) and ok('bulk-inserter',cx+1,cy,12) and ok('recycler',cx+3.5,cy+0.5,4) and ok('bulk-inserter',cx+6,cy,12) and ok('passive-provider-chest',cx+7,cy,0) then "
        "local pw=#s.find_entities_filtered{type='electric-pole',position={cx+3.5,cy},radius=3.2}>0 or #s.find_entities_filtered{name='substation',position={cx+3.5,cy},radius=8}>0 if pw then res=cx..','..cy end end end end end rcon.print(tostring(res))")

CFG = ("local s=game.surfaces.gleba local n=0 for _,u in pairs({UNITS}) do local c=s.find_entities_filtered{name='requester-chest',position={u[1],u[2]},radius=0.3}[1] local i=s.find_entities_filtered{name='bulk-inserter',position={u[1]+1,u[2]},radius=0.3}[1] "
       "if c and i then local rp=c.get_requester_point() rp.trash_not_requested=true local sec=rp.sections_count>0 and rp.get_section(1) or rp.add_section() sec.set_slot(1,{value={type='item',name=u[3],quality='normal',comparator='='},min=ASK}) "
       "i.use_filters=true i.inserter_filter_mode='whitelist' i.set_filter(1,u[3]) local cb=i.get_or_create_control_behavior() cb.connect_to_logistic_network=true cb.logistic_condition={first_signal={type='item',name=u[3]},comparator='>',constant=OVER} "
       "local o=s.find_entities_filtered{name='bulk-inserter',position={u[1]+6,u[2]},radius=0.3}[1] if o then o.use_filters=true o.inserter_filter_mode='whitelist' o.set_filter(1,u[3]) end n=n+1 end end rcon.print('sink units set '..n)")


def main():
    todo, units = [], []
    used = set()
    for seed in SEEDS:
        site = tools["run_lua"](SITE).strip()
        print(seed, "site", site)
        if site == "nil":
            return
        cx, cy = [float(v) for v in site.split(",")]
        while (cx, cy) in used:
            cy += 4
        used.add((cx, cy))
        q = {"quality": "epic"}
        todo += [{"name": "requester-chest", "x": cx, "y": cy, "direction": 0, "params": q}, {"name": "bulk-inserter", "x": cx + 1, "y": cy, "direction": 12, "params": q},
                 {"name": "recycler", "x": cx + 3.5, "y": cy + 0.5, "direction": 4, "params": q}, {"name": "bulk-inserter", "x": cx + 6, "y": cy, "direction": 12, "params": q},
                 {"name": "passive-provider-chest", "x": cx + 7, "y": cy, "direction": 0, "params": q}]
        units.append("{%s,%s,'%s'}" % (cx, cy, seed))
        break                                                  # one unit per run: the next seed needs its own site search after this one stands
    r = json.loads(tools["place_entities"](json.dumps(todo), surface="gleba", dry_run=not APPLY))
    print("placed" if APPLY else "dry", r.get("placed"), "failed", json.dumps(r.get("failed") or [])[:300])
    if APPLY:
        print(tools["run_lua"](CFG.replace("UNITS", ",".join(units)).replace("ASK", str(SEED_ASK)).replace("OVER", str(SEED_OVER))))


if __name__ == "__main__":
    main()
