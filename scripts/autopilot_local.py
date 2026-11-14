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

# Robots cannot be upgraded in the air (the Captain, 2026-11-13: swap them when they go to charge). Every cycle, each robot resting in a
# roboport below the best researched quality is replaced by the same robot at that quality, on every surface. Over a few hours every
# robot has docked once. The same swap as scripts/upgrade_quality.py --items, which only catches the robots resting at that moment.
ROBOTS = ("local f=game.forces.player local best=nil for n,q in pairs(prototypes.quality) do if n~='quality-unknown' and f.is_quality_unlocked(n) and (best==nil or q.level>best.level) then best=q end end "
          "local n=0 for _,s in pairs(game.surfaces) do for _,e in pairs(s.find_entities_filtered{force=f,type='roboport'}) do local inv=e.get_inventory(defines.inventory.roboport_robot) if inv then for i=1,#inv do local st=inv[i] "
          "if st.valid_for_read and st.quality.level<best.level then n=n+st.count st.set_stack{name=st.name,count=st.count,quality=best.name} end end end end end rcon.print('robots swapped '..n)")


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10**9
    ap.log("autopilot (local) started", LOG)
    for _ in range(n):
        try:
            queue = tools["run_lua"](ap.TOPUP.replace("rcon.print", "rcon.print"))
            snap = tools["run_lua"](ap.SNAP)
            fix = tools["run_lua"](ap.REPAIR)
            guard = tools["run_lua"](ap.SILO_GUARD)
            ships = tools["run_lua"](ap.SHIPS)
            bots = tools["run_lua"](ROBOTS).strip()
            tools["run_lua"](module_mall.LABS)                                               # speed modules into the Gleba labs first
            mods = tools["run_lua"](module_mall.sub(module_mall.INSTALL, True)).strip()      # finished productivity modules go into the wheels
            ap.log(snap + " | queue " + queue + " | " + fix + " | " + guard + " | " + ships + ("" if bots.endswith(" 0") else " | " + bots) + ("" if "installed 0 " in mods else " | " + mods), LOG)
        except Exception as exc:  # noqa: BLE001
            ap.log("error: " + repr(exc), LOG)
        time.sleep(ap.CYCLE)


if __name__ == "__main__":
    main()
