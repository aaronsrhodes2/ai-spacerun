local s=game.surfaces.aquilo local f=game.forces.player local o={}
local marked={} local all=s.find_entities_filtered{type='simple-entity'} local m=0
for _,e in pairs(all) do if e.to_be_deconstructed() then m=m+1 marked[#marked+1]=math.floor(e.position.x)..','..math.floor(e.position.y) end end
o[#o+1]='icebergs '..#all..' marked '..m..': '..table.concat(marked,' ')
local net=s.find_logistic_network_by_position({4,-11},f) o[#o+1]='lithium '..net.get_item_count('lithium')..' plate '..net.get_item_count('lithium-plate')..' ice-platform '..net.get_item_count('ice-platform')..' C robots '..net.available_construction_robots..'/'..net.all_construction_robots..' L '..net.available_logistic_robots..'/'..net.all_logistic_robots
local c=s.find_entities_filtered{name='requester-chest',position={14.5,-8.5},radius=0.4}[1] o[#o+1]='furnace chest lithium '..c.get_inventory(defines.inventory.chest).get_item_count('lithium')
local c2=s.find_entities_filtered{name='requester-chest',position={-32.5,-35.5},radius=0.4}[1] o[#o+1]='FK chest lithium '..c2.get_inventory(defines.inventory.chest).get_item_count('lithium')
rcon.print(table.concat(o,'\n'))
