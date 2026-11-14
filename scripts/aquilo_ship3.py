#!/usr/bin/env python3
"""Fulgora-Aquilo 3 Shuttle: the rocket ship (the Captain, 2026-11-14, after two ships were lost: make the rockets on the ground, carry
thousands, stock repair packs). Hull and defence as ship 2 (scripts/aquilo_shuttle.py with LASER: 14 rocket turrets, 26 lasers for the
fragments), with one change: the HUB feeds the ammunition belt. A bulk inserter at (4,1) takes rockets out of the hub onto a short belt that
dives under the fuel pipe and the water riser (7,1 -> 11,1) and side-loads onto the ammunition belt at (12,1), upstream of every turret
inserter. The rocket assembler aboard stays as a backup (it works only below 800 rockets in the hub).
Rockets come from scripts/rocket_line.py (Nauvis) and are moved into the hub by script (`rocket_line.py ship "Aquilo 3" N`).
Test flights carry no cells and no robots: `requests` asks only for repair packs, ice, carbon, iron ore and rockets.
Steps: check | create | build [--apply] | config | rename | requests | route [--go] | status | watch [minutes]
Usage: aquilo_ship3.py check | create | build [--apply] | config | rename | requests | route [--go] | status | watch [minutes]"""
import sys
import time

import aquilo_shuttle as A
from _game import tools

A.LASER = True
A.NAME = "Fulgora-Aquilo 4 Shuttle"
A.PLANET = "fulgora"
ICON = "[virtual-signal=signal-rightwards-leftwards-arrow] "
FIND = "local p for _,q in pairs(game.forces.player.platforms) do if q.name:sub(-#'NAME')=='NAME' then p=q end end "
_layout = A.layout


def layout():
    r = _layout()
    A.ins(4, 1, A.W, ["explosive-rocket"], name="bulk-inserter")          # hub -> belt
    A.belts([(5, 1), (6, 1), (7, 1, "in"), (11, 1, "out")], A.E)                     # under the fuel pipe (8) and the water riser (10)
    # Ship 3 died 2.5 minutes out (2026-11-14): 26 lasers (3.8 MW each while firing; the panels give about 7 MW at Fulgora, 4.4 at Aquilo)
    # emptied the accumulators on the fragments, every inserter stopped, and the turrets ran dry with 2,095 rockets in the hub.
    # Ship 4 (the Captain's universal armament): 6 lasers (small only), 10 gun turrets with uranium rounds (medium only), 14 rocket turrets
    # with explosive rockets (big, then medium). All ammunition comes from the hub; nothing is made aboard (the rocket assembler has no inserters).
    def gone(e):
        if e["name"] == "laser-turret":
            return not (e["x"] in (-18, 19) and e["y"] in (-18, -12, -6))
        return (e["name"] == "solar-panel" and e["x"] == 14.5 and e["y"] == 1.5) or (e["name"] == "fast-inserter" and (e["x"], e["y"]) in ((8.5, 4.5), (4.5, 3.5)))
    for e in [e for e in A.ents if gone(e)]:
        A.ents.remove(e)
        h = {"laser-turret": 1, "solar-panel": 1.5}.get(e["name"], .5)
        for x in range(int(e["x"] - h), int(e["x"] + h)):
            for y in range(int(e["y"] - h), int(e["y"] + h)):
                A.occ.pop((x, y), None)
    A.cfg[:] = [c for c in A.cfg if (c[0], c[1]) != (4.5, 3.5)]
    A.gates[:] = [g for g in A.gates if (g[0], g[1]) != (4.5, 3.5)]
    A.ins(4, 0, A.W, ["uranium-rounds-magazine"], name="bulk-inserter")   # hub -> magazines
    A.belts([(5, 0), (6, 0), (7, 0, "in"), (13, 0, "out"), (14, 0), (14, -1), (13, -1)], A.W)    # under the trunk, back onto it from the east: east lane
    for x, ix in ((-2, -2), (0, 1)):                                                 # nose guns
        A.put("gun-turret", x, -23, 2, 2)
        A.ins(ix, -21, A.S)
    for y in (-18, -15, -12, -9):                                                    # guns inside the belt, both flanks
        A.put("gun-turret", -11, y, 2, 2)
        A.ins(-12, y, A.W)
        A.put("gun-turret", 9, y, 2, 2)
        A.ins(11, y, A.E)
    keep = {(x, y) for (x, y) in A.tiles if -24 <= y <= 25 and (x, y) not in A.holes}
    A.tiles.clear()
    A.tiles.update(keep)
    r["entities"] = len(A.ents)
    return r


A.layout = layout
# Fluids are read from ONE tank of three (green wire). Item conditions read the hub on red: the real count (SKILL: the hub trash rule).
ROUTE = (FIND + "local function c(t,n,k) return {type='circuit',compare_type='and',condition={first_signal={type=t,name=n},comparator='>=',constant=k}} end "
         "p.schedule={current=CUR,records={{station='fulgora',wait_conditions={c('fluid','thruster-fuel',40000),c('fluid','thruster-oxidizer',40000),c('item','carbon',3000),c('item','iron-ore',3000),c('item','explosive-rocket',ROCKETS),c('item','uranium-rounds-magazine',MAGS),c('item','repair-pack',400),{type='time',compare_type='and',ticks=1800}}},"
         "{station='aquilo',wait_conditions={{type='time',compare_type='and',ticks=5400},c('fluid','thruster-fuel',15000),c('fluid','thruster-oxidizer',15000)}}}} p.paused=PAUSED if p.space_location then p.space_location=p.space_location.name end "
         "rcon.print('schedule fulgora <-> aquilo set for '..p.name..', paused='..tostring(p.paused)..', state '..p.state)")
REQ = (FIND + "local pt for _,q in pairs(p.hub.get_logistic_point()) do if q.mode==defines.logistic_mode.requester then pt=q end end local sec=nil for _,x in pairs(pt.sections) do if x.is_manual then sec=sec or x end end sec=sec or pt.add_section() "
       "for i=#sec.filters+8,1,-1 do pcall(function() sec.clear_slot(i) end) end for i,it in pairs{{'repair-pack',300,1000},{'ice',500,3000},{'carbon',3500,5000},{'iron-ore',3500,5000},{'explosive-rocket',0,40000},{'uranium-rounds-magazine',0,40000}} do "
       "sec.set_slot(i,{value={type='item',name=it[1],quality='normal'},min=it[2],max=it[3],import_from='fulgora',request_from=((it[1]=='carbon' or it[1]=='iron-ore' or it[1]=='ice') and 'platforms' or 'planet')}) end "
       "local t={} for _,fl in pairs(sec.filters) do if fl.value then t[#t+1]=fl.value.name..' '..fl.min..'..'..(fl.max or '-') end end rcon.print('ship requests: '..table.concat(t,', '))")
LASERS = (FIND + "local s=p.surface local n=0 for _,t in pairs(s.find_entities_filtered{name='laser-turret'}) do local i=0 for _,k in pairs{'metallic','carbonic','oxide','promethium'} do i=i+1 t.set_priority_target(i,'small-'..k..'-asteroid') end t.ignore_unprioritised_targets=true n=n+1 end rcon.print('lasers limited to small asteroids '..n)")
TARGETS = (FIND + "local s=p.surface local o={} local function set(name,list) local n=0 for _,t in pairs(s.find_entities_filtered{name=name}) do for i=1,12 do pcall(function() t.set_priority_target(i,nil) end) end "
           "for i,a in pairs(list) do t.set_priority_target(i,a) end t.ignore_unprioritised_targets=true n=n+1 end local t=s.find_entities_filtered{name=name}[1] local r={} for _,x in pairs(t.priority_targets) do r[#r+1]=x.name end o[#o+1]=name..' x'..n..' ignore_others='..tostring(t.ignore_unprioritised_targets)..': '..table.concat(r,',') end "
           "set('laser-turret',{'small-metallic-asteroid','small-carbonic-asteroid','small-oxide-asteroid','small-promethium-asteroid'}) set('gun-turret',{'medium-metallic-asteroid','medium-carbonic-asteroid','medium-oxide-asteroid','medium-promethium-asteroid'}) "
           "set('rocket-turret',{'big-oxide-asteroid','big-metallic-asteroid','big-carbonic-asteroid','big-promethium-asteroid','medium-oxide-asteroid','medium-metallic-asteroid','medium-carbonic-asteroid'}) "
           "for _,q in pairs({{4.5,1.5,'explosive-rocket'},{4.5,0.5,'uranium-rounds-magazine'}}) do local i=s.find_entities_filtered{type='inserter',position={q[1],q[2]},radius=0.3}[1] i.use_filters=true i.inserter_filter_mode='whitelist' for k=1,i.filter_slot_count do i.set_filter(k,nil) end i.set_filter(1,q[3]) end rcon.print(table.concat(o,' ;; '))")
WATCH = (FIND + "if not p then rcon.print('GONE') return end local s=p.surface local fl={} for _,t in pairs(s.find_entities_filtered{name='storage-tank'}) do for k,v in pairs(t.get_fluid_contents()) do fl[k]=(fl[k] or 0)+v end end "
         "local dmg,low=0,0 for _,e in pairs(s.find_entities_filtered{force='player'}) do if e.health and e.max_health and e.health<e.max_health then dmg=dmg+1 if e.health<e.max_health*0.5 then low=low+1 end end end "
         "local inv=p.hub.get_inventory(defines.inventory.hub_main) local tr=0 local tmin=999 for _,t in pairs(s.find_entities_filtered{name='rocket-turret'}) do local c=t.get_item_count('explosive-rocket') tr=tr+c if c<tmin then tmin=c end end "
         "local a,cap=0,0 for _,e in pairs(s.find_entities_filtered{name='accumulator'}) do a=a+e.energy cap=cap+e.electric_buffer_size end local gm,gmin=0,999 for _,t in pairs(s.find_entities_filtered{name='gun-turret'}) do local c=t.get_item_count('uranium-rounds-magazine') gm=gm+c if c<gmin then gmin=c end end local ast={} for _,a in pairs(s.find_entities_filtered{type='asteroid'}) do local k=a.name:match('^(%a+)') ast[k]=(ast[k] or 0)+1 end local at={} for k,v in pairs(ast) do at[#at+1]=k..' '..v end "
         "rcon.print((p.space_location and p.space_location.name or 'flight')..' st'..p.state..' | entities '..s.count_entities_filtered{force='player'}..' ghosts '..s.count_entities_filtered{type='entity-ghost'}..' damaged '..dmg..' below half '..low"
         "..' | rockets hub '..inv.get_item_count('explosive-rocket')..' turrets '..tr..' (least '..tmin..') | repair '..inv.get_item_count('repair-pack')..' | fuel '..math.floor(fl['thruster-fuel'] or 0)..' ox '..math.floor(fl['thruster-oxidizer'] or 0)"
         "..' | carbon '..inv.get_item_count('carbon')..' ore '..inv.get_item_count('iron-ore')..' ice '..inv.get_item_count('ice')..' | speed '..string.format('%.0f',p.speed or 0)..' | asteroids '..table.concat(at,', ')..' | tick '..game.tick)")


def lua(src):
    return tools["run_lua"](src.replace("NAME", A.NAME)).strip()


def main():
    step = sys.argv[1]
    if step == "rename":
        print(tools["run_lua"]("for _,p in pairs(game.forces.player.platforms) do if p.name=='%s' then p.name='%s'..p.name rcon.print('renamed '..p.name) end end" % (A.NAME, ICON)))
    elif step == "route":
        cur = lua(FIND + "rcon.print(p.space_location and p.space_location.name or 'none')")
        # counts wanted ABOARD; the hub shows its contents on both wires and a wait condition adds them, so the condition gets twice the number
        rockets = next((a.split("=")[1] for a in sys.argv if a.startswith("--rockets=")), "3000")
        mags = next((a.split("=")[1] for a in sys.argv if a.startswith("--mags=")), "3000")
        print(lua(ROUTE.replace("CUR", "2" if cur == "aquilo" else "1").replace("PAUSED", "false" if "--go" in sys.argv else "true").replace("ROCKETS", str(2 * int(rockets))).replace("MAGS", str(2 * int(mags)))))
    elif step == "requests":
        print(lua(REQ))
    elif step == "targets":
        print(lua(TARGETS).replace(" ;; ", chr(10)))
    elif step == "watch":
        minutes = float(sys.argv[2]) if len(sys.argv) > 2 else 1.5
        every = int(sys.argv[3]) if len(sys.argv) > 3 else 20
        end = time.time() + minutes * 60
        while time.time() < end:
            print(time.strftime("%H:%M:%S"), lua(WATCH), flush=True)
            time.sleep(every)
    else:
        r = A.main()
        if step in ("config",) or (step == "build" and "--apply" in sys.argv):
            print(lua(TARGETS).replace(" ;; ", chr(10)))
        return r


if __name__ == "__main__":
    main()
