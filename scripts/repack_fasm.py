#!/usr/bin/env python3
"""Repack step 1 (docs/replicator-compaction-plan.md): move the Replicator's fluid-assembler unit from (-330,-178) (south spill) to (-352,-185) inside the box.
Steps: retire (mark the old unit for deconstruction by robots, contents return to the network) | wall-south (remove the old internal south wall line y=-189.5) | build [--apply] | status.
Usage: repack_fasm.py retire | wall-south | build [--apply] | status"""
import json
import sys

import omni_fluid_asm as fa
from _game import tools

OLD, NEW = (-352, -192), (-346, -219)        # moved 6 east (2026-11-14), then 27 north with a folded table (2026-11-16, omni_fluid_asm.TABLE_FOLD)


def entities(site):
    n = len(fa.recipes())
    return fa.layout(*site) + fa.table_entities(site[0], site[1], n)


def retire():
    ents = entities(OLD)
    arr = "{" + ",".join("{'%s',%s,%s}" % (e["name"], e["x"], e["y"]) for e in ents) + "}"
    lua = ("local s=game.surfaces.nauvis local f=game.forces.player local n,m=0,0 for _,t in ipairs(" + arr + ") do local e=s.find_entities_filtered{name=t[1],position={t[2],t[3]},radius=0.35,force=f}[1] "
           "if e then if e.order_deconstruction(f) then n=n+1 end else m=m+1 end end rcon.print('marked '..n..' for deconstruction, '..m..' not found')")
    print(tools["run_lua"](lua))


def wall_south():
    print(tools["run_lua"]("local s=game.surfaces.nauvis local n=0 for _,w in ipairs(s.find_entities_filtered{name='stone-wall',area={{-367,-190.2},{-287,-188.8}},force=game.forces.player}) do w.destroy() n=n+1 end rcon.print('removed '..n..' old south wall pieces')"))


def build(apply):
    n, r = fa.place(NEW[0], NEW[1], apply)
    print("items", n, "placed" if apply else "dry run", r.get("placed"), "failed", json.dumps(r.get("failed") or [])[:500])
    if apply:
        print(tools["run_lua"](fa.sub(fa.CONFIG, *NEW)))


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else ""
    if step == "retire":
        retire()
    elif step == "wall-south":
        wall_south()
    elif step == "build":
        build("--apply" in sys.argv)
    elif step == "status":
        for site in (OLD, NEW):
            print(site, tools["run_lua"](fa.sub(fa.STATUS, *site)))
    else:
        print(__doc__)
