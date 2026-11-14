local s=game.surfaces.aquilo local o={'tick '..game.tick} local st={} for k,v in pairs(defines.entity_status) do st[v]=k end
local li=s.find_entities_filtered{name='chemical-plant',position={-21.5,-18.5},radius=0.6}[1] local fl='' for i=1,li.fluids_count do local fd=li.get_fluid(i) if fd then fl=fl..' '..fd.name..'='..math.floor(fd.amount) end end
o[#o+1]='lithium plant d'..li.direction..' '..st[li.status]..fl..' holmium '..li.get_inventory(defines.inventory.crafter_input).get_item_count('holmium-plate')..' made '..li.products_finished
local pj=s.find_entities_filtered{name='pumpjack',position={-52.5,58.5},radius=0.6}[1] o[#o+1]='brine pumpjack d'..pj.direction..' '..st[pj.status]
local pts={{-24,-10},{-24,10},{-24,30},{-30,37},{-38,40},{-38,55},{-45,62},{-55,60}}
for _,p in pairs(pts) do local best,bd=nil,1e9 for _,h in pairs(s.find_entities_filtered{name='heat-pipe',position={p[1]+0.5,p[2]+0.5},radius=3.5}) do local d=(h.position.x-p[1]-0.5)^2+(h.position.y-p[2]-0.5)^2 if d<bd then bd=d best=h end end if best then o[#o+1]=best.position.x..','..best.position.y..'='..math.floor(best.temperature) end end
local fr=0 for _,e in pairs(s.find_entities_filtered{force='player',area={{-60,-22},{-15,65}}}) do if e.frozen then fr=fr+1 end end o[#o+1]='frozen on the line '..fr
local net=s.find_logistic_network_by_position({4,-11},'player') o[#o+1]='lithium '..net.get_item_count('lithium')..' plate '..net.get_item_count('lithium-plate')..' packs '..net.get_item_count('cryogenic-science-pack')..' solid fuel '..net.get_item_count('solid-fuel')..' holmium '..net.get_item_count('holmium-plate')
for _,t in pairs(s.find_entities_filtered{name='heating-tower'}) do o[#o+1]='tower '..t.position.x..' T'..math.floor(t.temperature) end
for _,g in pairs(s.find_entities_filtered{type='generator'}) do o[#o+1]='turbine W '..math.floor(g.energy_generated_last_tick*60) end
rcon.print(table.concat(o,' | '))
