#!/usr/bin/env python3
"""Same autopilot as autopilot_server.py but run from this PC through the SSH tunnel (no service installed on the VM).
Usage: scripts/autopilot_local.py [cycles]   (default: run until stopped). Log: docs/autopilot.log"""
import sys
import time
from pathlib import Path

from _game import tools

import autopilot_server as ap

LOG = str(Path(__file__).resolve().parent.parent / "docs" / "autopilot.log")


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
            ap.log(snap + " | queue " + queue + " | " + fix + " | " + guard + " | " + ships, LOG)
        except Exception as exc:  # noqa: BLE001
            ap.log("error: " + repr(exc), LOG)
        time.sleep(ap.CYCLE)


if __name__ == "__main__":
    main()
