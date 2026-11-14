#!/usr/bin/env python3
"""The inner shuttles on the new hull (the Captain, 2026-11-13: "Redesign the nine inner shuttles on the new pattern"). The hull is
scripts/aquilo_shuttle.py with INNER set: the same cargo spine (seven bays, 325 slots against 97), two collectors, solar wings and rear
block, but no rockets (the inner routes have no big asteroids): 14 gun turrets, two magazine assemblers and three furnaces, basic
carbonic crushing, and the metallic crusher that reprocesses when ore is full.
  create NAME PLANET      a new platform in that planet's orbit (far planets are rich in chunks; Nauvis orbit is not)
  build NAME [--apply]    dry run, or deck and entities. Never apply twice on the same ship.
  config NAME             filters, recipes, gates, valve, recipe switch (safe to run again; run after a quality upgrade)
  adopt NAME OLD          copies OLD's hub requests, moves OLD's cargo, ammunition, ore, plates and tank contents across (both must be
                          in the same orbit), so the new ship starts loaded. Moving factory-made goods, nothing is created.
  route NAME DEST [--go]  nauvis <-> DEST; without --go it stays paused
  status NAME
Usage: inner_shuttle.py STEP NAME [...]"""
import sys

import aquilo_shuttle as A
from _game import tools

A.INNER = True
HOME = dict(fuel=14000, mags=800)        # one tank of three is on the wire: 14,000 is 42,000 on board
AWAY = dict(fuel=22000, mags=500)
ROUTE = ("local p=game.surfaces['SURF'].platform local function c(t,n,k) return {type='circuit',compare_type='and',condition={first_signal={type=t,name=n},comparator='>=',constant=k}} end "
         "local function stop(st,f,m) return {station=st,wait_conditions={c('fluid','thruster-fuel',f),c('fluid','thruster-oxidizer',f),c('item','firearm-magazine',m)}} end "
         "p.schedule={current=CUR,records={stop('nauvis',HF,HM),stop('DEST',AF,AM)}} p.paused=PAUSED rcon.print('schedule nauvis <-> DEST set, paused='..tostring(p.paused))")
ADOPT = ("local f=game.forces.player local new,old for _,p in pairs(f.platforms) do if p.name=='NEWNAME' then new=p elseif p.name=='OLDNAME' then old=p end end if not (new and old) then rcon.print('platform not found') return end "
         "if not (new.space_location and old.space_location and new.space_location==old.space_location) then rcon.print('not in the same orbit') return end local o={} "
         "local function req(h) for _,pt in pairs(h.get_logistic_point()) do if pt.mode==defines.logistic_mode.requester then return pt end end end local a,b=req(old.hub),req(new.hub) local n=0 "
         "for i=b.sections_count,1,-1 do b.remove_section(i) end for _,sec in pairs(a.sections) do local t=b.add_section(sec.group) if sec.group=='' then for i,fl in pairs(sec.filters) do if fl.value then t.set_slot(i,fl) n=n+1 end end end t.active=sec.active end o[#o+1]='requests copied '..n "
         "local oi,ni=old.hub.get_inventory(defines.inventory.hub_main),new.hub.get_inventory(defines.inventory.hub_main) local moved=0 for _,it in pairs(oi.get_contents()) do if not it.name:find('chunk') and it.name~='space-platform-foundation' then "
         "local put=ni.insert{name=it.name,count=it.count,quality=it.quality} if put>0 then oi.remove{name=it.name,count=put,quality=it.quality} moved=moved+put end end end o[#o+1]='items moved '..moved "
         "local TANKS={water={{-1.5,11.5},{1.5,11.5}},['thruster-oxidizer']={{-7.5,11.5},{-7.5,14.5},{-4.5,14.5}},['thruster-fuel']={{5.5,11.5},{5.5,14.5},{10.5,14.5}}} for _,fn in pairs{'thruster-fuel','thruster-oxidizer','water'} do local have=0 for _,t in pairs(old.surface.find_entities_filtered{name='storage-tank'}) do have=have+(t.get_fluid_contents()[fn] or 0) end local done=0 "
         "for _,q in pairs(TANKS[fn]) do local t=new.surface.find_entities_filtered{name='storage-tank',position=q,radius=0.5}[1] if t and done<have then done=done+t.insert_fluid{name=fn,amount=have-done} end end "
         "local left=done for _,t in pairs(old.surface.find_entities_filtered{name='storage-tank'}) do local h=t.get_fluid_contents()[fn] or 0 if left>0.5 and h>0 then local take=math.min(left,h) local ok=pcall(function() t.remove_fluid(1,{name=fn,amount=take}) end) if not ok then t.clear_fluid_inside() if h-take>0.5 then t.insert_fluid{name=fn,amount=h-take} end end left=left-take end end o[#o+1]=fn..' moved '..string.format('%.0f',done)..' of '..string.format('%.0f',have) end "
         "rcon.print(table.concat(o,', '))")


def main():
    step, name = sys.argv[1], sys.argv[2]
    A.NAME = name
    if step == "create":
        A.PLANET = sys.argv[3]
    if step in ("check", "create", "build", "config", "status"):
        sys.argv = [sys.argv[0], step] + [a for a in sys.argv[3:] if a.startswith("--")]
        return A.main()
    sf, index = A.surface()
    if step == "route":
        dest = sys.argv[3]
        cur = tools["run_lua"]("local p=game.surfaces['%s'].platform rcon.print(p.space_location and p.space_location.name or 'none')" % sf).strip()
        code = (ROUTE.replace("SURF", sf).replace("DEST", dest).replace("CUR", "1" if cur == "nauvis" else "2").replace("PAUSED", "false" if "--go" in sys.argv else "true")
                .replace("HF", str(HOME["fuel"])).replace("HM", str(HOME["mags"])).replace("AF", str(AWAY["fuel"])).replace("AM", str(AWAY["mags"])))
        print(tools["run_lua"](code))
    elif step == "adopt":
        print(tools["run_lua"](ADOPT.replace("NEWNAME", name).replace("OLDNAME", sys.argv[3])))


if __name__ == "__main__":
    main()
