"""Aquilo power watch: every N real seconds print turbine MW, total draw, low_power/frozen counts, tower and exchanger temperatures, fuel and ice stock.
_aq_powerwatch.py [rounds] [seconds]"""
import sys, time
from _game import tools
L = tools["run_lua"]
LUA = ("local s=game.surfaces.aquilo local p=s.find_entities_filtered{type='electric-pole',limit=1}[1] local st=p.electric_network_statistics local lo,fr=0,0 "
       "for _,e in pairs(s.find_entities_filtered{force='player'}) do if e.status==defines.entity_status.low_power then lo=lo+1 elseif e.status==defines.entity_status.frozen then fr=fr+1 end end "
       "local tw=s.find_entities_filtered{name='heating-tower',position={22.5,-15.5},radius=1}[1] local ex=s.find_entities_filtered{name='heat-exchanger',position={33,-19.5},radius=1}[1] local n=s.find_entities_filtered{name='roboport'}[1].logistic_network "
       "rcon.print(game.tick..' '..string.format('%.0f',(st.output_counts['steam-turbine'] or 0))..' low='..lo..' frozen='..fr..' tower='..math.floor(tw.temperature)..' E2='..math.floor(ex.temperature)..' fuel='..n.get_item_count('solid-fuel')..' ice='..n.get_item_count('ice'))")
rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 10
gap = float(sys.argv[2]) if len(sys.argv) > 2 else 30
prev = None
for _ in range(rounds):
    p = L(LUA).split(None, 2)
    t, e = int(p[0]), float(p[1])
    if prev:
        print("%5.0fs  turbines %.1f MW  %s" % ((t - prev[0]) / 60, (e - prev[1]) / ((t - prev[0]) / 60) / 1e6, p[2]), flush=True)
    prev = (t, e)
    time.sleep(gap)
