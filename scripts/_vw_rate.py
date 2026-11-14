"""Read only: crafts a game minute of every machine of the export line over a window (seconds, default 60), with what each holds at the end,
and the hub's product count at both ends. Usage: _vw_rate.py [seconds]"""
import json
import sys
import time

import wheel_export_vulcanus as wx
from _game import tools

wx.layout()
secs = int(sys.argv[1]) if len(sys.argv) > 1 else 60
pts = ",".join("{%s,%s,'%s'}" % (x, y, r) for x, y, r, d in wx.recipes)
SNAP = ("local s=game.surfaces['platform-17'] local t={tick=game.tick,hub=s.platform.hub.get_inventory(defines.inventory.hub_main).get_item_count('%s')} for i,q in ipairs({%s}) do local m=s.find_entities_filtered{type='assembling-machine',position={q[1],q[2]},radius=0.5}[1] "
        "local h={} for _,id in pairs{defines.inventory.crafter_input,defines.inventory.crafter_output} do local inv=m.get_inventory(id) if inv then for _,it in pairs(inv.get_contents()) do h[#h+1]=it.name..' '..it.count end end end for k,v in pairs(m.get_fluid_contents()) do h[#h+1]=k..' '..math.floor(v) end "
        "local st='?' for n,v in pairs(defines.entity_status) do if v==m.status then st=n end end t[i..' '..q[3]]={m.products_finished,st,table.concat(h,', '),m.crafting_speed,m.productivity_bonus} end rcon.print(helpers.table_to_json(t))" % (wx.PRODUCT, pts))
a = json.loads(tools["run_lua"](SNAP))
time.sleep(secs)
b = json.loads(tools["run_lua"](SNAP))
mins = (b["tick"] - a["tick"]) / 3600
print("game minutes %.2f; %s in the hub %d -> %d (%.1f a minute)" % (mins, wx.PRODUCT, a["hub"], b["hub"], (b["hub"] - a["hub"]) / mins))
for k in sorted(b, key=lambda s: int(s.split(" ")[0]) if s[0].isdigit() else 99):
    if k in ("tick", "hub"):
        continue
    print("  %-34s %6.1f crafts a minute  speed %.2f prod +%.0f%%  %-26s %s" % (k, (b[k][0] - a[k][0]) / mins, b[k][3], b[k][4] * 100, b[k][1], b[k][2]))
