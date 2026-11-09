"""
Second row of 12 electric furnaces at the iron depot, mirrored about the ore belt (y=-417.5): furnaces y=-420.5, input fast inserters y=-418.5,
output fast inserters y=-422.5 onto a new belt y=-423.5 flowing east, then south down x=-166.5 to side-load onto the loading belt at (-166.5,-411.5).
Usage: scripts/build_iron_smelter2.py [--build]
"""
import json
import sys

from _game import tools

from bridge.factorio.planner import batches

S, E = 8, 4
XS = [-203.5 + 3 * k for k in range(12)]
POLES = [-202.5, -196.5, -190.5, -184.5, -178.5, -172.5, -169.5]
FB = "fast-transport-belt"


def plan():
    e = []
    for x in XS:
        e.append({"name": "electric-furnace", "x": x, "y": -420.5})
        e.append({"name": "fast-inserter", "x": x, "y": -418.5, "direction": S})
        e.append({"name": "fast-inserter", "x": x, "y": -422.5, "direction": S})
    for x in POLES:
        e.append({"name": "medium-electric-pole", "x": x, "y": -418.5})
        e.append({"name": "medium-electric-pole", "x": x, "y": -422.5})
    for x in range(-205, -166):
        e.append({"name": FB, "x": x + 0.5, "y": -423.5, "direction": E})
    e.append({"name": FB, "x": -166.5, "y": -423.5, "direction": S})
    for y in range(-423, -412):
        e.append({"name": FB, "x": -166.5, "y": y + 0.5, "direction": S})
    return e


def main():
    ents = plan()
    seen = {}
    for e in ents:
        k = (e["x"], e["y"])
        if k in seen and e["name"] != "fast-transport-belt":
            raise SystemExit(f"overlap in plan at {k}")
        seen[k] = e["name"]
    for part in batches(ents):
        r = json.loads(tools["place_entities"](json.dumps(part), dry_run=True))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"dry run failed: {json.dumps(r)[:3000]}")
    print("dry run clean", len(ents))
    if "--build" not in sys.argv:
        return
    print(tools["save_game"]("before-iron-smelter2"))
    for part in batches(ents):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        print(r.get("placed"), r.get("failed"))


if __name__ == "__main__":
    main()
