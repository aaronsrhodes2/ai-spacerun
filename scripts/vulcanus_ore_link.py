#!/usr/bin/env python3
"""Vulcanus: link the isolated tungsten-ore network (2 roboports at (-262,-64) and (-226,-64), three passive provider chests holding 13,650 tungsten ore at
(-260,-69)) to the main network (nearest roboport (-96,-48)). Without the link no robot can carry that ore to the foundries (they sat empty, 15 tungsten drills blocked on
full belts, 3 metallurgic pack makers starved, 0 packs made; found 2026-11-15). Two epic roboports at about 44-tile spacing (epic logistic radius 25: cells must touch) and
a substation each, wired to the big poles on y -72..-68.
Usage: vulcanus_ore_link.py [--apply]   (default dry run)"""
import json
import sys

from _game import tools

ENTS = [
    {"name": "roboport", "x": -182, "y": -62, "params": {"quality": "epic"}},
    {"name": "substation", "x": -178, "y": -62, "params": {"quality": "epic"}},
    {"name": "roboport", "x": -139, "y": -56, "params": {"quality": "epic"}},
    {"name": "substation", "x": -135, "y": -56, "params": {"quality": "epic"}},
]

if __name__ == "__main__":
    apply = "--apply" in sys.argv
    print(tools["place_entities"](json.dumps(ENTS), surface="vulcanus", dry_run=not apply))
