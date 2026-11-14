#!/usr/bin/env python3
"""Space science for Gleba comes from orbit, not from Nauvis' ground (2026-11-14). White Science and the Nauvis Wheel give packs away
(`providing_to_other_platforms`); every Nauvis-Gleba shuttle's own space-science request (one slot, min N, no max so nothing is trashed)
is rewritten with request_from='platforms', import_from='nauvis'. `ground` puts it back to rockets from the planet.
The slot is rewritten in place and read back.
Usage: gleba_space_from_orbit.py orbit|ground|status [N=400] [name part, default Nauvis-Gleba]"""
import sys

from _game import tools

LUA = """
local f=game.forces.player local o={} local mode='%s' local n=%d
for i,p in pairs(f.platforms) do if p.hub and p.name:find('%s',1,true) then local inv=p.hub.get_inventory(defines.inventory.hub_main)
for si,se in pairs(p.hub.get_logistic_sections().sections) do if se.is_manual and (se.group==nil or se.group=='') then for k,fl in pairs(se.filters) do if fl.value and fl.value.name=='space-science-pack' then
if mode=='orbit' then se.set_slot(k,{value={type='item',name='space-science-pack',quality='normal'},min=n,import_from='nauvis',request_from='platforms'})
elseif mode=='ground' then se.set_slot(k,{value={type='item',name='space-science-pack',quality='normal'},min=n,import_from='nauvis'}) end
local r=se.get_slot(k) o[#o+1]='#'..i..' '..(p.space_location and p.space_location.name or 'transit')..' sec'..si..'/'..k..' min '..tostring(r.min)..' max '..tostring(r.max)..' request_from '..tostring(r.request_from)..' aboard '..inv.get_item_count('space-science-pack') end end end end end end
rcon.print(table.concat(o,'|'))
"""
mode = sys.argv[1]
n = int(sys.argv[2]) if len(sys.argv) > 2 else 400
want = sys.argv[3] if len(sys.argv) > 3 else "Nauvis-Gleba"
print(tools["run_lua"](" ".join((LUA % (mode, n, want)).split())).replace("|", "\n"))
