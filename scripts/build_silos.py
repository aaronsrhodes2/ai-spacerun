"""
More rocket silos, fed by drones. Each silo (9x9) gets, on its north side, three fast inserters taking from three blue requester chests
(processing unit, low density structure, rocket fuel), and on its south side three bulk inserters loading the rocket cargo from three
requester chests (first one asks for space platform foundations; the other two are left empty for the Captain to set).

Silos are set to launch automatically when the rocket is loaded. Parts come from red provider chests, via the logistic network.
Usage: scripts/build_silos.py --centers X Y [X Y ...] [--apply]
"""
import argparse
import json

import fx
from _game import tools

from bridge.factorio.planner import batches

PARTS = [("processing-unit", 40), ("low-density-structure", 40), ("rocket-fuel", 40)]
CARGO = [("space-platform-foundation", 100), (None, 0), (None, 0)]


def plan(cx, cy):
    ents = [{"name": "rocket-silo", "x": cx, "y": cy}]
    for k, dx in enumerate((-1, 0, 1)):
        ents.append({"name": "fast-inserter", "x": cx + dx, "y": cy - 5, "direction": 0})        # picks from the north chest, drops into the silo
        ents.append({"name": "requester-chest", "x": cx + dx, "y": cy - 6})
        ents.append({"name": "bulk-inserter", "x": cx + dx, "y": cy + 5, "direction": 8})        # picks from the south chest, drops into the rocket
        ents.append({"name": "requester-chest", "x": cx + dx, "y": cy + 6})
    return ents


def clear_box(cx, cy):
    box = f"{{{{{cx - 8},{cy - 8}}},{{{cx + 8},{cy + 8}}}}}"
    return fx.lua(
        f"local s=game.surfaces.nauvis local f=game.forces.player local A={box} local t,g=0,{{}} "
        "for _,e in pairs(s.find_entities_filtered{area=A,type={'tree','cliff','simple-entity','item-entity','corpse','fish'}}) do if e.force.name~='player' then e.destroy() t=t+1 end end "
        "for _,e in pairs(s.find_entities_filtered{area=A,force=f}) do local n=e.name if n=='substation' or n=='roboport' or n=='solar-panel' or n=='accumulator' or n=='medium-electric-pole' or n=='small-electric-pole' then g[n]=(g[n] or 0)+1 e.destroy() end end "
        "local o={} for k,v in pairs(g) do o[#o+1]=k..'='..v end rcon.print('cleared '..t..' natural pieces, removed '..table.concat(o,', '))")


def set_requests(cx, cy):
    parts = ",".join("{%s,%d}" % (("'%s'" % n if n else "nil"), c) for n, c in PARTS)
    cargo = ",".join("{%s,%d}" % (("'%s'" % n if n else "false"), c) for n, c in CARGO)
    return fx.lua(
        f"local s=game.surfaces.nauvis local f=game.forces.player local cx,cy={cx},{cy} local P={{{parts}}} local C={{{cargo}}} local done=0 "
        "local function req(x,y,item,n) local c=s.find_entities_filtered{name='requester-chest',position={x,y},radius=0.4}[1] if not c then return end "
        "if item and n>0 then local sec=c.get_logistic_sections().add_section() sec.set_slot(1,{value={name=item,quality='normal'},min=n}) done=done+1 end end "
        "for k,dx in ipairs({-1,0,1}) do req(cx+dx,cy-6,P[k][1],P[k][2]) local c=C[k] if c[1] then req(cx+dx,cy+6,c[1],c[2]) end end "
        "local sil=s.find_entities_filtered{name='rocket-silo',position={cx,cy},radius=1}[1] if sil then sil.send_to_orbit_automatically=true end "
        "rcon.print('requests set: '..done..', auto launch '..tostring(sil and sil.send_to_orbit_automatically))")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--centers", nargs="+", type=float, required=True)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    cs = list(zip(a.centers[0::2], a.centers[1::2]))
    for cx, cy in cs:
        ents = plan(cx, cy)
        if not a.apply:
            res = json.loads(tools["place_entities"](json.dumps(ents), dry_run=True))
            print((cx, cy), "dry run:", {k: v for k, v in res.items() if k in ("failed", "would_place", "placed")})
            continue
        print((cx, cy), clear_box(cx, cy))
        for part in batches(ents):
            r = json.loads(tools["place_entities"](json.dumps(part)))
            print("  placed", r.get("placed"), "failed", r.get("failed"))
        print("  ", set_requests(cx, cy))


if __name__ == "__main__":
    main()
