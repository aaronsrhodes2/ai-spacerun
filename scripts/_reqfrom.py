"""Print the raw space-pack request filter of one Nauvis-Gleba shuttle (to see how request_from reads back)."""
from _game import tools
LUA = "local f=game.forces.player for i,p in pairs(f.platforms) do if p.name:find('Nauvis-Gleba 4',1,true) then for si,se in pairs(p.hub.get_logistic_sections().sections) do for k,fl in pairs(se.filters) do if fl.value and fl.value.name=='space-science-pack' then rcon.print(si..'/'..k..' '..serpent.line(fl)..' slot '..serpent.line(se.get_slot(k))) end end end end end"
print(tools["run_lua"](LUA))
