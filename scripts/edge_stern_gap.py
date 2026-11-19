#!/usr/bin/env python3
"""Edgerunner STERN GAP (the Captain, 2026-11-18, with the middle of the base edge circled on the map: "this will be a problem at rest as
meteors drift in from behind while waiting at a planet").

WHY THERE WAS A GAP: edge_base.py put turrets "between the collectors", and the middle of the base (x -52..81) had no collectors left: the
four that stood there were removed for the old thruster row, which later moved to the crossbar. No turret of any kind stood there, in front
of the propellant plant, the 128 tanks and the throttle pumps.

BUILT: the base pattern carried across the middle as if collectors still stood every 30 tiles (first tiles -46, -16, 14, 44): gun +6,
rocket turret +11, railgun +17, gun +23, plus one railgun at x 3 for the piece the spoke gap skips. Guns end up at most 17 tiles apart
(range 18). Fed as on the rest of the base: guns and rocket turrets by a long-handed inserter on row 292 from belt A (row 290, over belt B),
railguns by a bulk inserter from belt B (row 291); railguns face SOUTH, where nothing of ours stands.
`gaps` lists every stretch of the frame longer than 30 tiles without a gun turret.

Steps: plan | deck | build [--apply] | gaps
Usage: edge_stern_gap.py plan ; edge_stern_gap.py deck ; edge_stern_gap.py build --apply ; edge_stern_gap.py gaps"""
import json
import sys

import triangle_miner as TM
from _game import tools
from edge_works import T

L = tools["run_lua"]
N, S = 0, 8
ROW_I = 292
COLS = (-46, -16, 14, 44)
EXTRA = [("railgun-turret", 3)]
BELT_X = (3, 72)                    # belts A and B run from |x| 3 to 72 on each side


def layout():
    ents, tiles, ins = [], set(), []
    todo = [(name, c + off) for c in COLS for name, off in (("gun-turret", 6), ("rocket-turret", 11), ("railgun-turret", 17), ("gun-turret", 23))] + EXTRA
    for name, x0 in sorted(todo, key=lambda t: t[1]):
        w = 2 if name == "gun-turret" else 3
        ix = x0 + (0 if w == 2 else 1)
        if not (BELT_X[0] <= abs(ix) <= BELT_X[1]):
            continue                                                  # no belt under the inserter's pick-up tile (the spoke gap)
        if name == "railgun-turret":
            ents += [T("bulk-inserter", ix, ROW_I, N), T(name, x0, 293, S, 3, 4)]
            tiles |= {(x0 + i, 292 + k) for i in range(3) for k in range(6)}
            ins.append((ix, 1))
        else:
            h = w
            ents += [T("long-handed-inserter", ix, ROW_I, N), T(name, x0, 294, 0, w, h)]
            tiles |= {(x0 + i, 294 + k) for i in range(w) for k in range(h)} | {(ix, ROW_I), (ix, 293)}
            ins.append((ix, 0))
    return ents, tiles, ins


def cells(ts):
    return "{" + ",".join("{%d,%d}" % c for c in sorted(ts)) + "}"


CONFIG = (TM.AT + "local rail,ok,bad=0,0,0 for _,q in pairs(INS) do local i=s.find_entities_filtered{type='inserter',position={q[1]+0.5,292.5},radius=0.3}[1] if i then "
          "if q[2]==1 then i.use_filters=true i.inserter_filter_mode='whitelist' i.set_filter(1,{name='railgun-ammo',quality='normal',comparator='='}) rail=rail+1 end "
          "if i.drop_target and i.drop_target.type=='ammo-turret' and i.pickup_target then ok=ok+1 else bad=bad+1 end end end rcon.print('inserters between a belt and a turret '..ok..', not '..bad..', railgun filters set '..rail)")

GAPS = (TM.AT + "local g={} for _,t in pairs(s.find_entities_filtered{name='gun-turret'}) do g[#g+1]={t.position.x,t.position.y} end rcon.print(helpers.table_to_json(g))")
BINS = (TM.AT + "local b={} for _,t in pairs(s.find_entities_filtered{type='ammo-turret',area={{-520,289},{520,300}}}) do local k=math.floor(t.position.x/50)*50 b[k]=b[k] or {0,0,0} local i=(t.name=='gun-turret' and 1) or (t.name=='rocket-turret' and 2) or 3 b[k][i]=b[k][i]+1 end "
        "local ks={} for k in pairs(b) do ks[#ks+1]=k end table.sort(ks) local o={} for _,k in pairs(ks) do o[#o+1]=k..':'..b[k][1]..'/'..b[k][2]..'/'..b[k][3] end rcon.print('base edge, 50-tile bins from x (guns/rocket turrets/railguns): '..table.concat(o,'  '))")


def gaps():
    guns = json.loads(L(GAPS))
    base = sorted(x for x, y in guns if y > 285)
    out = []
    for a, b in zip(base, base[1:]):
        if b - a > 30:
            out.append("base x %.0f .. %.0f (%.0f tiles)" % (a, b, b - a))
    for side, name in ((-1, "west flank"), (1, "east flank")):
        ys = sorted(y for x, y in guns if y <= 285 and x * side > 0)
        ys = [-577.0] + ys + [289.0]                                   # the nose and the base corner bound the side
        for a, b in zip(ys, ys[1:]):
            if (b - a) * 1.155 > 30:                                   # a row down the flank is 1.155 tiles along it
                out.append("%s rows %.0f .. %.0f (%.0f tiles along the flank)" % (name, a, b, (b - a) * 1.155))
    print("gun turrets %d; stretches longer than 30 tiles without one: %s" % (len(guns), "; ".join(out) if out else "none"))
    print(L(BINS))


def main():
    a = sys.argv[1:]
    step = a[0] if a else "plan"
    ents, tiles, ins = layout()
    if step == "plan":
        kinds = {}
        for e in ents:
            kinds[e["name"]] = kinds.get(e["name"], 0) + 1
        print(kinds, "| tiles", len(tiles), "|", L(TM.AT + "local need,blk=0,{} for _,q in pairs(" + cells(tiles) + ") do if s.get_tile(q[1],q[2]).name~='space-platform-foundation' then need=need+1 end "
              "for _,e in pairs(s.find_entities_filtered{area={{q[1]+0.1,q[2]+0.1},{q[1]+0.9,q[2]+0.9}}}) do if e.type~='tile-ghost' then blk[e.name..'@'..e.position.x..','..e.position.y]=true end end end "
              "local t={} for k in pairs(blk) do t[#t+1]=k end rcon.print('deck missing '..need..', in the way: '..(#t>0 and table.concat(t,' ') or 'nothing')..', hub foundations '..p.hub.get_inventory(defines.inventory.hub_main).get_item_count('space-platform-foundation'))").strip())
        print("guns at x:", sorted(round(e["x"] - 1) for e in ents if e["name"] == "gun-turret"))
    elif step == "deck":
        print(L(TM.AT + "local n=0 for _,q in pairs(" + cells(tiles) + ") do if s.get_tile(q[1],q[2]).name~='space-platform-foundation' and s.count_entities_filtered{type='tile-ghost',position={q[1]+0.5,q[2]+0.5},radius=0.3}==0 then "
                "if s.create_entity{name='tile-ghost',inner_name='space-platform-foundation',position={q[1],q[2]},force='player'} then n=n+1 end end end rcon.print('tile ghosts laid '..n)").strip())
    elif step == "build":
        apply = "--apply" in a
        ready = set(json.loads(L(TM.AT + "local t={} for _,q in pairs(" + cells(tiles) + ") do if s.get_tile(q[1],q[2]).name=='space-platform-foundation' then t[#t+1]=q[1]..','..q[2] end end rcon.print(helpers.table_to_json(t))")) or [])
        have = set(json.loads(L(TM.AT + "local t={} for _,e in pairs(s.find_entities_filtered{type={'ammo-turret','inserter'},area={{-60,292},{75,298}}}) do t[#t+1]=e.name..'@'..e.position.x..','..e.position.y end rcon.print(helpers.table_to_json(t))")) or [])
        todo = []
        for i in range(0, len(ents), 2):
            inserter, turret = ents[i], ents[i + 1]
            w, h = (2, 2) if turret["name"] == "gun-turret" else ((3, 3) if turret["name"] == "rocket-turret" else (3, 5))
            x0, y0 = round(turret["x"] - w / 2), (294 if turret["name"] != "railgun-turret" else 293)
            if "%s@%s,%s" % (turret["name"], ("%.1f" % turret["x"]).rstrip("0").rstrip("."), ("%.1f" % turret["y"]).rstrip("0").rstrip(".")) in have:
                continue
            if all("%d,%d" % (x0 + a2, y0 + b2) in ready for a2 in range(w) for b2 in range(h)):
                todo += [inserter, turret]
        ok, bad = TM.place(todo, apply)
        print("placed" if apply else "dry run: would place", ok, "of", len(todo), "(whole plan %d)" % len(ents), "failed", bad)
        if apply:
            print(L(CONFIG.replace("INS", "{" + ",".join("{%d,%d}" % q for q in ins) + "}")))
            import edge_flight
            print(L(edge_flight.TARGETS))
    elif step == "gaps":
        gaps()
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
