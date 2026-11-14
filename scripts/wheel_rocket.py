#!/usr/bin/env python3
"""The rocket district of every wheel (the Captain, 2026-11-13: fill the safe area inside the rim with more factories "doing useful
stuff", in sweeping circles and spirals, "creating goods for down below"). It stands in the south-west quadrant, a second spiral
south of the west spoke, and makes the three ingredients of a rocket part from chunks: rocket fuel, low density structure and
processing units, each up to CAP in the hub, where the planet's landing pad can take them.
  tap      three inserters south of the west spoke belt (y=-1): carbonic at -66,0 and oxide at -65,0 share belt in1 (a lane each:
           the carbonic stub turns into the belt, the oxide stub side-loads from the east), metallic at -67,0 has belt in2. The
           carbonic one works only while the hub holds more than SPARE carbon, so blue science keeps first call on carbon.
  spiral   a three-belt corridor (out-belt, in1, in2) from the spoke down x -65..-67, west along y 9..11, round the heart
           anticlockwise twice and in along y 59..61. Open space between the windings.
  heart    local 0,0 = wheel HX,HY; x -3..47, y 10..48. From the south: in2 (y 47), in1 (46), three crushers (carbonic, oxide,
           metallic, advanced) and a metallic reprocessor that hands oxide and carbonic chunks to them, dropping everything on the ore belt (y 41), which flows east past the two melting foundries, north up
           x 42, west along y 11, south down x -2 and out west along y 45: the out-belt. Nothing ends there: leftovers ride to the hub.
           A closed, counted loop belt (x 15..40, y 17..27) carries carbon, sulfur and calcite (lifted off the out-belt at x 41),
           coal, plastic, iron plate, copper cable, both circuits, solid fuel and the three products; every producer's inserter works
           only while the loop holds fewer than TARGETS of its item. The three products leave the loop for the out-belt at x 41 while
           the hub holds fewer than CAP of them.
           chemistry inside the loop, port to port where it can: acid plant -> refinery (simple coal liquefaction) -> heavy cracking
           -> light cracking -> plastic; coal plant under the acid plant; solid fuel and the rocket fuel assembler on the light oil;
           water from an ice melter east of the out-belt, by a main along y 26
           metal under the loop: iron and copper melters on the ore belt, pipe row y 34, casting foundries for iron plate, low density
           structure (plastic + both molten metals) and copper cable
           above the loop: processing unit (acid by a pipe under the loop's top row), electronic circuit, advanced circuit
  gates    crusher intakes: carbonic while the loop has less than its carbon target; oxide while the ice melter holds fewer than 20
           ice; metallic while the copper melter holds fewer than 50 copper ore
Never apply twice on the same wheel. After a quality upgrade run `config` (belt readers and over-reach wires).
Steps on every wheel (--only PLANET): check | build [--apply] | refit [--apply] | config | status.
Usage: wheel_rocket.py check | build [--apply] | config | status  [--only PLANET]"""
import sys

from _game import tools
from _wheels import lay_foundation, place_all, wheels

Q = {"quality": "epic"}
N, E, S, W = 0, 4, 8, 12
DIR = {(0, -1): N, (1, 0): E, (0, 1): S, (-1, 0): W}
HX, HY = -131, 14
CAP, SPARE = 2000, 5000
TARGETS = {"carbon": 40, "sulfur": 20, "calcite": 10, "coal": 30, "plastic-bar": 30, "iron-plate": 30, "copper-cable": 60,
           "electronic-circuit": 40, "advanced-circuit": 10, "solid-fuel": 30, "rocket-fuel": 4, "low-density-structure": 4, "processing-unit": 4}
PRODUCTS = ["rocket-fuel", "low-density-structure", "processing-unit"]
ents, cfg, recipes, occ, tiles, fluid, opening = [], [], [], {}, set(), {}, {}
loop_tiles, gated, exports = [], [], []


def put(name, tx, ty, w=1, h=1, d=N, filt=None, recipe=None, local=True, **params):
    if local:
        tx, ty = tx + HX, ty + HY
    for c in [(tx + i, ty + j) for i in range(w) for j in range(h)]:
        assert c not in occ, "%s at %s overlaps %s" % (name, c, occ[c])
        occ[c] = name
    for x in range(tx - 1, tx + w + 1):
        for y in range(ty - 1, ty + h + 1):
            tiles.add((x, y))
    e = {"name": name, "x": tx + w / 2, "y": ty + h / 2, "direction": d, "params": dict(Q, **params)}
    ents.append(e)
    if filt:
        cfg.append((e["x"], e["y"], filt))
    if recipe:
        recipes.append((e["x"], e["y"], recipe))
    return e


def sgn(a):
    return (a > 0) - (a < 0)


def poly(corners):
    out = [corners[0]]
    for a, b in zip(corners, corners[1:]):
        dx, dy = sgn(b[0] - a[0]), sgn(b[1] - a[1])
        assert (dx == 0) != (dy == 0), "corners %s %s" % (a, b)
        c = a
        while c != b:
            c = (c[0] + dx, c[1] + dy)
            out.append(c)
    return out


def belts(path, end, closed=False, local=False):
    n = len(path)
    for i, t in enumerate(path):
        nx = path[(i + 1) % n] if (closed or i + 1 < n) else None
        d = end if nx is None else DIR[(nx[0] - t[0], nx[1] - t[1])]
        put("express-transport-belt", t[0], t[1], d=d, local=local)


def ins(x, y, d, filt=None, name="fast-inserter", local=True):
    return put(name, x, y, d=d, filt=filt, local=local)


def pipe(f, *ts):
    for x, y in ts:
        put("pipe", x, y)
        fluid[(x, y)] = f


def ptg(f, x, y, d):
    put("pipe-to-ground", x, y, d=d)
    fluid[(x, y)] = f
    opening[(x, y)] = {v: k for k, v in DIR.items()}[d]


def gate(e, item):
    gated.append((e["x"], e["y"], item, TARGETS[item]))


def h(x, y):
    return (x + HX, y + HY)


# corridor, wheel coordinates, in the in-belts' direction of travel
IN1 = [(-66, 1), (-66, 10), (-146, 10), (-146, 67), (-77, 67), (-77, 17), (-139, 17), (-139, 60), h(16, 46)]
IN2 = [(-67, 1), (-67, 9), (-147, 9), (-147, 68), (-76, 68), (-76, 16), (-140, 16), (-140, 61), h(16, 47)]
OUT = [h(3, 41), h(42, 41), h(42, 11), h(-2, 11), h(-2, 45), (-138, 59), (-138, 18), (-78, 18), (-78, 66), (-145, 66), (-145, 11), (-65, 11), (-65, 3),
       (-56, 3), (-56, 2)]


def layout():
    # ---- the three long belts and the tap ----
    belts(poly(OUT), N)                                                   # ends pointing north: side-loads onto the spiral's out-belt at -56,1
    belts(poly(IN1), E)
    belts(poly(IN2), E)
    put("express-transport-belt", -65, 1, d=W, local=False)               # oxide stub: side-loads onto in1's first tile from the east
    ins(-66, 0, N, ["carbonic-asteroid-chunk"], name="bulk-inserter", local=False)
    ins(-65, 0, N, ["oxide-asteroid-chunk"], name="bulk-inserter", local=False)
    ins(-67, 0, N, ["metallic-asteroid-chunk"], name="bulk-inserter", local=False)
    # ---- crushers ----
    for x, kind, long in ((1, "carbonic", False), (9, "oxide", False), (13, "metallic", True)):
        put("crusher", x, 43, 3, 2, d=E, recipe="advanced-%s-asteroid-crushing" % kind)
        ins(x, 45, S, ["%s-asteroid-chunk" % kind], name="long-handed-inserter" if long else "fast-inserter")
        ins(x + 2, 42, S)
    # the reshuffler: the west spoke brings about five metallic chunks for every oxide one and the district is short of water, so
    # spare metallic chunks are reprocessed; oxide chunks go straight into the oxide crusher, carbonic ones into the carbonic
    # crusher, and whatever is left over rides the ore belt out (never a full output)
    put("crusher", 5, 43, 3, 2, d=E, recipe="metallic-asteroid-reprocessing")
    ins(5, 45, S, ["metallic-asteroid-chunk"], name="long-handed-inserter")
    ins(6, 42, S, ["metallic-asteroid-chunk", "carbonic-asteroid-chunk"])
    ins(8, 43, W, ["oxide-asteroid-chunk"])
    ins(4, 43, E, ["carbonic-asteroid-chunk"])
    # ---- metal: melters on the ore belt, pipe row, casters under the loop ----
    put("foundry", 26, 35, 5, 5, recipe="iron-ore-melting")
    ins(28, 40, S, ["iron-ore", "calcite"])
    put("foundry", 32, 35, 5, 5, recipe="copper-ore-melting")
    ins(34, 40, S, ["copper-ore", "calcite"])
    pipe("iron", *[(x, 34) for x in range(23, 30)])
    pipe("copper", *[(x, 34) for x in range(31, 36)])
    put("foundry", 22, 29, 5, 5, recipe="casting-iron")
    gate(ins(24, 28, S), "iron-plate")
    put("foundry", 28, 29, 5, 5, recipe="casting-low-density-structure")
    ins(30, 28, N, ["plastic-bar"])
    gate(ins(31, 28, S), "low-density-structure")
    put("foundry", 34, 29, 5, 5, recipe="casting-copper-cable")
    gate(ins(36, 28, S), "copper-cable")
    # ---- the counted loop ----
    loop = [h(x, y) for x, y in poly([(15, 17), (40, 17), (40, 27), (15, 27), (15, 17)])[:-1]]
    belts(loop, E, closed=True)
    loop_tiles.extend(loop)
    # ---- chemistry inside the loop ----
    put("chemical-plant", 18, 19, 3, 3, d=W, recipe="sulfuric-acid")
    ins(19, 18, N, ["sulfur", "iron-plate"])
    put("chemical-plant", 18, 22, 3, 3, d=W, recipe="coal-synthesis")
    ins(19, 25, S, ["carbon", "sulfur"], name="long-handed-inserter")
    gate(ins(20, 25, N, name="long-handed-inserter"), "coal")
    put("oil-refinery", 22, 20, 5, 5, d=E, recipe="simple-coal-liquefaction")
    ins(24, 19, N, ["coal", "calcite"], name="long-handed-inserter")
    put("chemical-plant", 29, 20, 3, 3, d=W, recipe="heavy-oil-cracking")
    put("chemical-plant", 33, 22, 3, 3, d=W, recipe="light-oil-cracking")
    put("chemical-plant", 36, 22, 3, 3, d=W, recipe="plastic-bar")
    ins(37, 25, S, ["coal"], name="long-handed-inserter")
    gate(ins(39, 23, W), "plastic-bar")
    put("chemical-plant", 33, 19, 3, 3, d=W, recipe="solid-fuel-from-light-oil")
    gate(ins(34, 18, S), "solid-fuel")
    put("assembling-machine-3", 36, 19, 3, 3, d=N, recipe="rocket-fuel")
    ins(38, 18, N, ["solid-fuel"])
    gate(ins(39, 20, W), "rocket-fuel")
    # ---- above the loop ----
    put("assembling-machine-3", 20, 13, 3, 3, d=S, recipe="processing-unit")
    ins(20, 16, S, ["electronic-circuit", "advanced-circuit"])
    gate(ins(22, 16, N), "processing-unit")
    put("assembling-machine-3", 24, 13, 3, 3, recipe="electronic-circuit")
    ins(24, 16, S, ["iron-plate", "copper-cable"])
    gate(ins(26, 16, N), "electronic-circuit")
    put("assembling-machine-3", 28, 13, 3, 3, recipe="advanced-circuit")
    ins(28, 16, S, ["plastic-bar", "copper-cable", "electronic-circuit"])
    gate(ins(30, 16, N), "advanced-circuit")
    # ---- between the loop and the out-belt: raw in, products out ----
    for y, item in ((18, "carbon"), (19, "sulfur"), (21, "calcite")):
        gate(ins(41, y, E, [item]), item)
    for y, item in ((22, "rocket-fuel"), (24, "low-density-structure"), (25, "processing-unit")):
        e = ins(41, y, W, [item])
        exports.append((e["x"], e["y"], item))
    # ---- fluids ----
    put("chemical-plant", 44, 26, 3, 3, d=E, recipe="ice-melting")
    ins(43, 27, W, ["ice"])
    ptg("water", 43, 26, E)
    ptg("water", 39, 26, W)
    pipe("water", *[(x, 26) for x in range(17, 39)], (32, 25), (32, 24), (28, 25), (28, 24), (28, 23), (28, 22), (17, 25), (17, 24), (17, 23), (17, 22), (17, 21))
    pipe("acid", (21, 21), (21, 20))
    ptg("acid", 21, 19, S)
    ptg("acid", 21, 16, N)
    pipe("heavy", (27, 20), (28, 20))
    pipe("light", (32, 22), (32, 21), (32, 18), (37, 18))
    ptg("light", 32, 20, S)
    ptg("light", 32, 19, N)
    ptg("light", 33, 18, W)
    ptg("light", 36, 18, E)
    for (x, y), f in fluid.items():
        for dx, dy in DIR:
            n = (x + dx, y + dy)
            g = fluid.get(n)
            joins = opening.get((x, y), (dx, dy)) == (dx, dy) and opening.get(n, (-dx, -dy)) == (-dx, -dy)
            assert g is None or g == f or not joins, "%s pipe at %s touches %s" % (f, (x, y), g)
    for x in range(-3, 48):                                               # the heart is one solid chamber
        for y in range(10, 49):
            tiles.add(h(x, y))
    # ---- lamps along the corridor's outer edge ----
    path = poly(IN2[:-1])
    for i, (x, y) in enumerate(path[:-1]):
        dx, dy = path[i + 1][0] - x, path[i + 1][1] - y
        c = (x - dy, y + dx)                                              # right of travel: outside the corridor
        if i % 6 == 3 and c not in occ and c in tiles:
            put("small-lamp", c[0], c[1], local=False)
    return {"entities": len(ents), "tiles": len(tiles), "loop": len(loop_tiles), "x": (min(t[0] for t in tiles), max(t[0] for t in tiles)), "y": (min(t[1] for t in tiles), max(t[1] for t in tiles))}


def lua_list(rows):
    return "{" + ",".join("{" + ",".join(("'%s'" % v) if isinstance(v, str) else ("{" + ",".join("'%s'" % f for f in v) + "}") if isinstance(v, list) else str(v) for v in r) + "}" for r in rows) + "}"


# THE DISTRICT YIELDS TO GREEN SCIENCE (2026-11-13): the metallic and oxide taps sit upstream of the spiral's taps (x -54, -55) on the west spoke
# and once took every chunk the spiral needed (green science fell to 0 on three wheels). They now work only while the last tile of the
# spiral's in-belt (the dead end by the crusher intakes, read in hold mode over a long wire) holds 4 or more of their chunk: the spiral's belt is
# full to the end, so what the district takes is surplus. Carbon (hub stock over SPARE) is unchanged.
# Step `refit` (once, on wheels built before the reshuffler): takes out the old oxide and metallic crushers and their inserters (what
# they hold goes into the hub) and places everything of the layout that is not standing yet.
REFIT = ("local s=game.surfaces['SURF'] local hub=s.platform.hub local n=0 for _,p in pairs(OLD) do for _,e in pairs(s.find_entities_filtered{position=p,radius=0.3,type={'assembling-machine','inserter'}}) do "
         "if e.type=='inserter' then if e.held_stack.valid_for_read then hub.insert{name=e.held_stack.name,count=e.held_stack.count} end else for _,id in pairs{defines.inventory.crafter_input,defines.inventory.crafter_output} do local inv=e.get_inventory(id) if inv then for _,it in pairs(inv.get_contents()) do hub.insert{name=it.name,count=it.count,quality=it.quality} end end end end e.destroy() n=n+1 end end rcon.print('old pieces removed '..n)")
LAMPS = "local s=game.surfaces['SURF'] local n=0 for _,p in pairs(CELLS) do for _,e in pairs(s.find_entities_filtered{type='lamp',position=p,radius=0.3}) do e.destroy() n=n+1 end end rcon.print('lamps in the way removed '..n)"
CONFIG = ("local s=game.surfaces['SURF'] local hub=s.platform.hub local W=defines.wire_connector_id local o={} local function at(t,x,y) return s.find_entities_filtered{type=t,position={x,y},radius=0.3}[1] end local n,r=0,0 "
          "local function mach(x,y) return s.find_entities_filtered{type='assembling-machine',position={x,y},radius=0.5}[1] end pcall(function() hub.get_or_create_control_behavior().read_contents=true end) "
          "for _,q in pairs(FILT) do local i=at('inserter',q[1],q[2]) if i then i.use_filters=true i.inserter_filter_mode='whitelist' for k,name in pairs(q[3]) do i.set_filter(k,name) end n=n+1 end end "
          "for _,q in pairs(REC) do local m=mach(q[1],q[2]) if m then m.set_recipe(q[3]) r=r+1 end end o[#o+1]='filters '..n..', recipes '..r "
          "local prev,nb=nil,0 for _,p in pairs(LOOP) do local b=at('transport-belt',p[1]+0.5,p[2]+0.5) if b then local bc=b.get_or_create_control_behavior() bc.read_contents=true bc.read_contents_mode=defines.control_behavior.transport_belt.content_read_mode.hold "
          "if prev then b.get_wire_connector(W.circuit_red,true).connect_to(prev.get_wire_connector(W.circuit_red,true),false) end prev=b nb=nb+1 end end o[#o+1]='loop belts read '..nb "
          "local function cond(i,sig,cmp,k,wire,target,twire) i.get_wire_connector(wire,true).connect_to(target.get_wire_connector(twire or wire,true),false) local cb=i.get_or_create_control_behavior() cb.circuit_enable_disable=true cb.circuit_condition={first_signal={type='item',name=sig},comparator=cmp,constant=k} end "
          "local g=0 for _,q in pairs(GATED) do local i=at('inserter',q[1],q[2]) if i then cond(i,q[3],'<',q[4],W.circuit_red,prev) g=g+1 end end o[#o+1]='gated on the loop '..g "
          "local x=0 for _,q in pairs(EXPORTS) do local i=at('inserter',q[1],q[2]) if i then cond(i,q[3],'<',CAP,W.circuit_red,hub) x=x+1 end end o[#o+1]='exports gated on the hub '..x "
          "cond(at('inserter',-65.5,0.5),'carbon','>',SPARE,W.circuit_red,hub) "
          "local ib=nil for x=-90,-112,-1 do ib=ib or s.find_entities_filtered{type='transport-belt',position={x+0.5,-26.5},radius=0.3}[1] end if ib then local bc=ib.get_or_create_control_behavior() bc.read_contents=true bc.read_contents_mode=defines.control_behavior.transport_belt.content_read_mode.hold "
          "for _,x in pairs{-66.5,-64.5} do at('inserter',x,0.5).get_wire_connector(W.circuit_red,true).disconnect_all() end "
          "cond(at('inserter',-66.5,0.5),'metallic-asteroid-chunk','>=',4,W.circuit_red,ib) cond(at('inserter',-64.5,0.5),'oxide-asteroid-chunk','>=',4,W.circuit_red,ib) o[#o+1]='metallic and oxide taps follow the spiral in-belt end' else o[#o+1]='NO in-belt end found' end "
          "cond(at('inserter',CX,CY),'carbon','<',CARBON,W.circuit_red,prev) cond(at('inserter',RX,RY),'ice','<',20,W.circuit_green,mach(WX,WY)) "
          "local melt=mach(WX,WY) melt.get_or_create_control_behavior().circuit_read_contents=true cond(at('inserter',OX,OY),'ice','<',20,W.circuit_green,melt) "
          "local cu=mach(MX,MY) cu.get_or_create_control_behavior().circuit_read_contents=true cond(at('inserter',TX,TY),'copper-ore','<',50,W.circuit_green,cu) o[#o+1]='tap and crusher gates set' rcon.print(table.concat(o,', '))")
STATUS = ("local s=game.surfaces['SURF'] local st={} for _,c in pairs(s.find_entities_filtered{type='assembling-machine',area={{X0,Y0},{X1,Y1}}}) do local k='?' for n,v in pairs(defines.entity_status) do if v==c.status then k=n end end "
          "local rc=c.get_recipe() k=(rc and rc.name or c.name)..' '..k st[k]=(st[k] or 0)+1 end local o={} for k,v in pairs(st) do o[#o+1]=k..' '..v end table.sort(o) "
          "local b={} for _,p in pairs(RING) do local e=s.find_entities_filtered{type='transport-belt',position={p[1]+0.5,p[2]+0.5},radius=0.3}[1] if e then for l=1,2 do for _,it in pairs(e.get_transport_line(l).get_contents()) do b[it.name]=(b[it.name] or 0)+it.count end end end end "
          "local q={} for k,v in pairs(b) do q[#q+1]=k..' '..v end table.sort(q) local f=game.forces.player.get_item_production_statistics(s) local inv=s.platform.hub.get_inventory(defines.inventory.hub_main) local p={} "
          "for _,n in pairs{'rocket-fuel','low-density-structure','processing-unit'} do p[#p+1]=n..' '..string.format('%.1f',f.get_flow_count{name=n,category='input',precision_index=defines.flow_precision_index.ten_minutes})..' a minute (10 min), in hub '..inv.get_item_count(n) end "
          "rcon.print(table.concat(o,' ; ')..' ; ON THE LOOP '..table.concat(q,', ')..' ; '..table.concat(p,' ; ')..' ; carbon in hub '..inv.get_item_count('carbon'))")


def main():
    step = sys.argv[1]
    apply = "--apply" in sys.argv
    print(layout())
    if step == "check":
        return
    hc = lambda x, y: (x + HX + .5, y + HY + .5)
    for name, planet, surface, turrets in wheels():
        print("==", name, surface or "(not created)")
        if not surface:
            continue
        if step == "build":
            if apply:
                print(tools["run_lua"](LAMPS.replace("SURF", surface).replace("CELLS", "{" + ",".join("{%s,%s}" % (x + .5, y + .5) for x, y in sorted(occ)) + "}")))
                print("deck tiles", lay_foundation(tiles, surface))
            ok, bad = place_all(ents, surface, apply)
            print("placed" if apply else "dry run", ok, "failed", bad)
        if step == "refit":
            old = [hc(6, 43), hc(10, 43), hc(5, 45), hc(7, 42), hc(9, 45), hc(11, 42)]
            if apply:
                print(tools["run_lua"](REFIT.replace("SURF", surface).replace("OLD", "{" + ",".join("{%s,%s}" % q for q in old) + "}")))
                print("deck tiles", lay_foundation(tiles, surface))
            have = tools["run_lua"]("local s=game.surfaces['%s'] local t={} for _,p in pairs({%s}) do t[#t+1]=s.count_entities_filtered{position=p,radius=0.2} end rcon.print(table.concat(t,','))"
                                    % (surface, ",".join("{%s,%s}" % (e["x"], e["y"]) for e in ents))).strip().split(",")
            todo = [e for e, hv in zip(ents, have) if hv == "0"]
            ok, bad = place_all(todo, surface, apply)
            print("missing pieces", len(todo), "placed" if apply else "dry run", ok, "failed", bad)
        if step == "config" or (step in ("build", "refit") and apply):
            code = (CONFIG.replace("SURF", surface).replace("FILT", lua_list([(x, y, fl) for x, y, fl in cfg])).replace("REC", lua_list(recipes))
                    .replace("LOOP", lua_list(loop_tiles)).replace("GATED", lua_list(gated)).replace("EXPORTS", lua_list(exports))
                    .replace("CAP", str(CAP)).replace("SPARE", str(SPARE)).replace("CARBON", str(TARGETS["carbon"]))
                    .replace("CX", str(hc(1, 45)[0])).replace("CY", str(hc(1, 45)[1])).replace("OX", str(hc(9, 45)[0])).replace("OY", str(hc(9, 45)[1]))
                    .replace("TX", str(hc(13, 45)[0])).replace("TY", str(hc(13, 45)[1])).replace("RX", str(hc(5, 45)[0])).replace("RY", str(hc(5, 45)[1])).replace("WX", str(HX + 45.5)).replace("WY", str(HY + 27.5))
                    .replace("MX", str(HX + 34.5)).replace("MY", str(HY + 37.5)))
            print(tools["run_lua"](code))
        elif step == "status":
            print(tools["run_lua"](STATUS.replace("SURF", surface).replace("RING", lua_list(loop_tiles)).replace("X0", str(HX - 3)).replace("Y0", str(HY + 10))
                                   .replace("X1", str(HX + 48)).replace("Y1", str(HY + 49))).replace(" ; ", "\n"))


if __name__ == "__main__":
    main()
