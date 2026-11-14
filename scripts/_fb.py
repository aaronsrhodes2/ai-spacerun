"""Read only: fluidboxes of the entities at given positions. Usage: _fb.py SURFACE x,y [x,y ...]"""
import sys

from _game import tools

for pos in sys.argv[2:]:
    x, y = pos.split(",")
    print(tools["run_lua"](
        "local s=game.surfaces['%s'] local e=s.find_entities_filtered{position={%s,%s},radius=0.6,type={'assembling-machine','furnace','storage-tank','pipe'}}[1] local o={e.name..' dir '..e.direction..' at '..e.position.x..','..e.position.y} local fb=e.fluidbox "
        "for i=1,#fb do local f=fb[i] local c={} for _,pc in pairs(fb.get_pipe_connections(i)) do c[#c+1]=pc.flow_direction..' at '..pc.position.x..','..pc.position.y..' -> '..pc.target_position.x..','..pc.target_position.y..(pc.target and (' joined to '..pc.target.owner.name) or ' open') end "
        "o[#o+1]=i..': '..(f and (f.name..' '..math.floor(f.amount)) or 'empty')..' ['..table.concat(c,' / ')..']' end rcon.print(table.concat(o,' ; '))" % (sys.argv[1], x, y)).replace(" ; ", "\n  "))
