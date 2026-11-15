#!/usr/bin/env python3
"""Steady-demand watch for the Replicator grid (the Captain, 2026-11-14: the Replicators serve building items and special orders; goods with
a CONTINUOUS need belong on dedicated lines). Each autopilot cycle samples the demand the cells read (the hub roboport's circuit signal on
Nauvis: missing requests + orbital silo requests). An item demanded in >= SHARE of the last WINDOW samples (and at least MIN samples) is a
steady consumer: it is reported once a day in game chat and in the log as "needs a dedicated line". It never changes the menus itself.
State: snapshots/replicator_demand_watch.json.   Usage: replicator_demand_watch.py sample | status"""
import json
import sys
import time
from pathlib import Path

from _game import tools

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "snapshots" / "replicator_demand_watch.json"
HUB = (-352, -229)
WINDOW, MIN, SHARE, REPEAT_S = 60, 30, 0.75, 86400
READ = ("local r=game.surfaces.nauvis.find_entities_filtered{name='roboport',position={%s,%s},radius=0.6}[1] if not r then rcon.print('') return end local t={} "
        "for _,w in pairs({defines.wire_connector_id.circuit_red,defines.wire_connector_id.circuit_green}) do local n=r.get_circuit_network(w) "
        "if n and n.signals then for _,s in pairs(n.signals) do if s.signal.type==nil or s.signal.type=='item' then if s.count>0 then t[s.signal.name]=true end end end end end "
        "local o={} for k in pairs(t) do o[#o+1]=k end rcon.print(table.concat(o,' '))")


def load():
    try:
        return json.loads(STATE.read_text())
    except (OSError, ValueError):
        return {"samples": [], "alerted": {}}


def steady(st):
    smp = st["samples"]
    if len(smp) < MIN:
        return []
    cnt = {}
    for s in smp:
        for it in s:
            cnt[it] = cnt.get(it, 0) + 1
    return sorted((it, c / len(smp)) for it, c in cnt.items() if c / len(smp) >= SHARE)


def sample():
    """Autopilot step. Never raises."""
    try:
        st = load()
        st["samples"] = (st["samples"] + [tools["run_lua"](READ % HUB).split()])[-WINDOW:]
        now, new = time.time(), []
        for it, share in steady(st):
            if now - st["alerted"].get(it, 0) > REPEAT_S:
                st["alerted"][it] = now
                new.append("%s (%d%%)" % (it, share * 100))
        STATE.write_text(json.dumps(st))
        if new:
            msg = "Replicator steady demand, needs a dedicated line: " + ", ".join(new)
            tools["run_lua"]("game.print('[color=1,0.67,0][Skippy][/color] %s') rcon.print('ok')" % msg.replace("'", ""))
            return msg
        return "demand watch: %d samples, %d items wanted now" % (len(st["samples"]), len(st["samples"][-1]))
    except Exception as exc:  # noqa: BLE001
        return "demand watch error " + repr(exc)


if __name__ == "__main__":
    if (sys.argv[1] if len(sys.argv) > 1 else "status") == "sample":
        print(sample())
    else:
        st = load()
        print("samples", len(st["samples"]), "| steady:", steady(st), "| now wanted:", st["samples"][-1] if st["samples"] else [])
