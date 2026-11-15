#!/usr/bin/env python3
"""Replicator hotspot detector (read-only): which goods is the Replicator (the make-anything block, area x -366..-288, y -232..-186) mostly busy making?
A universal maker is the wrong tool for a steady flow: while one of its units sits on one recipe, everything else waits for that unit. If a single
item takes a big share of a unit's working time, or the units are almost never free, that item belongs on static machines (build_cells.py kinds, belts),
or the Replicator needs more units / a second copy.

Method: poll the machines every 2 s for --seconds (default 60). Each poll, the machine's `products_finished` delta is credited to the recipe it held
before the poll; time spent working / blocked (no ingredients) / idle is counted per recipe.
Verdict per recipe: HOT when it holds 40%+ of the Replicator's total working time or runs 60%+ of a unit's time.

Usage: scripts/replicator_hotspots.py [--seconds 60] [--interval 2]
Exit text is plain; the ranker (worst_bottleneck.py) does not call this yet (a 1 minute sample is too slow for it)."""
import sys
import time

from _game import tools

SECONDS = float(sys.argv[sys.argv.index("--seconds") + 1]) if "--seconds" in sys.argv else 60.0
INTERVAL = float(sys.argv[sys.argv.index("--interval") + 1]) if "--interval" in sys.argv else 2.0

LUA = r'''
local s = game.surfaces.nauvis
local SN = {}
for k, v in pairs(defines.entity_status) do SN[v] = k end
local o = {}
for _, m in ipairs(s.find_entities_filtered{area = {{-366, -232}, {-288, -186}}, force = game.forces.player, type = {'assembling-machine', 'furnace', 'chemical-plant'}}) do
  local r = m.get_recipe()
  if not r and m.type == 'furnace' then r = m.previous_recipe end
  local rn = r and r.name or '-'
  o[#o + 1] = string.format('%.1f,%.1f|%s|%s|%d', m.position.x, m.position.y, rn, tostring(SN[m.status]), m.products_finished)
end
rcon.print(table.concat(o, ';'))
'''


def poll():
    out = {}
    for part in tools["run_lua"](LUA).split(";"):
        f = part.split("|")
        if len(f) == 4:
            out[f[0]] = (f[1], f[2], int(f[3]))
    return out


def main():
    prev = poll()
    t0 = time.time()
    polls = 0
    stat = {}          # recipe -> {crafts, work, blocked, idle}
    per_machine = {}   # machine key -> {recipe: polls working}
    while time.time() - t0 < SECONDS:
        time.sleep(INTERVAL)
        cur = poll()
        polls += 1
        for key, (rn, st, made) in prev.items():
            if key not in cur or rn in ("-", "None"):
                continue
            d = stat.setdefault(rn, {"crafts": 0, "work": 0, "blocked": 0, "idle": 0, "full": 0})
            delta = cur[key][2] - made
            if delta > 0:
                d["crafts"] += delta
            if st == "working":
                d["work"] += 1
                per_machine.setdefault(key, {}).setdefault(rn, 0)
                per_machine[key][rn] += 1
            elif st in ("item_ingredient_shortage", "fluid_ingredient_shortage", "no_ingredients"):
                d["blocked"] += 1
            elif st == "full_output":
                d["full"] += 1
            else:
                d["idle"] += 1
        prev = cur
    total_work = sum(d["work"] for d in stat.values()) or 1
    secs = polls * INTERVAL
    print(f"Replicator sample: {polls} polls over {secs:.0f} s, {len(prev)} machines")
    rows = sorted(stat.items(), key=lambda kv: -kv[1]["work"])
    print(f"{'recipe':34s} {'share':>6s} {'crafts':>7s} {'work':>5s} {'blocked':>8s} {'full':>5s}  verdict")
    for rn, d in rows:
        share = d["work"] / total_work
        # how much of one unit's time: work polls per machine-poll, taken as polls on this recipe over the sample's polls
        unit_load = d["work"] / polls if polls else 0
        hot = share >= 0.4 or unit_load >= 0.6
        print(f"{rn:34s} {share * 100:5.0f}% {d['crafts']:7d} {d['work']:5d} {d['blocked']:8d} {d['full']:5d}  {'HOT: static machines' if hot and d['work'] else ''}")
    busy = sum(d["work"] for d in stat.values()) / (polls * max(1, len(prev))) if polls else 0
    print(f"average share of machine-time spent working: {busy * 100:.0f}% (low and mostly blocked = the Replicator waits on stock, not on units)")


if __name__ == "__main__":
    main()
