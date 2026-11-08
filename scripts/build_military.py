"""
Military science plant in the east base (bridge/factorio/military.py): rows, bus taps, splitters.
Trunk belts already exist; the splitter tiles are cleared first. Usage: scripts/build_military.py [--build]
"""
import json
import sys

from _game import tools

from bridge.factorio import bus, military
from bridge.factorio.planner import batches


def main():
    build = "--build" in sys.argv
    plant, taps = military.plant()
    plant = military.dedupe(plant)
    branch = []
    for k, y in taps:
        branch += bus.tap(k, y, military.X)
    splitters = [e for e in bus.trunk_entities(taps) if e["name"] == "splitter"]
    ents = plant + branch
    counts = {}
    for e in ents + splitters:
        counts[e["name"]] = counts.get(e["name"], 0) + 1
    print(counts)
    for part in batches(ents):
        r = json.loads(tools["place_entities"](json.dumps(part), dry_run=True))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"dry run failed: {json.dumps(r)[:1500]}")
    print("dry run clean")
    if not build:
        return
    print(tools["save_game"]("before-military"))
    for k, y in taps:
        x, ty = bus.splitter_tile(k, y)
        tools["remove_entities"](x + 0.2, ty + 0.2, x + 0.8, ty + 0.8, names="transport-belt")
    for part in batches(ents + splitters):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"stopped: {json.dumps(r)[:1500]}")
        print("placed", r["placed"])


if __name__ == "__main__":
    main()
