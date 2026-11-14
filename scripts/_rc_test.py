import sys
import time

from _game import tools

X, Y = -350.5, -241.5
specs = [a.split(':') for a in sys.argv[1:]]
specs = [(x[0].split('=')[-1], x[1], x[0].split('=')[0] if '=' in x[0] else 'item') for x in specs]
slots = ''.join("sec.set_slot(%d,{value={type='%s',name='%s',quality='%s'},min=1}) " % (i+1, t, a, b) for i,(a,b,t) in enumerate(specs))
setup = ("local s=game.surfaces.nauvis local W=defines.wire_connector_id "
         "local am=s.find_entities_filtered{name='assembling-machine-3',position={AX,AY},radius=0.6}[1] "
         "local cc=s.find_entities_filtered{name='constant-combinator',position={-347.5,-242.5},radius=0.4}[1] "
         "local cb=cc.get_or_create_control_behavior() while cb.sections_count>0 do cb.remove_section(1) end local sec=cb.add_section() "
         + slots +
         "cc.get_wire_connector(W.circuit_green,true).connect_to(am.get_wire_connector(W.circuit_green,true),false) "
         "local ab=am.get_or_create_control_behavior() ab.circuit_set_recipe=true ab.circuit_read_ingredients=true "
         "rcon.print('set')")
setup = setup.replace('AX', str(X)).replace('AY', str(Y))
print(tools["run_lua"](setup))
time.sleep(3)
read = ("local s=game.surfaces.nauvis local W=defines.wire_connector_id local am=s.find_entities_filtered{name='assembling-machine-3',position={%s,%s},radius=0.6}[1] "
        "local r,rq=am.get_recipe() local n=am.get_circuit_network(W.circuit_green) local t={} if n and n.signals then for _,x in pairs(n.signals) do t[#t+1]=(x.signal.type or 'item')..':'..x.signal.name..'/'..(x.signal.quality or 'n')..'='..x.count end end "
        "rcon.print('recipe '..(r and (r.name..' q='..tostring(rq and rq.name)) or 'none')..' | wire: '..table.concat(t,', '))") % (X, Y)
for _ in range(3):
    print(tools["run_lua"](read))
    time.sleep(2)
