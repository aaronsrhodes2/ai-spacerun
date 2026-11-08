"""
Survey everything the Captain has explored: every resource patch, every lake, every enemy nest.
Writes snapshots/survey.json and prints a summary. Run again after more exploration.

Patches use the same flood-fill as find_resource_patches (16-tile cells, 8-connected).
Lakes are connected groups of 32-tile chunks that contain water tiles.
"""
import json
import math
from pathlib import Path

from _game import tools

OUT = Path(__file__).resolve().parent.parent / "snapshots" / "survey.json"
HUB = (-20, -62)


def lua(code):
    return tools["run_lua"](" ".join(code.splitlines()))


chunks = int(lua("local n = 0 for _ in game.surfaces.nauvis.get_chunks() do n = n + 1 end rcon.print(n)"))
print(chunks, "generated chunks")

survey = {"hub": HUB, "patches": {}, "lakes": [], "nests": []}
for ore in ["iron-ore", "copper-ore", "coal", "stone", "uranium-ore", "crude-oil"]:
    d = json.loads(tools["find_resource_patches"](ore.replace("-ore", "-ore"), limit=60))
    rows = []
    for p in d["patches"]:
        c = p["center"]
        rows.append({"x": c["x"], "y": c["y"], "tiles": p["tiles"], "amount": p["amount"],
                     "bbox": [p["x1"], p["y1"], p["x2"], p["y2"]],
                     "dist": round(math.hypot(c["x"] - HUB[0], c["y"] - HUB[1]))})
    rows.sort(key=lambda r: r["dist"])
    survey["patches"][ore] = rows
    print(f"{ore:12} {len(rows):3} patches, {sum(r['tiles'] for r in rows):6} tiles; nearest {rows[0]['dist'] if rows else '-'}")

# lakes: water tiles per chunk, then connect neighbouring chunks
raw = lua("""
local s = game.surfaces.nauvis
local out = {}
for c in s.get_chunks() do
  local n = s.count_tiles_filtered{area=c.area, name={'water','deepwater','water-green','deepwater-green','water-shallow','water-mud'}}
  if n > 0 then out[#out+1] = {c.x, c.y, n} end
end
rcon.print(helpers.table_to_json(out))
""")
cells = {(x, y): n for x, y, n in json.loads(raw)}
seen, lakes = set(), []
for start in cells:
    if start in seen:
        continue
    stack, comp = [start], []
    seen.add(start)
    while stack:
        cx, cy = stack.pop()
        comp.append((cx, cy))
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                nb = (cx + dx, cy + dy)
                if nb in cells and nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
    tiles = sum(cells[c] for c in comp)
    mx = sum(c[0] for c in comp) / len(comp) * 32 + 16
    my = sum(c[1] for c in comp) / len(comp) * 32 + 16
    lakes.append({"x": round(mx), "y": round(my), "chunks": len(comp), "tiles": tiles,
                  "dist": round(math.hypot(mx - HUB[0], my - HUB[1]))})
lakes.sort(key=lambda r: -r["tiles"])
survey["lakes"] = lakes[:40]
print(len(lakes), "lakes; biggest:", [(l["x"], l["y"], l["tiles"]) for l in lakes[:5]])

nests = json.loads(lua("""
local s = game.surfaces.nauvis
local out = {}
for _, e in pairs(s.find_entities_filtered{force='enemy', type='unit-spawner'}) do out[#out+1] = {math.floor(e.position.x), math.floor(e.position.y)} end
rcon.print(helpers.table_to_json(out))
"""))
survey["nests"] = nests
print(len(nests), "spawners")
OUT.write_text(json.dumps(survey))
print("wrote", OUT)
