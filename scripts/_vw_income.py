"""Read only: chunk income of a wheel from the crushers' craft counts over a window (seconds, default 90).
used[k] = crafts that took a chunk of kind k (crushing + reprocessing); returned[k] = chunks handed back by reprocessing (expected value);
net income = used - returned. Also lists the crushers near the centre with recipe and position (flag `list`)."""
import json
import sys
import time

from _game import tools

S = "platform-17"
secs = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 90
SNAP = ("local s=game.surfaces['%s'] local t={} for _,c in pairs(s.find_entities_filtered{name='crusher'}) do local rc=c.get_recipe() if rc then local d=c.position.x*c.position.x+c.position.y*c.position.y "
        "local k=rc.name..(d<56*56 and '@centre' or (c.position.y>20 and '@district' or '@spiral')) t[k]=(t[k] or 0)+c.products_finished end end t.tick=game.tick rcon.print(helpers.table_to_json(t))" % S)
if "list" in sys.argv:
    print(tools["run_lua"]("local s=game.surfaces['%s'] local o={} for _,c in pairs(s.find_entities_filtered{name='crusher'}) do local rc=c.get_recipe() local st='?' for n,v in pairs(defines.entity_status) do if v==c.status then st=n end end "
                           "o[#o+1]=string.format('%%.1f,%%.1f %%s %%s',c.position.x,c.position.y,rc and rc.name or 'none',st) end table.sort(o) rcon.print(table.concat(o,'\\n'))" % S))
    sys.exit()
a = json.loads(tools["run_lua"](SNAP))
time.sleep(secs)
b = json.loads(tools["run_lua"](SNAP))
mins = (b["tick"] - a["tick"]) / 3600
print("game minutes %.2f" % mins)
used = {"metallic": 0, "carbonic": 0, "oxide": 0}
back = {"metallic": 0, "carbonic": 0, "oxide": 0}
for k in sorted(b):
    if k == "tick":
        continue
    d = (b[k] - a.get(k, 0)) / mins
    print("  %-52s %7.1f crafts a minute" % (k, d))
    kind = [n for n in used if n in k.split("@")[0]][0]
    used[kind] += d
    if "reprocessing" in k:
        for n in back:
            back[n] += d * (0.4 if n == kind else 0.2)
for n in used:
    print("%s: used %.0f, handed back by reprocessing %.0f, net income %.0f a minute" % (n, used[n], back[n], used[n] - back[n]))
