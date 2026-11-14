#!/usr/bin/env python3
"""Print a tile map of Aquilo: _aq_grid.py x0 y0 x1 y1. S snow, C concrete, i meltable ice, ~ brash ice, P ice platform, . ocean, # entity of ours,
* iceberg/other simple entity, R resource."""
import sys

from _game import tools

LUA = ("local s=game.surfaces.aquilo local land={['dust-flat']='S',['dust-crests']='S',['dust-lumpy']='S',['dust-patchy']='S',['snow-crests']='S',['snow-flat']='S',['snow-lumpy']='S',['snow-patchy']='S',['frozen-concrete']='C',['concrete']='C',"
       "['refined-concrete']='C',['ice-smooth']='i',['ice-rough']='i',['brash-ice']='~',['ice-platform']='P'} local rows={} for y=%d,%d do local r={} for x=%d,%d do "
       "local c=land[s.get_tile(x,y).name] or '.' local es=s.find_entities_filtered{area={{x+0.05,y+0.05},{x+0.95,y+0.95}}} for _,e in pairs(es) do "
       "if e.type=='tile-ghost' then c=(c=='.' and ',' or c) elseif e.type=='resource' then c='R' elseif e.type=='simple-entity' or e.type=='tree' then c='*' elseif e.type~='logistic-robot' and e.type~='construction-robot' then c='#' break end end "
       "r[#r+1]=c end rows[#rows+1]=table.concat(r) end rcon.print(table.concat(rows,'|'))")


def grid(x0, y0, x1, y1):
    rows = []
    for ya in range(y0, y1 + 1, 40):
        yb = min(y1, ya + 39)
        rows += tools["run_lua"](LUA % (ya, yb, x0, x1)).strip().split("|")
    return rows


if __name__ == "__main__":
    x0, y0, x1, y1 = [int(v) for v in sys.argv[1:5]]
    rows = grid(x0, y0, x1, y1)
    print("     " + "".join(str(abs(x) // 10 % 10) if x % 10 == 0 else " " for x in range(x0, x1 + 1)))
    for j, r in enumerate(rows):
        print("%4d %s" % (y0 + j, r))
