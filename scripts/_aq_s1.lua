local s=game.surfaces['aquilo'] local f=game.forces.player local o={}
o[#o+1]='tick '..game.tick..' speed '..game.speed
local cnt={}
for _,e in pairs(s.find_entities_filtered{force=f}) do local k=e.name..(e.quality and e.quality.name~='normal' and (':'..e.quality.name) or '') cnt[k]=(cnt[k] or 0)+1 end
local t={} for k,v in pairs(cnt) do t[#t+1]=k..'='..v end table.sort(t) o[#o+1]=table.concat(t,' ')
local pad=s.find_entities_filtered{type='cargo-landing-pad'}[1]
if pad then local inv=pad.get_inventory(defines.inventory.cargo_landing_pad_main) local c={} for _,it in pairs(inv.get_contents()) do c[#c+1]=it.name..(it.quality~='normal' and (':'..it.quality) or '')..'='..it.count end table.sort(c) o[#o+1]='PAD '..pad.position.x..','..pad.position.y..' '..table.concat(c,' ') end
local net=s.find_logistic_network_by_position({4,-11},f)
if net then local c={} for _,it in pairs(net.get_contents()) do c[#c+1]=it.name..(it.quality~='normal' and (':'..it.quality) or '')..'='..it.count end table.sort(c) o[#o+1]='NET robots L'..net.all_logistic_robots..' C'..net.all_construction_robots..' avail L'..net.available_logistic_robots..' C'..net.available_construction_robots..' '..table.concat(c,' ') end
for _,e in pairs(s.find_entities_filtered{force=f,type={'assembling-machine','furnace','boiler','generator','reactor','mining-drill','offshore-pump'}}) do
local r='' if e.type=='assembling-machine' or e.type=='furnace' then local rr=e.get_recipe() r=rr and rr.name or '-' end
local st='?' for k,v in pairs(defines.entity_status) do if v==e.status then st=k end end
local fl='' for i=1,e.fluids_count do local fd=e.get_fluid(i) if fd then fl=fl..' '..fd.name..'='..math.floor(fd.amount) end end
o[#o+1]=e.name..' '..e.position.x..','..e.position.y..' d'..e.direction..' '..r..' '..st..(e.temperature and (' T'..math.floor(e.temperature)) or '')..fl end
for _,e in pairs(s.find_entities_filtered{force=f,name='heating-tower'}) do o[#o+1]='tower '..e.position.x..','..e.position.y..' T'..math.floor(e.temperature)..' st'..e.status end
local techs={'cryogenic-science-pack','foundation','quantum-processor','railgun','fusion-reactor','lithium-processing','cryogenic-plant','heating-tower','rocket-turret','captive-biter-spawner','promethium-science-pack','fluoroketone'}
for _,n in pairs(techs) do local te=f.technologies[n] if te then o[#o+1]='tech '..n..' '..tostring(te.researched) end end
local q={} for _,te in pairs(f.research_queue) do q[#q+1]=te.name end o[#o+1]='QUEUE '..table.concat(q,',')
rcon.print(table.concat(o,'\n'))
