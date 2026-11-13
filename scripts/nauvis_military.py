#!/usr/bin/env python3
"""Nauvis military science, robot-fed (2026-11-13). The belt plant at (99..127,-122) makes none: its grenade assemblers get no iron (the
iron lane of belt y -125.5 is empty, copper fills the other lane). Rocket turrets (for the Aquilo ships) need military packs, so this is a
separate cell: eleven free 9x3 slots found from x X eastward inside the robot network and near a pole (the substation lattice leaves no big
rectangle free), each slot blue chest, inserter, assembler, inserter, red chest.
Rows: firearm magazines, piercing rounds x2, grenades x3, walls, military science x4.
Usage: nauvis_military.py [--x -360] [--apply]"""
import json
import sys

from _game import tools

X = float(sys.argv[sys.argv.index("--x") + 1]) if "--x" in sys.argv else -360
ROWS = [("firearm-magazine", {"iron-plate": 200}),
        ("piercing-rounds-magazine", {"firearm-magazine": 40, "steel-plate": 40, "copper-plate": 200}),
        ("piercing-rounds-magazine", {"firearm-magazine": 40, "steel-plate": 40, "copper-plate": 200}),
        ("grenade", {"iron-plate": 100, "coal": 200}), ("grenade", {"iron-plate": 100, "coal": 200}), ("grenade", {"iron-plate": 100, "coal": 200}),
        ("stone-wall", {"stone-brick": 200}),
        ("military-science-pack", {"piercing-rounds-magazine": 40, "grenade": 40, "stone-wall": 80}),
        ("military-science-pack", {"piercing-rounds-magazine": 40, "grenade": 40, "stone-wall": 80}),
        ("military-science-pack", {"piercing-rounds-magazine": 40, "grenade": 40, "stone-wall": 80}),
        ("military-science-pack", {"piercing-rounds-magazine": 40, "grenade": 40, "stone-wall": 80})]
REQ = ("local s=game.surfaces.nauvis local n=0 for _,q in pairs(SPEC) do local c=s.find_entities_filtered{name='requester-chest',position={q[1],q[2]},radius=0.3}[1] if c then "
       "local ss=c.get_logistic_sections() local se=ss.sections[1] or ss.add_section() local i=0 for name,ct in pairs(q[3]) do i=i+1 se.set_slot(i,{value={name=name,quality='normal'},min=ct}) end n=n+1 end end "
       "rcon.print('requests set on '..n..' chests')")
SLOTS = ("local s=game.surfaces.nauvis local f=game.forces.player local o={} local used={} for x=X0,X1,10 do for y=-140,-40,3 do if #o<NEED then local a={{x,y},{x+9,y+3}} "
         "if s.count_entities_filtered{area=a}==0 and s.count_tiles_filtered{area=a,collision_mask='water_tile'}==0 and s.find_logistic_network_by_position({x+4.5,y+1.5},f) "
         "and #s.find_entities_filtered{type='electric-pole',position={x+4.5,y+1.5},radius=9}>0 then o[#o+1]=x..' '..y end end end end rcon.print(table.concat(o,';'))")
x0 = int(X)
slots = [tuple(map(int, q.split())) for q in tools["run_lua"](SLOTS.replace("X0", str(x0)).replace("X1", str(x0 + 40)).replace("NEED", str(len(ROWS)))).split(";") if q.strip()]
print("free slots found", len(slots), slots[:12])
e, reqs = [], []
for (sx, sy), (rec, req) in zip(slots, ROWS):
    y = sy + 1.5
    e += [{"name": "requester-chest", "x": sx + 0.5, "y": y}, {"name": "bulk-inserter", "x": sx + 1.5, "y": y, "direction": 12},
          {"name": "assembling-machine-3", "x": sx + 3.5, "y": y, "recipe": rec}, {"name": "bulk-inserter", "x": sx + 5.5, "y": y, "direction": 12},
          {"name": "passive-provider-chest", "x": sx + 6.5, "y": y}]
    reqs.append((sx + 0.5, y, req))
apply = "--apply" in sys.argv
print(tools["place_entities"](json.dumps(e), surface="nauvis", dry_run=not apply)[:700])
if apply:
    spec = "{" + ",".join("{%s,%s,{%s}}" % (x, y, ",".join("['%s']=%d" % kv for kv in r.items())) for x, y, r in reqs) + "}"
    print(tools["run_lua"](REQ.replace("SPEC", spec)))
