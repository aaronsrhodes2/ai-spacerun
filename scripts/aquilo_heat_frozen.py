#!/usr/bin/env python3
"""Lay heat pipes so every FROZEN entity of ours on Aquilo touches the heat network (the north pipe line and pumpjacks were ghosted with no
heat pipes beside them: 115 frozen with no heat neighbour, 2026-11-14). Uses aquilo_base.heat_all (BFS from the existing heat network over
free buildable tiles; ice-platform and concrete tiles count as buildable for a heat pipe here).
Usage: aquilo_heat_frozen.py [--apply] [--box X0 Y0 X1 Y1]"""
import json
import sys

import aquilo_base as base
from _game import tools

SIZE_LUA = ("local s=game.surfaces.aquilo local t={} for _,e in pairs(s.find_entities_filtered{force='player',area={{%d,%d},{%d,%d}}}) do "
            "if e.status==defines.entity_status.frozen then local b=e.bounding_box t[#t+1]=e.name..','..e.position.x..','..e.position.y..','..e.direction..','"
            "..math.floor(b.right_bottom.x-b.left_top.x+0.5)..','..math.floor(b.right_bottom.y-b.left_top.y+0.5) end end rcon.print(table.concat(t,';'))")


def main():
    apply = "--apply" in sys.argv
    box = (-95, -170, 10, -40)
    if "--box" in sys.argv:
        i = sys.argv.index("--box")
        box = tuple(int(v) for v in sys.argv[i + 1:i + 5])
    rows = [r.split(",") for r in tools["run_lua"](SIZE_LUA % box).strip().split(";") if r]
    print("frozen in box:", len(rows))
    base.ents[:] = []
    for n, x, y, d, w, h in rows:
        base.SIZE[n] = (int(w), int(h))
        base.HEATED.add(n)
        base.ents.append({"name": n, "x": float(x), "y": float(y), "direction": int(d), "params": dict(base.Q)})
        base.SIZE[n] = (int(w), int(h)) if int(d) in (0, 8) else (int(h), int(w))
    # let heat pipes stand on ice platforms and concrete as well as snow
    orig = base.free_grid

    def free_grid(x0, y0, x1, y1):
        lua = ("local s=game.surfaces['aquilo'] local ok={['snow-crests']=1,['snow-flat']=1,['snow-lumpy']=1,['snow-patchy']=1,['frozen-concrete']=1,['concrete']=1,['refined-concrete']=1,['ice-platform']=1} local rows={} for y=%d,%d do local r={} for x=%d,%d do local t=s.get_tile(x,y).name "
               "local c=ok[t] and '.' or 'x' if c=='.' and s.count_entities_filtered{area={{x+0.05,y+0.05},{x+0.95,y+0.95}}}>0 then c='#' end r[#r+1]=c end rows[#rows+1]=table.concat(r) end rcon.print(table.concat(rows,'|'))" % (y0, y1, x0, x1))
        rows2 = tools["run_lua"](lua).strip().split("|")
        return {(x0 + i, y0 + j) for j, row in enumerate(rows2) for i, c in enumerate(row) if c == "."}
    base.free_grid = free_grid
    added = base.heat_all(box)
    pipes = [e for e in base.ents if e["name"] == "heat-pipe"]
    print("heat pipes to add:", added)
    r = json.loads(tools["place_entities"](json.dumps(pipes), surface="aquilo", dry_run=not apply))
    print("placed" if apply else "dry run", r.get("placed"), "failed", len(r.get("failed") or []), json.dumps((r.get("failed") or [])[:4]))
    base.free_grid = orig


if __name__ == "__main__":
    main()
