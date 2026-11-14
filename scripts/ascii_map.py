#!/usr/bin/env python3
"""A character map of a piece of any surface: one character a tile, read straight off the game (the Captain, 2026-11-13: teach the skill
the trick). Use it before designing anything into built-up ground: free tiles, holes in a platform deck, water, belts in the way.
  ' '  no ground (open space on a platform)      '.'  free ground        '~'  water
  H heating tower   P electric pole   b belt, underground belt, splitter   i inserter   p pipe, pipe to ground   T storage tank
  c crusher   m assembling machine, furnace, chemical plant, other machine   L lab   C chest or cargo bay   s solar panel   a accumulator
  t turret   r rail   R roboport   O offshore pump   h heat pipe   x heat exchanger   g turbine or generator   k combinator
  ^ cliff   * tree or plant   o rock   # anything else   (robots and items on the ground are ignored)
The header rows give the x of every tenth column; each line starts with its y. A tile is the square from (x, y) to (x+1, y+1).
At most 120 x 80 tiles a call (an RCON reply is limited); ask for a larger area in pieces.
Usage: ascii_map.py SURFACE X0 Y0 X1 Y1      e.g. ascii_map.py gleba 112 6 162 56   or   ascii_map.py platform-14 -14 -10 14 9"""
import sys

from _game import tools

LUA = ("local s=game.surfaces['SURF'] local T={['heating-tower']='H',['offshore-pump']='O',['heat-pipe']='h',['heat-exchanger']='x',crusher='c',['cargo-bay']='C',['solar-panel']='s',accumulator='a',roboport='R'} "
       "local Y={['electric-pole']='P',['transport-belt']='b',['underground-belt']='b',splitter='b',inserter='i',pipe='p',['pipe-to-ground']='p',['storage-tank']='T',['assembling-machine']='m',furnace='m',lab='L',"
       "container='C',['logistic-container']='C',['ammo-turret']='t',['electric-turret']='t',['fluid-turret']='t',['straight-rail']='r',['curved-rail-a']='r',['curved-rail-b']='r',['half-diagonal-rail']='r',"
       "generator='g',['decider-combinator']='k',['arithmetic-combinator']='k',['constant-combinator']='k',cliff='^',tree='*',plant='*',['simple-entity']='o',['space-platform-hub']='C',['cargo-landing-pad']='C',['asteroid-collector']='m',thruster='m'} "
       "local skip={['logistic-robot']=1,['construction-robot']=1,['item-entity']=1,corpse=1,fish=1,['entity-ghost']=1,character=1} local rows={} "
       "for y=Y0,Y1 do local r={} for x=X0,X1 do local t=s.get_tile(x,y) local ch='.' if not t.valid or t.name=='empty-space' or t.name=='out-of-map' then ch=' ' elseif t.collides_with('water_tile') then ch='~' end "
       "for _,e in pairs(s.find_entities_filtered{area={{x+0.1,y+0.1},{x+0.9,y+0.9}},limit=4}) do if not skip[e.type] then ch=T[e.name] or Y[e.type] or '#' end end r[#r+1]=ch end rows[#rows+1]=table.concat(r) end rcon.print(table.concat(rows,'|'))")


def ascii_map(surface, x0, y0, x1, y1):
    assert (x1 - x0 + 1) <= 120 and (y1 - y0 + 1) <= 80, "at most 120 x 80 tiles a call"
    code = LUA.replace("SURF", surface).replace("X0", str(x0)).replace("X1", str(x1)).replace("Y0", str(y0)).replace("Y1", str(y1))
    rows = tools["run_lua"](code).rstrip("\n").split("|")
    tens = "".join(("%d" % (abs(x) // 10 % 10)) if x % 10 == 0 else " " for x in range(x0, x1 + 1))
    sign = "".join(("-" if x < 0 else "+") if x % 10 == 0 else " " for x in range(x0, x1 + 1))
    return "\n".join(["     " + sign, "     " + tens] + ["%4d %s" % (y0 + i, r) for i, r in enumerate(rows)])


if __name__ == "__main__":
    if len(sys.argv) != 6:
        sys.exit(__doc__)
    print(ascii_map(sys.argv[1], *[int(v) for v in sys.argv[2:6]]))
