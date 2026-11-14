"""Read only: power on a platform: panels, accumulators and their charge, the biggest users by prototype maximum. Usage: _fwx_power.py SURFACE"""
import sys

from _game import tools

surf = sys.argv[1]
LUA = ("local s=game.surfaces['%s'] local acc=s.find_entities_filtered{type='accumulator'} local e,cap=0,0 for _,a in pairs(acc) do e=e+a.energy cap=cap+a.electric_buffer_size end "
       "local pan=s.find_entities_filtered{type='solar-panel'} local pw=0 for _,p in pairs(pan) do pw=pw+p.energy_generated_last_tick*60 end "
       "local st=acc[1] and acc[1].electric_network_statistics local o={} if st then local tin,tout=0,0 "
       "for n,_ in pairs(st.input_counts) do local v=st.get_flow_count{name=n,category='input',precision_index=defines.flow_precision_index.one_minute} tin=tin+v o[#o+1]={n,v} end "
       "for n,_ in pairs(st.output_counts) do tout=tout+st.get_flow_count{name=n,category='output',precision_index=defines.flow_precision_index.one_minute} end "
       "table.sort(o,function(a,b) return a[2]>b[2] end) local t={} for i=1,math.min(12,#o) do t[#t+1]=o[i][1]..' '..string.format('%%.1f',o[i][2]*60/1e6)..' MW' end "
       "rcon.print(string.format('panels %%d now %%.1f MW (solar x%%.2f), accumulators %%d holding %%.0f of %%.0f MJ (%%.0f%%%%), used %%.1f MW, made %%.1f MW over the last minute | %%s',#pan,pw/1e6,s.solar_power_multiplier,#acc,e/1e6,cap/1e6,100*e/cap,tin*60/1e6,tout*60/1e6,table.concat(t,', '))) else rcon.print('no accumulators') end") % surf
print(tools["run_lua"](LUA))
