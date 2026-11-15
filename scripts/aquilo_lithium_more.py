#!/usr/bin/env python3
"""Aquilo: lithium plate supply for the three cryogenic science plants (the Captain, 2026-11-14: "Yes, scale lithium").

Usage:  aquilo_lithium_more.py status | modules [--apply] | plan | build [--apply] | config | measure [game_min]

Numbers (read from the game 2026-11-14): lithium = 1 holmium + 50 brine + 50 ammonia -> 5, 20 s (chemical plant, epic base speed 1.9);
lithium-plate = 1 lithium -> 1, 6.4 s (electric furnace, epic 3.8: with 2 speed-3 that is only 71 a minute); cryogenic pack = 1 plate.
All three recipes take productivity. Brine: 4 pumpjacks ~1,250/min = 25 lithium crafts a minute at most.
Before: one lithium plant (3 speed-3: 14.25 crafts = 71 lithium/min) and one furnace (71 plates/min) against 165 plates/min used.

Step 1, modules (moves only, from / back into Nauvis network 137; nothing spawned):
  lithium plant (-21.5,-18.5)  3 speed-3 -> 3 legendary speed-module-2 (+75% each): 18.5 crafts = 93 lithium/min
  furnace (15.5,-11.5)         2 speed-3 -> 2 legendary speed-module-2: 89 plates/min
  science plants x3            2 of 8 speed-3 -> 2 epic productivity-module-2 (+11.4% each): plates per pack 1/1.228, packs -3%
  coolers x3 + fluoroketone plant: +1 legendary efficiency-module-2 each (empty slots; -100% -> the 20% floor): ~4.8 MW freed
Step 2, build: a second lithium plant on the free snow at x -6..-4, y -20..-18 (3 epic productivity-module-2: 4 crafts, 27 lithium/min,
  +34% per holmium) and two more furnaces; brine from a tap on the trunk at (-24,-12) (the trunk's heat column is bridged round the tap),
  ammonia from a tap on the lithium branch at (-20,-24) (pipe-to-ground under the tower's heat pipe).
  Built with 1 legendary speed-module-2 + 2 epic productivity-module-2 (8.8 crafts, 54 lithium/min); its furnace (-4.5,-14.5) is fed
  straight by an inserter (1 legendary speed-2 + 1 epic prod-2), plates into the provider chest (-4.5,-11.5). 54 heat pipes; their
  warm-up covered by 6 uranium cells moved from the pad into the reactor.
Measured (aquilo_lithium_more.py measure): before 3.1 game min plates MADE 55.8/min USED 155.7/min (stock 265 -> 0);
  after 6.1 game min plates MADE 144.6/min USED 129.6/min, packs 159/min, holmium 27.3/min, power 60 MW with accumulators charging.
Power: right after, robot charging bursts (36 robots charging at once, roboports 39 MW) put 34 machines at low_power. 27 more legendary
  efficiency-module-2 (Nauvis 137) went into every unmoduled machine on Aquilo west of x=38 (6 ice-platform assemblers, separation
  plants, melters, rocket fuel, concrete and cryogenic-plant assemblers, pumpjacks; ~4.7 MW at full load): low_power 0, turbines
  51-57 MW of 60, accumulators full.
"""
import json
import sys

from _game import tools
import aquilo_cryo as AC

L = tools["run_lua"]
SCI = [(-24.5, -38.5), (-13.5, -39.5), (-5.5, -44.5)]
COOL = [(-24.5, -33.5), (-13.5, -44.5), (-5.5, -39.5)]
SYN = (-32.5, -39.5)
LIT = (-21.5, -18.5)
FURN = (15.5, -11.5)
# (name, position, target contents [(module, quality, count)], keep others?)
PLAN = ([("chemical-plant", LIT, [("speed-module-2", "legendary", 3)]),
         ("electric-furnace", FURN, [("speed-module-2", "legendary", 2)])]
        + [("cryogenic-plant", p, [("speed-module-3", "normal", 6), ("productivity-module-2", "epic", 2)]) for p in SCI]
        + [("cryogenic-plant", p, [("efficiency-module-2", "legendary", 1)]) for p in COOL + [SYN]])

SWAP = ("local s=game.surfaces.aquilo local f=game.forces.player local nv for _,nn in pairs(f.logistic_networks.nauvis) do if nn.network_id==137 then nv=nn end end "
        "local e=s.find_entities_filtered{name='%s',position={%s,%s},radius=0.6}[1] local mi=e.get_module_inventory() local want={%s} local apply=%s local o={} "
        "local have={} for _,it in pairs(mi.get_contents()) do have[it.name..'/'..it.quality]=it.count end "
        "local wk={} for _,w in pairs(want) do wk[w[1]..'/'..w[2]]=w[3] end "
        "for k,c in pairs(have) do local extra=c-(wk[k] or 0) if extra>0 then local n,q=k:match('(.+)/(.+)') o[#o+1]='out '..extra..' '..k "
        "if apply then local r=mi.remove{name=n,quality=q,count=extra} local back=nv.insert{name=n,quality=q,count=r} if back<r then mi.insert{name=n,quality=q,count=r-back} o[#o+1]='(no room on Nauvis for '..(r-back)..')' end end end end "
        "for _,w in pairs(want) do local need=w[3]-(have[w[1]..'/'..w[2]] or 0) if need>0 then o[#o+1]='in '..need..' '..w[1]..'/'..w[2]..' (Nauvis has '..nv.get_item_count({name=w[1],quality=w[2]})..')' "
        "if apply then local got=nv.remove_item{name=w[1],quality=w[2],count=need} local put=mi.insert{name=w[1],quality=w[2],count=got} if put<got then nv.insert{name=w[1],quality=w[2],count=got-put} end o[#o+1]='moved '..put end end end "
        "rcon.print(e.name..'@'..e.position.x..','..e.position.y..': '..(#o>0 and table.concat(o,', ') or 'already set')..' -> '..serpent.line(mi.get_contents()))")


def modules(apply):
    for name, pos, want in PLAN:
        w = ",".join("{'%s','%s',%d}" % t for t in want)
        print(L(SWAP % (name, pos[0], pos[1], w, "true" if apply else "false")))


MEASURE = ("local s=game.surfaces.aquilo local f=game.forces.player local ps=f.get_item_production_statistics(s) local net=s.find_logistic_network_by_position({4,-11},f) local w=0 "
           "for _,g in pairs(s.find_entities_filtered{type='generator'}) do w=w+g.energy_generated_last_tick*60 end "
           "rcon.print(game.tick..' '..ps.get_input_count('lithium-plate')..' '..ps.get_output_count('lithium-plate')..' '..ps.get_input_count('lithium')..' '..ps.get_output_count('holmium-plate')..' '..ps.get_input_count('cryogenic-science-pack')..' '"
           "..net.get_item_count('lithium-plate')..' '..net.get_item_count('holmium-plate')..' '..math.floor(w/1e5)/10)")


def measure(minutes):
    import time
    a = [float(v) for v in L(MEASURE).split()]
    while True:
        time.sleep(15)
        b = [float(v) for v in L(MEASURE).split()]
        if b[0] - a[0] >= minutes * 3600:
            break
    m = (b[0] - a[0]) / 3600
    d = [(b[i] - a[i]) / m for i in range(1, 6)]
    print("%.1f game min: lithium plate MADE %.1f/min USED %.1f/min | lithium made %.1f/min | holmium used %.1f/min | packs made %.1f/min | plates in network %d -> %d, holmium %d -> %d | power %.1f MW"
          % (m, d[0], d[1], d[2], d[3], d[4], a[6], b[6], a[7], b[7], b[8]))


N, E, S, W = 0, 4, 8, 12
BOX = (-30, -28, 2, -8)
TAPS = [(-24, -12), (-20, -24)]        # heat pipes that become a pipe (brine tap) and a pipe-to-ground (ammonia tap)
LIT2, FURN2 = (-4.5, -18.5), (-4.5, -14.5)
HOLCHEST, LIOUT = (-1.5, -18.5), (-4.5, -11.5)


def plan():
    P = AC.Plan()
    # brine: tap on the trunk (-25,y) through (-24,-12); the trunk's heat column x=-24 is bridged round it (x=-23/-22, y -13..-11)
    P.pipe(-24, -12)
    P.add("pipe-to-ground", -23, -12, d=W)
    P.add("pipe-to-ground", -21, -12, d=E)
    for x in range(-20, -6):
        P.pipe(x, -12)
    for y in range(-21, -12):
        P.pipe(-7, y)
    P.pipe(-6, -21)                                               # brine port (top left) of the new lithium plant
    # ammonia: tap on the lithium branch (-21,-24): pipe-to-ground under the tower's north heat pipe (-19,-24)
    P.add("pipe-to-ground", -20, -24, d=W)
    P.add("pipe-to-ground", -18, -24, d=E)
    for x in range(-17, -3):
        P.pipe(x, -24)
    for y in (-23, -22, -21):
        P.pipe(-4, y)                                             # ammonia port (top right)
    P.add("chemical-plant", -6, -20, 3, 3, N, recipe="lithium")
    P.add("fast-inserter", -3, -19, d=E)                          # holmium in from the chest east of it
    P.add("requester-chest", -2, -19)
    P.add("fast-inserter", -5, -17, d=N)                          # lithium straight into the furnace below
    P.add("electric-furnace", -6, -16, 3, 3)
    P.add("fast-inserter", -5, -13, d=N)                          # plates out
    P.add("passive-provider-chest", -5, -12)
    P.nohalo = P.occupied()
    extra = [(-23, -13), (-22, -13), (-22, -12), (-22, -11), (-23, -11)]       # heat bridge round the brine tap
    extra += [(x, -13) for x in range(-21, -7)]                   # under/over the brine row
    extra += [(-8, y) for y in range(-20, -13)]                   # beside the brine column
    extra += [(-8, -23), (-7, -23), (-6, -23), (-5, -23), (-7, -22), (-6, -22), (-5, -22), (-5, -21), (-3, -21), (-3, -20)]
    extra += [(-4, -17), (-6, -13), (-7, -11)]
    return P, extra


def grid_net():
    grid = AC.fetch(BOX)
    net = AC.heat_tiles(BOX)
    for t in TAPS:
        net.discard(t)
        grid[t] = "C"
    return grid, net


def show():
    P, extra = plan()
    grid, net = grid_net()
    H, cold = AC.heat_plan(P, grid, net, extra)
    occ = P.occupied() | H
    bad = sorted(t for t in occ if grid.get(t) not in AC.USABLE)
    pave = sorted(t for t in occ if grid.get(t) in ("i", "P", "~"))
    print("entities %d, heat pipes %d, unheated %s, pave %d, unusable %s" % (len(P.ents), len(H), cold, len(pave), bad[:20]))
    pipes = {t for e in P.ents if e["name"] in ("pipe", "pipe-to-ground") for t in e["tiles"]}
    for y in range(BOX[1], BOX[3] + 1):
        row = ""
        for x in range(BOX[0], BOX[2] + 1):
            t = (x, y)
            c = grid.get(t, "?")
            c = "|" if t in pipes else "h" if t in H else "@" if any(t in e["tiles"] for e in P.ents) else "7" if t in net else c
            row += c
        print("%4d %s" % (y, row))
    return P, H, cold, pave


def build(apply):
    P, H, cold, pave = show()
    if cold:
        print("refusing: unheated", cold)
        return
    for x, y in sorted(H):
        P.add("heat-pipe", x, y)
    out = [{k: v for k, v in e.items() if k != "tiles"} for e in P.ents]
    if not apply:
        r = json.loads(tools["place_entities"](json.dumps(out), surface="aquilo", dry_run=True))
        print("dry run placed", r.get("placed"), "failed", json.dumps(r.get("failed") or [])[:1200])
        return
    tools["save_game"]("skippy")
    if pave:
        print(L("local s=game.surfaces.aquilo local net=s.find_logistic_network_by_position({4,-11},game.forces.player) local got=net.remove_item({name='concrete',count=%d,quality='normal'}) local t={} for _,p in pairs({%s}) do t[#t+1]={name='concrete',position=p} end s.set_tiles(t) rcon.print('paved '..#t..' with '..got..' concrete')" % (len(pave), ",".join("{%d,%d}" % t for t in pave))))
    print(L("local s=game.surfaces.aquilo local n=0 for _,p in pairs({%s}) do local h=s.find_entities_filtered{name='heat-pipe',position=p,radius=0.3}[1] if h then h.destroy{raise_destroy=true} n=n+1 end end rcon.print('tap heat pipes removed '..n)" % ",".join("{%s,%s}" % (x + .5, y + .5) for x, y in TAPS)))
    out.sort(key=lambda e: 0 if e["name"] == "heat-pipe" else 1)
    r = json.loads(tools["place_entities"](json.dumps(out), surface="aquilo", dry_run=False, clear_trees=False))
    print("placed", r.get("placed"), "failed", json.dumps(r.get("failed") or [])[:1200])
    config()


def config():
    code = "local s=game.surfaces.aquilo local o={} "
    code += "do local e=s.find_entities_filtered{name='chemical-plant',position={%s,%s},radius=0.6}[1] if not e.get_recipe() then e.set_recipe('lithium') end e.direction=defines.direction.north o[#o+1]='lithium plant 2 faces '..e.direction end " % LIT2
    code += AC.ask(HOLCHEST[0], HOLCHEST[1], {"holmium-plate": 20})
    code += "rcon.print(table.concat(o,' | '))"
    print(L(code))
    for name, pos, want in (("chemical-plant", LIT2, [("speed-module-2", "legendary", 1), ("productivity-module-2", "epic", 2)]),
                            ("electric-furnace", FURN2, [("speed-module-2", "legendary", 1), ("productivity-module-2", "epic", 1)])):
        w = ",".join("{'%s','%s',%d}" % t for t in want)
        print(L(SWAP % (name, pos[0], pos[1], w, "true")))


def main():
    a = sys.argv[1:]
    step = a[0] if a else "status"
    apply = "--apply" in a
    if step == "modules":
        modules(apply)
    elif step == "plan":
        show()
    elif step == "build":
        build(apply)
    elif step == "config":
        config()
    elif step == "measure":
        measure(float(a[1]) if len(a) > 1 else 5.0)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
