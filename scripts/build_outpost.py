"""
Plate outpost: a mining patch layout (fx.py mine) whose collector belt runs straight into a smelter line, with every furnace dropping its plates
into a passive provider chest. Logistic robots (the whole revealed map is one network) carry the plates away; no train or long belt needed.

    ore patch --drills--> express collector --> smelter belt (furnaces both sides) --> fast inserter --> passive provider chest (one per furnace)

Per furnace pair (3 tiles of belt): input inserter, 3x3 electric furnace, output inserter, chest, on each side of the belt; poles every 6 tiles.
Usage: scripts/build_outpost.py --area X1 Y1 X2 Y2 --resource iron-ore|copper-ore --out N|E|S|W [--furnaces 72] [--apply]
"""
import argparse
import json
import sys
import types

import fx
from _game import tools

from bridge.factorio.planner import batches

EXPRESS = "express-transport-belt"


def smelter(out, last, cv, n_furn, plate_chest="passive-provider-chest"):
    ents = []
    tag = []
    per_side = n_furn // 2
    v0 = cv + 4
    belt_dir = fx.OUT_DIR[out]

    def add(e, k):
        ents.append(e)
        tag.append(k)

    for k in range(per_side):
        for t in range(3):                                               # three belt tiles per furnace row
            wx, wy = fx._to_world(out, last, v0 + 3 * k + t)
            add({"name": EXPRESS, "x": wx, "y": wy, "direction": belt_dir}, k)
        vc = v0 + 1 + 3 * k
        for side in (-1, 1):
            fx_, fy_ = fx._to_world(out, last + side * 3, vc)
            add({"name": "electric-furnace", "x": fx_, "y": fy_}, k)
            ix, iy = fx._to_world(out, last + side * 1, vc)
            add({"name": "fast-inserter", "x": ix, "y": iy, "direction": fx._dir_of(out, -side, 0)}, k)      # picks from the belt, drops into the furnace
            ox, oy = fx._to_world(out, last + side * 5, vc)
            add({"name": "fast-inserter", "x": ox, "y": oy, "direction": fx._dir_of(out, -side, 0)}, k)      # picks from the furnace, drops into the chest
            cx, cy = fx._to_world(out, last + side * 6, vc)
            add({"name": plate_chest, "x": cx, "y": cy}, k)
        if k % 2 == 0:
            for du in (-6, -1, 6):
                px, py = fx._to_world(out, last + du, v0 + 3 * k)
                add({"name": "medium-electric-pole", "x": px, "y": py}, k)
    bx, by = fx._to_world(out, last - 1, cv + 1)                           # link between the mining poles and the smelter poles
    add({"name": "medium-electric-pole", "x": bx, "y": by}, 0)
    return ents, tag


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--area", nargs=4, type=int, required=True)
    ap.add_argument("--resource", required=True)
    ap.add_argument("--out", default="S")
    ap.add_argument("--furnaces", type=int, default=72)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    ns = types.SimpleNamespace(area=a.area, around=None, surface="nauvis", resource=a.resource, out=a.out, drill="electric-mining-drill",
                               belt=EXPRESS, pole="medium-electric-pole", min_tiles=6, allow_mixed=False, plan_only=True, apply=False)
    mine_ents, meta = fx.cmd_mine(ns)
    out = meta["out"]
    sm_ents, tags = smelter(out, meta["last"], meta["cv"], a.furnaces)
    ents = mine_ents + sm_ents
    n_mine = len(mine_ents)
    def footprint(es):
        xs = [e["x"] for e in es]
        ys = [e["y"] for e in es]
        return (int(min(xs)) - 3, int(min(ys)) - 3, int(max(xs)) + 3, int(max(ys)) + 3)

    n_d = sum(1 for e in mine_ents if e["name"] == "electric-mining-drill")
    n_f = sum(1 for e in sm_ents if e["name"] == "electric-furnace")
    print(f"plan: {n_d} drills ({n_d * 0.5 * (1 + meta['bonus']):.0f} ore/s), up to {n_f} furnaces ({n_f * 0.625:.0f} ore/s), footprint {footprint(ents)}")
    if not a.apply:
        print("DRY RUN (add --apply: it clears trees/rocks/cliffs and the grid substations inside the footprint, then fits the smelter to the ground)")
        return
    print(tools["save_game"]("before-outpost"))
    box = footprint(ents)
    print(fx.lua(f"local s=game.surfaces.nauvis local t,n=0,0 for _,e in pairs(s.find_entities_filtered{{area={fx.a_box(box)},type={{'tree','cliff','simple-entity','item-entity','corpse'}}}}) do if e.force.name~='player' then e.destroy() t=t+1 end end for _,e in pairs(s.find_entities_filtered{{area={fx.a_box(box)},name='substation',force='player'}}) do e.destroy() n=n+1 end rcon.print('cleared '..t..' trees/rocks/cliffs, removed '..n..' grid substations')"))
    for _ in range(40):
        res = json.loads(tools["place_entities"](json.dumps(ents), dry_run=True))
        fails = res.get("failed") or []
        if not fails:
            break
        mine_fail = [f for f in fails if f["i"] < n_mine]
        if mine_fail:                                                    # drop blocked drills, keep the rest
            drop = {f["i"] for f in mine_fail if ents[f["i"]]["name"] == "electric-mining-drill"}
            if drop:
                mine_ents = [e for i, e in enumerate(mine_ents) if i not in drop]
                n_mine = len(mine_ents)
                ents = mine_ents + sm_ents
                continue
            print("blocked pieces in the mining part:", [(ents[f['i']]['name'], f['x'], f['y'], f['why']) for f in mine_fail[:5]])
            break
        cut = min(tags[f["i"] - n_mine] for f in fails)
        keep = [i for i, k in enumerate(tags) if k < cut]
        sm_ents = [sm_ents[i] for i in keep]
        tags = [tags[i] for i in keep]
        ents = mine_ents + sm_ents
        print(f"smelter cut to {cut} furnace rows per side (ground blocked)")
    n_f = sum(1 for e in sm_ents if e["name"] == "electric-furnace")
    n_c = sum(1 for e in sm_ents if e["name"] == "passive-provider-chest")
    n_d = sum(1 for e in mine_ents if e["name"] == "electric-mining-drill")
    print(f"building: {n_d} drills, {n_f} furnaces, {n_c} plate chests, {len(ents)} entities")
    for part in batches(ents):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        print("placed", r.get("placed"), "failed", len(r.get("failed") or []))
    print("footprint", footprint(ents))


if __name__ == "__main__":
    main()
