#!/usr/bin/env python3
"""Edgerunner POWER (the Captain, 2026-11-18: "Yes, build both": the rocket works and more power).

MEASURED before (meter pole at 16,16; a platform's network statistics are only readable through a pole): 144 legendary panels, 150 kW each
at 100% sun = 21.6 MW; no accumulators; draw 7.5 MW docked, 11.0 MW flying. Sun in orbit: Nauvis 300%, Vulcanus 600%, Gleba 200%,
Fulgora 120%, Aquilo 60%. At Aquilo the old field gave 13 MW against 11 MW, before the rocket works (about 5 MW bare, up to 15 MW with modules).

BUILT: a second field WEST of the cargo-bay chain, on new deck that touches the bays (deck carries the power, no poles):
  panels        20 x 15 = 300 legendary panels, x -74..-15, rows 48..92  (+45 MW at 100% sun; the ship then has 444 panels, 66.6 MW)
  accumulators  30 x 4 = 120 legendary accumulators, x -74..-15, rows 93..100
At Aquilo's 60% that is 40 MW against a worst case of about 26 MW. Past Aquilo the sun falls to 1%: that leg needs fusion, as planned.

Steps: plan | deck | build [--apply] | status | meter [SECONDS]
Usage: edge_power.py plan ; edge_power.py deck ; edge_power.py build --apply ; edge_power.py meter 20"""
import json
import sys
import time

import triangle_miner as TM
from _game import tools

L = tools["run_lua"]
Q = {"quality": "legendary"}
X0, Y0, COLS, ROWS = -74, 48, 20, 15
AY0, ACOLS, AROWS = 93, 30, 4


def layout():
    e = [TM.E("solar-panel", X0 + 3 * i + 1.5, Y0 + 3 * j + 1.5, 0, **Q) for i in range(COLS) for j in range(ROWS)]
    e += [TM.E("accumulator", X0 + 2 * i + 1.0, AY0 + 2 * j + 1.0, 0, **Q) for i in range(ACOLS) for j in range(AROWS)]
    return e


def tiles():
    return {(x, y) for x in range(X0, X0 + 3 * COLS) for y in range(Y0, AY0 + 2 * AROWS)}


def cells(ts):
    return "{" + ",".join("{%d,%d}" % c for c in sorted(ts)) + "}"


def missing():
    return json.loads(L(TM.AT + "local need,gh,blk=0,0,0 for _,q in pairs(" + cells(tiles()) + ") do if s.get_tile(q[1],q[2]).name~='space-platform-foundation' then need=need+1 "
                        "if s.count_entities_filtered{type='tile-ghost',position={q[1]+0.5,q[2]+0.5},radius=0.3}>0 then gh=gh+1 end end end "
                        "blk=s.count_entities_filtered{area={{%d,%d},{%d,%d}},type={'solar-panel','accumulator','tile-ghost'},invert=true} "
                        "rcon.print(helpers.table_to_json({need=need,ghost=gh,other_entities=blk,stock=p.hub.get_inventory(defines.inventory.hub_main).get_item_count('space-platform-foundation')}))" % (X0, Y0, X0 + 3 * COLS, AY0 + 2 * AROWS)))


STATUS = (TM.AT + "local h={} for _,e in pairs(s.find_entities_filtered{name={'solar-panel','accumulator'}}) do local k=e.name..' '..e.quality.name h[k]=(h[k] or 0)+1 end local t={} for k,v in pairs(h) do t[#t+1]=k..' x'..v end table.sort(t) "
          "local ch,cap=0,0 for _,a in pairs(s.find_entities_filtered{name='accumulator'}) do ch=ch+a.energy cap=cap+a.electric_buffer_size end "
          "local np=0 for _,e in pairs(s.find_entities_filtered{type={'assembling-machine','furnace','inserter','asteroid-collector'}}) do if e.status==defines.entity_status.no_power or e.status==defines.entity_status.low_power then np=np+1 end end "
          "rcon.print(table.concat(t,', ')..' | accumulators hold '..string.format('%.0f of %.0f MJ',ch/1e6,cap/1e6)..' | machines short of power '..np..' | at '..(p.space_location and p.space_location.name or 'flying')..' | tile ghosts '..s.count_entities_filtered{type='tile-ghost'})")
METER = (TM.AT + "local e=s.find_entities_filtered{type='electric-pole',limit=1}[1] local st=e.electric_network_statistics local i,u=0,0 for _,v in pairs(st.input_counts) do i=i+v end for _,v in pairs(st.output_counts) do u=u+v end "
         "local ch=0 for _,a in pairs(s.find_entities_filtered{name='accumulator'}) do ch=ch+a.energy end "
         "rcon.print(helpers.table_to_json({tick=game.tick,used=i,made=u,acc=ch,speed=p.speed*60,at=p.space_location and p.space_location.name or 'flying'}))")


def meter(seconds):
    a = json.loads(L(METER))
    time.sleep(seconds)
    b = json.loads(L(METER))
    dt = (b["tick"] - a["tick"]) / 60.0
    if dt <= 0:
        sys.exit("the game did not advance")
    print("%s, %.0f km/s, over %.0f game s: drawn %.1f MW, produced %.1f MW, accumulators %.0f -> %.0f MJ" % (
        b["at"], b["speed"], dt, (b["used"] - a["used"]) / dt / 1e6, (b["made"] - a["made"]) / dt / 1e6, a["acc"] / 1e6, b["acc"] / 1e6))


def main():
    a = sys.argv[1:]
    step = a[0] if a else "status"
    if step == "plan":
        ents = layout()
        print(len(ents), "entities,", len(tiles()), "tiles:", missing())
    elif step == "deck":
        n = 0
        ts = sorted(tiles())
        for i in range(0, len(ts), 1500):
            n += int(L(TM.AT + "local n=0 for _,q in pairs(" + cells(ts[i:i + 1500]) + ") do if s.get_tile(q[1],q[2]).name~='space-platform-foundation' and s.count_entities_filtered{type='tile-ghost',position={q[1]+0.5,q[2]+0.5},radius=0.3}==0 then "
                       "if s.create_entity{name='tile-ghost',inner_name='space-platform-foundation',position={q[1],q[2]},force='player'} then n=n+1 end end end rcon.print(n)").strip())
        print("tile ghosts laid", n)
    elif step == "build":
        apply = "--apply" in a
        have = json.loads(L(TM.AT + "local t={} for _,e in pairs(s.find_entities_filtered{name={'solar-panel','accumulator'},area={{%d,%d},{%d,%d}}}) do t[#t+1]=e.position.x..','..e.position.y end rcon.print(helpers.table_to_json(t))" % (X0, Y0, X0 + 3 * COLS, AY0 + 2 * AROWS))) or []
        have = set(have)
        ready = json.loads(L(TM.AT + "local t={} for _,q in pairs(" + cells(tiles()) + ") do if s.get_tile(q[1],q[2]).name=='space-platform-foundation' then t[#t+1]=q[1]..','..q[2] end end rcon.print(helpers.table_to_json(t))")) or []
        ready = {tuple(int(v) for v in r.split(",")) for r in ready}
        todo = []
        for e in layout():
            key = "%s,%s" % (("%.1f" % e["x"]).rstrip("0").rstrip("."), ("%.1f" % e["y"]).rstrip("0").rstrip("."))
            if key in have:
                continue
            w = 3 if e["name"] == "solar-panel" else 2
            x0, y0 = round(e["x"] - w / 2), round(e["y"] - w / 2)
            if all((x0 + i, y0 + j) in ready for i in range(w) for j in range(w)):
                todo.append(e)
        ok, bad = TM.place(todo, apply)
        print("standing", len(have), "| deck ready for", len(todo), "more |", "placed" if apply else "dry run:", ok, "failed", bad)
        print(L(STATUS))
    elif step == "status":
        print(L(STATUS))
    elif step == "meter":
        meter(int(a[1]) if len(a) > 1 else 20)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
