#!/usr/bin/env python3
"""Two more Nauvis mall units (2026-11-16): landfill and storage-chest. The ghosts waiting on the other planets (storage chests on Vulcanus, Fulgora and Aquilo,
landfill on Gleba) had no source: the Nauvis network held 0 of both. Same unit as scripts/nauvis_mall.py (requester chest -> assembler -> barred provider chest,
robot-fed), set east of the first block (site checked by dry run). Storage chest needs steel chests: nauvis_mall.py makes those.
Usage: nauvis_mall_extra.py check | build [--apply] | config | status   (build twice is safe: the second dry run reports blocked tiles, nothing doubles)"""
import json
import sys

from _game import tools
import nauvis_mall as M

M.ITEMS = ["landfill", "storage-chest"]
M.X0, M.Y0 = -28, -394


def layout():
    M.ents.clear()
    M.units.clear()
    M.layout()
    M.ents[:] = [e for e in M.ents if not (e["name"] == "substation" and e["x"] > M.X0 + 7)]     # one substation covers two columns


def main():
    step = sys.argv[1]
    apply = "--apply" in sys.argv
    layout()
    print({"units": len(M.units), "entities": len(M.ents)})
    if step == "build":
        r = json.loads(tools["place_entities"](json.dumps(M.ents), surface="nauvis", dry_run=not apply))
        print("placed" if apply else "dry run", r.get("placed"), "failed", json.dumps(r.get("failed") or [])[:400])
    if step == "config" or (step == "build" and apply):
        print(tools["run_lua"](M.CONFIG.replace("UNITS", M.lua_units())))
    elif step == "status":
        print(tools["run_lua"](M.STATUS.replace("UNITS", M.lua_units())).replace(" ; ", "\n"))


if __name__ == "__main__":
    main()
