#!/usr/bin/env python3
"""Same autopilot as autopilot_server.py but run from this PC through the SSH tunnel (no service installed on the VM).
Usage: scripts/autopilot_local.py [cycles]   (default: run until stopped). Log: docs/autopilot.log"""
import sys
import time
from pathlib import Path

from _game import tools

import autopilot_server as ap
import module_mall

LOG = str(Path(__file__).resolve().parent.parent / "docs" / "autopilot.log")

# The Captain's shared view (2026-11-13: Aquilo was built and the map stayed black): wherever anything of ours stands on a planet, that
# area and a chunk round it are charted, whoever built it. Every 3 cycles (3 minutes: the charted picture is refreshed, not only made once), every planet surface; at most 3,000 chunks a pass.
CHART = ("local f=game.forces.player local n,c=0,0 for _,s in pairs(game.surfaces) do if not s.platform then local seen={} for _,e in pairs(s.find_entities_filtered{force=f,type={'roboport','cargo-landing-pad','assembling-machine','heating-tower','reactor','rocket-silo','lab','mining-drill','pumpjack','furnace','generator','heat-pipe','electric-pole','solar-panel','storage-tank'}}) do "
         "local cx,cy=math.floor(e.position.x/32),math.floor(e.position.y/32) local k=cx*100000+cy if not seen[k] then seen[k]=true n=n+1 if n<=3000 then local ok=pcall(function() f.chart(s,{{(cx-1)*32,(cy-1)*32},{(cx+2)*32,(cy+2)*32}}) end) if ok then c=c+1 end end end end end end rcon.print('charted '..c..' of '..n..' chunks with our things')")
CHART_EVERY = 3

# Robots cannot be upgraded in the air (the Captain, 2026-11-13: swap them when they go to charge). Every cycle, each robot resting in a
# roboport below the best researched quality is replaced by the same robot at that quality, on every surface. Over a few hours every
# robot has docked once. The same swap as scripts/upgrade_quality.py --items, which only catches the robots resting at that moment.
ROBOTS = ("local f=game.forces.player local best=nil for n,q in pairs(prototypes.quality) do if n~='quality-unknown' and f.is_quality_unlocked(n) and (best==nil or q.level>best.level) then best=q end end "
          "local n=0 for _,s in pairs(game.surfaces) do for _,e in pairs(s.find_entities_filtered{force=f,type='roboport'}) do local inv=e.get_inventory(defines.inventory.roboport_robot) if inv then for i=1,#inv do local st=inv[i] "
          "if st.valid_for_read and st.quality.level<best.level then n=n+st.count st.set_stack{name=st.name,count=st.count,quality=best.name} end end end end end rcon.print('robots swapped '..n)")


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10**9
    ap.log("autopilot (local) started", LOG)
    for cyc in range(n):
        try:
            queue = tools["run_lua"](ap.TOPUP.replace("rcon.print", "rcon.print"))
            snap = tools["run_lua"](ap.SNAP)
            fix = tools["run_lua"](ap.REPAIR)
            guard = tools["run_lua"](ap.SILO_GUARD)
            ships = tools["run_lua"](ap.SHIPS)
            bots = tools["run_lua"](ROBOTS).strip()
            if cyc % CHART_EVERY == 0:
                tools["run_lua"](CHART)
            tools["run_lua"](module_mall.LABS)                                               # speed modules into the Gleba labs first
            mods = tools["run_lua"](module_mall.sub(module_mall.INSTALL, True)).strip()      # finished productivity modules go into the wheels
            ap.log(snap + " | queue " + queue + " | " + fix + " | " + guard + " | " + ships + ("" if bots.endswith(" 0") else " | " + bots) + ("" if "installed 0 / 0" in mods else " | " + mods), LOG)
        except Exception as exc:  # noqa: BLE001
            ap.log("error: " + repr(exc), LOG)
        time.sleep(ap.CYCLE)


if __name__ == "__main__":
    main()
