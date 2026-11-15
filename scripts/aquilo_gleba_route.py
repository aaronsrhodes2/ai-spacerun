#!/usr/bin/env python3
"""Cryogenic science from Aquilo to the Gleba labs (the Captain, 2026-11-14: "get Aquilo science flowing to Gleba").
The chain, link by link (`status` prints each):
  1 ground -> orbit  Aquilo silo (-5.5,3.5), orbital requests: a platform in Aquilo orbit that asks for cryogenic packs with
                     import_from='aquilo' makes the silo lift them (robots load the rocket from the network). The silo needs 50
                     processing units + 50 low density structure + 50 rocket fuel a rocket (`aquilo_silo.py arm` after LDS comes).
  2 orbit -> Gleba   `Gleba-Aquilo 1 Shuttle`: a twin of the proven `Fulgora-Aquilo 4 Shuttle` (scripts/aquilo_ship3.py, explosive-rocket
                     fit, hold control), built by the same code with PLANET gleba. Ammunition is pre-loaded from the ground, never made aboard.
  3 Gleba side       the landing pad (142,24) and the nine lab chests (x 121.5/133.5, y 24.5..39.5) get a cryogenic-science-pack request
                     (the pad 1,200, each chest 200), as the other packs have.
Steps (dry run unless --apply):
  status                 every link, plus the ship, the pad, the chests, the queue
  build [--apply]        create the platform at Gleba, lay the hull (aquilo_ship3 layout), config, targets, hold control, requests, fit explosive
  gleba-side [--apply] [--off]   cryogenic requests on the Gleba pad and lab chests (read back)
  cryo-request N D       ship's pack request: min N, minimum_delivery_count D (keep D at or under the packs the Aquilo network holds, or the silo never launches)
  stage [--apply]        Aquilo side before the flight: prints packs on the pad (a pad request does NOT make robots haul packs there; the silo loads from the red chest by robots) / in chests, silo rocket ready
  ammo [--apply]         bar the five explosive-rocket cell chests at 4 slots (400 each) and re-add the rocket request the cells lost; with --apply only
  load R M               move R explosive rockets and M uranium-round magazines from the Nauvis ammunition chests into the ship's hub
  route [--go] [--rockets=N] [--mags=N] [--packs=N] [--reserve=N] [--wait=TICKS]   (--reserve: the ship leaves Aquilo once its explosive rockets fall to N, packs or not: it burns ~9 a minute parked and the return needs ~800; default 900)   the schedule (paused unless --go)
  lds on|off             ask the Gleba Wheel for low density structure (150) to carry to the Aquilo pad (the silo needs it)
  verify                 the checks that must be green before a flight
Usage: aquilo_gleba_route.py status | build [--apply] | gleba-side [--apply] | ammo [--apply] | load R M | route [--go] | lds on|off | verify"""
import json
import sys

import aquilo_shuttle as A
import aquilo_ship3 as S
from _game import tools

NAME = "Gleba-Aquilo 1 Shuttle"
A.NAME = NAME
A.PLANET = "gleba"
S.A.NAME = NAME
S.A.PLANET = "gleba"
for _attr in ("REQ", "FIT", "HOLD", "TARGETS"):
    setattr(S, _attr, getattr(S, _attr).replace("'fulgora'", "'gleba'"))
# the gate is carbon/ore >= 3,000 aboard: ask for more than the gate (ship 4 asks 2,000 against a 3,000 gate)
S.REQ = S.REQ.replace("{'carbon',2000,100000}", "{'carbon',3500,100000}").replace("{'iron-ore',2000,100000}", "{'iron-ore',3500,100000}")

PAD_PACKS, CHEST_PACKS = 1200, 200
CHESTS = [(121.5, 24.5), (133.5, 24.5), (121.5, 27.5), (133.5, 27.5), (121.5, 30.5), (133.5, 30.5), (121.5, 33.5), (121.5, 36.5), (121.5, 39.5)]


def run(lua):
    return tools["run_lua"](" ".join(lua.split())).strip()


def lua_find():
    return S.FIND.replace("NAME", NAME)


GLEBA_SIDE = """
local g=game.surfaces.gleba local o={} local mode='MODE'
local function setcryo(e,tag,n) local secs=e.get_logistic_sections() local target
for _,se in pairs(secs.sections) do if se.is_manual then for k=1,se.filters_count do local f=se.get_slot(k) if f and f.value and f.value.name=='metallurgic-science-pack' then target=se end end end end
if not target then o[#o+1]=tag..' NO pack section' return end
local at for k=1,target.filters_count do local f=target.get_slot(k) if f and f.value and f.value.name=='cryogenic-science-pack' then at=k end end
if mode=='off' then if at then target.clear_slot(at) end elseif mode=='on' and not at then target.set_slot(target.filters_count+1,{value={type='item',name='cryogenic-science-pack',quality='normal'},min=n}) end
local r='absent' for k=1,target.filters_count do local f=target.get_slot(k) if f and f.value and f.value.name=='cryogenic-science-pack' then r='min '..f.min..' active '..tostring(target.active) end end o[#o+1]=tag..' '..r end
setcryo(g.find_entities_filtered{type='cargo-landing-pad'}[1],'pad',PADN)
for _,p in pairs(CHESTS) do local c=g.find_entities_filtered{name='requester-chest',position=p,radius=0.3}[1] if c then setcryo(c,'chest '..p[1]..','..p[2],CHESTN) else o[#o+1]='no chest '..p[1]..','..p[2] end end
rcon.print(table.concat(o,'|'))"""

ASK_CRYO = """
local sec for _,x in pairs(p.hub.get_logistic_point()) do if x.mode==defines.logistic_mode.requester then for _,s in pairs(x.sections) do if s.is_manual then sec=sec or s end end end end
local at for k=1,sec.filters_count do local f=sec.get_slot(k) if f and f.value and f.value.name=='cryogenic-science-pack' then at=k end end
sec.set_slot(at or sec.filters_count+1,{value={type='item',name='cryogenic-science-pack',quality='normal'},min=PACKS,max=100000,import_from='aquilo',minimum_delivery_count=DELIV})
local f=sec.get_slot(at or sec.filters_count) rcon.print('cryogenic request min '..tostring(f.min)..' max '..tostring(f.max)..' from '..tostring(f.import_from and f.import_from.name)..' delivery '..tostring(f.minimum_delivery_count))"""

LDS = """
local sec for _,x in pairs(p.hub.get_logistic_point()) do if x.mode==defines.logistic_mode.requester then for _,s in pairs(x.sections) do if s.is_manual then sec=sec or s end end end end
local at for k=1,sec.filters_count do local f=sec.get_slot(k) if f and f.value and f.value.name=='low-density-structure' then at=k end end
if 'MODE'=='off' then if at then sec.clear_slot(at) end else sec.set_slot(at or sec.filters_count+1,{value={type='item',name='low-density-structure',quality='normal'},min=150,max=100000,import_from='gleba',request_from='platforms'}) end
local r='absent' for k=1,sec.filters_count do local f=sec.get_slot(k) if f and f.value and f.value.name=='low-density-structure' then r='min '..f.min..' from '..tostring(f.import_from and f.import_from.name)..' request_from '..tostring(f.request_from) end end rcon.print('LDS request '..r)"""

# Aquilo side staged BEFORE the ship goes (a parked ship burns 100-330 rockets a minute near Aquilo): packs in the network (red chest, as Gleba's), a rocket standing ready in the silo, delivery count at or under the packs held. The silo loads and launches an
# orbital request only when the network holds a whole minimum_delivery_count: 379 packs against a 1,000 delivery never launched (2026-11-14).
STAGE = """
local s=game.surfaces.aquilo local o={} local pad=s.find_entities_filtered{type='cargo-landing-pad'}[1] local inv=pad.get_inventory(defines.inventory.cargo_landing_pad_main)
local at for si,se in pairs(pad.get_logistic_sections().sections) do for k=1,se.filters_count do local f=se.get_slot(k) if f and f.value and f.value.name=='cryogenic-science-pack' then at={se,k} end end end
o[#o+1]='pad request cryo '..(at and at[1].get_slot(at[2]).min or 'none')
local tot=0 for _,c in pairs(s.find_entities_filtered{type={'container','logistic-container'}}) do tot=tot+c.get_item_count('cryogenic-science-pack') end
o[#o+1]='packs on pad '..inv.get_item_count('cryogenic-science-pack')..', in all chests '..tot
local si=s.find_entities_filtered{name='rocket-silo'}[1] o[#o+1]='silo status '..si.status..' rocket ready '..tostring(si.rocket~=nil)..' parts '..si.rocket_parts..' LDS on pad '..inv.get_item_count('low-density-structure')
rcon.print(table.concat(o,'|'))"""

AMMO = """
local s=game.surfaces.nauvis local o={}
local cells={{-322,-99},{-315,-99},{-308,-99},{-322,-90},{-322,-86}}
for _,c in pairs(cells) do local ch=s.find_entities_filtered{name='steel-chest',position={c[1]+6.5,c[2]+1.5},radius=0.4}[1] local inv=ch.get_inventory(defines.inventory.chest) if 'APPLY'=='yes' then inv.set_bar(6) end
local q=s.find_entities_filtered{name='requester-chest',position={c[1]+0.5,c[2]+1.5},radius=0.4}[1] local sec=q.get_logistic_point(defines.logistic_member_index.logistic_container).sections[1]
local has=false for k=1,sec.filters_count do local f=sec.get_slot(k) if f and f.value and f.value.name=='rocket' then has=true end end if not has and 'APPLY'=='yes' then sec.set_slot(sec.filters_count+1,{value={type='item',name='rocket',quality='normal'},min=400}) end
local r={} for k=1,sec.filters_count do local f=sec.get_slot(k) if f and f.value then r[#r+1]=f.value.name..':'..f.min end end
o[#o+1]=c[1]..','..c[2]..' bar '..tostring(inv.get_bar())..' request '..table.concat(r,' ')..' made '..inv.get_item_count('explosive-rocket') end
rcon.print(table.concat(o,'|'))"""

LOAD = """
local s=game.surfaces.nauvis local p for _,q in pairs(game.forces.player.platforms) do if q.name:sub(-#'NAME')=='NAME' then p=q end end local hi=p.hub.get_inventory(defines.inventory.hub_main)
local want={['explosive-rocket']=RN,['uranium-rounds-magazine']=MN} local got={}
local cells={{-322,-99,'explosive-rocket'},{-315,-99,'explosive-rocket'},{-308,-99,'explosive-rocket'},{-322,-90,'explosive-rocket'},{-322,-86,'explosive-rocket'},{-322,-94,'uranium-rounds-magazine'},{-315,-94,'uranium-rounds-magazine'},{-308,-94,'uranium-rounds-magazine'},{-301,-94,'uranium-rounds-magazine'},{-308,-90,'uranium-rounds-magazine'}}
for _,c in pairs(cells) do local k=c[3] local need=want[k]-(got[k] or 0) if need>0 then local ch=s.find_entities_filtered{name='steel-chest',position={c[1]+6.5,c[2]+1.5},radius=0.4}[1] local inv=ch.get_inventory(defines.inventory.chest) local n=math.min(need,inv.get_item_count(k))
if n>0 then local put=hi.insert{name=k,count=n} if put>0 then inv.remove{name=k,count=put} got[k]=(got[k] or 0)+put end end end end
local o={} for k,v in pairs(got) do o[#o+1]=k..' +'..v..' (hub '..hi.get_item_count(k)..')' end rcon.print('moved to '..p.name..': '..table.concat(o,', '))"""

# One wait group per stop: a time wait did NOT hold this ship at Aquilo (it left after ~55 s of a 21,600-tick wait, twice), so an "or time"
# fallback would send it off at once. The hub signal counts cargo already launched, so the gate opens as the rocket lifts; the pod then lands on
# the departing ship (seen: 200 plates arrived 30 s after departure).
ROUTE = """
local function c(t,n,k,cmp,op) return {type='circuit',compare_type=cmp or 'and',condition={first_signal={type=t,name=n},comparator=op or '>=',constant=k}} end
local function tm(k,cmp) return {type='time',compare_type=cmp or 'and',ticks=k} end
local fuel,ox=c('fluid','thruster-fuel',40000),c('fluid','thruster-oxidizer',40000)
p.schedule={current=CUR,records={
{station='gleba',wait_conditions={fuel,ox,c('item','carbon',3000),c('item','iron-ore',3000),c('item','explosive-rocket',RK),c('item','uranium-rounds-magazine',MG),c('item','cryogenic-science-pack',40,'and','<'),tm(1800)}},
{station='aquilo',wait_conditions={c('fluid','thruster-fuel',15000),c('fluid','thruster-oxidizer',15000),c('item','cryogenic-science-pack',PK),c('item','explosive-rocket',RES,'or','<=')}}}}
if 'SIMPLE'=='yes' then p.schedule={current=CUR,records={p.schedule.records[1],{station='aquilo',wait_conditions={c('fluid','thruster-fuel',15000),c('fluid','thruster-oxidizer',15000),TESTGATE}}}} end
p.paused=PAUSED if p.space_location then p.space_location=p.space_location.name end
rcon.print('schedule gleba <-> aquilo set for '..p.name..', paused='..tostring(p.paused)..', state '..p.state)"""


def arg(name, default):
    return next((a.split("=")[1] for a in sys.argv if a.startswith("--%s=" % name)), default)


def status():
    print(run("""
local f=game.forces.player local o={} local p for _,q in pairs(f.platforms) do if q.name:sub(-#'NAME')=='NAME' then p=q end end
o[#o+1]='ship: '..(p and (p.name..' at '..(p.space_location and p.space_location.name or 'transit')..' state '..p.state..' paused '..tostring(p.paused)..' stops '..(p.schedule and #p.schedule.records or 0)) or 'NOT BUILT')
local ap=game.surfaces.aquilo.find_entities_filtered{type='cargo-landing-pad'}[1].get_inventory(defines.inventory.cargo_landing_pad_main)
o[#o+1]='aquilo pad: cryo '..ap.get_item_count('cryogenic-science-pack')..' PU '..ap.get_item_count('processing-unit')..' LDS '..ap.get_item_count('low-density-structure')..' RF '..ap.get_item_count('rocket-fuel')
local gp=game.surfaces.gleba.find_entities_filtered{type='cargo-landing-pad'}[1].get_inventory(defines.inventory.cargo_landing_pad_main) o[#o+1]='gleba pad: cryo '..gp.get_item_count('cryogenic-science-pack')..' free slots '..gp.count_empty_stacks()
local q={} for _,t in pairs(f.research_queue) do q[#q+1]=t.name end o[#o+1]='research queue: '..table.concat(q,',')
local lab=0 for _,l in pairs(game.surfaces.gleba.find_entities_filtered{type='lab'}) do lab=lab+l.get_item_count('cryogenic-science-pack') end o[#o+1]='cryo packs in Gleba labs '..lab
rcon.print(table.concat(o,'|'))""".replace("NAME", NAME)).replace("|", "\n"))
    print(run(GLEBA_SIDE.replace("MODE", "status").replace("PADN", "0").replace("CHESTN", "0").replace("CHESTS", "{" + ",".join("{%s,%s}" % c for c in CHESTS) + "}")).replace("|", "\n"))
    print(tools["run_lua"]("local s=game.surfaces.aquilo local si=s.find_entities_filtered{name='rocket-silo'}[1] local c=si.get_control_behavior() rcon.print('aquilo silo status '..si.status..' transitional '..tostring(si.use_transitional_requests)..' read_mode '..tostring(c and c.read_mode))"))


def main():
    step = sys.argv[1] if len(sys.argv) > 1 else "status"
    apply = "--apply" in sys.argv
    if step == "status":
        status()
    elif step == "gleba-side":
        mode = "off" if "--off" in sys.argv else ("on" if apply else "status")
        lst = "{" + ",".join("{%s,%s}" % c for c in CHESTS) + "}"
        print(run(GLEBA_SIDE.replace("MODE", mode).replace("PADN", str(PAD_PACKS)).replace("CHESTN", str(CHEST_PACKS)).replace("CHESTS", lst)).replace("|", "\n"))
    elif step == "cryo-request":
        print(S.lua(lua_find() + ASK_CRYO.replace("PACKS", sys.argv[2]).replace("DELIV", sys.argv[3])))
    elif step == "stage":
        print(run(STAGE.replace("APPLY", "yes" if apply else "no")).replace("|", chr(10)))
    elif step == "ammo":
        print(run(AMMO.replace("APPLY", "yes" if apply else "no")).replace("|", "\n"))
    elif step == "load":
        print(run(LOAD.replace("NAME", NAME).replace("RN", sys.argv[2]).replace("MN", sys.argv[3]).replace("local s=", "local s=")))
    elif step == "lds":
        print(run(lua_find() + LDS.replace("MODE", sys.argv[2])))
    elif step == "route":
        cur = run(lua_find() + "rcon.print(p.space_location and p.space_location.name or 'none')")
        r = ROUTE.replace("CUR", "2" if cur == "aquilo" else "1").replace("PAUSED", "false" if "--go" in sys.argv else "true")
        r = r.replace("RK", str(2 * int(arg("rockets", 1800)))).replace("MG", str(2 * int(arg("mags", 1500)))).replace("PK", str(2 * int(arg("packs", 400)))).replace("RES", str(2 * int(arg("reserve", 900)))).replace("WAIT", arg("wait", "36000")).replace("SIMPLE", "yes" if "--simple" in sys.argv else "no").replace("TESTGATE", "c('item','iron-plate',190)" if "--testgate" in sys.argv else "tm(%s)" % arg("wait", "36000"))
        print(run(lua_find() + r))
    elif step in ("create", "build", "config", "check", "requests", "hold", "targets", "fit", "watch", "rename"):
        sys.argv[0] = "aquilo_ship3.py"
        if step == "requests":
            print(S.lua(S.REQ))
            print(S.lua(lua_find() + ASK_CRYO.replace("PACKS", arg("packs", "1000")).replace("DELIV", arg("delivery", "1000"))))
            return
        S.main()
        if step == "build" and apply:
            print(S.lua(S.REQ))
            print(S.lua(lua_find() + ASK_CRYO.replace("PACKS", arg("packs", "1000")).replace("DELIV", arg("delivery", "1000"))))
            print(S.lua(S.HOLD.replace("VCAPS", "{" + ",".join("['%s']=%d" % kv for kv in S.VCAPS.items()) + "}")))
    elif step == "verify":
        status()
        print(run(lua_find() + "rcon.print('hub trash '..p.hub.get_inventory(defines.inventory.hub_trash).get_item_count()..' | '..(p.hub.get_inventory(defines.inventory.hub_main).get_item_count('explosive-rocket'))..' explosive rockets, '..p.hub.get_inventory(defines.inventory.hub_main).get_item_count('uranium-rounds-magazine')..' mags')".replace("NAME", NAME)))
        print(S.lua(S.WATCH))
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
