import time

from _game import tools

print(tools["run_lua"]("local s=game.surfaces.nauvis local cc=s.find_entities_filtered{name='constant-combinator',position={-347.5,-242.5},radius=0.4}[1] "
                       "local cb=cc.get_or_create_control_behavior() while cb.sections_count>0 do cb.remove_section(1) end rcon.print('cleared')"))
time.sleep(3)
print(tools["run_lua"]("local s=game.surfaces.nauvis local W=defines.wire_connector_id local am=s.find_entities_filtered{name='assembling-machine-3',position={-350.5,-241.5},radius=0.6}[1] "
                       "local r=am.get_recipe() local n=am.get_circuit_network(W.circuit_green) local t={} if n and n.signals then for _,x in pairs(n.signals) do t[#t+1]=x.signal.name..'='..x.count end end "
                       "rcon.print('recipe '..(r and r.name or 'none')..' | wire: '..table.concat(t,', '))"))
