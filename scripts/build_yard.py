"""
Bus-head unload yard and the first bus lane, plus the outpost-side rail stub.

  yard   unload rail on y=-121 from a dead end at x=200 east to x=250 (open end), stop for westbound trains at x=203, six unloading inserters per wagon
         onto an express belt on y=-117.5 that runs west and then south as bus lane `copper` (x=198.5) for 60 tiles.
  stub   the outpost load station rail: dead end at (329,114) north to y=70 (open end).

Usage: scripts/build_yard.py yard|stub [--apply]
"""
import argparse
import json

import fx
from _game import tools

from bridge.factorio import rails
from bridge.factorio.planner import batches

EXPRESS = "express-transport-belt"
WAGONS = (212, 219, 226, 233)            # wagon centres for a westbound train whose front stands at the stop rail x=203
YARD_Y = -121
BELT_Y = -117.5
LANE_X = 198.5
STOP_NAME = "Copper A Unload"


def lay(start, heading_d, target, apply, name):
    pieces, end = rails.run_to(start, target, heading_d)
    print(name, len(pieces), "rail pieces, open end", end)
    pts = ",".join("{%s,%s}" % (p[2][0], p[2][1]) for p in pieces)
    if apply:
        print(fx.lua("local s=game.surfaces.nauvis local n=0 for _,p in pairs({%s}) do for _,c in pairs(s.find_entities_filtered{position=p,radius=5,type={'tree','cliff','simple-entity','item-entity','corpse'}}) do if c.force.name~='player' then c.destroy() n=n+1 end end for _,c in pairs(s.find_entities_filtered{position=p,radius=4,name={'substation','solar-panel','accumulator','roboport'},force='player'}) do c.destroy() n=n+1 end end rcon.print('cleared '..n)" % pts))
    ents = [rails.entity(p) for p in pieces]
    for part in batches(ents):
        r = json.loads(tools["place_entities"](json.dumps(part), dry_run=not apply))
        if r.get("failed"):
            raise SystemExit(f"{name} blocked: {json.dumps(r)[:900]}")
    return end


def yard(apply):
    end = lay((200, YARD_Y, 4), 4, 250, apply, "yard rail")
    clear_yard(apply)
    ents = []
    for c in WAGONS:
        for k in (-2.5, -1.5, -0.5, 0.5, 1.5, 2.5):
            ents.append({"name": "fast-inserter", "x": c + k, "y": BELT_Y - 1, "direction": 0})        # picks the wagon (north), drops on the belt (south)
    for x in range(int(WAGONS[0] - 5), int(WAGONS[-1] + 6)):
        ents.append({"name": EXPRESS, "x": x + 0.5, "y": BELT_Y, "direction": 12})
    x = int(WAGONS[0] - 5) - 1
    while x + 0.5 > LANE_X:
        ents.append({"name": EXPRESS, "x": x + 0.5, "y": BELT_Y, "direction": 12})
        x -= 1
    ents.append({"name": EXPRESS, "x": LANE_X, "y": BELT_Y, "direction": 8})
    for k in range(60):
        ents.append({"name": EXPRESS, "x": LANE_X, "y": BELT_Y + 1 + k, "direction": 8})
    for x in range(int(WAGONS[0] - 8), int(WAGONS[-1] + 6), 6):
        ents.append({"name": "medium-electric-pole", "x": x + 0.5, "y": BELT_Y + 1})
    print("yard entities:", len(ents))
    for part in batches(ents):
        r = json.loads(tools["place_entities"](json.dumps(part), dry_run=not apply))
        if r.get("failed"):
            print("blocked:", json.dumps(r)[:900])
            return
    if apply:
        import build_outpost as bo
        bo.connect_power((190, int(YARD_Y) - 8, 255, int(YARD_Y) + 70))
        import build_coal_line as bc
        stop = bc.find_stop(203, YARD_Y, "W", True)
        print(fx.lua("for _,e in pairs(game.surfaces.nauvis.find_entities_filtered{name='train-stop',position={%s,%s},radius=1.5}) do e.backer_name='%s' end rcon.print('named')" % (stop["x"], stop["y"], STOP_NAME)))


def clear_yard(apply):
    if apply:
        print(fx.lua("local s=game.surfaces.nauvis local n=0 for _,e in pairs(s.find_entities_filtered{area={{196,%d},{254,%d}}}) do if e.force.name~='player' and (e.type=='tree' or e.type=='simple-entity' or e.type=='cliff') then e.destroy() n=n+1 elseif e.force.name=='player' and (e.name=='solar-panel' or e.name=='accumulator' or e.name=='roboport' or e.name=='substation') then e.destroy() n=n+1 end end rcon.print('yard ground cleared '..n)" % (YARD_Y - 4, YARD_Y + 8)))


def stub(apply, spec=(329, 114, 70), heading="N"):
    d = {"N": 0, "S": 8}[heading]
    return lay((spec[0], spec[1], d), d, spec[2], apply, "outpost stub")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["yard", "stub"])
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--y", type=int, help="unload rail line (odd), default -121")
    ap.add_argument("--lane", type=float, help="bus lane x (tile centre), default 198.5")
    ap.add_argument("--name", help="unload stop name")
    ap.add_argument("--stub", nargs=3, type=int, help="x y_dead_end y_target for the outpost stub")
    ap.add_argument("--dir", default="N", choices=["N", "S"], help="stub heading away from the dead end")
    a = ap.parse_args()
    if a.y is not None:
        YARD_Y = a.y
        BELT_Y = a.y + 3.5
    if a.lane is not None:
        LANE_X = a.lane
    if a.name:
        STOP_NAME = a.name
    if a.apply:
        print(tools["save_game"]("before-" + a.what))
    if a.what == "stub":
        stub(a.apply, tuple(a.stub) if a.stub else (329, 114, 70), a.dir)
    else:
        yard(a.apply)
