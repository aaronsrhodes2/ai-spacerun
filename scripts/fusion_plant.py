#!/usr/bin/env python3
"""Aquilo fusion plant 1 (the Captain, 2026-11-16: "now build the fusion plant on the west side"), west end of the prepared south area, beside the
spaceport block. Placed entities are free once researched, so the reactor and generators need no quantum processors; what the plant CONSUMES
(fusion power cells, fluoroketone) must be made by the factory.

Geometry (read from the prototypes, absolute tile centres; nothing here can stand on ice, the footprint x -38..-20, y 38..53 is paved with concrete first):
  reactor R (6 x 6) centre (-27,49)          cold fluoroketone in on its west/east faces, plasma out on its north/south faces
  generators G1, G2 (3 x 5) centres (-29.5,43.5), (-24.5,43.5), facing north: their plasma inputs sit on R's two north plasma outputs,
            their hot fluoroketone outputs open north onto the pipe row y = 40
  cooling plant K (cryogenic plant, fluoroketone-cooling) centre (-34.5,43.5), facing SOUTH: hot in at its north-east corner (pipe at (-33,40)),
            cold out at its south-east corner (pipe (-33,46)) -> (-33,47), (-32,47), (-31,47) = R's west cold input. A closed loop of 14 pipes.
  heat      what freezes: K (100 kW), pipes (1 kW each), the fuel inserter. K touches the existing hot heat column x = -38; a heat row y = 39 runs over the
            hot pipes, (-34,46..48) + row y = 48 beside the cold pipes, row y = 52 + (-24,51) for the fuel inserter. R and the generators need no heat.
  fuel      requester chest (-23,50) asks for fusion power cells, fast inserter (-24,50) feeds R
  power     substation (-21,47)
The loop starts EMPTY: it has to be charged with fluoroketone once (see `status`), and the cells need holmium plate, which Aquilo does not have yet.
Usage: fusion_plant.py dry | build | status"""
import json
import sys

from _game import tools

L = tools["run_lua"]
Q = {"quality": "legendary"}
CELLS = 50


def one(name, tx, ty, d=0, **kw):
    return {"name": name, "x": tx + 0.5, "y": ty + 0.5, "direction": d, "params": dict(Q), **kw}


def layout():
    e = [{"name": "fusion-reactor", "x": -27, "y": 49, "direction": 0, "params": dict(Q)},
         {"name": "fusion-generator", "x": -29.5, "y": 43.5, "direction": 0, "params": dict(Q)},
         {"name": "fusion-generator", "x": -24.5, "y": 43.5, "direction": 0, "params": dict(Q)},
         {"name": "cryogenic-plant", "x": -34.5, "y": 43.5, "direction": 8, "params": dict(Q), "recipe": "fluoroketone-cooling"},
         {"name": "substation", "x": -21, "y": 47, "direction": 0, "params": dict(Q)}]
    e += [one("pipe", x, 40) for x in range(-33, -23)]                                   # hot row
    e += [one("pipe", -33, 46), one("pipe", -33, 47), one("pipe", -32, 47), one("pipe", -31, 47)]   # cold link
    heat = [(x, 39) for x in range(-37, -23)] + [(-34, 46), (-34, 47)] + [(x, 48) for x in range(-37, -30)] + [(x, 52) for x in range(-37, -23)] + [(-24, 51)]
    e += [one("heat-pipe", x, y) for x, y in heat]
    e += [one("requester-chest", -23, 50), one("fast-inserter", -24, 50, 4)]             # direction = the side it picks from (east: the chest)
    return e


CONFIG = ("local s=game.surfaces.aquilo local f=game.forces.player local o={} local k=s.find_entities_filtered{name='cryogenic-plant',position={-34.5,43.5},radius=1}[1] "
          "if k then k.direction=8 if not k.get_recipe() or k.get_recipe().name~='fluoroketone-cooling' then k.set_recipe('fluoroketone-cooling') end o[#o+1]='K facing '..k.direction..' recipe '..k.get_recipe().name end "
          "local c=s.find_entities_filtered{name='requester-chest',position={-22.5,50.5},radius=0.4}[1] if c then local pt=c.get_logistic_point(defines.logistic_member_index.logistic_container) for i=#pt.sections,1,-1 do pt.remove_section(i) end "
          "pt.add_section().set_slot(1,{value={type='item',name='fusion-power-cell',quality='normal'},min=CELLSN}) o[#o+1]='chest asks for CELLSN fusion power cells' end f.chart(s,{{-45,32},{-15,58}}) rcon.print(table.concat(o,' | '))")

STATUS = ("local s=game.surfaces.aquilo local f=game.forces.player local m={} for k,v in pairs(defines.entity_status) do m[v]=k end local o={} "
          "for _,e in pairs(s.find_entities_filtered{area={{-38,38},{-19,54}},force=f}) do if e.type~='heat-pipe' and e.type~='pipe' and e.type~='tile-ghost' and e.type~='logistic-robot' and e.type~='construction-robot' and e.type~='wall' then "
          "local fl={} for i=1,8 do local ok,x=pcall(function() return e.get_fluid(i) end) if ok and x then fl[#fl+1]=x.name..' '..math.floor(x.amount) end end "
          "o[#o+1]=e.name..' @'..e.position.x..','..e.position.y..' '..tostring(m[e.status] or '-')..(#fl>0 and (' ['..table.concat(fl,', ')..']') or '') end end "
          "local pf,pz=0,0 for _,p in pairs(s.find_entities_filtered{type='pipe',area={{-34,40},{-23,48}},force=f}) do if p.status==defines.entity_status.frozen then pz=pz+1 end if next(p.get_fluid_contents()) then pf=pf+1 end end "
          "local r=s.find_entities_filtered{name='fusion-reactor',area={{-38,38},{-19,54}}}[1] local cells=r and r.get_item_count('fusion-power-cell') or -1 "
          "o[#o+1]='loop pipes holding fluid '..pf..', frozen '..pz..' | cells in the reactor '..cells rcon.print(table.concat(o,string.char(10)))")


def main():
    step = sys.argv[1] if len(sys.argv) > 1 else "status"
    if step in ("dry", "build"):
        apply = step == "build"
        if apply:
            print("save:", tools["save_game"]("pre-fusion-build"))
        r = json.loads(tools["place_entities"](json.dumps(layout()), surface="aquilo", dry_run=not apply))
        print("placed" if apply else "dry run:", r.get("placed"), "of", len(layout()), "failed", json.dumps(r.get("failed") or [])[:900])
        if apply:
            print(L(CONFIG.replace("CELLSN", str(CELLS))))
    elif step == "status":
        print(L(STATUS))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
