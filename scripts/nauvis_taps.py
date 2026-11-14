#!/usr/bin/env python3
"""Barrel filling stations on Nauvis (the Captain, 2026-11-13: solve the fluid recipes "by putting the fluids in barrels and swapping
them about, because barrels are much easier to clear than pipes"). One station per barrelable fluid, set against a pipe that
carries it: an assembling machine 3 with the fill recipe, its fluid port touching that pipe (a pipe joins on every side; the tanks'
own connections were all taken), a blue
chest asking for 10 empty barrels and a red chest barred to 2 slots (20 barrels, 1,000 units). Empty barrels are an ordinary item the
make-anything machines produce (scripts/omni_maker.py).
Nothing of the Captain's is changed: the station only touches a pipe from a free side. For each fluid the script lists the free
spots, places one, waits, and keeps it only if fluid actually arrives.
Usage: nauvis_taps.py [status]"""
import json
import sys
import time

from _game import tools

FLUIDS = ["petroleum-gas", "light-oil", "heavy-oil", "lubricant", "sulfuric-acid", "water", "crude-oil"]
Q = {"quality": "epic"}
CAND = ("local s=game.surfaces.nauvis local f=game.forces.player local out={} local function free(n,x,y) return s.can_place_entity{name=n,position={x,y},force=f,build_check_type=defines.build_check_type.manual} end "
        "for _,t in pairs(s.find_entities_filtered{type='pipe',force=f}) do if #out>=6 then break end if (t.get_fluid_contents()['FLUID'] or 0)>20 then local px,py=t.position.x,t.position.y "
        "for _,d in pairs{{0,1,0},{1,0,12},{0,-1,8},{-1,0,4}} do local dx,dy=d[1],d[2] local ax,ay=px+2*dx,py+2*dy "
        "if #out<6 and free('assembling-machine-3',ax,ay) and free('fast-inserter',ax+2*dx,ay+2*dy) and free('requester-chest',ax+3*dx,ay+3*dy) then local qx,qy=dy,dx "
        "for _,sg in pairs{1,-1} do if free('fast-inserter',ax+2*sg*qx,ay+2*sg*qy) and free('passive-provider-chest',ax+3*sg*qx,ay+3*sg*qy) then "
        "local idir=(dy==1 and 8) or (dy==-1 and 0) or (dx==1 and 4) or 12 local sx,sy=sg*qx,sg*qy local odir=(sy==1 and 0) or (sy==-1 and 8) or (sx==1 and 12) or 4 "
        "out[#out+1]={ax,ay,d[3],ax+2*dx,ay+2*dy,idir,ax+3*dx,ay+3*dy,ax+2*sx,ay+2*sy,odir,ax+3*sx,ay+3*sy} break end end end end end end rcon.print(helpers.table_to_json(out))")
SETUP = ("local s=game.surfaces.nauvis local a=s.find_entities_filtered{name='assembling-machine-3',position={AX,AY},radius=0.5}[1] a.set_recipe('FLUID-barrel') "
         "local rq=s.find_entities_filtered{name='requester-chest',position={RX,RY},radius=0.4}[1] local lp=rq.get_logistic_point(defines.logistic_member_index.logistic_container) local sec=lp.get_section(1) or lp.add_section() "
         "sec.set_slot(1,{value={type='item',name='barrel',quality='normal'},min=10}) local pv=s.find_entities_filtered{name='passive-provider-chest',position={PX,PY},radius=0.4}[1] pv.get_inventory(defines.inventory.chest).set_bar(3) rcon.print('set')")
CHECK = "local a=game.surfaces.nauvis.find_entities_filtered{name='assembling-machine-3',position={AX,AY},radius=0.5}[1] rcon.print(a.get_fluid_contents()['FLUID'] or 0)"
REMOVE = "local s=game.surfaces.nauvis local n=0 for _,p in pairs({LIST}) do for _,e in pairs(s.find_entities_filtered{position=p,radius=0.4,name={'assembling-machine-3','fast-inserter','requester-chest','passive-provider-chest'}}) do e.destroy() n=n+1 end end rcon.print(n)"
STATUS = ("local s=game.surfaces.nauvis local o={} for _,a in pairs(s.find_entities_filtered{name='assembling-machine-3'}) do local r=a.get_recipe() if r and r.name:find('%-barrel$') and not r.name:find('^empty') then local k='?' for n,v in pairs(defines.entity_status) do if v==a.status then k=n end end "
          "o[#o+1]=r.name..' @'..a.position.x..','..a.position.y..' '..k..' filled '..a.products_finished end end local net=s.find_logistic_network_by_position({-27.5,-393.5},'player') local t={} for _,n in pairs{FL} do t[#t+1]=n..'-barrel '..net.get_item_count(n..'-barrel') end "
          "rcon.print(table.concat(o,' ;; ')..' ;; in the network: '..table.concat(t,', ')..', empty barrels '..net.get_item_count('barrel'))")


def main():
    if "status" in sys.argv:
        return print(tools["run_lua"](STATUS.replace("FL", ",".join("'%s'" % f for f in FLUIDS))).replace(" ;; ", "\n"))
    have = tools["run_lua"](STATUS.replace("FL", ",".join("'%s'" % f for f in FLUIDS)))
    for fluid in FLUIDS:
        if fluid + "-barrel @" in have:
            print(fluid, "station already stands")
            continue
        cands = json.loads(tools["run_lua"](CAND.replace("FLUID", fluid)) or "[]")
        if isinstance(cands, dict):
            cands = []
        done = False
        for c in cands:
            ax, ay, ad, ix, iy, idr, rx, ry, ox, oy, od, px, py = c
            ents = [{"name": "assembling-machine-3", "x": ax, "y": ay, "direction": ad, "params": dict(Q, recipe=fluid + "-barrel")},
                    {"name": "fast-inserter", "x": ix, "y": iy, "direction": idr, "params": Q}, {"name": "requester-chest", "x": rx, "y": ry, "direction": 0, "params": Q},
                    {"name": "fast-inserter", "x": ox, "y": oy, "direction": od, "params": Q}, {"name": "passive-provider-chest", "x": px, "y": py, "direction": 0, "params": Q}]
            r = json.loads(tools["place_entities"](json.dumps(ents), surface="nauvis", dry_run=False))
            if r.get("failed"):
                tools["run_lua"](REMOVE.replace("LIST", ",".join("{%s,%s}" % p for p in [(ax, ay), (ix, iy), (rx, ry), (ox, oy), (px, py)])))
                continue
            sub = lambda code: code.replace("FLUID", fluid).replace("AX", str(ax)).replace("AY", str(ay)).replace("RX", str(rx)).replace("RY", str(ry)).replace("PX", str(px)).replace("PY", str(py))
            tools["run_lua"](sub(SETUP))
            time.sleep(2.5)
            got = float(tools["run_lua"](sub(CHECK)).strip() or 0)
            if got > 0:
                print(fluid, "station at", ax, ay, "fluid arriving", got)
                done = True
                break
            tools["run_lua"](REMOVE.replace("LIST", ",".join("{%s,%s}" % p for p in [(ax, ay), (ix, iy), (rx, ry), (ox, oy), (px, py)])))
        if not done:
            print(fluid, "no free tank connection found (%d spots tried)" % len(cands))


if __name__ == "__main__":
    main()
