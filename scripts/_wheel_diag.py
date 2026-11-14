"""Read only: per wheel, the hub stock, the three blue-line hub inserters (K, O, W) and what lies on each line."""
import sys

import wheel_blue as wb
from _game import tools
from _wheels import wheels

wb.layout()
ITEMS = ["carbon", "sulfur", "calcite", "ice", "iron-ore", "copper-ore", "stone", "iron-plate", "copper-plate", "steel-plate", "coal",
         "iron-gear-wheel", "copper-cable", "space-science-pack", "automation-science-pack", "logistic-science-pack", "chemical-science-pack",
         "military-science-pack", "production-science-pack", "utility-science-pack", "metallic-asteroid-chunk", "carbonic-asteroid-chunk", "oxide-asteroid-chunk"]
HUB = ("local s=game.surfaces['SURF'] local inv=s.platform.hub.get_inventory(defines.inventory.hub_main) local o={} for _,n in pairs({ITEMS}) do o[#o+1]=n..' '..inv.get_item_count(n) end "
       "rcon.print('HUB free '..inv.count_empty_stacks()..'/'..#inv..': '..table.concat(o,', '))")
INS = ("local s=game.surfaces['SURF'] local o={} local function sn(v) for n,x in pairs(defines.entity_status) do if x==v then return n end end return '?' end "
       "for _,q in pairs({{'K',-2.5},{'O',-1.5},{'W',-0.5}}) do local i=s.find_entities_filtered{type='inserter',position={4.5,q[2]},radius=0.3}[1] if i then local f={} for k=1,i.filter_slot_count do local x=i.get_filter(k) if x then f[#f+1]=(x.name or tostring(x)) end end "
       "local sg={} local net=i.get_circuit_network(defines.wire_connector_id.circuit_red) if net and net.signals then for _,g in pairs(net.signals) do sg[#sg+1]=g.signal.name..'='..g.count end end "
       "local h=i.held_stack.valid_for_read and (i.held_stack.name..' x'..i.held_stack.count) or '-' "
       "o[#o+1]=q[1]..' '..i.name..' '..sn(i.status)..' holds '..h..' filters ['..table.concat(f,',')..'] red {'..table.concat(sg,' ')..'}' else o[#o+1]=q[1]..' no inserter' end end rcon.print(table.concat(o,'\\n'))")
LINE = ("local s=game.surfaces['SURF'] local t={} local nb,rd=0,0 for _,p in pairs(TILES) do local e=s.find_entities_filtered{type={'transport-belt','underground-belt'},position=p,radius=0.3}[1] "
        "if e then nb=nb+1 if e.type=='transport-belt' then local cb=e.get_control_behavior() if cb and cb.read_contents then rd=rd+1 end end for l=1,e.get_max_transport_line_index() do for _,it in pairs(e.get_transport_line(l).get_contents()) do t[it.name]=(t[it.name] or 0)+it.count end end end end "
        "local o={} for k,v in pairs(t) do o[#o+1]=k..' '..v end table.sort(o) rcon.print('LINE belts '..nb..' reading '..rd..': '..table.concat(o,', '))")
for name, planet, surface, turrets in wheels():
    print("==", name, surface)
    print(tools["run_lua"](HUB.replace("SURF", surface).replace("ITEMS", ",".join("'%s'" % i for i in ITEMS))))
    print(tools["run_lua"](INS.replace("SURF", surface)))
    for k, tiles in wb.lines.items():
        print(tools["run_lua"](LINE.replace("SURF", surface).replace("LINE", k).replace("TILES", wb.lua_list(tiles))))
