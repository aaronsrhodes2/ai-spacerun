#!/usr/bin/env python3
"""Nauvis Triangle 1 strip miner with the SHUFFLE (the Captain, 2026-11-14). Platform `[shuffle] Nauvis Triangle 1` (platform-14).

WHAT THE RECIPES REALLY DO (read from the prototypes in the game, 2026-11-14; the brief had it wrong): crushing gives 20 ore / 10 carbon /
5 ice and hands the chunk back only 30% of the time; reprocessing gives back ONE chunk at random: 40% the same kind, 20% each other kind,
20% nothing. So a chunk is consumed (a crush eats 0.7, a reprocess 0.2) and the catch from the strip is what the products are made of.
One chunk becomes about 28.6 ore, 14.3 carbon or 7.1 ice (x productivity); a reprocessed chunk turns into the wanted kind half the time.

GEOMETRY (tiles): hub at 0,0 (tiles -4..3); station ring belt = rectangle x -9..8, y -9..8, clockwise, 68 belts; machines in a band between hub and
ring on three faces: west Cm (metallic crusher) + Rm (metallic reprocessor), north Cc + Rc, east Co + Ro (crusher 2x3, rotated on the north face).
Hub side of a crusher: three bulk inserters (filtered to the product, capped by the hub stock) straight into the hub. Ring side: an intake
inserter (filtered to the machine's chunk kind, enabled by the MODE) and a return inserter (filtered to chunk kinds) back on the ring.
South band: the circuit (15 combinators) and two substations; the spoke belt (x=0, y 288..9) joins the ring at (0,8) through one belt tile (0,9)
that STOPS by circuit while the ring holds LRING chunks or more (the ring never gets more chunks than it admits: every machine returns at most one).
Strip: base side first (y=288 belt flowing to x=0, fast inserters on y=289, collectors y 290..292 facing south, deck only under their back
two rows). Substations every 16 tiles on the strip and the spoke. Solar field south of the station (epic panels, no night in orbit).

THE SHUFFLE / MODE: mode I (iron ore), C (carbon), W (ice) is a signal 1/0 on the MODE wire. Per chunk kind there are two machines: the
crusher runs when its mode is on, the reprocessor when it is off, so every chunk is crushed if it is the wanted kind and reprocessed
(toward any kind, 40/20/20) if not. A mode flip needs no purge: the chunks on the ring simply change road.
  AUTOMATIC  stock of the three products in the hub (a renamer each); the lowest stock wins (selector, min). Full kinds (stock >= target)
             are lifted by 1000 so they are skipped; the running mode is lowered by HYST so it does not thrash. Other platforms draw on the
             hub (providing_to_other_platforms), so the one they drain is the one the strip turns to. It does NOT read the other hubs' requests.
  MANUAL     constant combinator OVERRIDE, signal M: 0 = automatic, 1 = iron, 2 = carbon, 3 = ice (`mode iron|carbon|ice|auto`).
Steps (never apply a step twice; each refuses when its first entity already stands):
  check | station [--apply] | config | stage1 [--apply] | stage2 [--apply] | mode [iron|carbon|ice|auto] | status | panels [--apply]
Usage: triangle_miner.py check|station|config|stage1|stage2|panels|mode|status [--apply]"""
import json
import math
import sys

from _game import tools

NAME = "Nauvis Triangle 1"
Q = {"quality": "epic"}
DIRS = {(0, -1): 0, (1, 0): 4, (0, 1): 8, (-1, 0): 12}
T_STOCK = 500                 # hub stock target per product (10 slots each; the hub has 59 slots, foundations take 6)
HYST = 100                    # the running mode counts as this much emptier than it is
LRING = 100                   # the ring admits chunks while it holds fewer than this (ring lane holds 4 a tile: 68 tiles, 272)
HUBX = 1                      # hub item signals read this many times the real count (measured in `config`)
CHUNK = {"m": "metallic-asteroid-chunk", "c": "carbonic-asteroid-chunk", "o": "oxide-asteroid-chunk"}
SIG = {"m": "signal-I", "c": "signal-C", "o": "signal-W"}
PRODUCT = {"m": "iron-ore", "c": "carbon", "o": "ice"}
# machine key: (kind, crush?, centre x, centre y, direction, face)
MACH = {"Rm": ("m", False, -6.0, 1.5, 0, "W"), "Cm": ("m", True, -6.0, -2.5, 0, "W"),
        "Cc": ("c", True, -2.5, -6.0, 4, "N"), "Rc": ("c", False, 1.5, -6.0, 4, "N"),
        "Co": ("o", True, 6.0, -2.5, 0, "E"), "Ro": ("o", False, 6.0, 1.5, 0, "E")}      # order = the MODE wire's hop order
COLLECT = 30                  # a collector every COLLECT tiles of strip
SUB = 16                      # a substation every SUB tiles of strip / spoke
BASE_Y = 288                  # base belt row; inserters y+1, collectors y+2..y+4 facing south
AT = "local p for _,q in pairs(game.forces.player.platforms) do if q.name:find('%s',1,true) then p=q end end local s=p.surface " % NAME
HEAD = (AT + "local W=defines.wire_connector_id local function at(n,x,y) return s.find_entities_filtered{name=n,position={x,y},radius=0.3}[1] end "
        "local function sg(n) if prototypes.item[n] then return {type='item',name=n} end return {type='virtual',name=n} end ")


def surface():
    return tools["run_lua"](AT + "rcon.print(s.name)").strip()


def lua(code):
    return tools["run_lua"](code)


def place(ents, apply, surf=None):
    surf = surf or surface()
    ok = bad = 0
    for i in range(0, len(ents), 400):
        r = json.loads(tools["place_entities"](json.dumps(ents[i:i + 400]), surface=surf, dry_run=not apply))
        ok += r.get("placed", 0)
        f = r.get("failed") or []
        bad += len(f)
        if f:
            print("failed", json.dumps(f)[:600])
    return ok, bad


def deck(tiles):
    """Foundation under `tiles` (only where there is none yet; never touches the hub's own tiles)."""
    ts = sorted(tiles)
    n = 0
    for i in range(0, len(ts), 3000):
        part = ",".join("{%d,%d}" % t for t in ts[i:i + 3000])
        n += int(lua(AT + "local add={} for _,q in pairs({%s}) do if s.get_tile(q[1],q[2]).name~='space-platform-foundation' then add[#add+1]={name='space-platform-foundation',position=q} end end s.set_tiles(add) rcon.print(#add)" % part))
    return n


def E(name, cx, cy, d=0, **params):
    p = dict(Q)
    p.update(params)
    return {"name": name, "x": cx, "y": cy, "direction": d, "params": p}


def T(name, tx, ty, d=0, w=1, h=1, **params):
    return E(name, tx + w / 2, ty + h / 2, d, **params)


# ------------------------------------------------------------------ the station
def ring_path():
    return ([(x, -9) for x in range(-9, 9)] + [(8, y) for y in range(-8, 9)] + [(x, 8) for x in range(7, -10, -1)] + [(-9, y) for y in range(7, -9, -1)])


COMB = {"AR": (-5, 5), "A_I": (-3, 5), "A_C": (-1, 5), "A_W": (1, 5), "D_I": (-5, 6), "D_C": (-3, 6), "D_W": (-1, 6), "AM": (1, 6),
        "SEL": (3, 6), "D1": (-5, 7), "D2": (-3, 7), "D3": (-1, 7)}
COMB_NAME = {"AR": "arithmetic-combinator", "A_I": "arithmetic-combinator", "A_C": "arithmetic-combinator", "A_W": "arithmetic-combinator",
             "D_I": "decider-combinator", "D_C": "decider-combinator", "D_W": "decider-combinator", "AM": "arithmetic-combinator",
             "SEL": "selector-combinator", "D1": "decider-combinator", "D2": "decider-combinator", "D3": "decider-combinator"}
CONST = {"OFFSET": (1, 7), "OVERRIDE": (3, 7)}
SUBS = [(-8, -8), (6, -8), (-8, 5), (6, 5)]          # 2x2 substations, top-left tiles


def station_ents():
    ents, tiles = [], set()
    for x in range(-9, 9):
        for y in range(-9, 9):
            tiles.add((x, y))
    path = ring_path()
    n = len(path)
    for i, t in enumerate(path):
        nx = path[(i + 1) % n]
        ents.append(T("express-transport-belt", t[0], t[1], DIRS[(nx[0] - t[0], nx[1] - t[1])]))
    for k, (kind, crush, cx, cy, d, face) in MACH.items():
        ents.append(E("crusher", cx, cy, d))
    # hub side product inserters (three each) and ring side intake / return inserters
    for k, (kind, crush, cx, cy, d, face) in MACH.items():
        if face == "W":
            hub = [E("bulk-inserter", -4.5, cy + o, 12) for o in (-1, 0, 1)] if crush else []
            ins, ret = E("fast-inserter", -7.5, cy - 1 if crush else cy - 1, 12), E("fast-inserter", -7.5, cy if crush else cy, 4)
        elif face == "E":
            hub = [E("bulk-inserter", 4.5, cy + o, 4) for o in (-1, 0, 1)] if crush else []
            ins, ret = E("fast-inserter", 7.5, cy - 1, 4), E("fast-inserter", 7.5, cy, 12)
        else:
            hub = [E("bulk-inserter", cx + o, -4.5, 0) for o in (-1, 0, 1)] if crush else []
            ins, ret = E("fast-inserter", cx - 1, -7.5, 0), E("fast-inserter", cx, -7.5, 8)
        ents += hub + [ins, ret]
    for name, (tx, ty) in COMB.items():
        ents.append(T(COMB_NAME[name], tx, ty, 4, 2, 1))
    for name, (tx, ty) in CONST.items():
        ents.append(T("constant-combinator", tx, ty, 0))
    for (tx, ty) in SUBS:
        ents.append(T("substation", tx, ty, 0, 2, 2))
    return ents, tiles


def lua_mach_table():
    out = []
    for k, (kind, crush, cx, cy, d, face) in MACH.items():
        rec = ("%s-asteroid-%s" % ({"m": "metallic", "c": "carbonic", "o": "oxide"}[kind], "crushing" if crush else "reprocessing"))
        if face == "W":
            ix, iy, rx, ry = -7.5, cy - 1, -7.5, cy
            hub = ",".join("{%s,%s}" % (-4.5, cy + o) for o in (-1, 0, 1))
        elif face == "E":
            ix, iy, rx, ry = 7.5, cy - 1, 7.5, cy
            hub = ",".join("{%s,%s}" % (4.5, cy + o) for o in (-1, 0, 1))
        else:
            ix, iy, rx, ry = cx - 1, -7.5, cx, -7.5
            hub = ",".join("{%s,%s}" % (cx + o, -4.5) for o in (-1, 0, 1))
        out.append("{key='%s',kind='%s',crush=%s,x=%s,y=%s,rec='%s',ix=%s,iy=%s,rx=%s,ry=%s,hub={%s},chunk='%s',prod='%s',sig='%s'}"
                   % (k, kind, str(crush).lower(), cx, cy, rec, ix, iy, rx, ry, hub if crush else "", CHUNK[kind], PRODUCT[kind], SIG[kind]))
    return "{" + ",".join(out) + "}"


def lua_comb_table():
    return "{" + ",".join("%s={x=%s,y=%s,name='%s'}" % (k, v[0] + 1.0, v[1] + 0.5, COMB_NAME[k]) for k, v in COMB.items()) + "}"


CONFIG = (
    HEAD + "local hub=p.hub local bad,made={}, {} local function note(m) bad[#bad+1]=m end "
    "local function con(e,id) return e.get_wire_connector(id,true) end "
    "local function wire(a,ia,b,ib,what) if not a or not b then note('missing '..what) return end local ca,cbn=con(a,ia),con(b,ib) local already=false pcall(function() already=ca.is_connected_to(cbn) end) local ok=already or ca.connect_to(cbn) if not ok then note('wire failed '..what) end end "
    "local function cond(sig,cmp,k,nets) local c={first_signal=sg(sig),comparator=cmp,constant=k} if nets then c.first_signal_networks=nets end return c end "
    "local MA=MACHTABLE local CB=COMBTABLE local TS=TSTOCK local HX=HUBX local HY=HYSTV local LR=LRINGV "
    # --- hub provides to the platforms in orbit
    "hub.providing_to_other_platforms=true pcall(function() hub.get_or_create_control_behavior().read_contents=true end) "
    # --- machines: recipes, filters, conditions, wires
    "local intakes={} local prodins={} local rets={} "
    "for _,m in pairs(MA) do local c=at('crusher',m.x,m.y) if not c then note('no machine '..m.key) else c.set_recipe(m.rec) "
    "local ii=at('fast-inserter',m.ix+0.0,m.iy+0.0) local ri=at('fast-inserter',m.rx+0.0,m.ry+0.0) "
    "if ii then ii.use_filters=true ii.inserter_filter_mode='whitelist' ii.set_filter(1,{name=m.chunk,quality='normal',comparator='='}) local cb=ii.get_or_create_control_behavior() cb.circuit_enable_disable=true "
    "cb.circuit_condition=m.crush and cond(m.sig,'>',0) or cond(m.sig,'<',1) intakes[#intakes+1]=ii else note('no intake '..m.key) end "
    "if ri then ri.use_filters=true ri.inserter_filter_mode='whitelist' if m.crush then ri.set_filter(1,{name=m.chunk,quality='normal',comparator='='}) else local k=0 for _,ch in pairs({'metallic-asteroid-chunk','carbonic-asteroid-chunk','oxide-asteroid-chunk'}) do k=k+1 ri.set_filter(k,{name=ch,quality='normal',comparator='='}) end end rets[#rets+1]=ri else note('no return '..m.key) end "
    "for _,h in pairs(m.hub) do local hi=at('bulk-inserter',h[1],h[2]) if hi then hi.use_filters=true hi.inserter_filter_mode='whitelist' hi.set_filter(1,{name=m.prod,quality='normal',comparator='='}) local cb=hi.get_or_create_control_behavior() cb.circuit_enable_disable=true "
    "cb.circuit_condition=cond(m.prod,'<',TS*HX) wire(hub,W.circuit_green,hi,W.circuit_green,'hub->'..m.key) prodins[#prodins+1]=hi else note('no hub inserter '..m.key) end end end end "
    # --- ring belts: read (hold) on a green chain
    "local ring={} local nb=0 local prev=nil for _,b in pairs(s.find_entities_filtered{type='transport-belt',area={{-9.5,-9.5},{9.5,8.99}}}) do if b.name=='express-transport-belt' then "
    "local x,y=b.position.x,b.position.y if y<9 and (x<-8.4 or x>7.4 or y<-8.4 or y>7.4) then ring[#ring+1]=b end end end "
    # order the ring belts along the path so the chain is short hops
    "table.sort(ring,function(a,b) return math.atan2(a.position.y+0.5,a.position.x+0.5)<math.atan2(b.position.y+0.5,b.position.x+0.5) end) "
    "for _,b in pairs(ring) do local bc=b.get_or_create_control_behavior() bc.read_contents=true bc.read_contents_mode=defines.control_behavior.transport_belt.content_read_mode.hold "
    "if prev then wire(prev,W.circuit_green,b,W.circuit_green,'ring chain') end prev=b nb=nb+1 end "
    # --- combinators
    "local C={} for k,v in pairs(CB) do C[k]=at(v.name,v.x,v.y) if not C[k] then note('no combinator '..k) end end "
    "local OFF=at('constant-combinator',1.5,7.5) local OVR=at('constant-combinator',3.5,7.5) if not OFF or not OVR then note('no constants') end "
    "local function arith(e,a,op,b,out) e.get_or_create_control_behavior().parameters={first_signal=a,second_constant=b,operation=op,output_signal=sg(out)} end "
    "if C.AR then C.AR.get_or_create_control_behavior().parameters={first_signal={type='virtual',name='signal-each'},second_constant=1,operation='*',output_signal=sg('signal-T')} end "
    "arith(C.A_I,sg('iron-ore'),HX==1 and '+' or '/',HX==1 and 0 or HX,'signal-I') arith(C.A_C,sg('carbon'),HX==1 and '+' or '/',HX==1 and 0 or HX,'signal-C') arith(C.A_W,sg('ice'),HX==1 and '+' or '/',HX==1 and 0 or HX,'signal-W') "
    "local function full(e,sig) e.get_or_create_control_behavior().parameters={conditions={{first_signal=sg(sig),comparator='>',constant=TS-1}},outputs={{signal=sg(sig),copy_count_from_input=false,constant=1000}}} end "
    "full(C.D_I,'signal-I') full(C.D_C,'signal-C') full(C.D_W,'signal-W') "
    "C.AM.get_or_create_control_behavior().parameters={first_signal={type='virtual',name='signal-each'},second_constant=-HY,operation='*',output_signal={type='virtual',name='signal-each'}} "
    "local okp,errp=pcall(function() local sb=C.SEL.get_or_create_control_behavior() sb.parameters={operation='select',select_max=false,index_constant=0} end) if not okp then note('selector '..tostring(errp)) end "
    "local function mode(e,sig,m) e.get_or_create_control_behavior().parameters={conditions={{first_signal=sg('signal-M'),comparator='=',constant=m},{first_signal=sg('signal-M'),comparator='=',constant=0,compare_type='or'},{first_signal=sg(sig),comparator='>',constant=0,compare_type='and'}},"
    "outputs={{signal=sg(sig),copy_count_from_input=false,constant=1}}} end "
    "mode(C.D1,'signal-I',1) mode(C.D2,'signal-C',2) mode(C.D3,'signal-W',3) "
    "local ob=OFF.get_or_create_control_behavior() while ob.sections_count>0 do ob.remove_section(1) end local sec=ob.add_section() sec.set_slot(1,{value={type='virtual',name='signal-I',quality='normal'},min=10000}) sec.set_slot(2,{value={type='virtual',name='signal-C',quality='normal'},min=10000}) sec.set_slot(3,{value={type='virtual',name='signal-W',quality='normal'},min=10000}) "
    # --- wires
    "wire(C.AR,W.combinator_input_green,ring[1],W.circuit_green,'AR in') "
    "local feed=at('express-transport-belt',0.5,9.5) if feed then local fb=feed.get_or_create_control_behavior() fb.circuit_enable_disable=true fb.circuit_condition=cond('signal-T','<',LR) wire(C.AR,W.combinator_output_red,feed,W.circuit_red,'AR out->feed') else note('no feed belt (stage1 not built yet)') end "
    "for _,k in pairs({'A_I','A_C','A_W'}) do wire(hub,W.circuit_green,C[k],W.combinator_input_green,'hub->'..k) end "
    "for _,k in pairs({'A_C','A_W'}) do wire(C.A_I,W.combinator_output_red,C[k],W.combinator_output_red,'N1 '..k) wire(C.A_I,W.combinator_output_green,C[k],W.combinator_output_green,'N2 '..k) end "
    "for _,k in pairs({'D_I','D_C','D_W'}) do wire(C.A_I,W.combinator_output_red,C[k],W.combinator_input_red,'N1->'..k) wire(C.A_I,W.combinator_output_green,C[k],W.combinator_output_green,'N2<-'..k) end "
    "wire(C.A_I,W.combinator_output_green,C.AM,W.combinator_output_green,'N2 AM') wire(C.A_I,W.combinator_output_green,OFF,W.circuit_green,'N2 offset') wire(C.A_I,W.combinator_output_green,C.SEL,W.combinator_input_green,'N2 sel') "
    "wire(C.SEL,W.combinator_output_red,OVR,W.circuit_red,'SEL ovr') for _,k in pairs({'D1','D2','D3'}) do wire(C.SEL,W.combinator_output_red,C[k],W.combinator_input_red,'SEL->'..k) if k~='D1' then wire(C.D1,W.combinator_output_red,C[k],W.combinator_output_red,'MODE '..k) end end "
    "wire(C.D1,W.combinator_output_red,C.AM,W.combinator_input_red,'MODE AM') local last=C.D1 for _,i in pairs(intakes) do wire(last,last.type=='inserter' and W.circuit_red or W.combinator_output_red,i,W.circuit_red,'MODE intake') last=i end "
    "for _,e in pairs(s.find_entities_filtered{type='electric-pole'}) do end "
    "rcon.print('machines '..#MA..' intakes '..#intakes..' product inserters '..#prodins..' ring belts '..nb..' notes '..#bad..' : '..table.concat(bad,' ; '))")


STATUS = (HEAD + "local hub=p.hub local inv=hub.get_inventory(defines.inventory.hub_main) local P=defines.flow_precision_index local out={} "
          "local function stn(v) for n,x in pairs(defines.entity_status) do if x==v then return n end end return '?' end "
          "local function sigs(name,x,y,id) local e=at(name,x,y) if not e then return '?' end local ok,v=pcall(function() return e.get_signals(id) end) local o={} if ok and v then for _,q in pairs(v) do o[#o+1]=q.signal.name:gsub('signal%-','')..'='..q.count end end return table.concat(o,',') end "
          "local o={} for _,n in pairs({'iron-ore','carbon','ice','space-platform-foundation','metallic-asteroid-chunk','carbonic-asteroid-chunk','oxide-asteroid-chunk'}) do o[#o+1]=n..' '..inv.get_item_count(n) end "
          "local tr=hub.get_inventory(defines.inventory.hub_trash) out[#out+1]='tick '..game.tick..' | HUB (free slots '..inv.count_empty_stacks()..', trash items '..(tr and #tr-tr.count_empty_stacks() or 0)..', provides '..tostring(hub.providing_to_other_platforms)..'): '..table.concat(o,', ') "
          "out[#out+1]='MODE wire '..sigs('decider-combinator',-4,7.5,W.combinator_output_red)..' | SELECTOR '..sigs('selector-combinator',4,6.5,W.combinator_output_red)..' | OVERRIDE M='..(function() local o=at('constant-combinator',3.5,7.5) local sec=o and o.get_or_create_control_behavior().get_section(1) local v=0 if sec then for _,f in pairs(sec.filters) do v=f.min or 0 end end return v end)()..' (0 = automatic)'..' | RING total T='..sigs('arithmetic-combinator',-4,5.5,W.combinator_output_red) "
          "local feed=at('express-transport-belt',0.5,9.5) out[#out+1]='feed belt (0,9) '..(feed and (feed.to_be_deconstructed() and 'x' or '')..'ok' or 'missing') "
          "local st={} for _,e in pairs(s.find_entities_filtered{type={'assembling-machine','furnace'}}) do local rc=e.get_recipe() local k=(rc and rc.name or e.name)..' '..stn(e.status) st[k]=(st[k] or 0)+1 end local o2={} for k,v in pairs(st) do o2[#o2+1]=k..' x'..v end table.sort(o2) out[#out+1]='MACHINES '..table.concat(o2,' ; ') "
          "local cs={} local ct={} for _,c in pairs(s.find_entities_filtered{type='asteroid-collector'}) do local k=stn(c.status) cs[k]=(cs[k] or 0)+1 for _,it in pairs(c.get_output_inventory().get_contents()) do ct[it.name:sub(1,3)]=(ct[it.name:sub(1,3)] or 0)+it.count end end local o3={} for k,v in pairs(cs) do o3[#o3+1]=k..' x'..v end "
          "out[#out+1]='COLLECTORS '..table.concat(o3,' ')..' | held met '..(ct.met or 0)..' car '..(ct.car or 0)..' oxi '..(ct.oxi or 0) "
          "local bt={} for _,e in pairs(s.find_entities_filtered{type='transport-belt'}) do for l=1,2 do for _,it in pairs(e.get_transport_line(l).get_contents()) do bt[it.name:sub(1,3)]=(bt[it.name:sub(1,3)] or 0)+it.count end end end out[#out+1]='ON BELTS met '..(bt.met or 0)..' car '..(bt.car or 0)..' oxi '..(bt.oxi or 0) "
          "local f=game.forces.player.get_item_production_statistics(s) local function fl(n,c,pp) return string.format('%.1f',f.get_flow_count{name=n,category=c,precision_index=pp}) end local o4={} "
          "for _,n in pairs({'iron-ore','carbon','ice','metallic-asteroid-chunk','carbonic-asteroid-chunk','oxide-asteroid-chunk'}) do o4[#o4+1]=n..' +'..fl(n,'input',P.one_minute)..'/min (10 min +'..fl(n,'input',P.ten_minutes)..', out '..fl(n,'output',P.ten_minutes)..')' end out[#out+1]='FLOWS '..table.concat(o4,' ; ') "
          "rcon.print(table.concat(out,'|'))")


POWER = (HEAD + "local sub=at('substation',-7,6) local es=sub.electric_network_statistics local o={} for n,c in pairs(es.output_counts) do o[#o+1]=n..'='..c end for n,c in pairs(es.input_counts) do o[#o+1]='IN:'..n..'='..c end rcon.print(game.tick..'|'..table.concat(o,';'))")


def power(wait=6.0):
    """Mean power per entity type over `wait` seconds (two samples of the network statistics): produced / consumed, MW."""
    import time

    def sample():
        t, body = lua(POWER).split("|", 1)
        d = {}
        for kv in body.split(";"):
            if "=" in kv:
                k, v = kv.rsplit("=", 1)
                d[k] = float(v)
        return int(t), d
    t0, a = sample()
    time.sleep(wait)
    t1, b = sample()
    dt = (t1 - t0) / 60.0
    prod = {k[3:]: (b[k] - a.get(k, 0)) / dt / 1e6 for k in b if k.startswith("IN:")}
    cons = {k: (b[k] - a.get(k, 0)) / dt / 1e6 for k in b if not k.startswith("IN:")}
    return "POWER over %.1f game s: made %s  |  used %s  (MW)" % (dt, {k: round(v, 2) for k, v in cons.items() if v > 0.005}, {k: round(v, 2) for k, v in prod.items() if v > 0.005})


def config_lua():
    return (CONFIG.replace("MACHTABLE", lua_mach_table()).replace("COMBTABLE", lua_comb_table()).replace("TSTOCK", str(T_STOCK)).replace("HUBX", str(HUBX))
            .replace("HYSTV", str(HYST * HUBX)).replace("LRINGV", str(LRING)))


# ------------------------------------------------------------------ solar field
def panel_ents(bands=(12, 17, 20, 23)):
    ents, tiles = [], set()
    for y0 in bands:
        for x0 in list(range(-30, -3, 3)) + list(range(3, 30, 3)):
            ents.append(T("solar-panel", x0, y0, 0, 3, 3))
            tiles |= {(x0 + i, y0 + j) for i in range(3) for j in range(3)}
    for (cx, cy) in [(-22, 15), (-10, 15), (8, 15), (20, 15)]:
        ents.append(T("substation", cx, cy, 0, 2, 2))
        tiles |= {(cx + i, cy + j) for i in range(2) for j in range(2)}
    for x in list(range(-30, -3)) + list(range(3, 30)):
        for y in (15, 16):
            tiles.add((x, y))
    return ents, tiles


# ------------------------------------------------------------------ the strip, base side
def base_ents(x0, x1, with_spoke):
    """Base side belt y=288 for x in [x0,x1) (flowing to x=0), collectors on the south, substations; the spoke belt up to the station."""
    ents, tiles = [], set()
    for x in range(x0, x1):
        if x == 0:
            ents.append(T("express-transport-belt", 0, BASE_Y, 0))
        else:
            ents.append(T("express-transport-belt", x, BASE_Y, 4 if x < 0 else 12))
    xs = [s * (COLLECT // 2 + COLLECT * k) for s in (-1, 1) for k in range(0, 1000) if x0 <= s * (COLLECT // 2 + COLLECT * k) < x1]
    for x in xs:
        ents.append(T("asteroid-collector", x - 1, BASE_Y + 2, 8, 3, 3))
        ents.append(T("fast-inserter", x, BASE_Y + 1, 8))
        tiles |= {(x + i, BASE_Y + 2 + j) for i in (-1, 0, 1) for j in (0, 1)}
    for x in range(x0 - x0 % SUB, x1, SUB):
        if x0 <= x < x1 - 1 and abs(x) > 3:
            ents.append(T("substation", x, BASE_Y - 2, 0, 2, 2))
    if with_spoke:
        for y in range(BASE_Y - 1, 8, -1):
            ents.append(T("express-transport-belt", 0, y, 0))
        for y in list(range(28, BASE_Y - 4, SUB)) + [BASE_Y - 4]:         # the last one links the spoke to the first base substations
            ents.append(T("substation", -2, y, 0, 2, 2))
    return ents, tiles, len(xs)


# ------------------------------------------------------------------ the strip, slanted sides (the same predicate triangle.py laid the deck with)
APEX, H, TW = -577, 866, 4
Y_TOP = -555            # the diagonal belt starts here (the apex wedge above is solid deck and carries nothing)
DSUB = 14               # slanted substations: 14 rows down is about 16 tiles of edge, inside the 18-tile reach (16 rows was 18.4: islands)
DROWS = 26              # a collector every DROWS rows = about COLLECT tiles of slanted strip


def row_span(y):
    """(leftmost, rightmost) strip tile in row y of the slanted sides, from the ghost predicate of triangle.py."""
    import math
    r = y - APEX
    w = r / math.sqrt(3)
    xs = [x for x in range(math.ceil(-w), math.floor(w) + 1) if min((w - abs(x)) * 0.866, H - r) < TW]
    return min(xs), max(xs)


def strip_row(y):
    import math
    r = y - APEX
    w = r / math.sqrt(3)
    return {x for x in range(math.ceil(-w), math.floor(w) + 1) if min((w - abs(x)) * 0.866, H - r) < TW}


def sub_tile(y, side, taken):
    """Top-left tile of a 2x2 substation on the slanted strip in rows y, y+1: all four tiles deck and not in `taken` (belts, inserters, bodies); None if none."""
    r0, r1 = strip_row(y), strip_row(y + 1)
    lo = min(r0) if side < 0 else max(r0)
    for k in range(2, 6):
        c = lo + k if side < 0 else lo - k - 1
        cells = [(c + i, y + j) for i in (0, 1) for j in (0, 1)]
        if all((x in (r0 if j == 0 else r1)) and (x, yy) not in taken for (x, yy), j in zip(cells, (0, 0, 1, 1))):
            return c
    return None


def ins_row(y0, side):
    """First row from y0 (then y0+1, y0-1) where the staircase belt takes no horizontal step, so the edge tile is free for the inserter."""
    for y in (y0, y0 + 1, y0 + 2, y0 - 1):
        a, b = row_span(y), row_span(y + 1)
        if a[0 if side < 0 else 1] == b[0 if side < 0 else 1]:
            return y
    raise ValueError(y0)


def diag_ents(side):
    """Left (side=-1) or right (+1) slanted side from Y_TOP down to the base belt: a staircase belt one tile inside the outer edge, an inserter
    on the outer edge tile and a collector outside facing outward (west / east) every DROWS rows. Flows down to the base belt (y=288)."""
    ents, tiles = [], set()
    ys = list(range(Y_TOP, 288))
    xb = {}
    for y in ys + [288]:
        lo, hi = row_span(y)
        xb[y] = lo + 1 if side < 0 else hi - 1
    path = []
    for y in ys:
        step = 1 if xb[y + 1] > xb[y] else -1
        x = xb[y]
        while True:
            path.append((x, y))
            if x == xb[y + 1]:
                break
            x += step
    path.append((xb[288], 288))
    path = path[:-1]
    for i, t in enumerate(path):
        nx = path[i + 1] if i + 1 < len(path) else (xb[288], 288)
        ents.append(T("express-transport-belt", t[0], t[1], DIRS[(nx[0] - t[0], nx[1] - t[1])]))
    ncol = 0
    for y0 in range(Y_TOP + DROWS // 2, 270, DROWS):
        y0 = ins_row(y0, side)
        lo, hi = row_span(y0)
        if side < 0:
            ix, bx, d = lo, lo - 3, 12
            deck_cols = (bx + 1, bx + 2)
        else:
            ix, bx, d = hi, hi + 1, 4
            deck_cols = (bx, bx + 1)
        ents.append(T("fast-inserter", ix, y0, d))
        ents.append(T("asteroid-collector", bx, y0 - 1, d, 3, 3))
        tiles |= {(c, y0 - 1 + j) for c in deck_cols for j in range(3)}
        ncol += 1
    taken = set()
    for e in ents:
        if e["name"] == "asteroid-collector":
            taken |= {(int(e["x"] - 1.5) + i, int(e["y"] - 1.5) + j) for i in range(3) for j in range(3)}
        else:
            taken.add((math.floor(e["x"]), math.floor(e["y"])))
    for y in range(Y_TOP + 4, 280, DSUB):
        c = sub_tile(y, side, taken)
        if c is None:
            c = sub_tile(y + 1, side, taken)
            y += 1
        if c is None:
            print("no substation spot at row", y)
            continue
        ents.append(T("substation", c, y, 0, 2, 2))
        taken |= {(c + i, y + j) for i in (0, 1) for j in (0, 1)}
    return ents, tiles, ncol


def first_standing(ents):
    e = ents[0]
    return lua(AT + "rcon.print(s.count_entities_filtered{name='%s',position={%s,%s},radius=0.3})" % (e["name"], e["x"], e["y"])).strip() != "0"


def main():
    step = sys.argv[1] if len(sys.argv) > 1 else "status"
    apply = "--apply" in sys.argv
    surf = surface()
    if step == "check":
        for nm, (ents, tiles) in {"station": station_ents(), "panels": panel_ents()}.items():
            print(nm, len(ents), "entities", len(tiles), "deck tiles", place(ents, False, surf))
        e, t, n = base_ents(-150, 151, True)
        print("stage1", len(e), "entities", n, "collectors", len(t), "deck tiles")
    elif step == "station":
        ents, tiles = station_ents()
        if apply and first_standing(ents):
            sys.exit("station already built")
        if apply:
            tools["save_game"]("skippy")
            print("deck", deck(tiles))
        print("station", place(ents, apply, surf))
        if apply:
            print(lua(config_lua()))
    elif step == "config":
        print(lua(config_lua()))
    elif step == "panels":
        ents, tiles = panel_ents()
        if apply and first_standing(ents):
            sys.exit("panels already built")
        if apply:
            print("deck", deck(tiles))
        print("panels", place(ents, apply, surf))
    elif step in ("stage1", "stage2"):
        x0, x1, spoke = (-150, 151, True) if step == "stage1" else (-500, 501, False)
        ents, tiles, n = base_ents(x0, x1, spoke)
        if step == "stage2":
            ents = [e for e in ents if not (-150 <= e["x"] < 151)]
        if apply and first_standing(ents):
            sys.exit(step + " already built")
        if apply:
            tools["save_game"]("skippy")
            print("deck", deck(tiles))
        print(step, "collectors", n, place(ents, apply, surf))
    elif step in ("stage3", "stage4"):
        ents, tiles, n = diag_ents(-1 if step == "stage3" else 1)
        if apply and first_standing(ents):
            sys.exit(step + " already built")
        if apply:
            tools["save_game"]("skippy")
            print("deck", deck(tiles))
        print(step, "collectors", n, "belts", sum(1 for e in ents if e["name"] == "express-transport-belt"), place(ents, apply, surf))
    elif step == "mode":
        want = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else None
        if want:
            v = {"auto": 0, "iron": 1, "carbon": 2, "ice": 3}[want]
            print(lua(HEAD + "local o=at('constant-combinator',3.5,7.5) local ob=o.get_or_create_control_behavior() while ob.sections_count>0 do ob.remove_section(1) end "
                      "if %d>0 then local sec=ob.add_section() sec.set_slot(1,{value={type='virtual',name='signal-M',quality='normal'},min=%d}) end rcon.print('override M=%d')" % (v, v, v)))
        else:
            print(lua(STATUS).split("|")[1:3])
    elif step == "status":
        print(lua(STATUS).replace("|", chr(10)))
        print(power())


if __name__ == "__main__":
    main()
