local s=game.surfaces.aquilo local f=game.forces.player local o={}
local carry={} local low=0 local n=0 for _,r in pairs(s.find_entities_filtered{type='logistic-robot',force=f}) do n=n+1 local st=r.get_inventory(defines.inventory.robot_cargo)[1] local k=st.valid_for_read and st.name or 'empty' carry[k]=(carry[k] or 0)+1 if r.energy<0.3*r.prototype.get_max_energy(r.quality) then low=low+1 end end
local t={} for k,v in pairs(carry) do t[#t+1]=k..'='..v end o[#o+1]='logistic robots flying '..n..' low energy '..low..' carrying '..table.concat(t,' ')
for _,r in pairs(s.find_entities_filtered{type='roboport'}) do o[#o+1]='roboport '..r.position.x..','..r.position.y..' energy '..math.floor(r.energy/1e6)..' MJ charging '..r.logistic_cell.charging_robot_count..' waiting '..r.logistic_cell.to_charge_robot_count..' stationed L '..r.logistic_cell.stationed_logistic_robot_count..' C '..r.logistic_cell.stationed_construction_robot_count end
local net=s.find_logistic_network_by_position({4,-11},f) o[#o+1]='lithium '..net.get_item_count('lithium')..' ice '..net.get_item_count('ice')..' solid '..net.get_item_count('solid-fuel')
for _,g in pairs(s.find_entities_filtered{type='generator'}) do o[#o+1]='turbine W '..math.floor(g.energy_generated_last_tick*60) end
local acc=0 for _,a in pairs(s.find_entities_filtered{type='accumulator'}) do acc=acc+a.energy end o[#o+1]='acc MJ '..math.floor(acc/1e6)
for _,c in pairs(s.find_entities_filtered{type='logistic-container',area={{-45,-75},{10,-14}}}) do local pt=c.get_requester_point() if pt then local t={} for _,it in pairs(c.get_inventory(defines.inventory.chest).get_contents()) do t[#t+1]=it.name..'='..it.count end o[#o+1]='req '..c.position.x..','..c.position.y..' '..table.concat(t,' ') end end
rcon.print(table.concat(o,'\n'))
