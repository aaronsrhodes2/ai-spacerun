#!/usr/bin/env python3
"""Edgerunner FUSION PLANT (plan "Solve Space Age", stage 1, approved by the Captain 2026-11-21).
WHY: the ship runs on 444 solar panels; sunlight is 200% at Gleba, 60% at Aquilo and 1% at the solar system edge, and railguns,
inserters, crushers and collectors all need electricity. Without another source the ship dies past Aquilo.

WHAT: the Aquilo plant of scripts/fusion_plant.py, moved by (+16,-28): its port geometry is the only one tested.
  reactor R (6 x 6) centre (-11,21); generators (3 x 5) centres (-13.5,15.5) and (-8.5,15.5) on R's two north plasma outputs
  cooler K (cryogenic plant, fluoroketone-cooling, facing SOUTH) centre (-18.5,15.5)
  hot row: pipes x -17..-8 at y 12 (generators and K open onto it); cold link: pipes (-17,18), (-17,19), (-16,19), (-15,19) = R's west input
  charge: pipe (-16,20) and an emptier E (assembling machine 3, empty-fluoroketone-cold-barrel, facing SOUTH) on tiles x -17..-15, y 21..23
WHERE: tiles x -21..-7, y 12..25, where 20 solar panels of the west field stand (they are removed: the plant replaces them many times over).
No heat pipes: nothing freezes on a platform. No power poles: the deck carries power.
FEEDING: the hub is boxed in and a platform has no robots, so `load` moves the ship's OWN goods by script: fusion power cells
  hub -> reactor, cold fluoroketone barrels hub -> emptier, empty barrels emptier -> hub. Nothing is created. A belt feed is still owed.
Cells and coolant are made on Aquilo; the hub asks for them there (ghost_carriers.py, row "Edgerunner").
Steps: plan | build [--apply] | load | status
Usage: edge_fusion.py plan ; edge_fusion.py build --apply ; edge_fusion.py load ; edge_fusion.py status"""
import json
import sys

import triangle_miner as TM
from _game import tools

L = tools["run_lua"]
Q = {"quality": "legendary"}
BOX = (-21, 12, -7, 25)          # tiles, inclusive


def one(name, tx, ty, d=0, **kw):
    return {"name": name, "x": tx + 0.5, "y": ty + 0.5, "direction": d, "params": dict(Q), **kw}


def ents():
    e = [{"name": "fusion-reactor", "x": -11, "y": 21, "direction": 0, "params": dict(Q)},
         {"name": "fusion-generator", "x": -13.5, "y": 15.5, "direction": 0, "params": dict(Q)},
         {"name": "fusion-generator", "x": -8.5, "y": 15.5, "direction": 0, "params": dict(Q)},
         {"name": "cryogenic-plant", "x": -18.5, "y": 15.5, "direction": 8, "params": dict(Q), "recipe": "fluoroketone-cooling"}]
    e += [one("pipe", x, 12) for x in range(-17, -7)]
    e += [one("pipe", -17, 18), one("pipe", -17, 19), one("pipe", -16, 19), one("pipe", -15, 19), one("pipe", -16, 20)]
    e.append({"name": "assembling-machine-3", "x": -15.5, "y": 22.5, "direction": 8, "params": dict(Q), "recipe": "empty-fluoroketone-cold-barrel"})
    return e


SURVEY = (TM.AT + "local x0,y0,x1,y1=%d,%d,%d,%d local nodeck=0 for y=y0,y1 do for x=x0,x1 do if s.get_tile(x,y).name~='space-platform-foundation' then nodeck=nodeck+1 end end end local c={} "
          "for _,e in pairs(s.find_entities_filtered{area={{x0,y0},{x1+1,y1+1}}}) do c[e.name]=(c[e.name] or 0)+1 end local t={} for k,v in pairs(c) do t[#t+1]=k..' '..v end rcon.print('tiles without deck '..nodeck..' | standing there: '..table.concat(t,', '))" % BOX)

CLEAR = (TM.AT + "local x0,y0,x1,y1=%d,%d,%d,%d local n,other=0,0 for _,e in pairs(s.find_entities_filtered{area={{x0,y0},{x1+1,y1+1}}}) do if e.name=='solar-panel' then local b=e.bounding_box "
         "if b.left_top.x>=x0-0.1 and b.right_bottom.x<=x1+1.1 and b.left_top.y>=y0-0.1 and b.right_bottom.y<=y1+1.1 then e.destroy() n=n+1 else other=other+1 end else other=other+1 end end rcon.print('solar panels removed '..n..', other things left '..other)" % BOX)

TURN = (TM.AT + "local k=s.find_entities_filtered{name='cryogenic-plant',position={-18.5,15.5},radius=1}[1] local e=s.find_entities_filtered{name='assembling-machine-3',position={-15.5,22.5},radius=1}[1] "
        "if k then k.direction=defines.direction.south end if e then e.direction=defines.direction.south end rcon.print('cooler facing '..tostring(k and k.direction)..', emptier facing '..tostring(e and e.direction))")

STATUS = (TM.AT + "local m={} for k,v in pairs(defines.entity_status) do m[v]=k end local o={} local inv=p.hub.get_inventory(defines.inventory.hub_main) "
          "for _,e in pairs(s.find_entities_filtered{area={{-21,12},{-6,26}}}) do if e.type~='pipe' then local fl={} for i=1,e.fluids_count do local x=e.get_fluid(i) if x then fl[#fl+1]=x.name..' '..math.floor(x.amount) end end "
          "local extra='' if e.name=='fusion-reactor' then extra=' cells '..e.get_item_count('fusion-power-cell') end "
          "o[#o+1]=e.name..'@'..e.position.x..','..e.position.y..' '..tostring(m[e.status])..extra..' ['..table.concat(fl,', ')..']' end end "
          "local pf,pn=0,0 for _,e in pairs(s.find_entities_filtered{type='pipe',area={{-21,12},{-6,26}}}) do pn=pn+1 local x=e.get_fluid(1) if x then pf=pf+x.amount end end "
          "local a,c=0,0 for _,e in pairs(s.find_entities_filtered{type='accumulator'}) do a=a+e.energy c=c+e.electric_buffer_size end "
          "o[#o+1]='pipes '..pn..' holding '..math.floor(pf)..' | hub: fusion cells '..inv.get_item_count('fusion-power-cell')..', cold barrels '..inv.get_item_count('fluoroketone-cold-barrel')..', empty barrels '..inv.get_item_count('barrel')..' | accumulators '..math.floor(100*a/c)..' pct | sun '..s.solar_power_multiplier "
          "rcon.print(table.concat(o,string.char(10)))")

LOAD = (TM.AT + "local inv=p.hub.get_inventory(defines.inventory.hub_main) local r=s.find_entities_filtered{name='fusion-reactor',position={-11,21},radius=2}[1] local e=s.find_entities_filtered{name='assembling-machine-3',position={-15.5,22.5},radius=1}[1] local o={} "
        "if r then local have=r.get_item_count('fusion-power-cell') local want=math.min(50-have,inv.get_item_count('fusion-power-cell')) if want>0 then local n=r.insert{name='fusion-power-cell',count=want} if n>0 then inv.remove{name='fusion-power-cell',count=n} end o[#o+1]='cells hub -> reactor '..n end o[#o+1]='reactor holds '..r.get_item_count('fusion-power-cell') end "
        "if e then local out=e.get_output_inventory() local b=out.get_item_count('barrel') if b>0 then local n=inv.insert{name='barrel',count=b} if n>0 then out.remove{name='barrel',count=n} end o[#o+1]='empty barrels back to the hub '..n end "
        "local ein=e.get_inventory(defines.inventory.crafter_input) local have=ein.get_item_count('fluoroketone-cold-barrel') local want=math.min(%d-have,inv.get_item_count('fluoroketone-cold-barrel')) if want>0 then local n=ein.insert{name='fluoroketone-cold-barrel',count=want} if n>0 then inv.remove{name='fluoroketone-cold-barrel',count=n} end o[#o+1]='cold barrels hub -> emptier '..n end end rcon.print(table.concat(o,'; '))")


def main():
    a = sys.argv[1:]
    step = a[0] if a else "plan"
    apply = "--apply" in a
    if step in ("plan", "build"):
        print(L(SURVEY).strip())
        go = apply and step == "build"
        if go:
            print(tools["save_game"]("pre-edge-fusion"))
            print(L(CLEAR).strip())
        r = tools["place_entities"](json.dumps(ents()), surface=L(TM.AT + "rcon.print(s.name)").strip(), dry_run=not go)
        print(str(r)[:600])
        if go:
            print(L(TURN).strip())
    elif step == "load":
        n = int(a[1]) if len(a) > 1 else 10
        print(L(LOAD % n).strip())
    elif step == "status":
        print(L(STATUS))
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
