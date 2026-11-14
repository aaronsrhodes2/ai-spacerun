"""Read only: stone, brick, iron plate and steel in each planet's robot networks, and the rocket silos' statuses."""
from _game import tools

print(tools["run_lua"](
    "local o={} for _,n in pairs({'nauvis','gleba','fulgora','vulcanus'}) do local s=game.surfaces[n] local seen={} for _,rp in pairs(s.find_entities_filtered{type='roboport'}) do local net=rp.logistic_network "
    "if net and not seen[net.network_id] then seen[net.network_id]=true local c=net.get_item_count('stone') local b=net.get_item_count('stone-brick') if c+b>0 then o[#o+1]=n..' net '..net.network_id..' cells '..#net.cells..' stone '..c..' brick '..b..' iron-plate '..net.get_item_count('iron-plate')..' steel '..net.get_item_count('steel-plate') end end end "
    "local st={} for _,si in pairs(s.find_entities_filtered{type='rocket-silo'}) do local k='?' for a,v in pairs(defines.entity_status) do if v==si.status then k=a end end st[#st+1]=k..(si.logistic_network and '' or '(no net)') end o[#o+1]=n..' silos: '..table.concat(st,', ') end rcon.print(table.concat(o,' ; '))").replace(" ; ", "\n"))
