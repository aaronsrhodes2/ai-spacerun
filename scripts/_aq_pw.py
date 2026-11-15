"""Electric network flow sampler for Aquilo: prints MW produced/consumed per type over a real-time window."""
import sys, time
from _game import tools
L = tools["run_lua"]
LUA = ("local s=game.surfaces.aquilo local p=s.find_entities_filtered{type='electric-pole',limit=1}[1] local st=p.electric_network_statistics local o={game.tick} "
       "for n,v in pairs(st.input_counts) do o[#o+1]='i|'..n..'|'..string.format('%.0f',v) end for n,v in pairs(st.output_counts) do o[#o+1]='o|'..n..'|'..string.format('%.0f',v) end rcon.print(table.concat(o,' '))")
def snap():
    p = L(LUA).split()
    return int(p[0]), {t: float(t2) for t, t2 in (x.rsplit("|", 1) for x in p[1:])}
secs = float(sys.argv[1]) if len(sys.argv) > 1 else 20
t0, a = snap(); time.sleep(secs); t1, b = snap()
dt = (t1 - t0) / 60.0
print("game seconds", dt)
for k in sorted(b):
    d = (b[k] - a.get(k, 0)) / dt / 1e6
    if abs(d) > 0.005:
        print("%-40s %8.2f MW" % (k, d))
