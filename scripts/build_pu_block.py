"""
Processing unit block, drone fed. Four assembler 3 side by side (4 tiles apart), a sulfuric acid pipe row above them, tapped from the acid line (surface pipe at (-215.5,-121.5)); below them a requester chest (electronic circuit, advanced circuit) with an inserter in, and an
inserter out into a passive provider chest. Electronic and advanced circuits come from the cells built by build_cells.py.

Usage: scripts/build_pu_block.py [--apply]
"""
import argparse
import json

import fx
from _game import tools

from bridge.factorio.planner import batches

CXS = [-212.5, -208.5, -204.5, -200.5]
CY = -117.5
PIPE_Y = CY - 2
TAP_X = -215.5
TAP_FROM = -121.5


EXTEND = False


def plan():
    ents = []
    x = CXS[0] - 2 if EXTEND else TAP_X
    while x <= CXS[-1] + 1:
        ents.append({"name": "pipe", "x": x, "y": PIPE_Y})
        x += 1
    y = TAP_FROM + 1 if not EXTEND else PIPE_Y
    while y < PIPE_Y:
        ents.append({"name": "pipe", "x": TAP_X, "y": y})
        y += 1
    for cx in CXS:
        ents += [
            {"name": "assembling-machine-3", "x": cx, "y": CY},
            {"name": "requester-chest", "x": cx - 1, "y": CY + 3},
            {"name": "bulk-inserter", "x": cx - 1, "y": CY + 2, "direction": 8},
            {"name": "bulk-inserter", "x": cx + 1, "y": CY + 2, "direction": 0},
            {"name": "passive-provider-chest", "x": cx + 1, "y": CY + 3},
        ]
    if EXTEND:
        for cx in CXS[1::2]:
            ents.append({"name": "substation", "x": cx - 2, "y": CY + 5})
    else:
        ents.append({"name": "substation", "x": -197, "y": -116})
    return ents


def clear_box():
    x1 = (CXS[0] - 3) if EXTEND else -217
    x2 = CXS[-1] + 6 if EXTEND else -195
    return fx.lua(
        "local s=game.surfaces.nauvis local f=game.forces.player local A={{%d,-121},{%d,-111}} local t,g=0,{} "
        "for _,e in pairs(s.find_entities_filtered{area=A,type={'tree','cliff','simple-entity','item-entity','corpse','fish'}}) do if e.force.name~='player' then e.destroy() t=t+1 end end "
        "for _,e in pairs(s.find_entities_filtered{area=A,force=f}) do local n=e.name if n=='substation' or n=='roboport' or n=='solar-panel' or n=='accumulator' or n=='medium-electric-pole' or n=='small-electric-pole' then g[n]=(g[n] or 0)+1 e.destroy() end end "
        "local o={} for k,v in pairs(g) do o[#o+1]=k..'='..v end rcon.print('cleared '..t..' natural pieces, removed '..table.concat(o,', '))" % (x1, x2))


def configure():
    xs = ",".join(str(c) for c in CXS)
    return fx.lua(
        f"local s=game.surfaces.nauvis local n,m=0,0 for _,cx in pairs({{{xs}}}) do "
        f"local c=s.find_entities_filtered{{name='requester-chest',position={{cx-1,{CY + 3}}},radius=0.4}}[1] "
        "if c then local sec=c.get_logistic_sections().add_section() sec.set_slot(1,{value={name='electronic-circuit',quality='normal'},min=100}) "
        "sec.set_slot(2,{value={name='advanced-circuit',quality='normal'},min=10}) n=n+1 end "
        f"local e=s.find_entities_filtered{{name='assembling-machine-3',position={{cx,{CY}}},radius=0.4}}[1] if e then e.set_recipe('processing-unit') m=m+1 end end "
        "rcon.print('requests '..n..', machines '..m)")


def main():
    global CXS, EXTEND
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--extend", type=int, default=0, help="add this many more assemblers east of the existing four (same acid row)")
    a = ap.parse_args()
    if a.extend:
        EXTEND = True
        CXS = [-196.5 + 4 * k for k in range(a.extend)]
    ents = plan()
    if not a.apply:
        res = json.loads(tools["place_entities"](json.dumps(ents), dry_run=True))
        print("dry run:", {k: v for k, v in res.items() if k in ("failed", "placed")})
        return
    print(clear_box())
    for part in batches(ents):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        print("placed", r.get("placed"), "failed", r.get("failed"))
    print(configure())


if __name__ == "__main__":
    main()
