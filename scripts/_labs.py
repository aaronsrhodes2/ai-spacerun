"""Read only: what the labs on a surface hold, the network stock of each pack, the current research and its packs, pad request sections."""
import sys

from _game import tools

S = sys.argv[1] if len(sys.argv) > 1 else "nauvis"
lua = (
    "local s=game.surfaces['%s'] local f=game.forces.player local o={} local tot={} local n=0 local zero={} "
    "for _,l in pairs(s.find_entities_filtered{type='lab'}) do n=n+1 local inv=l.get_inventory(defines.inventory.lab_input) local seen={} for _,it in pairs(inv.get_contents()) do tot[it.name]=(tot[it.name] or 0)+it.count seen[it.name]=true end "
    "for name,_ in pairs(prototypes.get_item_filtered{{filter='type',type='tool'}}) do if not seen[name] then zero[name]=(zero[name] or 0)+1 end end end "
    "local t={} for k,v in pairs(tot) do t[#t+1]=k:sub(1,8)..' '..v..' (labs without: '..(zero[k] or 0)..')' end table.sort(t) o[#o+1]=n..' labs hold: '..table.concat(t,'; ') "
    "local z={} for k,v in pairs(zero) do if not tot[k] then z[#z+1]=k end end o[#o+1]='in no lab: '..table.concat(z,', ') "
    "local r=f.current_research if r then local ing={} for _,i in pairs(r.research_unit_ingredients) do ing[#ing+1]=i.name:sub(1,8) end o[#o+1]='research '..r.name..' needs '..table.concat(ing,',')..' progress '..string.format('%%.3f',f.research_progress) else o[#o+1]='no research' end "
    "local q={} for _,t2 in pairs(f.research_queue) do q[#q+1]=t2.name end o[#o+1]='queue: '..table.concat(q,', ') "
    "local seenn={} for _,rp in pairs(s.find_entities_filtered{type='roboport'}) do local net=rp.logistic_network if net and not seenn[net.network_id] then seenn[net.network_id]=true local c={} for name,_ in pairs(prototypes.get_item_filtered{{filter='type',type='tool'}}) do local k=net.get_item_count(name) if k>0 then c[#c+1]=name:sub(1,8)..' '..k end end if #c>0 then o[#o+1]='network '..net.network_id..' ('..#net.cells..' cells): '..table.concat(c,', ') end end end "
    "for _,pad in pairs(s.find_entities_filtered{type='cargo-landing-pad'}) do for _,lp in pairs(pad.get_logistic_point()) do for si,sec in pairs(lp.sections) do local rq={} for i,fl in pairs(sec.filters) do if fl.value then rq[#rq+1]=fl.value.name..':'..(fl.min or 0)..'/'..tostring(fl.max)..(fl.import_from and ('@'..fl.import_from.name) or '') end end "
    "o[#o+1]='pad '..pad.position.x..','..pad.position.y..' section '..si..' group['..(sec.group or '')..'] active '..tostring(sec.active)..' mult '..sec.multiplier..': '..table.concat(rq,' ') end end end "
    "rcon.print(table.concat(o,'\\n'))" % S)
print(tools["run_lua"](lua))
