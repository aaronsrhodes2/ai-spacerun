#!/usr/bin/env python3
"""
Entry point for a local agent (purple Skippy). It never touches the game itself: it tells the agent what exists, what comes next, and the exact command to run.

    nauvis.py list                 every command with its status (ready / partial / gap)
    nauvis.py describe NAME        one command in full (what it does, how to verify, how to roll back)
    nauvis.py runbook              the ordered phases with their gates
    nauvis.py milestones           tech -> actions table
    nauvis.py next                 the first runbook step whose command is not yet marked done in state.json
    nauvis.py done STEP            mark a runbook step done in state.json (after its verify passed)

The agent runs the printed command itself (dry run first, then --apply) and reads the JSON that the scripts print.
Registry of coordinates, lanes and names lives in state.json next to this file.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAN = json.loads((HERE / "manifest.json").read_text())["commands"]
MIL = json.loads((HERE / "milestones.json").read_text())["milestones"]
STATE = HERE / "state.json"


def load_state():
    return json.loads(STATE.read_text()) if STATE.exists() else {"done": [], "registry": {}}


RUNBOOK = [
    ("audit", "audit", "1. Audit: no unexplained bottlenecks and science rates equal"),
    ("science-rates", "science-rates", "1b. Equalise the seven science packs"),
    ("discover", "discover", "2. Find every resource patch"),
    ("clear", "clear", "2b. Clear vegetation, rocks, enemies around each patch (never the crash site)"),
    ("pave", "pave", "3. Floor the cleared areas"),
    ("rail-line", "rail-line", "3b. Tracks between clearings and to the bus"),
    ("mine", "mine", "4. Cover each patch with drills"),
    ("train-outpost", "train-outpost", "5. Iron and copper: furnace block and train station next to the patch"),
    ("fluid-train-oil", "fluid-train-oil", "6. Oil by fluid train to the holding tanks"),
    ("uranium-outpost", "uranium-outpost", "8. Uranium to the processing centre"),
    ("cells", "cells", "9. Production cells where audit says the bottleneck is"),
    ("silos", "silos", "9b. Rocket parts and silos"),
    ("space-platform", "space-platform", "10. Orbital platform for extra iron, carbon, ice"),
]


def by_name():
    return {c["name"]: c for c in MAN}


def main():
    a = sys.argv[1:] or ["list"]
    cmd = a[0]
    if cmd == "list":
        for c in MAN:
            print(f"{c['status']:8s} {c['name']:18s} {c['does']}")
    elif cmd == "describe":
        print(json.dumps(by_name()[a[1]], indent=1))
    elif cmd == "runbook":
        for step, name, text in RUNBOOK:
            print(f"{by_name()[name]['status']:8s} {step:16s} {text}")
    elif cmd == "milestones":
        for m in MIL:
            print(f"{m['state']:5s} {m['tech']:34s} -> {', '.join(m['actions'])}{'' if m['have'] else '   [GAP: ' + m.get('gap', '') + ']'}")
    elif cmd == "next":
        done = set(load_state()["done"])
        for step, name, text in RUNBOOK:
            if step not in done:
                c = by_name()[name]
                print(text)
                print("status:", c["status"])
                print("run:   ", c["run"])
                print("verify:", c.get("verify", "-"))
                if c["status"] == "gap":
                    print("This step has no script yet: tell the Captain; do not improvise.")
                return
        print("runbook complete")
    elif cmd == "done":
        s = load_state()
        s["done"].append(a[1])
        STATE.write_text(json.dumps(s, indent=1))
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
