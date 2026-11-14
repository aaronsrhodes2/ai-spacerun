"""Read only: recipes of the processing unit chain with the force's productivity bonus, and what stands above the district loop."""
import sys

from _game import tools

surf = sys.argv[1] if len(sys.argv) > 1 else "platform-16"
R = ("local o={} for _,n in pairs{'processing-unit','advanced-circuit','electronic-circuit','copper-cable','casting-copper-cable','casting-iron','coal-synthesis','advanced-carbonic-asteroid-crushing','carbonic-asteroid-crushing','simple-coal-liquefaction','heavy-oil-cracking','light-oil-cracking','plastic-bar','sulfuric-acid','ice-melting','rocket-fuel','solid-fuel-from-light-oil','casting-low-density-structure'} do "
     "local r=prototypes.recipe[n] local i={} for _,x in pairs(r.ingredients) do i[#i+1]=x.amount..' '..x.name end local q={} for _,x in pairs(r.products) do q[#q+1]=tostring(x.amount or (x.amount_min..'-'..x.amount_max))..' '..x.name..((x.probability or 1)<1 and ('@'..x.probability) or '') end "
     "o[#o+1]=n..' '..r.energy..'s '..table.concat(i,' + ')..' -> '..table.concat(q,' + ')..' | force bonus '..string.format('%.2f',game.forces.player.recipes[n].productivity_bonus) end rcon.print(table.concat(o,'\\n'))")
print(tools["run_lua"](R))
A = ("local s=game.surfaces['%s'] local o={} for _,e in pairs(s.find_entities_filtered{area={{-118,25},{-88,31}}}) do if e.type~='transport-belt' then o[#o+1]=string.format('%%s %%s %%.1f,%%.1f d%%d',e.name,e.quality.name,e.position.x,e.position.y,e.direction) end end rcon.print(table.concat(o,'\\n'))") % surf
print(tools["run_lua"](A))
