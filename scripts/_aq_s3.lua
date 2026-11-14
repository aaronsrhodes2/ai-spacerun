local s=game.surfaces['aquilo'] local o={}
for _,a in pairs({{-20,-36,45,-25},{-40,-22,-20,22},{-8,12,18,22},{-40,-8,-25,2},{2,-6,12,-2}}) do
local cnt={} for _,e in pairs(s.find_entities_filtered{area={{a[1],a[2]},{a[3],a[4]}}}) do local k=e.type..'/'..e.name..'/'..(e.force and e.force.name or '') cnt[k]=(cnt[k] or 0)+1 end
local t={} for k,v in pairs(cnt) do t[#t+1]=k..'='..v end o[#o+1]=table.concat(a,',')..': '..table.concat(t,' ') end
local hp=prototypes.entity['heating-tower'] o[#o+1]='tower type '..hp.type..' maxE '..tostring(hp.get_max_energy_usage('epic')*60)
local t=s.find_entities_filtered{name='heating-tower'}[1] o[#o+1]='tower burner remaining '..t.burner.remaining_burning_fuel..' fuelinv '..t.burner.inventory.get_item_count()..' heat '..t.temperature
local rp=prototypes.entity['roboport'] o[#o+1]='roboport logi '..rp.logistic_radius..' cons '..rp.construction_radius
local sub=prototypes.entity['substation'] o[#o+1]='substation wire '..sub.get_max_wire_distance('epic')..' supply '..sub.get_supply_area_distance('epic')
local bp=prototypes.entity['big-electric-pole'] o[#o+1]='bigpole wire '..bp.get_max_wire_distance('epic')..' supply '..bp.get_supply_area_distance('epic')
local mp=prototypes.entity['medium-electric-pole'] o[#o+1]='medpole wire '..mp.get_max_wire_distance('epic')..' supply '..mp.get_supply_area_distance('epic')
for _,n in pairs({'chemical-plant','pumpjack','heat-exchanger','steam-turbine','heating-tower','offshore-pump','electric-furnace'}) do local p=prototypes.entity[n] local ok,sp=pcall(function() return p.get_crafting_speed('epic') end) o[#o+1]=n..' speed '..tostring(ok and sp or '-')..' maxE '..tostring(p.get_max_energy_usage and p.get_max_energy_usage('epic')*60 or '-')..' heat '..tostring(p.heating_energy*60) end
local es=s.find_entities_filtered{name='steam-turbine'}[1] o[#o+1]='turbine maxprod '..tostring(es.prototype.get_max_energy_production('epic')*60)
local st=s.find_entities_filtered{name='substation'}[1] local en=st.electric_network_statistics local inp=0 for k,v in pairs(en.input_counts) do inp=inp+en.get_flow_count{name=k,category='input',precision_index=defines.flow_precision_index.one_minute} end local outp=0 for k,v in pairs(en.output_counts) do outp=outp+en.get_flow_count{name=k,category='output',precision_index=defines.flow_precision_index.one_minute} end o[#o+1]='power used W '..(inp*60)..' produced W '..(outp*60)
for _,c in pairs(s.find_entities_filtered{type='logistic-container'}) do local inv=c.get_inventory(defines.inventory.chest) local t={} for _,it in pairs(inv.get_contents()) do t[#t+1]=it.name..'='..it.count end local rq='' local pt=c.get_requester_point() if pt then for _,sec in pairs(pt.sections) do for _,fl in pairs(sec.filters) do if fl.value then rq=rq..' ask '..fl.value.name..' '..(fl.min or 0) end end end end o[#o+1]=c.name..' '..c.position.x..','..c.position.y..' '..table.concat(t,' ')..rq end
rcon.print(table.concat(o,'\n'))
