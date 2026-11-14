local s=game.surfaces.aquilo local o={'tick '..game.tick}
local pts={{9,-14},{5,-16},{5,-24},{0,-25},{-10,-25},{-15,-25},{-17,-23},{-20,-24},{-26,-24},{-32,-24},{-33,-28},{-30,-33},{-29,-38},{-26,-43},{-35,-44},{-35,-50},{-35,-60},{-35,-68},{14,-22},{15,-34},{-10,-34}}
for _,p in pairs(pts) do local best,bd=nil,1e9 for _,h in pairs(s.find_entities_filtered{name='heat-pipe',position={p[1]+0.5,p[2]+0.5},radius=2.5}) do local d=(h.position.x-p[1]-0.5)^2+(h.position.y-p[2]-0.5)^2 if d<bd then bd=d best=h end end if best then o[#o+1]=best.position.x..','..best.position.y..'='..math.floor(best.temperature) end end
for _,t in pairs(s.find_entities_filtered{name='heating-tower'}) do o[#o+1]='tower '..t.position.x..','..t.position.y..' T'..math.floor(t.temperature)..' fuel '..t.burner.inventory.get_item_count() end
for _,g in pairs(s.find_entities_filtered{type='generator'}) do o[#o+1]='turbine '..g.position.x..','..g.position.y..' W '..math.floor(g.energy_generated_last_tick*60)..(g.frozen and ' frozen' or '') end
for _,x in pairs(s.find_entities_filtered{name='heat-exchanger'}) do o[#o+1]='exchanger '..x.position.x..','..x.position.y..' T'..math.floor(x.temperature) end
local acc=0 for _,a in pairs(s.find_entities_filtered{type='accumulator'}) do acc=acc+a.energy end o[#o+1]='acc MJ '..math.floor(acc/1e6)
rcon.print(table.concat(o,' | '))
