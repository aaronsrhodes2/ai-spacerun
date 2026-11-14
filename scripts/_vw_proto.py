"""Read only: recipes and prototypes the Vulcanus Wheel export line rests on."""
from _game import tools

LUA = ("local o={} local p=prototypes.entity['express-underground-belt'] o[#o+1]='express ug '..p.max_underground_distance local f=game.forces.player "
       "for _,r in pairs{'casting-low-density-structure','plastic-bar','coal-synthesis','simple-coal-liquefaction','heavy-oil-cracking','light-oil-cracking','sulfuric-acid','ice-melting','copper-ore-melting','iron-ore-melting','low-density-structure','carbonic-asteroid-crushing','advanced-carbonic-asteroid-crushing'} do "
       "local rc=f.recipes[r] if rc then local a={} for _,i in pairs(rc.ingredients) do a[#a+1]=i.amount..' '..i.name end local b={} for _,i in pairs(rc.products) do b[#b+1]=i.amount..' '..i.name end "
       "o[#o+1]=r..' ['..rc.energy..'s en='..tostring(rc.enabled)..' prod '..tostring(rc.productivity_bonus)..'] '..table.concat(a,' + ')..' -> '..table.concat(b,' + ') end end "
       "for _,t in pairs{'turbo-transport-belt','stack-inserter','foundry','bulk-inserter'} do local tt=f.technologies[t] o[#o+1]=t..' researched '..tostring(tt and tt.researched) end "
       "for _,n in pairs{'chemical-plant','foundry','oil-refinery','crusher'} do local e=prototypes.entity[n] o[#o+1]=n..' speed epic '..tostring(e.get_crafting_speed('epic'))..' modslots '..tostring(e.module_inventory_size) end "
       "o[#o+1]='bulk cap bonus '..f.bulk_inserter_capacity_bonus..' belt speed '..prototypes.entity['express-transport-belt'].belt_speed "
       "local s=game.surfaces.nauvis local net=f.find_logistic_network_by_position({0,0},s) "
       "for _,n in pairs{'productivity-module-2','productivity-module-3','speed-module-2','speed-module-3','productivity-module'} do local t={} for _,q in pairs{'normal','uncommon','rare','epic','legendary'} do local c=0 for _,nw in pairs(f.logistic_networks.nauvis or {}) do c=c+nw.get_item_count({name=n,quality=q}) end t[#t+1]=q:sub(1,1)..c end o[#o+1]='nauvis '..n..' '..table.concat(t,' ') end "
       "rcon.print(table.concat(o,'\\n'))")
print(tools["run_lua"](LUA))
