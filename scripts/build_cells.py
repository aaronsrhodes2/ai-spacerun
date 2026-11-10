"""
Drone-fed production cells for the rocket parts (steel plate, low density structure). Per cell, in a row going east:

    requester chest -> inserter -> machine -> inserter -> passive provider chest

Cells are stacked 3 tiles apart. The request fills the machine for a couple of minutes; the output chest offers the product to the whole
logistic network (the silos' requester chests, other cells). Nothing is belted.

Usage: scripts/build_cells.py --kind steel|lds --origin X Y --count N [--apply]
  (X, Y is the top-left tile corner of the first cell; the cell is 7 wide, 3 tall)
"""
import argparse
import json

import fx
from _game import tools

from bridge.factorio.planner import batches

KINDS = {
    "steel": {"machine": "electric-furnace", "recipe": None, "req": [("iron-plate", 100)]},
    "cable": {"machine": "assembling-machine-3", "recipe": "copper-cable", "req": [("copper-plate", 200)]},
    "ec": {"machine": "assembling-machine-3", "recipe": "electronic-circuit", "req": [("copper-cable", 300), ("iron-plate", 100)]},
    "ac": {"machine": "assembling-machine-3", "recipe": "advanced-circuit", "req": [("electronic-circuit", 40), ("plastic-bar", 40), ("copper-cable", 80)]},
    "foundation": {"machine": "assembling-machine-3", "recipe": "space-platform-foundation", "req": [("steel-plate", 100), ("copper-cable", 100)]},
    "lds": {"machine": "assembling-machine-3", "recipe": "low-density-structure",
            "req": [("copper-plate", 200), ("steel-plate", 20), ("plastic-bar", 50)]},
}


def plan(kind, x0, y0, n):
    k = KINDS[kind]
    ents = []
    for i in range(n):
        yc = y0 + 3 * i + 1.5
        ents += [
            {"name": "requester-chest", "x": x0 + 0.5, "y": yc},
            {"name": "bulk-inserter", "x": x0 + 1.5, "y": yc, "direction": 12},
            {"name": k["machine"], "x": x0 + 3.5, "y": yc},
            {"name": "bulk-inserter", "x": x0 + 5.5, "y": yc, "direction": 12},
            {"name": "passive-provider-chest", "x": x0 + 6.5, "y": yc},
        ]
    return ents


def clear_box(x0, y0, n):
    box = f"{{{{{x0 - 1},{y0 - 1}}},{{{x0 + 8},{y0 + 3 * n + 1}}}}}"
    return fx.lua(
        f"local s=game.surfaces.nauvis local f=game.forces.player local A={box} local t,g=0,{{}} "
        "for _,e in pairs(s.find_entities_filtered{area=A,type={'tree','cliff','simple-entity','item-entity','corpse','fish'}}) do if e.force.name~='player' then e.destroy() t=t+1 end end "
        "for _,e in pairs(s.find_entities_filtered{area=A,force=f}) do local n=e.name if n=='substation' or n=='roboport' or n=='solar-panel' or n=='accumulator' or n=='medium-electric-pole' or n=='small-electric-pole' then g[n]=(g[n] or 0)+1 e.destroy() end end "
        "local o={} for k,v in pairs(g) do o[#o+1]=k..'='..v end rcon.print('cleared '..t..' natural pieces, removed '..table.concat(o,', '))")


def configure(kind, x0, y0, n):
    k = KINDS[kind]
    req = ",".join("{'%s',%d}" % r for r in k["req"])
    recipe = f"e.set_recipe('{k['recipe']}')" if k["recipe"] else ""
    return fx.lua(
        f"local s=game.surfaces.nauvis local f=game.forces.player local R={{{req}}} local n,m=0,0 "
        f"for i=0,{n - 1} do local yc={y0}+3*i+1.5 "
        f"local c=s.find_entities_filtered{{name='requester-chest',position={{{x0}+0.5,yc}},radius=0.4}}[1] "
        "if c then local sec=c.get_logistic_sections().add_section() for j,r in ipairs(R) do sec.set_slot(j,{value={name=r[1],quality='normal'},min=r[2]}) end n=n+1 end "
        f"local e=s.find_entities_filtered{{name='{k['machine']}',position={{{x0}+3.5,yc}},radius=0.4}}[1] if e then {recipe} m=m+1 end end "
        "rcon.print('requests '..n..', machines '..m)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", choices=KINDS, required=True)
    ap.add_argument("--origin", nargs=2, type=int, required=True)
    ap.add_argument("--count", type=int, required=True)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    x0, y0 = a.origin
    ents = plan(a.kind, x0, y0, a.count)
    if not a.apply:
        res = json.loads(tools["place_entities"](json.dumps(ents), dry_run=True))
        print("dry run:", {k: v for k, v in res.items() if k in ("failed", "placed")})
        return
    print(clear_box(x0, y0, a.count))
    for part in batches(ents):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        print("placed", r.get("placed"), "failed", r.get("failed"))
    print(configure(a.kind, x0, y0, a.count))


if __name__ == "__main__":
    main()
