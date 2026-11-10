"""
One compact nuclear unit: four reactors in a 2x2 square (each has two aligned neighbours, so 120 MW each, 480 MW per unit),
48 heat exchangers and 96 steam turbines. 82 tiles wide, 26 tall, plus a water main on each side and a 2-row gap below for substations.

    rows  0..9   two turbines chained above every north exchanger
    rows 10..11  north exchangers (water passes along the row), steam out north
    rows 12..13  double heat pipe trunk, west and east of the reactor square
    rows 14..15  south exchangers, steam out south
    rows 16..25  two turbines chained below every south exchanger
    rows 26..27  substations (they reach the turbines of this unit and of the one below)
    col -1, 82   water mains, full height, so stacked units (pitch 28) join by themselves
    cols 36..45  reactors (rows 8..17); above and below them the fuel chests, a roboport and two substations

Why the square matters: a reactor only gets its neighbour bonus when it touches the next one exactly aligned (centres 5 apart).
Fuel: a requester chest per reactor asks the logistic network for fuel cells (group "Feed: Uranium Fuel Cell"); spent cells go to a red provider chest.
Units side by side: use --gap-east on the west one and put the east one at X+88 (the 4 free columns hold a roboport and a substation).

Without --apply it only reports what stands in the box. With --apply it removes trees, rocks, cliffs and the script-built lattice pieces
(substations, roboports and their solar kits) in the box, then places through place_entities (research gate applies). Robots that were
parked in removed roboports are put into the unit's roboport.

Usage: scripts/build_nuclear_unit.py --origin X Y --name "Nuclear Unit 1" [--top] [--gap-east] [--apply]
"""
import argparse
import json

import fx
from _game import tools

from bridge.factorio.planner import batches

GROUP = "Feed: Uranium Fuel Cell"
LATTICE = ("substation", "roboport", "solar-panel", "accumulator", "medium-electric-pole")
W_COLS = list(range(0, 36))
E_COLS = list(range(46, 82))


def plan(X, Y, top=False, gap=False):
    E = []
    add = lambda n, x, y, d=None: E.append({"name": n, "x": x, "y": y, **({"direction": d} if d is not None else {})})
    for cx in (38.5, 43.5):
        for cy in (10.5, 15.5):
            add("nuclear-reactor", X + cx, Y + cy)
    for c in W_COLS + E_COLS:
        add("heat-pipe", X + c + 0.5, Y + 12.5)
        add("heat-pipe", X + c + 0.5, Y + 13.5)
    for base in (0, 46):
        for k in range(12):
            x = X + base + 3 * k + 1.5
            add("heat-exchanger", x, Y + 11, 0)
            add("heat-exchanger", x, Y + 15, 8)
            for ty in (2.5, 7.5, 18.5, 23.5):
                add("steam-turbine", x, Y + ty, 0)
    for r in range(28):
        add("pipe", X - 0.5, Y + r + 0.5)
        add("pipe", X + 82.5, Y + r + 0.5)
    # fuel in, spent cells out (an inserter's direction is the side it picks up from)
    for cx in (37.5, 42.5):
        add("requester-chest", X + cx, Y + 6.5)
        add("fast-inserter", X + cx, Y + 7.5, 0)
        add("passive-provider-chest", X + cx + 2, Y + 6.5)
        add("fast-inserter", X + cx + 2, Y + 7.5, 8)
        add("requester-chest", X + cx, Y + 19.5)
        add("fast-inserter", X + cx, Y + 18.5, 8)
        add("passive-provider-chest", X + cx + 2, Y + 19.5)
        add("fast-inserter", X + cx + 2, Y + 18.5, 0)
    add("roboport", X + 41, Y + 2)
    add("substation", X + 41, Y + 5)
    add("substation", X + 41, Y + 21)
    for c in (8, 26, 44, 62, 80):
        add("substation", X + c, Y + 27)
        if top:
            add("substation", X + c, Y - 1)
    if gap:
        add("substation", X + 84, Y + 10)
        add("roboport", X + 85, Y + 13)
    return E


def box(X, Y, top, gap):
    return X - 1, Y - (2 if top else 0), X + (87 if gap else 83), Y + 28


def survey(b):
    x0, y0, x1, y1 = b
    return fx.lua(
        f"local s=game.surfaces.nauvis local A={{{{{x0}+0.1,{y0}+0.1}},{{{x1}-0.1,{y1}-0.1}}}} local g={{}} "
        "for _,e in pairs(s.find_entities_filtered{area=A}) do local k=e.force.name..':'..e.name..(e.last_user and ('/'..e.last_user.name) or '') "
        "if e.type=='tree' then k='tree' end g[k]=(g[k] or 0)+1 end local o={} for k,v in pairs(g) do o[#o+1]=k..'='..v end "
        "rcon.print('water tiles '..s.count_tiles_filtered{area=A,collision_mask='water_tile'}..'; '..table.concat(o,', '))")


def clear(b):
    """Natural pieces and the script-built lattice go. Returns the robots that sat in the removed roboports."""
    x0, y0, x1, y1 = b
    names = ",".join(f"{n}=true" for n in ("substation", "roboport", "accumulator")) + ",['solar-panel']=true,['medium-electric-pole']=true"
    out = fx.lua(
        f"local s=game.surfaces.nauvis local A={{{{{x0}+0.1,{y0}+0.1}},{{{x1}-0.1,{y1}-0.1}}}} local L={{{names}}} local t,n,R=0,0,{{}} "
        "for _,e in pairs(s.find_entities_filtered{area=A,type={'tree','cliff','simple-entity','item-entity','corpse','fish'}}) do if e.force.name~='player' then e.destroy() t=t+1 end end "
        "for _,e in pairs(s.find_entities_filtered{area=A,force='player'}) do if L[e.name] and not e.last_user then "
        "if e.name=='roboport' then for _,iv in pairs({defines.inventory.roboport_robot,defines.inventory.roboport_material}) do local inv=e.get_inventory(iv) "
        "if inv then for _,it in pairs(inv.get_contents()) do R[it.name]=(R[it.name] or 0)+it.count end end end end e.destroy() n=n+1 end end "
        "rcon.print(helpers.table_to_json({natural=t,lattice=n,robots=R}))")
    d = json.loads(out)
    return json.loads(d["result"]) if isinstance(d, dict) and "result" in d else d


def configure(X, Y, name, robots):
    items = ",".join("{'%s',%d}" % (k, v) for k, v in (robots or {}).items())
    return fx.lua(
        f"local s=game.surfaces.nauvis local f=game.forces.player local n=0 "
        f"for _,p in pairs({{{{{X}+37.5,{Y}+6.5}},{{{X}+42.5,{Y}+6.5}},{{{X}+37.5,{Y}+19.5}},{{{X}+42.5,{Y}+19.5}}}}) do "
        "local c=s.find_entities_filtered{name='requester-chest',position=p,radius=0.4}[1] if c then local ls=c.get_logistic_sections() "
        "local sec=ls.sections[1] or ls.add_section() sec.set_slot(1,{value={name='uranium-fuel-cell',quality='normal'},min=10}) "
        f"sec.group='{GROUP}' n=n+1 end end local put=0 "
        f"local rp=s.find_entities_filtered{{name='roboport',position={{{X}+41,{Y}+2}},radius=1}}[1] "
        f"if rp then for _,it in pairs({{{items}}}) do put=put+rp.insert{{name=it[1],count=it[2]}} end end "
        f"f.add_chart_tag(s,{{position={{{X}+41,{Y}+13}},text='{name}'}}) rcon.print('requests '..n..', robots returned '..put)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--origin", nargs=2, type=int, required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--top", action="store_true", help="also a substation row above the unit (the top unit of a stack)")
    ap.add_argument("--gap-east", action="store_true", help="roboport and substation in the 4 columns east of the east main")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    X, Y = a.origin
    b = box(X, Y, a.top, a.gap_east)
    ents = plan(X, Y, a.top, a.gap_east)
    print("box", b, "pieces", len(ents))
    if not a.apply:
        print(survey(b))
        return
    got = clear(b)
    print("cleared", got)
    placed = failed = 0
    for part in batches(ents):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        placed += len(r["placed"]) if isinstance(r.get("placed"), list) else (r.get("placed") or 0)
        fl = r.get("failed") or []
        failed += len(fl) if isinstance(fl, list) else fl
        if fl and isinstance(fl, list):
            print("  failed sample:", json.dumps(fl[:4]))
    print("placed", placed, "failed", failed)
    print(configure(X, Y, a.name, got.get("robots") if isinstance(got.get("robots"), dict) else {}))


if __name__ == "__main__":
    main()
