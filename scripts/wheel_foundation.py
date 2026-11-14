#!/usr/bin/env python3
"""Space platform foundation made in orbit on the Nauvis Wheel and handed hub to hub to the triangle (the Captain, 2026-11-14:
"Make them in orbit", then "increase production to the maximum amount those stations can"). No rockets.
NAUVIS WHEEL ONLY (platform-13). The other wheels are not touched; see "roll-out" at the end.

Why here. The hub's 32 edge tiles are all taken, so the works cannot have its own hub inserters. The red science line in the south
avenue (wheel_red.py) has two: iron ore out (-0.5,4.5) and copper ore out (-1.5,4.5), feeding one belt (a lane each) that passes the
six red units and dead-ends at 18,16. Red science stands at its cap of 20,000 packs with no taker, so that belt was idle. The works
is the continuation of that belt: ore that passes the red units rides on to a foundry district south of the loop. Red science keeps
first call by position (it sits upstream) and by gate (below).

  conveyor   18,15 east, 19,15..48 south (under the lamp at 19,36, under the loop at 19,41..42, under the lamp at 19,46)
  splitter   19..20,49, filter calcite to the east belt. x=19 (y 50..79) carries the ores, iron on one lane and copper on the
             other (pure lanes, so the dead end is safe). The calcite belt is a LOOP: x=20 south (y 50..80), x=21 north, back
             onto 20,50 from the side. As a dead end it stood still only at the far end and line A, nearest the splitter, starved.
  district   new deck x 1..23, y 46..82, all machines west of the ore belt, molten metal port to port (foundries facing west),
             a melter at x 13..17 and its caster at x 8..12 in each row:
             line A   iron -> steel   y 52..56          copper  copper -> cable  y 58..62
             line B   iron -> steel   y 64..68          line C  y 70..74          line D  y 76..80
             three assemblers (space-platform-foundation) at x 4..6: y 56..58 (steel from A, cable direct), y 62..64 (steel from
             B, cable direct), y 74..76 (steel from C and D; cable by belt: inserter 7,60 -> 6,60 west, down x=3, east along
             y=72 to 5,72, inserter 5,73). Bulk inserters at x=7 hand steel and cable straight from caster to assembler.
             ore inserters at x=18 (bulk, filtered), calcite by long-handed inserters at x=18 reaching over the ore belt
  return     inserters at 3,57 / 3,63 / 3,75 -> belt x=2 north to y=47, west to x=0, under the loop (0,46 -> 0,44), north to 0,40,
             where it side-loads onto the south crushers' product belt (y=39), which ends in the hub
  control    four deciders in the red clearing at 1..4, 8..9 (inputs: the hub on red, the belt count on green):
             W  works on: hub foundation < FCAP and iron ore > RES_FE and copper ore > RES_CU and calcite > RES_CA
             R  red on:   hub automation science < RED (the cap wheel_red.py had on the two hub inserters)
             the copper hub inserter runs while W or R; the iron hub inserter takes its filter from the circuit: calcite while W
             and the whole ore path (every belt tile from the hub to the district and the calcite loop, wired green, read-hold)
             carries fewer than CAL calcite, else iron ore while W or R. Calcite rides the IRON lane: the copper lane moves at
             1.4 ore a second, so calcite on it took eight minutes to arrive (first build). The twelve ore inserters of the red
             units run only while R: that is what now stops red science at its cap (before, the hub inserters did).
             RES_FE is the science reserve: space science, the blue block and the plate works draw the same hub ore through
             their own inserters, and the works stops when the hub is down to RES_FE iron ore. The works uses no hub steel.
  stack      `stack`: the iron hub inserter (-0.5,4.5) upgraded in place to a stack inserter (researched; belt stack 4). One
             bulk inserter gave the lane 18 ore a second and two of four lines starved; stacked it carries what four lines take.
  modules    melters 4 epic productivity 2; steel and cable casters 2 epic productivity 2 + 2 speed 3; assemblers 4 speed
             modules (the recipe takes no productivity; the autopilot's module mall fills empty slots within a minute, this
             step only corrects the foundries and fills what is empty). Moved from the Nauvis network, never spawned.
  triangle   `triangle`: a request section 'foundation-works <index>' on the Nauvis Triangle hub, foundation min TMIN max TMAX,
             request_from platforms, import_from nauvis. The wheel already has providing_to_other_platforms = true.

Measured 2026-11-14 (scripts/_wf_rate.py): 100 foundations a minute from about 1,400 iron ore a minute (13.8 ore, 1.5 copper ore
and 0.3 calcite a foundation; casting-steel counts +123% here). The four steel casters allow about 114. The hub's ore stayed level
at 32,000: the wheel crushed about 1,850 iron ore a minute from about 130 metallic chunks, which is all that arrives, so the
metallic chunk income is the limit that is left. More casters on productivity alone (12.2 ore a foundation) or more rim collectors
are the next steps; a fifth line needs both.

CAREFUL: `wheel_red.py config` on this wheel puts the two hub inserters back on the hub's own wire while the iron one still takes
its filters from the circuit: it would then pull every item the hub holds. After any `wheel_red.py config` here, and after a quality
upgrade (over-reach wires and belt read modes are dropped), run `wheel_foundation.py config` at once.
Roll-out to the other wheels: same script with SURF changed; each has the same red line and the same free ground south of the
loop. Check first that the wheel's red science is capped or wanted less than foundations, and its metallic income. Not done.
Steps, in order: check | build [--apply] | expand [--apply] (lines C, D) | loop [--apply] (calcite loop) | stack | config | modules |
triangle | status. Each build step refuses when its part stands. config and modules are safe to repeat.
Usage: wheel_foundation.py check | build | expand | loop [--apply] | stack | config | modules | triangle | status"""
import json
import sys

from _game import tools
from _wheels import lay_foundation

SURF = "platform-13"
TRIANGLE = "Nauvis Triangle 1"
Q = {"quality": "epic"}
N, E, S, W = 0, 4, 8, 12
FCAP, RES_FE, RES_CU, RES_CA, RED, CAL = 4000, 10000, 5000, 2000, 20000, 100
TMIN, TMAX = 500, 2000

ents, ents2, ents3, tiles = [], [], [], set()


def put(name, x, y, d=N, **params):
    ents.append({"name": name, "x": x, "y": y, "direction": d, "params": dict(Q, **params)})


def belt(x, y, d):
    put("express-transport-belt", x + .5, y + .5, d)


def ug(x, y, d, kind):
    put("express-underground-belt", x + .5, y + .5, d, type=kind)


MELT = [(15.5, 54.5, "iron-ore-melting"), (15.5, 60.5, "copper-ore-melting"), (15.5, 66.5, "iron-ore-melting"), (15.5, 72.5, "iron-ore-melting"), (15.5, 78.5, "iron-ore-melting")]
CAST = [(10.5, 54.5, "casting-steel"), (10.5, 60.5, "casting-copper-cable"), (10.5, 66.5, "casting-steel"), (10.5, 72.5, "casting-steel"), (10.5, 78.5, "casting-steel")]
ASM = [(5.5, 57.5), (5.5, 63.5), (5.5, 75.5)]
STAGE1 = (3, 3, 2, 12)                                                             # how many of MELT, CAST, ASM, FILT the first build placed
FILT = [(18.5, 53.5, "iron-ore"), (18.5, 55.5, "calcite"), (18.5, 59.5, "copper-ore"), (18.5, 61.5, "calcite"), (18.5, 65.5, "iron-ore"), (18.5, 67.5, "calcite"),
        (7.5, 56.5, "steel-plate"), (7.5, 58.5, "copper-cable"), (7.5, 62.5, "copper-cable"), (7.5, 64.5, "steel-plate"),
        (3.5, 57.5, "space-platform-foundation"), (3.5, 63.5, "space-platform-foundation"),
        (18.5, 71.5, "iron-ore"), (18.5, 73.5, "calcite"), (18.5, 77.5, "iron-ore"), (18.5, 79.5, "calcite"), (7.5, 74.5, "steel-plate"), (7.5, 76.5, "steel-plate"),
        (7.5, 60.5, "copper-cable"), (5.5, 73.5, "copper-cable"), (3.5, 75.5, "space-platform-foundation")]
PICK_N = {(5.5, 73.5)}                                                             # this one picks up from the north (the cable belt's end)
DECIDERS = [(1.5, 9.0), (2.5, 9.0), (3.5, 9.0), (4.5, 9.0)]                       # W, R, calcite, copper
ORE_PATH = []                                                                      # every belt tile that can carry calcite, hub to district


def layout():
    belt(18, 15, E)
    belt(19, 15, S)
    for y in range(16, 35):
        belt(19, y, S)
    ug(19, 35, S, "input")
    ug(19, 37, S, "output")
    belt(19, 38, S)
    belt(19, 39, S)
    ug(19, 40, S, "input")
    ug(19, 43, S, "output")
    belt(19, 44, S)
    ug(19, 45, S, "input")
    ug(19, 47, S, "output")
    belt(19, 48, S)
    put("express-splitter", 20.0, 49.5, S)
    for y in range(50, 68):
        belt(19, y, S)
        belt(20, y, S)
    nm, nc, na, nf = STAGE1
    for x, y, _ in MELT[:nm] + CAST[:nc]:
        put("foundry", x, y, W)
    for x, y in ASM[:na]:
        put("assembling-machine-3", x, y)
    for x, y, item in FILT[:nf]:
        put("long-handed-inserter" if item == "calcite" else "bulk-inserter", x, y, E)
    for y in range(63, 47, -1):
        belt(2, y, N)
    belt(2, 47, W)
    belt(1, 47, W)
    belt(0, 47, N)
    ug(0, 46, N, "input")
    ug(0, 44, N, "output")
    for y in range(43, 39, -1):
        belt(0, y, N)
    for x, y in DECIDERS:
        put("decider-combinator", x, y, N)
    for x in range(1, 24):
        for y in range(46, 83):
            tiles.add((x, y))
    # stage 2 (`expand`): lines C and D south of line B, a third assembler between their casters, cable to it by belt
    first = len(ents)
    for y in range(68, 80):
        belt(19, y, S)
        belt(20, y, S)
    for x, y, _ in MELT[nm:] + CAST[nc:]:
        put("foundry", x, y, W)
    for x, y in ASM[na:]:
        put("assembling-machine-3", x, y)
    for x, y, item in FILT[nf:]:
        put("long-handed-inserter" if item == "calcite" else "bulk-inserter", x, y, N if (x, y) in PICK_N else E)
    for x in (6, 5, 4):
        belt(x, 60, W)
    belt(3, 60, S)
    belt(3, 61, S)
    ug(3, 62, S, "input")
    ug(3, 64, S, "output")
    for y in range(65, 72):
        belt(3, y, S)
    belt(3, 72, E)
    belt(4, 72, E)
    belt(5, 72, E)
    for y in range(75, 63, -1):
        belt(2, y, N)
    ents2.extend(ents[first:])
    del ents[first:]
    # stage 3 (`loop`): the calcite belt closed into a loop (x=20 south, x=21 north), so calcite passes every melter again and again.
    # As a dead end it only stood still at the far end, and the melters near the splitter had to catch it in passing: line A starved.
    belt(20, 80, E)
    belt(21, 80, N)
    for y in range(79, 50, -1):
        belt(21, y, N)
    belt(21, 50, W)
    ents3.extend(ents[first:])
    del ents[first:]
    # the red line's ore belt (wheel_red.py turned half round) and the conveyor: the tiles whose calcite is counted
    ORE_PATH.extend([(-1, 5), (-1, 6), (-1, 7)] + [(-2, y) for y in range(5, 35)] + [(x, 38) for x in range(-2, 18)] + [(18, y) for y in range(38, 14, -1)]
                    + [(19, y) for y in range(15, 35)] + [(19, 38), (19, 39), (19, 44), (19, 48)] + [(x, y) for y in range(50, 80) for x in (19, 20)] + [(20, 80)] + [(21, y) for y in range(50, 81)])


def lua_pts(pts, off=0.0):
    return "{" + ",".join("{%s,%s}" % (p[0] + off, p[1] + off) for p in pts) + "}"


HEAD = "local s=game.surfaces['%s'] local hub=s.platform.hub local WI=defines.wire_connector_id local function at(t,x,y) return s.find_entities_filtered{type=t,position={x,y},radius=0.4}[1] end " % SURF


def lua_recipes():
    rec = ",".join("{%s,%s,'%s'}" % m for m in MELT + CAST)
    asm = lua_pts(ASM)
    filt = ",".join("{%s,%s,'%s'}" % f for f in FILT)
    return (HEAD + "local n,f=0,0 for _,q in pairs{%s} do local m=s.find_entities_filtered{name='foundry',position={q[1],q[2]},radius=0.6}[1] m.set_recipe(q[3]) m.direction=defines.direction.west if m.direction==defines.direction.west then n=n+1 end end "
            "for _,q in pairs(%s) do s.find_entities_filtered{name='assembling-machine-3',position=q,radius=0.6}[1].set_recipe('space-platform-foundation') n=n+1 end "
            "for _,q in pairs{%s} do local i=at('inserter',q[1],q[2]) i.use_filters=true i.inserter_filter_mode='whitelist' i.set_filter(1,q[3]) f=f+1 end "
            "local sp=s.find_entities_filtered{type='splitter',position={20,49.5},radius=0.6}[1] sp.splitter_filter={name='calcite',quality='normal'} sp.splitter_output_priority='left' "
            "rcon.print('recipes set and facing west '..n..' of %d, inserters filtered '..f..', splitter filter '..tostring(sp.splitter_filter and sp.splitter_filter.name)..' to the '..sp.splitter_output_priority)") % (rec, asm, filt, len(MELT) + len(CAST) + len(ASM))


def lua_belts():
    return (HEAD + "local prev,n,miss=nil,0,0 for _,p in pairs(%s) do local b=at('transport-belt',p[1],p[2]) if b then local bc=b.get_or_create_control_behavior() bc.read_contents=true "
            "bc.read_contents_mode=defines.control_behavior.transport_belt.content_read_mode.hold local c=b.get_wire_connector(WI.circuit_green,true) if prev then c.connect_to(prev,false) end prev=c n=n+1 else miss=miss+1 end end "
            "local d=at('decider-combinator',%s,%s) d.get_wire_connector(WI.combinator_input_green,true).connect_to(prev,false) d=at('decider-combinator',%s,%s) d.get_wire_connector(WI.combinator_input_green,true).connect_to(prev,false) "
            "rcon.print('belt tiles on the count wire '..n..', missing '..miss)") % (lua_pts(ORE_PATH, .5), DECIDERS[2][0], DECIDERS[2][1], DECIDERS[3][0], DECIDERS[3][1])


def lua_control():
    def it(n):
        return "{type='item',name='%s'}" % n
    vw, vr = "{type='virtual',name='signal-W'}", "{type='virtual',name='signal-R'}"
    red, green = "{red=true,green=false}", "{red=false,green=true}"
    d = ["at('decider-combinator',%s,%s)" % p for p in DECIDERS]
    return (HEAD + "local dw,dr,dc,du=%s,%s,%s,%s " % tuple(d) +
            "for _,x in pairs{dw,dr,dc,du} do for _,id in pairs{WI.combinator_input_red,WI.combinator_output_red,WI.combinator_output_green} do x.get_wire_connector(id,true).disconnect_all() end end "
            "local hr=hub.get_wire_connector(WI.circuit_red,true) dw.get_wire_connector(WI.combinator_input_red,true).connect_to(hr,false) dr.get_wire_connector(WI.combinator_input_red,true).connect_to(hr,false) "
            "local net=dw.get_wire_connector(WI.combinator_output_red,true) dr.get_wire_connector(WI.combinator_output_red,true).connect_to(net,false) "
            "dc.get_wire_connector(WI.combinator_input_red,true).connect_to(net,false) du.get_wire_connector(WI.combinator_input_red,true).connect_to(net,false) "
            "local fnet=dc.get_wire_connector(WI.combinator_output_green,true) du.get_wire_connector(WI.combinator_output_green,true).connect_to(fnet,false) "
            "dw.get_or_create_control_behavior().parameters={conditions={{first_signal=%s,comparator='<',constant=%d},{first_signal=%s,comparator='>',constant=%d,compare_type='and'},"
            "{first_signal=%s,comparator='>',constant=%d,compare_type='and'},{first_signal=%s,comparator='>',constant=%d,compare_type='and'}},outputs={{signal=%s,copy_count_from_input=false,constant=1}}} "
            % (it("space-platform-foundation"), FCAP, it("iron-ore"), RES_FE, it("copper-ore"), RES_CU, it("calcite"), RES_CA, vw) +
            "dr.get_or_create_control_behavior().parameters={conditions={{first_signal=%s,comparator='<',constant=%d}},outputs={{signal=%s,copy_count_from_input=false,constant=1}}} " % (it("automation-science-pack"), RED, vr) +
            "dc.get_or_create_control_behavior().parameters={conditions={{first_signal=%s,first_signal_networks=%s,comparator='>',constant=0},{first_signal=%s,first_signal_networks=%s,comparator='<',constant=%d,compare_type='and'}},"
            "outputs={{signal=%s,copy_count_from_input=false,constant=1}}} " % (vw, red, it("calcite"), green, CAL, it("calcite")) +
            "du.get_or_create_control_behavior().parameters={conditions={{first_signal=%s,first_signal_networks=%s,comparator='>=',constant=%d},{first_signal=%s,first_signal_networks=%s,comparator='>',constant=0,compare_type='and'},"
            "{first_signal=%s,first_signal_networks=%s,comparator='>=',constant=%d,compare_type='or'},{first_signal=%s,first_signal_networks=%s,comparator='>',constant=0,compare_type='and'},"
            "{first_signal=%s,first_signal_networks=%s,comparator='=',constant=0,compare_type='or'},{first_signal=%s,first_signal_networks=%s,comparator='>',constant=0,compare_type='and'}},"
            "outputs={{signal=%s,copy_count_from_input=false,constant=1}}} " % (it("calcite"), green, CAL, vw, red, it("calcite"), green, CAL, vr, red, vw, red, vr, red, it("iron-ore")) +
            "local fe,cu=at('inserter',-0.5,4.5),at('inserter',-1.5,4.5) for _,i in pairs{fe,cu} do for _,id in pairs{WI.circuit_red,WI.circuit_green} do i.get_wire_connector(id,true).disconnect_all() end end "
            "cu.get_wire_connector(WI.circuit_red,true).connect_to(net,false) local cb=cu.get_or_create_control_behavior() cb.circuit_set_filters=false cb.circuit_enable_disable=true cb.circuit_condition={first_signal={type='virtual',name='signal-anything'},comparator='>',constant=0} "
            "cu.use_filters=true cu.inserter_filter_mode='whitelist' cu.set_filter(1,'copper-ore') "
            "fe.get_wire_connector(WI.circuit_green,true).connect_to(fnet,false) cb=fe.get_or_create_control_behavior() fe.use_filters=true fe.inserter_filter_mode='whitelist' cb.circuit_set_filters=true cb.circuit_enable_disable=true "
            "cb.circuit_condition={first_signal={type='virtual',name='signal-anything'},comparator='>',constant=0} "
            "local u=0 for _,i in pairs(s.find_entities_filtered{type='inserter',area={{-1,16},{18,36}}}) do local f=i.use_filters and i.get_filter(1) if f and (f.name=='iron-ore' or f.name=='copper-ore') then "
            "local c=i.get_wire_connector(WI.circuit_red,true) c.disconnect_all() c.connect_to(net,false) local b=i.get_or_create_control_behavior() b.circuit_enable_disable=true b.circuit_condition={first_signal=%s,comparator='>',constant=0} u=u+1 end end "
            "rcon.print('deciders set, hub ore inserters rewired, red unit ore inserters gated on R: '..u..' (expect 12)')" % vr)


MODS = [("foundry", [m[:2] for m in MELT], [("productivity-module-2", "epic", 4)]),
        ("foundry", [c[:2] for c in CAST], [("productivity-module-2", "epic", 2), ("speed-module-3", "normal", 2)]),
        ("assembling-machine-3", ASM, [("speed-module-3", "normal", 4)])]


def lua_modules():
    parts = []
    for name, pts, mods in MODS:
        ml = ",".join("{'%s','%s',%d}" % m for m in mods)
        parts.append("{'%s',%s,{%s}}" % (name, lua_pts(pts), ml))
    return (HEAD + "local net=game.surfaces.nauvis.find_logistic_network_by_position({0,0},'player') local put,short,back=0,0,0 for _,g in pairs{%s} do for _,p in pairs(g[2]) do local m=s.find_entities_filtered{name=g[1],position=p,radius=0.6}[1] "
            "local inv=m.get_module_inventory() local same=true for _,q in pairs(g[3]) do if inv.get_item_count({name=q[1],quality=q[2]})~=q[3] then same=false end end if g[1]=='assembling-machine-3' and not inv.is_empty() then same=true end "
            "if not same then for _,it in pairs(inv.get_contents()) do back=back+net.insert{name=it.name,count=it.count,quality=it.quality} end inv.clear() "
            "for _,q in pairs(g[3]) do local got=net.remove_item{name=q[1],count=q[3],quality=q[2]} if got>0 then local ins=inv.insert{name=q[1],count=got,quality=q[2]} put=put+ins "
            "if ins<got then net.insert{name=q[1],count=got-ins,quality=q[2]} end end short=short+(q[3]-got) end end end end rcon.print('modules moved from the Nauvis network '..put..', handed back '..back..', short '..short)") % ",".join(parts)


STATUS = (HEAD + "local function sn(e) for n,x in pairs(defines.entity_status) do if x==e.status then return n end end return '?' end local o={} "
          "for _,m in pairs(s.find_entities_filtered{name={'foundry','assembling-machine-3'},area={{3,51},{18,82}}}) do local r=m.get_recipe() local fl={} for k,v in pairs(m.get_fluid_contents()) do fl[#fl+1]=k:sub(8)..' '..math.floor(v) end "
          "o[#o+1]=(r and r.name or 'no recipe')..' @'..m.position.x..','..m.position.y..' '..sn(m)..' made '..m.products_finished..' prod +'..math.floor(m.productivity_bonus*100)..'%% speed '..string.format('%%.1f',m.crafting_speed)..' '..table.concat(fl,',') end "
          "local inv=hub.get_inventory(defines.inventory.hub_main) local d=at('decider-combinator',%s,%s) local g=d and d.get_circuit_network(WI.combinator_input_green) local r=d and d.get_circuit_network(WI.combinator_input_red) "
          "local function sg(nw,t,n) return nw and nw.get_signal({type=t,name=n}) or -1 end local a,c=0,0 for _,e in pairs(s.find_entities_filtered{type='accumulator'}) do a=a+e.energy c=c+e.electric_buffer_size end "
          "local fe,cu=at('inserter',-0.5,4.5),at('inserter',-1.5,4.5) local cf=fe.get_filter(1) "
          "o[#o+1]='hub: foundation '..inv.get_item_count('space-platform-foundation')..', iron ore '..inv.get_item_count('iron-ore')..', copper ore '..inv.get_item_count('copper-ore')..', calcite '..inv.get_item_count('calcite')..', red packs '..inv.get_item_count('automation-science-pack')..', free slots '..inv.count_empty_stacks() "
          "o[#o+1]='signals: W '..sg(r,'virtual','signal-W')..' R '..sg(r,'virtual','signal-R')..' | on the ore belt: calcite '..sg(g,'item','calcite')..' iron ore '..sg(g,'item','iron-ore')..' copper ore '..sg(g,'item','copper-ore')..' | hub inserters: copper '..sn(cu)..', iron '..sn(fe)..' filter '..tostring(cf and cf.name) "
          "o[#o+1]='accumulators '..math.floor(a/1e6)..' of '..math.floor(c/1e6)..' MJ, providing to other platforms '..tostring(hub.providing_to_other_platforms) rcon.print(table.concat(o,' ; '))") % DECIDERS[2]

FIND_T = "local p for _,q in pairs(game.forces.player.platforms) do if q.name:find('%s',1,true) then p=q end end " % TRIANGLE
TRI = (FIND_T + "local g='foundation-works '..p.index local pt for _,q in pairs(p.hub.get_logistic_point()) do if q.mode==defines.logistic_mode.requester then pt=q end end "
       "local n=0 for i=1,#pt.sections do if n==0 and pt.sections[i].group==g then pt.remove_section(i) n=1 end end local sec=pt.add_section(g) "
       "sec.set_slot(1,{value={type='item',name='space-platform-foundation',quality='normal'},min=%d,max=%d,import_from='nauvis',request_from='platforms'}) local f=sec.get_slot(1) "
       "rcon.print(p.name..' @'..tostring(p.space_location and p.space_location.name)..': section '..g..' min '..tostring(f.min)..' max '..tostring(f.max)..' request_from '..tostring(f.request_from)..', paused '..tostring(p.paused))") % (TMIN, TMAX)
TRI_STATUS = (FIND_T + "local s=p.surface local h=p.hub local o={} for _,q in pairs(h.get_logistic_point()) do if q.mode==defines.logistic_mode.requester then for i,sc in pairs(q.sections) do for k=1,sc.filters_count do local f=sc.get_slot(k) "
              "if f and f.value then o[#o+1]='['..sc.group..'] '..f.value.name..' '..tostring(f.min)..'..'..tostring(f.max)..' from '..tostring(f.request_from) end end end end end "
              "rcon.print('triangle: tiles '..#s.find_tiles_filtered{name='space-platform-foundation'}..' ghosts '..s.count_entities_filtered{name='tile-ghost'}..' foundation aboard '..h.get_inventory(defines.inventory.hub_main).get_item_count('space-platform-foundation')..' | requests: '..table.concat(o,', '))")


def run(lua):
    return tools["run_lua"](lua).strip()


def stands():
    return run(HEAD + "rcon.print(s.count_entities_filtered{name='foundry',area={{8,52},{18,69}}})") != "0"


def place(apply, ents=ents):
    ok = bad = 0
    for i in range(0, len(ents), 400):
        r = json.loads(tools["place_entities"](json.dumps(ents[i:i + 400]), surface=SURF, dry_run=not apply, clear_trees=False))
        f = r.get("failed") or []
        ok += r.get("placed", 0)
        bad += len(f)
        if f:
            print("failed", json.dumps(f)[:1500])
    return ok, bad


def config():
    for lua in (lua_recipes(), lua_belts(), lua_control()):
        print(run(lua))


def main():
    step = sys.argv[1] if len(sys.argv) > 1 else "status"
    apply = "--apply" in sys.argv
    layout()
    if step == "check":
        cells = [(e["x"], e["y"]) for e in ents + ents2 + ents3]
        print("entities", len(ents), "+", len(ents2), "+", len(ents3), "deck tiles", len(tiles), "counted belt tiles", len(ORE_PATH), "duplicates", len(cells) - len(set(cells)))
        print("longest command", max(len(x) for x in (lua_recipes(), lua_belts(), lua_control(), lua_modules(), STATUS, TRI)))
    elif step == "build":
        if stands():
            print("the works already stands: not placing again")
            return
        if apply:
            run(HEAD + "s.request_to_generate_chunks({12,58},3) s.force_generate_chunk_requests() rcon.print('ok')")
            print("deck tiles laid", lay_foundation(tiles, SURF))
        ok, bad = place(apply)
        print("placed" if apply else "dry run", ok, "failed", bad)
        if apply and not bad:
            config()
    elif step == "expand":
        if run(HEAD + "rcon.print(s.count_entities_filtered{name='foundry',area={{8,70},{18,81}}})") != "0":
            print("lines C and D already stand: not placing again")
            return
        if apply:
            print("deck tiles laid", lay_foundation(tiles, SURF))
        ok, bad = place(apply, ents2)
        print("placed" if apply else "dry run", ok, "failed", bad)
        if apply and not bad:
            config()
            print(run(lua_modules()))
    elif step == "loop":
        if run(HEAD + "rcon.print(s.count_entities_filtered{type='transport-belt',position={21.5,60.5},radius=0.3})") != "0":
            print("the calcite loop already stands: not placing again")
            return
        ok, bad = place(apply, ents3)
        print("placed" if apply else "dry run", ok, "failed", bad)
        if apply and not bad:
            config()
    elif step == "stack":
        print(run(HEAD + "local i=at('inserter',-0.5,4.5) if i.name~='bulk-inserter' then rcon.print('already '..i.name) return end i.order_upgrade{target={name='stack-inserter',quality='epic'},force='player'} i.apply_upgrade() rcon.print('now '..at('inserter',-0.5,4.5).name)"))
        config()
    elif step == "config":
        config()
    elif step == "modules":
        print(run(lua_modules()))
    elif step == "triangle":
        print(run(TRI))
    elif step == "status":
        print(run(STATUS).replace(" ; ", "\n"))
        print(run(TRI_STATUS))


if __name__ == "__main__":
    main()
