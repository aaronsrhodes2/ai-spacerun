#!/usr/bin/env python3
"""Quality module 3 cell on Fulgora (2026-11-20, stage 0 of docs/fulgora-legendary-workshop.md): two robot-fed epic AM3 units at (124,-40),
each requester chest -> inserter -> assembler -> inserter -> provider chest. Recipe: 5 advanced circuit, 5 processing unit, 1 superconductor,
4 quality module 2 (the last two and the circuits come from Nauvis by qm_relay.py). Usage: qm3_cell.py [build --apply | config | status]"""
import json
import sys

import module_tier3 as M
from _game import tools

X0, Y0, N = 124, -40, 2
REQ = {"advanced-circuit": 20, "processing-unit": 20, "superconductor": 4, "quality-module-2": 16}
CONFIG = ("local s=game.surfaces.fulgora local n=0 for i=1,%d do local ux=%d+3*(i-1) local m=s.find_entities_filtered{name='assembling-machine-3',position={ux+1.5,%d+3.5},radius=0.6}[1] "
          "local rq=s.find_entities_filtered{name='requester-chest',position={ux+1.5,%d+0.5},radius=0.3}[1] local pv=s.find_entities_filtered{name='passive-provider-chest',position={ux+1.5,%d+6.5},radius=0.3}[1] "
          "if m and rq and pv then m.set_recipe('quality-module-3') local lp=rq.get_logistic_point(defines.logistic_member_index.logistic_container) local sec=lp.get_section(1) or lp.add_section() local k=0 "
          "for nm,c in pairs(%s) do k=k+1 sec.set_slot(k,{value={type='item',name=nm,quality='normal'},min=c}) end pv.get_inventory(defines.inventory.chest).set_bar(3) n=n+1 end end rcon.print('units set '..n)")
STATUS = ("local s=game.surfaces.fulgora local m={} for k,v in pairs(defines.entity_status) do m[v]=k end local o={} for i=1,%d do local ux=%d+3*(i-1) local a=s.find_entities_filtered{name='assembling-machine-3',position={ux+1.5,%d+3.5},radius=0.6}[1] "
          "if a then o[#o+1]=tostring(m[a.status])..' made '..a.products_finished end end local pv=s.find_entities_filtered{name='passive-provider-chest',position={%d+1.5,%d+6.5},radius=0.3}[1] "
          "o[#o+1]='first output chest qm3: '..(pv and pv.get_inventory(defines.inventory.chest).get_item_count('quality-module-3') or -1) rcon.print(table.concat(o,string.char(10)))")

if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "status"
    tab = "{" + ",".join("['%s']=%d" % kv for kv in REQ.items()) + "}"
    if step == "build":
        ents = M.layout(X0, Y0, ["quality-module-3"] * N)
        apply = "--apply" in sys.argv
        r = json.loads(tools["place_entities"](json.dumps(ents), surface="fulgora", dry_run=not apply, clear_trees=False))
        print("placed" if apply else "dry run:", r.get("placed"), "of", len(ents), "failed", json.dumps(r.get("failed") or [])[:400])
        if apply:
            print(tools["run_lua"](CONFIG % (N, X0, Y0, Y0, Y0, tab)).strip())
    elif step == "config":
        print(tools["run_lua"](CONFIG % (N, X0, Y0, Y0, Y0, tab)).strip())
    else:
        print(tools["run_lua"](STATUS % (N, X0, Y0, X0, Y0)))
