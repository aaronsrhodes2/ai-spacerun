local s=game.surfaces['aquilo'] local o={}
local cnt={} local x0,y0,x1,y1=1e9,1e9,-1e9,-1e9 for _,e in pairs(s.find_entities_filtered{type='tile-ghost'}) do cnt[e.ghost_name]=(cnt[e.ghost_name] or 0)+1 x0=math.min(x0,e.position.x) x1=math.max(x1,e.position.x) y0=math.min(y0,e.position.y) y1=math.max(y1,e.position.y) end
for k,v in pairs(cnt) do o[#o+1]='tile ghost '..k..'='..v end o[#o+1]='ghost box '..x0..','..y0..' '..x1..','..y1
o[#o+1]='entity ghosts '..s.count_entities_filtered{type='entity-ghost'}
local t=s.find_entities_filtered{name='heating-tower'}[1] o[#o+1]='tick '..game.tick..' tower burner remaining '..t.burner.remaining_burning_fuel..' fuelinv '..t.burner.inventory.get_item_count()..' heat '..t.temperature
local ib={} for _,e in pairs(s.find_entities_filtered{type='simple-entity'}) do ib[e.name]=(ib[e.name] or 0)+1 end for k,v in pairs(ib) do o[#o+1]='simple '..k..'='..v end
local c=0 for _,e in pairs(s.find_entities_filtered{type='simple-entity'}) do if e.to_be_deconstructed() then c=c+1 end end o[#o+1]='marked for decon '..c
for _,e in pairs(s.find_entities_filtered{type={'container','logistic-container'}}) do local inv=e.get_inventory(defines.inventory.chest) local n=inv.get_item_count('ice-platform') if n>0 then o[#o+1]=e.name..' '..e.position.x..','..e.position.y..' ice-platform '..n end end
for _,e in pairs(s.find_entities_filtered{type='roboport'}) do o[#o+1]='roboport '..e.position.x..','..e.position.y..' '..e.quality.name end
rcon.print(table.concat(o,'\n'))
