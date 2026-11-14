import omni_fluid
import omni_maker
from _game import tools

print("fluid recipes:", tools["run_lua"](omni_fluid.LIST + "rcon.print(#rs)").strip(), "x 8 deciders")
print("furnace items:", tools["run_lua"]("local f=game.forces.player " + omni_maker.SMELT + "rcon.print(#mk)").strip())
print(tools["run_lua"](omni_fluid.LIST + "local t={} for _,r in pairs(rs) do t[#t+1]=r.key..'('..#r.si..'s,'..#r.fi..'fi,'..#r.fo..'fo)' end rcon.print(table.concat(t,' '))"))
print(tools["run_lua"]("local s=game.surfaces.nauvis local c={} for _,e in pairs(s.find_entities_filtered{area={{-367,-235},{-288,-190}},force='player'}) do c[e.name]=(c[e.name] or 0)+1 end local t={} for k,v in pairs(c) do if k:find('combinator') then t[#t+1]=k..' '..v end end rcon.print(table.concat(t,', '))"))
