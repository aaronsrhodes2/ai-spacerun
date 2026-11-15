"""Gleba site choice: land patches in the main logistic network confirmed with real placement tests (wetlands are unbuildable), then the real dry-runs for the
depth-2 maker unit (omni_maker) and the biochamber barrel unit (omni_fluid_asm)."""
import math
import subprocess
import sys

from _game import tools

F = ("RCON", "tunnel", "172.18", "INFO", "aaron_s")


def run(*args):
    r = subprocess.run([sys.executable, "-u", *args], capture_output=True, text=True, encoding="utf-8")
    return "\n".join(l for l in r.stdout.splitlines() if not any(k in l for k in F))


LUA = r'''
local s = game.surfaces.gleba
local f = game.forces.player
local silo = s.find_entities_filtered{type = 'rocket-silo'}[1]
local sx, sy = silo.position.x, silo.position.y
local big, mainid = 0, nil
for _, rp in pairs(s.find_entities_filtered{name = 'roboport'}) do local n = rp.logistic_network if n and #n.cells > big then big = #n.cells mainid = n.network_id end end
local W, H = WW, HH
local out = {}
for x = XMIN, XMAX, 2 do for y = YMIN, YMAX, 2 do
  local ok = true
  for gx = 0, W - 1, 3 do for gy = 0, H - 1, 3 do
    if not s.can_place_entity{name = 'steel-chest', position = {x + gx + 0.5, y + gy + 0.5}, force = f, build_check_type = defines.build_check_type.manual} then ok = false break end
  end if not ok then break end end
  if ok then
    local nets = s.find_logistic_networks_by_construction_area({x + W / 2, y + H / 2}, f)
    for _, n in pairs(nets) do if n.network_id == mainid then out[#out + 1] = {x, y, math.sqrt((x + W / 2 - sx) ^ 2 + (y + H / 2 - sy) ^ 2)} break end end
  end
end end
table.sort(out, function(a, b) return a[3] < b[3] end)
local o = {}
for i = 1, math.min(60, #out) do o[#o + 1] = out[i][1] .. ',' .. out[i][2] end
rcon.print(table.concat(o, ';'))
'''


def patches(w, h, box):
    code = LUA.replace("WW", str(w)).replace("HH", str(h)).replace("XMIN", str(box[0])).replace("XMAX", str(box[1])).replace("YMIN", str(box[2])).replace("YMAX", str(box[3]))
    return [tuple(int(v) for v in p.split(",")) for p in tools["run_lua"](code).strip().split(";") if p]


BOX = (60, 260, -120, 130)
chosen = {}
pm = patches(17, 27, BOX)
print(len(pm), "patches 17x27 (maker unit)")
for px, py in pm:
    out = run("omni_maker.py", "build", "gleba", "--at", str(px), str(py))
    if "failed []" in out:
        chosen["maker"] = (px, py)
        print("maker clean at", (px, py), out.strip()[:80])
        break
pb = patches(15, 16, BOX)
print(len(pb), "patches 15x16 (biochamber unit)")
for px, py in pb:
    if "maker" in chosen and math.hypot(px - chosen["maker"][0], py - chosen["maker"][1]) < 30:
        continue
    cx, cy = px + 9, py + 8
    out = run("omni_fluid_asm.py", "build", "--at", str(cx), str(cy), "--planet", "gleba", "--maker", "biochamber", "--solid", "--menu", "carbon-fiber,rocket-fuel",
              "--recipes", "carbon-fiber,rocket-fuel-from-jelly", "--demand", "0", "0", "--fuel", "nutrients:20")
    if "failed []" in out:
        chosen["biochamber"] = (cx, cy)
        print("biochamber clean at", (cx, cy), out.strip()[:80])
        break
print("chosen:", chosen)
