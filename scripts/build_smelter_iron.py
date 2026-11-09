"""
Old iron smelter column (x -25..-19, y -100..-65): 12 coal-fed steel furnaces -> 12 electric furnaces.

Old: plate belt x=-25 | out inserters x=-24 | 2x2 furnaces | in inserters (normal from ore belt x=-20, long from coal belt x=-19) x=-21.
New: plate belt x=-26 | out inserters x=-25 | 3x3 electric furnaces x -24..-22 contiguous | in inserters x=-21 from the same ore belt x=-20.
The coal belt x=-19 is left in place (idle). The new plate belt ends by joining the existing west-flowing belt at (-26,-64).
Usage: scripts/build_smelter_iron.py [--build]
"""
import json
import sys

from _game import tools

from bridge.factorio.planner import batches

N = 12
Y0 = -100                       # top tile row
E_, S_ = 4, 8


def entities():
    e = []
    for y in range(Y0, Y0 + 3 * N):                                  # plate belt, one tile west of the old one
        e.append({"name": "transport-belt", "x": -25.5, "y": y + 0.5, "direction": S_})
    for k in range(N):
        top = Y0 + 3 * k
        e.append({"name": "electric-furnace", "x": -22.5, "y": top + 1.5, "direction": 0})
        e.append({"name": "inserter", "x": -20.5, "y": top + 1.5, "direction": E_})       # ore belt (east) -> furnace
        e.append({"name": "inserter", "x": -24.5, "y": top + 1.5, "direction": E_})       # furnace (east) -> plate belt (west)
    for k in range(0, N, 2):
        e.append({"name": "medium-electric-pole", "x": -20.5, "y": Y0 + 3 * k + 0.5})     # tile (-21, top)
    for k in range(1, N, 2):
        e.append({"name": "medium-electric-pole", "x": -24.5, "y": Y0 + 3 * k + 0.5})     # tile (-25, top)
    return e


CLEAR = """
local s=game.surfaces.nauvis
local n={}
local function kill(filter,area) local c=0 for _,e in pairs(s.find_entities_filtered{name=filter,area=area}) do e.destroy() c=c+1 end return c end
n[#n+1]='furnaces '..kill('steel-furnace',{{-24,-100.5},{-20.5,-64.5}})
n[#n+1]='inserters '..kill({'inserter','long-handed-inserter','burner-inserter'},{{-24.9,-100.5},{-20.1,-64.5}})
n[#n+1]='poles '..kill('medium-electric-pole',{{-24.9,-100.5},{-20.1,-64.5}})
n[#n+1]='small poles '..kill('small-electric-pole',{{-24.9,-100.5},{-20.1,-64.5}})
n[#n+1]='old plate belts '..kill('transport-belt',{{-25.4,-100.5},{-24.6,-64.6}})
n[#n+1]='ground items '..kill('item-on-ground',{{-27,-101},{-20,-64}})
rcon.print(helpers.table_to_json(n))
"""


def main():
    build = "--build" in sys.argv
    ents = entities()
    print(len(ents), "entities")
    if not build:
        return
    print(tools["save_game"]("before-smelter-iron"))
    print(tools["run_lua"](" ".join(CLEAR.splitlines())))
    for part in batches(ents):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        print("placed", r.get("placed"), "failed", r.get("failed"))


if __name__ == "__main__":
    main()
