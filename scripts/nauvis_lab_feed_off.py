#!/usr/bin/env python3
"""The Nauvis labs are gone (the Captain, 2026-11-14: all labs on Gleba). The six requester chests that fed them (x -72.5 and -6.5,
y 36.5/42.5/48.5) asked for 100 of every science pack and would keep hoarding. This switches their request sections off (not deleted,
chests left standing) and prints what each holds. `on` switches them back.
Usage: nauvis_lab_feed_off.py off|on|status"""
import sys

from _game import tools

LUA = """
local n=game.surfaces.nauvis local o={} local mode='%s' local tot={}
for _,x in pairs({-72.5,-6.5}) do for _,y in pairs({36.5,42.5,48.5}) do local e=n.find_entities_filtered{position={x,y},name='requester-chest'}[1] if e then
local act={} for _,se in pairs(e.get_logistic_sections().sections) do if mode=='off' then se.active=false elseif mode=='on' then se.active=true end act[#act+1]=tostring(se.active) end
local c={} for _,it in pairs(e.get_inventory(defines.inventory.chest).get_contents()) do c[#c+1]=(it.name:gsub('%%-science%%-pack',''))..':'..it.count tot[it.name]=(tot[it.name] or 0)+it.count end
o[#o+1]='chest '..x..','..y..' sections active ['..table.concat(act,',')..'] holds '..table.concat(c,' ') else o[#o+1]='no chest at '..x..','..y end end end
local t={} for k,v in pairs(tot) do t[#t+1]=(k:gsub('%%-science%%-pack',''))..':'..v end o[#o+1]='total '..table.concat(t,' ')
o[#o+1]='labs left on nauvis '..n.count_entities_filtered{type='lab'}..' marked '..n.count_entities_filtered{type='lab',to_be_deconstructed=true}
rcon.print(table.concat(o,'|'))
"""
print(tools["run_lua"](" ".join((LUA % sys.argv[1]).split())).replace("|", "\n"))
