#!/usr/bin/env python3
"""Military (grey) and production (purple) science on every wheel: "the Ring" (the Captain, 2026-11-13: ship stone up to the wheel
factories, it is the one thing asteroids cannot give; and fill the inside of the wheels with machines in circles, not rectangles).
A round island of deck north of the blue block (scripts/wheel_blue.py), centre CX,CY, with one closed belt on it: four straight
flats joined by four stepped diagonals, running clockwise. Machines stand on the flats, inside and outside.
  supply   three inserters at 95..97,-42 take iron plate, copper plate and coal off the K loop's north row (y=-41, the blue
           block's edge); two at 104..105,-33 take stone and steel plate off the ore loop round the blue cluster (the O line
           carries them since this script: TARGETS in wheel_blue.py). Both feed one stub that side-loads onto the ring's south flat. Petroleum gas for plastic comes from the blue block's gas row (102,-26)
           by pipe: north under the K row (y=-30) and the ore row, north again under the K row (y=-41), round to the plastic plant.
  ring     a counted loop like the spiral's heart: every belt tile is read (hold) on one red wire; every inserter that PUTS
           something on the ring works only while the ring holds fewer than TARGETS of that item. So no item can crowd out the
           others and a missing ingredient (no stone yet) only idles its own machines.
  machines south flat inside: brick furnace, wall, electric furnace (the item); outside: iron stick
           north flat inside: firearm magazine, piercing magazine, grenade; outside: copper cable, electronic circuit, advanced circuit
           east flat inside: rail, productivity module; outside: plastic (chemical plant, facing south, gas into its south edge)
           west flat outside: military science, production science: their output goes west onto a pack belt of its own
  packs    the pack belt runs down column 73, west along y=-43 and south down column 68 (the gap between the coal plants), under
           the K rows, the water main and the ore feed, and side-loads onto the blue line's pack belt at 68,-15, which enters the hub
  coal     the ring's coal inserter works only while the K loop holds more than SPARE coal (a decider reads K's own count and the
           ring's): grenades and plastic took the coal and gas blue science lives on, and it fell to nothing on the wheels with stone.
           Four more coal plants at 73..87,-34..-32 beside the blue block's four, on the same water main and the same K row: the
           ring's grenades and plastic took about half of the coal and blue science fell from about 11 a minute to 3
  cap      the two science assemblers' intake inserters are wired to the hub and stop above PACKS packs of their kind
Stone: about 10 a military pack (2 walls = 10 bricks = 20 stone for 2 packs) and about 12 a production pack (30 rails = 15 stone,
10 bricks = 20 stone, for 3 packs).
Steps on every wheel (--only PLANET): check | build [--apply] | config | status. Never apply twice. After a quality upgrade: config.
Run `wheel_blue.py config` once after changing its TARGETS.
Usage: wheel_grey_purple.py check | build [--apply] | config | status  [--only PLANET]"""
import math
import sys

from _game import tools
from _wheels import lay_foundation, place_all, wheels

Q = {"quality": "epic"}
N, E, S, W = 0, 4, 8, 12
DIR = {(0, -1): N, (1, 0): E, (0, 1): S, (-1, 0): W}
CX, CY, R, F = 92, -60, 13, 6
PACKS = 20000
SPARE = 150      # the ring takes coal only while the K loop carries more than this: blue science has first call on coal
TARGETS = {"stone": 30, "steel-plate": 30, "iron-plate": 40, "copper-plate": 30, "coal": 20, "stone-brick": 30, "stone-wall": 8,
           "firearm-magazine": 6, "piercing-rounds-magazine": 6, "grenade": 6, "iron-stick": 16, "rail": 60, "electric-furnace": 2,
           "copper-cable": 30, "electronic-circuit": 20, "plastic-bar": 12, "advanced-circuit": 12, "productivity-module": 2}
ents, cfg, recipes, gated, hubgate, occ, tiles, ring = [], [], [], [], [], {}, set(), []
A = "assembling-machine-3"


def put(name, tx, ty, w=1, h=1, d=N, filt=None, recipe=None, **params):
    for c in [(tx + i, ty + j) for i in range(w) for j in range(h)]:
        assert c not in occ, "%s at %s overlaps %s" % (name, c, occ[c])
        occ[c] = name
        if ty < -41:                                  # new deck only north of the blue block
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if c[1] + dy < -41:
                        tiles.add((c[0] + dx, c[1] + dy))
    e = {"name": name, "x": tx + w / 2, "y": ty + h / 2, "direction": d, "params": dict(Q, **params)}
    ents.append(e)
    if filt:
        cfg.append((e["x"], e["y"], filt))
    if recipe:
        recipes.append((e["x"], e["y"], recipe))
    return e


def ins(x, y, d, filt=None, target=None):
    e = put("fast-inserter", x, y, d=d, filt=filt)
    if target:
        gated.append((e["x"], e["y"], target, TARGETS[target]))
    return e


def ring_path():
    p = [(x, CY - R) for x in range(CX - F, CX + F + 1)]
    for k in range(1, R - F + 1):
        p += [(CX + F + k, CY - R + k - 1), (CX + F + k, CY - R + k)]
    p += [(CX + R, y) for y in range(CY - F + 1, CY + F + 1)]
    for k in range(1, R - F + 1):
        p += [(CX + R - k + 1, CY + F + k), (CX + R - k, CY + F + k)]
    p += [(x, CY + R) for x in range(CX + F - 1, CX - F - 1, -1)]
    for k in range(1, R - F + 1):
        p += [(CX - F - k, CY + R - k + 1), (CX - F - k, CY + R - k)]
    p += [(CX - R, y) for y in range(CY + F - 1, CY - F - 1, -1)]
    for k in range(1, R - F + 1):
        p += [(CX - R + k - 1, CY - F - k), (CX - R + k, CY - F - k)]
    out = []
    for t in p:
        if t not in out:
            out.append(t)
    return out


def belts(path, end, kinds=None):
    kinds = kinds or {}
    for i, t in enumerate(path):
        d = DIR[(path[i + 1][0] - t[0], path[i + 1][1] - t[1])] if i + 1 < len(path) and kinds.get(t) != "in" else end
        if kinds.get(t) == "in":
            nx = path[i + 1]
            d = DIR[((nx[0] > t[0]) - (nx[0] < t[0]), (nx[1] > t[1]) - (nx[1] < t[1]))]
            put("express-underground-belt", t[0], t[1], d=d, type="input")
        elif kinds.get(t) == "out":
            pv = path[i - 1]
            put("express-underground-belt", t[0], t[1], d=DIR[((t[0] > pv[0]) - (t[0] < pv[0]), (t[1] > pv[1]) - (t[1] < pv[1]))], type="output")
        else:
            put("express-transport-belt", t[0], t[1], d=d)


def machine(side, inside, slot, name, recipe, takes, makes, hub=None):
    """side N/E/S/W flat; slot 0..2 along it; an intake inserter on the first tile and an output inserter on the third."""
    off = (-5, -1, 3)[slot]
    sgn = -1 if inside else 1                       # outside: away from the centre
    if side in ("N", "S"):
        by = CY - R if side == "N" else CY + R
        out = -1 if side == "N" else 1              # outward direction in y
        iy = by + out * sgn                         # inserter row
        my = by + out * sgn * 2 if out * sgn > 0 else by + out * sgn * 4      # machine's top row
        x0 = CX + off
        put(name, x0, my, 3, 3, d=S if name == "chemical-plant" else N, recipe=recipe)
        toward_belt = N if iy > by else S           # inserter direction = its pickup side
        e = ins(x0, iy, toward_belt, takes)
        if hub:
            hubgate.append((e["x"], e["y"], hub))
        return ins(x0 + 2, iy, S if toward_belt == N else N, [makes], None if hub else makes), (x0, my)
    bx = CX + R if side == "E" else CX - R
    out = 1 if side == "E" else -1
    ix = bx + out * sgn
    mx = bx + out * sgn * 2 if out * sgn > 0 else bx + out * sgn * 4
    y0 = CY + off
    put(name, mx, y0, 3, 3, d=S if name == "chemical-plant" else N, recipe=recipe)
    toward_belt = W if ix > bx else E
    e = ins(ix, y0, toward_belt, takes)
    if hub:
        hubgate.append((e["x"], e["y"], hub))
        return None, (mx, y0)                       # science: its output goes to the pack belt, placed by the caller
    return ins(ix, y0 + 2, E if toward_belt == W else W, [makes], makes), (mx, y0)


def layout():
    ring.extend(ring_path())
    for i, t in enumerate(ring):
        nx = ring[(i + 1) % len(ring)]
        put("express-transport-belt", t[0], t[1], d=DIR[(nx[0] - t[0], nx[1] - t[1])])
    # --- supply from the K loop's north row (y=-41) ---
    for x, item in ((95, "iron-plate"), (96, "copper-plate"), (97, "coal")):
        ins(x, -42, S, [item], item)
    put("decider-combinator", 98, -42, 2, 1, d=E)                         # the coal tap's two conditions (SPARE on K, room on the ring)
    # stone and steel plate come off the ore loop round the blue cluster (its north row, y=-32): a line's hub inserter has only five
    # filter slots and K already carries five items; the first build put them on K and starved it of sulfur
    ins(104, -33, S, ["stone"], "stone")
    ins(105, -33, S, ["steel-plate"], "steel-plate")
    belts([(105, -34), (104, -34), (104, -35), (104, -36), (104, -37), (104, -38), (104, -39), (104, -40), (104, -42), (104, -43), (103, -43), (101, -43),
           (100, -43), (99, -43), (98, -43), (97, -43), (96, -43), (95, -43), (94, -43), (93, -43), (92, -43), (92, -44), (92, -45), (92, -46)], N,
          kinds={(104, -40): "in", (104, -42): "out", (103, -43): "in", (101, -43): "out"})
    # --- machines ---
    machine("S", True, 0, "electric-furnace", None, ["stone"], "stone-brick")
    machine("S", True, 1, A, "stone-wall", ["stone-brick"], "stone-wall")
    machine("S", True, 2, A, "electric-furnace", ["steel-plate", "advanced-circuit", "stone-brick"], "electric-furnace")
    machine("S", False, 0, A, "iron-stick", ["iron-plate"], "iron-stick")
    machine("N", True, 0, A, "firearm-magazine", ["iron-plate"], "firearm-magazine")
    machine("N", True, 1, A, "piercing-rounds-magazine", ["firearm-magazine", "steel-plate", "copper-plate"], "piercing-rounds-magazine")
    machine("N", True, 2, A, "grenade", ["iron-plate", "coal"], "grenade")
    machine("N", False, 0, A, "copper-cable", ["copper-plate"], "copper-cable")
    machine("N", False, 1, A, "electronic-circuit", ["iron-plate", "copper-cable"], "electronic-circuit")
    machine("N", False, 2, A, "advanced-circuit", ["electronic-circuit", "plastic-bar", "copper-cable"], "advanced-circuit")
    machine("E", True, 0, A, "rail", ["stone", "steel-plate", "iron-stick"], "rail")
    machine("E", True, 1, A, "productivity-module", ["advanced-circuit", "electronic-circuit"], "productivity-module")
    machine("E", False, 2, "chemical-plant", "plastic-bar", ["coal"], "plastic-bar")
    for slot, rec, takes in ((0, "military-science-pack", ["piercing-rounds-magazine", "grenade", "stone-wall"]),
                             (1, "production-science-pack", ["rail", "electric-furnace", "productivity-module"])):
        _, (mx, y0) = machine("W", False, slot, A, rec, takes, rec, hub=rec)
        ins(mx - 1, y0 + 1, E, [rec])                                     # packs out to the west, onto the pack belt
    # --- pack belt: column 73, row -43, column 68 down to the blue pack belt ---
    px = CX - R - 6
    path = [(px, y) for y in range(CY - 6, -43)] + [(x, -43) for x in range(px, 68, -1)] + [(68, -43), (68, -42), (68, -40)] + \
           [(68, -39), (68, -38), (68, -37), (68, -36), (68, -34), (68, -33), (68, -32), (68, -31), (68, -29)] + \
           [(68, y) for y in range(-28, -24)] + [(68, -24), (68, -20)] + [(68, y) for y in range(-19, -15)]
    belts(path, S, kinds={(68, -42): "in", (68, -40): "out", (68, -36): "in", (68, -34): "out", (68, -31): "in", (68, -29): "out", (68, -24): "in", (68, -20): "out"})
    # --- petroleum gas from the blue block ---
    for y in (-27, -28):
        put("pipe", 102, y)
    put("pipe-to-ground", 102, -29, d=S)
    put("pipe-to-ground", 102, -33, d=N)
    for y in range(-34, -40, -1):
        put("pipe", 102, y)
    put("pipe-to-ground", 102, -40, d=S)
    put("pipe-to-ground", 102, -42, d=N)
    for c in [(102, -43), (102, -44), (102, -45)] + [(x, -45) for x in range(103, 110)] + [(109, y) for y in range(-46, -55, -1)]:
        put("pipe", *c)
    # --- four more coal plants in the blue block, east of its four (grenades and plastic took half of the coal and blue science fell) ---
    for c in [(72, -36), (73, -36)] + [(x, -35) for x in range(73, 88)]:
        put("pipe", *c)                                                   # water, on from the main's end at 71,-36
    for x in (73, 77, 81, 85):
        put("chemical-plant", x, -34, 3, 3, recipe="coal-synthesis")
        put("fast-inserter", x, -31, d=S, filt=["carbon", "sulfur"])
        put("fast-inserter", x + 2, -31, d=N, filt=["coal"])              # coal onto the K row (y=-30), like the first four
    for x in range(CX - 21, CX + 22):                                    # the island is round
        for y in range(CY - 21, CY + 22):
            if math.hypot(x + .5 - CX - .5, y + .5 - CY - .5) <= 20.5 and y < -41:
                tiles.add((x, y))
    return {"entities": len(ents), "ring": len(ring), "deck tiles": len(tiles), "gated": len(gated)}


def lua_list(rows):
    return "{" + ",".join("{" + ",".join(("'%s'" % v) if isinstance(v, str) else ("{" + ",".join("'%s'" % f for f in v) + "}") if isinstance(v, list) else str(v) for v in r) + "}" for r in rows) + "}"


CONFIG = ("local s=game.surfaces['SURF'] local hub=s.platform.hub local W=defines.wire_connector_id local o={} local function at(t,x,y) return s.find_entities_filtered{type=t,position={x,y},radius=0.3}[1] end local n,r=0,0 "
          "for _,q in pairs(FILT) do local i=at('inserter',q[1],q[2]) if i then i.use_filters=true i.inserter_filter_mode='whitelist' local ok={} for k,name in pairs(q[3]) do i.set_filter(k,name) ok[name]=true end n=n+1 "
          "local h=i.held_stack if h.valid_for_read and not ok[h.name] then hub.insert{name=h.name,count=h.count,quality=h.quality} h.clear() end end end "
          "for _,q in pairs(REC) do local m=s.find_entities_filtered{type='assembling-machine',position={q[1],q[2]},radius=0.5}[1] if m then m.set_recipe(q[3]) r=r+1 end end o[#o+1]='filters '..n..', recipes '..r "
          "local prev,nb=nil,0 for _,p in pairs(LOOP) do local b=at('transport-belt',p[1]+0.5,p[2]+0.5) if b then local bc=b.get_or_create_control_behavior() bc.read_contents=true bc.read_contents_mode=defines.control_behavior.transport_belt.content_read_mode.hold "
          "if prev then b.get_wire_connector(W.circuit_red,true).connect_to(prev.get_wire_connector(W.circuit_red,true),false) end prev=b nb=nb+1 end end o[#o+1]='ring belts read '..nb "
          "local g=0 for _,q in pairs(GATED) do local i=at('inserter',q[1],q[2]) if i then local w=i.get_wire_connector(W.circuit_red,true) w.disconnect_all() w.connect_to(prev.get_wire_connector(W.circuit_red,true),false) local cb=i.get_or_create_control_behavior() cb.circuit_enable_disable=true "
          "cb.circuit_condition={first_signal={type='item',name=q[3]},comparator='<',constant=q[4]} g=g+1 end end o[#o+1]='ring inserters gated '..g "
          "pcall(function() hub.get_or_create_control_behavior().read_contents=true end) local hg=0 for _,q in pairs(HUBG) do local i=at('inserter',q[1],q[2]) if i then local w=i.get_wire_connector(W.circuit_red,true) w.disconnect_all() w.connect_to(hub.get_wire_connector(W.circuit_red,true),false) "
          "local cb=i.get_or_create_control_behavior() cb.circuit_enable_disable=true cb.circuit_condition={first_signal={type='item',name=q[3]},comparator='<',constant=PACKS} hg=hg+1 end end o[#o+1]='science intakes on the hub cap '..hg "
          "local dec=s.find_entities_filtered{name='decider-combinator',position={99,-41.5},radius=0.6}[1] local kb=at('transport-belt',97.5,-40.5) local ct=at('inserter',97.5,-41.5) if dec and kb and ct then "
          "for _,id in pairs{W.combinator_input_red,W.combinator_input_green,W.combinator_output_red,W.combinator_output_green} do dec.get_wire_connector(id,true).disconnect_all() end "
          "dec.get_wire_connector(W.combinator_input_green,true).connect_to(kb.get_wire_connector(W.circuit_green,true),false) dec.get_wire_connector(W.combinator_input_red,true).connect_to(prev.get_wire_connector(W.circuit_red,true),false) "
          "dec.get_or_create_control_behavior().parameters={conditions={{first_signal={type='item',name='coal'},first_signal_networks={red=false,green=true},comparator='>',constant=SPARE},"
          "{first_signal={type='item',name='coal'},first_signal_networks={red=true,green=false},comparator='<',constant=COALCAP,compare_type='and'}},outputs={{signal={type='virtual',name='signal-A'},copy_count_from_input=false,constant=1}}} "
          "local w=ct.get_wire_connector(W.circuit_red,true) w.disconnect_all() w.connect_to(dec.get_wire_connector(W.combinator_output_red,true),false) local cb=ct.get_or_create_control_behavior() cb.circuit_enable_disable=true "
          "cb.circuit_condition={first_signal={type='virtual',name='signal-A'},comparator='>',constant=0} o[#o+1]='coal tap on spare coal only' end rcon.print(table.concat(o,', '))").replace("PACKS", str(PACKS)).replace("SPARE", str(SPARE)).replace("COALCAP", str(TARGETS["coal"]))
STATUS = ("local s=game.surfaces['SURF'] local inv=s.platform.hub.get_inventory(defines.inventory.hub_main) local st={} for _,c in pairs(s.find_entities_filtered{type={'assembling-machine','furnace'},area={{CX-20,CY-20},{CX+20,CY+20}}}) do "
          "local k='?' for a,v in pairs(defines.entity_status) do if v==c.status then k=a end end local rc=c.type=='assembling-machine' and c.get_recipe() st[#st+1]=(rc and rc.name or 'brick furnace')..' '..k..' '..c.products_finished end table.sort(st) "
          "local b={} for _,p in pairs(LOOP) do local e=s.find_entities_filtered{type='transport-belt',position={p[1]+0.5,p[2]+0.5},radius=0.3}[1] if e then for l=1,2 do for _,it in pairs(e.get_transport_line(l).get_contents()) do b[it.name]=(b[it.name] or 0)+it.count end end end end "
          "local q={} for k,v in pairs(b) do q[#q+1]=k..' '..v end table.sort(q) local f=game.forces.player.get_item_production_statistics(s) local function fl(n,p) return string.format('%.1f',f.get_flow_count{name=n,category='input',precision_index=p}) end "
          "local M,T=defines.flow_precision_index.one_minute,defines.flow_precision_index.ten_minutes "
          "rcon.print(table.concat(st,' ; ')..' ;; ON THE RING '..table.concat(q,', ')..' ;; military a minute '..fl('military-science-pack',M)..' (10 min '..fl('military-science-pack',T)..'), in hub '..inv.get_item_count('military-science-pack')"
          "..' | production a minute '..fl('production-science-pack',M)..' (10 min '..fl('production-science-pack',T)..'), in hub '..inv.get_item_count('production-science-pack')..' | stone in hub '..inv.get_item_count('stone')..', steel '..inv.get_item_count('steel-plate'))")


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
        if step == "build":
            if apply:
                print("deck tiles", lay_foundation(tiles, surface))
            ok, bad = place_all(ents, surface, apply)
            print("placed" if apply else "dry run", ok, "failed", bad)
        if step == "config" or (step == "build" and apply):
            print(tools["run_lua"](CONFIG.replace("SURF", surface).replace("FILT", lua_list(cfg)).replace("REC", lua_list(recipes)).replace("LOOP", lua_list(ring))
                                   .replace("GATED", lua_list(gated)).replace("HUBG", lua_list(hubgate))))
        elif step == "status":
            print(tools["run_lua"](STATUS.replace("SURF", surface).replace("LOOP", lua_list(ring)).replace("CX", str(CX)).replace("CY", str(CY))).replace(" ;; ", "\n").replace(" ; ", "\n  "))


if __name__ == "__main__":
    main()
