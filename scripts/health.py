"""One-minute health report: power, coal, smelting, drills, gears, science chains, labs, and
measured items per minute. Run it whenever something looks off, and after every build.

Usage: scripts/health.py [seconds]   (default 60: the length of the rate measurement)"""
import json
import sys
import time

from _game import tools

secs = int(sys.argv[1]) if len(sys.argv) > 1 else 60
ITEMS = ["iron-ore", "copper-ore", "coal", "stone", "iron-plate", "copper-plate", "iron-gear-wheel",
         "electronic-circuit", "automation-science-pack", "logistic-science-pack"]

STATE = """
local s = game.surfaces.nauvis
local f = game.forces.player
local st = {}
for k, v in pairs(defines.entity_status) do st[v] = k end
local function group(filter)
  local c = {}
  for _, e in pairs(s.find_entities_filtered(filter)) do local k = st[e.status] or '?' c[k] = (c[k] or 0) + 1 end
  return c
end
local kw, cap = 0, 0
for _, e in pairs(s.find_entities_filtered{force='player', name='steam-engine'}) do kw = kw + e.energy_generated_last_tick * 60 / 1000 cap = cap + 900 end
local stats = f.get_item_production_statistics(s)
local made, used = {}, {}
for _, n in pairs(%s) do made[n] = stats.get_input_count(n) used[n] = stats.get_output_count(n) end
local packs = {}
for _, e in pairs(s.find_entities_filtered{force='player', type='assembling-machine'}) do
  local r = e.get_recipe() and e.get_recipe().name or '?'
  if r == 'logistic-science-pack' or r == 'automation-science-pack' or r == 'iron-gear-wheel' then
    packs[r] = packs[r] or {}
    packs[r][st[e.status] or '?'] = (packs[r][st[e.status] or '?'] or 0) + 1
  end
end
local lowest = {}
for _, e in pairs(s.find_entities_filtered{force='player', type='assembling-machine'}) do
  local r = e.get_recipe() and e.get_recipe().name or '?'
  if (r == 'inserter' or r == 'transport-belt' or r == 'electronic-circuit' or r == 'copper-cable') and e.status ~= defines.entity_status.full_output and e.status ~= defines.entity_status.working then
    lowest[r .. ':' .. (st[e.status] or '?')] = (lowest[r .. ':' .. (st[e.status] or '?')] or 0) + 1
  end
end
local q = {}
for i, t in pairs(f.research_queue) do q[i] = t.name end
rcon.print(helpers.table_to_json({tick=game.tick, power={gen_kw=math.floor(kw), capacity_kw=cap}, boilers=group{force='player', name='boiler'},
  drills=group{force='player', type='mining-drill'}, furnaces=group{force='player', type='furnace'},
  science=packs, chain_support_stalled=lowest, labs=group{force='player', name='lab'}, made=made, used=used,
  current=f.current_research and f.current_research.name or false, progress=math.floor(f.research_progress*100), queue=q}))
""" % json.dumps(ITEMS).replace("[", "{").replace("]", "}")

def sample():
    return json.loads(tools["run_lua"](" ".join(STATE.splitlines())))

a = sample()
time.sleep(secs)
b = sample()
mins = (b["tick"] - a["tick"]) / 3600
out = {k: b[k] for k in ("power", "boilers", "drills", "furnaces", "science", "chain_support_stalled", "labs", "current", "progress", "queue")}
out["per_minute"] = {n: {"made": round((b["made"][n] - a["made"][n]) / mins), "used": round((b["used"][n] - a["used"][n]) / mins)} for n in ITEMS}
print(json.dumps(out, indent=1))
