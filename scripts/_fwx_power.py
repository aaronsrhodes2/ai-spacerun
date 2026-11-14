"""Read only: power on a platform: panels, accumulators and their charge, the biggest users by prototype maximum. Usage: _fwx_power.py SURFACE"""
import sys

from _game import tools

surf = sys.argv[1]
LUA = ("local s=game.surfaces['%s'] local acc=s.find_entities_filtered{type='accumulator'} local e,cap=0,0 for _,a in pairs(acc) do e=e+a.energy cap=cap+a.electric_buffer_size end "
       "local pan=s.find_entities_filtered{type='solar-panel'} local pw=0 for _,p in pairs(pan) do pw=pw+0 end "
       "rcon.print(string.format('panels %%d (solar x%%.2f), accumulators %%d holding %%.0f of %%.0f MJ (%%.0f%%%%)',#pan,s.solar_power_multiplier,#acc,e/1e6,cap/1e6,100*e/cap))") % surf
print(tools["run_lua"](LUA))
