import sys, time
sys.path.insert(0,"scripts")
from _game import tools
lua="local s=game.surfaces.nauvis local n=0 local minx,maxx,miny,maxy=1e9,-1e9,1e9,-1e9 for _,e in pairs(s.find_entities_filtered{type={'transport-belt','underground-belt','splitter','container','logistic-container'}}) do local c=0 if e.type=='container' or e.type=='logistic-container' then c=e.get_inventory(defines.inventory.chest).get_item_count('utility-science-pack') else for i=1,e.get_max_transport_line_index() do c=c+e.get_transport_line(i).get_item_count('utility-science-pack') end end if c>0 then n=n+c minx=math.min(minx,e.position.x) maxx=math.max(maxx,e.position.x) miny=math.min(miny,e.position.y) maxy=math.max(maxy,e.position.y) end end local labs=0 local ok=0 for _,l in pairs(s.find_entities_filtered{type='lab'}) do labs=labs+1 if l.status==defines.entity_status.working then ok=ok+1 end end local f=game.forces.player rcon.print(string.format('yellow packs on belts/chests %d x[%.0f..%.0f] y[%.0f..%.0f]; labs working %d/%d; research %s %.2f',n,minx,maxx,miny,maxy,ok,labs,f.current_research and f.current_research.name or 'none',f.research_progress))"
for i in range(int(sys.argv[1]) if len(sys.argv)>1 else 10):
    print(time.strftime("%H:%M:%S"), tools["run_lua"](lua), flush=True)
    time.sleep(60)
