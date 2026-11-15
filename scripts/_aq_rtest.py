"""Reactor demand-following test: put ONE uranium fuel cell (from the Aquilo pad) in the idle reactor at 17.5,-16.5 and log its burn against the heat drawn."""
import sys, time
from _game import tools
L = tools["run_lua"]
if "--insert" in sys.argv:
    print(L("local s=game.surfaces.aquilo local pad=s.find_entities_filtered{type='cargo-landing-pad'}[1] local pi=pad.get_inventory(defines.inventory.cargo_landing_pad_main) local rx=s.find_entities_filtered{name='nuclear-reactor'}[1] "
            "if rx.get_fuel_inventory().get_item_count()>0 or rx.burner.remaining_burning_fuel>0 then rcon.print('reactor not empty') return end local n=pi.remove{name='uranium-fuel-cell',count=1} rx.get_fuel_inventory().insert{name='uranium-fuel-cell',count=n} rcon.print('moved '..n..' cell pad->reactor')"))
for i in range(int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 8):
    print(L("local s=game.surfaces.aquilo local rx=s.find_entities_filtered{name='nuclear-reactor'}[1] local t1=s.find_entities_filtered{name='heating-tower',position={22.5,-15.5},radius=1}[1] local t2=s.find_entities_filtered{name='heating-tower',position={-18.5,-21.5},radius=1}[1] "
            "rcon.print(game.tick..' rx T='..string.format('%.1f',rx.temperature)..' left='..string.format('%.0f',rx.burner.remaining_burning_fuel/1e6)..'MJ inv='..rx.get_fuel_inventory().get_item_count()..' bonus='..rx.neighbour_bonus..' | tw1 T='..string.format('%.1f',t1.temperature)..' left='..string.format('%.0f',t1.burner.remaining_burning_fuel/1e6)..' inv='..t1.get_fuel_inventory().get_item_count()..' | tw2 T='..string.format('%.1f',t2.temperature)..' inv='..t2.get_fuel_inventory().get_item_count())"))
    time.sleep(10)
