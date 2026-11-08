"""
Make ore effectively unlimited, because the Captain asked (2026-11-07): the nearby patches
mined out while drills ran flat out.

  1. Every finite ore entity (iron, copper, coal, stone, uranium) on nauvis is topped up to
     AMOUNT, which is below the engine's uint32 limit.
  2. Tiles that have already been mined out are re-created from the pre-build map snapshot
     (snapshots/first-mines-prebuild-grid.json: letters i/c/k/s = ore). Existing entities
     keep their place; only empty tiles get a new ore entity.
  3. Crude oil is left alone unless it has fallen under 100% yield; then it's reset to 300%.

Run again whenever drills report no_minable_resources.   Usage: scripts/unlimited_resources.py
"""
import json
from pathlib import Path

from _game import tools

AMOUNT = 2_000_000_000
ORES = {"i": "iron-ore", "c": "copper-ore", "k": "coal", "s": "stone", "u": "uranium-ore"}
SNAP = Path(__file__).resolve().parent.parent / "snapshots" / "first-mines-prebuild-grid.json"


def lua(code):
    return tools["run_lua"](" ".join(code.splitlines()))


# 1. top up everything that still exists
for name in ORES.values():
    print(name, lua(f"""
        local n = 0
        for _, e in pairs(game.surfaces.nauvis.find_entities_filtered{{name='{name}'}}) do e.amount = {AMOUNT} n = n + 1 end
        rcon.print(n)
    """), "tiles topped up")

# 2. re-create mined-out tiles from the snapshot
snap = json.loads(SNAP.read_text())
tiles = []
for dy, row in enumerate(snap["rows"]):
    for dx, ch in enumerate(row):
        if ch in ORES:
            tiles.append([snap["x1"] + dx, snap["y1"] + dy, ch])
print(len(tiles), "ore tiles in the snapshot")
made = 0
for i in range(0, len(tiles), 1200):
    chunk = tiles[i:i + 1200]
    r = lua(f"""
        local s = game.surfaces.nauvis
        local names = {{i='iron-ore', c='copper-ore', k='coal', s='stone', u='uranium-ore'}}
        local list = helpers.json_to_table([==[{json.dumps(chunk, separators=(',', ':'))}]==])
        local made = 0
        for _, t in pairs(list) do
          local x, y = t[1], t[2]
          if #s.find_entities_filtered{{type='resource', area={{{{x + 0.1, y + 0.1}}, {{x + 0.9, y + 0.9}}}}}} == 0 then
            if s.create_entity{{name=names[t[3]], position={{x + 0.5, y + 0.5}}, amount={AMOUNT}}} then made = made + 1 end
          end
        end
        rcon.print(made)
    """)
    made += int(r) if r.isdigit() else 0
print(made, "mined-out tiles re-created")

# 3. oil
print("oil:", lua("""
local n = 0
for _, e in pairs(game.surfaces.nauvis.find_entities_filtered{name='crude-oil'}) do
  if e.amount < 300000 then e.amount = 900000 n = n + 1 end
end
rcon.print(n .. ' wells reset to 300%')
"""))
