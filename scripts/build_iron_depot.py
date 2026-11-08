"""
Iron depot: a mine and electric furnace row at the (-219,-433) iron patch, a shuttle train, and an unloading
station north of the east base that feeds bus trunk 1.

    rails     one track from the depot's dead end (-174,-409) east, south down x=77, west along y=-157 to a dead end at x=36
    mine      two belts of electric drills on the patch, collecting into one ore belt
    furnaces  a row of electric furnaces, plate belt at y=-413 running east to the loading stop
    ...
Stages: rails | mine | furnaces | power | depot | unload | train     Usage: scripts/build_iron_depot.py <stage> [--build]
"""
import json
import sys

from _game import tools

from bridge.factorio import rails
from bridge.factorio.planner import batches

START = (-174, -409, 4)
LEGS = [("S", 77), ("W", -157, 36)]


def place(entities, build, label):
    counts = {}
    for e in entities:
        counts[e["name"]] = counts.get(e["name"], 0) + 1
    print(label, "plan:", counts)
    for part in batches(entities):
        r = json.loads(tools["place_entities"](json.dumps(part), dry_run=True))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"{label} dry run failed, nothing built: {json.dumps(r)[:1800]}")
    print(label, "dry run clean")
    if not build:
        return
    placed = 0
    for part in batches(entities):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"{label} stopped after {placed}: {json.dumps(r)[:1800]}")
        placed += r["placed"]
    print(label, "placed", placed)


def clear_cliffs(pieces, radius=6.0):
    pts = ",".join(f"{{{p[2][0]},{p[2][1]}}}" for p in pieces)
    r = tools["run_lua"](" ".join(f"""
        local s=game.surfaces.nauvis
        local pts={{{pts}}}
        local n=0
        for _,p in pairs(pts) do
          for _,c in pairs(s.find_entities_filtered{{type='cliff',position=p,radius={radius}}}) do c.destroy() n=n+1 end
        end
        rcon.print(n)""".splitlines()))
    print("cliffs cleared:", r)


def rails_stage(build):
    pieces, end = rails.route(START, LEGS)
    print("track:", len(pieces), "pieces, ends at", end)
    if build:
        print(tools["save_game"]("before-iron-depot"))
        clear_cliffs(pieces)
    place([rails.entity(p) for p in pieces], build, "rails")


def E_(name, x, y, d=0, **kw):
    e = {"name": name, "x": x, "y": y, "direction": d}
    e.update(kw)
    return e


def belt(x, y, d):
    return {"name": "transport-belt", "x": x + 0.5, "y": y + 0.5, "direction": d}


def ins(name, x, y, d):
    return {"name": name, "x": x + 0.5, "y": y + 0.5, "direction": d}


def pole(x, y, name="medium-electric-pole"):
    return {"name": name, "x": x + 0.5, "y": y + 0.5}


N_, E__, S_, W_ = 0, 4, 8, 12


def extend_stage(build):
    """Extend the unloading end of the track west to x=14 for the station."""
    pieces, end = rails.route(START, LEGS)
    more, end2 = rails.run_to(end, 14, 12)
    print("extra pieces:", len(more), "new end", end2)
    clear = build
    if build:
        clear_cliffs(more)
    place([rails.entity(p) for p in more], build, "rails-extend")


def mine_stage(build):
    ents = []
    def drills(x0s, y_n, y_s, belt_y, x_from, x_to):
        out = []
        for x0 in x0s:
            out.append({"name": "electric-mining-drill", "x": x0 + 1.5, "y": y_n + 1.5, "direction": S_})
            out.append({"name": "electric-mining-drill", "x": x0 + 1.5, "y": y_s + 1.5, "direction": N_})
        for x in range(x_from, x_to + 1):
            out.append(belt(x, belt_y, E__))
        return out
    ents += drills([-225, -221, -217, -213], -441, -437, -438, -225, -208)
    ents += drills([-228, -224, -220, -216], -434, -430, -431, -228, -208)
    for x in range(-207, -207 + 1):
        pass
    for y in range(-438, -418):
        ents.append(belt(-207, y, S_))
    ents.append(belt(-207, -418, E__))
    for gx in (-222, -218, -214):                       # band 1 gaps
        ents += [pole(gx, -440), pole(gx, -436)]
    for gx in (-225, -221, -217):                       # band 2 gaps
        ents += [pole(gx, -433), pole(gx, -429)]
    ents += [pole(-210, -440), pole(-210, -429)]
    place(ents, build, "mine")


FURN_X0 = -205
FURNACES = 12
ORE_Y, IN_Y, F_Y, OUT_Y, PLATE_Y = -418, -417, -416, -413, -412


def furnace_stage(build):
    ents = []
    for x in range(-206, FURN_X0 + 3 * FURNACES):
        ents.append(belt(x, ORE_Y, E__))
    for i in range(FURNACES):
        x = FURN_X0 + 3 * i
        ents.append({"name": "electric-furnace", "x": x + 1.5, "y": F_Y + 1.5, "direction": 0})
        ents.append(ins("inserter", x + 1, IN_Y, N_))        # picks the ore belt (north), drops into the furnace
        ents.append(ins("inserter", x + 1, OUT_Y, N_))       # picks the furnace (north), drops onto the plate belt
        if i % 2 == 0:
            ents += [pole(x + 2, IN_Y), pole(x + 2, OUT_Y)]
    for x in range(FURN_X0, -152):
        ents.append(belt(x, PLATE_Y, E__))
    # loading inserters, two wagons: x -165..-160 and -158..-153; inserters on row -411 pick north, drop south
    for x in list(range(-165, -159)) + list(range(-158, -152)):
        ents.append(ins("fast-inserter", x, -411, N_))
    ents += [pole(-166, -411), pole(-159, -411), pole(-152, -411), pole(-170, IN_Y), pole(-170, OUT_Y)]
    place(ents, build, "furnaces+loading")


def lua(code):
    return tools["run_lua"](" ".join(code.splitlines()))


def name_stop(stop, name):
    lua(f"for _, e in pairs(game.surfaces.nauvis.find_entities_filtered{{name='train-stop', position={{{stop['x']}, {stop['y']}}}, radius=1.5}}) do e.backer_name = '{name}' end rcon.print('named')")


def stops_stage(build):
    from build_coal_line import find_stop
    load = find_stop(-171, -409, "W", build)
    unload = find_stop(19, -157, "W", build)
    print("load stop", load["x"], load["y"], "unload stop", unload["x"], unload["y"])
    if build:
        name_stop(load, "Iron Depot Load")
        name_stop(unload, "Iron Depot Unload")


UNLOAD_X = (list(range(27, 33)), list(range(34, 40)))


def unload_stage(build):
    ents = []
    for x in UNLOAD_X[0] + UNLOAD_X[1]:
        ents.append(ins("fast-inserter", x, -156, N_))        # picks the wagon (north), drops on the belt (south)
    for x in range(27, 75):
        ents.append(belt(x, -155, E__))
    for y in range(-155, -139):
        ents.append(belt(75, y, S_))
    ents += [pole(26, -156), pole(33, -156), pole(40, -156)]
    place(ents, build, "unload")


def train_stage(build):
    cars = [
        {"name": "locomotive", "x": -169.0, "y": -409.0, "direction": 12},
        {"name": "cargo-wagon", "x": -162.0, "y": -409.0, "direction": 12},
        {"name": "cargo-wagon", "x": -155.0, "y": -409.0, "direction": 12},
        {"name": "locomotive", "x": -148.0, "y": -409.0, "direction": 4},
    ]
    place(cars, build, "train")
    if not build:
        return
    print(lua("""
        local s = game.surfaces.nauvis
        local locos = s.find_entities_filtered{name='locomotive', area={{-180,-415},{-140,-403}}}
        for _, l in pairs(locos) do l.get_fuel_inventory().insert{name='coal', count=150} end
        local t = locos[1].train
        t.schedule = {current = 1, records = {
          {station = 'Iron Depot Load', wait_conditions = {{type = 'full', compare_type = 'or'}, {type = 'inactivity', compare_type = 'or', ticks = 3600}}},
          {station = 'Iron Depot Unload', wait_conditions = {{type = 'empty', compare_type = 'or'}, {type = 'inactivity', compare_type = 'or', ticks = 600}}}}}
        t.manual_mode = false
        rcon.print(#t.carriages .. ' carriages, ' .. #locos .. ' locomotives')
    """))


STAGES = {"rails": rails_stage, "extend": extend_stage, "mine": mine_stage, "furnaces": furnace_stage,
          "stops": stops_stage, "unload": unload_stage, "train": train_stage}

if __name__ == "__main__":
    STAGES[sys.argv[1]]("--build" in sys.argv)
