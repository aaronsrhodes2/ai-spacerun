"""Read only: every inserter on a wheel that takes from or gives to the hub: position, direction of flow, filters, circuit condition and
whether the condition holds now. Usage: _hub_edge.py [--only PLANET]"""
from _game import tools
from _wheels import wheels

LUA = ("local s=game.surfaces['SURF'] local hub=s.platform.hub local o={} local function sn(v) for n,x in pairs(defines.entity_status) do if x==v then return n end end return '?' end "
       "for _,i in pairs(s.find_entities_filtered{type='inserter',area={{-8,-8},{8,8}}}) do local out=i.pickup_target==hub local into=i.drop_target==hub if out or into then local f={} if i.use_filters then for k=1,i.filter_slot_count do local x=i.get_filter(k) if x then f[#f+1]=x.name end end end "
       "local cb=i.get_control_behavior() local cond='' if cb and cb.circuit_enable_disable then local c=cb.circuit_condition cond=' cond '..(c.first_signal and c.first_signal.name or '?')..c.comparator..tostring(c.constant) end if cb and cb.circuit_set_filters then cond=cond..' (filters by circuit)' end "
       "o[#o+1]=(out and 'OUT ' or 'IN  ')..i.position.x..','..i.position.y..' '..i.name..' '..sn(i.status)..' ['..table.concat(f,',')..']'..cond end end table.sort(o) rcon.print(table.concat(o,' ; '))")
for name, planet, surface, turrets in wheels():
    print("==", name, surface)
    print(tools["run_lua"](LUA.replace("SURF", surface)).replace(" ; ", "\n"))
