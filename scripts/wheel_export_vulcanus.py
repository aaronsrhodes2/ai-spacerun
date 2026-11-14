#!/usr/bin/env python3
"""The export line of a wheel: low density structure from the HUB'S OWN STOCK (the Captain, 2026-11-14: the Vulcanus Wheel's export
role is low density structure, "increase production ... to the maximum those stations can").

Why: the rocket district (wheel_rocket.py) lives on chunks tapped off the west spoke and made 0.5 to 2 low density structures a
minute while the hub stood full of carbon, sulfur, ore and ice and the centre's crushers reprocessed 700 chunks a minute for nothing.
This line takes carbon, sulfur, copper ore, iron ore, ice, calcite and iron plate OUT of the hub and makes plastic and metal from them.

  hub      the west product column (x=-6) had four inserters INTO the hub and used one. The two southern ones (-5,-2 and -5,-1) are
           turned round: they now take OUT of the hub, each on its own lane of the feed belt, filters set by circuit:
             A (-5,-1): carbon, copper ore, iron ore        B (-5,-2): sulfur, ice, calcite, iron plate
           The product column now ends at (-6,-3), turned east so that it feeds nothing.
  control  rows -3/-2, x -13..-9: per inserter an arithmetic combinator (every feed belt, read in hold mode, times -1), a constant
           combinator (TARGETS) and a decider. An item is loaded while the feed carries less than its target AND the hub holds more
           than RESERVE of it AND the hub holds fewer than CAP of the product. So science keeps first call on everything, and the
           line stops by itself at the cap.
  feed     one belt: west along y=-1 (under the bridge bay and the product column), under the chunk loop along y=0, south down
           x=-60, west along y=12 (the free deck row under the district's corridor), south down x=-117 under the corridor's inner
           winding and the out-belt into the heart chamber. It is NOT a dead end: after the machines it runs into the start of the
           district's ore belt (-128,55), so whatever is not used feeds the district's own melters and loop and then rides home to
           the hub on the district's out-belt. Nothing can pile up; the targets only set how much is under way.
  metals   (heart, north-west): iron melter -130..-126 and copper melter -124..-120 (y 33..37) on the feed row y=39, pipe row y=32,
           casting foundry -127..-123, y 27..31. Its output inserter (-125,26) lays the product straight on the district's out-belt
           (y=25), gated on the hub's stock (CAP).
  ice      melter -121..-119, y 27..29 on the feed column; water by pipe down x=-119 to the main (y=44)
  chem     (heart, south-west; the district's own chemistry block turned by 180 degrees, so every port sits as in wheel_rocket.py):
           coal plant C1 -> refinery (simple coal liquefaction, acid from the plant under C1) -> heavy cracking -> light cracking
           -> plastic, port to port; a second coal plant C3 under the plastic plant feeds it coal by hand. Plastic rides its own
           pure belt (x=-131, y 43..30) to the casting foundry.
  feed order  ice melter, copper melter, iron melter (y=39), C1 (y=43), acid plant, refinery calcite, C3 (y=54), then the ore belt.
One coal plant (C1, 53 coal a minute with three epic productivity modules) is the line's designed ceiling: about 30 a minute.
Never apply twice on the same wheel. After a quality upgrade: config (belt readers and over-reach wires).
`wheel_rocket.py config` on this wheel puts the district's own export gate back to 2,000: run `config` here after it.
Usage: wheel_export_vulcanus.py check | build [--apply] | config | off | status   [--only PLANET]   (default: --only vulcanus)"""
import sys

from _game import tools
from _wheels import place_all, wheels

PRODUCT = "low-density-structure"
CAP = 4000                    # product in the hub: the export stock (10 a slot: 400 slots)
RESERVE = 2000                # the line never takes an item the hub holds fewer than this of
TARGETS_A = {"carbon": 260, "copper-ore": 120, "iron-ore": 40}
TARGETS_B = {"sulfur": 70, "ice": 100, "calcite": 20, "iron-plate": 4}
Q = {"quality": "epic"}
N, E, S, W = 0, 4, 8, 12
DIR = {(0, -1): N, (1, 0): E, (0, 1): S, (-1, 0): W}
ents, cfg, recipes, occ, tiles, fluid, opening, feed = [], [], [], {}, set(), {}, {}, []


def put(name, tx, ty, w=1, h=1, d=N, filt=None, recipe=None, **params):
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
        recipes.append((e["x"], e["y"], recipe, d))
    return e


def ins(x, y, d, filt=None, name="fast-inserter"):
    return put(name, x, y, d=d, filt=filt)


def pipe(f, *ts):
    for x, y in ts:
        put("pipe", x, y)
        fluid[(x, y)] = f


def ptg(f, x, y, d):
    put("pipe-to-ground", x, y, d=d)
    fluid[(x, y)] = f
    opening[(x, y)] = {v: k for k, v in DIR.items()}[d]


def run(x, y, d, n=1, new=True):
    """n belt tiles from x,y in direction d; returns the next tile. Existing tiles (new=False) are only listed for the wire."""
    dx, dy = {v: k for k, v in DIR.items()}[d]
    for _ in range(n):
        if new:
            put("express-transport-belt", x, y, d=d)
        feed.append((x + .5, y + .5))
        x, y = x + dx, y + dy
    return x, y


def under(x, y, d, gap):
    """Underground pair: entrance at x,y, exit gap tiles on; returns the tile after the exit."""
    dx, dy = {v: k for k, v in DIR.items()}[d]
    put("express-underground-belt", x, y, d=d, type="input")
    put("express-underground-belt", x + dx * gap, y + dy * gap, d=d, type="output")
    return x + dx * (gap + 1), y + dy * (gap + 1)


def layout():
    # ---- hub end: (-6,-2) and (-6,-1) stand already (the product column's last two tiles) and are turned west by `config` ----
    feed.extend([(-5.5, -1.5), (-5.5, -0.5)])
    put("express-transport-belt", -7, -1, d=N)                             # A's stub: side-loads onto the south lane of y=-2
    feed.append((-6.5, -0.5))
    p = run(-7, -2, W)
    p = run(*p, S)                                                         # -8,-2
    p = run(*p, W, 24)                                                     # -8,-1 .. -31,-1
    p = under(*p, W, 5)                                                    # -32 > -37 under the bridge bay
    p = run(*p, W)                                                         # -38
    p = under(*p, W, 2)                                                    # -39 > -41 under the product column
    p = run(*p, S)                                                         # -42,-1
    p = run(*p, W, 3)                                                      # -42,0 .. -44,0
    p = under(*p, W, 8)                                                    # -45 > -53 under the chunk loop and two inserters
    p = run(*p, W, 2)                                                      # -54, -55
    p = under(*p, W, 2)                                                    # -56 > -58 under the spiral out-belt's exit
    p = run(*p, W)                                                         # -59,0
    p = run(*p, S, 2)                                                      # -60,0 -60,1
    p = under(*p, S, 2)                                                    # -60,2 > -60,4 under the district's out-belt
    p = run(*p, S, 7)                                                      # -60,5 .. 11
    p = run(*p, W, 57)                                                     # -60,12 .. -116,12
    p = run(*p, S, 3)                                                      # -117,12 .. 14
    p = under(*p, S, 4)                                                    # 15 > 19 under the inner winding
    p = run(*p, S, 4)                                                      # 20 .. 23
    p = under(*p, S, 2)                                                    # 24 > 26 under the out-belt's top row
    p = run(*p, S, 12)                                                     # -117,27 .. 38
    p = run(*p, W, 13)                                                     # -117,39 .. -129,39
    p = run(*p, S, 4)                                                      # -130,39 .. 42
    p = run(*p, E, 20)                                                     # -130,43 .. -111,43
    p = run(*p, S, 11)                                                     # -110,43 .. 53
    p = run(*p, W, 22)                                                     # -110,54 .. -131,54
    p = run(*p, S)                                                         # -132,54
    p = run(*p, E, 4)                                                      # -132,55 .. -129,55 > the ore belt at -128,55
    assert p == (-128, 55), p
    # ---- control ----
    for x, nm in ((-9, "arithmetic-combinator"), (-10, "decider-combinator"), (-11, "arithmetic-combinator"), (-12, "decider-combinator")):
        put(nm, x, -3, 1, 2)
    put("constant-combinator", -13, -3)
    put("constant-combinator", -13, -2)
    # ---- ice ----
    put("chemical-plant", -121, 27, 3, 3, d=N, recipe="ice-melting")
    ins(-118, 28, E, ["ice"])
    pipe("water", (-121, 30), (-120, 30), (-119, 30), *[(-119, y) for y in range(31, 38)])
    ptg("water", -119, 38, N)
    ptg("water", -119, 44, S)
    pipe("water", (-120, 45), (-119, 45), (-118, 45))
    # ---- metals ----
    put("foundry", -130, 33, 5, 5, recipe="iron-ore-melting")
    ins(-128, 38, S, ["iron-ore", "calcite"], name="bulk-inserter")
    put("foundry", -124, 33, 5, 5, recipe="copper-ore-melting")
    ins(-122, 38, S, ["copper-ore", "calcite"], name="bulk-inserter")
    pipe("iron", *[(x, 32) for x in range(-129, -125)])
    pipe("copper", *[(x, 32) for x in range(-124, -120)])
    put("foundry", -127, 27, 5, 5, recipe="casting-low-density-structure")
    ins(-128, 30, W, ["plastic-bar"], name="bulk-inserter")
    ins(-125, 26, S, [PRODUCT])                                            # onto the district's out-belt, gated on the hub in config
    # ---- plastic belt (pure): from the plastic plant's long hand at -131,43 north to the foundry ----
    for y in range(43, 30, -1):
        put("express-transport-belt", -131, y, d=N)
    put("express-transport-belt", -131, 30, d=E)
    put("express-transport-belt", -130, 30, d=E)
    put("express-transport-belt", -129, 30, d=E)
    # ---- chemistry: wheel_rocket.py's block turned by 180 degrees (tile x' = -94 - x, y' = 70 - y) ----
    put("chemical-plant", -132, 46, 3, 3, d=E, recipe="plastic-bar")
    ins(-131, 45, S, ["plastic-bar"], name="long-handed-inserter")         # plant -> plastic belt, over the water main
    put("chemical-plant", -129, 46, 3, 3, d=E, recipe="light-oil-cracking")
    put("chemical-plant", -125, 48, 3, 3, d=E, recipe="heavy-oil-cracking")
    put("oil-refinery", -120, 46, 5, 5, d=W, recipe="simple-coal-liquefaction")
    ins(-118, 52, S, ["calcite"], name="long-handed-inserter")
    put("chemical-plant", -114, 49, 3, 3, d=E, recipe="sulfuric-acid")
    ins(-113, 52, S, ["sulfur", "iron-plate"], name="long-handed-inserter")
    put("chemical-plant", -114, 46, 3, 3, d=E, recipe="coal-synthesis")    # C1: coal for the refinery
    ins(-113, 45, N, ["carbon", "sulfur"], name="long-handed-inserter")
    ins(-115, 47, E, ["coal"])
    put("chemical-plant", -132, 50, 3, 3, d=N, recipe="coal-synthesis")    # C3: coal for the plastic plant
    ins(-131, 53, S, ["carbon", "sulfur"])
    ins(-131, 49, S, ["coal"])
    pipe("water", *[(x, 44) for x in range(-132, -110) if x != -119])
    pipe("water", (-126, 45), (-126, 46), (-122, 45), (-122, 46), (-122, 47), (-122, 48), *[(-111, y) for y in range(45, 50)])
    ptg("water", -132, 45, N)
    ptg("water", -132, 49, S)
    ptg("water", -130, 45, N)
    ptg("water", -130, 49, S)
    pipe("acid", (-115, 49))
    pipe("heavy", (-121, 50), (-122, 50))
    pipe("light", (-126, 48))
    for (x, y), f in fluid.items():
        for dx, dy in DIR:
            n = (x + dx, y + dy)
            g = fluid.get(n)
            joins = opening.get((x, y), (dx, dy)) == (dx, dy) and opening.get(n, (-dx, -dy)) == (-dx, -dy)
            assert g is None or g == f or not joins, "%s pipe at %s touches %s" % (f, (x, y), g)
    return {"entities": len(ents), "feed belts on the wire": len(feed), "deck tiles wanted": len(tiles)}


def lua_list(rows):
    return "{" + ",".join("{" + ",".join(("'%s'" % v) if isinstance(v, str) else ("{" + ",".join("'%s'" % f for f in v) + "}") if isinstance(v, list) else str(v) for v in r) + "}" for r in rows) + "}"


def lua_map(d):
    return "{" + ",".join("['%s']=%d" % kv for kv in d.items()) + "}"


CHECK = ("local s=game.surfaces['SURF'] local o={} local nt=0 for _,p in pairs(TILES) do local t=s.get_tile(p[1],p[2]) if not t.valid or t.name~='space-platform-foundation' then nt=nt+1 end end o[#o+1]='tiles without deck '..nt "
         "local nl,nb=0,0 for _,p in pairs(OCC) do for _,e in pairs(s.find_entities_filtered{area={{p[1]+0.1,p[2]+0.1},{p[1]+0.9,p[2]+0.9}}}) do if e.type=='lamp' then nl=nl+1 elseif e.type~='tile-ghost' then nb=nb+1 if nb<=12 then o[#o+1]='IN THE WAY '..e.name..' at '..e.position.x..','..e.position.y end end end end "
         "o[#o+1]='lamps in the way '..nl..', other entities in the way '..nb "
         "for _,q in pairs{{-6,-4},{-6,-3},{-6,-2},{-6,-1},{-128,55},{-125,25}} do local b=s.find_entities_filtered{type='transport-belt',position={q[1]+0.5,q[2]+0.5},radius=0.3}[1] o[#o+1]='belt '..q[1]..','..q[2]..' '..(b and ('dir '..b.direction) or 'NONE') end "
         "for y=-4,-1 do local i=s.find_entities_filtered{type='inserter',position={-4.5,y+0.5},radius=0.3}[1] o[#o+1]='hub inserter -5,'..y..' '..(i and (i.name..' dir '..i.direction..' '..i.quality.name) or 'NONE') end "
         "local hub=s.platform.hub local inv=hub.get_inventory(defines.inventory.hub_main) local g=hub.get_signals(defines.wire_connector_id.circuit_green) local r=hub.get_signals(defines.wire_connector_id.circuit_red) "
         "local function sig(t,n) for _,q in pairs(t or {}) do if q.signal.name==n then return q.count end end return 'none' end "
         "o[#o+1]='hub carbon '..inv.get_item_count('carbon')..', on green '..tostring(sig(g,'carbon'))..', on red '..tostring(sig(r,'carbon'))..', providing '..tostring(hub.providing_to_other_platforms) rcon.print(table.concat(o,'\\n'))")
LAMPS = "local s=game.surfaces['SURF'] local n=0 for _,p in pairs(OCC) do for _,e in pairs(s.find_entities_filtered{type='lamp',area={{p[1]+0.1,p[2]+0.1},{p[1]+0.9,p[2]+0.9}}}) do e.destroy() n=n+1 end end rcon.print('lamps in the way removed '..n)"
DECK = ("local s=game.surfaces['SURF'] local add={} for _,p in pairs(TILES) do local t=s.get_tile(p[1],p[2]) if t.valid and t.name=='empty-space' then add[#add+1]={name='space-platform-foundation',position=p} end end "
        "s.set_tiles(add) rcon.print('deck tiles laid '..#add)")
# the product column's end is turned away BEFORE anything is placed in front of it
TURN = ("local s=game.surfaces['SURF'] local b=s.find_entities_filtered{type='transport-belt',position={-5.5,-2.5},radius=0.3}[1] b.direction=defines.direction.east rcon.print('product column now ends at -6,-3 facing '..b.direction)")
CONFIG = ("local s=game.surfaces['SURF'] local hub=s.platform.hub local W=defines.wire_connector_id local o={} local function at(t,x,y,r) return s.find_entities_filtered{type=t,position={x,y},radius=r or 0.3}[1] end "
          "local function mach(x,y) return s.find_entities_filtered{type='assembling-machine',position={x,y},radius=0.5}[1] end pcall(function() hub.get_or_create_control_behavior().read_contents=true end) "
          "local n,r=0,0 for _,q in pairs(FILT) do local i=at('inserter',q[1],q[2]) if i then i.use_filters=true i.inserter_filter_mode='whitelist' for k,name in pairs(q[3]) do i.set_filter(k,name) end n=n+1 end end "
          "for _,q in pairs(REC) do local m=mach(q[1],q[2]) if m then if not (m.get_recipe() and m.get_recipe().name==q[3]) then m.set_recipe(q[3]) end if m.name~='foundry' then m.direction=q[4] end r=r+1 end end o[#o+1]='filters '..n..', recipes '..r "
          # the two hub inserters: filters by circuit first, then turned round
          "local dec={A=at('decider-combinator',-9.5,-2,0.6),B=at('decider-combinator',-11.5,-2,0.6)} local ar={A=at('arithmetic-combinator',-8.5,-2,0.6),B=at('arithmetic-combinator',-10.5,-2,0.6)} local cc={A=at('constant-combinator',-12.5,-2.5),B=at('constant-combinator',-12.5,-1.5)} "
          "local hi={A=at('inserter',-4.5,-0.5),B=at('inserter',-4.5,-1.5)} local tg={A=TA,B=TB} "
          "local prev,nb=nil,0 for _,p in pairs(FEED) do local b=at('transport-belt',p[1],p[2]) if b then local bc=b.get_or_create_control_behavior() bc.read_contents=true bc.read_contents_mode=defines.control_behavior.transport_belt.content_read_mode.hold "
          "local c=b.get_wire_connector(W.circuit_green,true) c.disconnect_all() if prev then c.connect_to(prev.get_wire_connector(W.circuit_green,true),false) end prev=b nb=nb+1 end end o[#o+1]='feed belts read '..nb "
          "local first=at('transport-belt',-5.5,-1.5) "
          "for _,k in pairs{'A','B'} do local d,a,c,i=dec[k],ar[k],cc[k],hi[k] "
          "for _,id in pairs{W.combinator_input_red,W.combinator_input_green,W.combinator_output_red,W.combinator_output_green} do d.get_wire_connector(id,true).disconnect_all() a.get_wire_connector(id,true).disconnect_all() end "
          "for _,id in pairs{W.circuit_red,W.circuit_green} do c.get_wire_connector(id,true).disconnect_all() i.get_wire_connector(id,true).disconnect_all() end "
          "local ccb=c.get_or_create_control_behavior() while ccb.sections_count>0 do ccb.remove_section(1) end local sec=ccb.add_section() local j=0 for name,v in pairs(tg[k]) do j=j+1 sec.set_slot(j,{value={type='item',name=name,quality='normal'},min=v}) end "
          "a.get_or_create_control_behavior().parameters={first_signal={type='virtual',name='signal-each'},second_constant=-1,operation='*',output_signal={type='virtual',name='signal-each'}} "
          "a.get_wire_connector(W.combinator_input_green,true).connect_to(first.get_wire_connector(W.circuit_green,true),false) "
          "local dr=d.get_wire_connector(W.combinator_input_red,true) dr.connect_to(a.get_wire_connector(W.combinator_output_red,true),false) dr.connect_to(c.get_wire_connector(W.circuit_red,true),false) "
          "d.get_wire_connector(W.combinator_input_green,true).connect_to(hub.get_wire_connector(W.circuit_green,true),false) "
          "d.get_or_create_control_behavior().parameters={conditions={{first_signal={type='virtual',name='signal-each'},first_signal_networks={red=true,green=false},comparator='>',constant=0},"
          "{first_signal={type='virtual',name='signal-each'},first_signal_networks={red=false,green=true},comparator='>',constant=RESERVE,compare_type='and'},"
          "{first_signal={type='item',name='PRODUCT'},first_signal_networks={red=false,green=true},comparator='<',constant=CAPSIG,compare_type='and'}},"
          "outputs={{signal={type='virtual',name='signal-each'},copy_count_from_input=false,constant=1}}} "
          "i.use_filters=true i.inserter_filter_mode='whitelist' local ib=i.get_or_create_control_behavior() ib.circuit_set_filters=true ib.circuit_enable_disable=true ib.circuit_condition={first_signal={type='virtual',name='signal-anything'},comparator='>',constant=0} "
          "i.get_wire_connector(W.circuit_red,true).connect_to(d.get_wire_connector(W.combinator_output_red,true),false) "
          "if i.direction~=defines.direction.east then i.direction=defines.direction.east end end "
          "for _,p in pairs{{-5.5,-1.5},{-5.5,-0.5}} do local b=at('transport-belt',p[1],p[2]) b.direction=defines.direction.west end o[#o+1]='hub inserters A and B take out of the hub, facing '..hi.A.direction..' and '..hi.B.direction "
          # the product leaves for the hub while the hub holds fewer than CAP: the line's own inserter and the district's
          "local function cond(i,sig,cmp,k) local c=i.get_wire_connector(W.circuit_red,true) c.disconnect_all() c.connect_to(hub.get_wire_connector(W.circuit_red,true),false) local cb=i.get_or_create_control_behavior() cb.circuit_enable_disable=true cb.circuit_condition={first_signal={type='item',name=sig},comparator=cmp,constant=k} end "
          "cond(at('inserter',-124.5,26.5),'PRODUCT','<',CAPSIG) local de=at('inserter',-89.5,38.5) local fq=de and de.get_filter(1) if fq and (type(fq)=='table' and fq.name or fq)=='PRODUCT' then cond(de,'PRODUCT','<',CAPSIG) o[#o+1]='district export gate raised too' end "
          "hub.providing_to_other_platforms=true o[#o+1]='hub provides to other platforms: '..tostring(hub.providing_to_other_platforms) rcon.print(table.concat(o,', '))")
OFF = ("local s=game.surfaces['SURF'] for _,y in pairs{-0.5,-1.5} do local i=s.find_entities_filtered{type='inserter',position={-4.5,y},radius=0.3}[1] local cb=i.get_or_create_control_behavior() cb.circuit_enable_disable=true "
       "cb.circuit_condition={first_signal={type='virtual',name='signal-red'},comparator='>',constant=0} end rcon.print('both hub inserters of the export line stopped (condition signal-red > 0); `config` starts them again')")
STATUS = ("local s=game.surfaces['SURF'] local hub=s.platform.hub local function sn(e) for n,x in pairs(defines.entity_status) do if x==e.status then return n end end return '?' end local o={} "
          "for _,q in pairs(REC) do local m=s.find_entities_filtered{type='assembling-machine',position={q[1],q[2]},radius=0.5}[1] if m then local fl={} for k,v in pairs(m.get_fluid_contents()) do fl[#fl+1]=k..' '..math.floor(v) end "
          "local mi=m.get_module_inventory() o[#o+1]=string.format('%-30s %-26s made %6d  modules %d/%d  %s',q[3],sn(m),m.products_finished,mi.get_item_count(),#mi,table.concat(fl,', ')) else o[#o+1]=q[3]..' MISSING' end end "
          "local t={} local nb=0 for _,p in pairs(FEED) do local b=s.find_entities_filtered{type='transport-belt',position={p[1],p[2]},radius=0.3}[1] if b then nb=nb+1 for l=1,2 do for _,it in pairs(b.get_transport_line(l).get_contents()) do t[it.name]=(t[it.name] or 0)+it.count end end end end "
          "local q={} for k,v in pairs(t) do q[#q+1]=k..' '..v end table.sort(q) o[#o+1]='ON THE BELT ('..nb..' belts): '..table.concat(q,', ') "
          "for k,y in pairs{A=-0.5,B=-1.5} do local i=s.find_entities_filtered{type='inserter',position={-4.5,y},radius=0.3}[1] local f={} for j=1,i.filter_slot_count do local fq=i.get_filter(j) if fq then f[#f+1]=type(fq)=='table' and fq.name or fq end end o[#o+1]='hub inserter '..k..' '..sn(i)..' filters now ['..table.concat(f,',')..']' end "
          "local w=0 for _,b in pairs(s.find_entities_filtered{type='transport-belt',area={{-31,-4},{-6,-3}}}) do for l=1,2 do w=w+b.get_transport_line(l).get_item_count() end end o[#o+1]='west product belt, 25 tiles before the hub: '..w..' items (200 = standing full)' "
          "local f=game.forces.player.get_item_production_statistics(s) local inv=hub.get_inventory(defines.inventory.hub_main) "
          "for _,n in pairs{'PRODUCT','plastic-bar','coal','carbon','sulfur'} do o[#o+1]=string.format('%-24s made %.1f used %.1f a minute (10 min), %.1f / %.1f (1 min), in hub %d',n,f.get_flow_count{name=n,category='input',precision_index=defines.flow_precision_index.ten_minutes},"
          "f.get_flow_count{name=n,category='output',precision_index=defines.flow_precision_index.ten_minutes},f.get_flow_count{name=n,category='input',precision_index=defines.flow_precision_index.one_minute},f.get_flow_count{name=n,category='output',precision_index=defines.flow_precision_index.one_minute},inv.get_item_count(n)) end "
          "o[#o+1]='hub free slots '..inv.count_empty_stacks()..' of '..#inv..', provides to other platforms '..tostring(hub.providing_to_other_platforms) rcon.print(table.concat(o,'\\n'))")


def main():
    step = sys.argv[1]
    apply = "--apply" in sys.argv
    if "--only" not in sys.argv:
        sys.argv += ["--only", "vulcanus"]
    print(layout())
    occ_l = "{" + ",".join("{%d,%d}" % c for c in sorted(occ)) + "}"
    til_l = "{" + ",".join("{%d,%d}" % c for c in sorted(tiles)) + "}"
    for name, planet, surface, turrets in wheels():
        print("==", name, surface or "(not created)")
        if not surface:
            continue
        sub = lambda code: code.replace("SURF", surface)
        if step == "check":
            print(tools["run_lua"](sub(CHECK).replace("TILES", til_l).replace("OCC", occ_l)))
        if step == "build":
            if apply:
                print(tools["run_lua"](sub(TURN)).strip())
                print(tools["run_lua"](sub(LAMPS).replace("OCC", occ_l)).strip())
                print(tools["run_lua"](sub(DECK).replace("TILES", til_l)).strip())
            ok, bad = place_all(ents, surface, apply)
            print("placed" if apply else "dry run", ok, "failed", bad)
        if step == "config" or (step == "build" and apply):
            factor = 1
            code = (sub(CONFIG).replace("FILT", lua_list([(x, y, fl) for x, y, fl in cfg])).replace("REC", lua_list(recipes)).replace("FEED", lua_list(feed))
                    .replace("TA", lua_map(TARGETS_A)).replace("TB", lua_map(TARGETS_B)).replace("RESERVE", str(RESERVE * factor)).replace("CAPSIG", str(CAP * factor)).replace("PRODUCT", PRODUCT))
            print(tools["run_lua"](code).strip())
        if step == "off":
            print(tools["run_lua"](sub(OFF)).strip())
        if step == "status":
            print(tools["run_lua"](sub(STATUS).replace("REC", lua_list(recipes)).replace("FEED", lua_list(feed)).replace("PRODUCT", PRODUCT)).strip())


if __name__ == "__main__":
    main()
