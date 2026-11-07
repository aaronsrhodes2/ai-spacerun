"""
Build the rail geometry catalog from the game itself.

Every rail piece (straight-rail, half-diagonal-rail, curved-rail-a, curved-rail-b) is placed
at each of the 16 directions on spare ground, and both of its rail ends are read with
get_rail_end(front/back).location. The router then connects pieces by matching one end of
the next piece to the open end of the last one, with no hand-written curve coordinates.

Writes snapshots/rail-catalog.json:  { "<name>": { "<dir>": {"ends": [[dx, dy, dir], ...],
"box": [x1, y1, x2, y2], "tiles": [[tx, ty], ...]} } } with positions relative to the piece.

Usage: scripts/rail_catalog.py [X Y]   (a clear spot; default far east)
"""
import json
import sys
from pathlib import Path

from _game import tools

X = float(sys.argv[1]) if len(sys.argv) > 1 else 300.0
Y = float(sys.argv[2]) if len(sys.argv) > 2 else -60.0
NAMES = ["straight-rail", "half-diagonal-rail", "curved-rail-a", "curved-rail-b"]


def lua(code):
    return tools["run_lua"](" ".join(code.splitlines()))


catalog = {}
for name in NAMES:
    catalog[name] = {}
    for d in range(16):
        r = json.loads(tools["place_entities"](json.dumps([{"name": name, "x": X, "y": Y, "direction": d}])))
        if r.get("error") or r["failed"] or not r["placed"]:
            tools["remove_entities"](X - 12, Y - 12, X + 12, Y + 12)
            continue
        info = lua(f"""
            local e = game.surfaces.nauvis.find_entities_filtered{{name='{name}', position={{{X}, {Y}}}, radius=6}}[1]
            if not e then rcon.print('none') return end
            local out = {{ends = {{}}, dir = e.direction}}
            for _, rd in pairs({{defines.rail_direction.front, defines.rail_direction.back}}) do
              local re = e.get_rail_end(rd)
              local l = re.location
              out.ends[#out.ends+1] = {{l.position.x - {X}, l.position.y - {Y}, l.direction}}
            end
            local b = e.bounding_box
            out.box = {{b.left_top.x - {X}, b.left_top.y - {Y}, b.right_bottom.x - {X}, b.right_bottom.y - {Y}}}
            rcon.print(helpers.table_to_json(out))
        """)
        tools["remove_entities"](X - 12, Y - 12, X + 12, Y + 12)
        if info == "none":
            continue
        catalog[name][str(d)] = json.loads(info)
    print(name, "directions:", sorted(int(k) for k in catalog[name]))

out = Path(__file__).resolve().parent.parent / "snapshots" / "rail-catalog.json"
out.write_text(json.dumps(catalog, indent=1))
print("wrote", out)
