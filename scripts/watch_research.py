"""Keep the research queue topped up from a list and report until all are done.
Usage: scripts/watch_research.py tech1,tech2,... [minutes]"""
import json
import sys
import time

from _game import tools

want = [t for t in sys.argv[1].split(",") if t]
minutes = int(sys.argv[2]) if len(sys.argv) > 2 else 40
LUA = """
local f = game.forces.player
local s = game.surfaces.nauvis
local st = {}
for k, v in pairs(defines.entity_status) do st[v] = k end
local q = {}
for i, t in pairs(f.research_queue) do q[i] = t.name end
local labs = {}
for _, l in pairs(s.find_entities_filtered{force='player', name='lab'}) do labs[st[l.status] or '?'] = (labs[st[l.status] or '?'] or 0) + 1 end
local done = {}
for _, n in pairs(%s) do if f.technologies[n].researched then done[#done+1] = n end end
rcon.print(helpers.table_to_json({tick=game.tick, current=f.current_research and f.current_research.name or false,
  progress=math.floor(f.research_progress*100), queue=q, labs=labs, done=done}))
""" % json.dumps(want).replace("[", "{").replace("]", "}")
for _ in range(minutes):
    r = json.loads(tools["run_lua"](" ".join(LUA.splitlines())))
    missing = [t for t in want if t not in r["done"] and t not in r["queue"] and t != r["current"]]
    if missing and len(r["queue"]) < 7:
        r["queued_now"] = tools["queue_research"](",".join(missing[: 7 - len(r["queue"])]))
    print(json.dumps(r), flush=True)
    if len(r["done"]) == len(want):
        print("ALL DONE", flush=True)
        break
    time.sleep(60)
