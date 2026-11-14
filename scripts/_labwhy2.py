"""Silos on Gleba and Nauvis, pack production and use per minute, where agricultural packs sit on Gleba, how Nauvis labs are fed."""
from _game import tools

LUA = """
local f=game.forces.player local o={} local st={} for k,v in pairs(defines.entity_status) do st[v]=k end
local function sh(n) return (n:gsub('%-science%-pack','')) end
o[#o+1]='agri spoil ticks '..tostring(prototypes.item['agricultural-science-pack'].get_spoil_ticks())..' weight '..prototypes.item['agricultural-science-pack'].weight..' stack '..prototypes.item['agricultural-science-pack'].stack_size
for _,sn in pairs({'gleba','nauvis'}) do local s=game.surfaces[sn]
for _,e in pairs(s.find_entities_filtered{type='rocket-silo'}) do local inv=e.get_inventory(defines.inventory.rocket_silo_rocket) local c={} if inv then for _,it in pairs(inv.get_contents()) do c[#c+1]=sh(it.name)..':'..it.count end end
o[#o+1]=sn..' silo '..e.position.x..','..e.position.y..' '..(st[e.status] or '?')..' parts '..e.rocket_parts..' auto '..tostring(e.use_transitional_requests)..' cargo '..table.concat(c,' ') end
local ps=f.get_item_production_statistics(s) local t={}
for _,n in pairs({'automation','logistic','chemical','production','utility','space','military','metallurgic','electromagnetic','agricultural'}) do local nm=n..'-science-pack'
t[#t+1]=n..' +'..math.floor(ps.get_flow_count{name=nm,category='input',precision_index=defines.flow_precision_index.ten_minutes,count=false})..' -'..math.floor(ps.get_flow_count{name=nm,category='output',precision_index=defines.flow_precision_index.ten_minutes,count=false}) end
o[#o+1]=sn..' per min (10 min avg) '..table.concat(t,' | ') end
local g=game.surfaces.gleba local w={} for _,e in pairs(g.find_entities_filtered{force=f,type={'container','logistic-container','cargo-landing-pad','lab','rocket-silo'}}) do local n=e.get_item_count('agricultural-science-pack') if n>0 and e.type~='lab' then w[#w+1]=e.name..'@'..e.position.x..','..e.position.y..'='..n end end
o[#o+1]='gleba agri at: '..table.concat(w,' ')
local n=game.surfaces.nauvis local labs=n.find_entities_filtered{type='lab',force=f} local x0,y0,x1,y1=1e9,1e9,-1e9,-1e9 for _,l in pairs(labs) do x0=math.min(x0,l.position.x) y0=math.min(y0,l.position.y) x1=math.max(x1,l.position.x) y1=math.max(y1,l.position.y) end
o[#o+1]='nauvis labs box '..x0..','..y0..' .. '..x1..','..y1..' name '..labs[1].name
local cc={} for _,e in pairs(n.find_entities_filtered{area={{x0-8,y0-8},{x1+8,y1+8}},force=f}) do cc[e.name]=(cc[e.name] or 0)+1 end local c2={} for k,v in pairs(cc) do c2[#c2+1]=k..'x'..v end o[#o+1]='around labs: '..table.concat(c2,' ')
local k=0 for _,e in pairs(n.find_entities_filtered{area={{x0-8,y0-8},{x1+8,y1+8}},force=f,type='logistic-container'}) do if k<6 and e.prototype.logistic_mode=='requester' or e.prototype.logistic_mode=='buffer' then k=k+1 local rq={} for _,se in pairs(e.get_logistic_sections().sections) do for _,fl in pairs(se.filters) do if fl.value then rq[#rq+1]=sh(fl.value.name)..' '..fl.min end end end
local c={} for _,it in pairs(e.get_inventory(defines.inventory.chest).get_contents()) do c[#c+1]=sh(it.name)..':'..it.count end
if k<=6 then o[#o+1]=' '..e.name..'@'..e.position.x..','..e.position.y..' req ['..table.concat(rq,', ')..'] has ['..table.concat(c,' ')..']' end end end
o[#o+1]='requester-ish chests near labs: '..k
rcon.print(table.concat(o,'\\n'))
"""
print(tools["run_lua"](" ".join(LUA.split())))
