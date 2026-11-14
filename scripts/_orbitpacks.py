"""Science packs on the platforms that can hand them on: White Science, the wheels; their provide flag, pause state, place; and the space and
automation requests of the Nauvis-Gleba shuttles and both pads."""
from _game import tools

LUA = """
local f=game.forces.player local o={}
local function sh(n) return (n:gsub('%-science%-pack','')) end
for i,p in pairs(f.platforms) do if p.hub and (p.name:find('Wheel',1,true) or p.name:find('White Science',1,true)) then local inv=p.hub.get_inventory(defines.inventory.hub_main) local t={} for _,it in pairs(inv.get_contents()) do if it.name:find('science') then t[#t+1]=sh(it.name)..':'..it.count end end
o[#o+1]='#'..i..' '..p.name:sub(-16)..' ['..p.surface.name..'] at '..(p.space_location and p.space_location.name or 'transit')..' paused '..tostring(p.paused)..' provide '..tostring(p.hub.providing_to_other_platforms)..' | '..table.concat(t,' ') end end
for i,p in pairs(f.platforms) do if p.hub and p.name:find('Nauvis-Gleba',1,true) then local t={} for si,se in pairs(p.hub.get_logistic_sections().sections) do for k,fl in pairs(se.filters) do if fl.value and (fl.value.name=='space-science-pack' or fl.value.name=='automation-science-pack') then t[#t+1]='sec'..si..'/'..k..' '..sh(fl.value.name)..' '..fl.min..'..'..tostring(fl.max)..' from '..tostring(fl.request_from)..' group '..tostring(se.group)..' active '..tostring(se.active) end end end
local inv=p.hub.get_inventory(defines.inventory.hub_main) o[#o+1]='#'..i..' at '..(p.space_location and p.space_location.name or 'transit')..' space '..inv.get_item_count('space-science-pack')..' auto '..inv.get_item_count('automation-science-pack')..' | '..table.concat(t,'; ') end end
for _,sn in pairs({'gleba','nauvis'}) do local pad=game.surfaces[sn].find_entities_filtered{type='cargo-landing-pad'}[1] o[#o+1]=sn..' pad space '..pad.get_item_count('space-science-pack')..' auto '..pad.get_item_count('automation-science-pack')..' pods '..game.surfaces[sn].count_entities_filtered{type='cargo-pod'} end
local n=0 for _,net in pairs(f.logistic_networks.nauvis or {}) do n=n+net.get_item_count('space-science-pack') end o[#o+1]='nauvis ground space packs '..n..' tick '..game.tick
rcon.print(table.concat(o,'|'))
"""
print(tools["run_lua"](" ".join(LUA.split())).replace("|", "\n"))
