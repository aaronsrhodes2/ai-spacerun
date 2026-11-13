#!/usr/bin/env python3
"""Chemical (blue) science on every wheel, made from asteroid products only (the Captain, 2026-11-13: "Build it"; nothing by rocket).
Carbon is the limit: a pack costs about 60 carbon through coal -> heavy oil -> petroleum gas -> plastic, so expect about 12 a minute
on the Gleba wheel and 7 on Nauvis. Ordinary coal liquefaction would halve that cost but needs steam, and no boiler stands in space.
  hub edge   three of the four valve tiles on the hub's east edge now feed the line (one valve inserter is left); each bulk inserter takes
             several items and a circuit keeps its belt from filling with one of them: every belt tile of the line is wired and read,
             the filter is "target minus what lies on the whole belt", so an item is only loaded while less than its target is
             under way (reading only a stretch near the hub failed: the item used least piled up from the far end and blocked the rest)
               K  carbon, sulfur, calcite      O  iron ore, copper ore      W  ice
             The east product belt used to end pointing north at tile 5,0; the ice belt now starts on the next tile, so that end is
             turned west (toward its inserter), or crusher products side-load onto the ice belt
  avenue     the three belts run out along the east avenue (rows 0..2), under the bridge bay, under the east flat and the loop,
             then north up three columns to the block
  block      new deck north of the east spoke, wheel x 46..123, y -41..-4 (local 0,0 = wheel 57,-29):
             chemistry  ice melters -> water main; 4 coal plants (carbon + sulfur + water) drop coal on the other lane of belt K;
                        sulfuric acid (own iron furnace) -> refinery (simple coal liquefaction, coal + calcite off K) -> heavy cracking
                        -> light cracking -> petroleum gas piped east to the plastic plant
             cluster    every machine hands its product straight to the next, no plate belts: furnaces round the outside take ore off
                        belt O (a U round the cluster); steel, gears and pipes meet in the engine assembler; cable, circuits and
                        plastic meet in the advanced-circuit assembler; both feed the one science assembler, sulfur comes off K
  packs      one belt back west under the loop, side-loading the east product belt, which the hub already takes in
Steps on every wheel (--only gleba|nauvis): check | pre | build [--apply] | refit | config | sweep | status. Never apply twice on the same wheel.
Usage: wheel_blue.py check | pre | build [--apply] | refit | config | sweep | status  [--only PLANET]"""
import sys

from _game import tools
from _wheels import lay_foundation, place_all, wheels

Q = {"quality": "rare"}
N, E, S, W = 0, 4, 8, 12
OX, OY = 57, -29
DIR = {(0, -1): N, (1, 0): E, (0, 1): S, (-1, 0): W}
TARGETS = {"K": {"carbon": 300, "sulfur": 100, "calcite": 30}, "O": {"iron-ore": 200, "copper-ore": 130}, "W": {"ice": 250}}   # on the whole belt
ents, cfg, recipes, occ, fluid, lines = [], [], [], {}, {}, {}


def put(name, tx, ty, w=1, h=1, d=N, filt=None, recipe=None, local=True, **params):
    if local:
        tx, ty = tx + OX, ty + OY
    for c in [(tx + i, ty + j) for i in range(w) for j in range(h)]:
        assert c not in occ, "%s at %s overlaps %s" % (name, c, occ[c])
        occ[c] = name
    p = dict(Q)
    p.update(params)
    e = {"name": name, "x": tx + w / 2, "y": ty + h / 2, "direction": d, "params": p}
    ents.append(e)
    if filt:
        cfg.append((e["x"], e["y"], filt))
    if recipe:
        recipes.append((e["x"], e["y"], recipe))


def sgn(a):
    return (a > 0) - (a < 0)


def belts(path, end, local=True, line=None):
    """path: tiles in order; (x, y, 'in') starts an underground that comes up at the next tile, marked (x, y, 'out')."""
    for i, t in enumerate(path):
        kind = t[2] if len(t) > 2 else None
        if line:
            lines.setdefault(line, []).append((t[0] + OX, t[1] + OY) if local else (t[0], t[1]))
        if kind == "out":
            a = path[i - 1]
            d = DIR[(sgn(t[0] - a[0]), sgn(t[1] - a[1]))]
            assert abs(t[0] - a[0]) + abs(t[1] - a[1]) <= 9
            put("express-underground-belt", t[0], t[1], d=d, local=local, type="output")
            continue
        if i + 1 < len(path):
            b = path[i + 1]
            assert kind == "in" or abs(b[0] - t[0]) + abs(b[1] - t[1]) == 1, "gap in belt at %s" % (t,)
            d = DIR[(sgn(b[0] - t[0]), sgn(b[1] - t[1]))]
        else:
            d = end
        if kind == "in":
            put("express-underground-belt", t[0], t[1], d=d, local=local, type="input")
        else:
            put("express-transport-belt", t[0], t[1], d=d, local=local)


def row(x0, x1, y):
    return [(x, y) for x in range(x0, x1 + sgn(x1 - x0), sgn(x1 - x0))]


def col(x, y0, y1):
    return [(x, y) for y in range(y0, y1 + sgn(y1 - y0), sgn(y1 - y0))]


def pipe(f, *tiles):
    for x, y in tiles:
        put("pipe", x, y)
        fluid[(x, y)] = f


def ptg(f, x, y, d):
    put("pipe-to-ground", x, y, d=d)
    fluid[(x, y)] = f


def ins(x, y, d, filt=None, name="fast-inserter"):
    put(name, x, y, d=d, filt=filt)


def layout():
    # --- hub side (wheel coordinates) ---
    put("bulk-inserter", 4, -3, d=W, local=False)
    put("bulk-inserter", 4, -2, d=W, local=False)
    put("bulk-inserter", 4, -1, d=W, local=False)
    for i in range(3):
        put("arithmetic-combinator", 9 + i, -4, 1, 2, local=False)
        put("constant-combinator", 9 + i, -2, local=False)
    # K: carbon, sulfur, calcite
    belts([(5, -3), (6, -3), (7, -3), (8, -3), (8, -2), (8, -1), (8, 0)] + row(9, 30, 0) + [(31, 0, "in"), (36, 0, "out"), (37, 0, "in"), (40, 0, "out"),
           (41, 0), (41, -1), (41, -2), (42, -2), (43, -2), (44, -2, "in"), (46, -2, "out")] + row(47, 52, -2) + col(53, -2, -37) +
          [(53, -38), (54, -38)] + col(55, -38, -31), S, local=False, line="K")
    # O: iron ore, copper ore
    belts([(5, -2), (6, -2), (7, -2), (7, -1), (7, 0), (7, 1)] + row(8, 30, 1) + [(31, 1, "in"), (36, 1, "out"), (37, 1, "in"), (40, 1, "out"),
           (41, 1), (42, 1), (42, 0), (42, -1), (43, -1), (44, -1, "in"), (46, -1, "out")] + row(47, 53, -1) + col(54, -1, -22) +
          [(54, -23), (55, -23, "in"), (57, -23, "out")] +
          [(x + OX, y + OY) for x, y in row(1, 12, 6) + [(13, 6)]] + [(13 + OX, 7 + OY, "in"), (13 + OX, 9 + OY, "out")] +
          [(x + OX, y + OY) for x, y in [(13, 10), (13, 11)] + row(13, 38, 12) + col(39, 12, 5)] +
          [(39 + OX, 4 + OY, "in"), (39 + OX, -2 + OY, "out")] + [(x + OX, y + OY) for x, y in [(39, -3), (39, -4)] + row(39, 42, -5) + [(43, -5), (43, -4)]],
          S, local=False, line="O")
    # the ore loop round the cluster: a mixed belt with a dead end jams (what is used least piles up at the end), a loop cannot.
    # The loop comes round on the south lane of row -3 (side-load at 42,-3), the feed joins on the north lane (side-load at 43,-3).
    put("express-transport-belt", 41, -3, d=E)
    belts(row(42, 63, -3) + col(64, -3, 24) + row(64, 43, 25) + col(42, 25, 5) + [(42, 4, "in"), (42, -2, "out")], N, line="O")
    # W: ice
    belts([(5, -1), (6, -1), (6, 0), (6, 1)] + row(6, 30, 2) + [(31, 2, "in"), (36, 2, "out"), (37, 2), (38, 2), (38, 1), (38, 0), (38, -1), (37, -1)] +
          col(37, -2, -6) + [(38, -6, "in"), (46, -6, "out"), (47, -6, "in"), (49, -6, "out"), (50, -6), (51, -6)] + col(52, -6, -39) + row(52, 63, -40),
          E, local=False, line="W")
    # --- the block (local coordinates) ---
    # K is a loop too: east along row -1 past the coal plants, acid, refinery and plastic, down to the science assembler, out east
    # under the ore loop, back west along row -12 and in behind its own head, so the feed from the north side-loads:
    # supply on the north lane, coal on the south
    belts(row(-2, 54, -1) + col(55, -1, 4) + [(55, 5, "in"), (55, 7, "out"), (55, 8), (56, 8), (56, 9), (56, 10), (56, 11), (56, 12)] + row(57, 62, 12) +
          [(63, 12, "in"), (65, 12, "out"), (66, 12)] + col(66, 11, -11) + [(66, -12)] + row(65, -6, -12) + [(-7, -12)] + col(-7, -11, -2) +
          [(-7, -1), (-6, -1, "in"), (-3, -1, "out")], E, line="K")
    for i in range(4):                                                 # coal
        put("chemical-plant", 4 * i, -5, 3, 3, recipe="coal-synthesis")
        ins(4 * i, -2, S, ["carbon", "sulfur"])
        ins(4 * i + 2, -2, N, ["coal"])
    for x in (0, 4):                                                   # water
        put("chemical-plant", x, -9, 3, 3, recipe="ice-melting")
        ins(x + 1, -10, N, ["ice"])
    pipe("water", *row(-1, 13, -6), (13, -7), (14, -7), (-1, -5), (-1, -4), (-1, -3), (14, 1), (14, 2), (14, 3), *col(-1, 1, 8), *row(0, 31, 8), (26, 7), (26, 6))
    ptg("water", 14, -6, N)
    ptg("water", 14, 0, S)
    ptg("water", -1, -2, N)
    ptg("water", -1, 0, S)
    put("chemical-plant", 15, 1, 3, 3, d=W, recipe="sulfuric-acid")    # acid, with its own iron furnace
    ins(16, 0, N, ["sulfur"])
    put("electric-furnace", 15, 5, 3, 3)
    ins(16, 4, S)
    ins(14, 6, W, ["iron-ore"])
    pipe("acid", (18, 3), (18, 2), (19, 2), (19, 3), (19, 4))
    put("oil-refinery", 20, 1, 5, 5, d=E, recipe="simple-coal-liquefaction")
    ins(21, 0, N, ["coal"])
    ins(23, 0, N, ["calcite"])
    pipe("heavy", *col(25, 1, 5), (26, 4))
    put("chemical-plant", 27, 4, 3, 3, d=W, recipe="heavy-oil-cracking")
    pipe("light", (30, 4), (30, 5), (30, 6), (31, 6))
    put("chemical-plant", 32, 6, 3, 3, d=W, recipe="light-oil-cracking")
    pipe("gas", (35, 6), (35, 7), (35, 8), (36, 6), (37, 6), (38, 6), (38, 5), (38, 4), *row(38, 51, 3))
    # the cluster: machine (i, j) stands at (52 + 4 i, 9 + 4 j); science is (0, 0)
    def m(name, i, j, recipe=None, d=N):
        put(name, 52 + 4 * i, 9 + 4 * j, 3, 3, d=d, recipe=recipe)
    A, F = "assembling-machine-3", "electric-furnace"
    m(A, 0, 0, "chemical-science-pack")
    m(A, 0, 1, "engine-unit")
    m(F, -1, 1)                                                        # steel
    m(F, -2, 1)
    m(A, 1, 1, "pipe")
    m(F, 2, 1)
    m(A, 0, 2, "iron-gear-wheel")
    m(F, 0, 3)
    m(A, 0, -1, "advanced-circuit")
    m(A, -1, -1, "copper-cable")
    m(F, -2, -1)
    m(A, 1, -1, "electronic-circuit")
    m(F, 2, -1)
    m("chemical-plant", 0, -2, "plastic-bar", d=W)
    m(A, 1, -2, "copper-cable")
    m(F, 2, -2)
    ins(43, 6, W, ["copper-ore"])
    ins(47, 6, W)
    ins(51, 6, W)
    ins(55, 6, E)
    ins(59, 6, E)
    ins(63, 6, E, ["iron-ore"])
    ins(57, 4, N)
    ins(59, 2, E)
    ins(63, 2, E, ["copper-ore"])
    ins(53, 4, N)
    ins(53, 0, N, ["coal"])
    ins(53, 8, N)
    ins(53, 12, S)
    ins(51, 14, W)
    ins(47, 14, W)
    ins(43, 14, W, ["iron-ore"])
    ins(55, 14, E)
    ins(59, 14, E)
    ins(63, 14, E, ["iron-ore"])
    ins(53, 16, S)
    ins(53, 20, S)
    ins(53, 24, S, ["iron-ore"])
    ins(55, 10, E, ["sulfur"])
    ins(51, 10, E, ["chemical-science-pack"])
    belts([(50, 10), (50, 9), (50, 8)] + row(49, 44, 8) + [(43, 8, "in"), (38, 8, "out"), (37, 8), (37, 9), (37, 10), (37, 11, "in"), (37, 13, "out")] +
          row(37, -1, 14) + [(-2, 14, "in"), (-6, 14, "out"), (-7, 14), (-8, 14)] + col(-9, 14, 24) + [(-10, 24), (-11, 24, "in"), (-17, 24, "out")], W)
    for (x, y), f in fluid.items():                                    # two fluids must never touch
        for dx, dy in DIR:
            g = fluid.get((x + dx, y + dy))
            assert g is None or g == f, "%s pipe at %s touches %s" % (f, (x, y), g)
    return {"entities": len(ents), "machines": sum(1 for e in ents if e["name"] in ("chemical-plant", "oil-refinery", "assembling-machine-3", "electric-furnace"))}


def lua_list(cells, off=0.5):
    return "{" + ",".join("{%s,%s}" % (c[0] + off, c[1] + off) for c in cells) + "}"


PRE = ("local s=game.surfaces['SURF'] local n,l=0,0 if s.count_entities_filtered{name='arithmetic-combinator',area={{8,-5},{13,0}}}>0 then rcon.print('already built') return end "
       "local b=s.find_entities_filtered{name='cargo-bay',position={10,-2},radius=0.5}[1] if b then b.destroy() n=n+1 end "
       "for _,y in pairs{-2.5,-1.5,-0.5} do local i=s.find_entities_filtered{type='inserter',position={4.5,y},radius=0.3}[1] if i then i.destroy() n=n+1 end end "
       "s.set_tiles{{name='space-platform-foundation',position={5,-3}},{name='space-platform-foundation',position={5,-2}},{name='space-platform-foundation',position={5,-1}}} "
       "for _,e in pairs(s.find_entities_filtered{type='transport-belt',position={5.5,0.5},radius=0.3}) do e.direction=defines.direction.west end "
       "local inv=s.platform.hub.get_inventory(defines.inventory.hub_main) rcon.print('bay and valve inserters removed '..n..', hub slots '..#inv..' free '..inv.count_empty_stacks())")
LAMPS = "local s=game.surfaces['SURF'] local l=0 for _,p in pairs(TILES) do for _,e in pairs(s.find_entities_filtered{type='lamp',position=p,radius=0.3}) do e.destroy() l=l+1 end end rcon.print('lamps removed '..l)"
CONFIG = ("local s=game.surfaces['SURF'] local n,r=0,0 for _,q in pairs(FILT) do local i=s.find_entities_filtered{type='inserter',position={q[1],q[2]},radius=0.3}[1] if i then i.use_filters=true i.inserter_filter_mode='whitelist' "
          "for k,name in pairs(q[3]) do i.set_filter(k,name) end n=n+1 end end "
          "for _,q in pairs(REC) do local m=s.find_entities_filtered{type='assembling-machine',position={q[1],q[2]},radius=0.5}[1] if m then m.set_recipe(q[3]) r=r+1 end end rcon.print('inserters filtered '..n..', recipes '..r)")
CIRCUIT = ("local s=game.surfaces['SURF'] local W=defines.wire_connector_id local o={} local function at(t,x,y) return s.find_entities_filtered{type=t,position={x,y},radius=0.3}[1] end "
           "for _,q in pairs(SETS) do local i=at('inserter',4.5,q.iy) local ar=at('arithmetic-combinator',q.ax,-3) local cc=at('constant-combinator',q.ax,-1.5) "
           "local sec=cc.get_or_create_control_behavior().get_section(1) or cc.get_or_create_control_behavior().add_section() local k=0 for name,c in pairs(q.t) do k=k+1 sec.set_slot(k,{value={type='item',name=name,quality='normal'},min=c}) end "
           "ar.get_or_create_control_behavior().parameters={first_signal={type='virtual',name='signal-each'},second_constant=-1,operation='*',output_signal={type='virtual',name='signal-each'}} "
           "local prev=nil local nb=0 for _,p in pairs(q.tiles) do local b=at('transport-belt',p[1],p[2]) if b then local bc=b.get_or_create_control_behavior() bc.read_contents=true bc.read_contents_mode=defines.control_behavior.transport_belt.content_read_mode.hold "
           "if prev then b.get_wire_connector(W.circuit_green,true).connect_to(prev.get_wire_connector(W.circuit_green,true),false) else ar.get_wire_connector(W.combinator_input_green,true).connect_to(b.get_wire_connector(W.circuit_green,true)) end prev=b nb=nb+1 end end "
           "local ir=i.get_wire_connector(W.circuit_red,true) local a=ir.connect_to(ar.get_wire_connector(W.combinator_output_red,true)) local c=ir.connect_to(cc.get_wire_connector(W.circuit_red,true)) "
           "i.use_filters=true i.inserter_filter_mode='whitelist' local ib=i.get_or_create_control_behavior() ib.circuit_set_filters=true ib.circuit_enable_disable=true ib.circuit_condition={first_signal={type='virtual',name='signal-anything'},comparator='>',constant=0} "
           "o[#o+1]=q.n..': belts read '..nb..', inserter-arithmetic '..tostring(ir.is_connected_to(ar.get_wire_connector(W.combinator_output_red,true)))..', inserter-constant '..tostring(ir.is_connected_to(cc.get_wire_connector(W.circuit_red,true))) end rcon.print(table.concat(o,' | '))")
PORTS = ("local s=game.surfaces['SURF'] local o={} for _,m in pairs(s.find_entities_filtered{name={'chemical-plant','oil-refinery'},area={{46,-42},{124,-3}}}) do local fb=m.fluidbox local t={} for i=1,#fb do local lf=fb.get_locked_fluid(i) if lf then "
         "for _,pc in pairs(fb.get_pipe_connections(i)) do t[#t+1]=lf..'@'..(pc.target_position.x-0.5-OX)..','..(pc.target_position.y-0.5-OY)..(pc.target and ' ok' or ' OPEN') end end end "
         "local k='?' for n,v in pairs(defines.entity_status) do if v==m.status then k=n end end o[#o+1]=(m.get_recipe() and m.get_recipe().name or 'none')..' ['..k..'] '..table.concat(t,'  ') end rcon.print(table.concat(o,' ; '))").replace("OX", str(OX)).replace("OY", "(%d)" % OY)
OLD = [(40, 4), (41, 4)]                            # belt tiles of the first build (dead-end belts) that the loops do not use
REFIT = ("local s=game.surfaces['SURF'] local hub=s.platform.hub local need={} local gone=0 local function out(e) for l=1,e.get_max_transport_line_index() do for _,it in pairs(e.get_transport_line(l).get_contents()) do hub.insert{name=it.name,count=it.count,quality=it.quality} end end e.destroy() gone=gone+1 end "
         "for _,p in pairs(OLDT) do for _,e in pairs(s.find_entities_filtered{type={'transport-belt','underground-belt'},position=p,radius=0.3}) do out(e) end end "
         "for i,q in pairs(WANT) do local e=s.find_entities_filtered{type={'transport-belt','underground-belt'},position={q[1],q[2]},radius=0.3}[1] "
         "if e and e.name==q[3] and e.direction==q[4] and (e.type~='underground-belt' or e.belt_to_ground_type==q[5]) then else if e then out(e) end need[#need+1]=i end end rcon.print(gone..';'..table.concat(need,','))")
ALLOWED = {"K": ["carbon", "sulfur", "calcite", "coal"], "O": ["iron-ore", "copper-ore"], "W": ["ice"]}
SWEEP = ("local s=game.surfaces['SURF'] local hub=s.platform.hub local ok={} for _,n in pairs(ALLOW) do ok[n]=true end local t={} local junk=0 for _,p in pairs(TILES) do local e=s.find_entities_filtered{type={'transport-belt','underground-belt'},position=p,radius=0.3}[1] "
         "if e then for l=1,e.get_max_transport_line_index() do local tl=e.get_transport_line(l) for _,it in pairs(tl.get_contents()) do if ok[it.name] then t[it.name]=(t[it.name] or 0)+it.count else junk=junk+tl.remove_item{name=it.name,count=it.count,quality=it.quality} hub.insert{name=it.name,count=it.count,quality=it.quality} end end end end end "
         "local o={} for k,v in pairs(t) do o[#o+1]=k..' '..v end rcon.print('LINE: '..table.concat(o,', ')..' | strays returned to the hub '..junk)")
STATUS = ("local s=game.surfaces['SURF'] local st={} for _,c in pairs(s.find_entities_filtered{type={'assembling-machine','furnace'},area={{46,-42},{124,-3}}}) do local k='?' for n,v in pairs(defines.entity_status) do if v==c.status then k=n end end "
          "local rc=c.get_recipe() k=(rc and rc.name or c.name)..' '..k st[k]=(st[k] or 0)+1 end local o={} for k,v in pairs(st) do o[#o+1]=k..' '..v end table.sort(o) local f=game.forces.player.get_item_production_statistics(s) local inv=s.platform.hub.get_inventory(defines.inventory.hub_main) "
          "rcon.print(table.concat(o,' ; ')..' ; blue science a minute (10 min window) '..string.format('%.1f',f.get_flow_count{name='chemical-science-pack',category='input',precision_index=defines.flow_precision_index.ten_minutes})"
          "..', in hub '..inv.get_item_count('chemical-science-pack')..', hub free slots '..inv.count_empty_stacks())")


def main():
    step = sys.argv[1]
    apply = "--apply" in sys.argv
    print(layout())
    if step == "check":
        return
    for name, planet, surface, turrets in wheels():
        print("==", name, surface or "(not created)")
        if not surface:
            continue
        if step == "pre":
            print(tools["run_lua"](PRE.replace("SURF", surface)))
            tiles = {(x, y) for x in range(46, 124) for y in range(-41, -3)} | set(occ)
            tiles -= {(x, y) for x, y in tiles if x < 46 and (x, y) not in occ}
            print("foundation tiles", lay_foundation(tiles, surface))
            cells = sorted(occ)
            for i in range(0, len(cells), 1500):
                print(tools["run_lua"](LAMPS.replace("SURF", surface).replace("TILES", lua_list(cells[i:i + 1500]))))
        elif step == "build":
            ok, bad = place_all(ents, surface, apply)
            print("placed" if apply else "dry run", ok, "failed", bad)
        if step == "config" or (step == "build" and apply):
            filt = "{" + ",".join("{%s,%s,{%s}}" % (x, y, ",".join("'%s'" % f for f in fl)) for x, y, fl in cfg) + "}"
            rec = "{" + ",".join("{%s,%s,'%s'}" % r for r in recipes) + "}"
            print(tools["run_lua"](CONFIG.replace("SURF", surface).replace("FILT", filt).replace("REC", rec)))
            for k, iy, ax in (("K", -2.5, 9.5), ("O", -1.5, 10.5), ("W", -0.5, 11.5)):
                sets = "{{n='%s',iy=%s,ax=%s,t={%s},tiles=%s}}" % (k, iy, ax, ",".join("['%s']=%d" % kv for kv in TARGETS[k].items()), lua_list(lines[k]))
                print(tools["run_lua"](CIRCUIT.replace("SURF", surface).replace("SETS", sets)))
        elif step == "refit":                       # for a wheel built with the dead-end belts: changes only the belt tiles that differ
            bl = [e for e in ents if e["name"] in ("express-transport-belt", "express-underground-belt")]
            want = "{" + ",".join("{%s,%s,'%s',%d,'%s'}" % (e["x"], e["y"], e["name"], e["direction"], e["params"].get("type", "")) for e in bl) + "}"
            gone, _, need = tools["run_lua"](REFIT.replace("SURF", surface).replace("OLDT", lua_list([(x + OX, y + OY) for x, y in OLD])).replace("WANT", want)).strip().partition(";")
            todo = [bl[int(i) - 1] for i in need.split(",") if i]
            print("belts removed", gone, "to place", len(todo), "placed, failed", place_all(todo, surface, True))
        elif step == "sweep":                       # what lies on each supply belt; anything that does not belong goes back into the hub
            for k, tiles in lines.items():
                print(tools["run_lua"](SWEEP.replace("SURF", surface).replace("LINE", k).replace("ALLOW", "{" + ",".join("'%s'" % a for a in ALLOWED[k]) + "}").replace("TILES", lua_list(tiles))))
        elif step == "ports":
            print(tools["run_lua"](PORTS.replace("SURF", surface)).replace(" ; ", "\n"))
        elif step == "status":
            print(tools["run_lua"](STATUS.replace("SURF", surface)).replace(" ; ", "\n"))


if __name__ == "__main__":
    main()
