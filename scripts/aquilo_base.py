#!/usr/bin/env python3
"""The first base on Aquilo (the Captain, 2026-11-13: "establishing Aquilo ... you have to keep a heat line running everywhere").
What the game says (read from the prototypes and tested on 2026-11-13):
  - Almost every machine, belt, inserter and pipe has a heating_energy (assembler 100 kW, belt 10 kW, inserter 30 kW, pipe 1 kW,
    pipe to ground 150 kW, foundry 300 kW, roboport 300 kW). An entity that is not heated has the status `frozen` and does not work
    (a lone pipe with no heat showed `frozen`).
  - Heat comes only from heat pipes, heating towers and reactors (heating_radius 1): an entity is heated when it touches one (a furnace
    beside a heat pipe worked, an assembler two tiles away stayed frozen). Chests, poles, panels and heat pipes themselves need none.
    A tower with no fuel cannot heat its own fuel inserter: the first fuel goes in straight from the pad.
  - Ice-smooth, ice-rough and brash-ice tiles are `meltable`: nothing heavy stands on them. Snow tiles and (frozen) concrete take
    everything. Land is scarce (20%); the free block is the concrete east of the pad, x 14..31, y -21..-7.
  - Solar is 1% of its nominal output (26 epic panels gave 26 kW), so power comes from steam (heat exchangers, turbines, water). Lithium
    icebergs are simple entities that robots may deconstruct (an ice platform, 3-7 ice, 1-3 lithium each).
Layout (tile coordinates, the concrete block east of the landing pad at 10,-18):
  heat row   a heat pipe row at y=-14, x 9..31, with a stub (31,-13)
  reactor    tiles 15..19 x -19..-15 (fuel cells), its south connections on the row; fuel inserter (17,-20) from a chest (17,-21)
  tower      tiles 21..23 x -17..-15, rocket fuel by inserter (24,-16) from a chest (25,-16)
  steam      heat exchanger (south facing) tiles 24..26 x -13..-12 under the row; turbine tiles 24..26 x -11..-7 straight under it
  water      ice melter (chemical plant, east facing) tiles 28..30 x -13..-11; a pipe at (27,-13) joins its output to the exchanger's
             east water port; ice by an inserter at (31,-12) from a chest (32,-12)
  cell       assembler tiles 10..12 x -13..-11, roboport tiles 14..17 x -13..-10, furnace tiles 19..21 x -13..-11, all under the row
  heat       `heat_all` lays heat pipes on free tiles so that every heated entity touches one, joined to the network
Steps: check | build [--apply] | status | fuel
Usage: aquilo_base.py build --apply"""
import json
import sys
from collections import deque

from _game import tools

SURF = "aquilo"
Q = {"quality": "epic"}
N, E, S, W = 0, 4, 8, 12
ents = []
HEATED = {"assembling-machine-3", "chemical-plant", "electric-furnace", "roboport", "fast-inserter", "inserter", "pipe", "steam-turbine",
          "storage-tank", "lab", "heat-exchanger", "electric-mining-drill", "pumpjack", "oil-refinery", "foundry", "cryogenic-plant", "transport-belt",
          "express-transport-belt", "bulk-inserter", "long-handed-inserter"}
SIZE = {"nuclear-reactor": (5, 5), "heating-tower": (3, 3), "chemical-plant": (3, 3), "assembling-machine-3": (3, 3), "electric-furnace": (3, 3), "roboport": (4, 4),
        "steam-turbine": (3, 5), "heat-exchanger": (3, 2), "substation": (2, 2), "lab": (3, 3), "cryogenic-plant": (5, 5), "oil-refinery": (5, 5),
        "pumpjack": (3, 3), "storage-tank": (3, 3), "foundry": (5, 5)}


def put(name, cx, cy, d=N, **p):
    ents.append({"name": name, "x": cx, "y": cy, "direction": d, "params": dict(Q, **p)})


def tiles_of(e):
    w, h = SIZE.get(e["name"], (1, 1))
    if e["direction"] in (E, W) and (w, h) != (1, 1) and e["name"] not in ("nuclear-reactor", "heating-tower", "chemical-plant", "assembling-machine-3", "electric-furnace"):
        w, h = h, w
    x0, y0 = int(round(e["x"] - w / 2)), int(round(e["y"] - h / 2))
    return {(x0 + i, y0 + j) for i in range(w) for j in range(h)}


def heat_pipe(x, y):
    put("heat-pipe", x + .5, y + .5)


def layout():
    for x in range(9, 32):
        heat_pipe(x, -14)
    heat_pipe(31, -13)
    put("nuclear-reactor", 17.5, -16.5)
    put("fast-inserter", 17.5, -19.5, N)       # an inserter's direction is the side it picks up from
    put("steel-chest", 17.5, -20.5)
    put("heating-tower", 22.5, -15.5)
    put("fast-inserter", 24.5, -15.5, E)
    put("steel-chest", 25.5, -15.5)
    put("heat-exchanger", 25.5, -12.0, S)
    put("steam-turbine", 25.5, -8.5, N)
    put("pipe", 27.5, -12.5)
    put("chemical-plant", 29.5, -11.5, E, recipe="ice-melting")
    put("fast-inserter", 31.5, -11.5, E)
    put("steel-chest", 32.5, -11.5)
    put("assembling-machine-3", 11.5, -11.5)
    put("roboport", 16.0, -11.0)
    put("electric-furnace", 20.5, -11.5)
    put("substation", 23.0, -20.0)
    return {"entities": len(ents)}


def free_grid(x0, y0, x1, y1):
    lua = ("local s=game.surfaces['%s'] local ok={['snow-crests']=1,['snow-flat']=1,['snow-lumpy']=1,['snow-patchy']=1,['frozen-concrete']=1} local rows={} for y=%d,%d do local r={} for x=%d,%d do local t=s.get_tile(x,y).name "
           "local c=ok[t] and '.' or 'x' if c=='.' and s.count_entities_filtered{area={{x+0.05,y+0.05},{x+0.95,y+0.95}}}>0 then c='#' end r[#r+1]=c end rows[#rows+1]=table.concat(r) end rcon.print(table.concat(rows,'|'))" % (SURF, y0, y1, x0, x1))
    rows = tools["run_lua"](lua).strip().split("|")
    return {(x0 + i, y0 + j) for j, row in enumerate(rows) for i, c in enumerate(row) if c == "."}


def heat_all(box=(5, -24, 36, 2)):
    """Add heat pipes on free tiles so that every heated entity in `ents` touches the network (edge-adjacent), as one connected network."""
    free = free_grid(*box)
    occupied = set()
    for e in ents:
        occupied |= tiles_of(e)
    free -= occupied
    net = {t for e in ents if e["name"] == "heat-pipe" for t in tiles_of(e)}
    sources = [e for e in ents if e["name"] in ("heating-tower", "nuclear-reactor")]
    def adj(t):
        x, y = t
        return ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
    def heated(tiles):
        return any(n in net for t in tiles for n in adj(t))
    added = []
    need = [e for e in ents if e["name"] in HEATED]
    for _ in range(3):
        for e in sorted(need, key=lambda e: (e["y"], e["x"])):
            tl = tiles_of(e)
            if heated(tl):
                continue
            targets = {n for t in tl for n in adj(t) if n in free}
            seen, q, found = {t: None for t in net}, deque(net), None
            while q and not found:
                c = q.popleft()
                for n in adj(c):
                    if n in seen or n not in free:
                        continue
                    seen[n] = c
                    if n in targets:
                        found = n
                        break
                    q.append(n)
            if not found:
                print("no heat path for", e["name"], e["x"], e["y"])
                continue
            c = found
            while c is not None and c not in net:
                net.add(c)
                added.append(c)
                free.discard(c)
                c = seen[c]
    for x, y in added:
        heat_pipe(x, y)
    return len(added)


def main():
    step = sys.argv[1]
    apply = "--apply" in sys.argv
    print(layout())
    print("heat pipes added by heat_all:", heat_all())
    if step == "build":
        r = json.loads(tools["place_entities"](json.dumps(ents), surface=SURF, dry_run=not apply))
        print("placed" if apply else "dry run", r.get("placed"), "failed", json.dumps(r.get("failed") or [])[:900])


if __name__ == "__main__":
    main()
