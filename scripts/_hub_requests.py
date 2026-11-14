"""Read only: every request section of a platform hub (default: the four wheels). Usage: _hub_requests.py [surface ...]"""
import sys

from _game import tools
from _wheels import wheels

LUA = ("local s=game.surfaces['SURF'] local h=s.platform.hub local o={} for pi,lp in pairs(h.get_logistic_point()) do for si,sec in pairs(lp.sections) do local rq={} for i,fl in pairs(sec.filters) do if fl.value then "
       "rq[#rq+1]=fl.value.name..':'..(fl.min or 0)..'/'..tostring(fl.max)..(fl.import_from and ('@'..fl.import_from.name) or '')..(fl.request_from and ('<'..tostring(fl.request_from)) or '')..(fl.minimum_delivery_count and (' md'..fl.minimum_delivery_count) or '') end end "
       "o[#o+1]='point '..pi..' section '..si..' group['..(sec.group or '')..'] active '..tostring(sec.active)..' mult '..sec.multiplier..': '..table.concat(rq,' ') end end "
       "o[#o+1]='providing_to_other_platforms '..tostring(h.providing_to_other_platforms)..' paused '..tostring(s.platform.paused) rcon.print(table.concat(o,'\\n'))")
surfaces = sys.argv[1:] or [w[2] for w in wheels()]
for s in surfaces:
    print("==", s)
    print(tools["run_lua"](LUA.replace("SURF", s)))
