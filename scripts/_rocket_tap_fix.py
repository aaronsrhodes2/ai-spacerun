"""One-off (2026-11-14): move the gate of the rocket district's metallic tap (-66.5,0.5) from the spiral in-belt's dead end to the tile
before the first metallic intake (-106.5,-26.5), on every wheel. The same change is in wheel_rocket.py `config`. Usage: _rocket_tap_fix.py [--only PLANET]"""
from _game import tools
from _wheels import wheels

LUA = ("local s=game.surfaces['SURF'] local W=defines.wire_connector_id local function at(t,x,y) return s.find_entities_filtered{type=t,position={x,y},radius=0.3}[1] end "
       "local i=at('inserter',-66.5,0.5) local b=at('transport-belt',-106.5,-26.5) if not i or not b then rcon.print('tap or belt missing') return end "
       "local bc=b.get_or_create_control_behavior() bc.read_contents=true bc.read_contents_mode=defines.control_behavior.transport_belt.content_read_mode.hold b.get_wire_connector(W.circuit_red,true).disconnect_all() "
       "local c=i.get_wire_connector(W.circuit_red,true) c.disconnect_all() c.connect_to(b.get_wire_connector(W.circuit_red,true),false) local cb=i.get_or_create_control_behavior() cb.circuit_enable_disable=true "
       "cb.circuit_condition={first_signal={type='item',name='metallic-asteroid-chunk'},comparator='>=',constant=4} local st='?' for n,v in pairs(defines.entity_status) do if v==i.status then st=n end end "
       "local net=i.get_circuit_network(W.circuit_red) rcon.print('metallic tap rewired, belt dir '..b.direction..', sees metallic '..(net and net.get_signal({type='item',name='metallic-asteroid-chunk'}) or -1))")
for name, planet, surface, turrets in wheels():
    print("==", name, tools["run_lua"](LUA.replace("SURF", surface)).strip())
