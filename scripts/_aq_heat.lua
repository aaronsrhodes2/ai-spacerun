local s=game.surfaces.aquilo local o={} local st={} for k,v in pairs(defines.entity_status) do st[v]=k end
local t=s.find_entities_filtered{name='heating-tower'}[1] o[#o+1]='tick '..game.tick..' tower T'..math.floor(t.temperature)..' '..st[t.status]..' fuel '..t.burner.inventory.get_item_count()..' cur '..tostring(t.burner.currently_burning and t.burner.currently_burning.name.name)
local r=s.find_entities_filtered{name='nuclear-reactor'}[1] o[#o+1]='reactor T'..math.floor(r.temperature)..' '..st[r.status]
local ex=s.find_entities_filtered{name='heat-exchanger'}[1] o[#o+1]='exchanger T'..math.floor(ex.temperature)..' '..st[ex.status]
local g=s.find_entities_filtered{type='generator'}[1] o[#o+1]='turbine W '..math.floor(g.energy_generated_last_tick*60)..' '..st[g.status]
local lo,hi,n=1e9,-1e9,0 local cold={} for _,h in pairs(s.find_entities_filtered{name='heat-pipe'}) do local T=h.temperature n=n+1 if T<lo then lo=T end if T>hi then hi=T end if T<40 and #cold<8 then cold[#cold+1]=h.position.x..','..h.position.y..'='..math.floor(T) end end o[#o+1]='heat pipes '..n..' min '..math.floor(lo)..' max '..math.floor(hi)..' cold: '..table.concat(cold,' ')
local acc=0 local cap=0 for _,a in pairs(s.find_entities_filtered{type='accumulator'}) do acc=acc+a.energy cap=cap+a.electric_buffer_size end o[#o+1]='accumulators '..math.floor(acc/1e6)..'/'..math.floor(cap/1e6)..' MJ'
rcon.print(table.concat(o,'\n'))
