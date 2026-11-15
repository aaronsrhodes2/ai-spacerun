#!/usr/bin/env python3
"""Aquilo lithium for the cryogenic science line (the Captain, 2026-11-14: "fix the lithium bottleneck on Aquilo").

Usage:  aquilo_lithium.py status | measure [game_minutes] | plan | build STAGE [--apply]
        STAGES: brine   more pumpjacks on the south-west brine wells (+ speed modules), collector pipe, crossing under the heat row
                furnace speed modules in the plate furnace (headroom to 10x)
Dry run is the default; --apply builds. Every stage skips what stands (idempotent).

THE CHAIN (all numbers read from the prototypes / measured in the game, epic quality)
  pack 1 lithium plate (+3/50 lithium per pack for the fluoroketone synthesis)  <-  electric furnace (-> `furnace`)
  lithium plate <- lithium <- chemical plant `lithium`: 1 holmium plate + 50 lithium brine + 50 ammonia -> 5 lithium, 20 s.
  The plant (-23..-21,-20..-18) runs at speed 4.75 (epic 1.9 + 3 speed-module-3): 14.25 crafts/min = 71 lithium/min = 712 brine/min.
  5x science (56.7 packs/min) = 56.7 plates + 3.4 lithium = 60 lithium = 12 crafts = 600 brine, 600 ammonia, 12 holmium plates a minute.
  10x = 120 lithium = 24 crafts = 1,200 brine (two plants) and 24 holmium a minute.

WHAT WAS THE LIMIT (measured 2026-11-14)
  BRINE.  One well (-52.5,58.5) with 2 speed modules gives 223 brine/min = 4.5 crafts = 22 lithium/min, against a use of 60/min at 5x
  (the net fell ~38/min = 60 - 22).  The plant stood at `fluid_ingredient_shortage` with 26 brine in it (ammonia 200 full, holmium
  400 in its chest, speed 4.75), the 113 pipe tiles of the trunk were EMPTY (0.0 brine each: supply, not pipe capacity), the pumpjack
  `working` with nothing queued behind it.  The furnace (speed 3.8, 71 plates/min) sat at `no_ingredients`; robots, chests,
  inserters idle.  Nothing downstream of the brine was short.
  A well gives 6.75e-4 brine/min per unit of `amount` (x2 with 2 speed-module-3 in the pumpjack).
"""
import json
import sys
import time

from _game import tools
import aquilo_cryo as C
import aquilo_cryo_scale as SC

L = tools["run_lua"]
SURF = "aquilo"
N, E, S, W = 0, 4, 8, 12
BOX = (-62, 40, -30, 80)
SCI, FURN = SC.SCI, (15.5, -11.5)
LITHIUM_PLANT = (-21.5, -18.5)
# Brine wells south of the standing trunk (centre, facing, amount 2026-11-14).  Facing E/W/N/S puts the output tile at
# (cx+2,cy+1) / (cx-2,cy-1) / (cx+1,cy-2) / (cx-1,cy+2): the pumpjack prototype's pipe connection.
WELLS = {"S1": (-52.5, 66.5, E, 262652), "S2": (-52.5, 72.5, E, 213988), "S3": (-46.5, 73.5, W, 290949)}
OUT = {N: (1, -2), E: (2, 1), S: (-1, 2), W: (-2, -1)}
CROSS_X = -51           # the pipe goes under the heat row (y=62) and the trunk (y=61) here; the standing trunk row is y=61, tiles x -54..-39
BRINE_UNIT = 6.75e-4    # brine/min per unit of amount at 1x; 2 speed-module-3 double it


def lua(code):
    return L(code)


def fetch(box):
    """Like aquilo_cryo.fetch but a resource (a brine well) does not make the tile 'occupied'."""
    x0, y0, x1, y1 = box
    code = ("local s=game.surfaces.aquilo local land={['dust-flat']='S',['dust-crests']='S',['dust-lumpy']='S',['dust-patchy']='S',['snow-crests']='S',['snow-flat']='S',['snow-lumpy']='S',['snow-patchy']='S',['frozen-concrete']='C',['concrete']='C',"
            "['refined-concrete']='C',['ice-smooth']='i',['ice-rough']='i',['brash-ice']='~',['ice-platform']='P'} local rows={} for y=%d,%d do local r={} for x=%d,%d do "
            "local c=land[s.get_tile(x,y).name] or '.' for _,e in pairs(s.find_entities_filtered{area={{x+0.05,y+0.05},{x+0.95,y+0.95}}}) do "
            "if e.type~='tile-ghost' and e.type~='resource' and e.type~='logistic-robot' and e.type~='construction-robot' then c='#' break end end r[#r+1]=c end rows[#rows+1]=table.concat(r) end rcon.print(table.concat(rows,'|'))")
    g = {}
    for ya in range(y0, y1 + 1, 40):
        rows = lua(code % (ya, min(y1, ya + 39), x0, x1)).strip().split("|")
        for j, row in enumerate(rows):
            for i, c in enumerate(row):
                g[(x0 + i, ya + j)] = c
    return g


# ------------------------------------------------------------------------------------------------ measuring
def status():
    print(lua("local s=game.surfaces.aquilo local st={} for k,v in pairs(defines.entity_status) do st[v]=k end local o={} "
              "local pl=s.find_entities_filtered{name='chemical-plant',position={%s,%s},radius=1}[1] local fl='' for i=1,pl.fluids_count do local f=pl.get_fluid(i) if f then fl=fl..f.name..'='..math.floor(f.amount)..' ' end end "
              "o[#o+1]='lithium plant '..(st[pl.status] or pl.status)..' speed '..string.format('%%.2f',pl.crafting_speed)..' made '..pl.products_finished..' '..fl "
              "for _,p in pairs(s.find_entities_filtered{name='pumpjack'}) do local r=p.mining_target o[#o+1]='pumpjack '..p.position.x..','..p.position.y..' '..(st[p.status] or p.status)..' well '..(r and r.amount or '-')..' modules '..p.get_module_inventory().get_item_count('speed-module-3') end "
              "local f=s.find_entities_filtered{name='electric-furnace',position={%s,%s},radius=1}[1] o[#o+1]='furnace '..(st[f.status] or f.status)..' speed '..f.crafting_speed..' made '..f.products_finished..' modules '..f.get_module_inventory().get_item_count('speed-module-3') "
              "local n,tot=0,0 for _,e in pairs(s.find_entities_filtered{type={'pipe','pipe-to-ground'},area={{-62,-30},{-20,80}}}) do local fd=e.get_fluid(1) if fd and fd.name=='lithium-brine' then n=n+1 tot=tot+fd.amount end end o[#o+1]='brine pipes '..n..' hold '..math.floor(tot)..' (full would be '..(n*100)..')' "
              "local c=s.find_entities_filtered{name='cryogenic-plant'} for _,e in pairs(c) do local r=e.get_recipe() o[#o+1]='cryo '..e.position.x..','..e.position.y..' '..(r and r.name or '-')..' '..(st[e.status] or e.status)..' made '..e.products_finished end "
              "local net=s.find_logistic_network_by_position({4,-11},game.forces.player) o[#o+1]='network lithium-plate '..net.get_item_count('lithium-plate')..' lithium '..net.get_item_count('lithium')..' holmium '..net.get_item_count('holmium-plate')..' packs '..net.get_item_count('cryogenic-science-pack') "
              "rcon.print(table.concat(o,'|'))" % (LITHIUM_PLANT + FURN)).replace("|", "\n"))


def sample():
    code = ("local s=game.surfaces.aquilo local pl=s.find_entities_filtered{name='chemical-plant',position={%s,%s},radius=1}[1] local f=s.find_entities_filtered{name='electric-furnace',position={%s,%s},radius=1}[1] "
            "local sc=s.find_entities_filtered{name='cryogenic-plant',position={%s,%s},radius=1}[1] local net=s.find_logistic_network_by_position({4,-11},game.forces.player) "
            "local fs=game.forces.player.get_fluid_production_statistics(s) "
            "rcon.print(game.tick..' '..pl.products_finished..' '..f.products_finished..' '..sc.products_finished..' '..net.get_item_count('lithium-plate')..' '..net.get_item_count('holmium-plate')..' '..fs.get_input_count('lithium-brine'))"
            % (LITHIUM_PLANT + FURN + SCI))
    return [float(v) for v in lua(code).split()]


def measure(minutes=3.0):
    a = sample()
    while True:
        time.sleep(15)
        b = sample()
        if b[0] - a[0] >= minutes * 3600:
            break
    m = (b[0] - a[0]) / 3600
    li = (b[1] - a[1]) / m
    print("%.1f game min: lithium plant %.1f crafts/min (= %.0f lithium/min, 5 a craft before productivity); furnace %.1f plates/min; science plant %.1f packs/min (5x = 56.7); brine made %.0f/min" %
          (m, li, li * 5, (b[2] - a[2]) / m, (b[3] - a[3]) / m, (b[6] - a[6]) / m))
    print("network: lithium-plate %d -> %d  holmium-plate %d -> %d" % (a[4], b[4], a[5], b[5]))
    status()


# ------------------------------------------------------------------------------------------------ plan / build
def brine_plan(grid):
    P = C.Plan()
    for k, (cx, cy, d, amt) in WELLS.items():
        P.add("pumpjack", int(cx - 1.5), int(cy - 1.5), 3, 3, d)
    # collector: the column x=CROSS_X from y=66 to the lowest well output; S1 and S2 face east and their output tiles ARE on the column;
    # S3 faces west, its output tile (-49,72) joins the column by one stub pipe
    outs = [(int((cx + OUT[d][0]) // 1), int((cy + OUT[d][1]) // 1)) for (cx, cy, d, amt) in WELLS.values()]
    pipes = {(CROSS_X, y) for y in range(66, max(o[1] for o in outs) + 1)} | set(outs)
    ymax = max(o[1] for o in outs)
    for o in outs:
        if o[0] != CROSS_X:                 # S3: down to the column's last row, then across (keeps every pipe beside a free tile for heat)
            for y in range(o[1], ymax + 1):
                pipes.add((o[0], y))
            for x in range(min(o[0], CROSS_X), max(o[0], CROSS_X) + 1):
                pipes.add((x, ymax))
    for t in sorted(pipes):
        P.pipe(*t)
    # the crossing: pipe-to-ground (surface opening south) at (CROSS_X,65), its partner (opening north) at (CROSS_X,60); underground it
    # passes below the substation (63..64), the heat row (62) and the trunk (61).  Exit: (CROSS_X,59) -> (CROSS_X+1,59) -> (CROSS_X+1,60),
    # which touches the plain trunk pipe at (CROSS_X+1,61).
    P.add("pipe-to-ground", CROSS_X, 65, d=S)
    P.add("pipe-to-ground", CROSS_X, 60, d=N)
    for t in ((CROSS_X, 59), (CROSS_X + 1, 59), (CROSS_X + 1, 60)):
        P.pipe(*t)
    return P


# The heat bridge: the trunk row (y=61) has heat on its south side only, and the strip y=60 between the trunk and the first pumpjack
# can be heated only from (CROSS_X+1.. ,59) above, so the pipe exit has nothing to take heat from.  Three trunk pipes
# (-53,61) (-52,61) (-51,61) become: pipe-to-ground (opening west) | heat pipe | pipe-to-ground (opening east): the trunk dives under
# the heat pipe, which joins the heat row (y=62) to the strip (y=60).  Fluid keeps flowing underground.
BRIDGE = [("pipe-to-ground", -53, 61, W), ("heat-pipe", -52, 61, N), ("pipe-to-ground", -51, 61, E)]


def bridge(apply):
    have = lua("local s=game.surfaces.aquilo rcon.print(#s.find_entities_filtered{name='heat-pipe',position={-51.5,61.5},radius=0.3})")
    if have.strip() == "1":
        print("  bridge already stands")
        return True
    names = lua("local s=game.surfaces.aquilo local o={} for _,x in pairs({-52.5,-51.5,-50.5}) do local e=s.find_entities_filtered{position={x,61.5},radius=0.3}[1] o[#o+1]=e and e.name or '-' end rcon.print(table.concat(o,' '))").split()
    print("  bridge: trunk pieces now at (-53,61),(-52,61),(-51,61):", names, "-> pipe-to-ground | heat pipe | pipe-to-ground")
    if names != ["pipe", "pipe", "pipe"]:
        print("  trunk is not what the bridge expects; not touching it")
        return False
    if not apply:
        return True
    print("  ", lua("local s=game.surfaces.aquilo local n=0 for _,x in pairs({-52.5,-51.5,-50.5}) do local e=s.find_entities_filtered{name='pipe',position={x,61.5},radius=0.3}[1] if e then e.destroy{raise_destroy=true} n=n+1 end end rcon.print('lifted '..n..' trunk pipes')"))
    out = [{"name": n, "x": x + .5, "y": y + .5, "direction": d, "params": dict(C.Q)} for n, x, y, d in BRIDGE]
    r = json.loads(tools["place_entities"](json.dumps(out), surface=SURF, dry_run=False))
    print("  bridge placed", r.get("placed"), "failed", r.get("failed"))
    return not r.get("failed")


def brine(apply):
    grid = fetch(BOX)
    P = brine_plan(grid)
    standing = lua("local s=game.surfaces.aquilo rcon.print(#s.find_entities_filtered{name='heat-pipe',position={-51.5,61.5},radius=0.3})").strip() == "1"
    net = C.heat_tiles(BOX) | {(-52, 61)}
    print("== brine: %d pumpjacks, %d pipes %s" % (len(WELLS), len([e for e in P.ents if e["name"] == "pipe"]), "(APPLY) ==" if apply else "(dry run) =="))
    tot = 0.0
    for k, (cx, cy, d, amt) in WELLS.items():
        tot += amt * BRINE_UNIT * 2
        print("  %s (%s,%s): amount %d -> %.0f brine/min with 2 speed-module-3" % (k, cx, cy, amt, amt * BRINE_UNIT * 2))
    print("  new total %.0f + existing ~220 = %.0f brine/min = %.1f lithium crafts/min (5x needs 12, 10x 24)" % (tot, tot + 220, (tot + 220) / 50))
    if apply:
        tools["save_game"]("skippy")
        if not bridge(True):
            return
    else:
        bridge(False)
    C.build(P, grid, net, apply, clear=False)
    for k, (cx, cy, d, amt) in WELLS.items():
        if apply or lua("local s=game.surfaces.aquilo rcon.print(#s.find_entities_filtered{name='pumpjack',position={%s,%s},radius=1})" % (cx, cy)).strip() == "1":
            SC.move_modules((cx, cy), "speed-module-3", 2, apply, "pumpjack")
        else:
            print("  would move 2 speed-module-3 into the new pumpjack", k)


def furnace(apply):
    print("== furnace modules ==")
    SC.move_modules(FURN, "speed-module-3", 2, apply, "electric-furnace")


def plan():
    print(__doc__)
    brine(False)
    furnace(False)


def main():
    a = sys.argv[1:]
    step = a[0] if a else "status"
    apply = "--apply" in a
    rest = [x for x in a[1:] if not x.startswith("--")]
    if step == "status":
        status()
    elif step == "measure":
        measure(float(rest[0]) if rest else 3.0)
    elif step == "plan":
        plan()
    elif step == "build":
        stage = rest[0] if rest else "brine"
        {"brine": brine, "furnace": furnace}[stage](apply)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
