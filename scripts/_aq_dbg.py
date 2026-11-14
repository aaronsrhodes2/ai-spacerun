import sys
import aquilo_cryo as a
which = sys.argv[1]
box = a.BOX_P if which == "platforms" else a.BOX_S
grid = a.fetch(box); net = a.heat_tiles(box)
P = a.platform_plan() if which == "platforms" else a.science_plan()
extra = [(x, a.CY - 5) for x in range(a.CXS[0] - 6, a.CXS[-1] + 5)] if which == "platforms" else []
H, cold = a.heat_plan(P, grid, net, extra)
sym = {"pipe": "=", "pipe-to-ground": "u", "chemical-plant": "c", "cryogenic-plant": "K", "bulk-inserter": "n", "fast-inserter": "n", "substation": "$", "offshore-pump": "o"}
ov = {}
for e in P.ents:
    for t in e["tiles"]:
        ov[t] = sym.get(e["name"], "b")
x0, y0, x1, y1 = box
for y in range(y0, y1 + 1):
    print("%4d " % y + "".join(ov.get((x, y)) or ("h" if (x, y) in H else "H" if (x, y) in net else grid[(x, y)]) for x in range(x0, x1 + 1)))
print(cold)
