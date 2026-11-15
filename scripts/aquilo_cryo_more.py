#!/usr/bin/env python3
"""Aquilo: two more cryogenic science stacks (the Captain, 2026-11-14: "more science on Aquilo!!").

Usage:  aquilo_cryo_more.py plan | build [--apply] | config | gate | modules [--apply] | measure [game_min] | status

Why here and why so: the first line (science (-24.5,-38.5) on its cooler (-24.5,-33.5), fluoroketone plant (-32.5,-39.5)) is wrapped in
heat pipes on every side, and Aquilo has no other free fluorine or ammonia tap. So the new stacks SHARE the first line's hot
fluoroketone network: one heat pipe (-27,-43) above the science plant's hot output pipe (-27,-42) becomes a pipe (the heat row stays
joined through the new heat column x=-28 and row y=-49), a riser x=-27 goes up to y=-48 and a bus runs east along y=-48 into the paved
platform field. Make-up hot fluoroketone still comes only from the first fluoroketone plant; its gate keeps the same idea (make hot only
when the coolers are short of cold, so the hot pipes never fill: the deadlock in aquilo_cryo_scale.py) but now reads all three coolers
(see gate()).
Warm-up: the 72 new heat pipes soak ~71 GJ; with the north-west tower gated off (fuel < 2,500) solid fuel fell ~95/min, so 5 uranium
fuel cells were moved from the Aquilo pad into the idle reactor (17.5,-16.5) for the warm-up (one-off, 8 GJ each).
Robots: with the fluids right, ICE delivery was the limit (all requester chests at 0 ice, 40/40 logistic robots busy). Nearly all of
Aquilo's ice sits in ONE chest, the fuel works' (25.5,-3.5), ~60 tiles from the science field; when robots cannot empty it, the
separation plant stops and solid fuel with it. 250 logistic robots (factory-made, normal) were moved from the Nauvis network (137) into
Aquilo roboports (40 -> 290): fuel went from -82/min to +69/min and packs up.

Layout (tiles), rows: top pipe row y=-48 (heat row y=-49 above it), plants -47..-38, bottom pipe row -37 (heat rows -37 / -36 below):
  stack 1 (mirrored, both S facing): cooler x -16..-12 y -47..-43 on top, science x -16..-12 y -42..-38; ports on the right column x=-12:
     cooler in (-12,-48), cooler out = science in (direct), science out (-12,-37). Inserters x=-17 (ice+lithium plate in at y=-41,
     packs out at y=-39), chests x=-18.
  hot column 1 x=-11, heat column x=-10, hot column 2 x=-9 (the two hot columns join at the bottom row -12..-8, y=-37).
  stack 2 (normal, both N facing): science x -8..-4 y -47..-43 on top, cooler x -8..-4 y -42..-38; ports on the left column x=-8:
     science out (-8,-48), cooler in (-8,-37). Inserters x=-3 (in y=-47, out y=-46), chests x=-2.
  The bus passes over cooler 1's unused top ports underground (pipe-to-ground -16 -> -13).
Each science plant gets 8 speed-module-3 (normal, moved from the Nauvis mall chests as aquilo_cryo_scale.py does): 57 packs a minute each,
so three stacks = 171 a minute = 3x. Coolers stay unmoduled (456 cold a minute against 342 used).
Paving: every meltable tile under the build is laid with concrete TAKEN from the Aquilo network (one concrete per tile).
"""
import json
import sys

from _game import tools
import aquilo_cryo as AC
from aquilo_cryo_scale import move_modules

N, E, S, W = 0, 4, 8, 12
L = tools["run_lua"]
BOX = (-40, -52, 4, -33)
SWAP = (-27, -43)                    # heat pipe -> pipe (the tap into the first line's hot network)
SCI1, COOL1 = (-13.5, -39.5), (-13.5, -44.5)
SCI2, COOL2 = (-5.5, -44.5), (-5.5, -39.5)
CHESTS = {"in1": (-17.5, -40.5), "out1": (-17.5, -38.5), "in2": (-1.5, -46.5), "out2": (-1.5, -45.5)}


def plan():
    P = AC.Plan()
    for y in range(-48, -42):
        P.pipe(-27, y)                                            # riser from the tap (-27,-43) to the bus
    for x in range(-26, -16):
        P.pipe(x, -48)                                            # bus
    P.add("pipe-to-ground", -16, -48, d=W)                        # over cooler 1's unused top ports
    P.add("pipe-to-ground", -13, -48, d=E)
    for x in (-12, -11, -9, -8):
        P.pipe(x, -48)
    for y in range(-47, -37):
        P.pipe(-11, y)                                            # hot column 1
        P.pipe(-9, y)                                             # hot column 2
    for x in range(-12, -7):
        P.pipe(x, -37)                                            # bottom row: science 1 out, the joint, cooler 2 in
    P.add("cryogenic-plant", -16, -47, 5, 5, S, recipe="fluoroketone-cooling")
    P.add("cryogenic-plant", -16, -42, 5, 5, S, recipe="cryogenic-science-pack")
    P.add("cryogenic-plant", -8, -47, 5, 5, N, recipe="cryogenic-science-pack")
    P.add("cryogenic-plant", -8, -42, 5, 5, N, recipe="fluoroketone-cooling")
    P.add("fast-inserter", -17, -41, d=W)                         # an inserter's direction is its pickup side
    P.add("requester-chest", -18, -41)
    P.add("fast-inserter", -17, -39, d=E)
    P.add("passive-provider-chest", -18, -39)
    P.add("fast-inserter", -3, -47, d=E)
    P.add("requester-chest", -2, -47)
    P.add("fast-inserter", -3, -46, d=W)
    P.add("passive-provider-chest", -2, -46)
    P.nohalo = P.occupied()                                       # no halos: every heat pipe below is chosen (each one soaks ~1 GJ)
    extra = [(-28, y) for y in range(-48, -43)]                   # riser heat, joins the standing row at (-28,-43)
    extra += [(x, -49) for x in range(-28, -2)]                   # heat row over the bus and both stack tops
    extra += [(-15, -48), (-14, -48)]                             # over the underground: heats cooler 1
    extra += [(-10, y) for y in range(-48, -37)]                  # heat column between the hot columns
    extra += [(x, -37) for x in range(-19, -12)]                  # joins (-20,-37): heats science 1's out pipe
    extra += [(x, -36) for x in range(-11, -3)] + [(-4, -35)]     # joins (-3,-35): heats the bottom row and cooler 2
    extra += [(-7, -37)]
    extra += [(-19, -40), (-18, -40), (-17, -40)]                 # inserters of stack 1, joins (-20,-40)
    extra += [(-3, -48), (-3, -45)]                               # inserters of stack 2 (heat_plan joins (-3,-45))
    return P, extra


def grid_net():
    grid = AC.fetch(BOX)
    net = AC.heat_tiles(BOX)
    if SWAP in net:
        net.discard(SWAP)
        grid[SWAP] = "C"
    return grid, net


def show():
    P, extra = plan()
    grid, net = grid_net()
    H, cold = AC.heat_plan(P, grid, net, extra)
    occ = P.occupied() | H
    bad = sorted(t for t in occ if grid.get(t) not in AC.USABLE)
    pave = sorted(t for t in occ if grid.get(t) in ("i", "P", "~"))
    print("entities %d, heat pipes %d (~%.0f GJ to warm), unheated %s, tiles to pave %d, unusable %s" % (len(P.ents), len(H), len(H) * 0.985, cold, len(pave), bad[:20]))
    x0, y0, x1, y1 = -30, -51, 1, -34
    pipes = {t for e in P.ents if e["name"] in ("pipe", "pipe-to-ground") for t in e["tiles"]}
    for y in range(y0, y1 + 1):
        row = ""
        for x in range(x0, x1 + 1):
            t = (x, y)
            c = grid.get(t, "?")
            if t in pipes:
                c = "|"
            elif t in H:
                c = "h"
            elif any(t in e["tiles"] for e in P.ents):
                c = "@"
            elif t in net:
                c = "7"
            row += c
        print("%4d %s" % (y, row))
    return P, H, cold, pave, grid


def build(apply):
    P, H, cold, pave, grid = show()
    if cold:
        print("refusing: unheated entities", cold)
        return
    for x, y in sorted(H):
        P.add("heat-pipe", x, y)
    out = [{k: v for k, v in e.items() if k != "tiles"} for e in P.ents]
    part = ",".join("{'%s',%s,%s}" % (e["name"], e["x"], e["y"]) for e in out)
    have = L("local s=game.surfaces.aquilo local t={} for i,q in pairs({%s}) do t[i]=#s.find_entities_filtered{name=q[1],position={q[2],q[3]},radius=0.3} end rcon.print(table.concat(t,','))" % part).strip().split(",")
    out = [e for e, h in zip(out, have) if h == "0"]
    print("new pieces:", len(out))
    if not apply:
        r = json.loads(tools["place_entities"](json.dumps(out), surface="aquilo", dry_run=True))
        pv = set(pave)
        fails = [f for f in (r.get("failed") or []) if (int(f["x"] // 1), int(f["y"] // 1)) not in pv]
        print("dry run placed", r.get("placed"), "failed (not counting tiles still to pave)", json.dumps(fails)[:1500])
        return
    tools["save_game"]("skippy")
    # 1) pave, paying one concrete from the Aquilo network for each tile
    if pave:
        r = L("local s=game.surfaces.aquilo local net=s.find_logistic_network_by_position({4,-11},game.forces.player) local need=%d local got=net.remove_item({name='concrete',count=need,quality='normal'}) "
              "if got<need then net.insert({name='concrete',count=got,quality='normal'}) rcon.print('short '..got) else local t={} for _,p in pairs({%s}) do t[#t+1]={name='concrete',position=p} end s.set_tiles(t) rcon.print('paved '..#t..' with '..got..' concrete from the network') end"
              % (len(pave), ",".join("{%d,%d}" % t for t in pave)))
        print(r)
        if not r.startswith("paved"):
            return
    # 2) the tap: the one heat pipe that becomes a pipe (its neighbours keep the heat row joined)
    print(L("local s=game.surfaces.aquilo local h=s.find_entities_filtered{name='heat-pipe',position={%s,%s},radius=0.3}[1] if h then h.destroy{raise_destroy=true} rcon.print('tap heat pipe removed') else rcon.print('tap: no heat pipe (done before)') end" % (SWAP[0] + .5, SWAP[1] + .5)))
    order = {"heat-pipe": 0}
    out.sort(key=lambda e: order.get(e["name"], 1))
    placed, failed = 0, []
    for i in range(0, len(out), 150):
        r = json.loads(tools["place_entities"](json.dumps(out[i:i + 150]), surface="aquilo", dry_run=False, clear_trees=False))
        placed += r.get("placed") or 0
        failed += r.get("failed") or []
    print("placed", placed, "failed", json.dumps(failed)[:1500])
    print(L("game.forces.player.chart(game.surfaces.aquilo,{{-45,-60},{10,-25}}) rcon.print('charted')"))
    config()
    gate()


def config():
    """Recipes, facing, chest requests. Re-run it if a plant reads the wrong facing: cooler 1 was found facing north again some minutes
    after it had been turned south (cause unknown); facing north its unused top-right output box dumped COLD fluoroketone into the hot
    bus and the whole hot network had to be flushed (clear_fluid_inside on the cold-filled pipes)."""
    code = "local s=game.surfaces.aquilo local o={} "
    for pos, rec, d in ((SCI1, "cryogenic-science-pack", "south"), (COOL1, "fluoroketone-cooling", "south"),
                        (SCI2, "cryogenic-science-pack", "north"), (COOL2, "fluoroketone-cooling", "north")):
        code += ("do local e=s.find_entities_filtered{name='cryogenic-plant',position={%s,%s},radius=0.6}[1] if e then if not e.get_recipe() then e.set_recipe('%s') end "
                 "e.direction=defines.direction.%s o[#o+1]=e.get_recipe().name..' '..e.position.x..','..e.position.y..' faces '..e.direction end end " % (pos + (rec, d)))
    code += AC.ask(CHESTS["in1"][0], CHESTS["in1"][1], {"ice": 100, "lithium-plate": 40})
    code += AC.ask(CHESTS["in2"][0], CHESTS["in2"][1], {"ice": 100, "lithium-plate": 40})
    code += "rcon.print(table.concat(o,' | '))"
    print(L(code))


def roboports(apply):
    """Charging: with 290 logistic robots every roboport had 4 charging and 18..37 waiting (211 of 291 robots low on energy) and packs
    FELL to 85/min. Three more epic roboports on the ice route add charging slots: two on the free snow at x 21..24 (half way between
    the fuel works' ice chest and the science field) and one at x 2..5 by the science field, each with a substation."""
    P = AC.Plan()
    P.add("roboport", 21, -29, 4, 4)
    P.add("roboport", 21, -35, 4, 4)
    P.add("substation", 25, -31, 2, 2)
    P.add("roboport", 2, -39, 4, 4)
    P.add("substation", 6, -38, 2, 2)
    P.nohalo = P.occupied()
    extra = [(20, -34), (3, -35)]                 # the first roboport touches the standing heat column x=20 already
    box = (-2, -42, 30, -22)
    grid = AC.fetch(box)
    net = AC.heat_tiles(box)
    H, cold = AC.heat_plan(P, grid, net, extra)
    pave = [t for t in (P.occupied() | H) if grid.get(t) in ("i", "P", "~")]
    print("heat pipes", len(H), "unheated", cold, "tiles to pave", len(pave))
    if cold:
        return
    if apply and pave:
        r = L("local net=game.surfaces.aquilo.find_logistic_network_by_position({4,-11},game.forces.player) rcon.print(net.remove_item({name='concrete',count=%d,quality='normal'}))" % len(pave))
        print("concrete taken from the network for paving:", r)
    AC.build(P, grid, net, apply, extra)


def gate():
    """The first gate (cooler 0 cold < 120) proved too weak once shared: cooler 0 sits next to the fluoroketone plant and takes the hot
    first, so it stayed near 120 while the far cooler 2 starved (cold 60, hot 3..13; packs 111/min). All three coolers now read their
    contents onto the gate's red wire (through the substations (-12,-35) and (-33,-46), which carry nothing else on red).
    A sum of COLD < 420 was tried first and failed: one starving cooler kept the sum low while the hot pipes filled, and the loop
    deadlocked (packs 7.6/min). The gate is on HOT instead: make-up runs while the coolers' hot input boxes together hold < 60, i.e. only
    when the hot network is nearly empty, so it can never fill the pipes (which is what blocks the science plants' hot output)."""
    print(L("local s=game.surfaces.aquilo local W=defines.wire_connector_id.circuit_red local function g(n,x,y,r) return s.find_entities_filtered{name=n,position={x,y},radius=r or 0.6}[1] end "
            "local c1=g('cryogenic-plant',%s,%s) local c2=g('cryogenic-plant',%s,%s) local s1=g('substation',-12,-35,1) local s2=g('substation',-33,-46,1) local ins=g('fast-inserter',-32.5,-36.5,0.4) "
            "local o={} local function w(a,b,tag) o[#o+1]=tag..'='..tostring(a.get_wire_connector(W,true).connect_to(b.get_wire_connector(W,true),true)) end "
            "w(c2,s1,'c2-s1') w(c1,s1,'c1-s1') w(s1,s2,'s1-s2') w(s2,ins,'s2-ins') for _,c in pairs({c1,c2}) do c.get_or_create_control_behavior().circuit_read_contents=true end "
            "local cb=ins.get_control_behavior() cb.circuit_enable_disable=true cb.circuit_condition={first_signal={type='fluid',name='fluoroketone-hot'},comparator='<',constant=60} "
            "o[#o+1]='gate sum hot<60 now '..tostring(cb.circuit_condition.fulfilled)..' '..serpent.line(ins.get_signals(W)) rcon.print(table.concat(o,' '))" % (COOL1 + COOL2)))


def modules(apply):
    for pos in (SCI1, SCI2):
        move_modules(pos, "speed-module-3", 8, apply)


def status():
    st = ("local s=game.surfaces.aquilo local st={} for k,v in pairs(defines.entity_status) do st[v]=k end local o={} "
          "for _,e in pairs(s.find_entities_filtered{area={{-30,-50},{0,-34}},type={'assembling-machine','inserter','pipe','pipe-to-ground'}}) do "
          "local bad=e.frozen or (e.status and (st[e.status]=='no_power' or st[e.status]=='frozen')) "
          "if e.type=='assembling-machine' or bad then local fl='' for i=1,e.fluids_count do local f=e.get_fluid(i) if f then fl=fl..f.name..'='..math.floor(f.amount)..' ' end end "
          "local am=e.type=='assembling-machine' local r=am and e.get_recipe() "
          "o[#o+1]=e.name..'@'..e.position.x..','..e.position.y..' '..(r and r.name or '')..' '..(st[e.status] or tostring(e.status))..(e.frozen and ' FROZEN' or '')..' made '..(am and e.products_finished or 0)..' '..fl end end "
          "rcon.print(table.concat(o,'\\n'))")
    print(L(st))


MEASURE = ("local s=game.surfaces.aquilo local n=0 for _,p in pairs({{-24.5,-38.5},{%s,%s},{%s,%s}}) do local e=s.find_entities_filtered{name='cryogenic-plant',position=p,radius=0.6}[1] n=n+e.products_finished end "
           "local f=game.forces.player local ps=f.get_item_production_statistics(s) local net=s.find_logistic_network_by_position({4,-11},f) local w=0 for _,g in pairs(s.find_entities_filtered{type='generator'}) do w=w+g.energy_generated_last_tick*60 end "
           "local t=s.find_entities_filtered{name='heat-pipe',position={-9.5,-48.5},radius=0.3}[1] local t2=s.find_entities_filtered{name='heat-pipe',position={-29.5,-42.5},radius=0.3}[1] "
           "rcon.print(game.tick..' '..n..' '..ps.get_output_count('lithium-plate')..' '..ps.get_output_count('ice')..' '..ps.get_input_count('solid-fuel')..' '..ps.get_output_count('solid-fuel')..' '..net.get_item_count('lithium-plate')..' '..net.get_item_count('solid-fuel')..' '..net.get_item_count('ice')..' '..math.floor(w/1e5)/10 ..' '..math.floor(t.temperature)..' '..math.floor(t2.temperature))") % (SCI1 + SCI2)


def measure(minutes):
    """Packs a game minute from all three science plants (products_finished), with lithium plate / ice use, fuel, power and heat."""
    import time
    a = [float(v) for v in L(MEASURE).split()]
    print("start: plates %d fuel %d ice %d power %.1f MW heat new-end %d C first-line %d C" % (a[6], a[7], a[8], a[9], a[10], a[11]))
    while True:
        time.sleep(15)
        b = [float(v) for v in L(MEASURE).split()]
        if b[0] - a[0] >= minutes * 3600:
            break
    m = (b[0] - a[0]) / 3600
    print("%.1f game min: PACKS %.1f/min (%.1fx the 57/min of one plant); lithium plate used %.0f/min, ice used %.0f/min; solid fuel made %.0f used %.0f /min" %
          (m, (b[1] - a[1]) / m, (b[1] - a[1]) / m / 57.0, (b[2] - a[2]) / m, (b[3] - a[3]) / m, (b[4] - a[4]) / m, (b[5] - a[5]) / m))
    print("end: plates %d fuel %d ice %d power %.1f MW heat new-end %d C first-line %d C" % (b[6], b[7], b[8], b[9], b[10], b[11]))


def main():
    a = sys.argv[1:]
    step = a[0] if a else "plan"
    apply = "--apply" in a
    if step == "plan":
        show()
    elif step == "build":
        build(apply)
    elif step == "config":
        config()
    elif step == "modules":
        modules(apply)
    elif step == "status":
        status()
    elif step == "roboports":
        roboports(apply)
    elif step == "gate":
        gate()
    elif step == "measure":
        measure(float([x for x in a[1:] if not x.startswith("--")][0]) if len(a) > 1 else 3.0)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
