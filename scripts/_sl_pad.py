import sys
from _game import tools
L = tools["run_lua"]
for s in sys.argv[1:]:
    print(s, L("local pad=game.surfaces['%s'].find_entities_filtered{type='cargo-landing-pad'}[1] local inv=pad.get_inventory(defines.inventory.cargo_landing_pad_main) local o={} for _,it in pairs(inv.get_contents()) do o[#o+1]=it.name..(it.quality~='normal' and ('/'..it.quality) or '')..'='..it.count end table.sort(o) rcon.print('slots '..#inv..' free '..inv.count_empty_stacks()..' :: '..table.concat(o,', '))" % s))
print(L("local o={} for _,sn in pairs{'nauvis','fulgora','gleba','aquilo'} do for _,e in pairs(game.surfaces[sn].find_entities_filtered{type='rocket-silo'}) do o[#o+1]=sn..' silo '..e.position.x..','..e.position.y..' status '..e.status..' parts '..e.rocket_parts..' auto='..tostring(e.auto_launch) end end rcon.print(table.concat(o,string.char(10)))"))
