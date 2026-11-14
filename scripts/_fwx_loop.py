"""Read only: the district loop tile by tile, lane 2 (and lane 1) contents as letters, twice a second apart. Usage: _fwx_loop.py SURFACE"""
import sys
import time

import wheel_rocket as wr
from _game import tools

wr.layout()
surf = sys.argv[1]
LUA = ("local s=game.surfaces['%s'] local o={} for _,p in pairs(RING) do local e=s.find_entities_filtered{type='transport-belt',position={p[1]+0.5,p[2]+0.5},radius=0.3}[1] local t='' "
       "if e then for l=1,2 do local c=e.get_transport_line(l).get_contents() local n=0 local k='' for _,it in pairs(c) do n=n+it.count k=k..it.name:sub(1,2) end t=t..n..k..(l==1 and '/' or '') end else t='MISSING' end o[#o+1]=t end rcon.print(table.concat(o,' '))") % surf
for i in range(2):
    print(tools["run_lua"](LUA.replace("RING", wr.lua_list(wr.loop_tiles))))
    time.sleep(1)
print("order: top row west to east (15..40,17), east column south, bottom row east to west, west column north")
