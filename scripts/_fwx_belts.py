"""Read only: the rocket district's three corridor belts on one wheel, per stretch of 20 tiles, what lies on each lane. Usage: _fwx_belts.py SURFACE"""
import sys

import wheel_rocket as wr
from _game import tools

surf = sys.argv[1]
LUA = ("local s=game.surfaces['%s'] local o={} local P=PATH local n=#P local i=1 while i<=n do local l1,l2={}, {} local missing=0 local j=math.min(i+STEP-1,n) for k=i,j do local e=s.find_entities_filtered{type='transport-belt',position={P[k][1]+0.5,P[k][2]+0.5},radius=0.3}[1] "
       "if e then for _,it in pairs(e.get_transport_line(1).get_contents()) do l1[it.name]=(l1[it.name] or 0)+it.count end for _,it in pairs(e.get_transport_line(2).get_contents()) do l2[it.name]=(l2[it.name] or 0)+it.count end else missing=missing+1 end end "
       "local function f(t) local q={} for k,v in pairs(t) do q[#q+1]=k:sub(1,10)..' '..v end table.sort(q) return table.concat(q,',') end "
       "o[#o+1]=string.format('%%d..%%d (%%d,%%d)->(%%d,%%d) L1[%%s] L2[%%s]%%s',i,j,P[i][1],P[i][2],P[j][1],P[j][2],f(l1),f(l2),missing>0 and (' MISSING '..missing) or '') i=j+1 end rcon.print(table.concat(o,'\\n'))")
step = int(sys.argv[2]) if len(sys.argv) > 2 else 40
for name, path in (("IN1", wr.poly(wr.IN1)), ("IN2", wr.poly(wr.IN2)), ("OUT", wr.poly(wr.OUT))):
    print("==", name, len(path), "tiles")
    print(tools["run_lua"]((LUA % surf).replace("PATH", "{" + ",".join("{%d,%d}" % t for t in path) + "}").replace("STEP", str(step))))
