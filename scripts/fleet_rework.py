#!/usr/bin/env python3
"""Fleet rework, part 1: timed schedules (the Captain, 2026-11-18: "shuttles that run on a timed schedule and only wait if there is a
package ready to be delivered, but moves on and lets the next shuttle take the next load if time's up"; "running requirements not cargo
requirements, only cargo wants").

Every stop of every shuttle becomes
      RUN and WANT and at least TMIN seconds      or      RUN and TMAX seconds
  RUN    what the ship needs to fly and fight, all of it made on board: the fluid conditions (thruster fuel, oxidizer) and its own
         ammunition count. Taken from the stop's existing conditions. A ship that cannot meet RUN stays parked: that is the safe state.
  WANT   cargo, never a requirement: the stop's existing cargo conditions if it had any (so many packs aboard, the drop finished),
         otherwise "no cargo moved for QUIET seconds", which is true as soon as nothing is being loaded or unloaded.
  TMAX   the way out. Whatever the cargo did, the ship leaves when TMAX is up and the next shuttle takes the next load.
Conditions on goods that come from a PLANET (explosive rockets, uranium rounds, repair packs, carbon, iron ore on the two Aquilo shuttles)
are neither: those ships are skipped here until their ammunition is made on board (part 2).
Steps: plan | apply [INDEX ...] | show INDEX
Usage: fleet_rework.py plan ; fleet_rework.py apply ; fleet_rework.py apply 5 34"""
import json
import sys

from _game import tools
from fleet_survey import shuttles

L = tools["run_lua"]
TMIN, QUIET = 30, 60
TMAX = {"nauvis": 900}          # seconds; other stops TMAX_FAR
TMAX_FAR = 300
RUN_ITEMS = {"firearm-magazine", "piercing-rounds-magazine", "signal-M"}                 # made on board (signal-M: Courier's magazine count)
PLANET_FED = {"explosive-rocket", "uranium-rounds-magazine", "repair-pack", "carbon", "iron-ore", "rocket"}

GET = "local p=game.forces.player.platforms[%d] rcon.print(helpers.table_to_json({name=p.name,schedule=p.schedule}))"
SET = "local p=game.forces.player.platforms[%d] local sc=helpers.json_to_table('%s') p.schedule=sc rcon.print('written, current '..p.schedule.current)"


def kind(c):
    if c["type"] in ("time", "inactivity"):
        return "time"
    if c["type"] == "circuit" or c["type"] == "item_count" or c["type"] == "fluid_count":
        sig = (c.get("condition") or {}).get("first_signal") or {}
        if sig.get("type") == "fluid" or sig.get("name") in RUN_ITEMS:
            return "run"
        if sig.get("name") in PLANET_FED:
            return "planet"
        return "cargo"
    return "cargo"                                   # all_requests_satisfied and the like


def rework(record):
    conds = record.get("wait_conditions") or []
    first = []                                       # the first AND group is the stop's intent; later OR groups are old fallbacks
    for i, c in enumerate(conds):
        if i > 0 and c.get("compare_type") == "or":
            break
        first.append(c)
    run = [dict(c, compare_type="and") for c in first if kind(c) == "run"]
    cargo = [dict(c, compare_type="and") for c in first if kind(c) == "cargo"]
    planet = [c for c in first if kind(c) == "planet"]
    if planet:
        return None, "needs planet-fed goods: " + ", ".join(c["condition"]["first_signal"]["name"] for c in planet)
    want = cargo or [{"type": "inactivity", "compare_type": "and", "ticks": QUIET * 60}]
    tmax = TMAX.get(record["station"], TMAX_FAR)
    out = run + want + [{"type": "time", "compare_type": "and", "ticks": TMIN * 60}]
    fb = [dict(c) for c in run] + [{"type": "time", "compare_type": "and", "ticks": tmax * 60}]
    fb[0]["compare_type"] = "or"
    return out + fb, "run %d, want %s, at most %d s" % (len(run), "cargo x%d" % len(cargo) if cargo else "quiet %d s" % QUIET, tmax)


def main():
    a = sys.argv[1:]
    step = a[0] if a else "plan"
    idx = [int(x) for x in a[1:] if x.isdigit()] or shuttles()
    for i in idx:
        d = json.loads(L(GET % i))
        sc = d.get("schedule")
        name = d["name"].split("]")[-1].strip()
        if not sc or not sc.get("records"):
            print(i, name, "no schedule")
            continue
        if step == "show":
            print(json.dumps(sc, indent=1)[:3000])
            continue
        notes, ok = [], True
        for r in sc["records"]:
            new, note = rework(r)
            notes.append("%s: %s" % (r["station"], note))
            if new is None:
                ok = False
            else:
                r["wait_conditions"] = new
        if not ok:
            print(i, name, "SKIPPED |", " | ".join(notes))
            continue
        if step == "apply":
            js = json.dumps(sc).replace("\\", "\\\\").replace("'", "\\'")
            print(i, name, "|", " | ".join(notes), "|", L(SET % (i, js)).strip())
        else:
            print(i, name, "|", " | ".join(notes))


if __name__ == "__main__":
    main()
