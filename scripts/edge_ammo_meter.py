#!/usr/bin/env python3
"""Edgerunner: ammunition used per asteroid killed, measured against what the game's numbers say a kill needs (read-only).
Why (the Captain, 2026-11-20): "calculate how much ammo it will take to kill a target asteroid and only shoot that many". A turret
cannot be given a shot count, so the question becomes: how far over the need are we? The game keeps both counts for the ship's
surface: kills by asteroid name (force.get_kill_count_statistics) and ammunition used (item production statistics, output side).

  need    rounds to kill each asteroid size, from the prototypes: asteroid health and resistances, the ammunition's damage (the
          projectile's own and its area damage both count) and our research bonuses
  mark    writes the counts now to snapshots/edge_ammo_meter.json (do this before a flight)
  since   counts since the mark: kills by size, ammunition used, used per kill against the need
  watch   mark, wait SECONDS, since
Rocket turrets shoot big and huge asteroids only, guns the rest, so rockets are set against big + huge kills and magazines against
small + medium kills. Big asteroids fly only on the Aquilo legs (space connection prototypes): any other leg measures the guns only.
Usage: edge_ammo_meter.py need ; edge_ammo_meter.py mark ; edge_ammo_meter.py since ; edge_ammo_meter.py watch 120"""
import json
import os
import sys
import time

import triangle_miner as TM
from _game import tools

L = tools["run_lua"]
FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "snapshots", "edge_ammo_meter.json")
AMMO = ("explosive-rocket", "rocket", "piercing-rounds-magazine", "uranium-rounds-magazine", "firearm-magazine", "railgun-ammo")

COUNTS = (TM.AT + "local f=game.forces.player local k=f.get_kill_count_statistics(s) local ip=f.get_item_production_statistics(s) local o={tick=game.tick,at=p.space_location and p.space_location.name or 'in flight',kills={},used={}} "
          "for n,c in pairs(k.input_counts) do if n:find('asteroid') then o.kills[n]=c end end for _,n in pairs{%s} do o.used[n]=ip.output_counts[n] or 0 end rcon.print(helpers.table_to_json(o))"
          % ",".join("'%s'" % a for a in AMMO))

# every damage effect found under an ammunition's action, following projectiles into their attack results
NEED = ("local f=game.forces.player local function walk(t,acc,seen) if type(t)~='table' then return end if t.type=='damage' and t.damage then acc[#acc+1]={t.damage.type,t.damage.amount} end "
        "if t.type=='projectile' and t.projectile and not seen[t.projectile] then seen[t.projectile]=true local pr=prototypes.entity[t.projectile] if pr then walk(pr.attack_result,acc,seen) walk(pr.final_attack_result,acc,seen) end end "
        "for _,v in pairs(t) do if type(v)=='table' then walk(v,acc,seen) end end end "
        "local o={} for _,a in pairs{%s} do local it=prototypes.item[a] local at=it.get_ammo_type('turret') or it.get_ammo_type() local acc={} walk(at.action,acc,{}) "
        "local cat=at.category or (it.ammo_category and it.ammo_category.name) local bonus=1+f.get_ammo_damage_modifier(cat) local row={ammo=a,rounds=it.magazine_size or 1,cat=cat,bonus=bonus,dmg=acc,kill={}} "
        "for _,size in pairs{'small','medium','big','huge'} do local as=prototypes.entity[size..'-carbonic-asteroid'] local res=as.resistances or {} local per=0 for _,d in pairs(acc) do local r=res[d[1]] local v=d[2]*bonus "
        "if r then v=math.max(0,v-r.decrease)*(1-r.percent) end per=per+v end row.kill[size]={hp=as.get_max_health(),per=per} end o[#o+1]=row end rcon.print(helpers.table_to_json(o))"
        % ",".join("'%s'" % a for a in ("explosive-rocket", "piercing-rounds-magazine", "uranium-rounds-magazine")))


def counts():
    return json.loads(L(COUNTS))


def need(show=True):
    """{ammo: {size: items (magazines or rockets) for one kill, or None when it does no damage}}"""
    out = {}
    for r in json.loads(L(NEED)):
        out[r["ammo"]] = {}
        parts = []
        for size in ("small", "medium", "big", "huge"):
            k = r["kill"][size]
            if k["per"] <= 0:
                out[r["ammo"]][size] = None
                parts.append("%s: no damage" % size)
            else:
                shots = -(-k["hp"] // k["per"])
                out[r["ammo"]][size] = shots / r["rounds"]
                parts.append("%s (%d hp): %d shots = %.1f %s" % (size, k["hp"], shots, shots / r["rounds"], "magazines" if r["rounds"] > 1 else "rockets"))
        if show:
            dmg = " + ".join("%s %s" % (d[1], d[0]) for d in r["dmg"]) if isinstance(r["dmg"], list) else "?"
            print("%s (%s, research x%.2f): %s" % (r["ammo"], dmg, r["bonus"], "; ".join(parts)))
    return out


def since():
    if not os.path.exists(FILE):
        print("no mark yet: run `mark` first")
        return
    a = json.load(open(FILE, encoding="utf-8"))
    b = counts()
    nd = need(False)
    secs = (b["tick"] - a["tick"]) / 60.0
    print("from %s to %s, %.0f game seconds" % (a["at"], b["at"], secs))
    kills = {}
    for n, c in b["kills"].items():
        d = c - a["kills"].get(n, 0)
        if d:
            size = n.split("-")[0]
            kills[size] = kills.get(size, 0) + d
    used = {n: c - a["used"].get(n, 0) for n, c in b["used"].items() if c - a["used"].get(n, 0)}
    print("kills: " + (", ".join("%s %d" % (s, kills[s]) for s in ("small", "medium", "big", "huge") if s in kills) or "none"))
    print("used:  " + (", ".join("%s %d" % kv for kv in sorted(used.items())) or "nothing"))
    # plain rockets and firearm magazines are INGREDIENTS on this ship (the statistics count them as used when an assembler takes them)
    rk = used.get("explosive-rocket", 0)
    heavy = kills.get("big", 0) + kills.get("huge", 0)
    if heavy:
        want = kills.get("big", 0) * (nd["explosive-rocket"]["big"] or 0) + kills.get("huge", 0) * (nd["explosive-rocket"]["huge"] or 0)
        print("rockets: %d for %d big and huge kills = %.1f a kill; the numbers say %.0f in all (%.0f%% over)" % (rk, heavy, rk / heavy, want, 100 * (rk - want) / want if want else 0))
    elif rk:
        print("rockets: %d used with NO big or huge kill: all of them wasted (wrong targets, or shots at asteroids that left range)" % rk)
    mags = used.get("piercing-rounds-magazine", 0) + used.get("uranium-rounds-magazine", 0)
    light = kills.get("small", 0) + kills.get("medium", 0)
    if light and mags:
        lo = sum(kills.get(s, 0) * (nd["uranium-rounds-magazine"][s] or 0) for s in ("small", "medium"))
        hi = sum(kills.get(s, 0) * (nd["piercing-rounds-magazine"][s] or 0) for s in ("small", "medium"))
        print("magazines: %d for %d small and medium kills = %.2f a kill; the numbers say %.0f (all uranium) to %.0f (all piercing)" % (mags, light, mags / light, lo, hi))


def main():
    a = sys.argv[1:]
    step = a[0] if a else "need"
    if step == "need":
        need()
    elif step == "mark":
        c = counts()
        json.dump(c, open(FILE, "w", encoding="utf-8"), indent=1)
        print("marked at tick %d (%s)" % (c["tick"], c["at"]))
    elif step == "since":
        since()
    elif step == "watch":
        c = counts()
        json.dump(c, open(FILE, "w", encoding="utf-8"), indent=1)
        time.sleep(float(a[1]) if len(a) > 1 else 120)
        since()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
