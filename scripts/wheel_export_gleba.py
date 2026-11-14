#!/usr/bin/env python3
"""The export works of a wheel: rocket fuel from HUB STOCK (the Captain, 2026-11-14: Gleba Wheel = rocket fuel, "increase production
to the maximum that station can", and make it available to other platforms in its orbit).
Why not the rocket district (scripts/wheel_rocket.py): it lives off chunks tapped from the west spoke, and the Gleba Wheel's west spoke
carries next to no carbonic chunks, so its coal plant starved (0.5 rocket fuel a minute) while the hub held 32,000 carbon. This cell
stands on the free deck south of the blue block and takes carbon, sulfur and calcite out of the hub through belt K's feed column.
  site     wheel x 57..87, y -13..-3: a closed, counted loop belt (clockwise) with the chemistry inside, as in the rocket district:
           ice melter -> water riser and pipe row; acid plant -> refinery (simple coal liquefaction) -> heavy cracking -> light oil ->
           solid fuel plant and two rocket fuel assemblers; two coal plants (carbon + sulfur + water). Every producer's inserter
           works only while the loop holds fewer than TARGETS of its item.
  taps     long-handed inserters at x 55 reach over belt O (x 54) into K's feed column (x 53): two for carbon, one sulfur, one
           calcite. K's hub inserter loads "target minus what lies on K", so what is taken here is replaced from the hub.
           BLUE SCIENCE HAS FIRST CALL. Measured on the Gleba Wheel: K's feed (92 tiles, hub to blue block) is a standing queue,
           full of carbon; blue's coal plants eat every carbon that reaches K's loop, and the loop holds blue's sulfur and
           calcite. K's hub inserter loads an item only while K as a whole holds less than its target, and the taps stand
           upstream of blue (unchecked they strip the queue of sulfur and calcite: blue's loop fell from about 30 calcite to 8).
           ask    two deciders (56,-10 / -12) put sulfur +60 and calcite +30 on the red wire of K's hub inserter (4.5,-2.5)
                  while this loop holds fewer than DEMAND of the item, so the hub sends that much more than blue's targets.
                  Bounded: K never carries more than that above its own targets.
           take   three deciders (56,-4 / -6 / -8) block an item's taps (they add 1000 to its signal) while K's LOOP, blue's
                  own stock, is thin: carbon while the loop holds fewer than 30 coal (carbon itself never lies there: blue's
                  coal plants eat it at once, coal is what it becomes), sulfur under 80, calcite under 12. Carbon and sulfur
                  also while the hub holds fewer than RESERVE carbon. K's loop belts are read on their free red connectors
                  (K's own count is on green).
                  Tried first and dropped: gating on the feed stretch north of the taps (a mixed standing queue reads low on
                  carbon and the taps starve beside it) and on K's whole count (the feed is physically full below K's carbon
                  target, so the count never rises above it).
  ice      one inserter west of belt W (51,-9), two belt tiles and an underground under the three columns to the melter (58,-8)
  iron     acid needs a plate per craft: an inserter takes iron ore off the ore loop (99,-8), five belt tiles, a furnace (89..91),
           plates onto the loop's east column
  export   an inserter at (71,-14) lifts rocket fuel off the loop's top row onto the pack belt (y -15), which the hub takes in;
           it works while the hub holds fewer than CAP. `provide on` lets other platforms in the orbit request it
           (request filter request_from='platforms').
  modules  `modules --apply` MOVES factory-made productivity module 2 from the Nauvis network into the cell's empty slots (epic into
           the plants, legendary into the two assemblers if there are any, else epic) and prints what it moved.
Per rocket fuel (with the modules): about 24 carbon, 6 sulfur, 1.3 calcite, 4 ice. Two coal plants are the cell's limit (about 107
coal a minute, 16 to 17 rocket fuel); above that the wheel's carbon income is.
`build` places only what does not stand yet. After a quality upgrade run `config` (belt readers and over-reach wires).
Steps (--only PLANET, default gleba): check | build [--apply] | config | sweep | modules [--apply] | provide on|off | status
Usage: wheel_export_gleba.py status ; wheel_export_gleba.py build --apply ; wheel_export_gleba.py modules --apply"""
import sys

from _game import tools
from _wheels import place_all, wheels
import wheel_blue

Q = {"quality": "epic"}
N, E, S, W = 0, 4, 8, 12
DIR = {(0, -1): N, (1, 0): E, (0, 1): S, (-1, 0): W}
LX, LY = 57, -13                     # the loop's top left corner, wheel coordinates
LW, LH = 30, 10                      # loop spans local x 0..LW, y 0..LH
CAP, RESERVE = 4000, 10000           # rocket fuel in the hub; carbon the hub keeps for blue science
TARGETS = {"carbon": 150, "sulfur": 80, "calcite": 30, "iron-plate": 8, "coal": 60, "solid-fuel": 40, "rocket-fuel": 8}
DECS = [(56.5, -4.0, "carbon", "coal", 30, 1), (56.5, -6.0, "sulfur", "sulfur", 80, 1), (56.5, -8.0, "calcite", "calcite", 12, 0)]
# x, y, item whose taps it blocks, item read on K's loop, least count there, 1 = also the hub's carbon reserve
KFEED, KLOOP = [], []                # every tile of belt K (scripts/wheel_blue.py), filled by layout()
DEMAND = [(56.5, -10.0, "sulfur", 60, 60), (56.5, -12.0, "calcite", 20, 30)]      # x, y, item, ask while the loop holds fewer, extra on K's filter signal
KHUB = (4.5, -2.5)                   # belt K's hub inserter (scripts/wheel_blue.py)
EXPORT = (71, -14)
ents, cfg, recipes, occ, fluid, opening = [], [], [], {}, {}, {}
loop_tiles, gated, taps, machines = [], [], [], []


def put(name, tx, ty, w=1, h=1, d=N, filt=None, recipe=None, local=True, **params):
    if local:
        tx, ty = tx + LX, ty + LY
    for c in [(tx + i, ty + j) for i in range(w) for j in range(h)]:
        assert c not in occ, "%s at %s overlaps %s" % (name, c, occ[c])
        occ[c] = name
    e = {"name": name, "x": tx + w / 2, "y": ty + h / 2, "direction": d, "params": dict(Q, **params)}
    ents.append(e)
    if filt:
        cfg.append((e["x"], e["y"], filt))
    if recipe:
        recipes.append((e["x"], e["y"], recipe))
    if w >= 3:
        machines.append((e["x"], e["y"], name, recipe or "iron plate"))
    return e


def ins(x, y, d, filt=None, name="fast-inserter", local=True):
    return put(name, x, y, d=d, filt=filt, local=local)


def gate(e, item):
    gated.append((e["x"], e["y"], item, TARGETS[item]))
    return e


def pipe(f, *ts):
    for x, y in ts:
        put("pipe", x, y)
        fluid[(x, y)] = f


def ptg(f, x, y, d):
    put("pipe-to-ground", x, y, d=d)
    fluid[(x, y)] = f
    opening[(x, y)] = {v: k for k, v in DIR.items()}[d]


def layout():
    LONG = "long-handed-inserter"
    wheel_blue.layout()
    k = wheel_blue.lines["K"]
    cut = k.index((55, -31)) + 1                                   # the feed ends where it side-loads K's loop
    KFEED.extend(k[:cut])
    KLOOP.extend(k[cut:])
    # ---- the counted loop, clockwise ----
    loop = ([(x, 0) for x in range(0, LW)] + [(LW, y) for y in range(0, LH)] + [(x, LH) for x in range(LW, 0, -1)] + [(0, y) for y in range(LH, 0, -1)])
    for i, t in enumerate(loop):
        nx = loop[(i + 1) % len(loop)]
        put("express-transport-belt", t[0], t[1], d=DIR[(nx[0] - t[0], nx[1] - t[1])])
        loop_tiles.append((t[0] + LX, t[1] + LY))
    # ---- water: ice off belt W, under the three columns, melter, riser, pipe row ----
    ins(51, -9, E, ["ice"], local=False)
    put("express-transport-belt", 50, -9, d=S, local=False)
    put("express-transport-belt", 50, -8, d=E, local=False)
    put("express-underground-belt", 51, -8, d=E, local=False, type="input")
    put("express-underground-belt", 1, 5, d=E, type="output")
    ins(2, 5, W, ["ice"])
    put("chemical-plant", 3, 4, 3, 3, d=W, recipe="ice-melting")
    pipe("water", *[(6, y) for y in range(2, 10)], *[(x, 9) for x in range(7, 26)], (17, 5), (17, 6), (17, 7), (17, 8), (25, 7), (25, 8))
    # ---- acid and coal at the west end ----
    put("chemical-plant", 7, 2, 3, 3, d=W, recipe="sulfuric-acid")
    ins(8, 1, N, ["sulfur", "iron-plate"])
    put("chemical-plant", 7, 5, 3, 3, d=W, recipe="coal-synthesis")
    ins(8, 8, S, ["carbon", "sulfur"], name=LONG)
    gate(ins(9, 8, N, name=LONG), "coal")
    pipe("acid", (10, 2), (10, 3), (10, 4))
    # ---- refinery, cracking ----
    put("oil-refinery", 11, 3, 5, 5, d=E, recipe="simple-coal-liquefaction")
    ins(13, 2, N, ["coal", "calcite"], name=LONG)
    pipe("heavy", (16, 3), (17, 3))
    put("chemical-plant", 18, 3, 3, 3, d=W, recipe="heavy-oil-cracking")
    # ---- light oil: solid fuel plant, two rocket fuel assemblers ----
    pipe("light", (21, 4), (21, 5), (21, 6), (21, 1), (27, 1))
    ptg("light", 21, 3, S)
    ptg("light", 21, 2, N)
    ptg("light", 22, 1, W)
    ptg("light", 26, 1, E)
    put("chemical-plant", 22, 2, 3, 3, d=W, recipe="solid-fuel-from-light-oil")
    gate(ins(23, 1, S), "solid-fuel")
    put("assembling-machine-3", 26, 2, 3, 3, d=N, recipe="rocket-fuel")
    ins(28, 1, N, ["solid-fuel"])
    gate(ins(29, 3, W), "rocket-fuel")
    put("assembling-machine-3", 22, 5, 3, 3, d=W, recipe="rocket-fuel")
    ins(23, 8, S, ["solid-fuel"], name=LONG)
    gate(ins(24, 8, N, name=LONG), "rocket-fuel")
    # ---- the second coal plant ----
    put("chemical-plant", 26, 5, 3, 3, d=W, recipe="coal-synthesis")
    ins(27, 8, S, ["carbon", "sulfur"], name=LONG)
    gate(ins(28, 8, N, name=LONG), "coal")
    # ---- iron plate for the acid: ore off the ore loop (wheel x 99), furnace, plates onto the east column ----
    ins(98, -8, E, ["iron-ore"], local=False)
    for x in range(97, 92, -1):
        put("express-transport-belt", x, -8, d=W, local=False)
    ins(92, -8, E, ["iron-ore"], local=False)
    put("electric-furnace", 89, -9, 3, 3, local=False)
    gate(ins(88, -8, E, ["iron-plate"], local=False), "iron-plate")
    # ---- taps on K's feed column (wheel x 53), reaching over belt O ----
    for y, item in ((-12, "carbon"), (-11, "carbon"), (-10, "sulfur"), (-6, "calcite")):
        e = gate(ins(55, y, W, [item], name=LONG, local=False), item)
        taps.append((e["x"], e["y"]))
    for row in DECS + DEMAND:
        dy = row[1]
        put("decider-combinator", 56, int(dy) - 1, 1, 2, local=False)
    # ---- export ----
    ins(EXPORT[0], EXPORT[1], S, ["rocket-fuel"], local=False)
    # ---- no two fluids touch ----
    for (x, y), f in fluid.items():
        for dx, dy in DIR:
            n = (x + dx, y + dy)
            g = fluid.get(n)
            joins = opening.get((x, y), (dx, dy)) == (dx, dy) and opening.get(n, (-dx, -dy)) == (-dx, -dy)
            assert g is None or g == f or not joins, "%s pipe at %s touches %s" % (f, (x, y), g)
    return {"entities": len(ents), "loop": len(loop_tiles), "machines": len(machines)}


def lua_list(rows):
    return "{" + ",".join("{" + ",".join(("'%s'" % v) if isinstance(v, str) else ("{" + ",".join("'%s'" % f for f in v) + "}") if isinstance(v, list) else str(v) for v in r) + "}" for r in rows) + "}"


HEAD = ("local s=game.surfaces['SURF'] local hub=s.platform.hub local W=defines.wire_connector_id local o={} local function at(t,x,y) return s.find_entities_filtered{type=t,position={x,y},radius=0.3}[1] end "
        "local function mach(x,y) return s.find_entities_filtered{type={'assembling-machine','furnace'},position={x,y},radius=0.5}[1] end ")
CONFIG = (HEAD + "local n,r=0,0 pcall(function() hub.get_or_create_control_behavior().read_contents=true end) "
          "for _,q in pairs(FILT) do local i=at('inserter',q[1],q[2]) if i then i.use_filters=true i.inserter_filter_mode='whitelist' for k,name in pairs(q[3]) do i.set_filter(k,name) end n=n+1 end end "
          "for _,q in pairs(REC) do local m=mach(q[1],q[2]) if m then m.set_recipe(q[3]) r=r+1 end end o[#o+1]='filters '..n..', recipes '..r "
          "local prev,nb=nil,0 for _,p in pairs(LOOP) do local b=at('transport-belt',p[1]+0.5,p[2]+0.5) if b then local bc=b.get_or_create_control_behavior() bc.read_contents=true bc.read_contents_mode=defines.control_behavior.transport_belt.content_read_mode.hold "
          "if prev then b.get_wire_connector(W.circuit_red,true).connect_to(prev.get_wire_connector(W.circuit_red,true),false) end prev=b nb=nb+1 end end o[#o+1]='loop belts read '..nb "
          "local function cond(i,sig,cmp,k,wire,target,twire) i.get_wire_connector(wire,true).connect_to(target.get_wire_connector(twire or wire,true),false) local cb=i.get_or_create_control_behavior() cb.circuit_enable_disable=true cb.circuit_condition={first_signal={type='item',name=sig},comparator=cmp,constant=k} end "
          "local g=0 for _,q in pairs(GATED) do local i=at('inserter',q[1],q[2]) if i then cond(i,q[3],'<',q[4],W.circuit_red,prev) g=g+1 end end o[#o+1]='gated on the loop '..g "
          "for _,p in pairs(KALL) do local b=at('transport-belt',p[1]+0.5,p[2]+0.5) if b then b.get_wire_connector(W.circuit_red,true).disconnect_all() end end "
          "local function chain(tiles) local last,k=nil,0 for _,p in pairs(tiles) do local b=at('transport-belt',p[1]+0.5,p[2]+0.5) if b then local bc=b.get_or_create_control_behavior() bc.read_contents=true bc.read_contents_mode=defines.control_behavior.transport_belt.content_read_mode.hold "
          "if last then b.get_wire_connector(W.circuit_red,true).connect_to(last.get_wire_connector(W.circuit_red,true),false) end last=b k=k+1 end end return last,k end "
          "local sL,nL=chain(KRING) o[#o+1]='K loop read on red '..nL "
          "local d0,dn=nil,0 for _,q in pairs(DECS) do local dec=s.find_entities_filtered{name='decider-combinator',position={q[1],q[2]},radius=0.6}[1] if dec and sL then local X={type='item',name=q[3]} "
          "local cs={{first_signal={type='item',name=q[4]},comparator='<',constant=q[5],first_signal_networks={red=true,green=false}}} "
          "if q[6]==1 then cs[2]={first_signal={type='item',name='carbon'},comparator='<',constant=RESERVE,first_signal_networks={red=false,green=true},compare_type='or'} dec.get_wire_connector(W.combinator_input_green,true).connect_to(hub.get_wire_connector(W.circuit_green,true),false) end "
          "dec.get_or_create_control_behavior().parameters={conditions=cs,outputs={{signal=X,copy_count_from_input=false,constant=1000}}} "
          "local ir=dec.get_wire_connector(W.combinator_input_red,true) ir.disconnect_all() ir.connect_to(sL.get_wire_connector(W.circuit_red,true),false) "
          "if d0 then dec.get_wire_connector(W.combinator_output_green,true).connect_to(d0.get_wire_connector(W.combinator_output_green,true),false) else d0=dec end dn=dn+1 end end "
          "local t=0 if d0 then for _,q in pairs(TAPS) do local i=at('inserter',q[1],q[2]) if i then i.get_wire_connector(W.circuit_green,true).connect_to(d0.get_wire_connector(W.combinator_output_green,true),false) t=t+1 end end end o[#o+1]='deciders '..dn..', taps behind them '..t "
          "local kh=at('inserter',KX,KY) local an=0 for _,q in pairs(ASKS) do local dec=s.find_entities_filtered{name='decider-combinator',position={q[1],q[2]},radius=0.6}[1] if dec and kh then local X={type='item',name=q[3]} "
          "dec.get_or_create_control_behavior().parameters={conditions={{first_signal=X,comparator='<',constant=q[4]}},outputs={{signal=X,copy_count_from_input=false,constant=q[5]}}} "
          "dec.get_wire_connector(W.combinator_input_red,true).connect_to(prev.get_wire_connector(W.circuit_red,true),false) dec.get_wire_connector(W.combinator_output_red,true).connect_to(kh.get_wire_connector(W.circuit_red,true),false) an=an+1 end end o[#o+1]='demand deciders on K '..an "
          "local ex=at('inserter',EX,EY) if ex then cond(ex,'rocket-fuel','<',CAP,W.circuit_red,hub) o[#o+1]='export gated on the hub at CAP' end rcon.print(table.concat(o,', '))")
SWEEP = (HEAD + "local keep={} for _,n in pairs(KEEP) do keep[n]=true end local moved={} local function back(name,count,quality) if count>0 then hub.insert{name=name,count=count,quality=quality} moved[name]=(moved[name] or 0)+count end end "
         "for _,p in pairs(LOOP) do local b=at('transport-belt',p[1]+0.5,p[2]+0.5) if b then for l=1,2 do local tl=b.get_transport_line(l) for _,it in pairs(tl.get_contents()) do if not keep[it.name] then back(it.name,tl.remove_item{name=it.name,count=it.count,quality=it.quality},it.quality) end end end end end "
         "for x=93,97 do local b=at('transport-belt',x+0.5,-7.5) if b then for l=1,2 do local tl=b.get_transport_line(l) for _,it in pairs(tl.get_contents()) do if it.name~='iron-ore' then back(it.name,tl.remove_item{name=it.name,count=it.count,quality=it.quality},it.quality) end end end end end "
         "for _,x in pairs{50.5} do for _,y in pairs{-8.5,-7.5} do local b=at('transport-belt',x,y) if b then for l=1,2 do local tl=b.get_transport_line(l) for _,it in pairs(tl.get_contents()) do if it.name~='ice' then back(it.name,tl.remove_item{name=it.name,count=it.count,quality=it.quality},it.quality) end end end end end end "
         "local f=mach(90.5,-7.5) if f then for _,id in pairs{defines.inventory.crafter_input,defines.inventory.crafter_output} do local inv=f.get_inventory(id) if inv then for _,it in pairs(inv.get_contents()) do if it.name~='iron-ore' and it.name~='iron-plate' then back(it.name,inv.remove{name=it.name,count=it.count,quality=it.quality},it.quality) end end end end end "
         "local w={} for k,v in pairs(moved) do w[#w+1]=k..' '..v end rcon.print('strays returned to the hub: '..(#w>0 and table.concat(w,', ') or 'none'))")
MODULES = (HEAD + "local nets=game.forces.player.logistic_networks['nauvis'] or {} local function take(name,quality,count) local got=0 for _,net in pairs(nets) do if got<count then got=got+net.remove_item{name=name,quality=quality,count=count-got} end end return got end "
           "local moved={} local empty=0 for _,q in pairs(MACH) do local m=mach(q[1],q[2]) if m then local inv=m.get_module_inventory() local free=inv and inv.count_empty_stacks() or 0 empty=empty+free if APPLY and free>0 then "
           "local order=(m.name=='assembling-machine-3') and {'legendary','epic'} or {'epic','legendary'} for _,ql in pairs(order) do if free>0 then local got=take('productivity-module-2',ql,free) if got>0 then local put=inv.insert{name='productivity-module-2',quality=ql,count=got} "
           "if put<got then game.forces.player.logistic_networks['nauvis'][1].insert{name='productivity-module-2',quality=ql,count=got-put} end free=free-put moved[ql]=(moved[ql] or 0)+put end end end end end end "
           "local w={} for k,v in pairs(moved) do w[#w+1]=v..' '..k end rcon.print('empty module slots found '..empty..'; productivity module 2 moved from the Nauvis network: '..(#w>0 and table.concat(w,', ') or 'none'))")
STATUS = (HEAD + "local w={} for _,q in pairs(MACH) do local e=mach(q[1],q[2]) if e then local k='?' for n,v in pairs(defines.entity_status) do if v==e.status then k=n end end local rc=e.get_recipe() local m=0 local mi=e.get_module_inventory() if mi then m=mi.get_item_count() end local fl='' for n,v in pairs(e.get_fluid_contents()) do fl=fl..' '..n..'='..math.floor(v) end "
          "w[#w+1]=string.format('%-28s %5.1f,%5.1f %-26s made %5d modules %d%s',(rc and rc.name or e.name),e.position.x,e.position.y,k,e.products_finished,m,fl) else w[#w+1]='MISSING machine at '..q[1]..','..q[2] end end "
          "local b={} for _,p in pairs(LOOP) do local e=at('transport-belt',p[1]+0.5,p[2]+0.5) if e then for l=1,2 do for _,it in pairs(e.get_transport_line(l).get_contents()) do b[it.name]=(b[it.name] or 0)+it.count end end end end local q={} for k,v in pairs(b) do q[#q+1]=k..' '..v end table.sort(q) "
          "local tp={} for _,p in pairs(TAPS) do local i=at('inserter',p[1],p[2]) if i then local k='?' for n,v in pairs(defines.entity_status) do if v==i.status then k=n end end tp[#tp+1]=(i.get_filter(1) and i.get_filter(1).name or '-')..' '..k end end "
          "local dl={} for _,q in pairs(DECS) do local dec=s.find_entities_filtered{name='decider-combinator',position={q[1],q[2]},radius=0.6}[1] if dec then local function sig(id,name) local v=0 for _,x in pairs(dec.get_signals(id) or {}) do if x.signal.name==name then v=x.count end end return v end "
          "dl[#dl+1]=q[4]..' '..sig(W.combinator_input_red,q[4])..' ('..q[3]..' taps work above '..q[5]..(sig(W.combinator_output_green,q[3])>0 and ', BLOCKED now)' or ')') end end local ds='blue first, on the loop of K: '..table.concat(dl,', ')..'; carbon reserve in the hub RESERVE' "
          "local al={} for _,q in pairs(ASKS) do local dec=s.find_entities_filtered{name='decider-combinator',position={q[1],q[2]},radius=0.6}[1] if dec then local v=0 for _,x in pairs(dec.get_signals(W.combinator_output_red) or {}) do if x.signal.name==q[3] then v=x.count end end al[#al+1]=q[3]..(v>0 and ' ASKING' or ' quiet') end end ds=ds..'; asking K for more: '..table.concat(al,', ') "
          "local f=game.forces.player.get_item_production_statistics(s) local inv=hub.get_inventory(defines.inventory.hub_main) local function fl(n,cat,pr) return string.format('%.1f',f.get_flow_count{name=n,category=cat,precision_index=pr}) end local P=defines.flow_precision_index "
          "local ex=at('inserter',EX,EY) local es='?' if ex then for n,v in pairs(defines.entity_status) do if v==ex.status then es=n end end end "
          "rcon.print(table.concat(w,'@@')..'@@on the loop: '..table.concat(q,', ')..'@@taps: '..table.concat(tp,' ; ')..'@@'..ds..'@@export inserter '..es..' (cap CAP), providing to other platforms '..tostring(hub.providing_to_other_platforms)"
          "..'@@rocket fuel made a minute: '..fl('rocket-fuel','input',P.one_minute)..' (1 min) '..fl('rocket-fuel','input',P.ten_minutes)..' (10 min) '..fl('rocket-fuel','input',P.one_hour)..' (1 h); in hub '..inv.get_item_count('rocket-fuel')"
          "..'@@carbon made '..fl('carbon','input',P.ten_minutes)..' used '..fl('carbon','output',P.ten_minutes)..' a minute (10 min), in hub '..inv.get_item_count('carbon')..'; sulfur made '..fl('sulfur','input',P.ten_minutes)..' used '..fl('sulfur','output',P.ten_minutes)..', in hub '..inv.get_item_count('sulfur')"
          "..'@@coal made '..fl('coal','input',P.ten_minutes)..' used '..fl('coal','output',P.ten_minutes)..'; chemical science '..fl('chemical-science-pack','input',P.ten_minutes)..' a minute (10 min), in hub '..inv.get_item_count('chemical-science-pack')..'; ice in hub '..inv.get_item_count('ice')..', calcite '..inv.get_item_count('calcite'))")


def fill(code, surface):
    return (code.replace("SURF", surface).replace("FILT", lua_list([(x, y, fl) for x, y, fl in cfg])).replace("REC", lua_list(recipes))
            .replace("LOOP", lua_list(loop_tiles)).replace("GATED", lua_list(gated)).replace("TAPS", lua_list(taps))
            .replace("MACH", lua_list([(x, y) for x, y, _, _ in machines])).replace("KEEP", "{" + ",".join("'%s'" % k for k in TARGETS) + "}")
            .replace("CAP", str(CAP)).replace("RESERVE", str(RESERVE)).replace("ASKS", lua_list(DEMAND)).replace("KX", str(KHUB[0])).replace("KY", str(KHUB[1])).replace("KALL", lua_list(KFEED + KLOOP)).replace("KRING", lua_list(KLOOP)).replace("DECS", lua_list(DECS))
            .replace("EX", str(EXPORT[0] + .5)).replace("EY", str(EXPORT[1] + .5)))


def main():
    step = sys.argv[1]
    apply = "--apply" in sys.argv
    if "--only" not in sys.argv:
        sys.argv += ["--only", "gleba"]
    print(layout())
    if step == "check":
        return
    for name, planet, surface, turrets in wheels():
        print("==", name, surface or "(not created)")
        if not surface:
            continue
        if step == "build":
            have = tools["run_lua"]("local s=game.surfaces['%s'] local t={} for _,p in pairs({%s}) do t[#t+1]=s.count_entities_filtered{position=p,radius=0.2} end rcon.print(table.concat(t,','))"
                                    % (surface, ",".join("{%s,%s}" % (e["x"], e["y"]) for e in ents))).strip().split(",")
            todo = [e for e, hv in zip(ents, have) if hv == "0"]          # only what does not stand yet: safe to run again
            ok, bad = place_all(todo, surface, apply)
            print("missing pieces", len(todo), "placed" if apply else "dry run", ok, "failed", bad)
        if step == "config" or (step == "build" and apply):
            print(tools["run_lua"](fill(CONFIG, surface)))
        if step == "sweep" or (step == "build" and apply):
            print(tools["run_lua"](fill(SWEEP, surface)))
        if step == "modules":
            print(tools["run_lua"](fill(MODULES, surface).replace("APPLY", "true" if apply else "false")))
        if step == "provide":
            on = sys.argv[2] == "on"
            print(tools["run_lua"]("local h=game.surfaces['%s'].platform.hub h.providing_to_other_platforms=%s rcon.print('providing to other platforms: '..tostring(h.providing_to_other_platforms))" % (surface, "true" if on else "false")))
        if step == "status":
            print(tools["run_lua"](fill(STATUS, surface)).replace("@@", "\n"))


if __name__ == "__main__":
    main()
