#!/usr/bin/env python3
"""Remove electric poles from platforms (the Captain, 2026-11-14: the platform foundation carries power; verified on the triangle: 237 poles
removed, 231/231 machines still powered). Keeps every pole that carries a CIRCUIT wire (red/green: the wheels use substations to carry
over-reach circuit wires). Per platform: count machines with energy before, record and remove the plain poles, wait, count again; if any
machine lost power, put the removed poles back (same name, position, quality) and report.
Usage: platform_poles_off.py "Gleba Wheel" ["Nauvis Wheel" ...] [--apply]   (dry run without --apply)"""
import json
import os
import sys
import time

from _game import tools

FIND = "local p for _,q in pairs(game.forces.player.platforms) do if q.name:find('%s',1,true) then p=q end end local s=p.surface "
COUNT = ("local ok,bad=0,0 for _,e in pairs(s.find_entities_filtered{force='player'}) do if e.electric_buffer_size and e.electric_buffer_size>0 and e.type~='electric-pole' "
         "and e.type~='solar-panel' and e.type~='accumulator' then if e.energy>0 then ok=ok+1 else bad=bad+1 end end end rcon.print(ok..' '..bad)")
PLAIN = ("local t={} local keep=0 for _,e in pairs(s.find_entities_filtered{type='electric-pole'}) do local r=e.get_wire_connector(defines.wire_connector_id.circuit_red,false) "
         "local g=e.get_wire_connector(defines.wire_connector_id.circuit_green,false) local wired=(r and r.connection_count>0) or (g and g.connection_count>0) "
         "if wired then keep=keep+1 else t[#t+1]=e.name..','..e.position.x..','..e.position.y..','..e.quality.name end end rcon.print(keep..'|'..table.concat(t,';'))")


def run(name, apply):
    f = FIND % name
    before = tools["run_lua"](f + COUNT).split()
    out = tools["run_lua"](f + PLAIN).strip()
    keep, rest = out.split("|", 1)
    poles = [x for x in rest.split(";") if x]
    print("%s: machines with power %s, without %s | poles with circuit wires kept %s, plain poles %d" % (name, before[0], before[1], keep, len(poles)))
    if not apply or not poles:
        return
    snap = os.path.join("snapshots", "poles_removed_%s.txt" % name.replace(" ", "_"))
    open(snap, "w").write(";".join(poles))
    for i in range(0, len(poles), 300):
        part = ",".join("{%s,%s}" % (p.split(",")[1], p.split(",")[2]) for p in poles[i:i + 300])
        tools["run_lua"](f + "local n=0 for _,q in pairs({%s}) do for _,e in pairs(s.find_entities_filtered{type='electric-pole',position=q,radius=0.3}) do e.destroy() n=n+1 end end rcon.print(n)" % part)
    time.sleep(15)
    after = tools["run_lua"](f + COUNT).split()
    print("  removed %d; after: with power %s, without %s" % (len(poles), after[0], after[1]))
    if int(after[1]) > int(before[1]):
        print("  POWER LOST: restoring")
        for i in range(0, len(poles), 200):
            ents = [{"name": p.split(",")[0], "x": float(p.split(",")[1]), "y": float(p.split(",")[2]), "direction": 0, "params": {"quality": p.split(",")[3]}} for p in poles[i:i + 200]]
            tools["place_entities"](json.dumps(ents), surface=tools["run_lua"](f + "rcon.print(s.name)").strip(), dry_run=False)
        print("  restored; after restore:", tools["run_lua"](f + COUNT))


if __name__ == "__main__":
    apply = "--apply" in sys.argv
    for n in [a for a in sys.argv[1:] if not a.startswith("--")]:
        run(n, apply)
