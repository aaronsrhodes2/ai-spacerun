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


def remove_unplanned(ents, box):
    planned = ";".join(f"{e['name']}|{e['x']}|{e['y']}" for e in ents)
    return fx.lua(
        "local s=game.surfaces.nauvis local keep={} for item in string.gmatch('%s','[^;]+') do local f={} for v in string.gmatch(item,'[^|]+') do f[#f+1]=v end keep[f[1]..'|'..f[2]..'|'..f[3]]=true end "
        "local r={} for _,e in pairs(s.find_entities_filtered{area={{%d,%d},{%d,%d}},force='player'}) do local n=e.name "
        "if n=='roboport' or n=='solar-panel' or n=='accumulator' or n=='substation' or n=='medium-electric-pole' then local k=n..'|'..e.position.x..'|'..e.position.y "
        "if not keep[k] then r[n]=(r[n] or 0)+1 e.destroy() end end end local t={} for k,v in pairs(r) do t[#t+1]=k..'='..v end rcon.print('removed '..table.concat(t,', '))"
        % (planned, box[0], box[1], box[2], box[3]))


def connect_power(box):
    import math
    import build_substation_grid as g
    g.SHIFT = 4
    area = "{{%d,%d},{%d,%d}}" % (box[0], box[1], box[2], box[3])
    cx, cy = (box[0] + box[2]) // 2, (box[1] + box[3]) // 2
    rad = max(box[2] - box[0], box[3] - box[1]) + 120
    for rnd in range(6):
        info = json.loads(tools["run_lua"](
            "local s=game.surfaces.nauvis local main=s.find_entities_filtered{type='generator',force='player'}[1].electric_network_id local ps={} "
            "for _,p in pairs(s.find_entities_filtered{area=%s,force='player',type='electric-pole'}) do if p.electric_network_id~=main then ps[#ps+1]={p.position.x,p.position.y} end end "
            "local subs={} for _,e in pairs(s.find_entities_filtered{name='substation',force='player',position={%d,%d},radius=%d}) do if e.electric_network_id==main then subs[#subs+1]={e.position.x,e.position.y} end end "
            "rcon.print(helpers.table_to_json({poles=ps,subs=subs}))" % (area, cx, cy, rad)))
        poles, subs = info["poles"], info["subs"]
        if not poles or not subs:
            print("power: all outpost poles are on the main network" if not poles else "power: no main substation nearby")
            return
        d, pp, m = min(((max(abs(p[0] - q[0]), abs(p[1] - q[1])), p, q) for p in poles for q in subs), key=lambda t: t[0])
        steps = max(1, math.ceil(d / 14))
        pts = [(round(m[0] + (pp[0] - m[0]) * k / steps), round(m[1] + (pp[1] - m[1]) * k / steps)) for k in range(1, steps + 1)]
        g.place_points(pts, batch=10)
    print("power: could not join every pole network after 6 rounds")


def cover_unpowered_drills(box):
    return fx.lua(
        "local s=game.surfaces.nauvis local f=game.forces.player local un={} for _,e in pairs(s.find_entities_filtered{area={{%d,%d},{%d,%d}},force='player',type='mining-drill'}) do "
        "if e.status==defines.entity_status.no_power then un[#un+1]=e end end table.sort(un,function(a,b) if a.position.y~=b.position.y then return a.position.y<b.position.y end return a.position.x<b.position.x end) "
        "local placed={} local n=0 for _,d in pairs(un) do local cov=false for _,p in pairs(placed) do if math.abs(p[1]-d.position.x)<=5 and math.abs(p[2]-d.position.y)<=5 then cov=true end end "
        "if not cov then local done=false for r=1,4 do for dx=-r,r do for dy=-r,r do if not done and (math.abs(dx)==r or math.abs(dy)==r) then local p={math.floor(d.position.x)+0.5+dx,math.floor(d.position.y)+0.5+dy} "
        "if math.abs(p[1]-d.position.x)<=4.99 and math.abs(p[2]-d.position.y)<=4.99 and s.can_place_entity{name='medium-electric-pole',position=p,force=f} then if s.create_entity{name='medium-electric-pole',position=p,force=f} then placed[#placed+1]=p n=n+1 done=true end end end end end end end end "
        "rcon.print('extra poles for unpowered drills: '..n)" % (box[0], box[1], box[2], box[3]))


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
    print(remove_unplanned(ents, box))
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
    box = footprint(ents)
    print("footprint", box)
    connect_power(box)
    print(cover_unpowered_drills(box))
    print("re-run scripts/build_roboport_grid.py --revealed --build to restore robot coverage where kits were removed")


if __name__ == "__main__":
    main()
