#!/usr/bin/env python3
"""Read-only: what the other platforms in Nauvis orbit ask for in iron ore, carbon and ice (and whether they may take it from platforms). This is the
information an 'automatic mode from the other hubs' requests' path would read; the strip miner itself follows its hub stock instead (see triangle_miner.py).
Usage: _triangle_demand.py"""
from _game import tools

LUA = ("local o={} for i,p in pairs(game.forces.player.platforms) do local h=p.hub if h and h.valid then local loc=p.space_location and p.space_location.name or 'transit' "
       "local want={} local ok=pcall(function() for si,se in pairs(h.get_logistic_sections().sections) do if se.active then for k,fl in pairs(se.filters) do if fl.value and (fl.value.name=='ice' or fl.value.name=='carbon' or fl.value.name=='iron-ore') then "
       "want[#want+1]=fl.value.name..' min '..tostring(fl.min)..' max '..tostring(fl.max)..' from '..tostring(fl.value.request_from) end end end end end) "
       "o[#o+1]=(p.name:gsub('^%[.-%]%s*',''))..' @'..loc..' provides='..tostring(h.providing_to_other_platforms)..' | '..table.concat(want,'; ') end end rcon.print(table.concat(o,' ## '))")

for line in tools["run_lua"](LUA).split(" ## "):
    print(line)
