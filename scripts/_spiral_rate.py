"""Read only: chunks crushed by each wheel's spiral over a window (default 120 s), next to an estimate of the metallic chunks that
passed on the west spoke (sampled every 10 s on the 100 tiles before the tap). Usage: _spiral_rate.py [seconds]"""
import sys
import time

from _game import tools
from _wheels import wheels

SECS = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 120
LUA = ("local s=game.surfaces['SURF'] local m,o=0,0 for _,c in pairs(s.find_entities_filtered{name='crusher',area={{-108,-31},{-92,-27}}}) do local r=c.get_recipe() if r and r.name:find('metallic',1,true) then m=m+c.products_finished else o=o+c.products_finished end end "
       "local n=0 for _,e in pairs(s.find_entities_filtered{type={'transport-belt','underground-belt'},area={{-160,-1},{-60,0}}}) do for l=1,e.get_max_transport_line_index() do n=n+e.get_transport_line(l).get_item_count('metallic-asteroid-chunk') end end "
       "local t=s.find_entities_filtered{name='storage-tank',position={-84.5,-36.5},radius=0.5}[1] rcon.print(m..' '..o..' '..n..' '..game.tick..' '..math.floor(t and t.get_fluid_count('molten-iron') or -1))")
ws = wheels()
first, samples = {}, {}
t0 = time.time()
while True:
    for name, planet, surface, turrets in ws:
        m, o, n, tick, tank = (int(v) for v in tools["run_lua"](LUA.replace("SURF", surface)).split())
        first.setdefault(name, (m, o, tick))
        samples.setdefault(name, []).append(n)
        last = (m, o, tick, tank)
        samples[name + "_last"] = last
    if time.time() - t0 >= SECS:
        break
    time.sleep(10)
for name, planet, surface, turrets in ws:
    m0, o0, k0 = first[name]
    m1, o1, k1, tank = samples[name + "_last"]
    mins = (k1 - k0) / 3600.0
    avg = sum(samples[name]) / len(samples[name])
    print("%-15s %.1f game minutes: spiral crushed %.1f metallic and %.1f oxide chunks a minute; west spoke carries about %.1f metallic chunks a minute past the tap (%.1f on 100 tiles); tank %d"
          % (name, mins, (m1 - m0) / mins if mins else 0, (o1 - o0) / mins if mins else 0, avg * 3.375, avg, tank))
