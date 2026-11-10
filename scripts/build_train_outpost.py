"""
A plate outpost that ships by train. Same drill layout and electric furnace row as build_outpost.py, but the furnaces drop plates onto two side belts
that merge (one per lane) onto a single express belt, which runs past a train load station. Everything is placed in the outpost's local frame (u across,
v along the output direction), mapped to the world with fx._to_world, so any of N/E/S/W works.

    stage plan       dry run of the whole outpost (drills, furnaces, belts, station); prints the counts and the open rail end
    stage outpost    place it (clears natural pieces and grid substations in the way first), join the power grid
    stage rail       lay the track from the station's open end to a goal end with rail_plan (see rail_plan.py)
    stage train      stops, train, schedule

Usage: scripts/build_train_outpost.py --area X1 Y1 X2 Y2 --resource copper-ore --out N --furnaces 62 --name "Copper A" --stage plan|outpost|train [--apply]
"""
import argparse
import json
import types

import build_outpost as bo
import fx
from _game import tools

from bridge.factorio import rails
from bridge.factorio.planner import batches

EXPRESS = "express-transport-belt"
CAR = 7           # spacing of train cars
STATION_CARS = (("locomotive", 2), ("cargo-wagon", 9), ("cargo-wagon", 16), ("cargo-wagon", 23), ("cargo-wagon", 30), ("locomotive", 37))


def layout(out, last, cv, n_furn):
    """Smelter with output belts, merge, and load station. Returns (entities, info)."""
    ents = []
    per_side = n_furn // 2
    v0 = cv + 4
    belt_dir = fx.OUT_DIR[out]

    def add(e):
        ents.append(e)

    for k in range(per_side):
        for t in range(3):
            wx, wy = fx._to_world(out, last, v0 + 3 * k + t)
            add({"name": EXPRESS, "x": wx, "y": wy, "direction": belt_dir})
        vc = v0 + 1 + 3 * k
        for side in (-1, 1):
            fxx, fyy = fx._to_world(out, last + side * 3, vc)
            add({"name": "electric-furnace", "x": fxx, "y": fyy})
            ix, iy = fx._to_world(out, last + side * 1, vc)
            add({"name": "fast-inserter", "x": ix, "y": iy, "direction": fx._dir_of(out, -side, 0)})
            ox, oy = fx._to_world(out, last + side * 5, vc)
            add({"name": "fast-inserter", "x": ox, "y": oy, "direction": fx._dir_of(out, -side, 0)})
        if k % 2 == 0:
            for du in (-6, -1, 6):
                px, py = fx._to_world(out, last + du, v0 + 3 * k)
                add({"name": "medium-electric-pole", "x": px, "y": py})
    v_s = v0 + 3 * per_side
    v_m = v_s + 1
    for side in (-1, 1):                                        # output belts, one per side, then in toward the centre
        for v in range(int(v0 - 0.5), int(v_m - 0.5)):
            wx, wy = fx._to_world(out, last + side * 6, v + 0.5)
            add({"name": EXPRESS, "x": wx, "y": wy, "direction": belt_dir})
        for du in range(6, 0, -1):
            wx, wy = fx._to_world(out, last + side * du, v_m)
            add({"name": EXPRESS, "x": wx, "y": wy, "direction": fx._dir_of(out, -side, 0)})
    bx, by = fx._to_world(out, last, v_m)
    add({"name": EXPRESS, "x": bx, "y": by, "direction": belt_dir})
    bxw, byw = fx._to_world(out, last, 0)                       # centre column in world coords (x for N/S, y for E/W)
    return ents, {"v_m": v_m, "last": last, "v0": v0}


def station(out, last, v_first, side, name_prefix=""):
    """Load station beyond the merge: belt, 24 fast inserters (6 per wagon), rail stub with stop point. Returns (ents, info).
    The belt column is `last`; inserters sit one tile to `side` (+1 or -1) of it, the rail 2.5 tiles to that side."""
    ents = []
    belt_dir = fx.OUT_DIR[out]
    v_stop = v_first + 0.5                                # rail centre of the stop, local v (cars lie further along +v)
    sx, sy = fx._to_world(out, last, v_stop)
    along = sy if out in 'NS' else sx
    if round(along) % 2 == 0:                             # rail pieces sit on odd coordinates: slide the whole station one tile along
        v_first += 1
        v_stop += 1
    for v in range(int(v_first), int(v_first + 36)):
        wx, wy = fx._to_world(out, last, v + 0.5)
        ents.append({"name": EXPRESS, "x": wx, "y": wy, "direction": belt_dir})
    for (n, off) in STATION_CARS:
        if n != "cargo-wagon":
            continue
        c = v_stop + off
        for k in (-2.5, -1.5, -0.5, 0.5, 1.5, 2.5):
            wx, wy = fx._to_world(out, last + side * 1, c + k)
            ents.append({"name": "fast-inserter", "x": wx, "y": wy, "direction": fx._dir_of(out, -side, 0)})
    for v in range(int(v_first), int(v_first + 36), 6):
        wx, wy = fx._to_world(out, last - side * 1, v + 0.5)
        ents.append({"name": "medium-electric-pole", "x": wx, "y": wy})
    return ents, {"v_stop": v_stop, "rail_u": last + side * 2.5}


def place(ents, label):
    print(label, "plan:", {n: sum(1 for e in ents if e["name"] == n) for n in sorted({e["name"] for e in ents})})
    for part in batches(ents):
        r = json.loads(tools["place_entities"](json.dumps(part), dry_run=True))
        if r.get("error") or r.get("failed"):
            return r
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--area", nargs=4, type=int, required=True)
    ap.add_argument("--resource", required=True)
    ap.add_argument("--out", default="N")
    ap.add_argument("--furnaces", type=int, default=62)
    ap.add_argument("--side", type=int, default=-1, help="which side of the station belt the wagons stand: -1 or +1 (the rail line must land on an odd coordinate)")
    ap.add_argument("--name", required=True)
    ap.add_argument("--stage", choices=["plan", "outpost"], default="plan")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    ns = types.SimpleNamespace(area=a.area, around=None, surface="nauvis", resource=a.resource, out=a.out, drill="electric-mining-drill",
                               belt=EXPRESS, pole="medium-electric-pole", min_tiles=6, allow_mixed=False, plan_only=True, apply=False)
    mine_ents, meta = fx.cmd_mine(ns)
    out, last, cv = meta["out"], meta["last"], meta["cv"]
    sm, info = layout(out, last, cv, a.furnaces)
    st, sinfo = station(out, last, info["v_m"] + 4, a.side)
    ents = mine_ents + sm + st
    rx, ry = fx._to_world(out, sinfo["rail_u"], sinfo["v_stop"])
    print(f"{a.name}: {sum(1 for e in mine_ents if e['name'] == 'electric-mining-drill')} drills, {a.furnaces} furnaces; stop rail at ({rx}, {ry}); rail line parity "
          f"{'OK' if (rx % 2 == 1 if out in 'NS' else ry % 2 == 1) else 'WRONG (use --side with the other sign)'}")
    xs = [e["x"] for e in ents]
    ys = [e["y"] for e in ents]
    box = (int(min(xs)) - 4, int(min(ys)) - 4, int(max(xs)) + 4, int(max(ys)) + 4)
    print("footprint", box)
    if a.stage == "plan":
        bad = place(ents, "outpost")
        print("dry run:", "clean" if not bad else json.dumps(bad)[:900])
        return
    if not a.apply:
        print("DRY RUN (add --apply)")
        return
    print(tools["save_game"]("before-" + a.name.lower().replace(" ", "-")))
    print(fx.lua(f"local s=game.surfaces.nauvis local t,n=0,0 for _,e in pairs(s.find_entities_filtered{{area={fx.a_box(box)},type={{'tree','cliff','simple-entity','item-entity','corpse'}}}}) do if e.force.name~='player' then e.destroy() t=t+1 end end for _,e in pairs(s.find_entities_filtered{{area={fx.a_box(box)},name={{'substation','solar-panel','accumulator','roboport'}},force='player'}}) do e.destroy() n=n+1 end rcon.print('cleared '..t..' natural pieces, removed '..n..' grid pieces')"))
    for part in batches(ents):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        print("placed", r.get("placed"), "failed", len(r.get("failed") or []))
    bo.connect_power(box)
    print(bo.cover_unpowered_drills(box))
    print("station rail centre", (rx, ry), "-- next: lay the track from here")


if __name__ == "__main__":
    main()
