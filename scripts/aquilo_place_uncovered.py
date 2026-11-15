#!/usr/bin/env python3
"""Place directly the Aquilo entity ghosts that no roboport can reach (the Captain, 2026-11-14: "place the north chain directly").
A ghost outside every construction area waits forever; the north chain (heat pipes, substations, pumpjacks to the roboport at (-29,-73)) is
exactly that. For each such ghost: read name/position/direction, remove the ghost, place the entity through place_entities (free placement,
research-checked, epic quality as standard). If placing fails the ghost is put back. Ghosts inside coverage are left to the robots.
Usage: aquilo_place_uncovered.py [--apply]"""
import json
import sys

from _game import tools

LIST = ("local s=game.surfaces.aquilo local f=game.forces.player local t={} for _,g in pairs(s.find_entities_filtered{type='entity-ghost',force=f}) do "
        "local nets=s.find_logistic_networks_by_construction_area(g.position,f) if #nets==0 then t[#t+1]=g.ghost_name..','..g.position.x..','..g.position.y..','..g.direction end end rcon.print(table.concat(t,';'))")


def main():
    apply = "--apply" in sys.argv
    rows = [r.split(",") for r in tools["run_lua"](LIST).strip().split(";") if r]
    print("ghosts outside coverage:", len(rows))
    if not rows or not apply:
        from collections import Counter
        print(dict(Counter(r[0] for r in rows)))
        return
    print(tools["save_game"]("skippy"))
    ents = [{"name": r[0], "x": float(r[1]), "y": float(r[2]), "direction": int(r[3]), "params": {"quality": "epic"}} for r in rows]
    # remove the ghosts, place, and put back the ghosts of anything that failed
    pos = ",".join("{%s,%s,'%s'}" % (r[1], r[2], r[0]) for r in rows)
    tools["run_lua"]("local s=game.surfaces.aquilo local n=0 for _,q in pairs({%s}) do for _,g in pairs(s.find_entities_filtered{type='entity-ghost',position={q[1],q[2]},radius=0.3}) do if g.ghost_name==q[3] then g.destroy() n=n+1 end end end rcon.print(n)" % pos)
    placed, failed = 0, []
    for i in range(0, len(ents), 200):
        r = json.loads(tools["place_entities"](json.dumps(ents[i:i + 200]), surface="aquilo", dry_run=False))
        placed += r.get("placed", 0)
        for fl in (r.get("failed") or []):
            failed.append(ents[i + fl["i"] - 1] | {"why": fl.get("why")})
    print("placed", placed, "failed", len(failed))
    if failed:
        back = ",".join("{'%s',%s,%s,%d}" % (e["name"], e["x"], e["y"], e["direction"]) for e in failed)
        tools["run_lua"]("local s=game.surfaces.aquilo local f=game.forces.player for _,q in pairs({%s}) do s.create_entity{name='entity-ghost',inner_name=q[1],position={q[2],q[3]},direction=q[4],force=f,expires=false} end rcon.print('ok')" % back)
        from collections import Counter
        print("failed kinds (ghosts restored):", dict(Counter((e["name"], e["why"]) for e in failed)))


if __name__ == "__main__":
    main()
