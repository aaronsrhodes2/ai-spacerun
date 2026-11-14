#!/usr/bin/env python3
"""The outer relay ship, Fulgora <-> Aquilo, a new design from scratch (the Captain, 2026-11-13: "Aquila shuttle", "it's a pretty ugly
shuttle", "the shuttles could likely operate on 1 or 2 grabbers"). North is the nose. The hub covers tiles -4..3.
Why it differs from the inner shuttles: the Fulgora-Aquilo run has big asteroids (2,000 hp, bullets do nothing), so it makes rockets on
board; Aquilo's orbit has 60% sun, so it has 36 panels on two wings; and it is built round its cargo: seven bays in a spine to the nose.
  hub edge   every machine that handles solids stands against the hub and trades with it by inserter, as on the inner shuttles
             north  chunks in, surplus valve (drops through a hole in the deck), first cargo bay, magazines out
             west   oxidizer plant, metallic crusher, furnace, ice melter
             east   fuel plant, carbonic crusher (advanced: carbon + sulfur), magazine assembler, rocket assembler
             south  oxide crusher, coal plant, explosives plant (hands explosives to the rocket assembler round the corner)
  chunks     two collectors on the nose corners; their belts dive under the ammunition belt, meet on row -18 and run down column -7
  ammunition one belt, a lane each: rockets leave the rocket assembler through an underground that starts the belt (right lane), it
             runs up the east flank, across the nose and down the west flank; magazines join from the west side at row -8 (left lane).
             Turrets stand outside it: six rocket turrets, eight gun turrets. Below row -8 on the east flank there are only rockets.
  fluids     water: row 8 and two risers (columns -12 and 10); oxidizer down column -10, fuel down column 8, both to three tanks each
             and the old rear block (headers on rows 17 and 19, four thrusters)
  circuits   hub contents on red gate the crusher, furnace and assembler inputs; a decider and a constant make the valve throw out only
             what is listed in CAPS and only above its cap; three tanks on green for the schedule (one tank of three: a third of the total)
Steps: check | create | build [--apply] | config | route | status. The surface is found by the platform's name.
Usage: aquilo_shuttle.py check | create | build [--apply] | config | route | status"""
import json
import sys

from _game import tools
from _wheels import create, place_all

NAME, PLANET = "Fulgora-Aquilo 1 Shuttle", "fulgora"
INNER = False            # scripts/inner_shuttle.py sets this: the same hull for the inner routes, guns only, three furnaces
Q = {"quality": "epic"}
N, E, S, W = 0, 4, 8, 12
DIR = {(0, -1): N, (1, 0): E, (0, 1): S, (-1, 0): W}
CAPS = {"metallic-asteroid-chunk": 30, "carbonic-asteroid-chunk": 30, "oxide-asteroid-chunk": 30, "sulfur": 1000}
ents, cfg, recipes, gates, occ, fluid, tiles, holes, opening = [], [], [], [], {}, {}, set(), set(), {}


def put(name, tx, ty, w=1, h=1, d=N, filt=None, recipe=None, gate=None, **params):
    for c in [(tx + i, ty + j) for i in range(w) for j in range(h)]:
        assert c not in occ and not (-4 <= c[0] < 4 and -4 <= c[1] < 4), "%s at %s overlaps %s" % (name, c, occ.get(c, "the hub"))
        occ[c] = name
    for x in range(tx - 1, tx + w + 1):
        for y in range(ty - 1, ty + h + 1):
            tiles.add((x, y))
    p = dict(Q)
    p.update(params)
    e = {"name": name, "x": tx + w / 2, "y": ty + h / 2, "direction": d, "params": p}
    ents.append(e)
    if filt:
        cfg.append((e["x"], e["y"], filt))
    if recipe:
        recipes.append((e["x"], e["y"], recipe))
    if gate:
        gates.append((e["x"], e["y"], gate[0], gate[1], gate[2] if len(gate) > 2 else "<"))


def ins(x, y, d, filt=None, gate=None, name="fast-inserter"):
    put(name, x, y, d=d, filt=filt, gate=gate)


def sgn(a):
    return (a > 0) - (a < 0)


def belts(path, end):
    for i, t in enumerate(path):
        kind = t[2] if len(t) > 2 else None
        if kind == "out":
            a = path[i - 1]
            assert abs(t[0] - a[0]) + abs(t[1] - a[1]) <= 9
            put("express-underground-belt", t[0], t[1], d=DIR[(sgn(t[0] - a[0]), sgn(t[1] - a[1]))], type="output")
            continue
        if i + 1 < len(path):
            b = path[i + 1]
            assert kind == "in" or abs(b[0] - t[0]) + abs(b[1] - t[1]) == 1, "gap in belt at %s" % (t,)
            d = DIR[(sgn(b[0] - t[0]), sgn(b[1] - t[1]))]
        else:
            d = end
        if kind == "in":
            put("express-underground-belt", t[0], t[1], d=d, type="input")
        else:
            put("express-transport-belt", t[0], t[1], d=d)


def row(x0, x1, y):
    return [(x, y) for x in range(x0, x1 + sgn(x1 - x0), sgn(x1 - x0) or 1)]


def col(x, y0, y1):
    return [(x, y) for y in range(y0, y1 + sgn(y1 - y0), sgn(y1 - y0) or 1)]


def pipe(f, *ts):
    for x, y in ts:
        put("pipe", x, y)
        fluid[(x, y)] = f


def ptg(f, x, y, d):
    put("pipe-to-ground", x, y, d=d)
    fluid[(x, y)] = f
    opening[(x, y)] = {v: k for k, v in DIR.items()}[d]                  # a pipe to ground joins only at its open end


def layout():
    # ---- hub edge, north ----
    ins(-4, -5, N, name="bulk-inserter")                                  # chunks in: everything, the valve throws out the surplus
    ins(-3, -5, S, name="bulk-inserter")                                  # the valve, drops into the hole at -3,-6
    holes.add((-3, -6))
    for tx, ty in ((-2, -8), (-2, -12), (-2, -16), (-6, -12), (2, -12), (-6, -16), (2, -16)):
        put("cargo-bay", tx, ty, 4, 4)                                    # the spine first: a bay must touch the hub or a bay
    ins(2, -5, S, ["firearm-magazine"], name="bulk-inserter")             # magazines out
    belts([(2, -6), (2, -7), (2, -8)] + row(3, 11, -8), E)                # ... to the ammunition belt, from its west side
    put("decider-combinator", 3, -7, 1, 2)                                # the valve's brain
    put("constant-combinator", 4, -7)
    # ---- west ----
    put("chemical-plant", -8, -6, 3, 3, recipe="thruster-oxidizer")
    ins(-5, -4, E, ["iron-ore"])
    put("crusher", -8, -2, 3, 2, d=E, recipe="metallic-asteroid-crushing")
    ins(-5, -2, E, ["metallic-asteroid-chunk"], gate=("iron-ore", 3000))
    ins(-5, -1, W)
    put("decider-combinator", -9, -6, 1, 2)                               # the west crusher's recipe: crushing below 3,000 iron ore,
    put("decider-combinator", -11, -6, 1, 2)                              # reprocessing at or above it (REPRO)
    put("electric-furnace", -8, 0, 3, 3)
    ins(-5, 0, E, ["iron-ore"], gate=("iron-plate", 400))
    ins(-5, 2, W)
    put("chemical-plant", -8, 3, 3, 3, recipe="ice-melting")
    ins(-5, 3, E, ["ice"])
    # ---- east ----
    put("chemical-plant", 5, -6, 3, 3, recipe="thruster-fuel")
    ins(4, -4, W, ["carbon"], gate=None if INNER else ("carbon", 200, ">"))   # the coal plant (rockets) has first call on carbon
    put("crusher", 5, -2, 3, 2, d=E, recipe="carbonic-asteroid-crushing" if INNER else "advanced-carbonic-asteroid-crushing")   # inner: no use for sulfur
    ins(4, -2, W, ["carbonic-asteroid-chunk"], gate=("carbon", 4000))
    ins(4, -1, E)
    put("assembling-machine-3", 5, 0, 3, 3, recipe="firearm-magazine")
    ins(4, 0, W, ["iron-plate"], gate=("firearm-magazine", 1000))
    ins(4, 2, E)
    put("assembling-machine-3", 5, 3, 3, 3, recipe="firearm-magazine" if INNER else "rocket")   # inner: a second magazine assembler, straight onto the belt
    ins(4, 3, W, ["iron-plate"])
    # ---- south ----
    put("crusher", -5, 5, 3, 2, d=E, recipe="oxide-asteroid-crushing")
    ins(-4, 4, N, ["oxide-asteroid-chunk"], gate=("ice", 1500))
    ins(-3, 4, S)
    if INNER:                                                             # two more furnaces: the Fulgora run burned 38 magazines a minute
        for fx in (-2, 1):                                                # and two furnaces (142 plates) could not keep up
            put("electric-furnace", fx, 5, 3, 3)
            ins(fx, 4, N, ["iron-ore"], gate=("iron-plate", 400))
            ins(fx + 2, 4, S)
    else:
        put("chemical-plant", -2, 5, 3, 3, d=S, recipe="coal-synthesis")
        ins(-2, 4, N, ["carbon", "sulfur"], gate=("coal", 300))
        ins(0, 4, S)
        put("chemical-plant", 1, 5, 3, 3, d=S, recipe="explosives")
        ins(1, 4, N, ["coal", "sulfur"])
        ins(4, 5, W)                                                      # explosives round the corner into the rocket assembler
    # ---- chunks ----
    for tx, ix, pick, bx in ((-11, -8, W, -7), (8, 7, E, 6)):
        put("asteroid-collector", tx, -24, 3, 3)
        for x in range(tx, tx + 3):
            holes.add((x, -24))                                           # a collector's front row hangs over open space
        ins(ix, -23, pick)
    belts([(-7, -23), (-7, -22), (-7, -21, "in"), (-7, -19, "out")] + col(-7, -18, -9) + [(-7, -8), (-6, -8), (-5, -8), (-4, -8), (-4, -7), (-4, -6)], S)
    belts([(6, -23), (6, -22), (6, -21, "in"), (6, -19, "out"), (6, -18)] + row(5, -6, -18), W)
    # ---- ammunition ----
    ins(8, 4, W)                                                          # rockets out of the assembler, onto the underground that starts the belt
    belts([(9, 4, "in"), (11, 4, "out"), (12, 4)] + col(12, 3, -19) + [(12, -20)] + row(11, -12, -20) + [(-13, -20)] + col(-13, -19, -1), S)
    for x in (-5, 2):                                                     # nose
        if INNER:
            put("gun-turret", x, -23, 2, 2)
        else:
            put("rocket-turret", x, -24, 3, 3)
        ins(x + 1, -21, S)
    put("gun-turret", -2, -23, 2, 2)
    ins(-2, -21, S)
    put("gun-turret", 0, -23, 2, 2)
    ins(1, -21, S)
    for y in (-19, -12, -10):                                             # flanks
        put("gun-turret", -16, y, 2, 2)
        ins(-14, y, E)
        put("gun-turret", 14, y, 2, 2)
        ins(13, y, W)
    for y in (-16, -3):
        if INNER:
            put("gun-turret", -16, y, 2, 2)
            put("gun-turret", 14, y, 2, 2)
        else:
            put("rocket-turret", -17, y, 3, 3)
            put("rocket-turret", 14, y, 3, 3)
        ins(-14, y + 1, E)
        ins(13, y + 1, W)
    # ---- water ----
    pipe("water", (-6, 6), (-6, 7), (-8, 6), (-8, 7), *row(-12, 10, 8), (-3, 9), (0, 9), *col(-12, 7, -7), *row(-11, -6, -7), *col(10, 7, -7), *row(9, 5, -7))
    put("storage-tank", -3, 10, 3, 3)
    put("storage-tank", 0, 10, 3, 3)
    # ---- oxidizer ----
    pipe("oxidizer", (-8, -3), (-7, -3), (-6, -3), (-9, -3), (-10, -3), *col(-10, -2, 6), *col(-10, 10, 15), (-6, 12), (-10, 19), (-9, 19), (-8, 19))
    ptg("oxidizer", -10, 7, N)
    ptg("oxidizer", -10, 9, S)
    ptg("oxidizer", -10, 16, N)
    ptg("oxidizer", -10, 18, S)
    put("storage-tank", -9, 10, 3, 3)
    put("storage-tank", -9, 13, 3, 3)
    put("storage-tank", -6, 13, 3, 3)
    # ---- fuel ----
    pipe("fuel", (5, -3), (6, -3), (7, -3), (8, -3), *col(8, -2, 2), (8, 6), *col(8, 10, 16), (7, 12), (6, 16), (11, 16))
    ptg("fuel", 8, 3, N)
    ptg("fuel", 8, 5, S)
    ptg("fuel", 8, 7, N)
    ptg("fuel", 8, 9, S)
    put("storage-tank", 4, 10, 3, 3)
    put("storage-tank", 4, 13, 3, 3)
    put("storage-tank", 9, 13, 3, 3)
    # ---- rear block, as on the inner shuttles ----
    pipe("fuel", *row(-12, 12, 17), *col(-12, 18, 21), (0, 21), (0, 22), (-1, 22), (-1, 23), *col(12, 18, 23), (11, 23))
    ptg("fuel", 0, 18, N)
    ptg("fuel", 0, 20, S)
    pipe("oxidizer", *row(-7, 5, 19), (-7, 20), (-7, 21), (-7, 22), (-6, 22), (-6, 23), (5, 20), (5, 21), (5, 22), (6, 22), (6, 23))
    for tx in (-11, -5, 1, 7):
        put("thruster", tx, 21, 4, 5)
    # ---- power ----
    for x0 in (-22, 13):
        for i in range(3):
            for j in range(6):
                put("solar-panel", x0 + 3 * i, 3 * j, 3, 3)
    for tx, ty in ((-5, 10), (-3, 13), (-1, 13), (1, 13)):
        put("accumulator", tx, ty, 2, 2)
    for (x, y), f in fluid.items():
        for dx, dy in DIR:
            n = (x + dx, y + dy)
            g = fluid.get(n)
            joins = opening.get((x, y), (dx, dy)) == (dx, dy) and opening.get(n, (-dx, -dy)) == (-dx, -dy)
            assert g is None or g == f or not joins, "%s pipe at %s touches %s" % (f, (x, y), g)
    for x in range(-5, 5):
        for y in range(-5, 5):
            tiles.add((x, y))
    keep = {(x, y) for (x, y) in tiles if -24 <= y <= 25 and (x, y) not in holes}
    tiles.clear()
    tiles.update(keep)
    return {"entities": len(ents), "tiles": len(tiles), "width": (min(x for x, y in tiles), max(x for x, y in tiles))}


def surface():
    r = tools["run_lua"]("for _,p in pairs(game.forces.player.platforms) do if p.name=='%s' then rcon.print(p.surface.name..'|'..p.index) return end end rcon.print('none')" % NAME).strip()
    return None if r == "none" else r.split("|")


TILES = ("local s=game.surfaces['SURF'] local want={} local add={} for _,p in pairs(LIST) do want[p[1]..','..p[2]]=true add[#add+1]={name='space-platform-foundation',position=p} end s.set_tiles(add) local rm={} "
         "for _,t in pairs(s.find_tiles_filtered{name='space-platform-foundation'}) do if not want[t.position.x..','..t.position.y] then rm[#rm+1]={name='empty-space',position=t.position} end end s.set_tiles(rm) rcon.print('foundation '..#add..' removed '..#rm)")
# Rocket turrets fire only at big and huge asteroids: left free they shot rockets at small and medium ones in Fulgora orbit, 5,635 rockets
# made and the hub held none, with all the carbon gone (the Captain, 2026-11-13: "major rocket ammo problems"). The guns take the small ones.
# The west crusher changes recipe by circuit (the Captain, 2026-11-13: reshuffle a surplus into what is short). Metallic chunks stood at their
# cap with 3,000 ore in store while carbon ran out. Two deciders read the hub (red): below 3,000 iron ore they send the recipe signal for
# metallic crushing, at or above it for metallic reprocessing, on a green wire of their own to the crusher. Its intake has no gate any more.
REPRO = ("local s=game.surfaces['SURF'] local hub=s.platform.hub local W=defines.wire_connector_id local function dec(x) return s.find_entities_filtered{name='decider-combinator',position={x,-5},radius=0.6}[1] end local a,b=dec(-8.5),dec(-10.5) "
         "local function set(d,cmp,rec) d.get_or_create_control_behavior().parameters={conditions={{first_signal={type='item',name='iron-ore'},comparator=cmp,constant=3000}},outputs={{signal={type='recipe',name=rec},copy_count_from_input=false,constant=1}}} end "
         "set(a,'<','metallic-asteroid-crushing') set(b,'>=','metallic-asteroid-reprocessing') "
         "a.get_wire_connector(W.combinator_input_red,true).connect_to(hub.get_wire_connector(W.circuit_red,true),false) b.get_wire_connector(W.combinator_input_red,true).connect_to(a.get_wire_connector(W.combinator_input_red,true),false) "
         "b.get_wire_connector(W.combinator_output_green,true).connect_to(a.get_wire_connector(W.combinator_output_green,true),false) "
         "local c=s.find_entities_filtered{name='crusher',position={-6.5,-1},radius=1}[1] c.get_wire_connector(W.circuit_green,true).connect_to(a.get_wire_connector(W.combinator_output_green,true),false) c.get_or_create_control_behavior().circuit_set_recipe=true "
         "s.find_entities_filtered{type='inserter',position={-4.5,-1.5},radius=0.3}[1].get_or_create_control_behavior().circuit_enable_disable=false rcon.print('west crusher recipe by circuit')")
TARGETS = ("local s=game.surfaces['SURF'] local n=0 for _,t in pairs(s.find_entities_filtered{name='rocket-turret'}) do local i=0 for _,sz in pairs{'big','huge'} do "
           "for _,k in pairs{'metallic','carbonic','oxide'} do i=i+1 t.set_priority_target(i,sz..'-'..k..'-asteroid') end end t.ignore_unprioritised_targets=true n=n+1 end rcon.print('rocket turrets limited to big asteroids '..n)")
CONFIG = ("local s=game.surfaces['SURF'] local hub=s.platform.hub local W=defines.wire_connector_id local n,r,g=0,0,0 local function ins(x,y) return s.find_entities_filtered{type='inserter',position={x,y},radius=0.3}[1] end "
          "pcall(function() hub.get_or_create_control_behavior().read_contents=true end) "
          "for _,q in pairs(FILT) do local i=ins(q[1],q[2]) if i then i.use_filters=true i.inserter_filter_mode='whitelist' for k,name in pairs(q[3]) do i.set_filter(k,name) end n=n+1 end end "
          "for _,q in pairs(REC) do for _,m in pairs(s.find_entities_filtered{position={q[1],q[2]},radius=0.5}) do if m.type=='assembling-machine' then m.set_recipe(q[3]) r=r+1 end end end "
          "for _,q in pairs(GATES) do local i=ins(q[1],q[2]) i.get_wire_connector(W.circuit_red,true).connect_to(hub.get_wire_connector(W.circuit_red,true),false) local cb=i.get_or_create_control_behavior() cb.circuit_enable_disable=true "
          "cb.circuit_condition={first_signal={type='item',name=q[3]},comparator=q[5],constant=q[4]} g=g+1 end "
          "local prev=hub for _,q in pairs({{-1.5,11.5},{5.5,11.5},{-7.5,11.5}}) do local t=s.find_entities_filtered{name='storage-tank',position=q,radius=0.5}[1] prev.get_wire_connector(W.circuit_green,true).connect_to(t.get_wire_connector(W.circuit_green,true),false) prev=t end "
          "rcon.print('inserters filtered '..n..', recipes '..r..', gates '..g)")
VALVE = ("local s=game.surfaces['SURF'] local hub=s.platform.hub local W=defines.wire_connector_id local dec=s.find_entities_filtered{name='decider-combinator',position={3.5,-6},radius=0.6}[1] local cc=s.find_entities_filtered{name='constant-combinator'}[1] "
         "local v=s.find_entities_filtered{type='inserter',position={-2.5,-4.5},radius=0.3}[1] local sec=cc.get_or_create_control_behavior().get_section(1) or cc.get_or_create_control_behavior().add_section() local k=0 "
         "for name,c in pairs(CAPS) do k=k+1 sec.set_slot(k,{value={type='item',name=name,quality='normal'},min=c}) end "
         "dec.get_or_create_control_behavior().parameters={conditions={{first_signal={type='virtual',name='signal-each'},first_signal_networks={red=true,green=false},comparator='>',second_signal={type='virtual',name='signal-each'},second_signal_networks={red=false,green=true}},"
         "{first_signal={type='virtual',name='signal-each'},first_signal_networks={red=false,green=true},comparator='>',constant=0,compare_type='and'}},outputs={{signal={type='virtual',name='signal-each'},copy_count_from_input=false}}} "
         "dec.get_wire_connector(W.combinator_input_red,true).connect_to(hub.get_wire_connector(W.circuit_red,true),false) dec.get_wire_connector(W.combinator_input_green,true).connect_to(cc.get_wire_connector(W.circuit_green,true),false) "
         "local vr=v.get_wire_connector(W.circuit_green,true) vr.connect_to(dec.get_wire_connector(W.combinator_output_green,true),false) v.use_filters=true v.inserter_filter_mode='whitelist' local cb=v.get_or_create_control_behavior() cb.circuit_set_filters=true cb.circuit_enable_disable=true "
         "cb.circuit_condition={first_signal={type='virtual',name='signal-anything'},comparator='>',constant=0} rcon.print('valve wired '..tostring(vr.is_connected_to(dec.get_wire_connector(W.combinator_output_green,true)))..', caps '..k)")
# ITEM conditions count double (the hub puts its contents on the red and the green wire): 5,000 carbon here is 2,500 in the hub. The first
# flight left with half of what was meant. One leg burned about 80,000 fuel, so Aquilo lets the ship go at 30,000 a tank (90,000 on board).
# The hub sees one tank of three for each fluid, so 40,000 here is 120,000 on board. Aquilo's orbit has almost no carbonic or metallic
# chunks: the ship refuels there from the carbon and iron ore in its hub (gates: 4,000 and 3,000), so it must leave Fulgora with both.
ROUTE = ("local p=game.surfaces['SURF'].platform local function c(t,n,k) return {type='circuit',compare_type='and',condition={first_signal={type=t,name=n},comparator='>=',constant=k}} end "
         "p.schedule={current=1,records={{station='fulgora',wait_conditions={c('fluid','thruster-fuel',40000),c('fluid','thruster-oxidizer',40000),c('item','firearm-magazine',1200),c('item','carbon',5000),c('item','iron-ore',4000),c('item','processing-unit',300),c('item','refined-concrete',60),{type='time',compare_type='and',ticks=18000}}},"
         "{station='aquilo',wait_conditions={c('fluid','thruster-fuel',30000),c('fluid','thruster-oxidizer',30000),{type='time',compare_type='and',ticks=7200}}}}} p.paused=false rcon.print('schedule fulgora <-> aquilo set')")
STATUS = ("local s=game.surfaces['SURF'] local p=s.platform local st={} for _,c in pairs(s.find_entities_filtered{type={'assembling-machine','furnace','asteroid-collector','ammo-turret'}}) do local k='?' for n,v in pairs(defines.entity_status) do if v==c.status then k=n end end "
          "local rc=c.type=='assembling-machine' and c.get_recipe() k=(rc and rc.name or c.name)..' '..k st[k]=(st[k] or 0)+1 end local o={} for k,v in pairs(st) do o[#o+1]=k..' '..v end table.sort(o) local fl={} for _,t in pairs(s.find_entities_filtered{name='storage-tank'}) do for k,v in pairs(t.get_fluid_contents()) do fl[k]=(fl[k] or 0)+v end end "
          "local f={} for k,v in pairs(fl) do f[#f+1]=k..' '..math.floor(v) end local inv=p.hub.get_inventory(defines.inventory.hub_main) local c={} for _,it in pairs(inv.get_contents()) do c[#c+1]=it.name..' '..it.count end "
          "local a,cap=0,0 for _,e in pairs(s.find_entities_filtered{name='accumulator'}) do a=a+e.energy cap=cap+e.electric_buffer_size end local dmg=0 for _,e in pairs(s.find_entities_filtered{force='player'}) do if e.health and e.max_health and e.health<e.max_health then dmg=dmg+1 end end "
          "rcon.print(table.concat(o,' ; ')..' ; TANKS '..table.concat(f,', ')..' ; HUB slots '..#inv..' free '..inv.count_empty_stacks()..': '..table.concat(c,', ')..' ; accumulators '..string.format('%.0f%%',cap>0 and 100*a/cap or 0)..', damaged '..dmg..', ghosts '..s.count_entities_filtered{type='entity-ghost'}..', at '..(p.space_location and p.space_location.name or 'in transit'))")


def main():
    step = sys.argv[1]
    apply = "--apply" in sys.argv
    print(layout())
    if step == "check":
        return
    if step == "create":
        print(create(NAME, PLANET))
        return
    sf, index = surface()
    print("==", NAME, sf, "platform", index)
    if step == "build":
        if apply:
            lst = "{" + ",".join("{%d,%d}" % t for t in sorted(tiles)) + "}"
            print(tools["run_lua"](TILES.replace("SURF", sf).replace("LIST", lst)))
        ok, bad = place_all(ents, sf, apply)
        print("placed" if apply else "dry run", ok, "failed", bad)
    if step == "config" or (step == "build" and apply):
        filt = "{" + ",".join("{%s,%s,{%s}}" % (x, y, ",".join("'%s'" % f for f in fl)) for x, y, fl in cfg) + "}"
        rec = "{" + ",".join("{%s,%s,'%s'}" % r for r in recipes) + "}"
        gt = "{" + ",".join("{%s,%s,'%s',%d,'%s'}" % g for g in gates) + "}"
        print(tools["run_lua"](CONFIG.replace("SURF", sf).replace("FILT", filt).replace("REC", rec).replace("GATES", gt)))
        print(tools["run_lua"](TARGETS.replace("SURF", sf)))
        print(tools["run_lua"](REPRO.replace("SURF", sf)))
        print(tools["run_lua"](VALVE.replace("SURF", sf).replace("CAPS", "{" + ",".join("['%s']=%d" % kv for kv in CAPS.items()) + "}")))
    elif step == "route":
        print(tools["run_lua"](ROUTE.replace("SURF", sf)))
    elif step == "status":
        print(tools["run_lua"](STATUS.replace("SURF", sf)).replace(" ; ", "\n"))


if __name__ == "__main__":
    main()
