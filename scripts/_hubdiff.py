"""What changes in a hub over N seconds (default 30): contents before and after, and pods in flight. Usage: _hubdiff.py "Nauvis-Gleba 2" [seconds]"""
import json
import sys
import time

from _game import tools

LUA = """
local f=game.forces.player for i,p in pairs(f.platforms) do if p.name:find('%s',1,true) then local t={} for _,it in pairs(p.hub.get_inventory(defines.inventory.hub_main).get_contents()) do t[it.name]=(t[it.name] or 0)+it.count end
t['_tick']=game.tick t['_pods']=p.surface.count_entities_filtered{type='cargo-pod'} rcon.print(helpers.table_to_json(t)) return end end
"""
lua = " ".join((LUA % sys.argv[1]).split())
a = json.loads(tools["run_lua"](lua))
time.sleep(int(sys.argv[2]) if len(sys.argv) > 2 else 30)
b = json.loads(tools["run_lua"](lua))
print("ticks", b["_tick"] - a["_tick"], "pods", a["_pods"], b["_pods"])
for k in sorted(set(a) | set(b)):
    if a.get(k, 0) != b.get(k, 0) and not k.startswith("_"):
        print(" ", k, a.get(k, 0), "->", b.get(k, 0))
