"""Read only: what the hub's west inserters really take a second. Item ids on the last 26 tiles of the west product belt at two moments;
the ids that are gone went into the hub. Usage: _vw_intake.py [seconds]"""
import json
import sys
import time

from _game import tools

gap = float(sys.argv[1]) if len(sys.argv) > 1 else 3
LUA = ("local s=game.surfaces['platform-17'] local ids={} local n=0 local function add(x,y) local b=s.find_entities_filtered{type='transport-belt',position={x+0.5,y+0.5},radius=0.3}[1] if b then for l=1,2 do for _,d in pairs(b.get_transport_line(l).get_detailed_contents()) do ids[#ids+1]=d.unique_id end end end end "
       "for x=-31,-6 do add(x,-4) end add(-6,-3) rcon.print(helpers.table_to_json({tick=game.tick,ids=ids}))")
for rep in range(3):
    a = json.loads(tools["run_lua"](LUA))
    time.sleep(gap)
    b = json.loads(tools["run_lua"](LUA))
    sa, sb = set(a["ids"] or []), set(b["ids"] or [])
    secs = (b["tick"] - a["tick"]) / 60
    print("%.1f game seconds: on the belt %d -> %d, taken into the hub %d = %.1f a second, arrived %d = %.1f a second" % (secs, len(sa), len(sb), len(sa - sb), len(sa - sb) / secs, len(sb - sa), len(sb - sa) / secs))
