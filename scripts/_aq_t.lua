local s=game.surfaces.aquilo local f=game.forces.player local o={}
local rp=s.find_entities_filtered{name='roboport',position={4,-11},radius=1}[1]
local ib=s.find_entities_filtered{type='simple-entity',position={4,-11},radius=55} table.sort(ib,function(a,b) return (a.position.x-4)^2+(a.position.y+11)^2<(b.position.x-4)^2+(b.position.y+11)^2 end)
local n=0 for i=1,math.min(24,#ib) do local e=ib[i] if e.name:find('lithium',1,true) and not e.to_be_deconstructed() then e.order_deconstruction(f) n=n+1 end end
o[#o+1]='icebergs in reach '..#ib..' marked '..n
o[#o+1]='worker cargo bonus '..f.worker_robots_storage_bonus..' speed mod '..f.worker_robots_speed_modifier
rcon.print(table.concat(o,'\n'))
