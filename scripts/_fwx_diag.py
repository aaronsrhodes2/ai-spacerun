"""Read only: every machine and inserter in an area of a wheel with status, contents, fluids, gate. Usage: _fwx_diag.py SURFACE x0 y0 x1 y1 [mach|ins|all]"""
import sys

from _game import tools

surf, x0, y0, x1, y1 = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
what = sys.argv[6] if len(sys.argv) > 6 else "all"
HEAD = "local s=game.surfaces['%s'] local function sn(e) for n,x in pairs(defines.entity_status) do if x==e.status then return n end end return '?' end local o={} " % surf
AREA = "area={{%s,%s},{%s,%s}}" % (x0, y0, x1, y1)
MACH = (HEAD + "for _,c in pairs(s.find_entities_filtered{type={'assembling-machine','furnace'}," + AREA + "}) do local rc=c.get_recipe() local t={} "
        "for i=1,c.get_max_inventory_index() do local inv=c.get_inventory(i) if inv then for _,it in pairs(inv.get_contents()) do t[#t+1]=it.name..' '..it.count end end end "
        "for k,v in pairs(c.get_fluid_contents()) do t[#t+1]=k..' '..math.floor(v) end "
        "o[#o+1]=string.format('%.1f,%.1f %s %s d%d %s made %d sp %.2f prod %.2f | %s',c.position.x,c.position.y,c.name,rc and rc.name or 'none',c.direction,sn(c),c.products_finished,c.crafting_speed,c.productivity_bonus,table.concat(t,', ')) end rcon.print(table.concat(o,'\\n'))")
INS = (HEAD + "for _,i in pairs(s.find_entities_filtered{type='inserter'," + AREA + "}) do local f={} for k=1,i.filter_slot_count do local x=i.get_filter(k) if x then f[#f+1]=x.name end end "
       "local cb=i.get_control_behavior() local g='' if cb and cb.circuit_enable_disable then local c=cb.circuit_condition local v=0 for _,w in pairs{defines.wire_connector_id.circuit_red,defines.wire_connector_id.circuit_green} do local net=i.get_circuit_network(w) if net and c.first_signal then v=v+net.get_signal(c.first_signal) end end "
       "g=' gate '..(c.first_signal and c.first_signal.name or '?')..c.comparator..tostring(c.constant)..' now '..v end "
       "local h=i.held_stack.valid_for_read and (i.held_stack.name..' x'..i.held_stack.count) or '-' "
       "o[#o+1]=string.format('%.1f,%.1f %s d%d %s holds %s [%s]%s',i.position.x,i.position.y,i.name,i.direction,sn(i),h,table.concat(f,','),g) end rcon.print(table.concat(o,'\\n'))")
if what in ("mach", "all"):
    print(tools["run_lua"](MACH))
if what in ("ins", "all"):
    print(tools["run_lua"](INS))
