#!/usr/bin/env python3
"""Whole-game audit, every surface (the Captain, 2026-11-18: "check out the whole base for problems, alerts, ghosts, backups,
starvations, non-op machines, missing recipes, machines not upgraded to legendary, damage, fuel problems, storage problems";
"check the whole game, all maps"). READ-ONLY. It complements scripts/worst_bottleneck.py (starved / backed / full, ranked).
Per surface, one block; a line is printed only when it has something to say:
  alerts    the in-game alert overview, by kind
  ghosts    entity ghosts by name, tile ghosts, entities marked for deconstruction or upgrade
  damage    damaged entities by name
  power     entities with no power or low power, by name; accumulator charge
  fuel      burner machines and reactors with no fuel; thrusters by state
  idle      crafting machines with no recipe, by name (a furnace with nothing to do is not counted)
  quality   entities below the best researched quality, by name
  turrets   ammunition turrets with no ammunition
  storage   landing pad and hub free slots; storage chests free slots
  modules   empty module slots
Usage: audit_all.py [SURFACE ...]"""
import sys

from _game import tools

L = tools["run_lua"]

ONE = ("local s=game.surfaces['%s'] local f=game.forces.player local o={} local function w(k,t) if #t>0 then table.sort(t) o[#o+1]='  '..k..': '..table.concat(t,', ') end end "
       "local function fold(h) local t={} for k,v in pairs(h) do t[#t+1]=k..' '..v end return t end "
       "local best=nil for n,q in pairs(prototypes.quality) do if n~='quality-unknown' and f.is_quality_unlocked(n) and (best==nil or q.level>best.level) then best=q end end "
       "local E=defines.entity_status local an={} for k,v in pairs(defines.alert_type) do an[v]=k end "
       "local al={} for _,pl in pairs(game.players) do local ok,a=pcall(function() return pl.get_alerts{surface=s} end) if ok and a then for _,bytype in pairs(a) do for ty,list in pairs(bytype) do local k=tostring(an[ty] or ty) al[k]=math.max(al[k] or 0,#list) end end end end w('ALERTS',fold(al)) "
       "local gh,dm,np,lp,nf,idle,ql,empt,dec,upg={}, {}, {}, {}, {}, {}, {}, {}, 0, 0 local tot,mods=0,0 local skip={['logistic-robot']=1,['construction-robot']=1,['cargo-pod']=1,['character']=1,['entity-ghost']=1,['tile-ghost']=1,['item-request-proxy']=1,['spider-leg']=1,['rocket-silo-rocket']=1,['rocket-silo-rocket-shadow']=1} "
       "for _,e in pairs(s.find_entities_filtered{force=f}) do local ty=e.type if ty=='entity-ghost' then gh[e.ghost_name]=(gh[e.ghost_name] or 0)+1 elseif ty~='tile-ghost' then tot=tot+1 "
       "if e.is_entity_with_health and e.health and e.max_health and e.health<e.max_health then dm[e.name]=(dm[e.name] or 0)+1 end "
       "if e.to_be_deconstructed() then dec=dec+1 end if e.to_be_upgraded() then upg=upg+1 end "
       "local st=e.status if st==E.no_power then np[e.name]=(np[e.name] or 0)+1 elseif st==E.low_power then lp[e.name]=(lp[e.name] or 0)+1 elseif st==E.no_fuel then nf[e.name]=(nf[e.name] or 0)+1 end "
       "if (ty=='assembling-machine' or ty=='rocket-silo') and st==E.no_recipe then idle[e.name]=(idle[e.name] or 0)+1 end "
       "if not skip[ty] and e.quality.level<best.level then ql[e.name..'/'..e.quality.name]=(ql[e.name..'/'..e.quality.name] or 0)+1 end "
       "if ty=='ammo-turret' and e.get_inventory(defines.inventory.turret_ammo).is_empty() then empt[e.name]=(empt[e.name] or 0)+1 end "
       "if ty=='assembling-machine' or ty=='furnace' or ty=='mining-drill' or ty=='lab' or ty=='beacon' then local mi=e.get_module_inventory() if mi then mods=mods+mi.count_empty_stacks() end end end end "
       "w('GHOSTS',fold(gh)) local tg=s.count_entities_filtered{type='tile-ghost'} if tg>0 then o[#o+1]='  TILE GHOSTS: '..tg end if dec+upg>0 then o[#o+1]='  MARKED: for deconstruction '..dec..', for upgrade '..upg end "
       "w('DAMAGED',fold(dm)) w('NO POWER',fold(np)) w('LOW POWER',fold(lp)) w('NO FUEL',fold(nf)) w('NO RECIPE',fold(idle)) w('BELOW '..best.name:upper(),fold(ql)) w('TURRETS WITH NO AMMUNITION',fold(empt)) "
       "local a,c=0,0 for _,e in pairs(s.find_entities_filtered{type='accumulator'}) do a=a+e.energy c=c+e.electric_buffer_size end if c>0 and a/c<0.5 then o[#o+1]='  ACCUMULATORS: '..math.floor(100*a/c)..'%%' end "
       "local st={} for _,pad in pairs(s.find_entities_filtered{type='cargo-landing-pad'}) do local inv=pad.get_inventory(defines.inventory.cargo_landing_pad_main) st[#st+1]='landing pad '..inv.count_empty_stacks()..' of '..#inv..' free' end "
       "if s.platform and s.platform.hub and s.platform.hub.valid then local inv=s.platform.hub.get_inventory(defines.inventory.hub_main) if inv.count_empty_stacks()<#inv*0.15 then st[#st+1]='hub '..inv.count_empty_stacks()..' of '..#inv..' free' end local tr=s.platform.hub.get_inventory(defines.inventory.hub_trash) if tr and not tr.is_empty() then st[#st+1]='hub holds trash' end end "
       "local n,free,cap=0,0,0 for _,ch in pairs(s.find_entities_filtered{name='storage-chest'}) do local inv=ch.get_inventory(defines.inventory.chest) n=n+1 free=free+inv.count_empty_stacks() cap=cap+#inv end if n>0 and free<cap*0.3 then st[#st+1]='storage chests '..free..' of '..cap..' slots free' end w('STORAGE',st) "
       "if mods>0 then o[#o+1]='  EMPTY MODULE SLOTS: '..mods end "
       "local th={} for _,e in pairs(s.find_entities_filtered{type={'reactor','fusion-reactor'}}) do local k=e.name..' '..tostring(e.status==E.working and 'working' or (e.status==E.no_fuel and 'NO FUEL' or 'other')) th[k]=(th[k] or 0)+1 end w('REACTORS',fold(th)) "
       "local nm=s.platform and s.platform.name:gsub('%%[.-%%]',''):gsub('^%%s+','') or s.name rcon.print('== '..nm..' ('..s.name..', '..tot..' entities)'..(#o>0 and (string.char(10)..table.concat(o,string.char(10))) or '  clean'))")


def main():
    names = sys.argv[1:] or L("local o={} for _,s in pairs(game.surfaces) do if s.count_entities_filtered{force='player',limit=1}>0 then o[#o+1]=s.name end end rcon.print(table.concat(o,','))").strip().split(",")
    for n in names:
        print(L(ONE % n), flush=True)


if __name__ == "__main__":
    main()
