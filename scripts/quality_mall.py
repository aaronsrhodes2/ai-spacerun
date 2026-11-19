#!/usr/bin/env python3
"""Quality modules on Nauvis (the Captain, 2026-11-18: the Nauvis Wheel is to become the legendary product producer; its asteroid
reprocessing loop needs quality modules in every crusher, and none existed anywhere).
Robot-fed units on the pattern of scripts/module_tier3.py (requester chest, inserter, assembler, inserter, provider chest), beside the
tier-3 mall: four make quality module 1, two make quality module 2, one stands ready for quality module 3 (that recipe needs a
superconductor from Fulgora; Nauvis holds none on 2026-11-18, so the unit waits).
Steps: plan | build --apply | config | status
Usage: quality_mall.py plan ; quality_mall.py build --apply ; quality_mall.py status"""
import json
import sys

import module_tier3 as M
from _game import tools

L = tools["run_lua"]
X0, Y0 = -140, -482
UNITS = ["quality-module"] * 4 + ["quality-module-2"] * 2 + ["quality-module-3"]
BAR = 2                         # one output slot a unit (50 modules): processing units are scarce on Nauvis (455 in the network)

STATUS = ("local s=game.surfaces.nauvis local m={} for k,v in pairs(defines.entity_status) do m[v]=k end local o={} for i=1,%d do local ux=%d+3*(i-1) local a=s.find_entities_filtered{name='assembling-machine-3',position={ux+1.5,%d+3.5},radius=0.6}[1] "
          "if a then local r=a.get_recipe() o[#o+1]=(r and r.name or 'no recipe')..' '..tostring(m[a.status])..' made '..a.products_finished end end "
          "local net=s.find_logistic_network_by_position(%s,'player') o[#o+1]='in the network: quality module 1 '..net.get_item_count('quality-module')..', 2 '..net.get_item_count('quality-module-2')..', 3 '..net.get_item_count('quality-module-3')..', processing units '..net.get_item_count('processing-unit')..', superconductors '..net.get_item_count('superconductor') "
          "rcon.print(table.concat(o,string.char(10)))") % (len(UNITS), X0, Y0, M.NET)


BARS = ("local s=game.surfaces.nauvis local n=0 for i=1,%d do local pv=s.find_entities_filtered{name='passive-provider-chest',position={%d+3*(i-1)+1.5,%d+6.5},radius=0.3}[1] if pv then pv.get_inventory(defines.inventory.chest).set_bar(%d) n=n+1 end end rcon.print('output chests barred to one slot: '..n)") % (len(UNITS), X0, Y0, BAR)


def config():
    return L(M.CONFIG.replace("UNITS", "{" + ",".join("'%s'" % u for u in UNITS) + "}").replace("X0", str(X0)).replace("Y0", str(Y0))).strip() + " | " + L(BARS).strip()


def main():
    step = sys.argv[1] if len(sys.argv) > 1 else "status"
    ents = M.layout(X0, Y0, UNITS)
    for e in ents:
        e["params"] = {"quality": "legendary"}
    if step in ("plan", "build"):
        apply = step == "build" and "--apply" in sys.argv
        r = json.loads(tools["place_entities"](json.dumps(ents), surface="nauvis", dry_run=not apply))
        print("placed" if apply else "dry run: would place", r.get("placed"), "of", len(ents), "failed", json.dumps(r.get("failed") or [])[:500])
        if apply:
            print(config())
    elif step == "config":
        print(config())
    elif step == "status":
        print(L(STATUS))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
