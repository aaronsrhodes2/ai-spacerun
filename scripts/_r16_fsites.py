"""Find clear 26 x 20 patches on Fulgora inside the main logistic network, closest to the rocket silo; confirm with the real placement dry-run."""
import json

import omni_maker as M
from _game import tools

LUA = r'''
local s = game.surfaces.fulgora
local f = game.forces.player
local silo = s.find_entities_filtered{type = 'rocket-silo'}[1]
local sx, sy = silo.position.x, silo.position.y
local best = {}
local mainid = nil
local big = 0
for _, rp in pairs(s.find_entities_filtered{name = 'roboport'}) do
  local n = rp.logistic_network
  if n and #n.cells > big then big = #n.cells mainid = n.network_id end
end
for x = 60, 260, 2 do
  for y = -260, -60, 2 do
    local area = {{x, y}, {x + 26, y + 20}}
    if s.count_entities_filtered{area = area, type = {'resource', 'tree', 'corpse', 'projectile'}, invert = true} == 0 then
      local nets = s.find_logistic_networks_by_construction_area({x + 13, y + 10}, f)
      local inmain = false
      for _, n in pairs(nets) do if n.network_id == mainid then inmain = true end end
      if inmain then
        local ok = true
        for _, p in ipairs({{x, y}, {x + 25, y}, {x, y + 19}, {x + 25, y + 19}, {x + 12, y + 10}}) do
          if not s.can_place_entity{name = 'wooden-chest', position = {p[1] + 0.5, p[2] + 0.5}, force = f, build_check_type = defines.build_check_type.manual} then ok = false end
        end
        if ok then best[#best + 1] = {x = x, y = y, d = math.sqrt((x + 13 - sx) ^ 2 + (y + 10 - sy) ^ 2)} end
      end
    end
  end
end
table.sort(best, function(a, b) return a.d < b.d end)
local o = {}
for i = 1, math.min(12, #best) do o[#o + 1] = best[i].x .. ',' .. best[i].y .. ',' .. string.format('%.0f', best[i].d) end
rcon.print(#best .. ';' .. table.concat(o, ';'))
'''

if __name__ == "__main__":
    out = tools["run_lua"](LUA).strip().split(";")
    print("candidate patches:", out[0])
    for c in out[1:]:
        x, y, d = (int(v) for v in c.split(","))
        M.SITES["fulgora"] = (x, y)
        ents = M.layout("fulgora") + M.stock_stage("fulgora")
        r = json.loads(tools["place_entities"](json.dumps(ents), surface="fulgora", dry_run=True))
        print(f"  ({x},{y}) {d} tiles from the silo: placeable {r.get('placed')}, failed {len(r.get('failed') or [])}", ("" if not r.get("failed") else json.dumps(r["failed"][:1])[:160]))
