"""Read only: the export line's feed, tile by tile from index A to B: lane counts and direction. Usage: _vw_tiles.py A B"""
import sys

import wheel_export_vulcanus as wx
from _game import tools

wx.layout()
a, b = int(sys.argv[1]), int(sys.argv[2])
pts = ",".join("{%s,%s}" % p for p in wx.feed[a:b])
print(tools["run_lua"]("local s=game.surfaces['platform-17'] local o={} for i,p in ipairs({%s}) do local e=s.find_entities_filtered{type={'transport-belt','underground-belt'},position={p[1],p[2]},radius=0.3}[1] "
                       "if e then local t={} for l=1,2 do local q={} for _,it in pairs(e.get_transport_line(l).get_contents()) do q[#q+1]=it.name:sub(1,4)..it.count end t[#t+1]=table.concat(q,'+') end o[#o+1]=string.format('%%d:(%%.0f,%%.0f)%%s d%%d [%%s|%%s]',i+%d-1,p[1]-0.5,p[2]-0.5,e.type=='underground-belt' and 'U' or '',e.direction,t[1],t[2]) else o[#o+1]='MISSING '..p[1]..','..p[2] end end rcon.print(table.concat(o,'  '))" % (pts, a)))
