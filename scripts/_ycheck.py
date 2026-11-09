import sys, time
sys.path.insert(0,"scripts")
from _game import tools
lua="local s=game.surfaces.nauvis local f=game.forces.player.get_item_production_statistics(s) local function r(n) return f.get_flow_count{name=n,category='input',precision_index=defines.flow_precision_index.one_minute}/60 end local function st(e) for k,v in pairs(defines.entity_status) do if v==e.status then return k end end return '?' end local c={} for _,e in pairs(s.find_entities_filtered{area={{15,-126},{125,-76}},force='player',type={'assembling-machine','chemical-plant'}}) do local q=e.get_recipe() if q and (q.name:find('utility') or q.name:find('processing') or q.name:find('flying') or q.name:find('electric-engine') or q.name=='electronic-circuit') then local k=q.name:sub(1,8)..' '..st(e) c[k]=(c[k] or 0)+1 end end local o={} for k,v in pairs(c) do o[#o+1]=k..' x'..v end table.sort(o) local b=s.find_entities_filtered{position={30.5,-109.5},radius=0.4,type='transport-belt'}[1] local l={} if b then for i=1,2 do for _,q in pairs(b.get_transport_line(i).get_contents()) do l[#l+1]='L'..i..q.name:sub(1,5)..q.count end end end rcon.print(string.format('EC %.2f/s utility %.3f/s | ',r('electronic-circuit'),r('utility-science-pack'))..table.concat(o,', ')..' | S1 '..table.concat(l,','))"
for i in range(6):
    print(time.strftime("%H:%M:%S"), tools["run_lua"](lua), flush=True)
    time.sleep(30)
