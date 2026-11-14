#!/usr/bin/env python3
"""Ammunition for the Aquilo shuttle, made on Nauvis and carried (the Captain, 2026-11-14: guns fire uranium rounds, rocket turrets fire
explosive rockets, everything pre-loaded). Ten robot-fed cells north of scripts/rocket_line.py, each: requester chest, inserter, epic
assembling machine 3, inserter, STEEL chest (outside the network, so nothing else takes the product):
  explosive-rocket (1 rocket + 2 explosives, 8 s)                 rows -99 (four cells) and -90 (x0 -322)
  uranium-rounds-magazine (1 piercing magazine + 1 U-238, 10 s)   rows -94 (four cells) and -90 (x0 -308)
Two substations on row -96. The rockets come from the two rocket assemblers of rocket_line.py (their output chests are passive providers again).
Steps: build [--apply] | config | status | ship NAME (moves all finished ammunition into that platform's hub)
Usage: ammo_line.py build [--apply] | config | status | ship NAME"""
import json
import sys

from _game import tools

Q = {"quality": "epic"}
CELLS = [(x, -99, "explosive-rocket") for x in (-322, -315, -308)] + [(-322, -90, "explosive-rocket"), (-322, -86, "explosive-rocket")] + \
        [(x, -94, "uranium-rounds-magazine") for x in (-322, -315, -308, -301)] + [(-308, -90, "uranium-rounds-magazine")]
NEEDS = {"explosive-rocket": (("rocket", 400), ("explosives", 800)), "uranium-rounds-magazine": (("piercing-rounds-magazine", 400), ("uranium-238", 400))}


def ents():
    out = [{"name": "substation", "x": x, "y": -95, "direction": 0, "params": {}} for x in (-315, -303)]
    for x, y, _ in CELLS:
        out.append({"name": "requester-chest", "x": x + .5, "y": y + 1.5, "direction": 0, "params": {}})
        out.append({"name": "bulk-inserter", "x": x + 1.5, "y": y + 1.5, "direction": 12, "params": Q})
        out.append({"name": "assembling-machine-3", "x": x + 3.5, "y": y + 1.5, "direction": 0, "params": Q})
        out.append({"name": "bulk-inserter", "x": x + 5.5, "y": y + 1.5, "direction": 12, "params": Q})
        out.append({"name": "steel-chest", "x": x + 6.5, "y": y + 1.5, "direction": 0, "params": {}})
    return out


def cells_lua():
    return "{" + ",".join("{%d,%d,'%s',{%s}}" % (x, y, r, ",".join("{'%s',%d}" % n for n in NEEDS[r])) for x, y, r in CELLS) + "}"


CONFIG = ("local s=game.surfaces.nauvis local n=0 for _,c in pairs(CELLS) do local m=s.find_entities_filtered{name='assembling-machine-3',position={c[1]+3.5,c[2]+1.5},radius=0.5}[1] m.set_recipe(c[3]) "
          "local q=s.find_entities_filtered{name='requester-chest',position={c[1]+0.5,c[2]+1.5},radius=0.4}[1] local pt=q.get_logistic_point(defines.logistic_member_index.logistic_container) local sec=pt.sections[1] or pt.add_section() "
          "for i,w in pairs(c[4]) do sec.set_slot(i,{value={type='item',name=w[1],quality='normal'},min=w[2]}) end n=n+1 end rcon.print('cells set '..n)")
STATUS = ("local s=game.surfaces.nauvis local st={} for k,v in pairs(defines.entity_status) do st[v]=k end local o={} local tot={} for _,c in pairs(CELLS) do local m=s.find_entities_filtered{name='assembling-machine-3',position={c[1]+3.5,c[2]+1.5},radius=0.5}[1] "
          "local ch=s.find_entities_filtered{name='steel-chest',position={c[1]+6.5,c[2]+1.5},radius=0.4}[1] local k=ch.get_item_count(c[3]) tot[c[3]]=(tot[c[3]] or 0)+k o[#o+1]=c[3]..'@'..c[1]..','..c[2]..' '..(st[m.status] or m.status)..' speed '..m.crafting_speed..' chest '..k end "
          "for k,v in pairs(tot) do o[#o+1]='READY '..k..' '..v end rcon.print(table.concat(o,' ; '))")
SHIP = ("local s=game.surfaces.nauvis local p for _,q in pairs(game.forces.player.platforms) do if q.name:find('NAME',1,true) then p=q end end local hi=p.hub.get_inventory(defines.inventory.hub_main) local got={} "
        "for _,c in pairs(CELLS) do local ch=s.find_entities_filtered{name='steel-chest',position={c[1]+6.5,c[2]+1.5},radius=0.4}[1] local inv=ch.get_inventory(defines.inventory.chest) local n=inv.get_item_count(c[3]) "
        "if n>0 then local put=hi.insert{name=c[3],count=n} if put>0 then inv.remove{name=c[3],count=put} got[c[3]]=(got[c[3]] or 0)+put end end end local o={} for k,v in pairs(got) do o[#o+1]=k..' +'..v..' (hub '..hi.get_item_count(k)..')' end "
        "rcon.print('moved to '..p.name..': '..table.concat(o,', '))")


def main():
    step = sys.argv[1]
    if step == "build":
        apply = "--apply" in sys.argv
        r = json.loads(tools["place_entities"](json.dumps(ents()), surface="nauvis", dry_run=not apply))
        print("placed" if apply else "dry run", r.get("placed"), "failed", json.dumps(r.get("failed") or [])[:600])
    if step == "config" or (step == "build" and "--apply" in sys.argv):
        print(tools["run_lua"](CONFIG.replace("CELLS", cells_lua())))
    elif step == "status":
        print(tools["run_lua"](STATUS.replace("CELLS", cells_lua())).replace(" ; ", "\n"))
    elif step == "ship":
        print(tools["run_lua"](SHIP.replace("CELLS", cells_lua()).replace("NAME", sys.argv[2])))


if __name__ == "__main__":
    main()
