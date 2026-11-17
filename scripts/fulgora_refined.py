#!/usr/bin/env python3
"""Fulgora refined-concrete line (2026-11-17): a useful good from the concrete surplus (384k in the hoard), for Aquilo's floor (7,848 tile ghosts).

Robot-fed block south-east of the base, origin tile (214,6), inside a wall ring on striped concrete (tile ghosts, never spawned):
  ice requester -> melter (chemical plant, outputs north) -> pipe row y 5 -> both assemblers' north fluid port
  assembler A (217..219) <- iron-stick maker (221..223) -> assembler B (225..227); sticks handed over by one inserter each side
  concrete + steel requesters and refined-concrete provider chests on the south side (y 10)
Gate: the concrete and ice inserters run only while the network holds under CAP refined concrete (2x Aquilo's need), so the line stops by itself.
Nothing is spawned: every input is carried by robots from Fulgora's own stock.

Usage: fulgora_refined.py plan | build | config | status
"""
import json
import sys

from _game import tools

OX, OY = 214, 6
CAP = 16000
Q = {"quality": "legendary"}
L = tools["run_lua"]


def ent(name, x, y, d=0, recipe=None):
    e = {"name": name, "x": OX + x + 0.5, "y": OY + y + 0.5, "direction": d, "params": dict(Q)}
    if recipe:
        e["recipe"] = recipe
    return e


def plan():
    E = [ent("chemical-plant", 1, 1, 8, "ice-melting"), ent("assembling-machine-3", 4, 1, 0, "refined-concrete"),
         ent("assembling-machine-3", 8, 1, 0, "iron-stick"), ent("assembling-machine-3", 12, 1, 0, "refined-concrete")]
    E += [ent("pipe", x, -1) for x in range(0, 13)]
    E += [ent("bulk-inserter", 6, 1, 4), ent("bulk-inserter", 10, 1, 12)]                     # sticks: east -> A, west -> B
    for x in (1, 3, 8, 11):                                                                   # inputs: chest south, inserter picks from the south
        E += [ent("bulk-inserter", x, 3, 8), ent("requester-chest", x, 4)]
    for x in (5, 12):                                                                         # outputs: inserter picks from the north
        E += [ent("bulk-inserter", x, 3, 0), ent("passive-provider-chest", x, 4)]
    ring = [(x, y) for x in range(-2, 15) for y in (-3, 6)] + [(x, y) for x in (-2, 14) for y in range(-2, 6)]
    E += [ent("stone-wall", x, y) for x, y in ring]
    return E


CONFIG = """local s=game.surfaces.fulgora local f=game.forces.player local n=0
local function at(t,x,y) return s.find_entities_filtered{type=t,position={%d+x+0.5,%d+y+0.5},radius=0.3,force=f}[1] end
local function req(x,items) local c=at('logistic-container',x,4) local ss=c.get_logistic_sections() local se=ss.sections[1] or ss.add_section()
  local i=0 for name,cnt in pairs(items) do i=i+1 se.set_slot(i,{value={name=name,quality='normal'},min=cnt}) end n=n+1 end
req(1,{ice=200}) req(3,{concrete=400,['steel-plate']=40}) req(8,{['iron-plate']=200}) req(11,{concrete=400,['steel-plate']=40})
local function gate(x) local i=at('inserter',x,3) local cb=i.get_or_create_control_behavior() cb.connect_to_logistic_network=true
  cb.logistic_condition={first_signal={type='item',name='refined-concrete'},comparator='<',constant=%d} n=n+1 end
gate(1) gate(3) gate(11)
local function filt(x,y,item) local i=at('inserter',x,y) i.use_filters=true i.inserter_filter_mode='whitelist' i.set_filter(1,item) n=n+1 end
filt(6,1,'iron-stick') filt(10,1,'iron-stick') filt(5,3,'refined-concrete') filt(12,3,'refined-concrete')
local t=0 for x=-1,13 do for y=-2,5 do local p={%d+x+0.5,%d+y+0.5}
  if s.get_tile(p[1],p[2]).name~='refined-hazard-concrete-left' and s.count_entities_filtered{type='tile-ghost',position=p,radius=0.3}==0 then
    s.create_entity{name='tile-ghost',inner_name='refined-hazard-concrete-left',position=p,force=f} t=t+1 end end end
f.chart(s,{{%d-8,%d-8},{%d+24,%d+16}})
rcon.print('configured '..n..', tile ghosts '..t)""" % (OX, OY, CAP, OX, OY, OX, OY, OX, OY)

STATUS = """local s=game.surfaces.fulgora local f=game.forces.player local E=defines.entity_status local SN={} for k,v in pairs(E) do SN[v]=k end local o={}
for _,e in pairs(s.find_entities_filtered{area={{%d-1,%d-2},{%d+14,%d+6}},force=f,type={'assembling-machine','furnace'}}) do local r=e.get_recipe()
  o[#o+1]=string.format('%%s %%d,%%d %%s speed %%.2f done %%d',r and r.name or '?',e.position.x,e.position.y,SN[e.status] or '?',e.crafting_speed,e.products_finished) end
local net=s.find_logistic_network_by_position({%d+5,%d+4},f)
o[#o+1]='network refined-concrete '..net.get_item_count('refined-concrete')..' (cap %d), concrete '..net.get_item_count('concrete')..', steel '..net.get_item_count('steel-plate')..', ice '..net.get_item_count('ice')
local ps=f.get_item_production_statistics(s) o[#o+1]=string.format('refined-concrete made %%.0f/min (1 min), %%.0f/min (10 min)',
  ps.get_flow_count{name='refined-concrete',category='input',precision_index=defines.flow_precision_index.one_minute},
  ps.get_flow_count{name='refined-concrete',category='input',precision_index=defines.flow_precision_index.ten_minutes})
o[#o+1]='tile ghosts left '..s.count_entities_filtered{type='tile-ghost',area={{%d-2,%d-3},{%d+15,%d+7}}}
rcon.print(table.concat(o,string.char(10)))""" % (OX, OY, OX, OY, OX, OY, CAP, OX, OY, OX, OY)


def one(code):
    return L(" ".join(code.split("\n")))


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "plan"
    if step in ("plan", "build"):
        E = plan()
        print(tools["place_entities"](json.dumps(E), surface="fulgora", dry_run=(step == "plan"))[:1500])
        if step == "build":
            print(one(CONFIG))
    elif step == "config":
        print(one(CONFIG))
    elif step == "status":
        print(one(STATUS))
