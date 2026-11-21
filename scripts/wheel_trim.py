#!/usr/bin/env python3
"""One-off trim of a Wheel hub that the surplus valve cannot keep up with (2026-11-20, ranker: Nauvis and Fulgora Wheel hubs 0 of 10,009 slots free).
The valve (wheel_valve.py) is one bulk inserter, about 10 items/s in total, and calcite alone stood at 177k and 194k, so a full hub blocked intake for days.
This does by hand what the valve does: removes the raw surplus above CAP (the valve's own cap, 36,000) from the listed raw items, overboard.
Never touches packs, chunks, plates or anything not listed. Usage: wheel_trim.py [--apply] [--only 'Nauvis Wheel']   (default dry run, all wheels)"""
import sys

from _game import tools

RAW = ["calcite", "iron-ore", "copper-ore", "ice", "sulfur", "carbon", "stone", "coal", "tungsten-ore"]
CAP = 36000
apply = "--apply" in sys.argv
only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
LUA = """local apply=APPLY for _,p in pairs(game.forces.player.platforms) do local nm=p.name:gsub('%[.-%]%s*','') if nm:find('Wheel') and (ONLY==nil or nm==ONLY) then local i=p.hub.get_inventory(defines.inventory.hub_main) local before=i.count_empty_stacks() local o={}
 for _,k in pairs(RAW) do local n=i.get_item_count(k) if n>CAP then local cut=n-CAP if apply then cut=i.remove{name=k,count=cut} end o[#o+1]=k..' -'..cut end end
 rcon.print(nm..' free slots '..before..' -> '..i.count_empty_stacks()..(apply and '' or ' (dry run, not changed)')..' ; '..table.concat(o,', ')) end end"""
code = (LUA.replace("APPLY", "true" if apply else "false").replace("ONLY", "'%s'" % only if only else "nil")
        .replace("RAW", "{" + ",".join("'%s'" % r for r in RAW) + "}").replace("CAP", str(CAP)))
print(tools["run_lua"](code).strip())
