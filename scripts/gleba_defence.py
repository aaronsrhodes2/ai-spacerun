import json,sys
from _game import tools
R={"quality":"rare"}
e=[{"name":"tesla-turret","x":x,"y":y,"params":R} for x,y in ((104,-2),(112,-2),(131,4),(54,10),(110,-2+0))][:4]
e+=[{"name":"laser-turret","x":x,"y":y,"params":R} for x,y in ((67,0),(119,23),(131,40),(-144,-108),(190,104))]
print(tools["place_entities"](json.dumps(e),surface="gleba",dry_run="--apply" not in sys.argv)[:600])
print(tools["run_lua"]("local f=game.forces.player rcon.print('tesla recipe '..tostring(f.recipes['tesla-turret'].enabled)..' wall '..tostring(f.recipes['stone-wall'].enabled)..' enemies within 150 of core '..game.surfaces.gleba.count_entities_filtered{force='enemy',position={95,10},radius=150})"))
