#!/usr/bin/env python3
"""Stock from Vulcanus to the Nauvis pad (the Captain, 2026-11-14: "make the Vulcanus Wheel's low density structure stock available for
pickup"; the coordinator added tungsten carbide for speed-module-3).

Design: request sections on the three Nauvis-Vulcanus shuttles, nothing on the wheel. Proven 2026-11-14 (see SKILL.md).
  LOAD   a section 'lds-<platform index>': item min = max = AMOUNT, request_from 'platforms', import_from 'vulcanus'. `import_from` makes a
         request live only while the ship orbits that planet. At Vulcanus the ship pulls the LDS from the Vulcanus Wheel hub in orbit
         (the hub has providing_to_other_platforms = true). Tungsten carbide has no platform source: a section 'tc-<index>' with
         request_from 'planet' loads it from the Vulcanus landing pad, and the pad gets a section 'tc-pickup' (min 1,000) so robots
         carry it from the network's chests to the pad.
  DROP   an UNREQUESTED item does NOT leave a hub (tested: 500 LDS rode Vulcanus-Nauvis-Vulcanus twice). Only TRASH is sent down. So a
         section 'lds-drop-<index>': item min = max = 0, import_from 'nauvis' puts the cargo into hub_trash at Nauvis and the pod sends it to the pad
         (500 LDS were on the pad 2 game-seconds after arrival, ship empty, trash empty again).
  WAIT   the Nauvis stop gets 'item count of ITEM < 1' (and) + 'time 9000 ticks' (or): the ship stays until the trash has gone down.
Per-ship amounts are below. The ship cycle is about 40,000 ticks (11 minutes, most of it waiting at Vulcanus for metallurgic packs).
Steps: status | apply [--lds N] | off.   Usage: lds_pickup.py apply"""
import sys

from _game import tools

LDS = "low-density-structure"
TC = "tungsten-carbide"
# ship -> {item: (amount, request_from)}
JOBS = {
    "Nauvis-Vulcanus 1 Shuttle": {TC: (1000, "planet")},
    "Nauvis-Vulcanus 3 Shuttle": {LDS: (150, "platforms")},     # V2 left alone: the Nauvis pad is nearly full (see SKILL.md), LDS only on one ship
}
PAD_TC = 1000      # the Vulcanus pad asks for this much carbide from its network
SHORT = {LDS: "lds", TC: "tc"}

LUA = ("local function plat(n) for _,p in pairs(game.forces.player.platforms) do if p.name:find(n,1,true) then return p end end end "
       "local function req(p) for _,q in pairs(p.hub.get_logistic_point()) do if q.mode==defines.logistic_mode.requester then return q end end end "
       "local function drop(pt,g) for i=pt.sections_count,1,-1 do if pt.sections[i].group==g then pt.remove_section(i) end end end "
       "local function job(p,item,short,amt,rf) local pt=req(p) drop(pt,short..'-'..p.index) drop(pt,short..'-drop-'..p.index) if not amt then return end "
       "local s=pt.add_section(short..'-'..p.index) s.set_slot(1,{value={type='item',name=item,quality='normal'},min=amt,max=amt,import_from='vulcanus',request_from=rf}) "
       "local d=pt.add_section(short..'-drop-'..p.index) d.set_slot(1,{value={type='item',name=item,quality='normal'},min=0,max=0,import_from='nauvis'}) "
       "local sch=p.schedule local w=sch.records[1].wait_conditions local have=false for _,c in pairs(w) do if c.type=='item_count' and c.condition.first_signal.name==item then have=true end end "
       "if not have then w[#w+1]={type='item_count',compare_type='and',condition={first_signal={type='item',name=item},comparator='<',constant=1}} w[#w+1]={type='time',compare_type='or',ticks=9000} p.schedule=sch end end "
       "local o={} %s rcon.print(table.concat(o,' ;; '))")


def run(body):
    return tools["run_lua"](LUA % body).replace(" ;; ", "\n")


def apply(jobs, pad_tc):
    body = ""
    for ship, items in jobs.items():
        for item, (amt, rf) in items.items():
            body += "job(plat('%s'),'%s','%s',%s,'%s') " % (ship, item, SHORT[item], amt if amt else "nil", rf)
    body += ("do local pd=game.surfaces.vulcanus.find_entities_filtered{type='cargo-landing-pad'}[1] local pp for _,q in pairs(pd.get_logistic_point()) do if q.mode==defines.logistic_mode.requester then pp=q end end "
             "drop(pp,'tc-pickup') %s end " % ("" if not pad_tc else "local s=pp.add_section('tc-pickup') s.set_slot(1,{value={type='item',name='tungsten-carbide',quality='normal'},min=%d})" % pad_tc))
    print(run(body))


def status():
    body = ""
    for ship in JOBS:
        body += ("do local p=plat('%s') local pt=req(p) local t={} for _,s in pairs(pt.sections) do if s.group and (s.group:find('^lds') or s.group:find('^tc')) then local f=s.filters[1] t[#t+1]=s.group..' '..f.min..'/'..f.max..' '..tostring(f.request_from) end end "
                 "local inv=p.hub.get_inventory(defines.inventory.hub_main) o[#o+1]=p.name:sub(-22)..' @'..tostring(p.space_location and p.space_location.name)..' st '..p.state..' | '..table.concat(t,', ')..' | aboard LDS '..inv.get_item_count('%s')..' TC '..inv.get_item_count('%s')..' | free slots '..inv.count_empty_stacks()..' | trash '..#p.hub.get_inventory(defines.inventory.hub_trash).get_contents() end " % (ship, LDS, TC))
    body += ("do local w=plat('Vulcanus Wheel') o[#o+1]='wheel provides '..tostring(w.hub.providing_to_other_platforms)..' LDS '..w.hub.get_inventory(defines.inventory.hub_main).get_item_count('%s') end "
             "do local v=game.surfaces.vulcanus local pd=v.find_entities_filtered{type='cargo-landing-pad'}[1] local vn=v.find_logistic_network_by_position(pd.position,'player') "
             "local n=game.surfaces.nauvis local nn=n.find_logistic_network_by_position({-216,-224},'player') "
             "o[#o+1]='Vulcanus network TC '..vn.get_item_count('%s')..' pad TC '..pd.get_inventory(defines.inventory.cargo_landing_pad_main).get_item_count('%s')..' | Nauvis network LDS '..nn.get_item_count('%s')..' TC '..nn.get_item_count('%s') end"
             % (LDS, TC, TC, LDS, TC))
    print(run(body))


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "status"
    if step == "apply":
        jobs = JOBS
        if "--lds" in sys.argv:
            n = int(sys.argv[sys.argv.index("--lds") + 1])
            jobs = {s: {i: ((n if i == LDS else a), rf) for i, (a, rf) in it.items()} for s, it in JOBS.items()}
        apply(jobs, PAD_TC)
    elif step == "off":
        apply({s: {i: (None, rf) for i, (a, rf) in it.items()} for s, it in JOBS.items()}, None)
    status()
