import sys
from _game import tools
L = tools["run_lua"]
DUMP = """local function dump(tag,ent) local o={} for _,pt in pairs(ent.get_logistic_point()) do for _,x in pairs(pt.sections) do local f={} for _,fl in pairs(x.filters) do if fl.value then f[#f+1]=fl.value.name..' '..tostring(fl.min)..'..'..tostring(fl.max)..(fl.import_from and (' from '..tostring(fl.import_from.name or fl.import_from)) or '')..(fl.request_from and fl.request_from~='planet' and (' rf='..fl.request_from) or '') end end o[#o+1]='  mode '..pt.mode..' grp="'..x.group..'" active='..tostring(x.active)..' mult='..tostring(x.multiplier)..' n='..#f..': '..table.concat(f,'; ') end end rcon.print(tag..string.char(10)..table.concat(o,string.char(10))) end """
what = sys.argv[1:]
for w in what:
    if w.startswith("pad:"):
        s = w[4:]
        print(L(DUMP + "dump('%s pad', game.surfaces['%s'].find_entities_filtered{type='cargo-landing-pad'}[1])" % (s, s)))
    else:
        print(L(DUMP + "for _,q in pairs(game.forces.player.platforms) do if q.name:find('%s',1,true) then dump(q.name..' hub',q.hub) local g={} for _,x in pairs(q.schedule and q.schedule.records or {}) do g[#g+1]=tostring(x.station) end rcon.print('  sched: '..table.concat(g,'>')..' providing='..tostring(q.hub.providing_to_other_platforms)) end end" % w))
