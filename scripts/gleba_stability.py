#!/usr/bin/env python3
"""Gleba stability watch (2026-11-16, the Captain: "an automated gleba watch set up until it's stable"). Runs from the autopilot every few cycles.
Each sample reads the labs, the research, the cell's stocks and the stuck-machine counts, appends one line to snapshots/gleba_stability.jsonl and keeps a state file
(snapshots/gleba_stability_state.json) with the clock of "hours since the last alarm". An alarm needs 2 samples in a row; it is logged, printed in game, and answered
once per episode by gleba_restart.run(True) (moves spoilage, eggs, fuel, seeds; creates nothing). Every alarm resets the clock.
Stable = STABLE_HOURS (10, the pass mark in docs/gleba-stable-cell.md) with no alarm; the watch then logs "GLEBA STABLE" once and keeps running quietly (one line a day).
Alarms: labs idle (2 or fewer of the labs working), eggs gone, bioflux low, nutrients gone, fruit processors stuck with a full output, biochambers without fuel,
seeds piling up past the sink trigger, agricultural packs missing from the labs.
Usage: gleba_stability.py [--apply-heal]   one sample now and print it (heal only with the flag)"""
import json
import sys
import time
from pathlib import Path

from _game import tools

ROOT = Path(__file__).resolve().parent.parent
LOGF = ROOT / "snapshots" / "gleba_stability.jsonl"
STATE = ROOT / "snapshots" / "gleba_stability_state.json"
STABLE_HOURS = 10.0
KEEP_LINES = 3000

SAMPLE = """
local s=game.surfaces.gleba local f=game.forces.player local E=defines.entity_status
local net=s.find_logistic_network_by_position({90,26},f)
local function nm(v) for k,x in pairs(E) do if x==v then return k end end return '?' end
local labs,work,agri=0,0,0 for _,e in pairs(s.find_entities_filtered{type='lab',force=f}) do labs=labs+1 if e.status==E.working then work=work+1 end local inv=e.get_inventory(defines.inventory.lab_input) agri=agri+inv.get_item_count('agricultural-science-pack') end
local c=f.current_research
local st={egg_work=0,egg_full=0,egg_total=0,proc_full=0,bio_nofuel=0,pack_work=0,pack_total=0}
for _,m in pairs(s.find_entities_filtered{type='assembling-machine',force=f}) do local r=m.get_recipe() if r then
  if r.name=='pentapod-egg' then st.egg_total=st.egg_total+1 if m.status==E.working then st.egg_work=st.egg_work+1 elseif m.status==E.full_output then st.egg_full=st.egg_full+1 end
  elseif r.name=='yumako-processing' or r.name=='jellynut-processing' then if m.status==E.full_output then local out=m.get_inventory(defines.inventory.crafter_output) if out.get_item_count('yumako-seed')+out.get_item_count('jellynut-seed')>0 then st.proc_full=st.proc_full+1 end end
  elseif r.name=='agricultural-science-pack' then st.pack_total=st.pack_total+1 if m.status==E.working then st.pack_work=st.pack_work+1 end end end
  if m.name=='biochamber' and m.status==E.no_fuel and not m.get_inventory(defines.inventory.crafter_input).is_empty() then st.bio_nofuel=st.bio_nofuel+1 end end
local function g(n) return net and net.get_item_count(n) or -1 end
rcon.print(helpers.table_to_json({labs=labs,work=work,agri=agri,research=c and c.name or 'none',progress=f.research_progress,bioflux=g('bioflux'),nutrients=g('nutrients'),eggs=g('pentapod-egg'),
  yseed=g('yumako-seed'),jseed=g('jellynut-seed'),yumako=g('yumako'),jellynut=g('jellynut'),st=st}))
"""


def read():
    raw = tools["run_lua"](" ".join(SAMPLE.split("\n"))).strip()
    return json.loads(raw)


def alarms(m):
    a = []
    st = m["st"]
    if m["labs"] and m["work"] <= 2:
        a.append("labs idle (%d of %d working)" % (m["work"], m["labs"]))
    if m["eggs"] == 0 and st["egg_work"] == 0:
        a.append("no eggs and no egg chamber working")
    if 0 <= m["bioflux"] < 100:
        a.append("bioflux %d (below 100)" % m["bioflux"])
    if 0 <= m["nutrients"] < 50:
        a.append("nutrients %d" % m["nutrients"])
    if st["proc_full"] > 0:
        a.append("%d fruit processors stuck with seeds in the output" % st["proc_full"])
    if st["bio_nofuel"] >= 4:
        a.append("%d biochambers without fuel" % st["bio_nofuel"])
    if m["yseed"] > 1300 or m["jseed"] > 1300:
        a.append("seeds piling up (yumako %d, jellynut %d)" % (m["yseed"], m["jseed"]))
    if m["labs"] and m["agri"] == 0:
        a.append("no agricultural packs in the labs")
    return a


def load_state():
    try:
        return json.loads(STATE.read_text())
    except Exception:  # noqa: BLE001
        return {"since": time.time(), "streak": {}, "healed": [], "last_summary": 0, "stable_logged": False, "samples": 0}


def trim_log():
    try:
        lines = LOGF.read_text().splitlines()
        if len(lines) > KEEP_LINES:
            LOGF.write_text("\n".join(lines[-KEEP_LINES:]) + "\n")
    except Exception:  # noqa: BLE001
        pass


def sample(heal=True):
    """One sample. Returns a log line when something should be logged (alarm, heal, hourly summary), else ''."""
    now = time.time()
    m = read()
    state = load_state()
    state["samples"] = state.get("samples", 0) + 1
    active = alarms(m)
    old = state.get("streak", {})
    new = {a: old.get(a, 0) + 1 for a in active}
    state["streak"] = new
    firing = [a for a, n in new.items() if n >= 2]
    out = []
    if firing:
        episode_new = [a for a in firing if a not in state.get("healed", [])]
        if episode_new:
            out.append("GLEBA ALARM: " + "; ".join(firing) + " | stable clock reset (was %.1f h)" % ((now - state["since"]) / 3600))
            state["since"] = now
            state["stable_logged"] = False
            if heal:
                try:
                    import gleba_restart
                    out.append("heal: " + gleba_restart.run(True))
                except Exception as exc:  # noqa: BLE001
                    out.append("heal error: " + repr(exc))
            try:
                tools["run_lua"]("game.print('GLEBA WATCH: " + "; ".join(firing).replace("'", "") + "')")
            except Exception:  # noqa: BLE001
                pass
        state["healed"] = firing
    else:
        state["healed"] = []
    hours = (now - state["since"]) / 3600
    if hours >= STABLE_HOURS and not state.get("stable_logged"):
        out.append("GLEBA STABLE: %.1f h with no alarm (pass mark %.0f h); the watch keeps running, one line a day" % (hours, STABLE_HOURS))
        state["stable_logged"] = True
    summary_every = 86400 if state.get("stable_logged") else 3600
    if now - state.get("last_summary", 0) >= summary_every:
        out.append("gleba watch: stable %.1f of %.0f h | labs %d/%d working, %s %.0f%% | bioflux %d nutrients %d eggs %d | seeds Y%d J%d | stuck: egg-full %d, proc-full %d, no-fuel %d | packs in labs %d"
                   % (hours, STABLE_HOURS, m["work"], m["labs"], m["research"], 100 * m["progress"], m["bioflux"], m["nutrients"], m["eggs"], m["yseed"], m["jseed"],
                      m["st"]["egg_full"], m["st"]["proc_full"], m["st"]["bio_nofuel"], m["agri"]))
        state["last_summary"] = now
    try:
        with open(LOGF, "a") as fh:
            fh.write(json.dumps({"t": int(now), "m": m, "alarms": active}) + "\n")
        if state["samples"] % 200 == 0:
            trim_log()
        STATE.write_text(json.dumps(state))
    except Exception:  # noqa: BLE001
        pass
    return " || ".join(out)


def main():
    r = sample(heal="--apply-heal" in sys.argv)
    m = read()
    print(json.dumps(m))
    print("alarms now:", alarms(m) or "none")
    print("log line:", r or "(nothing to log)")


if __name__ == "__main__":
    main()
