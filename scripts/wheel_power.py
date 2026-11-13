#!/usr/bin/env python3
"""Gleba Wheel power buffer (2026-11-13): accumulators along the spokes (x 1..2, every 6 tiles) buffer the laser turrets, as the Captain asked.
No substations: a space platform powers everything standing on it (the 425 I had placed were removed).
Usage: wheel_power.py [--apply]"""
import json
import sys

from _game import tools

Q = {"quality": "rare"}


def turn(t, k):
    for _ in range(k):
        t = (-t[1], t[0])
    return t


e = []
for k in range(4):
    for y in range(-580, -40, 6):
        x2, y2 = turn((2, y), k)
        e.append({"name": "accumulator", "x": x2, "y": y2, "params": dict(Q)})
apply = "--apply" in sys.argv
ok = bad = 0
for i in range(0, len(e), 400):
    r = json.loads(tools["place_entities"](json.dumps(e[i:i + 400]), surface="platform-12", dry_run=not apply))
    ok += r.get("placed", 0)
    f = r.get("failed") or []
    bad += len(f)
    if f:
        print("failed", json.dumps(f)[:300])
print("placed" if apply else "dry run ok", ok, "failed", bad)
