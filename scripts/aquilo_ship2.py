#!/usr/bin/env python3
"""Fulgora-Aquilo 2 Shuttle (the Captain, 2026-11-13: the first Aquilo shuttle was destroyed by asteroids; "you're going to have to redesign it").
The first ship defended itself with guns and rockets it made on board, from carbon and iron it was short of; big and huge asteroids on this
route (2,000 hp, flat physical resistance) shrug off bullets, and with the rockets gone nothing was left. This one has NO ammunition at all:
  hull      scripts/aquilo_shuttle.py with LASER set: the same spine of seven cargo bays (325 hub slots), two collectors, thruster fuel and
            oxidizer plants, metallic crusher that reprocesses when ore is full, carbonic and oxide crushers, valve, rear block of 4 thrusters
  defence   14 rocket turrets on the ammunition belt (2 on the nose, six a flank; they fire at medium, big and huge only) and 26 laser turrets outside
            them for the small asteroids (the wheels' own defence); rockets are made on board and capped at 800 in the hub
  power     64 epic solar panels (four columns a side, eight rows) and 40 accumulators (20 MJ each at epic): 800 MJ stored for bursts
  gone      the magazine line and the gun turrets (bullets do nothing here)
  cargo     hub room for 100 fuel cells (2 slots), robots and the rest of the Aquilo supply (scripts/aquilo_supply.py asks for it)
Schedule (`route`): at Fulgora wait for fuel and oxidizer (40,000 on one tank of three), 1,500 carbon, 1,500 iron ore, 150 rockets and 20 fuel cells aboard, at least 30 seconds; at
Aquilo leave after 90 seconds once fuel and oxidizer are back above 15,000. It never idles in Aquilo orbit.
Hub requests (`requests`): only what Aquilo lacks: 100 fuel cells, 50 construction and 20 logistic robots, 500 ice, all from the Fulgora pad by rocket. (What
the first ship carried, processing units, holmium, superconductors, concrete, stays on Aquilo's pad.) A hub exports what it holds but does not request:
the cargo has to be in the request or it goes back to the pad within half a minute.
Steps: check | create | build [--apply] | config | rename | requests | load | route | status
Usage: aquilo_ship2.py check | create | build [--apply] | config | rename | requests | load | route | status"""
import sys

import aquilo_shuttle as A
from _game import tools

A.LASER = True
A.NAME = "Fulgora-Aquilo 2 Shuttle"
A.PLANET = "fulgora"
ICON = "[virtual-signal=signal-rightwards-leftwards-arrow] "
# Fluids are read from ONE tank of three (green wire): 40,000 there is about 120,000 on board. Aquilo's orbit has no chunks: the ship carries
# carbon and iron ore (2 of each make 75 fuel or oxidizer) and refuels there until each tank reads 15,000 (45,000 on board). Item conditions on the hub count DOUBLE
# (contents on both wires): 40 fuel cells is 20 aboard. There is no timeout: a ship that left with too little fuel would be stranded.
ROUTE = ("local p for _,q in pairs(game.forces.player.platforms) do if q.name:sub(-#'NAME')=='NAME' then p=q end end local function c(t,n,k) return {type='circuit',compare_type='and',condition={first_signal={type=t,name=n},comparator='>=',constant=k}} end "
         "p.schedule={current=CUR,records={{station='fulgora',wait_conditions={c('fluid','thruster-fuel',40000),c('fluid','thruster-oxidizer',40000),c('item','carbon',3000),c('item','iron-ore',3000),c('item','rocket',300),c('item','uranium-fuel-cell',40),{type='time',compare_type='and',ticks=1800}}},"
         "{station='aquilo',wait_conditions={{type='time',compare_type='and',ticks=5400},c('fluid','thruster-fuel',15000),c('fluid','thruster-oxidizer',15000)}}}} p.paused=PAUSED "
         "rcon.print('schedule fulgora <-> aquilo set for '..p.name..', paused='..tostring(p.paused))")
REQ = ("local f=game.forces.player local p for _,q in pairs(f.platforms) do if q.name:sub(-#'NAME')=='NAME' then p=q end end local pt for _,q in pairs(p.hub.get_logistic_point()) do if q.mode==defines.logistic_mode.requester then pt=q end end local sec=nil for _,x in pairs(pt.sections) do if x.is_manual then sec=sec or x end end sec=sec or pt.add_section() "
       "for i=#sec.filters+8,1,-1 do pcall(function() sec.clear_slot(i) end) end for i,it in pairs{{'uranium-fuel-cell',100},{'construction-robot',50},{'logistic-robot',20},{'ice',500}} do sec.set_slot(i,{value={type='item',name=it[1],quality='normal'},min=it[2],max=it[2],import_from='fulgora'}) end "
       "local t={} for _,fl in pairs(sec.filters) do if fl.value then t[#t+1]=fl.value.name..' '..fl.min end end rcon.print('ship requests: '..table.concat(t,', '))")
LOAD = ("local f=game.forces.player local p for _,q in pairs(f.platforms) do if q.name:sub(-#'NAME')=='NAME' then p=q end end local pad=game.surfaces.fulgora.find_entities_filtered{type='cargo-landing-pad'}[1] local pi=pad.get_inventory(defines.inventory.cargo_landing_pad_main) local hi=p.hub.get_inventory(defines.inventory.hub_main) local o={} "
        "for _,w in pairs{{'uranium-fuel-cell',100},{'construction-robot',50},{'logistic-robot',20}} do local got=0 for _,it in pairs(pi.get_contents()) do if it.name==w[1] and got<w[2] then local n=pi.remove{name=it.name,count=math.min(it.count,w[2]-got),quality=it.quality} got=got+hi.insert{name=it.name,count=n,quality=it.quality} end end o[#o+1]=w[1]..' '..got end "
        "rcon.print('moved from the Fulgora pad onto the ship: '..table.concat(o,', '))")


def main():
    step = sys.argv[1]
    if step == "rename":
        print(tools["run_lua"]("for _,p in pairs(game.forces.player.platforms) do if p.name=='%s' then p.name='%s'..p.name rcon.print('renamed '..p.name) end end" % (A.NAME, ICON)))
    elif step == "route":
        cur = tools["run_lua"]("for _,p in pairs(game.forces.player.platforms) do if p.name:sub(-#'%s')=='%s' then rcon.print(p.space_location and p.space_location.name or 'none') end end" % (A.NAME, A.NAME)).strip()
        go = "--go" in sys.argv
        print(tools["run_lua"](ROUTE.replace("NAME", A.NAME).replace("CUR", "2" if cur == "aquilo" else "1").replace("PAUSED", "false" if go else "true")))
    elif step == "requests":
        print(tools["run_lua"](REQ.replace("NAME", A.NAME)))
    elif step == "load":
        print(tools["run_lua"](LOAD.replace("NAME", A.NAME)))
    else:
        return A.main()


if __name__ == "__main__":
    main()
