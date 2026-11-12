"""Gleba watch: science made per minute and the stocks that matter, every INTERVAL seconds, N times. Usage: _glebawatch.py [n] [interval]"""
import sys
import time

from _game import tools

L = ("local s=game.surfaces.gleba local sci,egg,bf=0,0,0 local work={} for _,m in pairs(s.find_entities_filtered{name='biochamber',area={{56,0},{134,21}}}) do local r=m.get_recipe() if r then "
     "if r.name=='agricultural-science-pack' then sci=sci+m.products_finished elseif r.name=='pentapod-egg' then egg=egg+m.products_finished elseif r.name=='bioflux' then bf=bf+m.products_finished end "
     "if m.status==defines.entity_status.working then work[r.name]=(work[r.name] or 0)+1 end end end "
     "local function belts(x0,y0,x1,y1,item) local c=0 for _,b in pairs(s.find_entities_filtered{type='transport-belt',area={{x0,y0},{x1+1,y1+1}}}) do for l=1,2 do c=c+b.get_transport_line(l).get_item_count(item) end end return c end "
     "local ch=s.find_entities_filtered{type='logistic-container',position={128.5,20.5},radius=0.3}[1].get_inventory(defines.inventory.chest) "
     "local sil=s.find_entities_filtered{name='rocket-silo'}[1] local en=s.count_entities_filtered{force='enemy',area={{30,-30},{160,50}}} "
     "rcon.print(game.tick..' '..sci..' '..egg..' '..bf..' chest packs '..ch.get_item_count('agricultural-science-pack')..' spoilage '..ch.get_item_count('spoilage')..' | rocket parts '..sil.rocket_parts..' | belts: yumako '..belts(74,3,126,3,'yumako')..' jellynut '..belts(74,3,126,3,'jellynut')"
     "..' bioflux '..belts(67,10,116,10,'bioflux')..' nutrients '..(belts(76,9,124,9,'nutrients')+belts(67,11,124,11,'nutrients'))..' eggs '..belts(61,17,122,20,'pentapod-egg')..' | working '..helpers.table_to_json(work)..' | enemies '..en)")
n = int(sys.argv[1]) if len(sys.argv) > 1 else 5
iv = int(sys.argv[2]) if len(sys.argv) > 2 else 60
prev = None
for i in range(n):
    r = tools["run_lua"](L)
    p = r.split(" ", 4)
    tick, sci, egg, bf = int(p[0]), int(p[1]), int(p[2]), int(p[3])
    if prev:
        m = (tick - prev[0]) / 3600
        print("science %.0f/min eggs made %.0f/min bioflux crafts %.1f/min | %s" % ((sci - prev[1]) * 1.5 / m, (egg - prev[2]) * 3 / m, (bf - prev[3]) / m, p[4]), flush=True)
    else:
        print("start | " + p[4], flush=True)
    prev = (tick, sci, egg, bf)
    if i < n - 1:
        time.sleep(iv)
