from _game import tools
import sys
PAIRS = [('platform-23', 32, 6), ('platform-24', 33, 7), ('platform-25', 34, 5)]
for surf, idx, sib in PAIRS:
    LUA = ("local f=game.forces.player local p=f.platforms[%d] local old=f.platforms[%d] "
           "local secs=p.hub.get_logistic_sections() local mine={} for _,se in pairs(secs.sections) do for _,fl in pairs(se.filters) do if fl.value then mine[fl.value.name]=true end end end "
           "local n=0 for _,se in pairs(old.hub.get_logistic_sections().sections) do for _,fl in pairs(se.filters) do if fl.value and not mine[fl.value.name] and string.find(fl.value.name,'science') then "
           "local ns=secs.add_section() ns.set_slot(1,{value={name=fl.value.name,quality='normal'},min=fl.min,import_from=fl.import_from,request_from=fl.request_from,minimum_delivery_count=fl.minimum_delivery_count}) n=n+1 end end end "
           "local inv=p.hub.get_inventory(defines.inventory.hub_main) if inv.get_item_count('iron-plate')<200 then local nb,bn=nil,0 for _,net in pairs(f.logistic_networks.nauvis or {}) do if net.all_logistic_robots>bn then nb=net bn=net.all_logistic_robots end end "
           "local got=nb.remove_item{name='iron-plate',count=200} inv.insert{name='iron-plate',count=got} end "
           "rcon.print('science sections copied '..n..' from %d, plates ok')") % (idx, sib, sib)
    print(tools["run_lua"](LUA))
