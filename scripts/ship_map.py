#!/usr/bin/env python3
"""ASCII map of a space platform (entities as letters) for planning builds on it.
Usage: ship_map.py "Fulgora-Aquilo 2 Shuttle" [x0 y0 x1 y1]"""
import sys

from _game import tools

GLYPH = {"transport-belt": "b", "express-transport-belt": "B", "express-underground-belt": "U", "underground-belt": "u", "fast-inserter": "i", "inserter": "i",
         "asteroid-collector": "C", "laser-turret": "L", "rocket-turret": "R", "accumulator": "a", "solar-panel": "s", "space-platform-hub": "H",
         "assembling-machine-3": "M", "chemical-plant": "P", "medium-electric-pole": "p", "substation": "p", "thruster": "T", "storage-tank": "K", "pipe": "-",
         "pipe-to-ground": "-", "crusher": "X", "splitter": "y", "express-splitter": "y", "pump": "-", "radar": "r"}


def main():
    name = sys.argv[1]
    x0, y0, x1, y1 = (int(v) for v in sys.argv[2:6]) if len(sys.argv) >= 6 else (-34, -26, 34, 16)
    g = ",".join("['%s']='%s'" % (k, v) for k, v in GLYPH.items())
    lua = ("local p for _,q in pairs(game.forces.player.platforms) do if q.name:find('%s',1,true) then p=q end end local s=p.surface local g={%s} local rows={} "
           "for y=%d,%d do local r={} for x=%d,%d do local t=s.get_tile(x,y) local c=' ' if t.valid and t.name~='empty-space' and t.name~='out-of-map' then c='.' end "
           "for _,e in pairs(s.find_entities_filtered{area={{x+0.01,y+0.01},{x+0.99,y+0.99}}}) do if e.type~='tile-ghost' and e.type~='entity-ghost' then c=g[e.name] or '?' end end r[#r+1]=c end "
           "rows[#rows+1]=string.format('%%4d ',y)..table.concat(r) end rcon.print(table.concat(rows,'|'))") % (name, g, y0, y1, x0, x1)
    print(tools["run_lua"](lua).replace("|", "\n"))


if __name__ == "__main__":
    main()
