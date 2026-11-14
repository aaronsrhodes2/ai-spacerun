"""One-off trial of the tap fix on one wheel (the lasting version lives in wheel_export_fulgora.py). Usage: _fwx_tap.py SURFACE dry|apply"""
import json
import sys

import wheel_rocket as wr
from _game import tools

surf, apply = sys.argv[1], sys.argv[2] == "apply"
print(tools["run_lua"]("local s=game.surfaces['%s'] local t=s.get_tile(-65,2) rcon.print('tile -65,2 '..t.name..' entities '..s.count_entities_filtered{area={{-65,2},{-64,3}}})" % surf))
r = tools["place_entities"](json.dumps([{"name": "express-transport-belt", "x": -64.5, "y": 2.5, "direction": 12, "params": {"quality": "epic"}}]), surface=surf, dry_run=not apply)
print(r)
if apply:
    print(tools["run_lua"]("local s=game.surfaces['%s'] local b=s.find_entities_filtered{type='transport-belt',position={-64.5,1.5},radius=0.3}[1] b.direction=defines.direction.south "
                           "local c=s.find_entities_filtered{type='transport-belt',position={-64.5,2.5},radius=0.3}[1] rcon.print('stub now '..b.direction..', new belt '..tostring(c and c.direction))" % surf))
    path = wr.poly(wr.IN1)
    MOVE = ("local s=game.surfaces['%s'] local hub=s.platform.hub local moved,tohub=0,0 for _,p in pairs(PATH) do local e=s.find_entities_filtered{type='transport-belt',position={p[1]+0.5,p[2]+0.5},radius=0.3}[1] if e then "
            "local a,b=e.get_transport_line(1),e.get_transport_line(2) local n=a.get_item_count('carbonic-asteroid-chunk') if n>0 then a.remove_item{name='carbonic-asteroid-chunk',count=n} "
            "for k=1,n do local ok=false for _,q in pairs{0.1,0.35,0.6,0.85} do if not ok and b.can_insert_at(q) then ok=b.insert_at(q,{name='carbonic-asteroid-chunk',count=1}) end end if ok then moved=moved+1 else tohub=tohub+hub.insert{name='carbonic-asteroid-chunk',count=1} end end end end end "
            "rcon.print('carbonic chunks moved to lane 2: '..moved..', to the hub: '..tohub)") % surf
    print(tools["run_lua"](MOVE.replace("PATH", "{" + ",".join("{%d,%d}" % t for t in path) + "}")))
