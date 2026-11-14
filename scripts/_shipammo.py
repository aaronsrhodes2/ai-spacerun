"""Turret-by-turret ammunition, inserters with filters and status, and belt contents on one platform surface, to compare ships.
Usage: _shipammo.py platform-23"""
import sys

from _game import tools

LUA = """
local s=game.surfaces['%s'] local o={} local st={} for k,v in pairs(defines.entity_status) do st[v]=k end
local t={} for _,e in pairs(s.find_entities_filtered{type='ammo-turret'}) do t[#t+1]=e.position.x..','..e.position.y..'='..e.get_inventory(defines.inventory.turret_ammo).get_item_count()..'/'..e.quality.name:sub(1,2)..'/'..(st[e.status] or '?') end o[#o+1]='turrets '..table.concat(t,' ')
local i={} for _,e in pairs(s.find_entities_filtered{type='inserter'}) do local fs={} for k=1,e.filter_slot_count do local f=e.get_filter(k) if f then fs[#fs+1]=f.name end end
local cb=e.get_control_behavior() local cond='' if cb and cb.circuit_enable_disable then local c=cb.circuit_condition cond=' if '..tostring(c.first_signal and c.first_signal.name)..c.comparator..tostring(c.constant) end
i[#i+1]=e.position.x..','..e.position.y..' d'..e.direction..' '..(st[e.status] or '?')..' ['..table.concat(fs,',')..']'..cond..(e.use_filters and '' or ' nofilter')..' wires '..((e.get_wire_connector(defines.wire_connector_id.circuit_red,false) and e.get_wire_connector(defines.wire_connector_id.circuit_red,false).connection_count or 0)+(e.get_wire_connector(defines.wire_connector_id.circuit_green,false) and e.get_wire_connector(defines.wire_connector_id.circuit_green,false).connection_count or 0)) end
table.sort(i) o[#o+1]='inserters '..#i..'\\n '..table.concat(i,'\\n ')
local b={} local nb=0 for _,e in pairs(s.find_entities_filtered{type={'transport-belt','underground-belt','splitter'}}) do nb=nb+1 for l=1,e.get_max_transport_line_index() do for _,it in pairs(e.get_transport_line(l).get_contents()) do b[it.name]=(b[it.name] or 0)+it.count end end end
local bb={} for k,v in pairs(b) do bb[#bb+1]=k..':'..v end o[#o+1]='belts '..nb..' hold '..table.concat(bb,' ')
rcon.print(table.concat(o,'\\n'))
"""
print(tools["run_lua"](" ".join((LUA % sys.argv[1]).split())))
