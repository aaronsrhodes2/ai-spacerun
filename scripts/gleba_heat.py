#!/usr/bin/env python3
"""Gleba: power from the spoilage burners (the Captain, 2026-11-13: "we should be capturing that heat and converting it into energy
with turbines"). Five of the seven heating towers stood at 1000 degrees with nothing taking the heat.
  heat    the four western towers (68,2  74,6  64,11  61,17) join one heat pipe row along y=6 by short stubs
  power   two heat exchangers on that row, each with a steam turbine straight on its steam outlet (no pipes between)
  water   a second offshore pump at 98,54 facing the wetland to its south; pipe round to y=55, west along it, north up x=61, under the belts at y=19..20 to x=59,
          and under the heat row to the northern exchanger
Tiles are whole numbers (the entity's top-left tile). Steps: build (dry run) | build --apply | status; add --east for the three eastern towers (layout_east). Never apply twice.
Usage: gleba_heat.py build [--east] [--apply] | status"""
import json
import sys

from _game import tools

Q = {"quality": "epic"}
N, E, S, W = 0, 4, 8, 12
ents, occ = [], {}


def put(name, tx, ty, w=1, h=1, d=N, **params):
    for c in [(tx + i, ty + j) for i in range(w) for j in range(h)]:
        assert c not in occ, "%s at %s overlaps %s" % (name, c, occ[c])
        occ[c] = name
    ents.append({"name": name, "x": tx + w / 2, "y": ty + h / 2, "direction": d, "params": dict(Q, **params)})


def layout():
    for x in range(57, 73):
        put("heat-pipe", x, 6)                       # the row; tower 74,6 touches its east end
    for c in [(68, 4), (68, 5), (64, 7), (64, 8), (64, 9)] + [(61, y) for y in range(7, 16)]:
        put("heat-pipe", *c)                         # stubs to towers 68,2 (south side), 64,11 (north side) and 61,17 (north side)
    put("heat-exchanger", 56, 7, 3, 2, d=S)          # south of the row: steam out at the bottom
    put("steam-turbine", 56, 9, 3, 5, d=N)
    put("heat-exchanger", 62, 4, 3, 2, d=N)          # north of the row: steam out at the top
    put("steam-turbine", 62, -1, 3, 5, d=N)
    ents.append({"name": "offshore-pump", "x": 98.5, "y": 54.5, "direction": S, "params": dict(Q)})   # only this spot and facing took: land at 98,54, wetland south of it
    for c in [(98, 53), (97, 53), (96, 53), (95, 53), (95, 54)]:
        put("pipe", *c)
    for x in range(61, 96):
        put("pipe", x, 55)
    for y in range(22, 55):
        put("pipe", 61, y)
    put("pipe", 60, 22)
    put("pipe", 59, 22)
    put("pipe-to-ground", 59, 21, d=S)               # under the belts and the substation at y=19..20
    put("pipe-to-ground", 59, 18, d=N)
    for y in range(7, 18):
        put("pipe", 59, y)                           # 59,7 is the southern exchanger's east water port
    put("pipe", 60, 8)
    put("pipe-to-ground", 60, 7, d=S)                # under the heat row
    put("pipe-to-ground", 60, 5, d=N)
    put("pipe", 60, 4)
    put("pipe", 61, 4)
    put("pipe", 61, 5)                               # the northern exchanger's west water port
    return {"entities": len(ents)}


def layout_east():
    """The three eastern towers, each with its own exchanger and turbine: belts lie between them and a heat pipe cannot go under one.
    131,18  heat from its north side round to an exchanger east of it (133..135, 14..15), turbine below; water from the Captain's pipe
            row y=12 at 129,12, under the heat pipe by a pipe-to-ground pair
    125,20  heat from its west side to x=120 and south; exchanger 118..120, 26..27, turbine below; own pump at 116,42
    127,45  heat from its east side; exchanger 129..131, 46..47, turbine below; own pump at 124,43, pipe under the belt at x=127"""
    for c in [(131, 16), (131, 15), (131, 14), (131, 13), (132, 13), (133, 13), (134, 13)]:
        put("heat-pipe", *c)
    put("heat-exchanger", 133, 14, 3, 2, d=S)
    put("steam-turbine", 133, 16, 3, 5, d=N)
    put("pipe-to-ground", 132, 14, d=E)
    put("pipe-to-ground", 130, 14, d=W)
    put("pipe", 129, 14)
    put("pipe", 129, 13)
    for c in [(123, 20), (122, 20), (121, 20), (121, 21), (121, 22), (120, 22), (120, 23), (120, 24), (120, 25), (119, 25)]:
        put("heat-pipe", *c)
    put("heat-exchanger", 118, 26, 3, 2, d=S)
    put("steam-turbine", 118, 28, 3, 5, d=N)
    ents.append({"name": "offshore-pump", "x": 116.5, "y": 42.5, "direction": S, "params": dict(Q)})
    for y in range(26, 42):
        put("pipe", 116, y)
    put("pipe", 117, 26)
    put("heat-pipe", 129, 45)
    put("heat-pipe", 130, 45)
    put("heat-exchanger", 129, 46, 3, 2, d=S)
    put("steam-turbine", 129, 48, 3, 5, d=N)
    ents.append({"name": "offshore-pump", "x": 124.5, "y": 43.5, "direction": S, "params": dict(Q)})
    put("pipe", 124, 42)
    put("pipe", 125, 42)
    put("pipe-to-ground", 126, 42, d=W)
    put("pipe-to-ground", 128, 42, d=E)
    for x in range(129, 133):
        put("pipe", x, 42)
    for y in range(43, 47):
        put("pipe", 132, y)
    return {"entities": len(ents)}


STATUS = ("local s=game.surfaces.gleba local o={} for _,e in pairs(s.find_entities_filtered{name='heating-tower'}) do o[#o+1]='tower '..e.position.x..','..e.position.y..' '..string.format('%.0f',e.temperature) end "
          "for _,e in pairs(s.find_entities_filtered{name={'heat-exchanger','steam-turbine','offshore-pump'}}) do local k='?' for a,v in pairs(defines.entity_status) do if v==e.status then k=a end end local fl={} for n,c in pairs(e.get_fluid_contents()) do fl[#fl+1]=n..' '..string.format('%.0f',c) end "
          "o[#o+1]=e.name..' '..e.position.x..','..e.position.y..' '..k..(e.temperature and (' temp '..string.format('%.0f',e.temperature)) or '')..' '..table.concat(fl,',')..(e.type=='generator' and (' making '..string.format('%.2f',e.energy_generated_last_tick*60/1e6)..' MW') or '') end rcon.print(table.concat(o,' ; '))")

if __name__ == "__main__":
    print(layout_east() if "--east" in sys.argv else layout())
    if sys.argv[1] == "build":
        apply = "--apply" in sys.argv
        r = json.loads(tools["place_entities"](json.dumps(ents), surface="gleba", dry_run=not apply))
        print("placed" if apply else "dry run", r.get("placed"), "failed", json.dumps(r.get("failed") or [])[:600])
    else:
        print(tools["run_lua"](STATUS).replace(" ; ", "\n"))
