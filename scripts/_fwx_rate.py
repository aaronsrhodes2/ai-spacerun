"""Read only: crafts per game minute and share of time working for every machine in an area, sampled over real seconds.
Usage: _fwx_rate.py SURFACE x0 y0 x1 y1 [seconds=60]"""
import sys
import time

from _game import tools

surf, x0, y0, x1, y1 = sys.argv[1:6]
secs = int(sys.argv[6]) if len(sys.argv) > 6 else 60
LUA = ("local s=game.surfaces['%s'] local o={game.tick} for _,c in pairs(s.find_entities_filtered{type={'assembling-machine','furnace'},area={{%s,%s},{%s,%s}}}) do local rc=c.get_recipe() "
       "local k='?' for n,x in pairs(defines.entity_status) do if x==c.status then k=n end end o[#o+1]=string.format('%%.1f,%%.1f|%%s|%%d|%%s',c.position.x,c.position.y,rc and rc.name or 'none',c.products_finished,k) end rcon.print(table.concat(o,';'))") % (surf, x0, y0, x1, y1)


def snap():
    parts = tools["run_lua"](LUA).strip().split(";")
    return int(parts[0]), {p.split("|")[0]: p.split("|")[1:] for p in parts[1:]}


t0, a = snap()
hist = {k: {} for k in a}
n = max(1, secs // 6)
for i in range(n):
    time.sleep(secs / n)
    t1, b = snap()
    for k, v in b.items():
        hist.setdefault(k, {})
        hist[k][v[2]] = hist[k].get(v[2], 0) + 1
mins = (t1 - t0) / 3600.0
print("window %.2f game minutes" % mins)
for k in sorted(b, key=lambda q: b[q][0]):
    if k in a:
        d = int(b[k][1]) - int(a[k][1])
        print("%-34s %-14s %7.1f crafts/min  %s" % (b[k][0], k, d / mins, ", ".join("%s %d%%" % (s, 100 * c // n) for s, c in sorted(hist[k].items(), key=lambda q: -q[1]))))
