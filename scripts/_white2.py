"""Read only: White Science detail: crushers (recipe, output), furnaces, assemblers, inserters with pickup/drop targets."""
import sys

from _game import tools

S = sys.argv[1] if len(sys.argv) > 1 else "platform-1"
AREA = sys.argv[2] if len(sys.argv) > 2 else None
area = (",area=%s" % AREA) if AREA else ""
lua = (
    "local s=game.surfaces['%s'] local o={} local function sn(v) for n,x in pairs(defines.entity_status) do if x==v then return n end end return '?' end "
    "local function inv(e,id) local i=e.get_inventory(id) if not i then return '' end local c={} for _,it in pairs(i.get_contents()) do c[#c+1]=it.name..' '..it.count end return table.concat(c,',') end "
    "for _,e in pairs(s.find_entities_filtered{type={'assembling-machine','furnace'}%s}) do local rc=e.get_recipe() "
    "o[#o+1]=e.name..' '..e.position.x..','..e.position.y..' '..(rc and rc.name or '-')..' '..sn(e.status)..' in['..inv(e,defines.inventory.crafter_input)..'] out['..inv(e,defines.inventory.crafter_output)..']' end "
    "for _,e in pairs(s.find_entities_filtered{type='inserter'%s}) do local f={} if e.use_filters then for k=1,e.filter_slot_count do local x=e.get_filter(k) if x then f[#f+1]=x.name end end end "
    "local pt=e.pickup_target local dt=e.drop_target local cb=e.get_control_behavior() local cond='' if cb and cb.circuit_enable_disable then local c=cb.circuit_condition cond=' cond '..(c.first_signal and c.first_signal.name or '?')..c.comparator..tostring(c.constant or (c.second_signal and c.second_signal.name)) end "
    "o[#o+1]=e.name..' '..e.position.x..','..e.position.y..' '..sn(e.status)..' '..(pt and pt.name or 'nil')..'->'..(dt and dt.name or 'nil')..' ['..table.concat(f,',')..']'..cond..(e.held_stack.valid_for_read and (' holds '..e.held_stack.name) or '') end "
    "rcon.print(table.concat(o,'\\n'))" % (S, area, area))
print(tools["run_lua"](lua))
