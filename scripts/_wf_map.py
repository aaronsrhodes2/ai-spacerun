"""Read only: map of a box on the Nauvis Wheel with belt arrows. Usage: _wf_map.py x0 y0 x1 y1"""
import sys
from _game import tools
g = {"express-underground-belt": "U", "fast-inserter": "i", "bulk-inserter": "I", "long-handed-inserter": "l", "space-platform-hub": "H", "assembling-machine-3": "M", "cargo-bay": "#", "crusher": "X", "electric-furnace": "F", "foundry": "Y", "small-lamp": "*", "decider-combinator": "d", "arithmetic-combinator": "d", "constant-combinator": "d", "express-splitter": "y", "solar-panel": "s", "accumulator": "a", "pipe": "-", "pipe-to-ground": "=", "storage-tank": "K", "chemical-plant": "P", "asteroid-collector": "C"}
gl = ",".join("['%s']='%s'" % kv for kv in g.items())
x0, y0, x1, y1 = (int(v) for v in sys.argv[1:5])
lua = ("local s=game.surfaces['platform-13'] local g={%s} local ar={[0]='^',[4]='>',[8]='v',[12]='<'} local rows={} for y=%d,%d do local r={} for x=%d,%d do local t=s.get_tile(x,y) local c=' ' if t.valid and t.name~='empty-space' and t.name~='out-of-map' then c='.' end "
       "for _,e in pairs(s.find_entities_filtered{area={{x+0.2,y+0.2},{x+0.8,y+0.8}}}) do if e.type~='tile-ghost' and e.type~='entity-ghost' then if e.type=='transport-belt' then c=ar[e.direction] or 'B' else c=g[e.name] or '?' end end end r[#r+1]=c end rows[#rows+1]=string.format('%%4d ',y)..table.concat(r) end rcon.print(table.concat(rows,'|'))") % (gl, y0, y1, x0, x1)
print("x0 =", x0)
print(tools["run_lua"](lua).replace("|", "\n"))
