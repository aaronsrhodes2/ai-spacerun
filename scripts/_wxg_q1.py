"""Scratch (read-only): recipes of the rocket fuel chain, the district's machines with modules and status."""
import sys

from _game import tools

SURF = sys.argv[1] if len(sys.argv) > 1 else "platform-12"


def q(lua):
    print(tools["run_lua"](lua.replace("SURF", SURF)).replace("@@", "\n"))


q("local o={} for _,r in pairs{'rocket-fuel','solid-fuel-from-light-oil','heavy-oil-cracking','simple-coal-liquefaction','coal-synthesis','sulfuric-acid','ice-melting','advanced-carbonic-asteroid-crushing','carbonic-asteroid-crushing','light-oil-cracking','solid-fuel-from-heavy-oil','solid-fuel-from-petroleum-gas'} do local p=prototypes.recipe[r] local s=r..' [t='..p.energy..' maxprod='..tostring(p.maximum_productivity)..' prodbonus='..string.format('%.2f',game.forces.player.recipes[r].productivity_bonus)..' en='..tostring(game.forces.player.recipes[r].enabled)..']: ' for _,i in pairs(p.ingredients) do s=s..i.amount..' '..i.name..', ' end s=s..'=> ' for _,i in pairs(p.products) do s=s..(i.amount or (i.amount_min..'-'..i.amount_max))..' '..i.name..(i.probability and i.probability<1 and ('@'..i.probability) or '')..', ' end local am={} for k,v in pairs(p.allowed_effects or {}) do if v then am[#am+1]=k end end s=s..' effects:'..table.concat(am,'/') o[#o+1]=s end rcon.print(table.concat(o,'@@'))")
q("local s=game.surfaces['SURF'] local w={} for _,e in pairs(s.find_entities_filtered{type={'assembling-machine','furnace'},area={{-135,23},{-83,64}}}) do local k='?' for n,v in pairs(defines.entity_status) do if v==e.status then k=n end end local rc=e.get_recipe() local m='' for _,it in pairs(e.get_module_inventory().get_contents()) do m=m..' '..it.count..'x'..it.name..'/'..it.quality end local fl='' for n,v in pairs(e.get_fluid_contents()) do fl=fl..' '..n..'='..math.floor(v) end "
  "w[#w+1]=string.format('%-36s %6.1f,%5.1f %-26s speed %.2f prod %.2f done %d |%s |%s',(rc and rc.name or '-'),e.position.x,e.position.y,k,e.crafting_speed,e.productivity_bonus,e.products_finished,m,fl) end table.sort(w) rcon.print(table.concat(w,'@@'))")
