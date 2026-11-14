"""Read only: what lies on the rocket district's three long belts of the Vulcanus Wheel, per lane, by stretch of 60 tiles."""
import sys

import wheel_rocket as wr
from _game import tools

S = sys.argv[1] if len(sys.argv) > 1 else "platform-17"
for nm, path in (("IN1", wr.poly(wr.IN1)), ("IN2", wr.poly(wr.IN2)), ("OUT", wr.poly(wr.OUT))):
    pts = ",".join("{%d,%d}" % p for p in path)
    code = ("local s=game.surfaces['%s'] local o={} local P={%s} local acc={{},{}} local nb=0 for i,p in ipairs(P) do local e=s.find_entities_filtered{type='transport-belt',position={p[1]+0.5,p[2]+0.5},radius=0.3}[1] "
            "if e then nb=nb+1 for l=1,2 do for _,it in pairs(e.get_transport_line(l).get_contents()) do acc[l][it.name]=(acc[l][it.name] or 0)+it.count end end end "
            "if i%%60==0 or i==#P then local t={} for l=1,2 do local q={} for k,v in pairs(acc[l]) do q[#q+1]=k:sub(1,10)..' '..v end table.sort(q) t[#t+1]='L'..l..'['..table.concat(q,', ')..']' end o[#o+1]=i..' ('..p[1]..','..p[2]..') belts '..nb..' '..table.concat(t,' ') acc={{},{}} nb=0 end end rcon.print(table.concat(o,'\\n'))" % (S, pts))
    print("==", nm, len(path))
    print(tools["run_lua"](code))
