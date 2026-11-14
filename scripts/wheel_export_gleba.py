#!/usr/bin/env python3
"""The export works of a wheel: rocket fuel from HUB STOCK (the Captain, 2026-11-14: Gleba Wheel = rocket fuel, "increase production
to the maximum that station can", and make it available to other platforms in its orbit).
Why not the rocket district (scripts/wheel_rocket.py): it lives off chunks tapped from the west spoke, and the Gleba Wheel's west spoke
carries next to no carbonic chunks, so its coal plant starved (0.5 rocket fuel a minute) while the hub held 32,000 carbon. This cell
stands on the free deck south of the blue block and is fed out of the hub over belt W (the ice belt of scripts/wheel_blue.py).
  site     wheel x 57..87, y -13..-3: a closed, counted loop belt (clockwise) with the chemistry inside, as in the rocket district:
           ice melter -> water riser and pipe row; acid plant -> refinery (simple coal liquefaction) -> heavy cracking -> light oil ->
           solid fuel plant and two rocket fuel assemblers; two coal plants (carbon + sulfur + water). Every producer's inserter
           works only while the loop holds fewer than TARGETS of its item.
  supply   belt W carried one item (ice) of its hub inserter's five filters, and runs up x 52 right past the site.
           ask      three deciders (55,-4 / -6 / -8) put carbon, sulfur and calcite on the red wire of W's hub inserter (4.5,-0.5)
                    while this loop holds fewer than the item's DEMAND; W's own circuit subtracts what already lies on W, so
                    the number asked is the most that is ever under way. Carbon and sulfur only while the hub holds more than
                    RESERVE carbon: below that everything is blue science's (it draws through belt K, untouched by this cell).
           split    a splitter in W's column (51..52,-12) with filter ice: ice, and only ice, goes on north to blue's melters;
                    everything else leaves west, round and under the three columns (51,-11 -> 56,-11) and side-loads the
                    loop's west column. W's dead end can never fill with the cell's goods. W's green count wire is bridged
                    across the splitter.
           overflow THE BRANCH MUST NEVER STAND STILL: a carbon waiting at the first splitter holds up all the ice behind it,
                    and blue's melters run dry (seen within twenty minutes of the first build: the loop's west lane stood
                    full of sulfur and calcite, the branch backed up, one blue melter had no ice). So a second splitter on
                    the branch (49..50,-12, facing south) prefers the loop and hands whatever the loop cannot take to the
                    pack belt (49,-11 side-loads x 48), which carries it back into the hub.
                    W's count wire does not see undergrounds or the branch, so more than the asked number can be under way
                    (seen: 149 sulfur on the loop against an ask below 50): the asks are kept small.
           flow     W used to be a standing queue of ice (target 250 on 88 tiles), where the cell's goods would wait behind
                    ice that only moves as blue melts it. A constant combinator (55,-13) puts ice ICEOFF on W's filter wire:
                    W now carries about 80 ice and flows freely (80 ice under way is about 5 a second, blue melts 1 to 2).
           TRIED FIRST AND TAKEN OUT (same day, scripts/_wxg_retire_k.py): taps on belt K's feed column. K's feed is a standing
           queue that blue's junction eats from the head at a fixed number of items a second, K's hub inserter loads sulfur
           before carbon before calcite, and the feed is physically full below K's carbon target. Every sulfur or calcite let
           through cost blue a carbon (blue's coal 72 a minute instead of 100), drawing carbon kept the carbon filter on and
           locked calcite out for blue's refinery, and no gate (feed fullness, K's count, K's loop stock) held for long.
  ice      one inserter west of belt W (51,-9), two belt tiles and an underground under the three columns to the melter (58,-8)
  iron     acid needs a plate per craft: an inserter takes iron ore off the ore loop (99,-8), five belt tiles, a furnace (89..91),
           plates onto the loop's east column
  export   an inserter at (71,-14) lifts rocket fuel off the loop's top row onto the pack belt (y -15), which the hub takes in;
           it works while the hub holds fewer than CAP. `provide on` lets other platforms in the orbit request it
           (request filter request_from='platforms').
  modules  `modules --apply` MOVES factory-made productivity module 2 from the Nauvis network into the cell's empty slots (epic into
           the plants, legendary into the two assemblers if there are any, else the other) and prints what it moved.
Per rocket fuel (with the modules): about 24 carbon, 6 sulfur, 1.3 calcite, 4 ice. Two coal plants are the cell's limit (about 107
coal a minute, 16 to 17 rocket fuel); above that W's hub inserter, then the wheel's carbon income.
`build` places only what does not stand yet. After a quality upgrade, and after `wheel_blue.py config` (it rewires W's circuit),
run `config` here.
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
DEMAND = [(55.5, -4.0, "carbon", 90, 90, 1), (55.5, -6.0, "sulfur", 30, 24, 1), (55.5, -8.0, "calcite", 14, 14, 0)]
# x, y, item, ask while the loop holds fewer, how many may be under way on W, 1 = only above the hub's carbon reserve
WHUB = (4.5, -0.5)                   # belt W's hub inserter (scripts/wheel_blue.py)
SPLIT = (52.0, -11.5)                # splitter, tiles (51,-12) and (52,-12): ice north, the rest west
OVER = (50.0, -11.5)                 # overflow splitter on the branch, tiles (49,-12) and (50,-12), facing south: loop first, else the pack belt
CONST = (55.5, -12.5)                # constant combinator: ice offset on W's filter wire
ICEOFF, WMAX = -170, 80              # W's ice target is 250 (wheel_blue.TARGETS): 250 - 170 = 80 under way
WTILES = []                          # every tile of belt W, filled by layout()
EXPORT = (71, -14)
ents, cfg, recipes, occ, fluid, opening = [], [], [], {}, {}, {}
loop_tiles, gated, machines = [], [], []


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
        recipes.append((e["x"], e["y"], recipe, d))
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
    WTILES.extend(wheel_blue.lines["W"])
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
    # ---- supply over belt W: splitter (ice north, the rest west), round and under the three columns, side-load on the west column ----
    put("express-splitter", 51, -12, 2, 1, d=N, local=False)
    put("express-transport-belt", 51, -13, d=W, local=False)
    put("express-transport-belt", 50, -13, d=S, local=False)
    put("express-splitter", 49, -12, 2, 1, d=S, local=False)
    put("express-transport-belt", 49, -11, d=W, local=False)
    put("express-transport-belt", 50, -11, d=E, local=False)
    put("express-underground-belt", 51, -11, d=E, local=False, type="input")
    put("express-underground-belt", 56, -11, d=E, local=False, type="output")
    for row in DEMAND:
        put("decider-combinator", 55, int(row[1]) - 1, 1, 2, local=False)
    put("constant-combinator", 55, -13, local=False)
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
          "for _,q in pairs(REC) do local m=mach(q[1],q[2]) if m then if not (m.get_recipe() and m.get_recipe().name==q[3]) then m.set_recipe(q[3]) end if m.direction~=q[4] then m.direction=q[4] end r=r+1 end end o[#o+1]='filters '..n..', recipes '..r "
          "local prev,nb=nil,0 for _,p in pairs(LOOP) do local b=at('transport-belt',p[1]+0.5,p[2]+0.5) if b then local bc=b.get_or_create_control_behavior() bc.read_contents=true bc.read_contents_mode=defines.control_behavior.transport_belt.content_read_mode.hold "
          "if prev then b.get_wire_connector(W.circuit_red,true).connect_to(prev.get_wire_connector(W.circuit_red,true),false) b.get_wire_connector(W.circuit_green,true).connect_to(prev.get_wire_connector(W.circuit_green,true),false) end prev=b nb=nb+1 end end o[#o+1]='loop belts read '..nb "
          "local function cond(i,sig,cmp,k,wire,target,twire) i.get_wire_connector(wire,true).connect_to(target.get_wire_connector(twire or wire,true),false) local cb=i.get_or_create_control_behavior() cb.circuit_enable_disable=true cb.circuit_condition={first_signal={type='item',name=sig},comparator=cmp,constant=k} end "
          "local g=0 for _,q in pairs(GATED) do local i=at('inserter',q[1],q[2]) if i then cond(i,q[3],'<',q[4],W.circuit_red,prev) g=g+1 end end o[#o+1]='gated on the loop '..g "
          "local wh=at('inserter',WHX,WHY) local sp=s.find_entities_filtered{type='splitter',position={SPX,SPY},radius=0.6}[1] "
          "if sp then sp.splitter_filter={name='ice'} sp.splitter_output_priority='right' local a=at('transport-belt',SPX+0.5,SPY+1) local b=at('transport-belt',SPX+0.5,SPY-1) "
          "if a and b then a.get_wire_connector(W.circuit_green,true).connect_to(b.get_wire_connector(W.circuit_green,true),false) end o[#o+1]='splitter: ice north, W count wire bridged' else o[#o+1]='NO splitter' end "
          "local ov=s.find_entities_filtered{type='splitter',position={OVX,OVY},radius=0.6}[1] if ov then ov.splitter_output_priority='left' o[#o+1]='overflow splitter: loop first' else o[#o+1]='NO overflow splitter' end "
          "local cc=s.find_entities_filtered{name='constant-combinator',position={CCX,CCY},radius=0.4}[1] if cc and wh and sp then local cb=cc.get_or_create_control_behavior() local sec=cb.get_section(1) or cb.add_section() sec.set_slot(1,{value={type='item',name='ice',quality='normal'},min=ICEOFF}) "
          "cc.get_wire_connector(W.circuit_red,true).connect_to(wh.get_wire_connector(W.circuit_red,true),false) o[#o+1]='ice offset ICEOFF on W' end "
          "local an=0 for _,q in pairs(ASKS) do local dec=s.find_entities_filtered{name='decider-combinator',position={q[1],q[2]},radius=0.6}[1] if dec and wh and sp then local X={type='item',name=q[3]} "
          "local cs={{first_signal=X,comparator='<',constant=q[4],first_signal_networks={red=true,green=false}}} if q[6]==1 then cs[2]={first_signal={type='item',name='carbon'},comparator='>',constant=RESERVE,first_signal_networks={red=false,green=true},compare_type='and'} end "
          "dec.get_or_create_control_behavior().parameters={conditions=cs,outputs={{signal=X,copy_count_from_input=false,constant=q[5]}}} "
          "local ir=dec.get_wire_connector(W.combinator_input_red,true) ir.disconnect_all() ir.connect_to(prev.get_wire_connector(W.circuit_red,true),false) local ig=dec.get_wire_connector(W.combinator_input_green,true) ig.disconnect_all() ig.connect_to(hub.get_wire_connector(W.circuit_green,true),false) "
          "dec.get_wire_connector(W.combinator_output_red,true).connect_to(wh.get_wire_connector(W.circuit_red,true),false) an=an+1 end end o[#o+1]='asks on W '..an "
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
          "local wc={} for _,p in pairs(WTILES) do local e=s.find_entities_filtered{type={'transport-belt','underground-belt'},position={p[1]+0.5,p[2]+0.5},radius=0.3}[1] if e then for l=1,2 do for _,it in pairs(e.get_transport_line(l).get_contents()) do wc[it.name]=(wc[it.name] or 0)+it.count end end end end local wq={} for k,v in pairs(wc) do wq[#wq+1]=k..' '..v end table.sort(wq) "
          "local al={} for _,q in pairs(ASKS) do local dec=s.find_entities_filtered{name='decider-combinator',position={q[1],q[2]},radius=0.6}[1] if dec then local function sig(id,name) local v=0 for _,x in pairs(dec.get_signals(id) or {}) do if x.signal.name==name then v=x.count end end return v end "
          "al[#al+1]=q[3]..' (loop '..sig(W.combinator_input_red,q[3])..', asks below '..q[4]..', W filter signal '..sig(W.combinator_output_red,q[3])..')' end end "
          "local sp=s.find_entities_filtered{type='splitter',position={SPX,SPY},radius=0.6}[1] local wh=at('inserter',WHX,WHY) local ws='?' if wh then for n,v in pairs(defines.entity_status) do if v==wh.status then ws=n end end end "
          "local ov=s.find_entities_filtered{type='splitter',position={OVX,OVY},radius=0.6}[1] local br=0 for _,p in pairs{{51,-13},{50,-13},{50,-11},{51,-11},{56,-11}} do local e=s.find_entities_filtered{type={'transport-belt','underground-belt'},position={p[1]+0.5,p[2]+0.5},radius=0.3}[1] if e then for l=1,2 do br=br+e.get_transport_line(l).get_item_count() end end end "
          "local ds='ON BELT W: '..table.concat(wq,', ')..'; on the branch '..br..' (5 tiles, 40 places); overflow splitter '..(ov and 'stands' or 'MISSING')..'; hub inserter '..ws..'; splitter '..(sp and ('filter '..(sp.splitter_filter and sp.splitter_filter.name or 'NONE')..' to the '..sp.splitter_output_priority) or 'MISSING')..'@@asks: '..table.concat(al,' ; ')..'; carbon reserve in the hub RESERVE' "
          "local f=game.forces.player.get_item_production_statistics(s) local inv=hub.get_inventory(defines.inventory.hub_main) local function fl(n,cat,pr) return string.format('%.1f',f.get_flow_count{name=n,category=cat,precision_index=pr}) end local P=defines.flow_precision_index "
          "local ex=at('inserter',EX,EY) local es='?' if ex then for n,v in pairs(defines.entity_status) do if v==ex.status then es=n end end end "
          "rcon.print(table.concat(w,'@@')..'@@on the loop: '..table.concat(q,', ')..'@@'..ds..'@@export inserter '..es..' (cap CAP), providing to other platforms '..tostring(hub.providing_to_other_platforms)"
          "..'@@rocket fuel made a minute: '..fl('rocket-fuel','input',P.one_minute)..' (1 min) '..fl('rocket-fuel','input',P.ten_minutes)..' (10 min) '..fl('rocket-fuel','input',P.one_hour)..' (1 h); in hub '..inv.get_item_count('rocket-fuel')"
          "..'@@carbon made '..fl('carbon','input',P.ten_minutes)..' used '..fl('carbon','output',P.ten_minutes)..' a minute (10 min), in hub '..inv.get_item_count('carbon')..'; sulfur made '..fl('sulfur','input',P.ten_minutes)..' used '..fl('sulfur','output',P.ten_minutes)..', in hub '..inv.get_item_count('sulfur')"
          "..'@@coal made '..fl('coal','input',P.ten_minutes)..' used '..fl('coal','output',P.ten_minutes)..'; chemical science '..fl('chemical-science-pack','input',P.ten_minutes)..' a minute (10 min), in hub '..inv.get_item_count('chemical-science-pack')..'; ice in hub '..inv.get_item_count('ice')..', calcite '..inv.get_item_count('calcite'))")


def fill(code, surface):
    return (code.replace("SURF", surface).replace("FILT", lua_list([(x, y, fl) for x, y, fl in cfg])).replace("REC", lua_list(recipes))
            .replace("LOOP", lua_list(loop_tiles)).replace("GATED", lua_list(gated)).replace("WTILES", lua_list(WTILES))
            .replace("MACH", lua_list([(x, y) for x, y, _, _ in machines])).replace("KEEP", "{" + ",".join("'%s'" % k for k in TARGETS) + "}")
            .replace("CAP", str(CAP)).replace("RESERVE", str(RESERVE)).replace("ASKS", lua_list(DEMAND)).replace("WHX", str(WHUB[0])).replace("WHY", str(WHUB[1]))
            .replace("OVX", str(OVER[0])).replace("OVY", str(OVER[1])).replace("SPX", str(SPLIT[0])).replace("SPY", str(SPLIT[1])).replace("CCX", str(CONST[0])).replace("CCY", str(CONST[1])).replace("ICEOFF", str(ICEOFF)).replace("WMAX", str(WMAX))
            .replace("EX", str(EXPORT[0] + .5)).replace("EY", str(EXPORT[1] + .5)))


# Step `build --apply`, once: the W belt tile under the splitter comes out (what lies on it goes into the hub), and W's standing queue of
# ice is taken back into the hub from the hub end until WMAX is left, so the belt flows from the first minute.
SPLICE = (HEAD + "local sp=s.find_entities_filtered{type='splitter',position={SPX,SPY},radius=0.6}[1] local b=at('transport-belt',SPX+0.5,SPY) if b and not sp then for l=1,2 do local tl=b.get_transport_line(l) for _,it in pairs(tl.get_contents()) do hub.insert{name=it.name,count=it.count,quality=it.quality} end tl.clear() end b.destroy() rcon.print('W belt tile under the splitter removed') else rcon.print(sp and 'splitter stands' or 'no W belt at the splitter tile') end")
TRIMW = (HEAD + "local tot=0 local ts={} for _,p in pairs(WTILES) do local e=at('transport-belt',p[1]+0.5,p[2]+0.5) if e then ts[#ts+1]=e for l=1,2 do tot=tot+e.get_transport_line(l).get_item_count('ice') end end end local back=0 "
         "for _,e in pairs(ts) do for l=1,2 do local tl=e.get_transport_line(l) local c=tl.get_item_count('ice') if c>0 and tot-back>WMAX then local r=tl.remove_item{name='ice',count=math.min(c,tot-back-WMAX)} back=back+r end end end if back>0 then hub.insert{name='ice',count=back} end rcon.print('ice on W '..tot..', taken back into the hub '..back)")


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
            stands = tools["run_lua"]("rcon.print(game.surfaces['%s'].count_entities_filtered{type='splitter',position={%s,%s},radius=0.6})" % (surface, SPLIT[0], SPLIT[1])).strip() != "0"
            have = tools["run_lua"]("local s=game.surfaces['%s'] local t={} for _,p in pairs({%s}) do t[#t+1]=s.count_entities_filtered{position=p,radius=0.2} end rcon.print(table.concat(t,','))"
                                    % (surface, ",".join("{%s,%s}" % (e["x"], e["y"]) for e in ents))).strip().split(",")
            todo = [e for e, hv in zip(ents, have) if hv == "0" and e["name"] != "express-splitter"]          # only what does not stand yet: safe to run again
            over = tools["run_lua"]("rcon.print(game.surfaces['%s'].count_entities_filtered{type='splitter',position={%s,%s},radius=0.6})" % (surface, OVER[0], OVER[1])).strip() != "0"
            if not over:
                if apply:
                    print(tools["run_lua"](fill(SPLICE, surface).replace(str(SPLIT[0]), str(OVER[0]))))      # same step, at the overflow splitter's belt tile (50,-12)
                    todo.append([e for e in ents if e["name"] == "express-splitter" and e["x"] == OVER[0]][0])
                else:
                    print("the overflow splitter replaces the branch belt at (50,-12): not in the dry run")
            if not stands:
                if apply:
                    print(tools["run_lua"](fill(SPLICE, surface)))
                    todo.append([e for e in ents if e["name"] == "express-splitter" and e["x"] == SPLIT[0]][0])
                else:
                    print("the splitter replaces the W belt tile at (52,-12): not in the dry run")
            ok, bad = place_all(todo, surface, apply)
            print("missing pieces", len(todo), "placed" if apply else "dry run", ok, "failed", bad)
            if apply and not (stands and over):
                print(tools["run_lua"](fill(CONFIG, surface)))
                print(tools["run_lua"](fill(TRIMW, surface)))
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
