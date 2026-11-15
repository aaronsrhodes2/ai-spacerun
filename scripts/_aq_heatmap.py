"""Heat map of Aquilo: _aq_heatmap.py x0 y0 x1 y1. Heat pipe = digit (temperature/100), T tower, R reactor, X exchanger, G steam turbine, M melter chem plant,
+ other entity, . free tile (snow/concrete), x non-buildable tile, p ice platform, i ice."""
import sys
from _game import tools
LUA = ("local s=game.surfaces.aquilo local rows={} local ok={['snow-crests']=1,['snow-flat']=1,['snow-lumpy']=1,['snow-patchy']=1,['frozen-concrete']=1,['concrete']=1,['refined-concrete']=1,['dust-flat']=1,['dust-crests']=1,['dust-lumpy']=1,['dust-patchy']=1} "
       "for y=%d,%d do local r={} for x=%d,%d do local tn=s.get_tile(x,y).name local c=ok[tn] and '.' or (tn:find('ice%%-platform') and 'p' or (tn:find('ice') and 'i' or 'x')) "
       "for _,e in pairs(s.find_entities_filtered{area={{x+0.05,y+0.05},{x+0.95,y+0.95}}}) do if e.type=='heat-pipe' then c=tostring(math.min(9,math.floor(e.temperature/100))) break elseif e.name=='heating-tower' then c='T' break elseif e.name=='nuclear-reactor' then c='R' break "
       "elseif e.name=='heat-exchanger' then c='X' break elseif e.name=='steam-turbine' then c='G' break elseif e.type=='tile-ghost' then if c=='x' then c=',' end elseif e.type=='resource' then c='r' elseif e.type=='simple-entity' or e.type=='tree' then c='*' elseif e.type~='logistic-robot' and e.type~='construction-robot' and e.type~='entity-ghost' then c='+' break end end "
       "r[#r+1]=c end rows[#rows+1]=table.concat(r) end rcon.print(table.concat(rows,'|'))")
x0, y0, x1, y1 = [int(v) for v in sys.argv[1:5]]
rows = []
for ya in range(y0, y1 + 1, 30):
    rows += tools["run_lua"](LUA % (ya, min(y1, ya + 29), x0, x1)).strip().split("|")
print("     " + "".join(str(abs(x) // 10 % 10) if x % 10 == 0 else " " for x in range(x0, x1 + 1)))
for j, r in enumerate(rows):
    print("%4d %s" % (y0 + j, r))
