#!/usr/bin/env python3
"""Productivity modules from the Nauvis circuit mountain, into the wheels (the Captain, 2026-11-13: "turn overages into useful
materials"). Nauvis held 448,000 advanced circuits, 240,000 electronic circuits and 90,000 processing units with nothing asking for
them, and the Nauvis Wheel had 349 empty module slots. A productivity module 2 gives 6% more product (epic: more) from the same
input; every crushing recipe accepts it.
  mall     six robot-fed units at X0,Y0 (the pattern of scripts/nauvis_mall.py): four make productivity module 1, two make
           productivity module 2 (the best researched). Red chests barred: module 1 to 2 slots, module 2 to 10 slots.
  install  takes finished modules out of the Nauvis network and puts them into the wheels' machines at the best researched quality
           (the standing order: everything at researched quality, as scripts/upgrade_quality.py --items does). Factory-made modules
           are moved, none is created. Order: the agricultural science biochambers first (research is the end product), , then crushers on a crushing recipe (all raw materials), then foundries, then the space
           science assemblers. Reprocessing does not accept productivity and is skipped. Safe to run again: it fills what is empty.
Steps: build [--apply] | speed [--apply] | more [--apply] | config | install [--apply] | labs | status
Usage: module_mall.py build --apply ; module_mall.py install --apply"""
import json
import sys

from _game import tools

X0, Y0 = 34, -386
Q = {"quality": "epic"}
UNITS = ["productivity-module"] * 4 + ["productivity-module-2"] * 2
MODULE = "productivity-module-2"
# Second block (step `speed`): speed module 3 for the Gleba labs. Ten labs are what limits research (agricultural packs are made
# faster than the labs use them), and with few labs speed beats productivity: research = packs used x (1 + productivity).
SX0, SY0 = 34, -418
SUNITS = ["speed-module"] * 4 + ["speed-module-2"] * 2 + ["speed-module-3"]
# Step `more`: three more blocks of nine units for the fill of every surface (about 6,400 empty slots): at 7 a minute it would take
# fifteen hours. Two machines of tier 1 feed one of tier 2.
EXTRA = [(-98, -470, ["productivity-module"] * 6 + ["productivity-module-2"] * 3), (-64, -470, ["productivity-module"] * 6 + ["productivity-module-2"] * 3),
         (-8, -470, ["speed-module"] * 6 + ["speed-module-2"] * 3)]


def layout(x0=None, y0=None, units=None):
    x0, y0, units = (X0, Y0, UNITS) if x0 is None else (x0, y0, units)
    ents = []

    def e(name, tx, ty, w=1, h=1):
        ents.append({"name": name, "x": tx + w / 2, "y": ty + h / 2, "direction": 0, "params": dict(Q)})

    for i in range(len(units)):
        ux = x0 + 3 * i
        e("requester-chest", ux + 1, y0)
        e("fast-inserter", ux + 1, y0 + 1)
        e("assembling-machine-3", ux, y0 + 2, 3, 3)
        e("fast-inserter", ux + 1, y0 + 5)
        e("passive-provider-chest", ux + 1, y0 + 6)
    e("substation", x0 + 3 * len(units), y0 + 2, 2, 2)
    return ents


CONFIG = ("local s=game.surfaces.nauvis local f=game.forces.player local n=0 for i,rec in pairs(UNITS) do local ux=X0+3*(i-1) local m=s.find_entities_filtered{name='assembling-machine-3',position={ux+1.5,Y0+3.5},radius=0.6}[1] "
          "local rq=s.find_entities_filtered{name='requester-chest',position={ux+1.5,Y0+0.5},radius=0.3}[1] local pv=s.find_entities_filtered{name='passive-provider-chest',position={ux+1.5,Y0+6.5},radius=0.3}[1] "
          "m.set_recipe(rec) local lp=rq.get_logistic_point(defines.logistic_member_index.logistic_container) local sec=lp.get_section(1) or lp.add_section() for k,ing in pairs(f.recipes[rec].ingredients) do sec.set_slot(k,{value={type='item',name=ing.name,quality='normal'},min=ing.amount*6}) end "
          "pv.get_inventory(defines.inventory.chest).set_bar((rec:find('%-2$') or rec:find('%-3$')) and 11 or 3) n=n+1 end rcon.print('units set '..n)")
LABS = ("local f=game.forces.player local best=nil for n,q in pairs(prototypes.quality) do if n~='quality-unknown' and f.is_quality_unlocked(n) and (best==nil or q.level>best.level) then best=q end end "
        "local net=game.surfaces.nauvis.find_logistic_network_by_position({-27.5,-393.5},'player') local put,back,want=0,0,0 for _,l in pairs(game.surfaces.gleba.find_entities_filtered{type='lab'}) do local mi=l.get_module_inventory() for i=1,#mi do local st=mi[i] "
        "if not (st.valid_for_read and st.name=='speed-module-3') then want=want+1 if net.get_item_count('speed-module-3')>0 and net.remove_item{name='speed-module-3',count=1}==1 then if st.valid_for_read then back=back+net.insert{name=st.name,count=1,quality='normal'} end "
        "st.set_stack{name='speed-module-3',count=1,quality=best.name} put=put+1 end end end end rcon.print('lab slots without a speed module 3: '..want..', installed '..put..', other modules handed back '..back)")
# Every surface, every empty module slot (the Captain, 2026-11-13: "look for empty module slots and fill them with modules that are
# useful ... productivity and speed"; no efficiency modules, no quality modules). The choice per machine:
#   mining drills and pumpjacks  productivity (the patch lasts longer)
#   a machine whose recipe takes productivity and that is NOT working at the moment (waiting for input or with a full output: it has
#       time to spare)  productivity
#   a machine that IS working (it is the narrow point of its line), or whose recipe refuses productivity, a recycler, a beacon  speed
#   a machine that already holds modules gets more of the same kind; labs are left to step `labs` (speed module 3)
# Forty speed modules 2 are always left in the network for the speed module 3 unit (the labs come first).
# A surface whose accumulators are below 40% is skipped for that pass: modules raise the power draw (+60% each for productivity, +50%
# for speed) and a brown-out would cost more than the modules bring.
INSTALL = ("local f=game.forces.player local best=nil for n,q in pairs(prototypes.quality) do if n~='quality-unknown' and f.is_quality_unlocked(n) and (best==nil or q.level>best.level) then best=q end end "
           "local net=game.surfaces.nauvis.find_logistic_network_by_position({-27.5,-393.5},'player') local stock={P=net.get_item_count('productivity-module-2'),S=math.max(0,net.get_item_count('speed-module-2')-40)} local item={P='productivity-module-2',S='speed-module-2'} "
           "local put={P=0,S=0} local want={P=0,S=0} local skipped={} local W=defines.entity_status.working "
           "local function kind(e) local mi=e.get_module_inventory() for i=1,#mi do if mi[i].valid_for_read then local n=mi[i].name if n:find('^productivity') then return 'P' elseif n:find('^speed') then return 'S' else return nil end end end "
           "if e.type=='mining-drill' then return 'P' end if e.type=='beacon' or e.name=='recycler' then return 'S' end local r=e.get_recipe() if not r and e.type=='furnace' then r=e.previous_recipe and e.previous_recipe.name and f.recipes[e.previous_recipe.name.name or e.previous_recipe.name] end if not r then return nil end "
           "if r.prototype.allowed_effects.productivity and e.status~=W then return 'P' end return 'S' end "
           "local order={} for _,n in pairs{'gleba'} do order[#order+1]=game.surfaces[n] end for _,p in pairs(f.platforms) do if p.name:find('Wheel$') then order[#order+1]=p.surface end end for _,n in pairs{'vulcanus','fulgora','nauvis'} do order[#order+1]=game.surfaces[n] end "
           "for _,p in pairs(f.platforms) do if not p.name:find('Wheel$') and p.surface then order[#order+1]=p.surface end end "
           "for _,s in pairs(order) do local a,cap=0,0 for _,e in pairs(s.find_entities_filtered{name='accumulator',limit=60}) do a=a+e.energy cap=cap+e.electric_buffer_size end "
           "if cap>0 and a/cap<0.4 then skipped[#skipped+1]=s.name else for _,e in pairs(s.find_entities_filtered{force=f,type={'assembling-machine','furnace','mining-drill','beacon','rocket-silo'}}) do local mi=e.get_module_inventory() "
           "if mi and #mi>0 and mi.count_empty_stacks()>0 then local k=kind(e) if k then for i=1,#mi do if not mi[i].valid_for_read then want[k]=want[k]+1 if APPLY and put[k]<stock[k] and net.remove_item{name=item[k],count=1}==1 then mi[i].set_stack{name=item[k],count=1,quality=best.name} put[k]=put[k]+1 end end end end end end end end "
           "rcon.print('empty slots: productivity '..want.P..', speed '..want.S..' | in stock '..stock.P..' / '..stock.S..' | installed '..put.P..' / '..put.S..' at '..best.name..(#skipped>0 and (' | skipped for low power: '..table.concat(skipped,',')) or ''))")
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
    if step == "speed":
        r = json.loads(tools["place_entities"](json.dumps(layout(SX0, SY0, SUNITS)), surface="nauvis", dry_run=not apply)) if "--config" not in sys.argv else {}
        print("placed" if apply else "dry run", r.get("placed"), "failed", json.dumps(r.get("failed") or [])[:300])
        if apply or "--config" in sys.argv:
            print(tools["run_lua"](CONFIG.replace("UNITS", "{" + ",".join("'%s'" % u for u in SUNITS) + "}").replace("X0", str(SX0)).replace("Y0", str(SY0)).replace("MODULE", MODULE)))
    if step == "more":
        for x0, y0, units in EXTRA:
            r = json.loads(tools["place_entities"](json.dumps(layout(x0, y0, units)), surface="nauvis", dry_run=not apply)) if "--config" not in sys.argv else {}
            print((x0, y0), "placed" if apply else "dry run", r.get("placed"), "failed", json.dumps(r.get("failed") or [])[:200])
            if apply or "--config" in sys.argv:
                print(tools["run_lua"](CONFIG.replace("UNITS", "{" + ",".join("'%s'" % u for u in units) + "}").replace("X0", str(x0)).replace("Y0", str(y0)).replace("MODULE", MODULE)))
    if step == "labs":
        print(tools["run_lua"](LABS))
    if step == "config" or (step == "build" and apply):
        print(tools["run_lua"](sub(CONFIG)))
    elif step == "install":
        print(tools["run_lua"](sub(INSTALL, apply)))
    elif step == "status":
        print(tools["run_lua"](sub(STATUS)).replace(" ;; ", "\n").replace(" ; ", "\n  "))


if __name__ == "__main__":
    main()
