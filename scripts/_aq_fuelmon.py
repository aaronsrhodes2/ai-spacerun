"""Fuel works monitor: fuel made/used per min, ice chest, network ice and fuel, plant states. _aq_fuelmon.py [rounds] [real seconds between]"""
import sys, time
from _game import tools
L = tools["run_lua"]
LUA = ("local s=game.surfaces.aquilo local function st(e) for a,v in pairs(defines.entity_status) do if v==e.status then return a end end return '?' end local f=game.forces.player local fi=f.get_item_production_statistics(s) "
       "local n=s.find_entities_filtered{name='roboport'}[1].logistic_network local ch=s.find_entities_filtered{name='passive-provider-chest',position={25.5,-3.5},radius=0.4}[1] local fc=s.find_entities_filtered{name='passive-provider-chest',position={32.5,-0.5},radius=0.4}[1] "
       "local pj=s.find_entities_filtered{name='pumpjack',position={35.5,-2.5},radius=0.5}[1] local sp=s.find_entities_filtered{name='chemical-plant',position={28.5,-3.5},radius=0.5}[1] local fp=s.find_entities_filtered{name='chemical-plant',position={32.5,-3.5},radius=0.5}[1] "
       "local tw=s.find_entities_filtered{name='heating-tower',position={22.5,-15.5},radius=1}[1] "
       "rcon.print(game.tick..' '..fi.get_input_count('solid-fuel')..' '..fi.get_output_count('solid-fuel')..' icechest='..ch.get_inventory(defines.inventory.chest).get_item_count()..' fuelchest='..fc.get_inventory(defines.inventory.chest).get_item_count()..' netice='..n.get_item_count('ice')..' netfuel='..n.get_item_count('solid-fuel')..' pj='..st(pj)..' sep='..st(sp)..' fuelplant='..st(fp)..' tower='..st(tw)..' T='..math.floor(tw.temperature))")
rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 3
gap = float(sys.argv[2]) if len(sys.argv) > 2 else 20
prev = None
for _ in range(rounds):
    p = L(LUA).split()
    t, made, used = int(p[0]), int(p[1]), int(p[2])
    if prev:
        dt = (t - prev[0]) / 60
        print("%-6.0fs made %.0f/min used %.0f/min | %s" % (dt, (made - prev[1]) / dt * 60, (used - prev[2]) / dt * 60, " ".join(p[3:])))
    else:
        print(" ".join(p[3:]))
    prev = (t, made, used)
    time.sleep(gap)
