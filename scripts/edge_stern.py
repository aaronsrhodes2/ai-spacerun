#!/usr/bin/env python3
"""Edgerunner PROPULSION: the stern (the Captain, 2026-11-17: "Yes, build it"; plan stage 4 in docs/fusion-and-galaxy-edge-plan.md).
Stage 1 is scripts/edge_ship.py, stage 2 scripts/edge_works.py, the station scripts/triangle_miner.py.

THRUST   24 thrusters in one row south of the base strip, x -71..70, pitch 6 (4 wide + a 2-tile gap), rows 293..297. A thruster needs EMPTY
         space behind it. Ports as proven on the inner shuttles: fuel west-top and east-middle, oxidizer east-top and west-middle, so the gaps carry
         one fluid each, alternating oxidizer, fuel. Fuel header row 289 (the strip's free south row), oxidizer header row 291; the fuel drops
         cross the oxidizer header by pipe to ground. Four base collectors (x -45, -15, 15, 45) stood in the row and are removed.
PLANT    two mirrored halves on new deck beside the south spoke (x 2..20 east = oxidizer, x -20..-2 west = fuel, rows 262..285). Each half takes
         chunks straight off the spoke belt (x = 0, flowing north to the station), so the plant is served before the station:
           crusher M   (270..272) plain metallic (east: iron ore) / plain carbonic (west: carbon) -> belt S, right lane
           crusher AO  (276..278) advanced oxide: calcite -> belt S, left lane (dropped on an east-flowing stub from its south side);
                                  ice -> melter M2 beside it
           crusher PO  (280..282) plain oxide: ice -> melter M1 (the advanced recipe gives 3 ice per 2 calcite; a craft needs 10)
           belt S      x = 5, 274 -> 264, one item kind per lane, dead end (cannot clog)
           plants X1 (270..272), X2 (264..266): advanced thruster oxidizer / fuel = 2 ore or carbon + 1 calcite + 100 water -> 1,500
           water main x = 10, product main x = 12 (the water main ducks under the two product rows), 16 tanks on the column x = 17
         Every crusher has a return inserter that puts the handed-back chunk on the spoke belt one row UPSTREAM of its intake (the gap the
         intake makes travels upstream on a backed-up belt).
THROTTLE one pump per fluid on row 286 between the tanks and the header (3,000 /s legendary: that alone caps the burn at about 125 /s a
         thruster). Each runs only while the hub's speed signal V is under TARGET km/s. One tank per fluid is on the hub's green wire
         (schedule conditions read one tank of sixteen: x16).
DECK     tile ghosts, built by the hub from its foundation stock (request `foundation-works 37`, raised while this is built).
Steps: plan | deck | clear | build [east|west|stern] | config | overflow | gaps | status | speed N
Usage: edge_stern.py plan ; edge_stern.py deck ; edge_stern.py build east ; edge_stern.py config ; edge_stern.py status"""
import sys

import triangle_miner as TM
from _game import tools
from edge_works import T

L = tools["run_lua"]
TARGET = 30                          # km/s: the pumps stop above this
N_THR, X0, PITCH = 24, -71, 6
ROW_F, ROW_O, ROW_T = 289, 291, 293  # fuel header, oxidizer header, thruster top row
BELT, PIPE, PTG, INS = "express-transport-belt", "pipe", "pipe-to-ground", "fast-inserter"
N, E, S, W = 0, 4, 8, 12
REMOVE_X = (-45, -15, 15, 45)        # base collectors in the thruster row (centre tile)
FILTERS = []                         # (x, y, names) filled by half()


def half(side):
    """side +1 = east (oxidizer, iron ore), -1 = west (fuel, carbon): the west half is the east half mirrored on x -> -x."""
    e = []

    def X(x, w=1):
        return x if side > 0 else -(x + w - 1)

    def D(d):
        return d if side > 0 or d in (N, S) else (W if d == E else E)

    def put(name, x, y, d=0, w=1, h=1, recipe=None):
        e.append(T(name, X(x, w), y, D(d), w, h, recipe))

    def ins(x, y, d, *names):
        put(INS, x, y, d)
        FILTERS.append((X(x), y, names))

    chunk = "metallic-asteroid-chunk" if side > 0 else "carbonic-asteroid-chunk"
    solid = "iron-ore" if side > 0 else "carbon"
    any_chunk = ("metallic-asteroid-chunk", "carbonic-asteroid-chunk", "oxide-asteroid-chunk")
    # crushers on the spoke: return (x = 1) on the top row, intake one row south (upstream), product east. The belt moves (see OVERFLOW),
    # and on a moving belt the gap an intake makes travels DOWNSTREAM: the return must stand north of its intake or it never finds room.
    put("crusher", 2, 270, 0, 2, 3, "metallic-asteroid-crushing" if side > 0 else "carbonic-asteroid-crushing")
    ins(1, 270, E, *any_chunk)
    ins(1, 271, W, chunk)
    ins(4, 271, W, solid)
    put("crusher", 2, 276, 0, 2, 3, "advanced-oxide-asteroid-crushing")
    ins(1, 276, E, *any_chunk)
    ins(1, 277, W, "oxide-asteroid-chunk")
    ins(3, 275, S, "calcite")
    ins(4, 277, W, "ice")
    put("crusher", 2, 280, 0, 2, 3, "oxide-asteroid-crushing")
    ins(1, 280, E, *any_chunk)
    ins(1, 281, W, "oxide-asteroid-chunk")
    ins(4, 281, W, "ice")
    # belt S
    put(BELT, 3, 274, E)
    put(BELT, 4, 274, E)
    for y in range(274, 263, -1):
        put(BELT, 5, y, N)
    # melters (water out on the far side from the spoke) and the water main
    put("chemical-plant", 5, 276, W, 3, 3, "ice-melting")
    put("chemical-plant", 5, 280, W, 3, 3, "ice-melting")
    for y0, ym in ((276, 277), (280, 281)):
        for y in range(y0, y0 + 3):
            put(PIPE, 8, y)
        put(PIPE, 9, ym)
    for y in list(range(263, 266)) + list(range(269, 272)) + list(range(275, 282)):
        put(PIPE, 10, y)
    for y, d in ((266, N), (268, S), (272, N), (274, S)):
        put(PTG, 10, y, d)
    # plants: water on the north row, product on the south row
    recipe = "advanced-thruster-oxidizer" if side > 0 else "advanced-thruster-fuel"
    for top in (270, 264):
        put("chemical-plant", 7, top, N, 3, 3, recipe)
        ins(6, top + 1, W, solid, "calcite")
        for x in range(7, 10):
            put(PIPE, x, top - 1)
        for x in range(7, 13):
            put(PIPE, x, top + 3)
    # product main, tanks, pump
    for y in range(268, 273):
        put(PIPE, 12, y)
    for y in range(274, 286):
        put(PIPE, 12, y)
    for x in range(6, 18):
        put(PIPE, x, 286)
    for y in range(262, 286):
        put(PIPE, 17, y)
    for y0 in range(262, 286, 3):
        put("storage-tank", 14, y0, 0, 3, 3)
        put("storage-tank", 18, y0, 0, 3, 3)
    put("pump", 4, 286, W, 2, 1)
    put(PIPE, 3, 286)
    put(PTG, 3, 287, N)
    tiles = {(X(x), y) for x in range(2, 21) for y in range(262, 286)}
    return e, tiles


def stern():
    e, tiles = [], set()

    def put(name, x, y, d=0, w=1, h=1):
        e.append(T(name, x, y, d, w, h))
        tiles.update((x + i, y + j) for i in range(w) for j in range(h))

    def pipes(*cells):
        for x, y in cells:
            put(PIPE, x, y)

    last = X0 + PITCH * (N_THR - 1)
    xw, xe = X0 - 1, last + 5
    for k in range(N_THR):
        put("thruster", X0 + PITCH * k, ROW_T, 0, 4, 5)
    under = set()                                   # oxidizer header tiles that go underground (fuel feed bridge at x -3)
    for k in range(N_THR - 1):
        a = X0 + PITCH * k + 4
        if k % 2 == 0:                              # oxidizer gap
            pipes((a, 292), (a, 293), (a, 294), (a + 1, 294), (a + 1, 295))
        else:                                       # fuel gap
            gx = a + 1
            put(PTG, gx, 290, N)
            put(PTG, gx, 292, S)
            pipes((gx, 293), (gx, 294), (gx - 1, 294), (gx - 1, 295))
        tiles.update((x, y) for x in (a, a + 1) for y in (293, 294, 295))
    # fuel header (row 289) with the feed at x -3: the feed's pipe to ground goes north under the belt, so the header steps round it on row 290
    for x in range(xw, xe + 1):
        if x != -3:
            pipes((x, ROW_F))
    put(PTG, -3, ROW_F, S)
    pipes((-4, 290), (-3, 290), (-2, 290))
    under.update((-4, -3, -2))
    put(PTG, -5, ROW_O, W)
    put(PTG, -1, ROW_O, E)
    pipes(*[(xw, y) for y in range(290, 294)])
    pipes(*[(xe, y) for y in range(290, 296)], (xe - 1, 295))
    tiles.update((x, y) for x in (xe - 1, xe) for y in (293, 294, 295))
    # oxidizer header (row 291) from the first to the last oxidizer gap; feed at x 3 from the north under header and belt
    for x in range(X0 + 4, last - 1):
        if x not in under and x not in (-5, -1):
            pipes((x, ROW_O))
    put(PTG, 3, 290, S)
    tiles.update((x, y) for x in range(xw, xe + 1) for y in (290, 291, 292))
    return e, tiles


def parts():
    FILTERS.clear()
    east, t1 = half(1)
    west, t2 = half(-1)
    st, t3 = stern()
    return {"east": (east, t1), "west": (west, t2), "stern": (st, t3)}


def cells(ts):
    return "{" + ",".join("{%d,%d}" % c for c in sorted(ts)) + "}"


def plan():
    for name, (ents, tiles) in parts().items():
        r = L(TM.AT + "local need,gh=0,0 local blk={} for _,q in pairs(" + cells(tiles) + ") do if s.get_tile(q[1],q[2]).name~='space-platform-foundation' then need=need+1 "
              "if s.count_entities_filtered{type='tile-ghost',position={q[1]+0.5,q[2]+0.5},radius=0.3}>0 then gh=gh+1 end end "
              "for _,e in pairs(s.find_entities_filtered{area={{q[1]+0.1,q[2]+0.1},{q[1]+0.9,q[2]+0.9}}}) do if e.type~='tile-ghost' then blk[e.name]=(blk[e.name] or 0)+1 end end end "
              "local t={} for k,v in pairs(blk) do t[#t+1]=k..' '..v end rcon.print('deck missing '..need..' (ghosts laid '..gh..'), in the way: '..(#t>0 and table.concat(t,', ') or 'nothing'))")
        print("%-5s %3d entities, %4d tiles: %s" % (name, len(ents), len(tiles), r.strip()))
    print(L(TM.AT + "rcon.print('hub foundations '..p.hub.get_inventory(defines.inventory.hub_main).get_item_count('space-platform-foundation'))"))


def deck(which):
    p = parts()
    tiles = set().union(*(p[k][1] for k in which))
    print(L(TM.AT + "local n=0 for _,q in pairs(" + cells(tiles) + ") do if s.get_tile(q[1],q[2]).name~='space-platform-foundation' and "
            "s.count_entities_filtered{type='tile-ghost',position={q[1]+0.5,q[2]+0.5},radius=0.3}==0 then "
            "if s.create_entity{name='tile-ghost',inner_name='space-platform-foundation',position={q[1],q[2]},force='player'} then n=n+1 end end end rcon.print('tile ghosts laid '..n)"))


CLEAR = (TM.AT + "local inv=p.hub.get_inventory(defines.inventory.hub_main) local n,kept,lost=0,0,0 for _,x in pairs({XS}) do "
         "for _,e in pairs(s.find_entities_filtered{area={{x-1.5,289},{x+2.5,293}}}) do if e.valid and (e.name=='asteroid-collector' or e.type=='inserter') then "
         "for i=1,e.get_max_inventory_index() do local v=e.get_inventory(i) if v then for _,it in pairs(v.get_contents()) do local put=inv.insert{name=it.name,count=it.count,quality=it.quality} kept=kept+put lost=lost+it.count-put end end end "
         "e.destroy() n=n+1 end end end rcon.print('removed '..n..' (collectors and their inserters), items into the hub '..kept..', lost '..lost)")

CONFIG = (TM.AT + "local Wd=defines.wire_connector_id local hub=p.hub local o={} local bad=0 "
          "for _,f in pairs(FILT) do local e=s.find_entities_filtered{type='inserter',position={f[1]+0.5,f[2]+0.5},radius=0.3}[1] if e then e.use_filters=true e.inserter_filter_mode='whitelist' "
          "for i,n in pairs(f[3]) do e.set_filter(i,{name=n,quality='normal',comparator='='}) end else bad=bad+1 end end o[#o+1]='filters set '..(#FILT-bad)..' missing '..bad "
          "local cb=hub.get_or_create_control_behavior() cb.read_contents=true cb.read_speed=true cb.speed_signal={type='virtual',name='signal-V'} "
          "local hg=hub.get_wire_connector(Wd.circuit_green,true) "
          "for _,x in pairs({-4.5,5}) do local pu=s.find_entities_filtered{name='pump',position={x,286.5},radius=0.8}[1] if pu then local c=pu.get_wire_connector(Wd.circuit_green,true) "
          "if not c.is_connected_to(hg) then c.connect_to(hg,false) end local pb=pu.get_or_create_control_behavior() pb.circuit_enable_disable=true "
          "pb.circuit_condition={first_signal={type='virtual',name='signal-V'},comparator='<',constant=TARGETV} o[#o+1]='pump '..x..' ok' else o[#o+1]='NO pump '..x end end "
          "for _,x in pairs({-18.5,19.5}) do local t=s.find_entities_filtered{name='storage-tank',position={x,284.5},radius=0.8}[1] if t then local c=t.get_wire_connector(Wd.circuit_green,true) "
          "if not c.is_connected_to(hg) then c.connect_to(hg,false) end o[#o+1]='tank '..x..' wired' else o[#o+1]='NO tank '..x end end "
          "rcon.print(table.concat(o,' | '))")

STATUS = (TM.AT + "local m={} for k,v in pairs(defines.entity_status) do m[v]=k end local o={} "
          "for _,e in pairs(s.find_entities_filtered{type={'assembling-machine','furnace'},area={{-21,262},{21,286}}}) do local rc=e.get_recipe() "
          "o[#o+1]=string.format('%-34s @%5.1f,%5.1f %-26s made %d',rc and rc.name or e.name,e.position.x,e.position.y,tostring(m[e.status]),e.products_finished) end table.sort(o) "
          "local fl={} local nt={} for _,t in pairs(s.find_entities_filtered{name='storage-tank',area={{-21,262},{21,286}}}) do for k,v in pairs(t.get_fluid_contents()) do fl[k]=(fl[k] or 0)+v end end "
          "for k,v in pairs(fl) do o[#o+1]='tanks '..k..' '..math.floor(v) end "
          "local th=s.find_entities_filtered{name='thruster'} local fed,st=0,{} for _,t in pairs(th) do local c=t.get_fluid_contents() if (c['thruster-fuel'] or 0)>0 and (c['thruster-oxidizer'] or 0)>0 then fed=fed+1 end "
          "local k=tostring(m[t.status]) st[k]=(st[k] or 0)+1 end local ts={} for k,v in pairs(st) do ts[#ts+1]=k..' '..v end o[#o+1]='thrusters '..#th..', holding both fluids '..fed..' ('..table.concat(ts,', ')..')' "
          "for _,x in pairs({-4.5,5}) do local pu=s.find_entities_filtered{name='pump',position={x,286.5},radius=0.8}[1] if pu then o[#o+1]='pump '..x..' '..tostring(m[pu.status]) end end "
          "o[#o+1]='speed '..string.format('%.1f',p.speed*60)..' km/s, weight '..math.floor(p.weight/1000)..' t, at '..(p.space_location and p.space_location.name or 'in transit')..', paused '..tostring(p.paused) "
          "o[#o+1]='tile ghosts '..s.count_entities_filtered{type='tile-ghost'}..', entity ghosts '..s.count_entities_filtered{type='entity-ghost'}..', hub foundations '..p.hub.get_inventory(defines.inventory.hub_main).get_item_count('space-platform-foundation') "
          "rcon.print(table.concat(o,string.char(10)))")


def config(target=TARGET):
    parts()
    filt = "{" + ",".join("{%d,%d,{%s}}" % (x, y, ",".join("'%s'" % n for n in names)) for x, y, names in FILTERS) + "}"
    print(L(CONFIG.replace("FILT", filt).replace("TARGETV", str(target))))


# OVERFLOW (after the first flight, 2026-11-18): the spoke belt backs up when the hub ring is full, the belt stops, and a crusher can then neither
# find its chunk nor put the handed-back one down: no ice, no water, no propellant. A splitter north of the plant (row OV) sends the belt on to
# the hub first; what the hub cannot take goes down a two-tile stub and two bulk inserters throw it overboard. The belt always moves.
OV = 258
OVER = (TM.AT + "local sp=s.find_entities_filtered{name='express-splitter',position={1,OVR+0.5},radius=0.6}[1] local o={} if sp then sp.splitter_output_priority='left' o[#o+1]='splitter priority '..sp.splitter_output_priority else o[#o+1]='NO splitter' end "
        "for _,y in pairs({OVR-1,OVR-2}) do local i=s.find_entities_filtered{type='inserter',position={2.5,y+0.5},radius=0.3}[1] o[#o+1]=i and ('inserter '..y..' drops at '..i.drop_position.x..' on '..s.get_tile(i.drop_position.x,i.drop_position.y).name) or ('NO inserter '..y) end "
        "rcon.print(table.concat(o,' | '))")


def overflow(apply):
    tiles = [(2, OV - 1), (2, OV - 2)]
    missing = int(L(TM.AT + "local n=0 for _,q in pairs(" + cells(tiles) + ") do if s.get_tile(q[1],q[2]).name~='space-platform-foundation' then n=n+1 "
                    "if APPLY and s.count_entities_filtered{type='tile-ghost',position={q[1]+0.5,q[2]+0.5},radius=0.3}==0 then s.create_entity{name='tile-ghost',inner_name='space-platform-foundation',position={q[1],q[2]},force='player'} end end end rcon.print(n)".replace("APPLY", "true" if apply else "false")))
    if missing:
        return print("deck missing", missing, "(tile ghosts laid: run again when the hub has built them)" if apply else "(--apply lays the ghosts)")
    ents = [T("express-splitter", 0, OV, N, 2, 1), T(BELT, 1, OV - 1, N), T(BELT, 1, OV - 2, N),
            T("bulk-inserter", 2, OV - 1, W), T("bulk-inserter", 2, OV - 2, W)]
    if apply:                                                             # the belt tile under the splitter goes first; what lies on it goes back on the belt behind
        print(L(TM.AT + "local b=s.find_entities_filtered{name='express-transport-belt',position={0.5,OVR+0.5},radius=0.3}[1] if b then b.destroy() rcon.print('belt tile removed') else rcon.print('no belt tile') end".replace("OVR", str(OV))))
    ok, bad = TM.place(ents, apply)
    print("overflow", "placed" if apply else "dry run: would place", ok, "of", len(ents), "failed", bad)
    if apply:
        print(L(OVER.replace("OVR", str(OV))))


# GAPS (same day): the belt through the plant is always packed (the collectors hold thousands of chunks), and a hand-back inserter needs a gap
# on its far lane. Two filtered inserters one row south of the crushers (row GAP) throw a metallic or carbonic chunk into a one-tile hole in the
# deck beside them (the tile is lifted by the hub, not deleted), so gaps on both lanes keep flowing north past every hand-back. Oxide is never
# thrown away here; the unfiltered overflow at row OV is what keeps an all-oxide belt moving.
GAP = 284
GAPS = (TM.AT + "local o={} for _,q in pairs({{1.5,2},{-0.5,-2}}) do local i=s.find_entities_filtered{type='inserter',position={q[1],GAPR+0.5},radius=0.3}[1] if i then i.use_filters=true i.inserter_filter_mode='whitelist' "
        "i.set_filter(1,{name='metallic-asteroid-chunk',quality='normal',comparator='='}) i.set_filter(2,{name='carbonic-asteroid-chunk',quality='normal',comparator='='}) "
        "o[#o+1]='inserter '..q[1]..' drops on '..s.get_tile(i.drop_position.x,i.drop_position.y).name else o[#o+1]='NO inserter '..q[1] end end rcon.print(table.concat(o,' | '))")


def gaps(apply):
    holes = int(L(TM.AT + "local n=0 for _,x in pairs({2,-2}) do local t=s.get_tile(x,GAPR) if t.name=='space-platform-foundation' then n=n+1 if APPLY and not t.to_be_deconstructed() then t.order_deconstruction('player') end end end rcon.print(n)"
                  .replace("GAPR", str(GAP)).replace("APPLY", "true" if apply else "false")))
    if holes:
        return print("deck tiles still to lift", holes, "(marked: run again when the hub has lifted them)" if apply else "(--apply marks them)")
    ents = [T(INS, 1, GAP, W), T(INS, -1, GAP, E)]
    ok, bad = TM.place(ents, apply)
    print("gap makers", "placed" if apply else "dry run: would place", ok, "of", len(ents), "failed", bad)
    if apply:
        print(L(GAPS.replace("GAPR", str(GAP))))


def main():
    a = sys.argv[1:]
    step = a[0] if a else "status"
    which = [k for k in ("east", "west", "stern") if k in a] or ["east", "west", "stern"]
    if step == "plan":
        plan()
    elif step == "deck":
        deck(which)
    elif step == "clear":
        print(L(CLEAR.replace("XS", ",".join(str(x) for x in REMOVE_X))))
    elif step == "build":
        p = parts()
        for k in which:
            ok, bad = TM.place(p[k][0], "--apply" in a)
            print(k, "placed" if "--apply" in a else "dry run: would place", ok, "of", len(p[k][0]), "failed", bad)
    elif step == "overflow":
        overflow("--apply" in a)
    elif step == "gaps":
        gaps("--apply" in a)
    elif step == "config":
        config()
    elif step == "speed":
        config(int(a[1]))
    elif step == "status":
        print(L(STATUS))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
