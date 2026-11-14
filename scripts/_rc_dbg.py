import time

from _game import tools

pick = ("local s=game.surfaces.nauvis local W=defines.wire_connector_id local am=s.find_entities_filtered{name='assembling-machine-3',position={-350.5,-241.5},radius=0.6}[1] "
        "local b=am.get_or_create_control_behavior() local r=am.get_recipe() local n=am.get_circuit_network(W.circuit_green) local t={} if n and n.signals then for _,x in pairs(n.signals) do t[#t+1]=x.signal.name..'='..x.count end end "
        "local k='?' for a,v in pairs(defines.entity_status) do if v==am.status then k=a end end "
        "rcon.print('status '..k..' recipe '..(r and r.name or 'none')..' read_ing='..tostring(b.circuit_read_ingredients)..' set='..tostring(b.circuit_set_recipe)..' wire: '..table.concat(t,', '))")
print(tools["run_lua"](pick))
