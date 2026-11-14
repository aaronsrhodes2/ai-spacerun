#!/usr/bin/env python3
"""Rockets for the Aquilo shuttle, made on Nauvis (the Captain, 2026-11-14: make them on the ground, carry thousands).
What stood there (another session, y=-68.5): explosives plant (-290.5), rocket assembler (-298.5), explosive-rocket assembler (-306.5), each
robot-fed (requester chest west, provider chest east). The two assemblers run at speed 4.1 (about a rocket a second each): the one explosives
plant (0.45 a second) was the limit, and the explosive-rocket assembler ate the rockets (an explosive rocket does less to one asteroid).
This adds four epic explosives plants north of the water main on row -80 (tiles x0..x0+2, rows -83..-81, facing south, both inputs on the
main), each with a requester chest (coal, sulfur) and a provider chest on row -85, and turns the explosive-rocket assembler into a second
rocket assembler. Rockets collect in the provider chests at (-295.5,-68.5) and (-303.5,-68.5).
Steps: build [--apply] | config | status | ship NAME COUNT (moves rockets from the two chests into that platform's hub)
Usage: rocket_line.py build [--apply] | config | status | ship NAME COUNT"""
import json
import sys

from _game import tools

Q = {"quality": "epic"}
X0 = (-315, -311, -307, -303)


def ents():
    out = []
    for x in X0:
        out.append({"name": "chemical-plant", "x": x + 1.5, "y": -81.5, "direction": 8, "params": dict(Q, recipe="explosives")})
        out.append({"name": "bulk-inserter", "x": x + .5, "y": -83.5, "direction": 0, "params": Q})
        out.append({"name": "bulk-inserter", "x": x + 2.5, "y": -83.5, "direction": 8, "params": Q})
        out.append({"name": "requester-chest", "x": x + .5, "y": -84.5, "direction": 0, "params": {}})
        out.append({"name": "passive-provider-chest", "x": x + 2.5, "y": -84.5, "direction": 0, "params": {}})
    return out


CONFIG = ("local s=game.surfaces.nauvis local n=0 for _,x in pairs({XS}) do local m=s.find_entities_filtered{name='chemical-plant',position={x+1.5,-81.5},radius=0.5}[1] if m then m.set_recipe('explosives') "
          "local c=s.find_entities_filtered{name='requester-chest',position={x+0.5,-84.5},radius=0.4}[1] local pt=c.get_logistic_point(defines.logistic_member_index.logistic_container) local sec=pt.sections[1] or pt.add_section() "
          "sec.set_slot(1,{value={type='item',name='coal',quality='normal'},min=400}) sec.set_slot(2,{value={type='item',name='sulfur',quality='normal'},min=400}) n=n+1 end end "
          "local a=s.find_entities_filtered{name='assembling-machine-3',position={-306.5,-68.5},radius=0.5}[1] local rc=a.get_recipe() if rc and rc.name~='rocket' then local left=a.set_recipe('rocket') "
          "local ch=s.find_entities_filtered{name='passive-provider-chest',position={-303.5,-68.5},radius=0.4}[1] for _,it in pairs(left or {}) do ch.insert(it) end end "
          "local c=s.find_entities_filtered{name='requester-chest',position={-309.5,-68.5},radius=0.4}[1] local pt=c.get_logistic_point(defines.logistic_member_index.logistic_container) local sec=pt.sections[1] for i=#pt.sections,2,-1 do pt.remove_section(i) end "
          "sec.clear_slot(1) sec.clear_slot(2) sec.set_slot(1,{value={type='item',name='iron-plate',quality='normal'},min=2000}) sec.set_slot(2,{value={type='item',name='explosives',quality='normal'},min=1000}) "
          "local inv=c.get_inventory(defines.inventory.chest) local r=inv.get_item_count('rocket') if r>0 then local ch=s.find_entities_filtered{name='passive-provider-chest',position={-303.5,-68.5},radius=0.4}[1] inv.remove{name='rocket',count=ch.insert{name='rocket',count=r}} end "
          "rcon.print('explosives plants set '..n..', second rocket assembler: '..a.get_recipe().name)")
STATUS = ("local s=game.surfaces.nauvis local st={} for k,v in pairs(defines.entity_status) do st[v]=k end local o={} "
          "for _,m in pairs(s.find_entities_filtered{type='assembling-machine',area={{-316,-84},{-286,-67}}}) do local rc=m.get_recipe() if rc and (rc.name=='explosives' or rc.name=='rocket' or rc.name=='explosive-rocket') then o[#o+1]=rc.name..'@'..m.position.x..','..m.position.y..' '..(st[m.status] or m.status)..' made '..m.products_finished end end "
          "local r=0 for _,p in pairs({{-295.5,-68.5},{-303.5,-68.5}}) do local c=s.find_entities_filtered{name='passive-provider-chest',position=p,radius=0.4}[1] r=r+c.get_item_count('rocket') end "
          "local net=s.find_entities_filtered{name='roboport',position={-310,-77},radius=1}[1].logistic_network rcon.print(table.concat(o,' ; ')..' ; rockets in the two chests '..r..' ; network: rocket '..net.get_item_count('rocket')..' explosives '..net.get_item_count('explosives')..' coal '..net.get_item_count('coal')..' sulfur '..net.get_item_count('sulfur')..' iron plate '..net.get_item_count('iron-plate'))")
SHIP = ("local s=game.surfaces.nauvis local p for _,q in pairs(game.forces.player.platforms) do if q.name:find('NAME',1,true) then p=q end end local hi=p.hub.get_inventory(defines.inventory.hub_main) local want,got=COUNT,0 "
        "for _,pos in pairs({{-295.5,-68.5},{-303.5,-68.5}}) do local c=s.find_entities_filtered{name='passive-provider-chest',position=pos,radius=0.4}[1] local inv=c.get_inventory(defines.inventory.chest) local have=inv.get_item_count('rocket') local n=math.min(have,want-got) "
        "if n>0 then local put=hi.insert{name='rocket',count=n} if put>0 then inv.remove{name='rocket',count=put} got=got+put end end end rcon.print('rockets moved from the Nauvis line to '..p.name..': '..got..', hub now '..hi.get_item_count('rocket'))")


def main():
    step = sys.argv[1]
    if step == "build":
        apply = "--apply" in sys.argv
        r = json.loads(tools["place_entities"](json.dumps(ents()), surface="nauvis", dry_run=not apply))
        print("placed" if apply else "dry run", r.get("placed"), "failed", json.dumps(r.get("failed") or [])[:600])
        if apply:
            print(tools["run_lua"](CONFIG.replace("XS", ",".join(str(x) for x in X0))))
    elif step == "config":
        print(tools["run_lua"](CONFIG.replace("XS", ",".join(str(x) for x in X0))))
    elif step == "status":
        print(tools["run_lua"](STATUS).replace(" ; ", "\n"))
    elif step == "ship":
        print(tools["run_lua"](SHIP.replace("NAME", sys.argv[2]).replace("COUNT", sys.argv[3])))


if __name__ == "__main__":
    main()
