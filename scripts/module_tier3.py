#!/usr/bin/env python3
"""Tier-3 modules at the best researched quality in every module slot of ours (the Captain, 2026-11-14: "upgrade all machine modules to
the level 3 epic quality variety").
  count    slots per surface by module kind/tier/quality, plus network stock of module items, plus power headroom per surface
  mall     [--apply] robot-fed units at TX0,TY0 that make speed-module-3 (and productivity-module-3 once researched); the tier-2 feedstock
           comes from the network (modules swapped out of machines go back there), circuits and processing units too
  install  [--apply] [--surface NAME] swaps the tier-1/tier-2 modules of a machine for a tier-3 module of the SAME KIND (speed stays speed,
           productivity stays productivity, efficiency, quality likewise) at the best researched quality, tier-3 stock permitting.
           Order of value: Gleba labs, Gleba rest, wheels, Vulcanus, Fulgora, Nauvis, other platforms. The removed modules go back into the
           Nauvis network (a machine's whole module set is swapped slot by slot). Power rule: speed/productivity tier 3 draw more; a surface
           whose accumulators are under 50% or that is on the short-power list (POWER_SHORT) gets only what the gate allows.
           Idempotent: slots already at tier 3 and best quality are skipped. Empty slots are filled with the kind of the other slots only.
Modules at tier 3 but below best quality are raised to best quality with the standing method of scripts/upgrade_quality.py --items.
Usage: module_tier3.py count | mall [--apply] | install [--apply] [--surface NAME] [--limit N]"""
import json
import sys

from _game import tools

TX0, TY0 = -140, -470
UNITS = ["speed-module-3"] * 5 + ["productivity-module-3"] * 3 + ["speed-module-2"] * 2 + ["productivity-module-2"] * 2
Q = {"quality": "epic"}
NET = "{-27.5,-393.5}"
BEST = ("local f=game.forces.player local best=nil for n,q in pairs(prototypes.quality) do if n~='quality-unknown' and f.is_quality_unlocked(n) and (best==nil or q.level>best.level) then best=q end end ")


def layout(x0, y0, units):
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
          "if m and rq and pv and f.recipes[rec].enabled then m.set_recipe(rec) local lp=rq.get_logistic_point(defines.logistic_member_index.logistic_container) local sec=lp.get_section(1) or lp.add_section() for k,ing in pairs(f.recipes[rec].ingredients) do sec.set_slot(k,{value={type='item',name=ing.name,quality='normal'},min=ing.amount*4}) if ing.name:find('module') then sec.set_slot(k+10,{value={type='item',name=ing.name,quality='epic'},min=ing.amount*4}) end end "
          "pv.get_inventory(defines.inventory.chest).set_bar(11) n=n+1 end end rcon.print('units set '..n)")

COUNT = BEST + ("local s=game.surfaces['%s'] local by={} local slots=0 for _,e in pairs(s.find_entities_filtered{force=f,type={'assembling-machine','furnace','lab','mining-drill','beacon','rocket-silo'}}) do local mi=e.get_module_inventory() if mi then for i=1,#mi do slots=slots+1 local st=mi[i] local k='empty' if st.valid_for_read then k=st.name:gsub('%%-module','')..'/'..st.quality.name end by[k]=(by[k] or 0)+1 end end end "
                "local a,cap=0,0 for _,e in pairs(s.find_entities_filtered{name='accumulator',limit=100}) do a=a+e.energy cap=cap+e.electric_buffer_size end by['_slots']=slots by['_acc%%']=cap>0 and math.floor(100*a/cap) or -1 rcon.print(helpers.table_to_json(by))")

STOCK = ("local net=game.surfaces.nauvis.find_logistic_network_by_position(%s,'player') local o={} for _,k in pairs{'speed','productivity','efficiency','quality'} do for _,t in pairs{'','-2','-3'} do local n=k..'-module'..t local c=net.get_item_count(n) local q=0 for _,qq in pairs{'normal','uncommon','rare','epic','legendary'} do local v=net.get_item_count{name=n,quality=qq} if v>0 then o[#o+1]=n..'/'..qq..'='..v end end end end "
         "for _,n in pairs{'advanced-circuit','processing-unit'} do o[#o+1]=n..'='..net.get_item_count(n) end rcon.print(table.concat(o,' '))") % NET

# Surfaces where power is short (measured 2026-11-14 in the task; see the report): tier-3 speed/productivity are NOT put into these unless
# the accumulator gate allows and the surface is not listed. Efficiency modules are exempt from the gate.
POWER_SHORT = ["aquilo"]

INSTALL = BEST + ("local net=game.surfaces.nauvis.find_logistic_network_by_position(" + NET + ",'player') local apply=APPLY local limit=LIMIT local s=game.surfaces['SURF'] local short=SHORT local gate=GATE "
                  "local function kindof(n) return n:match('^(%a+)%-module') end local have={} local function stock(k) if have[k]==nil then have[k]=net.get_item_count(k..'-module-3') end return have[k] end "
                  "local a,cap=0,0 for _,e in pairs(s.find_entities_filtered{name='accumulator',limit=100}) do a=a+e.energy cap=cap+e.electric_buffer_size end local lowpow=(cap>0 and a/cap<gate) or short[s.name] "
                  "local done,slots,blocked,nokind,raised=0,0,0,0,0 local back={} local per={} "
                  "for _,e in pairs(s.find_entities_filtered{force=f,type=TYPES}) do if done>=limit then break end local mi=e.get_module_inventory() if mi and #mi>0 then "
                  "for i=1,#mi do local st=mi[i] if st.valid_for_read then local n=st.name local k=kindof(n) if k and not n:find('%-3$') then slots=slots+1 local t3=k..'-module-3' "
                  "if (k=='speed' or k=='productivity') and lowpow then blocked=blocked+1 elseif done<limit and stock(k)>0 then if apply then if net.remove_item{name=t3,count=1}==1 then local bk=n..'|'..st.quality.name back[bk]=(back[bk] or 0)+1 st.set_stack{name=t3,count=1,quality=best.name} done=done+1 have[k]=have[k]-1 else have[k]=0 end else done=done+1 have[k]=have[k]-1 end per[k]=(per[k] or 0)+1 end elseif not k then nokind=nokind+1 "
                  "elseif st.name:find('%-3$') and st.quality.level<best.level then if apply then local nm=st.name st.set_stack{name=nm,count=1,quality=best.name} end raised=raised+1 end end end end end "
                  "if apply then for bk,c in pairs(back) do local nm,ql=bk:match('^(.-)|(.+)$') net.insert{name=nm,count=c,quality=ql} end end "
                  "rcon.print(helpers.table_to_json({surface=s.name,swapped=done,still_tier12=slots-done,blocked_power=blocked,raised_quality=raised,acc_pct=cap>0 and math.floor(100*a/cap) or -1,lowpower=lowpow and true or false,per=per,returned=back}))")


def lua_install(surface, apply, limit, gate=0.5, types="'lab','assembling-machine','furnace','mining-drill','beacon','rocket-silo'"):
    short = "{" + ",".join("%s=true" % s for s in POWER_SHORT) + "}"
    return (INSTALL.replace("APPLY", "true" if apply else "false").replace("LIMIT", str(limit)).replace("SURF", surface)
            .replace("SHORT", short).replace("TYPES", "{" + types + "}").replace("GATE", str(gate)))


def surfaces():
    return tools["run_lua"]("local o={} for _,s in pairs(game.surfaces) do o[#o+1]=s.name end rcon.print(table.concat(o,','))").strip().split(",")


def main():
    step = sys.argv[1]
    apply = "--apply" in sys.argv
    if step == "count":
        for n in surfaces():
            print(n, tools["run_lua"](COUNT % n).strip())
        print(tools["run_lua"](STOCK))
    elif step == "mall":
        r = json.loads(tools["place_entities"](json.dumps(layout(TX0, TY0, UNITS)), surface="nauvis", dry_run=not apply))
        print("placed" if apply else "dry run", r.get("placed"), "failed", json.dumps(r.get("failed") or [])[:400])
        if apply or "--config" in sys.argv:
            print(tools["run_lua"](CONFIG.replace("UNITS", "{" + ",".join("'%s'" % u for u in UNITS) + "}").replace("X0", str(TX0)).replace("Y0", str(TY0))))
    elif step == "install":
        limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else 100000
        only = sys.argv[sys.argv.index("--surface") + 1] if "--surface" in sys.argv else None
        for n in ([only] if only else surfaces()):
            print(tools["run_lua"](lua_install(n, apply, limit, types=("'%s'" % sys.argv[sys.argv.index("--types") + 1].replace(",", "','")) if "--types" in sys.argv else "'lab','assembling-machine','furnace','mining-drill','beacon','rocket-silo'")).strip(), flush=True)


if __name__ == "__main__":
    main()
