"""Plastic row taps (2026-11-14): the ten plastic plants at y -247.5 drop on ONE lane of the belt at y -244.5 and a single bulk inserter
at its east end lifted the plastic into a red chest, so the row topped out near 23 plastic a second however much gas it had.
Nine more bulk inserters (y -243.5, picking from the belt) with red chests (y -242.5, barred at 20 slots) between the plants.

Usage: scripts/build_plastic_taps.py [--apply]"""
import json
import sys

from _game import tools

Q = {"quality": "epic"}
XS = [-292.5, -288.5, -284.5, -280.5, -276.5, -272.5, -268.5, -264.5, -260.5]

ents = []
for x in XS:
    ents.append({"name": "bulk-inserter", "x": x, "y": -243.5, "direction": 0, "params": Q})
    ents.append({"name": "passive-provider-chest", "x": x, "y": -242.5, "params": Q})
apply = "--apply" in sys.argv
print(tools["place_entities"](json.dumps(ents), dry_run=not apply, clear_trees=False))
if apply:
    print(tools["run_lua"]("local s=game.surfaces.nauvis local n=0 for _,c in pairs(s.find_entities_filtered{name='passive-provider-chest',area={{-294,-243},{-260,-242}}}) do c.get_inventory(defines.inventory.chest).set_bar(21) n=n+1 end rcon.print('barred '..n)"))
