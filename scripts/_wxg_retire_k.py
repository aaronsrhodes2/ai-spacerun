"""One-off (2026-11-14): take out the export cell's first supply, the taps on belt K's feed column and their combinators (all built
by wheel_export_gleba.py the same day), and take the cell's red wires off K's belts. What the taps hold goes back into the hub.
Why: sharing K's feed with blue science could not be made safe (see the docstring of wheel_export_gleba.py). Usage: _wxg_retire_k.py [SURFACE]"""
import sys

from _game import tools
import wheel_blue

SURF = sys.argv[1] if len(sys.argv) > 1 else "platform-12"
wheel_blue.layout()
K = "{" + ",".join("{%d,%d}" % t for t in wheel_blue.lines["K"]) + "}"
print(tools["run_lua"](("local s=game.surfaces['SURF'] local hub=s.platform.hub local n,held=0,0 for y=-12,-3 do local i=s.find_entities_filtered{name='long-handed-inserter',position={55.5,y+0.5},radius=0.3}[1] if i then if i.held_stack.valid_for_read then held=held+i.held_stack.count hub.insert{name=i.held_stack.name,count=i.held_stack.count,quality=i.held_stack.quality} end i.destroy() n=n+1 end end "
                        "local c=0 for _,p in pairs{{56.5,-4},{56.5,-6},{56.5,-8},{56.5,-10},{56.5,-12},{55.5,-13},{56.5,-2}} do for _,e in pairs(s.find_entities_filtered{type={'decider-combinator','arithmetic-combinator'},position=p,radius=0.6}) do e.destroy() c=c+1 end end "
                        "local w=0 for _,p in pairs(KT) do local b=s.find_entities_filtered{type='transport-belt',position={p[1]+0.5,p[2]+0.5},radius=0.3}[1] if b then local cn=b.get_wire_connector(defines.wire_connector_id.circuit_red,false) if cn and cn.connection_count>0 then cn.disconnect_all() w=w+1 end end end "
                        "rcon.print('taps removed '..n..' (held items returned '..held..'), combinators removed '..c..', K belts freed of red wires '..w)").replace("SURF", SURF).replace("KT", K)))
