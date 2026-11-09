"""
Old copper smelter column (x -35..-29, y -84..-65): 6 coal-fed steel furnaces -> 6 electric furnaces, then removal of the 5-furnace burner row below.

Old: plate belt x=-34 | out inserters x=-33 | 2x2 furnaces x -32..-31 | in inserters x=-30 | ore+coal belt x=-29.
New: plate belt x=-35 | out inserters x=-34 | 3x3 electric furnaces x -33..-31 | in inserters x=-30 | the same ore belt x=-29 (its coal lane just stays full).
The new plate belt turns east at (-35,-64) into the existing belt column at (-34,-64) which carries on south.
Usage: scripts/build_smelter_copper.py [--build]
"""
import json
import sys

from _game import tools

from bridge.factorio.planner import batches

N = 6
Y0 = -84
E_, S_ = 4, 8


def entities():
    e = []
    for y in range(Y0, Y0 + 3 * N + 2):                              # plate belt x=-35 from y=-84 to -65
        e.append({"name": "transport-belt", "x": -34.5, "y": y + 0.5, "direction": S_})
    e.append({"name": "transport-belt", "x": -34.5, "y": -63.5, "direction": E_})   # (-35,-64) turns east into (-34,-64)
    for k in range(N):
        top = Y0 + 3 * k
        e.append({"name": "electric-furnace", "x": -31.5, "y": top + 1.5, "direction": 0})
        e.append({"name": "inserter", "x": -29.5, "y": top + 1.5, "direction": E_})
        e.append({"name": "inserter", "x": -33.5, "y": top + 1.5, "direction": E_})
    for k in range(0, N, 2):
        e.append({"name": "medium-electric-pole", "x": -29.5, "y": Y0 + 3 * k + 0.5})
    for k in range(1, N, 2):
        e.append({"name": "medium-electric-pole", "x": -33.5, "y": Y0 + 3 * k + 0.5})
    return e


CLEAR = """
local s=game.surfaces.nauvis
local n={}
local function kill(filter,area) local c=0 for _,e in pairs(s.find_entities_filtered{name=filter,area=area}) do e.destroy() c=c+1 end return c end
n[#n+1]='copper furnaces '..kill('steel-furnace',{{-33,-85},{-30,-64.5}})
n[#n+1]='inserters '..kill({'inserter','long-handed-inserter','burner-inserter'},{{-33.9,-85},{-29.9,-65}})
n[#n+1]='poles '..kill({'medium-electric-pole','small-electric-pole'},{{-35.9,-85},{-29.9,-65}})
n[#n+1]='old plate belts '..kill('transport-belt',{{-34.4,-85},{-33.6,-65}})
n[#n+1]='ground items '..kill('item-on-ground',{{-36,-86},{-29,-64}})
rcon.print(helpers.table_to_json(n))
"""


def main():
    build = "--build" in sys.argv
    ents = entities()
    print(len(ents), "entities")
    if not build:
        return
    print(tools["save_game"]("before-smelter-copper"))
    print(tools["run_lua"](" ".join(CLEAR.splitlines())))
    for part in batches(ents):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        print("placed", r.get("placed"), "failed", r.get("failed"))


if __name__ == "__main__":
    main()
