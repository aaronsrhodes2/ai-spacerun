"""Read only: White Science machines by kind: quality, crafting speed, module slots and modules, productivity bonus; whether the space
science and crushing recipes allow productivity; productivity and speed modules by quality in the Nauvis robot networks; row 4 free tiles."""
from _game import tools

print(tools["run_lua"](
    "local s=game.surfaces['platform-1'] local o={} local g={} for _,e in pairs(s.find_entities_filtered{type={'assembling-machine','furnace'}}) do local rc=e.get_recipe() local mi=e.get_module_inventory() local m={} if mi then for _,it in pairs(mi.get_contents()) do m[#m+1]=it.count..'x'..it.name..'/'..it.quality end end "
    "local k=e.name..'/'..e.quality.name..' '..(rc and rc.name or '-')..' speed '..string.format('%.2f',e.crafting_speed)..' prod '..string.format('%.2f',e.productivity_bonus)..' slots '..(mi and #mi or 0)..' ['..table.concat(m,',')..']' g[k]=(g[k] or 0)+1 end "
    "for k,v in pairs(g) do o[#o+1]=v..' x '..k end table.sort(o) "
    "for _,r in pairs({'space-science-pack','metallic-asteroid-crushing','oxide-asteroid-crushing','carbonic-asteroid-crushing','metallic-asteroid-reprocessing','iron-plate'}) do local p=prototypes.recipe[r] local ae=p.allowed_effects local t={} if ae then for k,v in pairs(ae) do if v then t[#t+1]=k end end end "
    "local cats={} if p.allowed_module_categories then for k,_ in pairs(p.allowed_module_categories) do cats[#cats+1]=k end end o[#o+1]='recipe '..r..' effects ['..table.concat(t,',')..'] module categories ['..table.concat(cats,',')..'] time '..p.energy..' max productivity '..tostring(p.maximum_productivity) end "
    "local f=game.forces.player o[#o+1]='recipe productivity bonus (research): space science '..f.recipes['space-science-pack'].productivity_bonus..', metallic crushing '..f.recipes['metallic-asteroid-crushing'].productivity_bonus..', oxide crushing '..f.recipes['oxide-asteroid-crushing'].productivity_bonus "
    "local seen={} for _,rp in pairs(game.surfaces.nauvis.find_entities_filtered{type='roboport'}) do local net=rp.logistic_network if net and not seen[net.network_id] then seen[net.network_id]=true local c={} for _,n in pairs({'productivity-module','productivity-module-2','productivity-module-3','speed-module','speed-module-2','speed-module-3'}) do for q,_ in pairs(prototypes.quality) do if q~='quality-unknown' then local k=net.get_item_count({name=n,quality=q}) if k>0 then c[#c+1]=n..'/'..q..' '..k end end end end if #c>0 then o[#o+1]='nauvis net '..net.network_id..': '..table.concat(c,', ') end end end "
    "local fr={} for x=-4,3 do if s.count_entities_filtered{area={{x+0.1,4.1},{x+0.9,4.9}}}==0 then fr[#fr+1]=x end end o[#o+1]='row 4 free tiles x: '..table.concat(fr,',') "
    "rcon.print(table.concat(o,' ; '))").replace(" ; ", "\n"))
