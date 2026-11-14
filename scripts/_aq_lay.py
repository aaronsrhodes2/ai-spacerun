#!/usr/bin/env python3
"""Lay ice platforms on a fixed list of the Captain's ghost tiles, paying one platform from the works' chests/assemblers for each (cheap
polling, no map fetch). _aq_lay.py tiles.json [seconds]. The list is written by `aquilo_cryo.py brine` (aquilo_brine_water.json)."""
import json
import sys
import time

from _game import tools

tiles = json.load(open(sys.argv[1]))
secs = int(sys.argv[2]) if len(sys.argv) > 2 else 100
lst = ",".join("{%d,%d}" % tuple(t) for t in tiles)
LUA = ("local s=game.surfaces.aquilo local src={} for _,e in pairs(s.find_entities_filtered{name={'passive-provider-chest','assembling-machine-3'},area={{-15,-32},{20,-26}}}) do "
       "src[#src+1]=e.type=='assembling-machine' and e.get_inventory(defines.inventory.crafter_output) or e.get_inventory(defines.inventory.chest) end "
       "local function take() for _,inv in pairs(src) do if inv.remove({name='ice-platform',count=1})==1 then return true end end return false end "
       "local done,left,nog=0,0,0 for _,p in pairs({%s}) do if s.get_tile(p[1],p[2]).name=='ice-platform' or s.get_tile(p[1],p[2]).name=='concrete' then done=done+1 else "
       "local g=s.find_entities_filtered{type='tile-ghost',position={p[1]+0.5,p[2]+0.5},radius=0.3}[1] if not g then nog=nog+1 elseif take() then g.revive{raise_revive=true} done=done+1 else left=left+1 end end end "
       "rcon.print(done..' '..left..' '..nog)" % lst)
end = time.time() + secs
while time.time() < end:
    done, left, nog = tools["run_lua"](LUA).split()
    if left == "0":
        break
    time.sleep(1.5)
print("laid", done, "of", len(tiles), "waiting", left, "no ghost", nog)
