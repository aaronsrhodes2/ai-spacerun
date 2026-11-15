"""Choose three non-overlapping clean sites on Vulcanus (main logistic network, land) for: the solid maker unit (omni_maker), the assembler barrel unit and the foundry barrel unit."""
import json
import math
import subprocess
import sys

from _game import tools

HERE = "."


def run(*args):
    r = subprocess.run([sys.executable, "-u", *args], capture_output=True, text=True, encoding="utf-8")
    return "\n".join(l for l in r.stdout.splitlines() if not any(k in l for k in ("RCON", "tunnel", "172.18", "INFO", "aaron_s")))


LUA = r'''
local s = game.surfaces.vulcanus
local f = game.forces.player
local silo = s.find_entities_filtered{type = 'rocket-silo'}[1]
local sx, sy = silo.position.x, silo.position.y
local big, mainid = 0, nil
for _, rp in pairs(s.find_entities_filtered{name = 'roboport'}) do local n = rp.logistic_network if n and #n.cells > big then big = #n.cells mainid = n.network_id end end
local function land(x, y) local t = s.get_tile(x, y).name return not (t:find('oil') or t:find('out%-of%-map') or t:find('lava') or t:find('water')) end
local out = {}
local W, H = 16, 15
for x = -160, 100, 2 do for y = -160, 120, 2 do
  local ok = true
  for gx = 0, W - 1, 3 do for gy = 0, H - 1, 3 do if not land(x + gx, y + gy) then ok = false break end end if not ok then break end end
  if ok and land(x + W - 1, y + H - 1) then
    local area = {{x, y}, {x + W, y + H}}
    if s.count_entities_filtered{area = area, type = {'resource', 'tree', 'corpse', 'projectile', 'simple-entity', 'decorative', 'cliff'}, invert = true} == 0 and s.count_entities_filtered{area = area, type = 'cliff'} == 0 then
      local nets = s.find_logistic_networks_by_construction_area({x + W / 2, y + H / 2}, f)
      for _, n in pairs(nets) do if n.network_id == mainid then out[#out + 1] = {x, y, math.sqrt((x + 8 - sx) ^ 2 + (y + 7 - sy) ^ 2)} break end end
    end
  end
end end
table.sort(out, function(a, b) return a[3] < b[3] end)
local o = {}
for i = 1, math.min(80, #out) do o[#o + 1] = out[i][1] .. ',' .. out[i][2] end
rcon.print(table.concat(o, ';'))
'''

patches = [tuple(int(v) for v in p.split(",")) for p in tools["run_lua"](LUA).strip().split(";") if p]
print(len(patches), "land patches near the Vulcanus silo (closest first)")
chosen = {}
want = ["maker", "assembler", "foundry"]
for px, py in patches:
    if len(chosen) == 3:
        break
    if any(math.hypot(px - c[0], py - c[1]) < 20 for c in chosen.values()):
        continue
    for kind in want:
        if kind in chosen:
            continue
        if kind == "maker":
            out = run("omni_maker.py", "build", "vulcanus", "--at", str(px), str(py))
            ok = "failed []" in out
            site = (px, py)
        elif kind == "assembler":
            cx, cy = px + 8, py + 7
            out = run("omni_fluid_asm.py", "build", "--at", str(cx), str(cy), "--planet", "vulcanus", "--menu", "tungsten-carbide,foundry", "--demand", "0", "0")
            ok = "failed []" in out
            site = (cx, cy)
        else:
            cx, cy = px + 8, py + 6
            out = run("omni_fluid_asm.py", "build", "--at", str(cx), str(cy), "--planet", "vulcanus", "--maker", "foundry", "--menu", "turbo-splitter,turbo-transport-belt,turbo-underground-belt", "--demand", "0", "0")
            ok = "failed []" in out
            site = (cx, cy)
        if ok:
            chosen[kind] = site
            print(f"{kind}: clean at {site}  ({out.strip()[:90]})")
            break
print("chosen:", chosen)
