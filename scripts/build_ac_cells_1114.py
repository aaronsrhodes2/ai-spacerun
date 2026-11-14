"""Eight more drone-fed advanced circuit cells (2026-11-14), epic, on free lattice ground west of the old AC column:
origins (-55,-262) and (-39,-262), four cells each. Plastic went from 4 to about 60 a second with the west oil field, and every
drone-fed AC cell was working, so circuit machines became the limit. Uses build_cells.plan/configure; dry run without --apply."""
import json
import sys

import build_cells as bc
from _game import tools

SITES = [(-55, -262, 4), (-39, -262, 4)]
apply = "--apply" in sys.argv
for x0, y0, n in SITES:
    ents = bc.plan("ac", x0, y0, n)
    for e in ents:
        e["params"] = {"quality": "epic"}
    if not apply:
        print(tools["place_entities"](json.dumps(ents), dry_run=True, clear_trees=False))
        continue
    print(bc.clear_box(x0, y0, n))
    print(tools["place_entities"](json.dumps(ents)))
    print(bc.configure("ac", x0, y0, n))
