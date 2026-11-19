#!/usr/bin/env python3
"""One line of facts per shuttle, for the fleet rework (the Captain, 2026-11-18: every shuttle stable when parked at either end, timed
runs, running requirements only, cargo as wants). Read-only.
  fleet_survey.py            a block per shuttle: place, schedule with every wait condition, request sections, drop sections (max 0),
                             trash, turrets and ammunition, machines by recipe, fluids, power, deck size
  fleet_survey.py --brief    one line per shuttle
Usage: fleet_survey.py [--brief] [INDEX ...]"""
import sys

from _game import tools

L = tools["run_lua"]
NL = "string.char(10)"

ONE = ("local p=game.forces.player.platforms[%d] local s=p.surface local hub=p.hub local inv=hub.get_inventory(defines.inventory.hub_main) local o={} local function w(x) o[#o+1]=x end "
       "local sm={} for k,v in pairs(defines.space_platform_state) do sm[v]=k end "
       "local function cond(c) if c.condition then local f=c.condition.first_signal return (f and f.name or '?')..c.condition.comparator..tostring(c.condition.constant) elseif c.ticks then return c.type..' '..math.floor(c.ticks/60)..'s' else return c.type end end "
       "w('== '..p.index..' '..p.name:gsub('%%[.-%%]','')..' | '..(p.space_location and p.space_location.name or 'flying')..' | '..tostring(sm[p.state])..(p.paused and ' PAUSED' or '')..' | weight '..math.floor(p.weight/1000)..' t | hub slots '..#inv..' free '..inv.count_empty_stacks()) "
       "if p.schedule then for i,r in pairs(p.schedule.records) do local t={} for _,c in pairs(r.wait_conditions or {}) do t[#t+1]=(c.compare_type=='or' and 'OR ' or '')..cond(c) end w('  stop '..i..(p.schedule.current==i and '*' or ' ')..r.station..': '..table.concat(t,' & ')) end else w('  no schedule') end "
       "for _,pt in pairs(hub.get_logistic_point()) do for _,sec in pairs(pt.sections) do local u={} local drop=true for i=1,sec.filters_count do local f=sec.get_slot(i) if f and f.value then if not (f.max and f.max==0) then drop=false end "
       "u[#u+1]=f.value.name..' '..tostring(f.min)..(f.max and ('..'..f.max) or '')..(f.import_from and ('@'..(type(f.import_from)=='string' and f.import_from or f.import_from.name)) or '') end end "
       "if #u>0 then w('  '..(drop and 'DROP' or 'ask ')..' ['..sec.group..']'..(sec.active and '' or ' OFF')..': '..table.concat(u,', '):sub(1,420)) end end end "
       "local tr=hub.get_inventory(defines.inventory.hub_trash) local t={} if tr then for _,i in pairs(tr.get_contents()) do t[#t+1]=i.name..' '..i.count end end if #t>0 then w('  TRASH (blocks departure if it cannot drop): '..table.concat(t,', ')) end "
       "local tu={} for _,e in pairs(s.find_entities_filtered{type={'ammo-turret','electric-turret'}}) do local k=e.name tu[k]=tu[k] or {0,0} tu[k][1]=tu[k][1]+1 if e.type=='ammo-turret' and e.get_inventory(defines.inventory.turret_ammo).is_empty() then tu[k][2]=tu[k][2]+1 end end "
       "local t2={} for k,v in pairs(tu) do t2[#t2+1]=k..' '..v[1]..(v[2]>0 and (' ('..v[2]..' EMPTY)') or '') end table.sort(t2) "
       "local am={} for _,n in pairs{'explosive-rocket','rocket','uranium-rounds-magazine','piercing-rounds-magazine','firearm-magazine','railgun-ammo','repair-pack'} do local c=inv.get_item_count(n) if c>0 then am[#am+1]=n..' '..c end end w('  turrets: '..table.concat(t2,', ')..' | hold: '..table.concat(am,', ')) "
       "local h={} for _,e in pairs(s.find_entities_filtered{type={'assembling-machine','furnace'}}) do local r=e.get_recipe() local k=(r and r.name or e.name) h[k]=(h[k] or 0)+1 end local u={} for k,v in pairs(h) do u[#u+1]=k..' x'..v end table.sort(u) w('  machines: '..table.concat(u,', ')) "
       "local fl={} for _,e in pairs(s.find_entities_filtered{type='storage-tank'}) do for n,a in pairs(e.get_fluid_contents()) do fl[n]=(fl[n] or 0)+a end end local t3={} for k,v in pairs(fl) do t3[#t3+1]=k..' '..math.floor(v) end table.sort(t3) "
       "local c={} for _,n in pairs{'thruster','asteroid-collector','solar-panel','accumulator','cargo-bay','fusion-reactor','fusion-generator','nuclear-reactor'} do local k=s.count_entities_filtered{name=n} if k>0 then c[#c+1]=n..' '..k end end "
       "local d,g=0,s.count_entities_filtered{type='entity-ghost'} for _,x in pairs(s.find_entities_filtered{force='player'}) do if x.is_entity_with_health and x.health<x.max_health then d=d+1 end end "
       "w('  fluids: '..table.concat(t3,', ')..' | '..table.concat(c,', ')..' | deck tiles '..s.count_tiles_filtered{name='space-platform-foundation'}..' | damaged '..d..', ghosts '..g) "
       "rcon.print(table.concat(o," + NL + "))")

LIST = "local t={} for i,p in pairs(game.forces.player.platforms) do if p.name:find('Shuttle',1,true) or p.name:find('Courier',1,true) then t[#t+1]=i end end rcon.print(table.concat(t,','))"


def shuttles():
    return [int(x) for x in L(LIST).strip().split(",") if x]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    idx = [int(a) for a in args] or shuttles()
    for i in idx:
        out = L(ONE % i)
        print(out.splitlines()[0] if "--brief" in sys.argv else out)


if __name__ == "__main__":
    main()
