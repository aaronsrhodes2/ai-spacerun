#!/usr/bin/env python3
"""Productivity modules from the Nauvis circuit mountain, into the wheels (the Captain, 2026-11-13: "turn overages into useful
materials"). Nauvis held 448,000 advanced circuits, 240,000 electronic circuits and 90,000 processing units with nothing asking for
them, and the Nauvis Wheel had 349 empty module slots. A productivity module 2 gives 6% more product (epic: more) from the same
input; every crushing recipe accepts it.
  mall     six robot-fed units at X0,Y0 (the pattern of scripts/nauvis_mall.py): four make productivity module 1, two make
           productivity module 2 (the best researched). Red chests barred: module 1 to 2 slots, module 2 to 10 slots.
  install  takes finished modules out of the Nauvis network and puts them into the wheels' machines at the best researched quality
           (the standing order: everything at researched quality, as scripts/upgrade_quality.py --items does). Factory-made modules
           are moved, none is created. Order: crushers on a crushing recipe first (all raw materials), then foundries, then the space
           science assemblers. Reprocessing does not accept productivity and is skipped. Safe to run again: it fills what is empty.
Steps: build [--apply] | config | install [--apply] | status
Usage: module_mall.py build --apply ; module_mall.py install --apply"""
import json
import sys

from _game import tools

X0, Y0 = 34, -386
Q = {"quality": "epic"}
UNITS = ["productivity-module"] * 4 + ["productivity-module-2"] * 2
MODULE = "productivity-module-2"


def layout():
    ents = []

    def e(name, tx, ty, w=1, h=1):
        ents.append({"name": name, "x": tx + w / 2, "y": ty + h / 2, "direction": 0, "params": dict(Q)})

    for i in range(len(UNITS)):
        ux = X0 + 3 * i
        e("requester-chest", ux + 1, Y0)
        e("fast-inserter", ux + 1, Y0 + 1)
        e("assembling-machine-3", ux, Y0 + 2, 3, 3)
        e("fast-inserter", ux + 1, Y0 + 5)
        e("passive-provider-chest", ux + 1, Y0 + 6)
    e("substation", X0 + 3 * len(UNITS), Y0 + 2, 2, 2)
    return ents


CONFIG = ("local s=game.surfaces.nauvis local f=game.forces.player local n=0 for i,rec in pairs(UNITS) do local ux=X0+3*(i-1) local m=s.find_entities_filtered{name='assembling-machine-3',position={ux+1.5,Y0+3.5},radius=0.6}[1] "
          "local rq=s.find_entities_filtered{name='requester-chest',position={ux+1.5,Y0+0.5},radius=0.3}[1] local pv=s.find_entities_filtered{name='passive-provider-chest',position={ux+1.5,Y0+6.5},radius=0.3}[1] "
          "m.set_recipe(rec) local lp=rq.get_logistic_point(defines.logistic_member_index.logistic_container) local sec=lp.get_section(1) or lp.add_section() for k,ing in pairs(f.recipes[rec].ingredients) do sec.set_slot(k,{value={type='item',name=ing.name,quality='normal'},min=ing.amount*6}) end "
          "pv.get_inventory(defines.inventory.chest).set_bar((rec=='MODULE') and 11 or 3) n=n+1 end rcon.print('units set '..n)")
INSTALL = ("local f=game.forces.player local best=nil for n,q in pairs(prototypes.quality) do if n~='quality-unknown' and f.is_quality_unlocked(n) and (best==nil or q.level>best.level) then best=q end end "
           "local net=game.surfaces.nauvis.find_logistic_network_by_position({-27.5,-393.5},'player') local have=net.get_item_count('MODULE') local put,want=0,0 local o={} "
           "local function fill(e) local r=e.get_recipe() if not r or not r.prototype.allowed_effects.productivity then return end local mi=e.get_module_inventory() if not mi then return end "
           "for i=1,#mi do if not mi[i].valid_for_read then want=want+1 if APPLY and put<have and net.remove_item{name='MODULE',count=1}==1 then mi[i].set_stack{name='MODULE',count=1,quality=best.name} put=put+1 end end end end "
           "for pass=1,3 do for _,p in pairs(f.platforms) do if p.name:find('Wheel$') then local s=p.surface "
           "if pass==1 then for _,e in pairs(s.find_entities_filtered{name='crusher'}) do fill(e) end elseif pass==2 then for _,e in pairs(s.find_entities_filtered{name='foundry'}) do fill(e) end "
           "else for _,e in pairs(s.find_entities_filtered{name='assembling-machine-3'}) do local r=e.get_recipe() if r and r.name=='space-science-pack' then fill(e) end end end end end end "
           "rcon.print('empty slots that take productivity '..want..', modules in the Nauvis network '..have..', installed '..put..' at '..best.name..' quality')")
STATUS = ("local s=game.surfaces.nauvis local f=game.forces.player local o={} for i,rec in pairs(UNITS) do local ux=X0+3*(i-1) local m=s.find_entities_filtered{name='assembling-machine-3',position={ux+1.5,Y0+3.5},radius=0.6}[1] "
          "local k='?' for a,v in pairs(defines.entity_status) do if v==m.status then k=a end end o[#o+1]=rec..' '..k..' made '..m.products_finished end local net=s.find_logistic_network_by_position({-27.5,-393.5},'player') "
          "local t={} for _,p in pairs(f.platforms) do if p.name:find('Wheel$') then local slots,used=0,0 for _,e in pairs(p.surface.find_entities_filtered{type={'assembling-machine','furnace'}}) do local mi=e.get_module_inventory() if mi then slots=slots+#mi used=used+(#mi-mi.count_empty_stacks()) end end "
          "local es=p.surface.find_entities_filtered{name='accumulator',limit=1}[1] t[#t+1]=p.name:gsub('^%[.-%]%s*','')..' modules '..used..'/'..slots..(es and (' accumulators '..string.format('%.0f%%',100*es.energy/es.electric_buffer_size)) or '') end end "
          "rcon.print(table.concat(o,' ; ')..' ;; in the network: module 1 '..net.get_item_count('productivity-module')..', module 2 '..net.get_item_count('MODULE')..' ;; '..table.concat(t,' ; '))")


def sub(code, apply=False):
    return (code.replace("UNITS", "{" + ",".join("'%s'" % u for u in UNITS) + "}").replace("X0", str(X0)).replace("Y0", str(Y0)).replace("MODULE", MODULE)
            .replace("APPLY", "true" if apply else "false"))


def main():
    step = sys.argv[1]
    apply = "--apply" in sys.argv
    if step == "build":
        r = json.loads(tools["place_entities"](json.dumps(layout()), surface="nauvis", dry_run=not apply))
        print("placed" if apply else "dry run", r.get("placed"), "failed", json.dumps(r.get("failed") or [])[:300])
    if step == "config" or (step == "build" and apply):
        print(tools["run_lua"](sub(CONFIG)))
    elif step == "install":
        print(tools["run_lua"](sub(INSTALL, apply)))
    elif step == "status":
        print(tools["run_lua"](sub(STATUS)).replace(" ;; ", "\n").replace(" ; ", "\n  "))


if __name__ == "__main__":
    main()
