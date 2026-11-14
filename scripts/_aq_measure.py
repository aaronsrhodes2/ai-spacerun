#!/usr/bin/env python3
"""Measure the Aquilo lines over game time: _aq_measure.py [ticks, default 40000]. Prints what was made a game minute (3,600 ticks)
between two samples: cryogenic science packs, ice platforms, lithium, rocket fuel, solid fuel made and used, tile ghosts laid."""
import sys
import time

from _game import tools

LUA = ("local s=game.surfaces.aquilo local f=game.forces.player local ps=f.get_item_production_statistics(s) local o={game.tick} "
       "for _,n in pairs({'cryogenic-science-pack','ice-platform','lithium','lithium-plate','rocket-fuel','solid-fuel','ice'}) do o[#o+1]=ps.get_input_count(n) o[#o+1]=ps.get_output_count(n) end "
       "o[#o+1]=s.count_entities_filtered{type='tile-ghost'} local net=s.find_logistic_network_by_position({4,-11},f) o[#o+1]=net.get_item_count('solid-fuel') o[#o+1]=net.get_item_count('cryogenic-science-pack') "
       "local w=0 for _,g in pairs(s.find_entities_filtered{type='generator'}) do w=w+g.energy_generated_last_tick*60 end o[#o+1]=math.floor(w) rcon.print(table.concat(o,' '))")
NAMES = ["cryogenic-science-pack", "ice-platform", "lithium", "lithium-plate", "rocket-fuel", "solid-fuel", "ice"]


def sample():
    return [float(v) for v in tools["run_lua"](LUA).split()]


want = int(sys.argv[1]) if len(sys.argv) > 1 else 40000
a = sample()
while True:
    time.sleep(20)
    b = sample()
    if b[0] - a[0] >= want:
        break
mins = (b[0] - a[0]) / 3600
print("ticks %d = %.1f game minutes" % (b[0] - a[0], mins))
for i, n in enumerate(NAMES):
    print("%-24s made %.1f/min  used %.1f/min" % (n, (b[1 + 2 * i] - a[1 + 2 * i]) / mins, (b[2 + 2 * i] - a[2 + 2 * i]) / mins))
k = 1 + 2 * len(NAMES)
print("tile ghosts %d -> %d (%.1f laid a minute); solid fuel stock %d -> %d; packs in the network %d; power now %.1f MW" % (a[k], b[k], (a[k] - b[k]) / mins, a[k + 1], b[k + 1], b[k + 2], b[k + 3] / 1e6))
