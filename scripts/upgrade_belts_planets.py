#!/usr/bin/env python3
"""Belt / inserter upgrades on the four planets' grounds (the Captain: "turbo ... where appropriate; don't upgrade if power is an issue").
Usage: upgrade_belts_planets.py [dry|status|apply] [SURFACE ...]      (default: dry run, all four; `--apply` also works)

Decisions (2026-11-14, measured; see `status` for live numbers):
  vulcanus  1,266 express belts -> turbo. Belts draw no power. Wired belts (circuit connections) are left alone and reported.
  fulgora      92 express belts -> turbo, same way. Its 228 bulk inserters stay: a bulk->stack swap adds up to 2.8 kW each
               (prototype: bulk 2,800 W max, stack 5,600 W max, drain 16.7 W both) = up to +638 kW on a lightning grid that fell
               from 18,140 MJ to ~2,400 MJ at full load; no inserter is a measured bottleneck.
  gleba     nothing. 786 belts are already turbo. The 200 plain belts are the core's deliberate lines (junk belt y 2.5, egg belt y 17.5,
               science belt y 18.5: dead-end queues that burn what rots, wired to the egg gate / reserve sensors) plus the lab pack belt
               x 127.5, y 22..43 (full and backed up: more speed gains nothing). Inserters: the core is throttled on purpose; 132 bulk
               -> stack would add up to +370 kW with no bottleneck.
  aquilo    nothing. No belts; 15 fast + 7 bulk inserters on a one-turbine grid with another agent building; no measured benefit.
`apply` only does the belt kinds named in BELTS, in bounded batches; re-runnable (replaced belts leave the query)."""
import json
import sys

from _game import tools

OLD, NEW = "express-transport-belt", "turbo-transport-belt"
BELTS = {"vulcanus": OLD, "fulgora": OLD}          # surface -> belt name to upgrade
BATCH = 300
ALL = ["gleba", "vulcanus", "fulgora", "aquilo"]


def jl(t):
    try:
        return json.loads(t)
    except Exception:
        raise SystemExit("lua said: " + t)


def lua(src):
    return tools["run_lua"](" ".join(src.strip().splitlines()))


def survey(s):
    return jl(lua("""
local s=game.surfaces['%s'] local o={belts={},ins={},status={}}
for _,e in pairs(s.find_entities_filtered{force='player',type={'transport-belt','underground-belt','splitter'}}) do o.belts[e.name]=(o.belts[e.name] or 0)+1 end
for _,e in pairs(s.find_entities_filtered{force='player',type='inserter'}) do o.ins[e.name]=(o.ins[e.name] or 0)+1 end
local lp,np,n=0,0,0 for _,e in pairs(s.find_entities_filtered{force='player',type={'inserter','assembling-machine','lab','furnace','mining-drill','roboport'}}) do n=n+1
 if e.status==defines.entity_status.low_power then lp=lp+1 elseif e.status==defines.entity_status.no_power then np=np+1 end end
o.status={machines=n,low_power=lp,no_power=np}
local a,ae,am=0,0,0 for _,e in pairs(s.find_entities_filtered{force='player',type='accumulator'}) do a=a+1 ae=ae+e.energy end
o.acc={n=a,MJ=math.floor(ae/1e6)}
local w=0 for _,e in pairs(s.find_entities_filtered{force='player',name='%s'}) do local c=e.get_wire_connector(defines.wire_connector_id.circuit_red,false) local g=e.get_wire_connector(defines.wire_connector_id.circuit_green,false) if (c and c.connection_count>0) or (g and g.connection_count>0) then w=w+1 end end
o.wired_old=w
rcon.print(helpers.table_to_json(o))""" % (s, BELTS.get(s, OLD))))


def batch(s, old, new):
    return jl(lua("""
local s=game.surfaces['%s'] local L=s.find_entities_filtered{force='player',name='%s'} local done,skip,fail=0,0,0
for i=1,math.min(#L,%d) do local e=L[i] if e.valid then
 local r,g=e.get_wire_connector(defines.wire_connector_id.circuit_red,false),e.get_wire_connector(defines.wire_connector_id.circuit_green,false)
 if (r and r.connection_count>0) or (g and g.connection_count>0) then skip=skip+1 else
  local p,d,f,q=e.position,e.direction,e.force,e.quality
  local n=s.create_entity{name='%s',position=p,direction=d,force=f,fast_replace=true,spill=false,quality=q,raise_built=true}
  if n then done=done+1 else fail=fail+1 end end end end
rcon.print(helpers.table_to_json({done=done,skip=skip,fail=fail,left=#L}))""" % (s, old, BATCH, new)))


def main():
    args = [a for a in sys.argv[1:]]
    mode = "dry"
    for a in list(args):
        if a in ("dry", "status", "apply", "--apply"):
            mode = "apply" if a in ("apply", "--apply") else a
            args.remove(a)
    surfaces = args or ALL
    if mode == "apply":
        print(tools["save_game"]("skippy"))
    for s in surfaces:
        print("==", s, json.dumps(survey(s)))
        if mode != "apply" or s not in BELTS:
            continue
        stuck = 0
        for _ in range(12):
            r = batch(s, BELTS[s], NEW)
            print(" batch", r)
            stuck += r["skip"] + r["fail"]
            if r["left"] - r["done"] <= stuck or r["done"] == 0:
                break
        print("  after:", json.dumps(survey(s)))


main()
