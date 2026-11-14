#!/usr/bin/env python3
"""Pack delivery between Nauvis and Gleba, both ways (2026-11-14).
  stops     every "Nauvis-Gleba" shuttle that is parked: the Nauvis stop becomes
              fuel AND oxidizer AND magazines AND all requests satisfied   OR   fuel AND oxidizer AND magazines AND 5 minutes since arrival
            so one scarce pack (chemical, production) no longer holds a ship with the other packs aboard while Gleba's labs starve.
            The Gleba stop is fuel, oxidizer, magazines and 60 quiet seconds, OR fuel, oxidizer, magazines and 800 agricultural packs
            aboard (constant 1600: hub items count double on the wires): a ship drips packs to the Gleba pad for a long time and is
            never quiet, and the agricultural packs aboard rot meanwhile. Ships in transit are skipped: run again.
            Quiet seconds do not work at Nauvis: the ship's own inserters touch the hub (plates, magazines), so the fallback is a time wait.
  agri      every "Nauvis-Gleba" shuttle asks Gleba for 800 agricultural packs with minimum_delivery_count 800. The Gleba silo only
            launches when the network holds a whole delivery, i.e. when the science chest (gate at 1,000) has piled up 800 that Gleba's
            own labs did not use. So Nauvis gets the surplus only. The Nauvis pad asks for 1,600; the lab chests already ask for 100 each.
  agri-off  remove those requests again (ships and pad).
  unferry   on the three ships built 2026-11-14 (platform index 32, 33, 34) remove the single-item sections that the twin step copied
            from the sibling's orbit-ferry group (logistic 2000, chemical 2000, military 300, production 80).
  twin3     Nauvis-Vulcanus 3 takes the Vulcanus stop of Nauvis-Vulcanus 2 (wait for packs), keeping its place in the schedule.
  status    one line per ship.
Usage: gleba_delivery.py stops|agri|agri-off|unferry|twin3|status"""
import sys

from _game import tools

FIND = "local f=game.forces.player local o={} local function ships(w) local r={} for i,p in pairs(f.platforms) do if p.name:find(w,1,true) and p.hub then r[#r+1]={i,p} end end return r end "
REARRIVE = "local function settle(p,cur) if p.space_location and p.state~=defines.space_platform_state.waiting_at_station then p.space_location=p.space_location.name end end "

STOPS = FIND + REARRIVE + """
local function c(kind,name,n,cmp) return {type='circuit',compare_type=cmp or 'and',condition={first_signal={type=kind,name=name},comparator='>=',constant=n}} end
local function base(fuel,mags,first) return c('fluid','thruster-fuel',fuel,first),c('fluid','thruster-oxidizer',fuel),c('item','firearm-magazine',mags) end
for _,q in pairs(ships('Nauvis-Gleba')) do local i,p=q[1],q[2] if not p.space_location then o[#o+1]='#'..i..' in transit, skipped' else
local a1,a2,a3=base(20000,800) local b1,b2,b3=base(20000,800,'or') local g1,g2,g3=base(32000,500) local h1,h2,h3=base(32000,500,'or')
local sch=p.schedule or {} local cur=sch.current or 1 if p.space_location.name=='gleba' then cur=2 else cur=1 end
sch.records={{station='nauvis',wait_conditions={a1,a2,a3,{type='all_requests_satisfied',compare_type='and'},b1,b2,b3,{type='time',compare_type='and',ticks=18000}}},
{station='gleba',wait_conditions={g1,g2,g3,{type='inactivity',compare_type='and',ticks=3600},h1,h2,h3,c('item','agricultural-science-pack',1600)}}} sch.current=cur p.schedule=sch p.paused=false settle(p)
local w={} for _,x in pairs(p.schedule.records[1].wait_conditions) do w[#w+1]=(x.compare_type or '?')..' '..x.type end
o[#o+1]='#'..i..' at '..p.space_location.name..' current '..p.schedule.current..' state '..p.state..' nauvis stop: '..table.concat(w,', ') end end
rcon.print(table.concat(o,'|'))
"""

AGRI = FIND + """
for _,q in pairs(ships('Nauvis-Gleba')) do local i,p=q[1],q[2] local secs=p.hub.get_logistic_sections() local have=false
for _,se in pairs(secs.sections) do for _,fl in pairs(se.filters) do if fl.value and fl.value.name=='agricultural-science-pack' then have=true end end end
if not have then local ns=secs.add_section() ns.set_slot(1,{value={type='item',name='agricultural-science-pack',quality='normal'},min=800,import_from='gleba',minimum_delivery_count=800}) end
for si,se in pairs(secs.sections) do for _,fl in pairs(se.filters) do if fl.value and fl.value.name=='agricultural-science-pack' then
o[#o+1]='#'..i..' sec'..si..' agricultural min '..fl.min..' max '..tostring(fl.max)..' from '..tostring(fl.import_from and fl.import_from.name)..' min delivery '..tostring(fl.minimum_delivery_count) end end end end
local pad=game.surfaces.nauvis.find_entities_filtered{type='cargo-landing-pad'}[1] local ps=pad.get_logistic_sections() local have=false
for _,se in pairs(ps.sections) do for _,fl in pairs(se.filters) do if fl.value and fl.value.name=='agricultural-science-pack' then have=true end end end
if not have then local ns=ps.add_section() ns.set_slot(1,{value={type='item',name='agricultural-science-pack',quality='normal'},min=1600}) end
for si,se in pairs(ps.sections) do for _,fl in pairs(se.filters) do if fl.value and fl.value.name=='agricultural-science-pack' then o[#o+1]='nauvis pad sec'..si..' agricultural min '..fl.min end end end
rcon.print(table.concat(o,'|'))
"""

AGRI_OFF = FIND + """
local function strip(ent,tag) local secs=ent.get_logistic_sections() for si=#secs.sections,1,-1 do local se=secs.sections[si] if se.is_manual and #se.filters==1 and se.filters[1].value and se.filters[1].value.name=='agricultural-science-pack' then secs.remove_section(si) o[#o+1]=tag..' removed' end end end
for _,q in pairs(ships('Nauvis-Gleba')) do strip(q[2].hub,'#'..q[1]) end strip(game.surfaces.nauvis.find_entities_filtered{type='cargo-landing-pad'}[1],'nauvis pad')
rcon.print(table.concat(o,'|'))
"""

UNFERRY = FIND + """
local junk={['logistic-science-pack']=2000,['chemical-science-pack']=2000,['military-science-pack']=300,['production-science-pack']=80}
for _,i in pairs({32,33,34}) do local p=f.platforms[i] if p and p.hub and p.name:find('3 Shuttle',1,true) or p and p.hub and p.name:find('Gleba 6 Shuttle',1,true) then local secs=p.hub.get_logistic_sections() local n=0
for si=#secs.sections,1,-1 do local se=secs.sections[si] if se.is_manual and (se.group==nil or se.group=='') and #se.filters==1 and se.filters[1].value and junk[se.filters[1].value.name]==se.filters[1].min then secs.remove_section(si) n=n+1 end end
local left={} for _,se in pairs(secs.sections) do for _,fl in pairs(se.filters) do if fl.value then left[#left+1]=fl.value.name:gsub('%-science%-pack','')..' '..fl.min end end end
o[#o+1]='#'..i..' removed '..n..' copied ferry sections; left: '..table.concat(left,', ') end end
rcon.print(table.concat(o,'|'))
"""

TWIN3 = FIND + REARRIVE + """
local new=ships('Nauvis-Vulcanus 3')[1] local old=ships('Nauvis-Vulcanus 2')[1]
if new and old then local p=new[2] if not p.space_location then o[#o+1]='in transit, skipped' else local sch=p.schedule local cur=(p.space_location.name=='vulcanus') and 2 or 1
sch.records=old[2].schedule.records sch.current=cur p.schedule=sch p.paused=false settle(p)
for ri,rec in pairs(p.schedule.records) do o[#o+1]='stop'..ri..(p.schedule.current==ri and '*' or '')..' '..rec.station..' '..#rec.wait_conditions..' conditions' end o[#o+1]='state '..p.state end end
rcon.print(table.concat(o,'|'))
"""

STATUS = FIND + """
for _,q in pairs(ships('Nauvis-Gleba')) do local i,p=q[1],q[2] local inv=p.hub.get_inventory(defines.inventory.hub_main) local t={}
for _,n in pairs({'automation','logistic','chemical','production','agricultural'}) do t[#t+1]=n:sub(1,4)..' '..inv.get_item_count(n..'-science-pack') end
local tr=0 for _,it in pairs(p.hub.get_inventory(defines.inventory.hub_trash).get_contents()) do tr=tr+it.count end
o[#o+1]='#'..i..' '..(p.space_location and p.space_location.name or 'transit')..' state '..p.state..' stop '..(p.schedule and p.schedule.current or 0)..' | '..table.concat(t,', ')..' | spoilage '..inv.get_item_count('spoilage')..' trash '..tr end
rcon.print(table.concat(o,'|'))
"""

if __name__ == "__main__":
    lua = {"stops": STOPS, "agri": AGRI, "agri-off": AGRI_OFF, "unferry": UNFERRY, "twin3": TWIN3, "status": STATUS}[sys.argv[1]]
    print(tools["run_lua"](" ".join(lua.split())).replace("|", "\n"))
