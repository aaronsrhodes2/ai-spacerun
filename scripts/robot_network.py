#!/usr/bin/env python3
"""Drone supply (the Captain, 2026-11-14): a logistic network detects that it is short of robots, asks for more, the Replicator (or the
robot cells' stock) provides them, and they are put into the network's roboports ("drone ports"), only while the network is short.
Per surface the MAIN network is the one with the most roboport cells. For each robot kind (logistic, construction):
  SHORT (enter)  any of: robots in the network < floor (max(F_MIN, F_PER x roboports): too few for its size);
                 idle share (available/all) < ENTER (0.10) at the last SAMPLES (3) samples spanning >= SPAN ticks (2 game minutes);
                 construction only: ghosts waiting > QUEUE_K (25) x available construction robots (sustained as above).
  OK (exit)      robots >= floor AND idle share >= EXIT (0.25) AND queue short enough, or the shortfall computed is 0. (Hysteresis: 0.10 / 0.25.)
  OVER           idle share > 0.60: reported only; nothing is requested or fed.
  shortfall      max(floor - robots, busy/(1-EXIT) - robots [robots that bring the idle share back to EXIT], ghosts/QUEUE_K - available).
  request        a requester chest (the "robot intake", one per network) gets min = min(CAP (200), shortfall) while SHORT, cleared when OK.
                 The network's stock answers it; what stock lacks is a MISSING REQUEST, which the Replicator (omni_maker.py: logistic-robot and
                 construction-robot are solid-ingredient recipes; frame <- electric engine unit, battery stocks) builds. Never a fixed batch.
  home           DEMAND-GATED: only while SHORT, min(robots in the intake chest, shortfall) are moved into the network's roboports (lowest robot
                 count first, balanced, never past a roboport's slots). A network that is OK receives nothing; the surplus stays in the chest.
  ship           other planets: the same shortfall is also written as a request section 'Robots (auto)' on the planet's landing pad and
                 (fulgora/gleba/vulcanus) on its shuttle's hub (import from Nauvis), so the shuttle carries robots; the intake chest pulls from the pad.
Steps: status | detect | request | home | cycle | build [--apply] [--surface S ...] | test [--surface S] | off
Options: --test-threshold T (enter T, exit T+0.05: fakes a shortage on a healthy network) --test-cap N  --samples N --span TICKS --no-ship
Usage: robot_network.py cycle        (the autopilot runs this every few cycles; failures are logged, not fatal)"""
import json
import math
import sys
import time
from pathlib import Path

from _game import tools

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "snapshots" / "robot_network_state.json"
SURFACES = ["nauvis", "fulgora", "vulcanus", "gleba", "aquilo"]
SHIPS = {"fulgora": "Nauvis-Fulgora 2 Shuttle", "gleba": "Nauvis-Gleba 3 Shuttle", "vulcanus": "Nauvis-Vulcanus 2 Shuttle"}
KINDS = {"l": "logistic-robot", "c": "construction-robot"}
F_MIN = {"l": 40, "c": 20}
F_PER = {"l": 10, "c": 5}
ENTER, EXIT, OVER = 0.10, 0.25, 0.60
SAMPLES, SPAN = 3, 7200
QUEUE_K = 25
CAP = 200

STATS = ("local s=game.surfaces['%(S)s'] if not s then rcon.print('{}') return end local f=game.forces.player local best=nil "
         "for _,p in pairs(s.find_entities_filtered{force=f,type='roboport'}) do local n=p.logistic_network if n and (best==nil or #n.cells>#best.cells) then best=n end end "
         "if not best then rcon.print('{}') return end local r={id=best.network_id,cells=#best.cells,tick=game.tick,al=best.all_logistic_robots,vl=best.available_logistic_robots,ac=best.all_construction_robots,vc=best.available_construction_robots,"
         "ghosts=s.count_entities_filtered{force=f,type='entity-ghost'},cl=0,cc=0,chest=false} "
         "local c=s.find_entities_filtered{name='requester-chest',position={%(X)s,%(Y)s},radius=0.4}[1] if c then r.chest=true r.innet=(c.logistic_network~=nil and c.logistic_network.network_id==best.network_id) "
         "for _,it in pairs(c.get_inventory(defines.inventory.chest).get_contents()) do if it.name=='logistic-robot' then r.cl=r.cl+it.count elseif it.name=='construction-robot' then r.cc=r.cc+it.count end end "
         "r.stock_l=best.get_item_count('logistic-robot') r.stock_c=best.get_item_count('construction-robot') r.frames=best.get_item_count('flying-robot-frame') r.engines=best.get_item_count('electric-engine-unit') r.batteries=best.get_item_count('battery') end "
         "rcon.print(helpers.table_to_json(r))")

SETREQ = ("local s=game.surfaces['%(S)s'] local c=s.find_entities_filtered{name='requester-chest',position={%(X)s,%(Y)s},radius=0.4}[1] if not c then rcon.print('no intake chest') return end "
          "local pt=c.get_logistic_point(defines.logistic_member_index.logistic_container) local sec=nil for _,x in pairs(pt.sections) do if x.group=='Robot intake' then sec=x end end "
          "if not sec then sec=pt.add_section() sec.group='Robot intake' end sec.filters={} local L,C=%(L)d,%(C)d "
          "if L>0 then sec.set_slot(1,{value={type='item',name='logistic-robot',quality='normal'},min=L}) end if C>0 then sec.set_slot(2,{value={type='item',name='construction-robot',quality='normal'},min=C}) end "
          "rcon.print('intake request logistic '..L..' construction '..C)")

FEED = ("local s=game.surfaces['%(S)s'] local f=game.forces.player local nm='%(N)s' local want=%(A)d "
        "local c=s.find_entities_filtered{name='requester-chest',position={%(X)s,%(Y)s},radius=0.4}[1] if not c or want<=0 then rcon.print('fed 0') return end local net=c.logistic_network if not net then rcon.print('chest outside network') return end "
        "local ci=c.get_inventory(defines.inventory.chest) local took={} local got=0 for _,it in pairs(ci.get_contents()) do if it.name==nm and got<want then local n=math.min(it.count,want-got) local r=ci.remove{name=nm,count=n,quality=it.quality} if r>0 then took[#took+1]={it.quality,r} got=got+r end end end "
        "if got==0 then rcon.print('fed 0 (chest empty)') return end local ports={} for _,cell in pairs(net.cells) do local o=cell.owner if o and o.valid and o.type=='roboport' then local inv=o.get_inventory(defines.inventory.roboport_robot) if inv then ports[#ports+1]={o,inv,inv.get_item_count(nm)} end end end "
        "table.sort(ports,function(a,b) return a[3]<b[3] end) local per=math.max(1,math.ceil(got/math.max(1,math.min(#ports,math.ceil(got/25))))) local put=0 "
        "for _,tk in pairs(took) do local left=tk[2] for _,p in ipairs(ports) do if left<=0 then break end local ins=p[2].insert{name=nm,count=math.min(per,left),quality=tk[1]} left=left-ins put=put+ins end "
        "if left>0 then ci.insert{name=nm,count=left,quality=tk[1]} end end rcon.print('fed '..put..' '..nm..' into '..#ports..' roboports (took '..got..' from the intake chest)')")

SHIP = ("local s=game.surfaces['%(S)s'] local f=game.forces.player local L,C=%(L)d,%(C)d local o={} "
        "local function setsec(ent,imp) for _,pt in pairs(ent.get_logistic_point()) do if pt.mode==defines.logistic_mode.requester then local sec=nil for _,x in pairs(pt.sections) do if x.group=='Robots (auto)' then sec=x end end "
        "if not sec then sec=pt.add_section() sec.group='Robots (auto)' end sec.filters={} local function put(i,nm,n) if n>0 then local sl={value={type='item',name=nm,quality='normal'},min=n} if imp then sl.max=n*2+60 sl.import_from='nauvis' end sec.set_slot(i,sl) end end "
        "put(1,'logistic-robot',L) put(2,'construction-robot',C) return true end end return false end "
        "local pad=s.find_entities_filtered{type='cargo-landing-pad'}[1] o[#o+1]='pad '..tostring(pad and setsec(pad,false)) local ship='%(SHIP)s' "
        "if ship~='' then for _,p in pairs(f.platforms) do if p.valid and p.hub and p.name:sub(-#ship)==ship then o[#o+1]='hub '..tostring(setsec(p.hub,true)) end end end rcon.print(table.concat(o,', '))")


ANCHOR = ("local s=game.surfaces['%s'] if not s then rcon.print('none') return end local f=game.forces.player local best=nil for _,p in pairs(s.find_entities_filtered{force=f,type='roboport'}) do local n=p.logistic_network if n and (best==nil or #n.cells>#best.cells) then best=n end end "
          "if not best then rcon.print('none') return end local pad=s.find_entities_filtered{type='cargo-landing-pad'}[1] local ax,ay=-270,-200 if '%s'~='nauvis' and pad then ax,ay=pad.position.x,pad.position.y end "
          "local bp,bd=nil,1e12 for _,cell in pairs(best.cells) do local o=cell.owner if o.type=='roboport' then local d=(o.position.x-ax)^2+(o.position.y-ay)^2 if d<bd then bd=d bp=o end end end rcon.print(bp.position.x..','..bp.position.y)")


def lua(code, **kw):
    return tools["run_lua"](code % kw).strip()


def pos(surface):
    st = load().get("chests", {})
    return st.get(surface)


def load():
    try:
        return json.loads(STATE.read_text())
    except Exception:  # noqa: BLE001
        return {}


def save(st):
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps(st, indent=1))


def stats(surface):
    p = pos(surface) or (0, 0)
    out = lua(STATS, S=surface, X=p[0], Y=p[1])
    return json.loads(out) if out.startswith("{") and out != "{}" else None


def decide(surface, a, st, enter=ENTER, exit_=EXIT, samples=SAMPLES, span=SPAN, cap=CAP, persist=True):
    """Decision per kind from the stats and the sample history in st. Returns {kind: {...}}."""
    d = {}
    hist = st.setdefault("hist", {}).setdefault(surface, [])
    hist.append({"t": a["tick"], "rl": a["vl"] / a["al"] if a["al"] else 0, "rc": a["vc"] / a["ac"] if a["ac"] else 0, "g": a["ghosts"], "vc": a["vc"]})
    del hist[:-12]
    flags = st.setdefault("short", {}).setdefault(surface, {})
    for k in "lc":
        tot, av = a["a" + k], a["v" + k]
        busy = tot - av
        ratio = av / tot if tot else 0.0
        floor = max(F_MIN[k], F_PER[k] * a["cells"])
        recent = hist[-samples:]
        sustained = len(recent) >= samples and recent[-1]["t"] - recent[0]["t"] >= span
        low = sustained and all(h["r" + k] < enter for h in recent)
        queue = 0
        qrule = False
        if k == "c":
            queue = math.ceil(a["ghosts"] / QUEUE_K) - av
            qrule = queue > 0 and sustained and all(h["g"] > QUEUE_K * max(h["vc"], 1) for h in recent)
        need_floor = max(0, floor - tot)
        need_ratio = max(0, math.ceil(busy / (1 - exit_)) - tot) if ratio < exit_ else 0
        need_q = max(0, queue) if qrule else 0
        short_new = need_floor > 0 or low or qrule
        was = bool(flags.get(k))
        shortfall = max(need_floor, need_ratio, need_q)
        if was:
            is_short = shortfall > 0 and not (tot >= floor and ratio >= exit_ and not qrule)
        else:
            is_short = short_new
        if persist:
            flags[k] = is_short
        have = a["c" + k]
        d[k] = {"robots": tot, "idle": av, "ratio": round(ratio, 3), "floor": floor, "state": ("SHORT" if is_short else ("OVER" if ratio > OVER else "OK")),
                "shortfall": shortfall if is_short else 0, "want": min(cap, shortfall) if is_short else 0, "chest": have, "queue": queue if k == "c" else None,
                "why": [w for w, c in (("floor", need_floor > 0), ("idle<%.2f" % enter, low), ("queue", qrule)) if c]}
    return d


def run_surface(surface, args, do_request, do_home, ship=True, st=None):
    a = stats(surface)
    if not a:
        return None
    test = args.get("test")
    enter, exit_ = (test, min(0.95, test + 0.05)) if test is not None else (ENTER, EXIT)
    d = decide(surface, a, st, enter, exit_, args.get("samples", 1 if test is not None else SAMPLES), args.get("span", 0 if test is not None else SPAN),
               args.get("cap", CAP), persist=test is None)
    line = {"surface": surface, "net": a["id"], "cells": a["cells"], "ghosts": a["ghosts"], "chest": a["chest"] and a.get("innet"), "d": d,
            "stock": [a.get("stock_l"), a.get("stock_c")], "frames/engines/batteries": [a.get("frames"), a.get("engines"), a.get("batteries")]}
    if do_request and a["chest"]:
        line["request"] = lua(SETREQ, S=surface, X=pos(surface)[0], Y=pos(surface)[1], L=d["l"]["want"], C=d["c"]["want"])
        if ship and (surface in SHIPS or surface == "aquilo"):
            try:
                line["ship"] = lua(SHIP, S=surface, L=d["l"]["want"], C=d["c"]["want"], SHIP=SHIPS.get(surface, ""))
            except Exception as exc:  # noqa: BLE001
                line["ship"] = "error " + repr(exc)
    if do_home and a["chest"]:
        line["home"] = []
        for k in "lc":
            n = min(a["c" + k], d[k]["shortfall"]) if d[k]["state"] == "SHORT" else 0
            line["home"].append(lua(FEED, S=surface, X=pos(surface)[0], Y=pos(surface)[1], N=KINDS[k], A=n) if n > 0 else "gate closed (%s, %s): fed 0" % (KINDS[k], d[k]["state"]))
    return line


def surfaces_from(argv):
    s = [argv[i + 1] for i, x in enumerate(argv) if x == "--surface"]
    return s or [x for x in SURFACES if x in load().get("chests", {})] or ["nauvis"]


def optval(argv, name, cast):
    return cast(argv[argv.index(name) + 1]) if name in argv else None


def cycle(argv=None, request=True, home=True):
    argv = argv or []
    args = {}
    for n, c, key in (("--test-threshold", float, "test"), ("--test-cap", int, "cap"), ("--samples", int, "samples"), ("--span", int, "span")):
        v = optval(argv, n, c)
        if v is not None:
            args[key] = v
    st = load()
    out = []
    for s in surfaces_from(argv):
        line = run_surface(s, args, request, home, "--no-ship" not in argv, st)
        if line:
            out.append(line)
    if "test" not in args:
        save(st)
    return out


def summary(lines):
    for ln in lines:
        d = ln["d"]
        print("%s net %s cells %d ghosts %d chest %s | logistic %s %d/%d idle (%.0f%%, floor %d, short %d, want %d, chest %d) | construction %s %d/%d idle (%.0f%%, floor %d, short %d, want %d, chest %d, queue %s) | stock %s frames/engines/batteries %s" % (
            ln["surface"], ln["net"], ln["cells"], ln["ghosts"], ln["chest"], d["l"]["state"], d["l"]["idle"], d["l"]["robots"], 100 * d["l"]["ratio"], d["l"]["floor"], d["l"]["shortfall"], d["l"]["want"], d["l"]["chest"],
            d["c"]["state"], d["c"]["idle"], d["c"]["robots"], 100 * d["c"]["ratio"], d["c"]["floor"], d["c"]["shortfall"], d["c"]["want"], d["c"]["chest"], d["c"]["queue"], ln["stock"], ln["frames/engines/batteries"]))
        for k in ("request", "ship", "home"):
            if ln.get(k):
                print("   ", k, ln[k])


def build(argv):
    apply = "--apply" in argv
    st = load()
    ch = st.setdefault("chests", {})
    for s in surfaces_from(argv) if "--surface" in argv else SURFACES:
        if s in ch:
            print(s, "intake chest already at", ch[s])
            continue
        out = tools["run_lua"](ANCHOR % (s, s)).strip()
        if out == "none":
            print(s, "no roboport network")
            continue
        px, py = (float(v) for v in out.split(","))
        done = False
        for dx, dy in [(3.5, -1.5), (3.5, 1.5), (-3.5, -1.5), (-3.5, 1.5), (1.5, 3.5), (-1.5, 3.5), (1.5, -3.5), (-1.5, -3.5), (5.5, 0.5), (-5.5, 0.5), (0.5, 5.5), (0.5, -5.5)]:
            x, y = math.floor(px + dx) + 0.5, math.floor(py + dy) + 0.5
            ent = json.dumps([{"name": "requester-chest", "x": x, "y": y, "direction": 0, "params": {"quality": "epic"}}])
            r = json.loads(tools["place_entities"](ent, surface=s, dry_run=True))
            if r.get("placed") and not r.get("failed"):
                if apply:
                    r = json.loads(tools["place_entities"](ent, surface=s, dry_run=False))
                    if not r.get("placed"):
                        continue
                    ch[s] = [x, y]
                print(s, "intake chest", "placed" if apply else "dry run ok", (x, y), "beside roboport", (px, py))
                done = True
                break
        if not done:
            print(s, "no free spot beside roboport", (px, py))
    if apply:
        save(st)


def off(argv):
    for s, p in load().get("chests", {}).items():
        print(s, lua(SETREQ, S=s, X=p[0], Y=p[1], L=0, C=0))
        if s in SHIPS or s == "aquilo":
            print(s, lua(SHIP, S=s, L=0, C=0, SHIP=SHIPS.get(s, "")))
    st = load()
    st["short"] = {}
    save(st)


def test(argv):
    """Fake a shortage on a healthy network (default nauvis, threshold 0.8, cap 50), time the stages, then switch the request off."""
    s = optval(argv, "--surface", str) or "nauvis"
    thr = optval(argv, "--test-threshold", float) or 0.8
    cap = optval(argv, "--test-cap", int) or 50
    base = ["--surface", s, "--test-threshold", str(thr), "--test-cap", str(cap), "--no-ship"]
    t0 = time.time()
    print("== OK network, normal thresholds: nothing may move")
    summary(cycle(["--surface", s, "--no-ship"]))
    print("== fake shortage (threshold %.2f, cap %d)" % (thr, cap))
    summary(cycle(base, True, False))
    for i in range(8):
        time.sleep(15)
        print("-- t+%ds" % (time.time() - t0))
        summary(cycle(base, False, True))
    print("== threshold back to normal: gate must close")
    summary(cycle(["--surface", s, "--no-ship"]))
    off(argv)


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "status"
    if step == "build":
        build(sys.argv)
    elif step == "off":
        off(sys.argv)
    elif step == "test":
        test(sys.argv)
    elif step in ("status", "detect"):
        summary(cycle(sys.argv, False, False))
    elif step == "request":
        summary(cycle(sys.argv, True, False))
    elif step == "home":
        summary(cycle(sys.argv, False, True))
    else:
        summary(cycle(sys.argv, True, True))
