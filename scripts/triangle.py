#!/usr/bin/env python3
"""The triangle strip miner (the Captain, 2026-11-14): a platform shaped as the OUTLINE of an equilateral triangle, 1,000 tiles a side,
a thin strip of foundation like a wheel's rim. The strip carries the asteroid collectors (and, away from Nauvis, the turrets); the catch
rides belts to the hub, where a reprocessing loop turns any chunk into the kind that space asks for (carbon, iron, ice) and other
platforms in the same orbit request the goods from the hub. It is NOT a filled triangle (the first try laid 433,000 ghosts).
Geometry (tiles): the hub at 0,0 is the centroid. Apex (0,-577), base y=+289 from x=-500 to 500. Strip width T. One spoke, W wide, from the
hub straight south to the base (a platform must be one piece). Never clear tiles under the hub: that destroys it (it happened to the test platform).
Steps: ghosts (lays tile ghosts for strip and spoke, skips what is laid) | spokes (the two spokes to the left and right edge middles) | status
Usage: triangle.py ghosts | status"""
import sys

from _game import tools

NAME = "Nauvis Triangle 1"
APEX, H, T, W = -577, 866, 4, 4
SW = 4                          # width of the two later spokes

FIND = "local p for _,q in pairs(game.forces.player.platforms) do if q.name:find('%s',1,true) then p=q end end local s=p.surface " % NAME


def ghosts():
    total = 0
    for a in range(0, H + 1, 100):
        b = min(a + 99, H)
        lua = (FIND + "local n=0 for r=%d,%d do local y=%d+r local w=r/math.sqrt(3) for x=math.ceil(-w),math.floor(w) do "
               "local strip=math.min((w-math.abs(x))*0.866,%d-r)<%d local spoke=(y>=5 and x>=-%d and x<%d) "
               "if (strip or spoke) and s.get_tile(x,y).name~='space-platform-foundation' and s.count_entities_filtered{name='tile-ghost',position={x+0.5,y+0.5},radius=0.3}==0 then "
               "if s.create_entity{name='tile-ghost',inner_name='space-platform-foundation',position={x,y},force='player'} then n=n+1 end end end end rcon.print(n)"
               % (a, b, APEX, H, T, W // 2, W - W // 2))
        n = int(tools["run_lua"](lua).strip())
        total += n
        print("rows", a, b, "ghosts", n, flush=True)
    print("ghosts laid", total)


def spokes():
    """Two more spokes (the Captain, 2026-11-14): from the hub to the MIDDLES of the left and right edges, like the south spoke to the base.
    Edge midpoints: (-250,-144) and (250,-144). Tiles within SW/2 of the segment from the hub's edge to the midpoint."""
    import math
    out = []
    for ex, ey in ((-250.0, -144.0), (250.0, -144.0)):
        tiles = set()
        L = math.hypot(ex, ey)
        ux, uy = ex / L, ey / L
        for i in range(0, int(L) + 2):
            cx, cy = ux * i, uy * i
            for dx in range(-4, 5):
                for dy in range(-4, 5):
                    x, y = int(math.floor(cx)) + dx, int(math.floor(cy)) + dy
                    px, py = x + 0.5 - 0.0, y + 0.5
                    t = max(0.0, min(L, px * ux + py * uy))
                    d = math.hypot(px - ux * t, py - uy * t)
                    if d <= SW / 2.0 + 0.5:
                        tiles.add((x, y))
        out.append(sorted(tiles))
    for tiles in out:
        for a in range(0, len(tiles), 600):
            part = ",".join("{%d,%d}" % t for t in tiles[a:a + 600])
            lua = (FIND + "local n=0 for _,p in pairs({%s}) do if s.get_tile(p[1],p[2]).name~='space-platform-foundation' and s.count_entities_filtered{name='tile-ghost',position={p[1]+0.5,p[2]+0.5},radius=0.3}==0 then "
                   "if s.create_entity{name='tile-ghost',inner_name='space-platform-foundation',position={p[1],p[2]},force='player'} then n=n+1 end end end rcon.print(n)" % part)
            print("spoke ghosts", tools["run_lua"](lua).strip(), flush=True)


def status():
    print(tools["run_lua"](FIND + "local h=p.hub rcon.print(p.name..' '..s.name..' hub '..tostring(h and h.valid)..' tiles '..#s.find_tiles_filtered{name='space-platform-foundation'}"
                           "..' ghosts '..s.count_entities_filtered{name='tile-ghost'}..' foundation aboard '..(h and h.get_inventory(defines.inventory.hub_main).get_item_count('space-platform-foundation') or 0))"))


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "status"
    if step == "ghosts":
        ghosts()
    elif step == "spokes":
        spokes()
    status()
