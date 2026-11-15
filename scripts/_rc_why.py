from _game import tools
lua = ("local s=game.surfaces.nauvis local W=defines.wire_connector_id local function at(n,x,y) return s.find_entities_filtered{name=n,position={x,y},radius=0.4}[1] end "
       "local rp=s.find_entities_filtered{name='roboport',position={-352,-229},radius=1}[1] local net=rp.logistic_network local o={} "
       "local dem=rp.get_circuit_network(W.circuit_red) local function dv(n) return dem and dem.get_signal({type='item',name=n}) or 0 end "
       "for _,n in pairs{'fast-underground-belt','underground-belt','transport-belt','iron-gear-wheel','iron-plate'} do o[#o+1]=n..' stock '..net.get_item_count(n)..' missing '..dv(n) end "
       "for u=0,2 do local ox=7*u local sel=at('selector-combinator',-354+ox+6.5,-223) local rq=at('requester-chest',-354+ox+2.5,-224.5) local am=at('assembling-machine-3',-354+ox+2.5,-221.5) "
       "local si=sel.get_circuit_network(W.combinator_input_red) local function sv(n) return si and si.get_signal({type='item',name=n}) or 0 end "
       "local inv={} for _,c in pairs(rq.get_inventory(defines.inventory.chest).get_contents()) do inv[#inv+1]=c.name..' '..c.count end local ai={} for _,c in pairs(am.get_inventory(defines.inventory.crafter_input).get_contents()) do ai[#ai+1]=c.name..' '..c.count end "
       "local k='?' for a,v in pairs(defines.entity_status) do if v==am.status then k=a end end "
       "o[#o+1]='m'..(u+1)..' '..k..' score fub '..sv('fast-underground-belt')..' ub '..sv('underground-belt')..' tb '..sv('transport-belt')..' | blue '..table.concat(inv,',')..' | machine in '..table.concat(ai,',') end "
       "rcon.print(table.concat(o,' ;; '))")
print(tools["run_lua"](lua).replace(" ;; ", "\n"))
