"""Read only: one line every 30 s for N minutes: foundations made on the Nauvis Wheel, wheel hub stock, triangle tiles. Usage: _wf_watch.py [minutes]"""
import sys, time
from _game import tools
LUA = ("local s=game.surfaces['platform-13'] local made=0 local st={} for _,m in pairs(s.find_entities_filtered{name='assembling-machine-3',area={{3,55},{8,66}}}) do made=made+m.products_finished end "
       "local steel=0 for _,m in pairs(s.find_entities_filtered{name='foundry',area={{8,52},{13,69}}}) do local r=m.get_recipe() if r and r.name=='casting-steel' then steel=steel+m.products_finished end end "
       "local inv=s.platform.hub.get_inventory(defines.inventory.hub_main) local p for _,q in pairs(game.forces.player.platforms) do if q.name:find('Nauvis Triangle 1',1,true) then p=q end end local ts=p.surface "
       "local a=0 for _,e in pairs(s.find_entities_filtered{type='accumulator'}) do a=a+e.energy end "
       "rcon.print(game.tick..' '..made..' '..inv.get_item_count('space-platform-foundation')..' '..#ts.find_tiles_filtered{name='space-platform-foundation'}..' '..p.hub.get_inventory(defines.inventory.hub_main).get_item_count('space-platform-foundation')..' '..inv.get_item_count('iron-ore')..' '..inv.get_item_count('copper-ore')..' '..steel..' '..math.floor(a/1e6))")
n = int(float(sys.argv[1]) * 2) if len(sys.argv) > 1 else 3
first = None
print("min(game) made wheel_hub tri_tiles tri_hub iron_ore copper_ore steel_crafts accu_MJ | made/min tiles/min")
for i in range(n + 1):
    v = [int(x) for x in tools["run_lua"](LUA).split()]
    if first is None:
        first = v
    dt = (v[0] - first[0]) / 3600
    print("%.1f" % dt, *v[1:], "|", ("%.1f %.1f" % ((v[1] - first[1]) / dt, (v[3] - first[3]) / dt)) if dt > 0 else "", flush=True)
    if i < n:
        time.sleep(30)
