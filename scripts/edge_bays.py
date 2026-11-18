#!/usr/bin/env python3
"""Edgerunner CARGO BAYS: massive storage for consumables (the Captain, 2026-11-18: "Give the ship massive storage for fluids and consumables").
A platform cannot hold chests: its only store is the hub, and the hub grows by cargo bays (legendary: 50 slots each) that touch the hub or
another bay. The hub (x -4..3, y -4..3) is boxed in by the station ring, so one face has to be opened:

  WEST FACE   bay 1 at x -8..-5, y 0..3 (touches the hub), bay 2 at x -12..-9, y 0..3, bay 3 at x -13..-10, y 4..7, then a chain south
              round the old solar wing (see bays()) and a long column at x -13..-10 down to row 147, above the thruster bar.
  what moves  the metallic reprocessing crusher that stood on bay 1's ground goes under the ring's south row (x -8..-6, y 10..11, new
              deck), with both inserters, filters, the intake's circuit condition and its red wires (it is a link in the station's wire
              chain: the new inserter takes over all three connections before the old one goes).
              The ring's west column passes under bay 2 by underground belt (row 4 -> row -1).
  uranium     the only free hub face tile on the west, (-5,3), is under bay 1, so the uranium round outlet moves to the east face:
              the oxide reprocessing crusher goes under the ring's south row too (x 4..6, y 10..11); outlet inserter (4,1), belt
              (5,1)-(7,1), under the ring's inserters (0 -> -5), under the ring's top row (-7 -> -11), east on row -12 to x 10, north
              to a splitter (10..11,-32): right to the east feed inserter (11,-37), left west along row -33 (under the piercing column,
              both buses and the west column) to the west feed inserter (-8,-37). The west trunk of edge_uranium.py is taken out.
Steps (in this order): plan | deck | crushers [--apply] | uranium [--apply] | ring [--apply] | bays [--apply] | status
Usage: edge_bays.py plan ; edge_bays.py deck ; edge_bays.py crushers --apply ; edge_bays.py uranium --apply ; edge_bays.py ring --apply ; edge_bays.py bays --apply"""
import sys

import triangle_miner as TM
from _game import tools
from edge_works import T

L = tools["run_lua"]
BELT, UG, SPLIT, BULK, FAST = "express-transport-belt", "express-underground-belt", "express-splitter", "bulk-inserter", "fast-inserter"
N, E, S, W = 0, 4, 8, 12
NB = 25                                   # bays in the long column: rows 48 .. 48 + 4*NB - 1 = 147
BX = -13                                  # the column's west tile
# (name, old crusher centre, old intake, old return, new crusher top-left, new intake, new return)
MOVES = [("metallic-asteroid-reprocessing", (-6, 1.5), (-7.5, 0.5), (-7.5, 1.5), (-8, 10), (-7, 9), (-8, 9)),
         ("oxide-asteroid-reprocessing", (6, 1.5), (7.5, 0.5), (7.5, 1.5), (4, 10), (5, 9), (4, 9))]


def deck_tiles():
    t = set()
    for x0 in (-8, 4):
        t |= {(x, y) for x in range(x0, x0 + 3) for y in (9, 10, 11)}
    for e in bays()[2:]:
        x0, y0 = int(e["x"] - 2), int(e["y"] - 2)
        t |= {(x, y) for x in range(x0, x0 + 4) for y in range(y0, y0 + 4)}
    return t


def bays():
    """In chain order (each touches one before it). The old solar wing stands at x -18..-6, rows 12..41, so the chain goes round it:
    west along rows 8..11, south at x -22..-19 to row 43, back east along rows 44..47, then the long column at x -13..-10 to row 147."""
    c = [(-8, 0), (-12, 0), (BX, 4), (BX, 8), (-17, 8), (-21, 8)] + [(-22, 12 + 4 * k) for k in range(8)] + [(-18, 44), (-14, 44)]
    c += [(BX, 48 + 4 * k) for k in range(NB)]
    return [T("cargo-bay", x, y, 0, 4, 4) for x, y in c]


def crushers():
    e = []
    for rec, _, _, _, c, i, r in MOVES:
        e += [T("crusher", c[0], c[1], E, 3, 2, rec), T(FAST, i[0], i[1], N), T(FAST, r[0], r[1], S)]
    return e


# the west trunk of edge_uranium.py that goes (tile, entity type); the two feed ends on x -8 and x 11 stay
OLD = [(-5, 3), (-6, 3), (-7, 3), (-8, 3), (-8, 2), (-8, -5), (-8, -6), (-8, -7), (-8, -13), (-8, -14), (-8, -15), (-8, -16), (-8, -18)] + \
      [(-8, y) for y in range(-19, -32, -1)] + [(-8, -32), (-7, -33), (-6, -33), (3, -33), (4, -33), (7, -33), (8, -33), (9, -33), (10, -33)]


def uranium():
    e = [T(BELT, 5, 1, E), T(BELT, 6, 1, E), T(BELT, 7, 1, N),
         T(UG, 7, 0, N, type="input"), T(UG, 7, -5, N, type="output"), T(BELT, 7, -6, N),
         T(UG, 7, -7, N, type="input"), T(UG, 7, -11, N, type="output"),
         T(BELT, 7, -12, E), T(BELT, 8, -12, E), T(BELT, 9, -12, E)]
    e += [T(BELT, 10, y, N) for y in range(-12, -32, -1)]
    e += [T(SPLIT, 10, -32, N, 2, 1)]
    e += [T(BELT, 10, -33, W), T(BELT, 9, -33, W), T(BELT, 8, -33, W),
          T(UG, 7, -33, W, type="input"), T(UG, 4, -33, W, type="output"),
          T(UG, 3, -33, W, type="input"), T(UG, -6, -33, W, type="output"), T(BELT, -7, -33, W)]
    return e


CELLS = lambda ts: "{" + ",".join("{%s,%s}" % c for c in ts) + "}"

REMOVE = (TM.AT + "local inv=p.hub.get_inventory(defines.inventory.hub_main) local n,kept,lost=0,0,0 local function save(st) if st and st.valid_for_read then local c=st.count local put=inv.insert(st) kept=kept+put lost=lost+c-put end end "
          "for _,q in pairs(LIST) do for _,e in pairs(s.find_entities_filtered{area={{q[1]+0.1,q[2]+0.1},{q[1]+0.9,q[2]+0.9}},force='player'}) do if e.valid and e.name~='space-platform-hub' and e.name~='cargo-bay' and e.type~='entity-ghost' then "
          "if e.type=='inserter' then save(e.held_stack) end "
          "if e.type=='transport-belt' or e.type=='underground-belt' or e.type=='splitter' then for i=1,e.get_max_transport_line_index() do for _,it in pairs(e.get_transport_line(i).get_contents()) do "
          "local put=inv.insert{name=it.name,count=it.count,quality=it.quality} kept=kept+put lost=lost+it.count-put end end end e.destroy() n=n+1 end end end rcon.print('removed '..n..', items into the hub '..kept..', lost '..lost)")

# One crusher: the new intake takes the old one's filters, condition and every wire; modules and contents move; then the old three go.
MOVE = (TM.AT + "local inv=p.hub.get_inventory(defines.inventory.hub_main) local function ins(q) return s.find_entities_filtered{type='inserter',position=q,radius=0.3}[1] end "
        "local oc=s.find_entities_filtered{name='crusher',position=OC,radius=0.6}[1] local nc=s.find_entities_filtered{name='crusher',position=NC,radius=0.6}[1] local oi,orr,ni,nr=ins(OI),ins(OR),ins(NI),ins(NR) "
        "if not (nc and ni and nr) then rcon.print('REC: new crusher or inserters missing, nothing changed') return end if not (oc and oi and orr) then rcon.print('REC: old ones already gone') return end "
        "for _,pr in pairs({{oi,ni},{orr,nr}}) do local a,b=pr[1],pr[2] b.use_filters=a.use_filters b.inserter_filter_mode=a.inserter_filter_mode for k=1,a.filter_slot_count do b.set_filter(k,a.get_filter(k)) end "
        "local ca=a.get_control_behavior() if ca and ca.circuit_enable_disable then local cb=b.get_or_create_control_behavior() cb.circuit_enable_disable=true cb.circuit_condition=ca.circuit_condition end "
        "for _,wc in pairs(a.get_wire_connectors(false)) do local nw=b.get_wire_connector(wc.wire_connector_id,true) for _,c in pairs(wc.connections) do if c.target.owner.valid and c.target.owner~=a then nw.connect_to(c.target,false) end end end end "
        "local mo,mn=oc.get_module_inventory(),nc.get_module_inventory() local mods=0 for _,it in pairs(mo.get_contents()) do mods=mods+mn.insert{name=it.name,count=it.count,quality=it.quality} end mo.clear() "
        "local kept,lost=0,0 for _,e in pairs({oc,oi,orr}) do for i=1,e.get_max_inventory_index() do local v=e.get_inventory(i) if v then for _,it in pairs(v.get_contents()) do local put=inv.insert{name=it.name,count=it.count,quality=it.quality} kept=kept+put lost=lost+it.count-put end end end "
        "if e.type=='inserter' and e.held_stack.valid_for_read then local c=e.held_stack.count local put=inv.insert(e.held_stack) kept=kept+put lost=lost+c-put end e.destroy() end "
        "local w=0 for _,wc in pairs(ni.get_wire_connectors(false)) do w=w+#wc.connections end local cb=ni.get_control_behavior() "
        "rcon.print('REC moved: modules '..mods..', wires on the new intake '..w..', condition '..(cb and helpers.table_to_json(cb.circuit_condition) or 'none')..', contents into the hub '..kept..', lost '..lost)")

OUTLET = (TM.AT + "local function filt(e) e.use_filters=true e.inserter_filter_mode='whitelist' e.set_filter(1,{name='uranium-rounds-magazine',quality='normal',comparator='='}) end "
          "local out=s.find_entities_filtered{type='inserter',position={4.5,1.5},radius=0.3}[1] if not out then out=s.create_entity{name='bulk-inserter',position={4.5,1.5},direction=12,quality='legendary',force='player'} end "
          "if out then filt(out) rcon.print('outlet (4,1) picks '..out.pickup_position.x..','..out.pickup_position.y..' drops '..out.drop_position.x..','..out.drop_position.y) else rcon.print('NO outlet') end")

STATUS = (TM.AT + "local inv=p.hub.get_inventory(defines.inventory.hub_main) local o={} o[#o+1]='cargo bays '..s.count_entities_filtered{name='cargo-bay'}..', hub slots '..#inv..', free '..inv.count_empty_stacks() "
          "local m={} for k,v in pairs(defines.entity_status) do m[v]=k end for _,c in pairs(s.find_entities_filtered{name='crusher',area={{-9,9},{8,12}}}) do local r=c.get_recipe() o[#o+1]=(r and r.name or '?')..' @'..c.position.x..','..c.position.y..' '..tostring(m[c.status])..' made '..c.products_finished end "
          "o[#o+1]='tile ghosts '..s.count_entities_filtered{type='tile-ghost'}..', entity ghosts '..s.count_entities_filtered{type='entity-ghost'}..', hub foundations '..inv.get_item_count('space-platform-foundation') rcon.print(table.concat(o,string.char(10)))")


def place(ents, apply, what):
    ok, bad = TM.place(ents, apply)
    print(what, "placed" if apply else "dry run: would place", ok, "of", len(ents), "failed", bad)
    return bad


def main():
    a = sys.argv[1:]
    step = a[0] if a else "status"
    apply = "--apply" in a
    if step == "plan":
        t = deck_tiles()
        print(L(TM.AT + "local need=0 for _,q in pairs(" + CELLS(sorted(t)) + ") do if s.get_tile(q[1],q[2]).name~='space-platform-foundation' then need=need+1 end end rcon.print('deck tiles '..#" + CELLS(sorted(t)) + "..', missing '..need)"))
        print(len(bays()), "bays (", len(bays()) * 50, "slots ),", len(crushers()), "crusher pieces,", len(uranium()), "uranium line pieces")
    elif step == "deck":
        t = deck_tiles()
        print(L(TM.AT + "local n=0 for _,q in pairs(" + CELLS(sorted(t)) + ") do if s.get_tile(q[1],q[2]).name~='space-platform-foundation' and "
                "s.count_entities_filtered{type='tile-ghost',position={q[1]+0.5,q[2]+0.5},radius=0.3}==0 then "
                "if s.create_entity{name='tile-ghost',inner_name='space-platform-foundation',position={q[1],q[2]},force='player'} then n=n+1 end end end rcon.print('tile ghosts laid '..n)"))
    elif step == "crushers":
        if place(crushers(), apply, "crushers") or not apply:
            return
        for rec, oc, oi, orr, c, i, r in MOVES:
            lua = MOVE.replace("REC", rec.split("-")[0])
            for k, v in (("OC", oc), ("NC", (c[0] + 1.5, c[1] + 1)), ("OI", oi), ("OR", orr), ("NI", (i[0] + 0.5, i[1] + 0.5)), ("NR", (r[0] + 0.5, r[1] + 0.5))):
                lua = lua.replace(k + ",", "{%s,%s}," % v).replace(k + ")", "{%s,%s})" % v)
            print(L(lua))
    elif step == "uranium":
        if not apply:
            return place(uranium(), False, "uranium line (the old trunk still stands, so some tiles read blocked)")
        print(L(REMOVE.replace("LIST", CELLS(OLD))))
        if not place(uranium(), True, "uranium line"):
            print(L(OUTLET))
    elif step == "ring":
        if not apply:
            return print("would put the ring's west column underground from row 4 to row -1")
        print(L(REMOVE.replace("LIST", CELLS([(-9, y) for y in range(-1, 5)]))))
        place([T(UG, -9, 4, N, type="input"), T(UG, -9, -1, N, type="output")], True, "ring underground")
    elif step == "bays":
        # place_entities refuses a bay that touches the one before it on only part of an edge (its manual build check says no), but the
        # game accepts such a bay and counts its slots (tried at (-13,4): 159 -> 209 slots). So bays are created directly, in chain order,
        # each only on complete free deck and only when the one before it stands.
        if not apply:
            return print("would place", len(bays()), "bays in chain order")
        lst = "{" + ",".join("{%s,%s}" % (e["x"], e["y"]) for e in bays()) + "}"
        print(L(TM.AT + "local made,have,wait=0,0,0 for _,q in pairs(" + lst + ") do if s.count_entities_filtered{name='cargo-bay',position=q,radius=1}>0 then have=have+1 else "
                "local ok=true for x=q[1]-2,q[1]+1 do for y=q[2]-2,q[2]+1 do if s.get_tile(x,y).name~='space-platform-foundation' then ok=false end end end "
                "if ok and s.can_place_entity{name='cargo-bay',position=q,force='player'} and s.create_entity{name='cargo-bay',position=q,force='player',quality='legendary'} then made=made+1 else wait=wait+1 break end end end "
                "rcon.print('bays placed now '..made..', already standing '..have..', still waiting (deck or something in the way) from the next one on')"))
        if apply:
            print(L(STATUS))
    elif step == "status":
        print(L(STATUS))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
