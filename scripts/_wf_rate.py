"""Read only: rates of the Nauvis Wheel foundation works over N seconds (default 90). Usage: _wf_rate.py [seconds]"""
import sys, time
from _game import tools
L = ("local s=game.surfaces['platform-13'] local fe,st=0,0 for _,m in pairs(s.find_entities_filtered{name='foundry',area={{8,52},{18,81}}}) do local r=m.get_recipe().name local n=m.products_finished if r=='iron-ore-melting' then fe=fe+n elseif r=='casting-steel' then st=st+n end end "
     "local am=0 for _,m in pairs(s.find_entities_filtered{name='assembling-machine-3',area={{3,55},{8,78}}}) do am=am+m.products_finished end local inv=s.platform.hub.get_inventory(defines.inventory.hub_main) "
     "local p for _,q in pairs(game.forces.player.platforms) do if q.name:find('Nauvis Triangle 1',1,true) then p=q end end local a=0 for _,e in pairs(s.find_entities_filtered{type='accumulator'}) do a=a+e.energy end "
     "rcon.print(game.tick..' '..fe..' '..st..' '..am..' '..inv.get_item_count('iron-ore')..' '..inv.get_item_count('copper-ore')..' '..inv.get_item_count('space-platform-foundation')..' '..#p.surface.find_tiles_filtered{name='space-platform-foundation'}..' '..math.floor(a/1e6))")
a = [int(x) for x in tools["run_lua"](L).split()]
time.sleep(float(sys.argv[1]) if len(sys.argv) > 1 else 90)
b = [int(x) for x in tools["run_lua"](L).split()]
m = (b[0] - a[0]) / 3600
print("game minutes %.2f | foundations/min %.1f | steel/min %.0f | iron ore melted/min %.0f | hub iron ore %d -> %d (%+.0f/min), copper ore %d -> %d | wheel hub foundation %d -> %d | triangle tiles %d -> %d (%+.1f/min) | accumulators %d MJ"
      % (m, (b[3] - a[3]) / m, (b[2] - a[2]) / m, (b[1] - a[1]) / 1.956 * 50 / m, a[4], b[4], (b[4] - a[4]) / m, a[5], b[5], a[6], b[6], a[7], b[7], (b[7] - a[7]) / m, b[8]))
