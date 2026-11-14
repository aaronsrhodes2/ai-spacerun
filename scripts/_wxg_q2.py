"""Scratch (read-only): wires on the K feed column and the ore loop column, free tiles for the export cell's outliers."""
import sys

from _game import tools

SURF = sys.argv[1] if len(sys.argv) > 1 else "platform-12"


def q(lua):
    print(tools["run_lua"](lua.replace("SURF", SURF)).replace("@@", "\n"))


q("local s=game.surfaces['SURF'] local o={} for _,p in pairs{{53,-16},{53,-15},{99,-8},{52,-9}} do local b=s.find_entities_filtered{type='transport-belt',position={p[1]+0.5,p[2]+0.5},radius=0.3}[1] local t=p[1]..','..p[2]..': ' if b then for n,id in pairs{red=defines.wire_connector_id.circuit_red,green=defines.wire_connector_id.circuit_green} do local c=b.get_wire_connector(id,false) t=t..n..' '..(c and c.connection_count or 0)..' ' end local cb=b.get_control_behavior() if cb then t=t..' read='..tostring(cb.read_contents)..' mode='..tostring(cb.read_contents_mode) end "
  "local l={} for i=1,2 do for _,it in pairs(b.get_transport_line(i).get_contents()) do l[#l+1]='lane'..i..' '..it.name..' '..it.count end end t=t..' | '..table.concat(l,', ') else t=t..'no belt' end o[#o+1]=t end rcon.print(table.concat(o,'@@'))")
q("local s=game.surfaces['SURF'] local o={} for _,a in pairs{{50,-9,52,-7},{88,-10,99,-6},{55,-14,57,-2},{70,-15,73,-13}} do local t={} for _,e in pairs(s.find_entities_filtered{area={{a[1],a[2]},{a[3],a[4]}}}) do t[#t+1]=e.name..'@'..e.position.x..','..e.position.y end o[#o+1]=a[1]..','..a[2]..'..'..a[3]..','..a[4]..': '..table.concat(t,' ') end rcon.print(table.concat(o,'@@'))")
