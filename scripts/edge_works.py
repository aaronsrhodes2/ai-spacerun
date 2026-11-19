#!/usr/bin/env python3
"""Edgerunner STAGE 2: the ammunition works (the Captain, 2026-11-16: ammunition "made on board from asteroids"; 2026-11-17: "start stage 2").
Design and stages: docs/fusion-and-galaxy-edge-plan.md. Stage 1 (turret pads, side belts) is scripts/edge_ship.py; the station is scripts/triangle_miner.py.

WHERE: the free deck wedge north of the station ring (ring x/y -9..8, wedge y -10..-38). Nothing inside the ring moves except two new hub inserters.
WHAT GOES IN
  iron plate, copper plate   out of the hub (the plate works keep it at about 800 each): bulk inserters (-1,-5) and (3,-5) on the hub's north face,
                             each only while the hub holds more than KEEP of its plate; under the ring by underground belt (y -6 -> -10)
  carbon + sulfur            crusher KC (advanced carbonic crushing: 5 carbon + 2 sulfur a chunk), carbonic chunks straight off the ring's top row
  ice                        crusher KO (plain oxide crushing: 5 ice, no calcite to get rid of), oxide chunks off the ring's top row
  5 carbon + 2 sulfur + 1 ice = 1 coal -> 2 explosives: exactly one advanced carbonic crush, so nothing is left over and nothing is thrown away.
LAYOUT (tiles)
  chemical row   KO (-9..-7,-12..-11) -> melter IM (-11..-9,-16..-14, facing south: water out on its north side)
                 KC (-5..-3,-12..-11) -> coal plant CS (-7..-5,-16..-14) and explosives plant EX (-3..-1,-16..-14); coal CS -> EX by inserter (-4,-15)
                 water main: pipes y = -17, x -9..-3 (the plants take water on their north side)
  bus            X (x = 1, y -13..-36, north): explosives on its east lane (from EX, inserter (0,-15)), steel on its west lane
                 P (x = 2, y -12..-36, north): iron plate on its west lane, copper plate on its east lane (the two port belts side-load at (2,-12))
  west column    (x -3..-1; next to X, reaches P with long-handed inserters): railgun ammo RG1, cable CC, railgun ammo RG2 (CC feeds both
                 directly), rocket RK -> explosive rocket ER. Output belt OW (x = -5): railgun ammo and explosive rockets.
  east column    (x 4..6; next to P, reaches X with long-handed inserters): steel furnaces F6, F5, magazine FM -> piercing PM, furnaces F1..F4.
                 Output belt OE (x = 8): piercing magazines.
  Both lanes of both buses carry ONE item kind each, so a dead end cannot clog. OW and OE end at y = -37 for now: they fill, the machines stop
  (back-pressure is the cap; the hub has 4 free slots and railgun ammo stacks to 10, so the hub is not the store). Stage 3 takes them on to the sides.
Steps: plan | build (saves first) | config | relief | priority | status | rates [SECONDS] | drain
  drain   TEST: moves the finished ammunition from OW / OE onto the stage-1 side belts (real product, nothing is created), so the works keep running
Usage: edge_works.py plan ; edge_works.py build ; edge_works.py status ; edge_works.py rates 120"""
import json
import sys
import time

import edge_ship as ES
import triangle_miner as TM
from _game import tools

L = tools["run_lua"]
Q = "legendary"
KEEP = 300                    # a plate leaves the hub for the works only while the hub holds more than this
BELT, UG = "express-transport-belt", "express-underground-belt"
ASM, CHEM, FUR = "assembling-machine-3", "chemical-plant", "electric-furnace"
Y_END = -36                   # last bus row
OUT_END = -37                 # last row of the two output belts


def T(name, tx, ty, d=0, w=1, h=1, recipe=None, **params):
    e = {"name": name, "x": tx + w / 2, "y": ty + h / 2, "direction": d, "params": dict({"quality": Q}, **params)}
    if recipe:
        e["recipe"] = recipe
    return e


def layout():
    e = []
    # hub ports and the plate belts
    for x in (-1, 3):
        # the port inserter itself (x,-5) is made by CONFIG, filter set in the same tick: placed unfiltered it put 24 foundations on the bus (2026-11-17)
        e += [T(UG, x, -6, 0, type="input"), T(UG, x, -10, 0, type="output"), T(BELT, x, -11, 0)]
    e += [T(BELT, -1, -12, 4), T(BELT, 0, -12, 4), T(BELT, 1, -12, 4), T(BELT, 3, -12, 12)]
    e += [T(BELT, 2, y, 0) for y in range(-12, Y_END - 1, -1)]
    e += [T(BELT, 1, y, 0) for y in range(-13, Y_END - 1, -1)]
    # chemical row
    e += [T("crusher", -9, -12, 4, 3, 2, "oxide-asteroid-crushing"), T("fast-inserter", -9, -10, 8), T("fast-inserter", -8, -10, 0),
          T("crusher", -5, -12, 4, 3, 2, "advanced-carbonic-asteroid-crushing"), T("fast-inserter", -5, -10, 8), T("fast-inserter", -4, -10, 0),
          T("fast-inserter", -9, -13, 8), T("fast-inserter", -5, -13, 8), T("fast-inserter", -3, -13, 8),
          T(CHEM, -11, -16, 8, 3, 3, "ice-melting"), T(CHEM, -7, -16, 0, 3, 3, "coal-synthesis"), T(CHEM, -3, -16, 0, 3, 3, "explosives"),
          T("fast-inserter", -4, -15, 12), T("fast-inserter", 0, -15, 12)]
    e += [T("pipe", x, -17) for x in range(-9, -2)]
    # west column: next to X (fast), P by long-handed
    e += [T(ASM, -3, -20, 0, 3, 3, "railgun-ammo"), T("fast-inserter", 0, -19, 4), T("fast-inserter", -4, -19, 4),
          T("fast-inserter", -2, -21, 0),
          T(ASM, -3, -24, 0, 3, 3, "copper-cable"), T("long-handed-inserter", 0, -23, 4),
          T("fast-inserter", -2, -25, 8),
          T(ASM, -3, -28, 0, 3, 3, "railgun-ammo"), T("fast-inserter", 0, -27, 4), T("fast-inserter", -4, -27, 4),
          T(ASM, -3, -31, 0, 3, 3, "rocket"), T("fast-inserter", 0, -30, 4), T("long-handed-inserter", 0, -31, 4),
          T("fast-inserter", -2, -32, 8),
          T(ASM, -3, -35, 0, 3, 3, "explosive-rocket"), T("fast-inserter", 0, -34, 4), T("fast-inserter", -4, -34, 4)]
    e += [T(BELT, -5, y, 0) for y in range(-19, OUT_END - 1, -1)]
    # east column: next to P (fast), X by long-handed
    # The bus flows north, so steel only reaches users NORTH of the furnace that made it: all six furnaces stand at the south end
    # (first build, 2026-11-17, had four of them north of every user: their steel filled the dead end and the piercing line starved).
    for top in (-14, -17, -20, -23, -26, -29):                                  # steel furnaces (the recipe follows the iron plate)
        e += [T(FUR, 4, top, 0, 3, 3), T("fast-inserter", 3, top, 12), T("long-handed-inserter", 3, top + 1, 4)]
    e += [T(ASM, 4, -32, 0, 3, 3, "firearm-magazine"), T("fast-inserter", 3, -31, 12),
          T("fast-inserter", 5, -33, 8),
          T(ASM, 4, -36, 0, 3, 3, "piercing-rounds-magazine"), T("fast-inserter", 3, -35, 12), T("long-handed-inserter", 3, -34, 12), T("fast-inserter", 7, -35, 12)]
    e += [T(BELT, 8, y, 0) for y in range(-35, OUT_END - 1, -1)]
    return e


def east_column():
    """The east column north of the first two furnaces (used once to re-order it; see the note in layout())."""
    return [e for e in layout() if e["x"] >= 3 and e["y"] <= -17]


def tiles_of(ents):
    out = set()
    for e in ents:
        w = h = 1
        if e["name"] in (ASM, CHEM, FUR):
            w = h = 3
        elif e["name"] == "crusher":
            w, h = 3, 2
        x0, y0 = round(e["x"] - w / 2), round(e["y"] - h / 2)
        out |= {(x0 + i, y0 + j) for i in range(w) for j in range(h)}
    return out


def plan():
    ents = layout()
    tiles = tiles_of(ents)
    cells = "{" + ",".join("{%d,%d}" % c for c in sorted(tiles)) + "}"
    print(len(ents), "entities on", len(tiles), "tiles")
    print(L(TM.AT + "local need=0 local blk={} for _,q in pairs(" + cells + ") do if s.get_tile(q[1],q[2]).name~='space-platform-foundation' then need=need+1 end "
            "for _,e in pairs(s.find_entities_filtered{area={{q[1]+0.1,q[2]+0.1},{q[1]+0.9,q[2]+0.9}}}) do if e.type~='tile-ghost' then local k=e.name..' @'..e.position.x..','..e.position.y blk[k]=true end end end "
            "local t={} for k in pairs(blk) do t[#t+1]=k end rcon.print('tiles without foundation '..need..' | standing in the way: '..(#t>0 and table.concat(t,'; ') or 'nothing'))"))
    ok, bad = TM.place(ents, False)
    print("dry run: would place", ok, "of", len(ents), "failed", bad)
    return ents


CONFIG = (TM.AT + "local W=defines.wire_connector_id local hub=p.hub local o={} local function at(n,x,y) return s.find_entities_filtered{name=n,position={x+0.5,y+0.5},radius=0.3}[1] end "
          "local function filt(e,names) e.use_filters=true e.inserter_filter_mode='whitelist' for i,n in pairs(names) do e.set_filter(i,{name=n,quality='normal',comparator='='}) end end "
          "pcall(function() hub.get_or_create_control_behavior().read_contents=true end) "
          "for _,q in pairs({{-1,'iron-plate'},{3,'copper-plate'}}) do local e=at('bulk-inserter',q[1],-5) or s.create_entity{name='bulk-inserter',position={q[1]+0.5,-4.5},direction=8,quality='legendary',force='player'} if e then filt(e,{q[2]}) local cb=e.get_or_create_control_behavior() cb.circuit_enable_disable=true "
          "cb.circuit_condition={first_signal={type='item',name=q[2]},comparator='>',constant=KEEPV} local a,b=hub.get_wire_connector(W.circuit_green,true),e.get_wire_connector(W.circuit_green,true) "
          "if not a.is_connected_to(b) then a.connect_to(b) end o[#o+1]='port '..q[2]..' ok' else o[#o+1]='NO port '..q[2] end end "
          "for _,q in pairs({{-9,'oxide-asteroid-chunk'},{-8,'oxide-asteroid-chunk'},{-5,'carbonic-asteroid-chunk'},{-4,'carbonic-asteroid-chunk'}}) do local e=at('fast-inserter',q[1],-10) if e then filt(e,{q[2]}) else o[#o+1]='NO ring inserter '..q[1] end end "
          "for _,q in pairs({{-9,-12,'oxide-asteroid-crushing'},{-5,-12,'advanced-carbonic-asteroid-crushing'}}) do local c=s.find_entities_filtered{name='crusher',area={{q[1],q[2]},{q[1]+3,q[2]+2}}}[1] "
          "if c then if not c.get_recipe() or c.get_recipe().name~=q[3] then c.set_recipe(q[3]) end else o[#o+1]='NO crusher '..q[1] end end "
          "local im=s.find_entities_filtered{name='chemical-plant',position={-9.5,-14.5},radius=0.5}[1] if im then im.direction=8 o[#o+1]='melter faces '..im.direction end "
          # sulfur guard: the explosives plant takes sulfur one at a time and only while it holds fewer than 2 (it hoarded sulfur, the coal plant starved)
          "local kc=s.find_entities_filtered{name='crusher',position={-3.5,-11},radius=0.5}[1] local ex=s.find_entities_filtered{name='chemical-plant',position={-1.5,-14.5},radius=0.5}[1] "
          "local si=at('fast-inserter',-3,-13) if si and ex then si.inserter_stack_size_override=1 filt(si,{'sulfur'}) local eb=ex.get_or_create_control_behavior() eb.circuit_read_contents=true eb.circuit_read_ingredients=false "
          "local a,b=ex.get_wire_connector(W.circuit_red,true),si.get_wire_connector(W.circuit_red,true) if not a.is_connected_to(b) then a.connect_to(b) end local ib=si.get_or_create_control_behavior() ib.circuit_enable_disable=true "
          "ib.circuit_condition={first_signal={type='item',name='sulfur'},comparator='<',constant=2} o[#o+1]='sulfur guard ok' end "
          # carbon chute: the modules the autopilot fits give the coal plant productivity, so a crush leaves carbon over (about 0.9 a crush at +45%); the crusher
          # filled with carbon and everything stopped. A one-tile hole in the deck at (-4,-14) and an inserter that drops carbon into it while the crusher holds more than 10.
          "if kc then s.set_tiles({{name='empty-space',position={-4,-14}}}) kc.get_or_create_control_behavior().circuit_read_contents=true o[#o+1]='chute: see RELIEF' end "
          "rcon.print(table.concat(o,' | '))")

# RELIEF (2026-11-18). The row wedged twice in one day: the crusher stops when it holds 6 sulfur, the coal plant sat on 4 carbon (it needs 5: the
# chute had taken an odd number) and nothing could move. Two faults in the first design: the chute looked at carbon only, and the sulfur guard read the
# plant's INGREDIENT signals on top of its contents (1 too many, so the plant only ever took sulfur when it held none).
# Now two decider combinators (tiles -6,-13 and -6,-11) read the crusher and set the chute inserter's FILTER:
#   carbon > 9 and sulfur < 2   -> the chute drops carbon   (carbon is in the way, sulfur is wanted)
#   sulfur > 3 and carbon < 5    -> the chute drops sulfur   (sulfur is in the way, carbon is wanted)
# With the line backed up both pile up, neither rule holds and the crusher simply stops. The chute moves one item at a time.
RELIEF_ENTS = [{"name": "decider-combinator", "x": -5.5, "y": -12.0, "direction": 0, "params": {"quality": "normal"}},
               {"name": "decider-combinator", "x": -5.5, "y": -10.0, "direction": 0, "params": {"quality": "normal"}}]
RELIEF = (TM.AT + "local W=defines.wire_connector_id local o={} local kc=s.find_entities_filtered{name='crusher',position={-3.5,-11},radius=0.5}[1] local ch=s.find_entities_filtered{type='inserter',position={-3.5,-12.5},radius=0.3}[1] "
          "local da=s.find_entities_filtered{name='decider-combinator',position={-5.5,-12},radius=0.6}[1] local db=s.find_entities_filtered{name='decider-combinator',position={-5.5,-10},radius=0.6}[1] "
          "if not (kc and ch and da and db) then rcon.print('MISSING: crusher '..tostring(kc~=nil)..' chute '..tostring(ch~=nil)..' deciders '..tostring(da~=nil)..' '..tostring(db~=nil)) return end "
          "local function I(n) return {type='item',name=n} end "
          "da.get_or_create_control_behavior().parameters={conditions={{first_signal=I('carbon'),comparator='>',constant=9},{first_signal=I('sulfur'),comparator='<',constant=2,compare_type='and'}},outputs={{signal=I('carbon'),copy_count_from_input=false,constant=1}}} "
          "db.get_or_create_control_behavior().parameters={conditions={{first_signal=I('sulfur'),comparator='>',constant=3},{first_signal=I('carbon'),comparator='<',constant=5,compare_type='and'}},outputs={{signal=I('sulfur'),copy_count_from_input=false,constant=1}}} "
          "kc.get_or_create_control_behavior().circuit_read_contents=true local kg=kc.get_wire_connector(W.circuit_green,true) "
          "local cg=ch.get_wire_connector(W.circuit_green,true) if cg.is_connected_to(kg) then cg.disconnect_from(kg) end "
          "for _,d in pairs({da,db}) do local di=d.get_wire_connector(W.combinator_input_green,true) if not di.is_connected_to(kg) then di.connect_to(kg) end "
          "local dout=d.get_wire_connector(W.combinator_output_red,true) local cr=ch.get_wire_connector(W.circuit_red,true) if not dout.is_connected_to(cr) then dout.connect_to(cr) end end "
          "ch.use_filters=true ch.inserter_filter_mode='whitelist' for i=1,ch.filter_slot_count do ch.set_filter(i,nil) end ch.inserter_stack_size_override=1 "
          "local cb=ch.get_or_create_control_behavior() cb.circuit_set_filters=true cb.circuit_enable_disable=true cb.circuit_condition={first_signal={type='virtual',name='signal-anything'},comparator='>',constant=0} "
          "local ex=s.find_entities_filtered{name='chemical-plant',position={-1.5,-14.5},radius=0.5}[1] if ex then ex.get_or_create_control_behavior().circuit_read_ingredients=false end "
          "rcon.print('relief wired: carbon rule '..helpers.table_to_json(da.get_control_behavior().parameters.conditions):sub(1,160)..' | chute set_filters '..tostring(cb.circuit_set_filters))")

# PRIORITY (2026-11-18, after the breach on the Gleba -> Nauvis leg). The two railgun-round assemblers stand first on the bus. A round takes 5 steel
# (25 iron plate) and 10 cable (5 copper plate); with their belts open they ran flat out, the hub's copper fell under 300 (the copper port shuts
# there), the furnaces took the iron, and piercing magazines fell from about 150 a minute to 77 against 327 used: both flanks ran dry and were holed.
# Now the railgun assemblers' steel-and-explosives inserters (0,-19) and (0,-27) run only while the PIERCING assembler holds more than 8 finished
# magazines, which it only does when the magazine belts are full or the uranium reserve is flowing: magazines first, railgun rounds from what is left.
# Green wire from the piercing assembler along the furnace inserters on column 3 (relays only; they carry no condition).
PRIORITY = (TM.AT + "local W=defines.wire_connector_id local o={} local function ins(x,y) return s.find_entities_filtered{type='inserter',position={x+0.5,y+0.5},radius=0.3}[1] end "
            "local pm=s.find_entities_filtered{type='assembling-machine',position={5.5,-34.5},radius=0.5}[1] if not pm then rcon.print('NO piercing assembler') return end "
            "local cb=pm.get_or_create_control_behavior() cb.circuit_read_contents=true cb.circuit_read_ingredients=false "
            "local chain={pm} for _,q in pairs({{3,-31},{3,-29},{3,-26},{3,-23},{3,-20}}) do local i=ins(q[1],q[2]) if i then chain[#chain+1]=i else o[#o+1]='no relay at '..q[1]..','..q[2] end end "
            "for k=2,#chain do local a,b=chain[k-1].get_wire_connector(W.circuit_green,true),chain[k].get_wire_connector(W.circuit_green,true) if not a.is_connected_to(b) then if a.can_wire_reach(b) then a.connect_to(b) else o[#o+1]='CANNOT REACH relay '..k end end end "
            "for _,q in pairs({{0,-27,3},{0,-19,6}}) do local i=ins(q[1],q[2]) local r=chain[q[3]] if i and r then local a,b=r.get_wire_connector(W.circuit_green,true),i.get_wire_connector(W.circuit_green,true) "
            "if not a.is_connected_to(b) then if a.can_wire_reach(b) then a.connect_to(b) else o[#o+1]='CANNOT REACH '..q[1]..','..q[2] end end "
            "local ib=i.get_or_create_control_behavior() ib.circuit_enable_disable=true ib.circuit_condition={first_signal={type='item',name='piercing-rounds-magazine'},comparator='>',constant=8} o[#o+1]='gated '..q[1]..','..q[2] end end "
            "rcon.print(table.concat(o,' | '))")

STATUS = (TM.AT + "local m={} for k,v in pairs(defines.entity_status) do m[v]=k end local o={} "
          "for _,e in pairs(s.find_entities_filtered{type={'assembling-machine','furnace'},area={{-12,-38},{9,-10}}}) do local rc=e.get_recipe() if not rc and e.type=='furnace' and e.previous_recipe then rc=e.previous_recipe end "
          "local out={} local inv=e.get_output_inventory() if inv then for _,i in pairs(inv.get_contents()) do out[#out+1]=i.name..' '..i.count end end "
          "local fl={} for i=1,4 do local ok,x=pcall(function() return e.get_fluid(i) end) if ok and x then fl[#fl+1]=x.name..' '..math.floor(x.amount) end end "
          "local nm=rc and rc.name or e.name if type(nm)~='string' then nm=nm.name end o[#o+1]=string.format('%-36s @%5.1f,%5.1f %-28s made %d  out[%s] %s',nm,e.position.x,e.position.y,tostring(m[e.status]),e.products_finished,table.concat(out,', '),table.concat(fl,', ')) end table.sort(o) "
          "local function belt(x,y0,y1) local c={} for y=y0,y1,-1 do local b=s.find_entities_filtered{name='express-transport-belt',position={x+0.5,y+0.5},radius=0.3}[1] if b then for li=1,2 do for _,i in pairs(b.get_transport_line(li).get_contents()) do "
          "local k=i.name..(li==1 and ' (L)' or ' (R)') c[k]=(c[k] or 0)+i.count end end end end local t={} for k,v in pairs(c) do t[#t+1]=k..' '..v end table.sort(t) return #t>0 and table.concat(t,', ') or 'empty' end "
          "o[#o+1]='bus X: '..belt(1,-13,YEND) o[#o+1]='bus P: '..belt(2,-12,YEND) o[#o+1]='out west: '..belt(-5,-19,OEND) o[#o+1]='out east: '..belt(8,-35,OEND) "
          "local inv=p.hub.get_inventory(defines.inventory.hub_main) o[#o+1]='hub: iron plate '..inv.get_item_count('iron-plate')..', copper plate '..inv.get_item_count('copper-plate')..', free slots '..inv.count_empty_stacks() "
          "local np=0 for _,e in pairs(s.find_entities_filtered{area={{-12,-38},{9,-5}}}) do if e.status==defines.entity_status.no_power or e.status==defines.entity_status.low_power then np=np+1 end end o[#o+1]='without power: '..np "
          "rcon.print(table.concat(o,string.char(10)))")

MADE = (TM.AT + "local t={} for _,e in pairs(s.find_entities_filtered{type={'assembling-machine','furnace'},area={{-12,-38},{9,-10}}}) do local rc=e.get_recipe() if not rc and e.type=='furnace' and e.previous_recipe then rc=e.previous_recipe end "
        "local k=rc and rc.name or e.name if type(k)~='string' then k=k.name end t[k]=(t[k] or 0)+e.products_finished end local o={} for k,v in pairs(t) do o[#o+1]=k..'='..v end rcon.print(game.tick..'|'..table.concat(o,';'))")

DRAIN = (TM.AT + "local moved={} local function take(x,y0,y1) local got={} for y=y0,y1,-1 do local b=s.find_entities_filtered{name='express-transport-belt',position={x+0.5,y+0.5},radius=0.3}[1] if b then for li=1,2 do local tl=b.get_transport_line(li) "
         "for _,i in pairs(tl.get_contents()) do got[i.name]=(got[i.name] or 0)+i.count end tl.clear() end end end return got end "
         "local got=take(-5,-19,OEND) for k,v in pairs(take(8,-18,OEND)) do got[k]=(got[k] or 0)+v end "
         "local sides={SIDEA,SIDEB} local lost={} for name,cnt in pairs(got) do local left=cnt for pass=1,2 do for _,cells in pairs(sides) do local share=math.ceil(left/(pass==1 and 2 or 1)) "
         "for _,q in pairs(cells) do local b=s.find_entities_filtered{name='express-transport-belt',position={q[1]+0.5,q[2]+0.5},radius=0.3}[1] if b and share>0 and left>0 then for li=1,2 do local tl=b.get_transport_line(li) "
         "for pos=0.1,0.9,0.25 do if share>0 and left>0 and tl.can_insert_at(pos) and tl.insert_at(pos,{name=name,count=1}) then share=share-1 left=left-1 end end end end end end end "
         "moved[#moved+1]=name..' '..(cnt-left)..(left>0 and (' (NOT placed '..left..')') or '') lost[name]=left end "
         "for name,left in pairs(lost) do if left>0 then local b=s.find_entities_filtered{name='express-transport-belt',position={-4.5,-18.5},radius=0.3}[1] for li=1,2 do local tl=b.get_transport_line(li) for pos=0.1,0.9,0.25 do "
         "if left>0 and tl.can_insert_at(pos) and tl.insert_at(pos,{name=name,count=1}) then left=left-1 end end end end end "
         "rcon.print(#moved>0 and table.concat(moved,', ') or 'nothing on the output belts')")


def sub(code):
    return code.replace("KEEPV", str(KEEP)).replace("YEND", str(Y_END)).replace("OEND", str(OUT_END))


def made():
    t, body = L(MADE).split("|", 1)
    return int(t), {k: int(v) for k, v in (kv.split("=") for kv in body.split(";") if "=" in kv)}


def side_cells():
    sides = ES.both(TM.Y_TOP, 100)
    return ["{" + ",".join("{%d,%d}" % (b[0], b[1]) for b in sides[side][0][:150]) + "}" for side in (-1, 1)]


def rates(seconds, draining=None):
    """Products finished per game minute, by recipe, over `seconds` of real time (the game may run faster or slower: the tick count decides)."""
    t0, a = made()
    if draining:                                   # keep the output belts empty, so the rate is the works' own and not the full belt's
        end = time.time() + seconds
        while time.time() < end:
            L(sub(DRAIN).replace("SIDEA", draining[0]).replace("SIDEB", draining[1]))
            time.sleep(4)
    else:
        time.sleep(seconds)
    t1, b = made()
    mins = (t1 - t0) / 3600.0
    if mins <= 0:
        sys.exit("the game did not advance (paused?)")
    print("over %.2f game minutes (crafts finished per minute; a craft may give more than one item):" % mins)
    for k in sorted(b):
        print("  %-38s %7.1f /min" % (k, (b[k] - a.get(k, 0)) / mins))


def drain():
    cells = side_cells()
    print(L(sub(DRAIN).replace("SIDEA", cells[0]).replace("SIDEB", cells[1])))


def main():
    step = sys.argv[1] if len(sys.argv) > 1 else "status"
    if step == "plan":
        plan()
    elif step == "build":
        ents = layout()
        print("save:", tools["save_game"]("pre-edge-works"))
        ok, bad = TM.place(ents, True)
        print("placed", ok, "of", len(ents), "failed", bad)
        print(L(sub(CONFIG)))
    elif step == "reorder-east":
        drain()
        print(L(TM.AT + "local n=0 for _,e in pairs(s.find_entities_filtered{area={{3.1,-37.9},{8.9,-17.1}}}) do if e.valid and e.type~='tile-ghost' then e.destroy() n=n+1 end end rcon.print('removed '..n)"))
        ok, bad = TM.place(east_column(), True)
        print("placed", ok, "failed", bad)
    elif step == "config":
        print(L(sub(CONFIG)))
        print(L(RELIEF))
    elif step == "priority":
        print(L(PRIORITY))
    elif step == "relief":
        print("deciders:", TM.place(RELIEF_ENTS, True) if not L(TM.AT + "rcon.print(s.count_entities_filtered{name='decider-combinator',area={{-6,-13},{-5,-9}}})").strip() == "2" else "standing")
        print(L(RELIEF))
    elif step == "status":
        print(L(sub(STATUS)))
    elif step == "rates":
        rates(int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 60, side_cells() if "--drain" in sys.argv else None)
    elif step == "drain":
        drain()
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
