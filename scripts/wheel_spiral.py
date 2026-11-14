#!/usr/bin/env python3
"""The spiral foundry district of every wheel (the Captain, 2026-11-13: "Foundries on the wheels ... Do it", "create new rings, new
spokes, new patterns ... a maze curling in upon itself, interesting and alien", "let's do the spiral pattern hub space stations").
It stands in the empty north-west quadrant, outside the round centre (radius 52) and north of the west spoke, and makes logistic
(green) science from molten metal. Nothing touches the hub edge: it lives off the west spoke belt and hands everything to the west
product belt.
  tap      two bulk inserters north of the spoke belt (y=-1) at x=-54 and -55 take metallic and oxide chunks; the metallic stub turns
           into the in-belt, the oxide stub side-loads onto it from the south, so each lane holds one kind and the dead end cannot jam
  spiral   a two-belt corridor (in-belt outside, out-belt inside, lamps on both edges, open space between the windings) from the spoke
           up column x=-56/-57 and 2 3/4 turns anticlockwise inward to the heart. About 580 tiles a belt.
  heart    x -108..-73, y -59..-26, from south to north:
           in-belt (y=-27) -> 2 metallic crushers + 1 oxide crusher (advanced) -> ore belt (y=-32) flowing east PAST the two melting
           foundries (iron at -91,-36; copper at -79,-36) and on as the out-belt, so surplus copper ore, ice and returned chunks leave
           molten iron by a pipe row (y=-39) to the plate and gear casting foundries, a tank beside it; molten copper to the cable foundry
           a closed loop belt (x -94..-76, y -52..-46) carries plates, gears, cable, circuits, inserters and belts; every producer's
           output inserter works only while the loop holds fewer than TARGETS of its item (belts read in hold mode, all on one red wire)
           inside the loop: 2 circuit assemblers, inserter assembler, belt assembler; above it: 2 science assemblers, packs onto the out-belt
  gates    metallic crusher intakes run while the tank holds less than IRON molten iron (green wire); the oxide intake while the two
           melters together hold fewer than CALCITE calcite (they read their contents onto a red wire)
  out      the out-belt runs back out beside the in-belt, under the solar band and the spoke belt, east along y=1, under the loop
           (x=-46) and side-loads onto the west product belt at -40,1. Two inserters at -52,0 and -50,0 lift returned chunks from it
           back onto the spoke belt.
Space platforms need no poles. The in-belt holds about 2,300 chunks a lane before it backs up: the first fill takes a while.
Steps on every wheel (--only gleba|nauvis): check | build [--apply] | config | status. Never apply twice on the same wheel.
Usage: wheel_spiral.py check | build [--apply] | config | status  [--only PLANET]"""
import sys

from _game import tools
from _wheels import lay_foundation, place_all, wheels

Q = {"quality": "epic"}
N, E, S, W = 0, 4, 8, 12
DIR = {(0, -1): N, (1, 0): E, (0, 1): S, (-1, 0): W}
TARGETS = {"iron-plate": 60, "iron-gear-wheel": 40, "copper-cable": 60, "electronic-circuit": 30, "inserter": 16, "transport-belt": 16}
IRON, CALCITE = 15000, 6
CHUNKS = ["metallic-asteroid-chunk", "carbonic-asteroid-chunk", "oxide-asteroid-chunk"]
ents, cfg, recipes, occ, tiles = [], [], [], {}, set()
loop_tiles, gated = [], []                       # loop belt positions; (x, y, item) of the output inserters on the counted loop


def put(name, tx, ty, w=1, h=1, d=N, filt=None, recipe=None, margin=True, **params):
    for c in [(tx + i, ty + j) for i in range(w) for j in range(h)]:
        assert c not in occ, "%s at %s overlaps %s" % (name, c, occ[c])
        occ[c] = name
    m = 1 if margin else 0
    for x in range(tx - m, tx + w + m):
        for y in range(ty - m, ty + h + m):
            tiles.add((x, y))
    p = dict(Q)
    p.update(params)
    e = {"name": name, "x": tx + w / 2, "y": ty + h / 2, "direction": d, "params": p}
    ents.append(e)
    if filt:
        cfg.append((e["x"], e["y"], filt))
    if recipe:
        recipes.append((e["x"], e["y"], recipe))
    return e


def sgn(a):
    return (a > 0) - (a < 0)


def poly(corners):
    """Tiles along a rectilinear polyline through the corner tiles, each once."""
    out = [corners[0]]
    for a, b in zip(corners, corners[1:]):
        dx, dy = sgn(b[0] - a[0]), sgn(b[1] - a[1])
        assert (dx == 0) != (dy == 0), "corners %s %s" % (a, b)
        c = a
        while c != b:
            c = (c[0] + dx, c[1] + dy)
            out.append(c)
    return out


def belts(path, end, closed=False):
    """A belt on every tile of the path, each pointing at the next; ('in'/'out', x, y, d) entries are underground ends."""
    n = len(path)
    for i, t in enumerate(path):
        if t[0] in ("in", "out"):
            put("express-underground-belt", t[1], t[2], d=t[3], type="input" if t[0] == "in" else "output")
            continue
        nx = path[(i + 1) % n] if (closed or i + 1 < n) else None
        if nx is None:
            d = end
        elif nx[0] in ("in", "out"):
            d = DIR[(sgn(nx[1] - t[0]), sgn(nx[2] - t[1]))]
        else:
            d = DIR[(nx[0] - t[0], nx[1] - t[1])]
        put("express-transport-belt", t[0], t[1], d=d)


def ins(x, y, d, filt=None, name="fast-inserter"):
    return put(name, x, y, d=d, filt=filt)


OUT = [(-105, -32), (-74, -32), (-74, -58), (-107, -58), (-107, -28), (-112, -28), (-112, -63), (-69, -63), (-69, -22), (-118, -22),
       (-118, -69), (-63, -69), (-63, -16), (-124, -16), (-124, -75), (-57, -75), (-57, -11)]
IN = [(-56, -11), (-56, -76), (-125, -76), (-125, -15), (-62, -15), (-62, -70), (-119, -70), (-119, -21), (-68, -21), (-68, -64),
      (-113, -64), (-113, -27), (-97, -27)]


def layout():
    # ---- the two long belts ----
    out = poly(OUT) + [("in", -57, -10, S), ("out", -57, -6, S), (-57, -5), (-57, -4), (-57, -3), ("in", -57, -2, S), ("out", -57, 0, S)]
    out += poly([(-57, 1), (-48, 1)]) + [("in", -47, 1, E), ("out", -45, 1, E)] + poly([(-44, 1), (-41, 1)])
    belts(out, E)
    belts(poly([(-54, -3), (-54, -4), (-56, -4), (-56, -5)]) + [("in", -56, -6, N), ("out", -56, -10, N)] + poly(IN), E)
    put("express-transport-belt", -55, -3, d=N)                           # the oxide stub: side-loads onto -55,-4 from the south
    ins(-54, -2, S, ["metallic-asteroid-chunk"], name="bulk-inserter")    # the tap
    ins(-55, -2, S, ["oxide-asteroid-chunk"], name="bulk-inserter")
    for x in (-52, -50):
        ins(x, 0, S, CHUNKS)                                              # returned chunks back onto the spoke belt
    # ---- heart: crushers ----
    for x, kind in ((-105, "metallic"), (-101, "metallic"), (-97, "oxide")):
        put("crusher", x, -30, 3, 2, d=E, recipe="advanced-%s-asteroid-crushing" % kind)
        ins(x, -28, S, ["%s-asteroid-chunk" % kind])
        ins(x + 2, -31, S)
    # ---- melting and casting ----
    put("foundry", -93, -38, 5, 5, recipe="iron-ore-melting")
    ins(-91, -33, S, ["iron-ore", "calcite"])
    put("foundry", -81, -38, 5, 5, recipe="copper-ore-melting")
    ins(-79, -33, S, ["copper-ore", "calcite"])
    put("pipe", -92, -39)
    put("pipe-to-ground", -91, -39, d=W)
    put("pipe-to-ground", -87, -39, d=E)
    put("pipe", -86, -39)
    put("storage-tank", -86, -38, 3, 3)
    put("pipe", -80, -39)
    for x, rec, item in ((-93, "casting-iron", "iron-plate"), (-87, "casting-iron-gear-wheel", "iron-gear-wheel"), (-81, "casting-copper-cable", "copper-cable")):
        put("foundry", x, -44, 5, 5, recipe=rec)
        e = ins(x + 2, -45, S)
        gated.append((e["x"], e["y"], item))
    # ---- the counted loop and its assemblers ----
    loop = poly([(-94, -52), (-76, -52), (-76, -46), (-94, -46), (-94, -52)])[:-1]
    belts(loop, E, closed=True)
    loop_tiles.extend(loop)
    for x, rec in ((-93, "electronic-circuit"), (-89, "electronic-circuit"), (-85, "inserter"), (-81, "transport-belt")):
        put("assembling-machine-3", x, -50, 3, 3, recipe=rec)
        ins(x, -51, N)
        e = ins(x + 2, -47, N)
        gated.append((e["x"], e["y"], rec))
    for x in (-89, -83):
        put("assembling-machine-3", x, -56, 3, 3, recipe="logistic-science-pack")
        ins(x, -53, S, ["inserter", "transport-belt"])
        ins(x + 2, -57, S, ["logistic-science-pack"])
    for x in range(-108, -72):                                            # the heart is one solid chamber
        for y in range(-59, -25):
            tiles.add((x, y))
    # ---- lamps along the corridor, alternately on its inner and outer edge ----
    path = poly(OUT[4:])
    for i, (x, y) in enumerate(path[:-1]):
        dx, dy = path[i + 1][0] - x, path[i + 1][1] - y
        if i % 8 == 3:
            c = (x - dy, y + dx)                                          # right of the out-belt's travel: the inner edge
        elif i % 8 == 7:
            c = (x + 2 * dy, y - 2 * dx)                                  # left, beyond the in-belt: the outer edge
        else:
            continue
        if c not in occ and c in tiles and not (-108 <= c[0] <= -73 and -59 <= c[1] <= -26):
            put("small-lamp", c[0], c[1], margin=False)
    return {"entities": len(ents), "tiles": len(tiles), "loop": len(loop_tiles), "x": (min(t[0] for t in tiles), max(t[0] for t in tiles)), "y": (min(t[1] for t in tiles), max(t[1] for t in tiles))}


def lua_list(rows):
    return "{" + ",".join("{" + ",".join(("'%s'" % v) if isinstance(v, str) else ("{" + ",".join("'%s'" % f for f in v) + "}") if isinstance(v, list) else str(v) for v in r) + "}" for r in rows) + "}"


LAMPS = "local s=game.surfaces['SURF'] local n=0 for _,p in pairs(CELLS) do for _,e in pairs(s.find_entities_filtered{type='lamp',position=p,radius=0.3}) do e.destroy() n=n+1 end end rcon.print('lamps in the way removed '..n)"
CONFIG = ("local s=game.surfaces['SURF'] local W=defines.wire_connector_id local o={} local function at(t,x,y) return s.find_entities_filtered{type=t,position={x,y},radius=0.3}[1] end local n,r=0,0 "
          "for _,q in pairs(FILT) do local i=at('inserter',q[1],q[2]) if i then i.use_filters=true i.inserter_filter_mode='whitelist' for k,name in pairs(q[3]) do i.set_filter(k,name) end n=n+1 end end "
          "for _,q in pairs(REC) do local m=s.find_entities_filtered{type='assembling-machine',position={q[1],q[2]},radius=0.5}[1] if m then m.set_recipe(q[3]) r=r+1 end end o[#o+1]='filters '..n..', recipes '..r "
          "local prev,nb=nil,0 for _,p in pairs(LOOP) do local b=at('transport-belt',p[1]+0.5,p[2]+0.5) if b then local bc=b.get_or_create_control_behavior() bc.read_contents=true bc.read_contents_mode=defines.control_behavior.transport_belt.content_read_mode.hold "
          "if prev then b.get_wire_connector(W.circuit_red,true).connect_to(prev.get_wire_connector(W.circuit_red,true),false) end prev=b nb=nb+1 end end o[#o+1]='loop belts read '..nb "
          "local g=0 for _,q in pairs(GATED) do local i=at('inserter',q[1],q[2]) if i then i.get_wire_connector(W.circuit_red,true).connect_to(prev.get_wire_connector(W.circuit_red,true),false) local cb=i.get_or_create_control_behavior() cb.circuit_enable_disable=true "
          "cb.circuit_condition={first_signal={type='item',name=q[3]},comparator='<',constant=q[4]} g=g+1 end end o[#o+1]='producers gated '..g "
          "local tank=s.find_entities_filtered{name='storage-tank',position={-84.5,-36.5},radius=0.5}[1] for _,x in pairs{-104.5,-100.5} do local i=at('inserter',x,-27.5) i.get_wire_connector(W.circuit_green,true).connect_to(tank.get_wire_connector(W.circuit_green,true),false) "
          "local cb=i.get_or_create_control_behavior() cb.circuit_enable_disable=true cb.circuit_condition={first_signal={type='fluid',name='molten-iron'},comparator='<',constant=IRON} end "
          "local ox=at('inserter',-96.5,-27.5) for _,q in pairs{{-90.5,-35.5},{-78.5,-35.5}} do local m=s.find_entities_filtered{name='foundry',position=q,radius=0.5}[1] m.get_or_create_control_behavior().circuit_read_contents=true "
          "m.get_wire_connector(W.circuit_red,true).connect_to(ox.get_wire_connector(W.circuit_red,true),false) end local cb=ox.get_or_create_control_behavior() cb.circuit_enable_disable=true "
          "cb.circuit_condition={first_signal={type='item',name='calcite'},comparator='<',constant=CALCITE} o[#o+1]='crusher gates set' rcon.print(table.concat(o,', '))").replace("IRON", str(IRON)).replace("CALCITE", str(CALCITE))
STATUS = ("local s=game.surfaces['SURF'] local st={} for _,c in pairs(s.find_entities_filtered{type='assembling-machine',area={{-109,-60},{-72,-25}}}) do local k='?' for n,v in pairs(defines.entity_status) do if v==c.status then k=n end end "
          "local rc=c.get_recipe() k=(rc and rc.name or c.name)..' '..k st[k]=(st[k] or 0)+1 end local o={} for k,v in pairs(st) do o[#o+1]=k..' '..v end table.sort(o) "
          "local b={} for _,e in pairs(s.find_entities_filtered{type={'transport-belt','underground-belt'},area={{-127,-78},{-55,-10}}}) do for l=1,2 do for _,it in pairs(e.get_transport_line(l).get_contents()) do b[it.name]=(b[it.name] or 0)+it.count end end end "
          "local q={} for k,v in pairs(b) do q[#q+1]=k..' '..v end table.sort(q) local tank=s.find_entities_filtered{name='storage-tank',position={-84.5,-36.5},radius=0.5}[1] local f=game.forces.player.get_item_production_statistics(s) "
          "local inv=s.platform.hub.get_inventory(defines.inventory.hub_main) rcon.print(table.concat(o,' ; ')..' ; ON THE BELTS '..table.concat(q,', ')..' ; molten iron in the tank '..string.format('%.0f',tank and (tank.get_fluid_contents()['molten-iron'] or 0) or -1)"
          "..' ; green science made a minute '..string.format('%.1f',f.get_flow_count{name='logistic-science-pack',category='input',precision_index=defines.flow_precision_index.one_minute})..' (10 min window '..string.format('%.1f',f.get_flow_count{name='logistic-science-pack',category='input',precision_index=defines.flow_precision_index.ten_minutes})..'), in hub '..inv.get_item_count('logistic-science-pack'))")


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
                print(tools["run_lua"](LAMPS.replace("SURF", surface).replace("CELLS", "{" + ",".join("{%s,%s}" % (x + .5, y + .5) for x, y in sorted(occ)) + "}")))
                print("deck tiles", lay_foundation(tiles, surface))
            ok, bad = place_all(ents, surface, apply)
            print("placed" if apply else "dry run", ok, "failed", bad)
        if step == "config" or (step == "build" and apply):
            code = (CONFIG.replace("SURF", surface).replace("FILT", lua_list([(x, y, fl) for x, y, fl in cfg])).replace("REC", lua_list(recipes))
                    .replace("LOOP", lua_list(loop_tiles)).replace("GATED", lua_list([(x, y, it, TARGETS[it]) for x, y, it in gated])))
            print(tools["run_lua"](code))
        elif step == "status":
            print(tools["run_lua"](STATUS.replace("SURF", surface)).replace(" ; ", "\n"))


if __name__ == "__main__":
    main()
