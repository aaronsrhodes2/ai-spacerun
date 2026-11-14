"""Read only: a map of a surface with belt directions as arrows. Usage: _arrow_map.py SURFACE X0 Y0 X1 Y1
^ > v < belts; n e s w underground belts (flow direction); Y splitter; X crusher; C collector; i inserter; F furnace; M assembler; H hub; B cargo bay; # other."""
import sys

from _game import tools

surf = sys.argv[1]
x0, y0, x1, y1 = (int(v) for v in sys.argv[2:6])
lua = ("local s=game.surfaces['%s'] local A={[0]='^',[4]='>',[8]='v',[12]='<'} local U={[0]='n',[4]='e',[8]='s',[12]='w'} local rows={} "
       "local T={crusher='X',['asteroid-collector']='C',inserter='i',furnace='F',['assembling-machine']='M',['space-platform-hub']='H',['cargo-bay']='B',splitter='Y',['solar-panel']='s',accumulator='a'} "
       "for y=%d,%d do local r={} for x=%d,%d do local t=s.get_tile(x,y) local c=' ' if t.valid and t.name~='empty-space' and t.name~='out-of-map' then c='.' end "
       "for _,e in pairs(s.find_entities_filtered{area={{x+0.1,y+0.1},{x+0.9,y+0.9}}}) do if e.type=='transport-belt' then c=A[e.direction] elseif e.type=='underground-belt' then c=U[e.direction] elseif e.type~='entity-ghost' and e.type~='tile-ghost' then c=T[e.type] or '#' end end r[#r+1]=c end "
       "rows[#rows+1]=string.format('%%4d ',y)..table.concat(r) end rcon.print(table.concat(rows,'|'))") % (surf, y0, y1, x0, x1)
print("     " + "".join(str(abs(x) // 10 % 10) if x % 10 == 0 else " " for x in range(x0, x1 + 1)))
print(tools["run_lua"](lua).replace("|", "\n"))
