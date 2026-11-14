"""Read only: machines and inserters in an area of a surface. Usage: _vw_diag.py SURFACE x0 y0 x1 y1 [m|i|mi]"""
import sys

from _game import tools

S, x0, y0, x1, y1 = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
what = sys.argv[6] if len(sys.argv) > 6 else "mi"
PRE = ("local s=game.surfaces['%s'] local A={{%s,%s},{%s,%s}} local function sn(e) for n,x in pairs(defines.entity_status) do if x==e.status then return n end end return '?' end local o={} " % (S, x0, y0, x1, y1))
M = ("for _,e in pairs(s.find_entities_filtered{type={'assembling-machine','furnace'},area=A}) do local rc=e.get_recipe() local t={} "
     "for _,id in pairs{defines.inventory.crafter_input,defines.inventory.crafter_output} do local inv=e.get_inventory(id) if inv then for _,it in pairs(inv.get_contents()) do t[#t+1]=it.name..' '..it.count end end end "
     "for k,v in pairs(e.get_fluid_contents()) do t[#t+1]=k..' '..math.floor(v) end local mo={} local mi=e.get_module_inventory() if mi then for _,it in pairs(mi.get_contents()) do mo[#mo+1]=it.name:sub(1,4)..it.name:sub(-1)..'x'..it.count..(it.quality and it.quality:sub(1,1) or '') end end "
     "o[#o+1]=string.format('%s %.1f,%.1f d%d %s %s made %d [%s] mod(%s) %s',e.name,e.position.x,e.position.y,e.direction,rc and rc.name or 'NO RECIPE',sn(e),e.products_finished,table.concat(t,', '),table.concat(mo,','),e.quality.name) end ")
I = ("for _,e in pairs(s.find_entities_filtered{type='inserter',area=A}) do local f={} if e.use_filters then for k=1,e.filter_slot_count do local q=e.get_filter(k) if q then f[#f+1]=type(q)=='table' and q.name or q end end end "
     "local cb=e.get_control_behavior() local c='' if cb and cb.circuit_enable_disable then local cc=cb.circuit_condition c=' cond '..(cc.first_signal and cc.first_signal.name or '?')..cc.comparator..tostring(cc.constant) end "
     "local pt,dt=e.pickup_target,e.drop_target o[#o+1]=string.format('%s %.1f,%.1f d%d %s [%s]%s %s -> %s',e.name,e.position.x,e.position.y,e.direction,sn(e),table.concat(f,','),c,pt and pt.name or '-',dt and dt.name or '-') end ")
code = PRE + (M if "m" in what else "") + (I if "i" in what else "") + "rcon.print(table.concat(o,'\\n'))"
print(tools["run_lua"](code))
