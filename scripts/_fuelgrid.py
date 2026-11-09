import sys, json
sys.path.insert(0, "scripts")
from _game import tools
X1, X2, Y1, Y2 = -258, 118, -170, -95
rows = {}
for y0 in range(Y1, Y2 + 1, 10):
    y1 = min(y0 + 9, Y2)
    lua = ("local s=game.surfaces.nauvis local o={} for y=%d,%d do local r={} for x=%d,%d do r[#r+1]=s.can_place_entity{name='transport-belt',position={x+0.5,y+0.5},direction=4,force='player'} and '.' or '#' end o[#o+1]=table.concat(r) end rcon.print(table.concat(o,','))" % (y0, y1, X1, X2))
    res = tools["run_lua"](lua).split(",")
    for i, r in enumerate(res):
        rows[y0 + i] = r
json.dump({"x1": X1, "rows": rows}, open("scripts/_fuelgrid.json", "w"))
print(len(rows), "rows", len(next(iter(rows.values()))), "wide")
