"""
Steel and stone brick for the east base bus.

  steel   3 electric furnaces west of the iron feeder belt (x=75, y -154..-140): inserters take iron plates
          off the feeder, steel goes down a belt at x=69 into the head of trunk 0.
  stone   a mine at the (95,-424) stone patch, 6 electric furnaces making brick, and a plain belt (no train:
          brick is light) down x=79 to the head of trunk 5 at (87,-139), hopping under the copper unload belt.

Stages: steel | mine | furnaces | belt | power     Usage: scripts/build_stone_depot.py <stage> [--build]
"""
import json
import math
import sys

from _game import tools
from build_iron_depot import belt, ins, lua, place, pole

N_, E_, S_, W_ = 0, 4, 8, 12


def clear_ground(x1, y1, x2, y2):
    n = lua(f"local n=0 for _,e in pairs(game.surfaces.nauvis.find_entities_filtered{{area={{{{{x1},{y1}}},{{{x2},{y2}}}}},type={{'tree','cliff','simple-entity'}}}}) do if e.type~='simple-entity' or e.name:find('rock') then e.destroy() n=n+1 end end rcon.print(n)")
    print("cleared trees/cliffs/rocks:", n)


def steel_stage(build):
    ents = []
    for k in range(3):
        fy = -153 + 3 * k
        ents.append({"name": "electric-furnace", "x": 72.5, "y": fy + 1.5, "direction": 0})
        ents.append(ins("inserter", 74, fy + 1, E_))        # picks the feeder belt (east), drops into the furnace
        ents.append(ins("inserter", 70, fy + 1, E_))        # picks the furnace (east), drops on the steel belt (west)
    for y in range(-152, -142):
        ents.append(belt(69, y, S_))
    ents += [belt(69, -142, E_), belt(70, -142, E_), belt(71, -142, E_)]
    ents += [belt(72, y, S_) for y in (-142, -141, -140)]
    ents += [pole(70, -150), pole(74, -150), pole(70, -147), pole(74, -147), pole(74, -144)]
    place(ents, build, "steel")


BAND_YS = (-428, -421)
X0S = (88, 92, 96)
COLLECT_X = 100
ORE_Y, IN_Y, F_Y, OUT_Y, BRICK_Y = -405, -404, -403, -400, -399
FURN_X = [82 + 3 * i for i in range(6)]


def mine_stage(build):
    ents = []
    for by in BAND_YS:
        for x0 in X0S:
            ents.append({"name": "electric-mining-drill", "x": x0 + 1.5, "y": by - 3 + 1.5, "direction": S_})
            ents.append({"name": "electric-mining-drill", "x": x0 + 1.5, "y": by + 1 + 1.5, "direction": N_})
        for x in range(88, COLLECT_X):
            ents.append(belt(x, by, E_))
    for y in range(BAND_YS[0], ORE_Y):
        ents.append(belt(COLLECT_X, y, S_))
    ents.append(belt(COLLECT_X, ORE_Y, W_))
    for gx in (91, 95, 99):
        for py in (-430, -426, -423, -419):
            ents.append(pole(gx, py))
    ents += [pole(101, -418), pole(101, -411), pole(101, -406)]
    if build:
        clear_ground(80, -440, 104, -395)
    place(ents, build, "mine")


def furnace_stage(build):
    ents = []
    for x in range(COLLECT_X - 1, FURN_X[0] - 1, -1):
        ents.append(belt(x, ORE_Y, W_))
    for x in FURN_X:
        ents.append({"name": "electric-furnace", "x": x + 1.5, "y": F_Y + 1.5, "direction": 0})
        ents.append(ins("inserter", x + 1, IN_Y, N_))
        ents.append(ins("inserter", x + 1, OUT_Y, N_))
    for x in range(FURN_X[-1] + 2, 79, -1):
        ents.append(belt(x, BRICK_Y, W_))
    for x in (FURN_X[0] + 2, FURN_X[2] + 2, FURN_X[4] + 2):
        ents += [pole(x, IN_Y), pole(x, OUT_Y)]
    place(ents, build, "furnaces")


def belt_stage(build):
    ents = []
    for y in range(BRICK_Y, -148):                         # x=79 south to the hop
        ents.append(belt(79, y, S_))
    ents.append({"name": "underground-belt", "x": 79.5, "y": -147.5, "direction": 8, "params": {"type": "input"}})
    ents.append({"name": "underground-belt", "x": 79.5, "y": -145.5, "direction": 8, "params": {"type": "output"}})
    ents += [belt(79, -145 + i, S_) for i in range(0, 3)]       # -145, -144, -143
    ents.append(belt(79, -142, E_))
    ents += [belt(x, -142, E_) for x in range(80, 87)]
    ents += [belt(87, y, S_) for y in (-142, -141, -140)]
    if build:
        clear_ground(77, -400, 83, -140)
    place(ents, build, "brick belt")


def power_stage(build):
    from _lines import free_spot
    prev = (126.4, -295.6)
    end = (96.5, -403.5)
    poles = []
    while math.hypot(end[0] - prev[0], end[1] - prev[1]) > 8.0:
        d = math.hypot(end[0] - prev[0], end[1] - prev[1])
        mv = min(26.0, d - 5.0 if d > 13 else d)
        tx, ty = prev[0] + (end[0] - prev[0]) / d * mv, prev[1] + (end[1] - prev[1]) / d * mv
        px, py = free_spot("big-electric-pole", tx, ty, 2)
        if math.hypot(px - prev[0], py - prev[1]) > 29.0:
            raise SystemExit(f"gap too long at {px},{py}")
        poles.append({"name": "big-electric-pole", "x": px, "y": py})
        prev = (px, py)
    print(len(poles), "big poles, last", prev)
    place(poles, build, "power")


STAGES = {"steel": steel_stage, "mine": mine_stage, "furnaces": furnace_stage, "belt": belt_stage, "power": power_stage}

if __name__ == "__main__":
    STAGES[sys.argv[1]]("--build" in sys.argv)
