"""Gleba long run log: one line a minute of real time (several game minutes when the game speed is raised) into docs/gleba_longrun.log.
Usage: _glebalong.py [lines] [seconds between lines]"""
import sys
import time

from _game import tools

L = ("local f=game.forces.player local s=game.surfaces.gleba local st=f.get_item_production_statistics('gleba') local P=defines.flow_precision_index.ten_minutes "
     "local function fl(n,c) return math.floor(st.get_flow_count{name=n,category=c,precision_index=P}) end "
     "local function belts(x0,y0,x1,y1,item) local c=0 for _,b in pairs(s.find_entities_filtered{type='transport-belt',area={{x0,y0},{x1+1,y1+1}}}) do for l=1,2 do c=c+b.get_transport_line(l).get_item_count(item) end end return c end "
     "local keep,eggw,sciw,nofuel=0,0,0,0 for _,m in pairs(s.find_entities_filtered{name='biochamber',area={{56,0},{134,21}}}) do local r=m.get_recipe() local w=m.status==defines.entity_status.working if m.status==defines.entity_status.no_fuel then nofuel=nofuel+1 end "
     "if r and r.name=='pentapod-egg' then if w then eggw=eggw+1 end if m.position.x>116 then keep=keep+m.get_inventory(defines.inventory.crafter_input).get_item_count('pentapod-egg')+m.get_output_inventory().get_item_count('pentapod-egg')+(m.is_crafting() and 1 or 0) end elseif r and r.name=='agricultural-science-pack' and w then sciw=sciw+1 end end "
     "local ch=s.find_entities_filtered{type='logistic-container',position={128.5,20.5},radius=0.3}[1].get_inventory(defines.inventory.chest) "
     "local pl={} for _,t in pairs(s.find_entities_filtered{name='agricultural-tower'}) do pl[#pl+1]=s.count_entities_filtered{type='plant',area={{t.position.x-10.5,t.position.y-10.5},{t.position.x+10.5,t.position.y+10.5}}} end "
     "local nb,bn=nil,0 for _,net in pairs(f.logistic_networks.nauvis or {}) do if net.all_logistic_robots>bn then nb=net bn=net.all_logistic_robots end end local p=f.platforms[6] "
     "local sp=0 for _,b in pairs(s.find_entities_filtered{type='transport-belt',area={{56,0},{134,21}}}) do for l=1,2 do sp=sp+b.get_transport_line(l).get_item_count('spoilage') end end "
     "rcon.print(string.format('%.2f',game.tick/216000)..'h | per min: science '..fl('agricultural-science-pack','input')..' eggs '..fl('pentapod-egg','input')..' bioflux '..fl('bioflux','input')..' nutrients '..fl('nutrients','input')..' yumako '..fl('yumako','input')..' jellynut '..fl('jellynut','input')"
     "..' | keeper eggs '..keep..' egg chambers working '..eggw..' science working '..sciw..' chambers without fuel '..nofuel..' | chest packs '..ch.get_item_count('agricultural-science-pack')..' rot '..ch.get_item_count('spoilage')"
     "..' | belts: yumako '..belts(74,3,126,3,'yumako')..' jellynut '..belts(74,3,126,3,'jellynut')..' bioflux '..belts(67,10,116,10,'bioflux')..' nutrients '..(belts(76,9,124,9,'nutrients')+belts(67,11,124,11,'nutrients'))..' eggs '..belts(61,17,122,20,'pentapod-egg')..' rot on core belts '..sp"
     "..' | plants '..table.concat(pl,'/')..' | enemies near core '..s.count_entities_filtered{force='enemy',area={{30,-30},{160,50}}}..' | rockets launched '..f.rockets_launched..' | Nauvis packs '..nb.get_item_count('agricultural-science-pack')..' shuttle '..(p.space_location and p.space_location.name or 'in transit')..' hub packs '..p.hub.get_item_count('agricultural-science-pack'))")
n = int(sys.argv[1]) if len(sys.argv) > 1 else 40
iv = int(sys.argv[2]) if len(sys.argv) > 2 else 60
for i in range(n):
    try:
        r = tools["run_lua"](L)
    except Exception as e:
        r = "error " + str(e)[:200]
    open("docs/gleba_longrun.log", "a", encoding="utf-8").write(r + "\n")
    print(r, flush=True)
    if i < n - 1:
        time.sleep(iv)
