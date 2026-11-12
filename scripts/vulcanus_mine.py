#!/usr/bin/env python3
"""Vulcanus tungsten mine inside territory 5, every entity at least 12 tiles from the demolisher's patrol path.
  drills   big mining drills on both sides of the belt column x=-371.5 (rows 7 apart, substations in the gaps) and along the belt row y=-203.5
  poles    big electric poles beside the belt (docs/vulcanus_tungsten_belt.json) from the mine to the crossing at (-258,-70)
  cross    robot crossing of the patrol path; east = belt and poles from the crossing to the base edge (-118,-70)
Usage: vulcanus_mine.py drills|poles|cross|east [--apply]"""
import json
import sys
from pathlib import Path

from _game import tools

ROUTE = Path(__file__).resolve().parent.parent / "docs" / "vulcanus_tungsten_belt.json"


def drills():
    e = []
    for cy in (-186.5, -179.5, -172.5, -165.5, -158.5):
        e.append({"name": "big-mining-drill", "x": -374.5, "y": cy, "direction": 4})
        e.append({"name": "big-mining-drill", "x": -368.5, "y": cy, "direction": 12})
        e.append({"name": "substation", "x": -375, "y": cy + 3.5})
    for cx in (-388.5, -383.5, -378.5):
        e.append({"name": "big-mining-drill", "x": cx, "y": -206.5, "direction": 8})
    for cx in (-388.5, -383.5):
        e.append({"name": "big-mining-drill", "x": cx, "y": -200.5, "direction": 0})
    e += [{"name": "substation", "x": -392, "y": -207}, {"name": "substation", "x": -375, "y": -207}, {"name": "substation", "x": -375, "y": -195}]
    return e


def cross():
    """Robot crossing over the T5 patrol path at y -70 (path x about -245): the west belt ends in three red chests at (-258,-69),
    the east belt starts from six blue chests at (-229,-70); roboports 18 tiles either side of the path; one big pole span carries power."""
    e = [{"name": "bulk-inserter", "x": -258.5, "y": -68.5, "direction": 4}, {"name": "passive-provider-chest", "x": -259.5, "y": -68.5},
         {"name": "bulk-inserter", "x": -258.5, "y": -67.5, "direction": 4}, {"name": "passive-provider-chest", "x": -259.5, "y": -67.5},
         {"name": "bulk-inserter", "x": -257.5, "y": -69.5, "direction": 8}, {"name": "passive-provider-chest", "x": -257.5, "y": -70.5},
         {"name": "roboport", "x": -262, "y": -64}, {"name": "substation", "x": -261, "y": -72},
         {"name": "roboport", "x": -226, "y": -64}, {"name": "big-electric-pole", "x": -227, "y": -60}, {"name": "substation", "x": -232, "y": -66}]
    for x in (-229.5, -228.5, -227.5):
        e += [{"name": "bulk-inserter", "x": x, "y": -70.5, "direction": 0}, {"name": "requester-chest", "x": x, "y": -71.5},
              {"name": "bulk-inserter", "x": x, "y": -68.5, "direction": 8}, {"name": "requester-chest", "x": x, "y": -67.5}]
    return e


def poles(apply, route=ROUTE):
    belt = json.load(open(route))
    taken = {(round(b["x"] - 0.5), round(b["y"] - 0.5)) for b in belt}
    placed, last = [], None
    for i, b in enumerate(belt):
        if last is not None and i - last < 22:
            continue
        x, y = round(b["x"] - 0.5), round(b["y"] - 0.5)
        for dx, dy in ((2, 2), (-2, 2), (2, -2), (-2, -2), (3, 0), (-3, 0), (0, 3), (0, -3)):
            px, py = x + dx, y + dy
            cells = {(px - 1, py - 1), (px, py - 1), (px - 1, py), (px, py)}
            if cells & taken:
                continue
            r = json.loads(tools["place_entities"](json.dumps([{"name": "big-electric-pole", "x": px, "y": py}]), surface="vulcanus", dry_run=not apply))
            if r["placed"] == 1:
                placed.append((px, py))
                taken |= cells
                last = i
                break
    print("big poles", len(placed), placed[:6], "...", placed[-3:])


def main():
    step = sys.argv[1]
    apply = "--apply" in sys.argv
    if step == "drills":
        print(tools["place_entities"](json.dumps(drills()), surface="vulcanus", dry_run=not apply)[:1500])
    elif step == "poles":
        poles(apply)
    elif step == "cross":
        print(tools["place_entities"](json.dumps(cross()), surface="vulcanus", dry_run=not apply)[:1500])
    elif step == "east":
        route = ROUTE.with_name("vulcanus_tungsten_belt_east.json")
        belt = json.load(open(route))
        seen = {}
        for b in belt:
            seen[(b["x"], b["y"])] = b
        print(tools["place_entities"](json.dumps(list(seen.values())), surface="vulcanus", dry_run=not apply)[:800])
        poles(apply, route)


if __name__ == "__main__":
    main()
