"""
Copper depot: the same pattern as the iron depot (scripts/build_iron_depot.py) at the (128,-329) copper patch.

    mine      two belts of electric drills (x 112..127), collector x=129 flowing south
    furnaces  12 electric furnaces east of the collector; plate belt runs east to the loading stop
    track     dead end (162,-293) east to x=195, south to y=-149, west to a dead end at x=84
    unload    inserters at y=-148 onto a belt at y=-147 flowing west into trunk 1's feeder (x=75) from the east,
              so copper takes the lane opposite the iron

Stages: rails | mine | furnaces | stops | unload | power | train     Usage: scripts/build_copper_depot.py <stage> [--build]
"""
import json
import math
import sys

from _game import tools
from build_iron_depot import belt, clear_cliffs, ins, lua, name_stop, place, pole

from bridge.factorio import rails

N_, E_, S_, W_ = 0, 4, 8, 12
START = (162, -293, 4)
LEGS = [("S", 195), ("W", -149, 84)]
YR = -293                         # centre line of the loading rail
PLATE, INS, OUT, F_TOP, IN, ORE = YR - 3, YR - 2, YR - 4, YR - 7, YR - 8, YR - 9
FURN_X0, FURNACES = 131, 12
COLLECT_X = 129


def rails_stage(build):
    pieces, end = rails.route(START, LEGS)
    print("track:", len(pieces), "pieces, ends at", end)
    if build:
        print(tools["save_game"]("before-copper-depot"))
        lua("local n=0 for _,c in pairs(game.surfaces.nauvis.find_entities_filtered{type='cliff',area={{100,-345},{200,-285}}}) do c.destroy() n=n+1 end rcon.print(n)")
        clear_cliffs(pieces, 6.0)
    place([rails.entity(p) for p in pieces], build, "rails")


def mine_stage(build):
    ents = []
    for belt_y in (-336, -329):
        for x0 in (112, 116, 120, 124):
            ents.append({"name": "electric-mining-drill", "x": x0 + 1.5, "y": belt_y - 3 + 1.5, "direction": S_})
            ents.append({"name": "electric-mining-drill", "x": x0 + 1.5, "y": belt_y + 1 + 1.5, "direction": N_})
        for x in range(112, COLLECT_X):
            ents.append(belt(x, belt_y, E_))
    for y in range(-336, ORE):
        ents.append(belt(COLLECT_X, y, S_))
    ents.append(belt(COLLECT_X, ORE, E_))
    for gx in (115, 119, 123):
        ents += [pole(gx, -338), pole(gx, -334), pole(gx, -331), pole(gx, -327)]
    ents += [pole(126, -338), pole(126, -327)]
    place(ents, build, "mine")


def furnace_stage(build):
    ents = []
    for x in range(COLLECT_X + 1, FURN_X0 + 3 * FURNACES):
        ents.append(belt(x, ORE, E_))
    for i in range(FURNACES):
        x = FURN_X0 + 3 * i
        ents.append({"name": "electric-furnace", "x": x + 1.5, "y": F_TOP + 1.5, "direction": 0})
        ents.append(ins("inserter", x + 1, IN, N_))
        ents.append(ins("inserter", x + 1, OUT, N_))
        if i % 2 == 0:
            ents += [pole(x + 2, IN), pole(x + 2, OUT)]
    for x in list(range(FURN_X0, 163)) + list(range(167, 184)):       # plate belt, hopping under the stop at 164..165
        ents.append(belt(x, PLATE, E_))
    ents.append({"name": "underground-belt", "x": 163.5, "y": PLATE + 0.5, "direction": 4, "params": {"type": "input"}})
    ents.append({"name": "underground-belt", "x": 166.5, "y": PLATE + 0.5, "direction": 4, "params": {"type": "output"}})
    for x in list(range(171, 177)) + list(range(178, 184)):
        ents.append(ins("fast-inserter", x, INS, N_))
    ents += [pole(170, INS), pole(177, INS), pole(184, INS), pole(127, IN), pole(127, OUT)]
    place(ents, build, "furnaces+loading")


def stops_stage(build):
    from build_coal_line import find_stop
    load = find_stop(165, YR, "W", build)
    unload = find_stop(87, -149, "W", build)
    print("load stop", load["x"], load["y"], "unload stop", unload["x"], unload["y"])
    if build:
        name_stop(load, "Copper Depot Load")
        name_stop(unload, "Copper Depot Unload")


def unload_stage(build):
    ents = []
    for x in list(range(95, 101)) + list(range(102, 108)):
        ents.append(ins("fast-inserter", x, -148, N_))
    for x in range(107, 75, -1):
        ents.append(belt(x, -147, W_))                    # last tile (76) feeds the x=75 belt from the east
    ents += [pole(94, -148), pole(101, -148), pole(108, -148), pole(93, -143)]
    place(ents, build, "unload")


def power_stage(build):
    from _lines import free_spot
    prev = (93.5, -142.5)
    end = (127.5, -300.5)
    poles = []
    while math.hypot(end[0] - prev[0], end[1] - prev[1]) > 8.0:
        d = math.hypot(end[0] - prev[0], end[1] - prev[1])
        mv = min(7.0 if not poles else 26.0, d - 5.0 if d > 13 else d)
        tx, ty = prev[0] + (end[0] - prev[0]) / d * mv, prev[1] + (end[1] - prev[1]) / d * mv
        px, py = free_spot("big-electric-pole", tx, ty, 2)
        limit = 8.95 if not poles else 29.0
        gap = math.hypot(px - prev[0], py - prev[1])
        if gap > limit:
            raise SystemExit(f"pole {len(poles)+1} at {px},{py} is {gap:.1f} from the last (limit {limit})")
        poles.append({"name": "big-electric-pole", "x": px, "y": py})
        prev = (px, py)
    print(len(poles), "big poles, last", prev)
    place(poles, build, "power")


def train_stage(build):
    if not build:
        return
    print(lua("""
        local s = game.surfaces.nauvis
        local specs={{'locomotive',168,12},{'cargo-wagon',175,12},{'cargo-wagon',182,12},{'locomotive',189,4}}
        local made={}
        for _,sp in pairs(specs) do
          local e=s.create_entity{name=sp[1],position={sp[2],-293},direction=sp[3],force='player'}
          made[#made+1]=e and (e.name..'@'..e.position.x) or ('FAILED '..sp[1]..sp[2])
        end
        local locos=s.find_entities_filtered{name='locomotive',area={{160,-300},{200,-286}}}
        for _,l in pairs(locos) do l.get_fuel_inventory().insert{name='coal',count=150} end
        local t=locos[1].train
        t.schedule={current=1,records={
         {station='Copper Depot Load',wait_conditions={{type='full',compare_type='or'},{type='inactivity',compare_type='or',ticks=3600}}},
         {station='Copper Depot Unload',wait_conditions={{type='empty',compare_type='or'},{type='inactivity',compare_type='or',ticks=600}}}}}
        t.manual_mode=false
        rcon.print(helpers.table_to_json({made=made,carriages=#t.carriages}))
    """))


STAGES = {"rails": rails_stage, "mine": mine_stage, "furnaces": furnace_stage, "stops": stops_stage,
          "unload": unload_stage, "power": power_stage, "train": train_stage}

if __name__ == "__main__":
    STAGES[sys.argv[1]]("--build" in sys.argv)
