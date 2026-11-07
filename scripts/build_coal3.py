"""
Replace the burner coal ring with five electric drills on the trunk's source belt.

    the old ring: seven burner drills, eight burner inserters, and a bottom belt (y=-59)
    with an east side (x=34) looping into the top belt (y=-63) were all fuelling each other
    now: electric drills at y=-62..-60, x=18..32, facing N onto the top belt (y=-63),
    poles at y=-59. The top belt is the trunk's source (the hub lift at (16,-62) and the
    coal to the iron row, copper row, smelters and plastic all come from it).

The boiler line is fed by the north coal field (build_coal2.py); the two lift inserters at
(30,-58) and (31,-58) are left in place and now simply idle.

Usage: scripts/build_coal3.py [--build]
"""
import json
import sys

from _game import tools

from bridge.factorio.planner import Grid, Plan, batches

X0S = [18, 21, 24, 27, 30]


def main():
    build = "--build" in sys.argv
    plan_ents = [{"name": "electric-mining-drill", "x": x + 1.5, "y": -60.5, "direction": 0} for x in X0S]
    plan_ents += [{"name": "medium-electric-pole", "x": x + 0.5, "y": -58.5} for x in (19, 25, 31)]
    print("plan:", len(plan_ents), "entities")
    if not build:
        return
    print(tools["save_game"]("before-coal-ring-swap"))
    print("burner drills:", tools["remove_entities"](17, -63.4, 36, -58.6, names="burner-mining-drill"))
    print("burner inserters:", tools["remove_entities"](17, -62.4, 36, -58.6, names="burner-inserter"))
    print("bottom belt:", tools["remove_entities"](17.6, -59.4, 35, -58.6, names="transport-belt"))
    print("east side:", tools["remove_entities"](34.3, -61.9, 34.7, -58.6, names="transport-belt"))
    r = json.loads(tools["place_entities"](json.dumps(plan_ents)))
    print("placed", r["placed"], "failed", r["failed"])


if __name__ == "__main__":
    main()
