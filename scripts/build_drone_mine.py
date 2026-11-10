"""
Raw-ore outpost carried by drones: a mining patch layout (fx.py mine) whose collector belt ends in a short unloading spur, where bulk inserters
on both sides lift the ore into passive provider chests (red chests, end of the line). The whole revealed map is one robot network, so no train
and no long belt is needed. Meant for cargo that is used raw: coal, stone.

    ore patch --drills--> express collector --> spur (N belt tiles) --> bulk inserter each side --> passive provider chest

One express lane carries 22.5 per second; the collector fills one lane only (every drill column side-loads from the same side), which is the cap.
With --apply: trees, rocks, cliffs and the lattice pieces (substations, roboports, solar kits) inside the footprint go, the drills that do not fit
are dropped, power is joined to the main network and a map tag is set (docs/naming-sop.md).

Usage: scripts/build_drone_mine.py --area X1 Y1 X2 Y2 --resource coal --out N|E|S|W --name "Coal A" [--chests 16] [--apply]
"""
import argparse
import json
import types

import build_outpost as bo
import fx
from _game import tools

from bridge.factorio.planner import batches

EXPRESS = "express-transport-belt"


def spur(out, last, cv, n_chests):
    """Belt goes on from the collector's exit; every tile has an inserter and a chest on each side."""
    ents = []
    v0 = cv + 4
    for k in range(n_chests // 2):
        wx, wy = fx._to_world(out, last, v0 + k)
        ents.append({"name": EXPRESS, "x": wx, "y": wy, "direction": fx.OUT_DIR[out]})
        for side in (-1, 1):
            ix, iy = fx._to_world(out, last + side, v0 + k)
            ents.append({"name": "bulk-inserter", "x": ix, "y": iy, "direction": fx._dir_of(out, -side, 0)})   # direction is the side it picks up from
            cx, cy = fx._to_world(out, last + 2 * side, v0 + k)
            ents.append({"name": "passive-provider-chest", "x": cx, "y": cy})
    for k in (0, n_chests // 2 - 1):
        for side in (-3, 3):                                             # a pole behind the chests on each side (one side alone does not reach the far inserters)
            px, py = fx._to_world(out, last + side, v0 + k)
            ents.append({"name": "medium-electric-pole", "x": px, "y": py})
    rx, ry = fx._to_world(out, last + 5.5, v0 + 1.5)                     # its own roboport: the lattice one in the footprint is removed
    ents.append({"name": "roboport", "x": rx, "y": ry})
    return ents


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--area", nargs=4, type=int, required=True)
    ap.add_argument("--resource", required=True)
    ap.add_argument("--out", default="S")
    ap.add_argument("--name", required=True, help="site name for the map tag, e.g. 'Coal A'")
    ap.add_argument("--chests", type=int, default=16)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    ns = types.SimpleNamespace(area=a.area, around=None, surface="nauvis", resource=a.resource, out=a.out, drill="electric-mining-drill",
                               belt=EXPRESS, pole="medium-electric-pole", min_tiles=6, allow_mixed=False, plan_only=True, apply=False)
    mine_ents, meta = fx.cmd_mine(ns)
    out = meta["out"]
    sp = spur(out, meta["last"], meta["cv"], a.chests)

    def footprint(es):
        xs = [e["x"] for e in es]
        ys = [e["y"] for e in es]
        return (int(min(xs)) - 3, int(min(ys)) - 3, int(max(xs)) + 3, int(max(ys)) + 3)

    box = footprint(mine_ents + sp)
    n_d = sum(1 for e in mine_ents if e["name"] == "electric-mining-drill")
    print(f"plan: {n_d} drills ({n_d * 0.5 * (1 + meta['bonus']):.0f} ore/s before the 22.5/s lane cap), {a.chests} chests, footprint {box}")
    if not a.apply:
        print(bo.fx.lua(f"local s=game.surfaces.nauvis local g={{}} for _,e in pairs(s.find_entities_filtered{{area={fx.a_box(box)},force='player'}}) do g[e.name]=(g[e.name] or 0)+1 end "
                        "local o={} for k,v in pairs(g) do o[#o+1]=k..'='..v end rcon.print('standing in the footprint: '..table.concat(o,', '))"))
        print("DRY RUN (add --apply)")
        return
    print(tools["save_game"]("before-drone-mine"))
    print(fx.lua(f"local s=game.surfaces.nauvis local t=0 for _,e in pairs(s.find_entities_filtered{{area={fx.a_box(box)},type={{'tree','cliff','simple-entity','item-entity','corpse'}}}}) do "
                 "if e.force.name~='player' then e.destroy() t=t+1 end end rcon.print('cleared '..t..' trees/rocks/cliffs')"))
    print(bo.remove_unplanned(mine_ents + sp, box))
    for _ in range(10):
        ents = mine_ents + sp
        fails = json.loads(tools["place_entities"](json.dumps(ents), dry_run=True)).get("failed") or []
        drop = {f["i"] for f in fails if f["i"] < len(mine_ents) and ents[f["i"]]["name"] == "electric-mining-drill"}
        if not drop:
            if fails:
                print("blocked pieces:", [(ents[f["i"]]["name"], f["x"], f["y"], f["why"]) for f in fails[:6]])
            break
        mine_ents = [e for i, e in enumerate(mine_ents) if i not in drop]
    ents = mine_ents + sp
    placed = failed = 0
    for part in batches(ents):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        placed += len(r["placed"]) if isinstance(r.get("placed"), list) else (r.get("placed") or 0)
        failed += len(r.get("failed") or [])
    print("placed", placed, "failed", failed, "drills", sum(1 for e in mine_ents if e["name"] == "electric-mining-drill"))
    bo.connect_power(box)
    print(bo.cover_unpowered_drills(box))
    tx, ty = fx._to_world(out, meta["last"], meta["cv"] + 4)
    print(fx.lua(f"game.forces.player.add_chart_tag(game.surfaces.nauvis,{{position={{{tx},{ty}}},text='{a.name} (drone outpost)'}}) rcon.print('tagged')"))
    print("re-run scripts/build_roboport_grid.py --revealed --build to restore robot coverage where kits were removed")


if __name__ == "__main__":
    main()
