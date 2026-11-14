#!/usr/bin/env python3
"""The triangle strip miner (the Captain, 2026-11-14): a platform shaped as the OUTLINE of an equilateral triangle, 1,000 tiles a side,
a thin strip of foundation like a wheel's rim. The strip carries the asteroid collectors (and, away from Nauvis, the turrets); the catch
rides belts to the hub, where a reprocessing loop turns any chunk into the kind that space asks for (carbon, iron, ice) and other
platforms in the same orbit request the goods from the hub. It is NOT a filled triangle (the first try laid 433,000 ghosts).
Geometry (tiles): the hub at 0,0 is the centroid. Apex (0,-577), base y=+289 from x=-500 to 500. Strip width T. One spoke, W wide, from the
hub straight south to the base (a platform must be one piece). Never clear tiles under the hub: that destroys it (it happened to the test platform).
Steps: ghosts (lays tile ghosts for strip and spoke, skips what is laid) | status
Usage: triangle.py ghosts | status"""
import sys

from _game import tools

NAME = "Nauvis Triangle 1"
APEX, H, T, W = -577, 866, 4, 4

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


def status():
    print(tools["run_lua"](FIND + "local h=p.hub rcon.print(p.name..' '..s.name..' hub '..tostring(h and h.valid)..' tiles '..#s.find_tiles_filtered{name='space-platform-foundation'}"
                           "..' ghosts '..s.count_entities_filtered{name='tile-ghost'}..' foundation aboard '..(h and h.get_inventory(defines.inventory.hub_main).get_item_count('space-platform-foundation') or 0))"))


if __name__ == "__main__":
    if (sys.argv[1] if len(sys.argv) > 1 else "status") == "ghosts":
        ghosts()
    status()
