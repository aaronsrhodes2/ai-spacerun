"""Nauvis rocket silos: status, parts, cargo aboard, and what the platforms in Nauvis orbit still lack from Nauvis."""
from _game import tools

LUA = """
local f=game.forces.player local n=game.surfaces.nauvis local o={} local st={} for k,v in pairs(defines.entity_status) do st[v]=k end
for _,e in pairs(n.find_entities_filtered{type='rocket-silo'}) do local c={} for _,nm in pairs({defines.inventory.rocket_silo_rocket,defines.inventory.rocket_silo_trash}) do local inv=e.get_inventory(nm) if inv then for _,it in pairs(inv.get_contents()) do c[#c+1]=it.name..':'..it.count end end end
local cp=e.cargo_pod local pc={} if cp and cp.valid then local inv=cp.get_inventory(defines.inventory.cargo_unit) if inv then for _,it in pairs(inv.get_contents()) do pc[#pc+1]=it.name..':'..it.count end end end
o[#o+1]='silo '..e.position.x..','..e.position.y..' '..(st[e.status] or '?')..' parts '..e.rocket_parts..' silo_status '..tostring(e.rocket_silo_status)..' cargo ['..table.concat(c,' ')..'] pod ['..table.concat(pc,' ')..']' end
for i,p in pairs(f.platforms) do if p.hub and p.space_location and p.space_location.name=='nauvis' then local inv=p.hub.get_inventory(defines.inventory.hub_main) local lack={} for _,se in pairs(p.hub.get_logistic_sections().sections) do if se.active then for _,fl in pairs(se.filters) do if fl.value and fl.import_from and fl.import_from.name=='nauvis' then local have=inv.get_item_count({name=fl.value.name,quality=fl.value.quality or 'normal'}) if have<fl.min then lack[#lack+1]=fl.value.name:gsub('%-science%-pack','')..' '..(fl.min-have) end end end end end
if #lack>0 then o[#o+1]='#'..i..' '..p.name:sub(-24)..' lacks: '..table.concat(lack,', ') end end end
rcon.print(table.concat(o,'|'))
"""
print(tools["run_lua"](" ".join(LUA.split())).replace("|", "\n"))
