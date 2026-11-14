"""Read only: the export line's feed belt by stretch (per lane), the two hub inserters and the deciders' signals. Usage: _vw_feed.py [samples]"""
import sys
import time

import wheel_export_vulcanus as wx
from _game import tools

wx.layout()
pts = ",".join("{%s,%s}" % p for p in wx.feed)
LUA = ("local s=game.surfaces['platform-17'] local o={} local P={%s} local acc={{},{}} local nb=0 for i,p in ipairs(P) do local e=s.find_entities_filtered{type='transport-belt',position={p[1],p[2]},radius=0.3}[1] "
       "if e then nb=nb+1 for l=1,2 do for _,it in pairs(e.get_transport_line(l).get_contents()) do acc[l][it.name]=(acc[l][it.name] or 0)+it.count end end end "
       "if i%%28==0 or i==#P then local t={} for l=1,2 do local q={} for k,v in pairs(acc[l]) do q[#q+1]=k:sub(1,6)..' '..v end table.sort(q) t[#t+1]='L'..l..'['..table.concat(q,', ')..']' end o[#o+1]=string.format('%%3d (%%6.1f,%%5.1f) ',i,p[1],p[2])..table.concat(t,' ') acc={{},{}} nb=0 end end "
       "local function sn(e) for n,x in pairs(defines.entity_status) do if x==e.status then return n end end return '?' end "
       "for k,y in pairs{A=-0.5,B=-1.5} do local i=s.find_entities_filtered{type='inserter',position={-4.5,y},radius=0.3}[1] local sg={} for _,q in pairs(i.get_signals(defines.wire_connector_id.circuit_red) or {}) do sg[#sg+1]=q.signal.name..'='..q.count end "
       "o[#o+1]='inserter '..k..' '..sn(i)..' holds '..(i.held_stack.valid_for_read and (i.held_stack.name..' x'..i.held_stack.count) or '-')..' signals '..table.concat(sg,' ') end "
       "for k,x in pairs{A=-9.5,B=-11.5} do local d=s.find_entities_filtered{type='decider-combinator',position={x,-2},radius=0.6}[1] local sg={} for _,q in pairs(d.get_signals(defines.wire_connector_id.combinator_input_red) or {}) do sg[#sg+1]=q.signal.name..'='..q.count end o[#o+1]='deficits '..k..': '..table.concat(sg,' ') end "
       "rcon.print(table.concat(o,'\\n'))" % pts)
for i in range(int(sys.argv[1]) if len(sys.argv) > 1 else 1):
    print(tools["run_lua"](LUA))
    time.sleep(3)
