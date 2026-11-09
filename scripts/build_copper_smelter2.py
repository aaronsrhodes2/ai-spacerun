"""
Second row of 12 electric furnaces at the copper depot (doubles plate output while the train loads: the train waits for 'full', so loading time
is set by furnace count). Mirror of the existing row about the ore belt (y=-301.5): furnaces y=-304.5, input inserters y=-302.5 (pick the ore belt),
output inserters y=-306.5 onto a new belt y=-307.5 flowing east, then south down x=172.5 to side-load onto the loading belt at (172.5,-295.5).
Usage: scripts/build_copper_smelter2.py [--build]
"""
import json
import sys

from _game import tools

from bridge.factorio.planner import batches

S, E = 8, 4
XS = [132.5 + 3 * k for k in range(12)]


def plan():
    e = []
    for x in XS:
        e.append({"name": "electric-furnace", "x": x, "y": -304.5})
        e.append({"name": "inserter", "x": x, "y": -302.5, "direction": S})
        e.append({"name": "inserter", "x": x, "y": -306.5, "direction": S})
    for x in [133.5 + 6 * k for k in range(6)]:
        e.append({"name": "medium-electric-pole", "x": x, "y": -302.5})
        e.append({"name": "medium-electric-pole", "x": x, "y": -306.5})
    for x in range(131, 172):
        e.append({"name": "transport-belt", "x": x + 0.5, "y": -307.5, "direction": E})
    e.append({"name": "transport-belt", "x": 172.5, "y": -307.5, "direction": S})
    for y in range(-307, -296):
        e.append({"name": "transport-belt", "x": 172.5, "y": y + 0.5, "direction": S})
    return e


def main():
    ents = plan()
    for part in batches(ents):
        r = json.loads(tools["place_entities"](json.dumps(part), dry_run=True))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"dry run failed: {json.dumps(r)[:3000]}")
    print("dry run clean", len(ents))
    if "--build" not in sys.argv:
        return
    print(tools["save_game"]("before-copper-smelter2"))
    for part in batches(ents):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        print(r.get("placed"), r.get("failed"))


if __name__ == "__main__":
    main()
