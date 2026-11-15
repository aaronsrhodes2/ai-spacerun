#!/usr/bin/env python3
"""Iron and copper PLATES on the Nauvis Triangle (the Captain, 2026-11-14: "you could make the Nauvis triangle manufacture copper and iron
plates"). Platform `[shuffle] Nauvis Triangle 1` (platform-14), an extension of scripts/triangle_miner.py (read that docstring first).

WHY: Nauvis ground is short of plates (scripts/worst_bottleneck.py, 2026-11-14: copper 240/s made vs 324/s used, iron 132 vs 165/s).
A landing pad's request is served by platforms in that orbit that hold the item (proven before with the Nauvis Wheel), so plates in
the triangle's hub (providing_to_other_platforms = true) are on call for the Nauvis pad.

RECIPES (read in the game, 2.1): iron-plate / copper-plate = 1 ore -> 1 plate, 3.2 s (epic electric furnace: speed 3.8, 180 kW, 2 module
slots, about 71 plates a minute). Foundry route: iron-ore-melting = 50 ore + 1 CALCITE -> 500 molten iron (32 s), casting-iron = 20 molten
-> 2 plates (3.2 s), so 1 ore -> 1 plate plus the foundry's +50% base productivity, at 2.5 MW a foundry. The foundry is researched and
has no surface condition, but the triangle makes no calcite (it needs advanced oxide crushing, the scarcest chunk) and fluids add pipes,
so this first build uses ELECTRIC FURNACES. Advanced metallic crushing (5 s): 1 metallic chunk -> 10 iron ore + 4 copper ore, chunk back 10%.

LAYOUT (tiles; the station ring is x/y -9..8, the hub -4..3; nothing inside the ring is moved, poles none: the foundation carries power):
  IRON WORKS, east. Two bulk inserters take iron ore out of the hub: OUT1 at (3,4) (south face) and OUT2 at (4,3) (east face), only
  while the hub holds more than OUT_KEEP iron ore (so the mode switch still sees iron as stocked and gives carbon / ice their turn
  when other platforms draw them). Ore belt y=5 east, under the ring at x=8 (underground 7 -> 9), along y=5 to x=10+3*NE.
  NE furnaces on y 1..3 from x=10 (input inserter y=4, output inserter y=0), plate belt y=-1 flowing west, under the ring (9 -> 7),
  bulk inserter IN_E at (4,-1) into the hub while iron plate < CAP.
  COPPER WORKS, west. Two crushers CA1 (tiles x -12..-11, y -8..-6) and CA2 (y -4..-2) on advanced metallic crushing, outside the
  ring's west column: intake fast inserter at x=-10 takes metallic chunks off the ring, return inserter puts the 10% chunk back
  (every machine returns at most one chunk per chunk taken, so the ring governor still holds). Two bulk inserters per crusher at
  x=-13 put the ore (iron + copper, mixed) on a belt x=-14 flowing south, under the plate belt (-2 -> 0), then west along y=5.
  NW furnaces on y 1..3 from x=-17 going west, each fed by an UNFILTERED inserter (WPAT; filters deadlocked the mixed belt), plate belt
  y=-1 flowing east, under the ring (-10 -> -8), bulk inserter IN_W at (-5,-1) into the hub while copper plate < CAP (it takes the
  iron plates of the copper works too).
  VALVE = THE DELIVERY: a hub section `triangle-plates-valve` with iron-plate / copper-plate min 0, max = VALVE (800, below CAP):
  whatever goes over it is hub trash, and a hub's trash in Nauvis orbit goes down to the Nauvis pad by pod with no request on the
  pad (proven 2026-11-14: hub iron plate 1,455 -> 800, the pad 22 -> 800 iron plate within 0.5 game minutes). So the works run at
  full rate, the hub keeps 800 of each for other platforms, and the rest lands on the pad, where the Nauvis robots take it.
  PAD REQUEST (step `pad`, NOT the way): a section `triangle-plates` on the Nauvis pad (copper-plate PAD_CU, import_from nauvis) is
  served by platforms in orbit, but the game picked the Nauvis Wheel (about 1,000 copper plate out of its hub in under a game
  minute), not the triangle. It cannot choose the source, so it is left OFF (`pad off` removes it; the pad's own sections are not touched).
  POWER: NE + NW furnaces x 180 kW + 2 crushers x 540 kW; step `panels` adds two bands of epic solar panels (y 35..40, 36 panels).
Steps: check | build [--apply] (saves the game first, deck, entities, config) | config | panels [--apply] | pad [off] | status
Usage: triangle_plates.py check ; triangle_plates.py build --apply ; triangle_plates.py pad ; triangle_plates.py status
Read-only helper: _triangle_plates_rate.py [minutes] (plates per minute, chunks, pad and hub counts)."""
import json
import sys

from _game import tools
import triangle_miner as tm

NE = 16                       # east (iron) furnaces
WPAT = "AAAAAAAAAAAA"         # west furnaces from x=-17 going west: A = any ore (unfiltered), C = copper only, I = iron only. FILTERED
                              # INSERTERS DEADLOCK a mixed belt (tested 2026-11-14): the belt end fills with the surplus kind, the belt stops, and an
                              # iron-filtered inserter waits forever beside a tile of copper. Unfiltered, any furnace takes the ore in front of it.
NW = len(WPAT)
CAP = 1000                    # hub stock cap per plate (10 slots each)
VALVE = 800                   # above this a plate is hub trash and drops to the Nauvis pad (below CAP, so the works run and the surplus goes down)
OUT_KEEP = 300                # iron ore stays in the hub above this (the mode switch reads it)
PAD_CU = 1000                 # the Nauvis pad's standing copper plate request (section `triangle-plates`)
PAD_GROUP = "triangle-plates"
VALVE_GROUP = "triangle-plates-valve"
T, E = tm.T, tm.E
UG = "express-underground-belt"
BELT = "express-transport-belt"
CA = [(-11.0, -6.5), (-11.0, -2.5)]          # copper works crushers (centre); intake at (x=-10, top row), return (x=-10, second row)


def east_ents():
    ents, tiles = [], set()
    ents.append(T("bulk-inserter", 3, 4, 0))                 # OUT1: picks from the hub (north), drops on (3,5)
    ents.append(T("bulk-inserter", 4, 3, 12))                # OUT2: picks from the hub (west), drops on (5,3)
    ents.append(T(BELT, 5, 3, 8))
    ents.append(T(BELT, 5, 4, 8))                            # side-loads (5,5)
    for x in range(3, 7):
        ents.append(T(BELT, x, 5, 4))
    ents.append(T(UG, 7, 5, 4, type="input"))
    ents.append(T(UG, 9, 5, 4, type="output"))
    xe = 10 + 3 * NE
    for x in range(10, xe):
        ents.append(T(BELT, x, 5, 4))
    for i in range(NE):
        x0 = 10 + 3 * i
        ents.append(T("electric-furnace", x0, 1, 0, 3, 3))
        ents.append(T("fast-inserter", x0 + 1, 4, 8))         # picks from the ore belt (south), drops into the furnace
        ents.append(T("fast-inserter", x0 + 1, 0, 8))         # picks from the furnace (south), drops on the plate belt
    for x in range(10, xe):
        ents.append(T(BELT, x, -1, 12))
    ents.append(T(UG, 9, -1, 12, type="input"))
    ents.append(T(UG, 7, -1, 12, type="output"))
    ents.append(T(BELT, 6, -1, 12))
    ents.append(T(BELT, 5, -1, 12))
    ents.append(T("bulk-inserter", 4, -1, 4))                # IN_E: picks from (5,-1), drops into the hub
    tiles |= {(x, y) for x in range(9, xe) for y in range(-1, 6)}
    return ents, tiles


def west_ents():
    ents, tiles = [], set()
    for (cx, cy) in CA:
        top = int(cy - 1.5)
        ents.append(E("crusher", cx, cy, 0))
        ents.append(T("fast-inserter", -10, top, 4))         # intake: picks from the ring (east), drops into the crusher
        ents.append(T("fast-inserter", -10, top + 1, 12))    # return: picks from the crusher (west), drops on the ring
        ents.append(T("bulk-inserter", -13, top, 4))         # ore out: picks from the crusher (east), drops on the belt x=-14
        ents.append(T("bulk-inserter", -13, top + 1, 4))
        tiles |= {(x, y) for x in (-12, -11, -10, -13) for y in range(top, top + 3)}
    for y in range(-8, -2):
        ents.append(T(BELT, -14, y, 8))
    ents.append(T(UG, -14, -2, 8, type="input"))
    ents.append(T(UG, -14, 0, 8, type="output"))
    for y in range(1, 5):
        ents.append(T(BELT, -14, y, 8))
    xw = -17 - 3 * (NW - 1)                                  # leftmost furnace tile
    for x in range(xw, -13):
        ents.append(T(BELT, x, 5, 12))
    for i, k in enumerate(WPAT):
        x0 = -17 - 3 * i
        ents.append(T("electric-furnace", x0, 1, 0, 3, 3))
        ents.append(T("fast-inserter", x0 + 1, 4, 8))
        ents.append(T("fast-inserter", x0 + 1, 0, 8))
    for x in range(xw, -10):
        ents.append(T(BELT, x, -1, 4))
    ents.append(T(UG, -10, -1, 4, type="input"))
    ents.append(T(UG, -8, -1, 4, type="output"))
    ents.append(T(BELT, -7, -1, 4))
    ents.append(T(BELT, -6, -1, 4))
    ents.append(T("bulk-inserter", -5, -1, 12))              # IN_W: picks from (-6,-1), drops into the hub
    tiles |= {(x, y) for x in range(xw, -9) for y in range(-1, 6)}
    tiles |= {(-14, y) for y in range(-8, 6)}
    return ents, tiles


def panel_ents():
    ents, tiles = [], set()
    for y0 in (35, 38):
        for x0 in list(range(-30, -3, 3)) + list(range(3, 30, 3)):
            ents.append(T("solar-panel", x0, y0, 0, 3, 3))
            tiles |= {(x0 + i, y0 + j) for i in range(3) for j in range(3)}
    return ents, tiles


AT, HEAD = tm.AT, tm.HEAD
WEST_FURN = "{" + ",".join("{x=%s,k='%s'}" % (-17 - 3 * i + 1.5, k) for i, k in enumerate(WPAT)) + "}"
CONFIG = (HEAD + "local hub=p.hub local bad={} local function note(m) bad[#bad+1]=m end "
          "local function wire(a,b,what) if not a or not b then note('missing '..what) return end local ca,cb=a.get_wire_connector(W.circuit_green,true),b.get_wire_connector(W.circuit_green,true) local ok=ca.is_connected_to(cb) or ca.connect_to(cb) if not ok then note('wire failed '..what) end end "
          "local function filt(e,items) e.use_filters=true e.inserter_filter_mode='whitelist' for i=1,5 do e.set_filter(i,nil) end for i,n in pairs(items) do e.set_filter(i,{name=n,quality='normal',comparator='='}) end end "
          "local function cond(e,sig,cmp,k) local cb=e.get_or_create_control_behavior() cb.circuit_enable_disable=true cb.circuit_condition={first_signal={type='item',name=sig},comparator=cmp,constant=k} end "
          "local n=0 "
          "local o1,o2=at('bulk-inserter',3.5,4.5),at('bulk-inserter',4.5,3.5) for _,e in pairs({o1,o2}) do if e then filt(e,{'iron-ore'}) cond(e,'iron-ore','>',OUTKEEP) wire(hub,e,'hub->out') n=n+1 else note('no OUT') end end "
          "local ie=at('bulk-inserter',4.5,-0.5) if ie then filt(ie,{'iron-plate'}) cond(ie,'iron-plate','<',CAPV) wire(hub,ie,'hub->IN_E') n=n+1 else note('no IN_E') end "
          "local iw=at('bulk-inserter',-4.5,-0.5) if iw then filt(iw,{'copper-plate','iron-plate'}) cond(iw,'copper-plate','<',CAPV) wire(hub,iw,'hub->IN_W') n=n+1 else note('no IN_W') end "
          "for _,c in pairs(CATAB) do local cr=at('crusher',c[1],c[2]) if cr then cr.set_recipe('advanced-metallic-asteroid-crushing') n=n+1 else note('no crusher') end "
          "local top=c[2]-1.0 local ii,ri=at('fast-inserter',-9.5,top),at('fast-inserter',-9.5,top+1) if ii and ri then filt(ii,{'metallic-asteroid-chunk'}) filt(ri,{'metallic-asteroid-chunk'}) n=n+2 else note('no ring inserters') end "
          "for _,yy in pairs({top,top+1}) do local b=at('bulk-inserter',-12.5,yy) if b then filt(b,{'iron-ore','copper-ore'}) n=n+1 else note('no ore inserter') end end end "
          "for _,f in pairs(WFURN) do local fi=at('fast-inserter',f.x,4.5) if fi then if f.k=='A' then for i=1,5 do fi.set_filter(i,nil) end fi.use_filters=false else filt(fi,{f.k=='C' and 'copper-ore' or 'iron-ore'}) end n=n+1 else note('no furnace inserter '..f.x) end end "
          "local pt=nil for _,q in pairs(hub.get_logistic_point()) do if q.mode==defines.logistic_mode.requester then pt=q end end "
          "if pt then for i=pt.sections_count,1,-1 do if pt.sections[i].group=='VGROUP' then pt.remove_section(i) end end local sc=pt.add_section('VGROUP') "
          "sc.set_slot(1,{value={type='item',name='iron-plate',quality='normal'},min=0,max=VALVEV}) sc.set_slot(2,{value={type='item',name='copper-plate',quality='normal'},min=0,max=VALVEV}) n=n+1 else note('no hub requester point') end "
          "rcon.print('configured '..n..' notes '..#bad..': '..table.concat(bad,' ; '))"
          ).replace("OUTKEEP", str(OUT_KEEP)).replace("CAPV", str(CAP)).replace("VALVEV", str(VALVE)).replace("VGROUP", VALVE_GROUP).replace(
              "CATAB", "{" + ",".join("{%s,%s}" % c for c in CA) + "}").replace("WFURN", WEST_FURN)

PAD = ("local pad=game.surfaces.nauvis.find_entities_filtered{type='cargo-landing-pad',position={-216,-228},radius=3}[1] "
       "local pt=pad.get_logistic_point(defines.logistic_member_index.cargo_landing_pad_requester) "
       "for i=pt.sections_count,1,-1 do if pt.sections[i].group=='GROUP' then pt.remove_section(i) end end "
       "if AMT>0 then local sc=pt.add_section('GROUP') sc.set_slot(1,{value={type='item',name='copper-plate',quality='normal'},min=AMT,import_from='nauvis'}) end "
       "local inv=pad.get_inventory(defines.inventory.cargo_landing_pad_main) local g={} for i=1,pt.sections_count do g[#g+1]=pt.sections[i].group..'('..#pt.sections[i].filters..')' end "
       "rcon.print('pad sections: '..table.concat(g,', ')..' | free slots '..inv.count_empty_stacks()..' copper-plate '..inv.get_item_count('copper-plate')..' iron-plate '..inv.get_item_count('iron-plate'))")

STATUS = (HEAD + "local hub=p.hub local inv=hub.get_inventory(defines.inventory.hub_main) local tr=hub.get_inventory(defines.inventory.hub_trash) "
          "local function stn(v) for n,x in pairs(defines.entity_status) do if x==v then return n end end return '?' end "
          "local o={} for _,n in pairs({'iron-ore','copper-ore','iron-plate','copper-plate','carbon','ice','space-platform-foundation'}) do o[#o+1]=n..' '..inv.get_item_count(n) end "
          "local out={'tick '..game.tick..' HUB free '..inv.count_empty_stacks()..' trash '..(tr and (#tr-tr.count_empty_stacks()) or 0)..': '..table.concat(o,', ')} "
          "local st={} for _,e in pairs(s.find_entities_filtered{type={'furnace','assembling-machine'}}) do local r=e.get_recipe() if e.type=='furnace' and e.previous_recipe then r=e.previous_recipe.name end "
          "local k=e.name..' '..(r and (type(r)=='string' and r or r.name) or '-')..' '..stn(e.status)..(e.position.x>0 and ' E' or ' W') st[k]=(st[k] or 0)+1 end local o2={} for k,v in pairs(st) do o2[#o2+1]=k..' x'..v end table.sort(o2) out[#out+1]='MACHINES '..table.concat(o2,' ; ') "
          "local f=game.forces.player.get_item_production_statistics(s) local P=defines.flow_precision_index local o4={} "
          "for _,n in pairs({'iron-plate','copper-plate','iron-ore','copper-ore','carbon','ice','metallic-asteroid-chunk','carbonic-asteroid-chunk','oxide-asteroid-chunk'}) do o4[#o4+1]=n..' +'..string.format('%.0f',f.get_flow_count{name=n,category='input',precision_index=P.ten_minutes})..'/-'..string.format('%.0f',f.get_flow_count{name=n,category='output',precision_index=P.ten_minutes}) end out[#out+1]='10-MIN FLOWS per min (made/used) '..table.concat(o4,' ; ') "
          "local lp=0 for _,e in pairs(s.find_entities_filtered{type={'furnace','assembling-machine','asteroid-collector','inserter'}}) do if e.status==defines.entity_status.low_power or e.status==defines.entity_status.no_power then lp=lp+1 end end out[#out+1]='low/no power entities '..lp "
          "rcon.print(table.concat(out,'\\n'))")


def first_standing(ents):
    return tm.first_standing(ents)


def main():
    step = sys.argv[1] if len(sys.argv) > 1 else "status"
    apply = "--apply" in sys.argv
    surf = tm.surface()
    if step == "check":
        for nm, (ents, tiles) in {"east (iron)": east_ents(), "west (copper)": west_ents(), "panels": panel_ents()}.items():
            print(nm, len(ents), "entities", len(tiles), "deck tiles;", "ALREADY STANDING" if first_standing(ents) else "not built", "dry run", tm.place(ents, False, surf))
    elif step == "build":
        ents = east_ents()[0] + west_ents()[0]
        tiles = east_ents()[1] | west_ents()[1]
        if apply and first_standing(ents):
            sys.exit("plate works already built (run config to re-apply settings)")
        if apply:
            print(tools["save_game"]("skippy"))
            print("deck", tm.deck(tiles))
        print("plate works", tm.place(ents, apply, surf))
        if apply:
            print(tools["run_lua"](CONFIG))
    elif step == "config":
        print(tools["run_lua"](CONFIG))
    elif step == "panels":
        ents, tiles = panel_ents()
        if apply and first_standing(ents):
            sys.exit("panels already built")
        if apply:
            print("deck", tm.deck(tiles))
        print("panels", tm.place(ents, apply, surf))
    elif step == "pad":
        amt = 0 if (len(sys.argv) > 2 and sys.argv[2] == "off") else PAD_CU
        print(tools["run_lua"](PAD.replace("GROUP", PAD_GROUP).replace("AMT", str(amt))))
    elif step == "status":
        print(tools["run_lua"](STATUS))
        print(tools["run_lua"](PAD.replace("GROUP", "__none__").replace("AMT", "0")))


if __name__ == "__main__":
    main()
