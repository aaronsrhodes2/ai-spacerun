#!/usr/bin/env python3
"""The export product of a wheel's rocket district (the Captain, 2026-11-14: every wheel has an export role next to its own science;
Fulgora Wheel = processing units, Gleba Wheel = rocket fuel, Vulcanus Wheel = low density structure). This script sits on top of
scripts/wheel_rocket.py (read its docstring first: tap, spiral corridor, heart, counted loop) and raises one product of that district
to what the west spoke's chunks can carry. Written for and run on the Fulgora Wheel only; `--only PLANET` is there for a later
roll-out (PRODUCT below), and without it the script works on Fulgora alone.

What was wrong (found on the Fulgora Wheel, the same build stands on all four):
  1 in1 was a mixed dead end. The carbonic inserter drops on the first tile of in1 and the oxide stub turned INTO that tile (a curve,
    not a side-load), so both kinds lay on lane 1, the belt filled (1,236 carbonic and 329 oxide chunks) and each crusher intake stood
    in front of the other kind: no carbon, so no coal, no plastic, no circuits. `tap`: the oxide stub now runs south one tile and
    side-loads from the east at (-66,2) (lane 1); the carbonic inserter drops on a straight tile and lands on lane 2. A lane each.
  2 The processing unit assembler faced north (place_entities leaves machines facing north), its acid port away from the acid pipe:
    0 processing units ever made. `config` turns it (south for the old assembler, west for the electromagnetic plant).
  3 Rocket fuel took the light oil before plastic got any gas (15 solid fuel a minute against 4 plastic). `config`: the two products
    that are not the export work only while the loop holds SURPLUS of the export's last intermediate (advanced circuits >= 5 here).
  4 One assembler 3 a step: 17 processing units a minute at most. `em`: three epic electromagnetic plants above the loop instead
    (processing unit x 19..22, electronic circuit x 24..27, advanced circuit x 29..32, all y 12..15 heart-local), electronic circuits
    handed straight from plant to plant (bulk inserter at 23,13 to the processing unit plant, fast inserter at 28,13 to the advanced
    circuit plant), so they never ride the loop. Productivity 0.5 built in, five modules: about 29 processing units a minute from one
    plant, at half the material of the assembler.
  5 Loop traffic: copper cable target 120 with a second (bulk) cable inserter at 37,28; carbon 60 with a second (bulk) lift at 41,20;
    iron plate 40; processing unit 8.
Caps in the hub: the export CAP_EXPORT, the other two CAP_SIDE. The hub request for the export from the planet below (a bonus, the
wheel does not depend on it) gets its `max` lifted above the cap, or everything the wheel makes over that max goes to the hub's trash.
`hub.providing_to_other_platforms` is set, so a platform in the same orbit can ask with request_from='platforms'.

  6 One carbonic crusher (18 chunks, 167 carbon a minute) fed everything. `crusher`: a second one at 17..19,43..44, in1 one tile longer.
  7 Copper cable for circuits (400 a minute) crowded the loop's inner lane, where everything from outside the loop lands, and iron plate
    could not get on. `ec2`: a second circuit plant west of the processing unit plant with its own cable caster (see EC2_ENTS); the
    loop's cable target drops from 120 to 30 (advanced circuits only), carbon rises to 80.
  8 Water. With the old stock of oxide chunks gone, the oxide tap (it yields to the spiral) brings about 5 chunks a minute: 25 ice, 500
    water, about 12 processing units a minute. `water`: the reshuffler turns spare carbonic chunks into oxide (and metallic) ones while
    the melter is short of ice (see WATER_ENTS).
  9 The coal plant's one long-handed inserter lifted about 190 carbon a minute off a loop that carried 420 past it. `coal`: a second one at 18,25.
 10 Power (see POWER_SPOKES): `power w e --apply` lays a second row of panels along the named spokes; without --apply it counts free spots.
Steps: check | tap | em [--apply] | crusher [--apply] | ec2 [--apply] | water [--apply] | coal [--apply] | power [w n e s] [--apply] | trim | modules | config | status | rate [seconds]      [--only PLANET]
Order on a wheel: tap, em (dry run), em --apply, crusher (dry run), crusher --apply, ec2 (dry run), ec2 --apply, water (dry run), water --apply, config. `em --apply` refuses a second run. After a quality upgrade and after any
`wheel_rocket.py config`: `wheel_export_fulgora.py config` (wheel_rocket.py sets every cap back to 2,000 and its own targets).
Never run `wheel_rocket.py build` or `refit` on a wheel that has the plants: it would try to put the three assemblers back."""
import json
import sys
import time

if "--only" not in sys.argv:
    sys.argv += ["--only", "fulgora"]

import wheel_rocket as wr  # noqa: E402
from _game import tools  # noqa: E402
from _wheels import wheels  # noqa: E402

Q = {"quality": "epic"}
N, E, S, W = 0, 4, 8, 12
PRODUCT = {"fulgora": "processing-unit", "gleba": "rocket-fuel", "vulcanus": "low-density-structure", "nauvis": "processing-unit"}
SURPLUS = {"processing-unit": ("advanced-circuit", 5), "rocket-fuel": ("solid-fuel", 20), "low-density-structure": ("plastic-bar", 20)}
CAP_EXPORT, CAP_SIDE = 4000, 300
REQUEST_MIN = 300
TARGETS = dict(wr.TARGETS, **{"carbon": 80, "copper-cable": 30, "iron-plate": 40, "processing-unit": 8})
HX, HY = wr.HX, wr.HY


def hc(x, y):
    """Centre of the heart-local tile x,y in wheel coordinates."""
    return (x + HX + .5, y + HY + .5)


def ent(name, x, y, d=N, w=1):
    return {"name": name, "x": x + HX + w / 2, "y": y + HY + w / 2, "direction": d, "params": dict(Q)}


# the side products' intakes: what stops when the export is short (heart-local tiles)
SIDE_INTAKE = {"rocket-fuel": (38, 18), "low-density-structure": (30, 28), "processing-unit": (20, 16)}
EXPORT_INS = {"rocket-fuel": (41, 22), "low-density-structure": (41, 24), "processing-unit": (41, 25)}
OLD_MACH = [(21.5, 14.5), (25.5, 14.5), (29.5, 14.5)]
OLD_INS = [(20, 16), (22, 16), (24, 16), (26, 16), (28, 16), (30, 16)]
PLANTS = [(19, "processing-unit", W), (24, "electronic-circuit", N), (29, "advanced-circuit", N)]
EM_ENTS = ([ent("electromagnetic-plant", x, 12, d, 4) for x, r, d in PLANTS] + [
    ent("fast-inserter", 20, 16, S), ent("fast-inserter", 22, 16, N),                                      # advanced circuits in, processing units out
    ent("bulk-inserter", 23, 13, E),                                                                         # electronic circuits, plant to plant
    ent("bulk-inserter", 24, 16, S), ent("bulk-inserter", 25, 16, S), ent("bulk-inserter", 27, 16, S),       # iron plate, copper cable twice
    ent("fast-inserter", 28, 13, W),                                                                         # electronic circuits to the advanced circuit plant
    ent("fast-inserter", 29, 16, S), ent("fast-inserter", 31, 16, S), ent("fast-inserter", 30, 16, N),       # plastic, cable in; advanced circuits out
])
EXTRA_ENTS = [ent("bulk-inserter", 37, 28, S), ent("bulk-inserter", 41, 20, E)]
COAL_ENTS = [ent("long-handed-inserter", 18, 25, S)]                                                          # second carbon intake of the coal plant
COAL_FILTERS = [(18, 25, ["carbon"])]                              # second cable out, second carbon lift
EM_FILTERS = [(20, 16, ["advanced-circuit", "electronic-circuit"]), (24, 16, ["iron-plate"]), (25, 16, ["copper-cable"]), (27, 16, ["copper-cable"]), (29, 16, ["plastic-bar"]),
              (31, 16, ["copper-cable"]), (22, 16, ["processing-unit"]), (30, 16, ["advanced-circuit"]), (23, 13, ["electronic-circuit"]), (28, 13, ["electronic-circuit"]),
              (37, 28, ["copper-cable"]), (41, 20, ["carbon"])]
EM_GATES = [(37, 28, "copper-cable"), (41, 20, "carbon"), (22, 16, "processing-unit"), (30, 16, "advanced-circuit")]
# a second carbonic crusher east of the first four: in1 grows one tile (17,46), intake at 17,45, products onto the ore belt from 19,42
CRUSHER = (17, 43)
CRUSH_ENTS = [{"name": "crusher", "x": CRUSHER[0] + HX + 1.5, "y": CRUSHER[1] + HY + 1, "direction": E, "params": dict(Q)},
              ent("fast-inserter", 17, 45, S), ent("fast-inserter", 19, 42, S), ent("express-transport-belt", 17, 46, E)]
# a second electronic circuit plant west of the processing unit plant with its own cable caster, so cable for circuits never rides the loop:
# caster 8..12,12..16 -> bulk inserter 13,14 -> plant 14..17,12..15 -> bulk inserter 18,13 -> processing unit plant; iron plate off the loop at 16,16;
# molten copper from the pipe row (31,34) by an underground pair (30,34 -> 20,34, under the molten iron pipes), west along y 34, north up x 14, in at 11,17
EC2_PIPES = [(x, 34) for x in range(14, 20)] + [(14, y) for y in range(18, 34)] + [(13, 18), (12, 18), (11, 18), (11, 17)]
EC2_ENTS = ([ent("foundry", 8, 12, N, 5), ent("electromagnetic-plant", 14, 12, N, 4), ent("bulk-inserter", 13, 14, W), ent("bulk-inserter", 18, 13, W), ent("bulk-inserter", 16, 16, S),
             ent("pipe-to-ground", 30, 34, E), ent("pipe-to-ground", 20, 34, W)] + [ent("pipe", x, y) for x, y in EC2_PIPES])
EC2_REC = [(8 + HX + 2.5, 12 + HY + 2.5, "casting-copper-cable", N, "foundry"), (14 + HX + 2, 12 + HY + 2, "electronic-circuit", N, "electromagnetic-plant")]
EC2_FILTERS = [(13, 14, ["copper-cable"]), (18, 13, ["electronic-circuit"]), (16, 16, ["iron-plate"])]
# water: the reshuffler (5..7,43..44) reprocesses CARBONIC chunks, the kind the west spoke has to spare, instead of metallic ones:
# intake 6,45 from in1 (the long-handed one at 5,45 that reached in2 is gone), oxide chunks straight into the oxide crusher (8,43, as before),
# carbonic ones into the first carbonic crusher (4,43, as before) or back onto in1 at 5,45, ONE TILE UPSTREAM of the intake (in1 stands
# full: downstream of the intake the returned chunk found no gap and the reshuffler stopped at full output; upstream, every chunk the
# intake lifts opens the gap), metallic ones onto in2 (long-handed, 7,45);
# the old relief inserter at 6,42 (chunks onto the ore belt and so into the hub, a slot each) is given a filter that never matches
WATER_ENTS = [ent("fast-inserter", 5, 45, N), ent("fast-inserter", 6, 45, S), ent("long-handed-inserter", 7, 45, N),
              {"name": "decider-combinator", "x": 8 + HX, "y": 48.5 + HY, "direction": E, "params": dict(Q)}]
# the reshuffler's metallic chunks are now ALL the metal the district gets: the spoke's metallic tap is shut (its chunks stood packed on
# in2 and the by-product found no gap: reshuffler at full output, no oxide, no water, everything stopped) and the metallic crusher takes
# whatever in2 brings (ore the melters do not want rides out to the hub). So the reshuffler has two reasons to run, joined by the decider
# at 7..8,48: the melter holds fewer than 20 ice (green wire) OR the copper melter holds fewer than 30 copper ore (red wire).
WATER_FILTERS = [(5, 45, ["carbonic-asteroid-chunk"]), (6, 45, ["carbonic-asteroid-chunk"]), (7, 45, ["metallic-asteroid-chunk"]), (6, 42, ["carbon"])]
WATERCLEAR = ("local s=game.surfaces['SURF'] local hub=s.platform.hub local n=0 for _,e in pairs(s.find_entities_filtered{name='long-handed-inserter',position={IX,IY},radius=0.3}) do "
              "if e.held_stack.valid_for_read then hub.insert(e.held_stack) e.held_stack.clear() end e.destroy() n=n+1 end rcon.print('long-handed intake of the reshuffler removed '..n)")
# the first carbonic crusher now only takes the reshuffler's returned chunks and its pace sets the reshuffler's: it gets the metallic crusher's
# two speed modules, the metallic crusher (a few chunks a minute now) gets its two productivity modules
MODSWAP = ("local s=game.surfaces['SURF'] local a=s.find_entities_filtered{name='crusher',position={AX,AY},radius=0.5}[1] local b=s.find_entities_filtered{name='crusher',position={BX,BY},radius=0.5}[1] "
           "local ma,mb=a.get_module_inventory(),b.get_module_inventory() if not (ma[1].valid_for_read and mb[1].valid_for_read and ma[1].name:find('productivity',1,true) and mb[1].name:find('speed',1,true)) then rcon.print('modules: nothing to swap') return end "
           "local n=0 for k=1,math.min(#ma,#mb) do if ma[k].valid_for_read and mb[k].valid_for_read then ma[k].swap_stack(mb[k]) n=n+1 end end rcon.print('modules swapped between the first carbonic crusher and the metallic crusher: '..n..' pairs; speeds now '..a.crafting_speed..' and '..b.crafting_speed)")
CRUSH_FILTERS = [(17, 45, ["carbonic-asteroid-chunk"])]
CRUSH_GATES = [(17, 45, "carbon")]

# power: the plants and casters draw about 30 MW at full pace and the accumulators fell from 98% to 18% in ten game minutes. A second row of
# panels on the free deck strip between the spoke belt and the first row (W spoke: tiles y -6..-4, x -583..-130), spoke by spoke
POWER_SPOKES = {"w": lambda x: (x, -4.5), "n": lambda x: (4.5, x), "e": lambda x: (-x, 4.5), "s": lambda x: (-4.5, -x)}


def power_ents(spokes):
    return [{"name": "solar-panel", "x": POWER_SPOKES[k](x + .5)[0], "y": POWER_SPOKES[k](x + .5)[1], "params": dict(Q)} for k in spokes for x in range(-583, -130, 3)]


POWER = ("local s=game.surfaces['SURF'] local acc=s.find_entities_filtered{type='accumulator'} local e,cap=0,0 for _,a in pairs(acc) do e=e+a.energy cap=cap+a.electric_buffer_size end "
         "rcon.print(string.format('solar panels %d, accumulators %d holding %.0f of %.0f MJ (%.0f%%)',s.count_entities_filtered{type='solar-panel'},#acc,e/1e6,cap/1e6,100*e/cap))")
AT = "local function at(t,x,y) return s.find_entities_filtered{type=t,position={x,y},radius=0.3}[1] end "
HAS_EM = "local s=game.surfaces['SURF'] rcon.print(s.count_entities_filtered{name='electromagnetic-plant',position={PX,PY},radius=0.5})"
TAP = ("local s=game.surfaces['SURF'] local hub=s.platform.hub " + AT + "local stub=at('transport-belt',-64.5,1.5) local nb=at('transport-belt',-64.5,2.5) if not stub or not nb then rcon.print('tap: stub or new belt missing') return end "
       "stub.direction=defines.direction.south nb.direction=defines.direction.west local moved,tohub=0,0 for _,p in pairs(PATH) do local e=at('transport-belt',p[1]+0.5,p[2]+0.5) if e then "
       "local a,b=e.get_transport_line(1),e.get_transport_line(2) local n=a.get_item_count('carbonic-asteroid-chunk') if n>0 then a.remove_item{name='carbonic-asteroid-chunk',count=n} "
       "for k=1,n do local ok=false for _,q in pairs{0.1,0.35,0.6,0.85} do if not ok and b.can_insert_at(q) then ok=b.insert_at(q,{name='carbonic-asteroid-chunk',count=1}) end end "
       "if ok then moved=moved+1 else tohub=tohub+hub.insert{name='carbonic-asteroid-chunk',count=1} end end end "
       "local m=b.get_item_count('oxide-asteroid-chunk') if m>0 then b.remove_item{name='oxide-asteroid-chunk',count=m} tohub=tohub+hub.insert{name='oxide-asteroid-chunk',count=m} end end end "
       "rcon.print('tap: oxide stub south then west onto in1 from the east; carbonic chunks moved from lane 1 to lane 2: '..moved..', to the hub: '..tohub)")
EMCLEAR = ("local s=game.surfaces['SURF'] local hub=s.platform.hub local n,m=0,0 local function empty(e) for i=1,e.get_max_inventory_index() do local inv=e.get_inventory(i) if inv then for _,it in pairs(inv.get_contents()) do m=m+hub.insert{name=it.name,count=it.count,quality=it.quality} end inv.clear() end end end "
           "for _,p in pairs(MACH) do for _,e in pairs(s.find_entities_filtered{name='assembling-machine-3',position=p,radius=0.3}) do empty(e) e.destroy() n=n+1 end end "
           "for _,p in pairs(INS) do for _,e in pairs(s.find_entities_filtered{name='fast-inserter',position=p,radius=0.3}) do if e.held_stack.valid_for_read then m=m+hub.insert(e.held_stack) e.held_stack.clear() end e.destroy() n=n+1 end end "
           "rcon.print('old assemblers and inserters removed '..n..', items handed to the hub '..m)")
MODULES = ("local s=game.surfaces['SURF'] local hub=s.platform.hub local inv=hub.get_inventory(defines.inventory.hub_main) local fromhub,fromnet,short=0,0,0 local mod={name='productivity-module-2',quality='epic'} "
           "for _,e in pairs(s.find_entities_filtered{name={'electromagnetic-plant','crusher'},area={{MODA,MODB},{MODC,MODD}}}) do local mi=e.get_module_inventory() for k=1,#mi do if not mi[k].valid_for_read then local got=false "
           "if inv.get_item_count(mod)>0 then inv.remove{name=mod.name,quality=mod.quality,count=1} got=true fromhub=fromhub+1 else for _,net in pairs(game.forces.player.logistic_networks['nauvis'] or {}) do "
           "if not got and net.get_item_count(mod)>0 and net.remove_item{name=mod.name,quality=mod.quality,count=1}>0 then got=true fromnet=fromnet+1 end end end "
           "if got then mi[k].set_stack{name=mod.name,quality=mod.quality,count=1} else short=short+1 end end end end "
           "rcon.print('epic productivity module 2 fitted: '..fromhub..' from the hub (out of the old assemblers), '..fromnet..' from the Nauvis network, slots still empty '..short)")
CONFIG = ("local s=game.surfaces['SURF'] local hub=s.platform.hub local W=defines.wire_connector_id local o={} " + AT +
          "local lb=at('transport-belt',LBX,LBY) local function cond(i,sig,cmp,k,target) if not i then return 0 end local c=i.get_wire_connector(W.circuit_red,true) c.disconnect_all() c.connect_to(target.get_wire_connector(W.circuit_red,true),false) "
          "local cb=i.get_or_create_control_behavior() cb.circuit_enable_disable=true cb.circuit_condition={first_signal={type='item',name=sig},comparator=cmp,constant=k} return 1 end "
          "local nf=0 for _,q in pairs(FILT) do local i=at('inserter',q[1],q[2]) if i then i.use_filters=true i.inserter_filter_mode='whitelist' for k=1,i.filter_slot_count do i.set_filter(k,q[3][k]) end nf=nf+1 end end "
          "local nr=0 for _,q in pairs(REC) do local m=s.find_entities_filtered{name=q[5],position={q[1],q[2]},radius=0.5}[1] if m then if not m.get_recipe() or m.get_recipe().name~=q[3] then for _,st in pairs(m.set_recipe(q[3])) do hub.insert(st) end end m.direction=q[4] nr=nr+1 end end "
          "local cr=s.find_entities_filtered{name='crusher',position={CRX,CRY},radius=0.5}[1] if cr then if not cr.get_recipe() then cr.set_recipe('advanced-carbonic-asteroid-crushing') end cr.direction=defines.direction.east o[#o+1]='second carbonic crusher set' end "
          "local rp=s.find_entities_filtered{name='crusher',position={RPX,RPY},radius=0.5}[1] local ri=at('inserter',RIX,RIY) local rr=at('inserter',RIX-1,RIY) if rp and ri and rr then ri.direction=defines.direction.south rr.direction=defines.direction.north rr.get_wire_connector(W.circuit_green,true).disconnect_all() rr.get_or_create_control_behavior().circuit_enable_disable=false "
          "if not rp.get_recipe() or rp.get_recipe().name~='carbonic-asteroid-reprocessing' then for _,st in pairs(rp.set_recipe('carbonic-asteroid-reprocessing')) do hub.insert(st) end end "
          "local melt=s.find_entities_filtered{type='assembling-machine',position={WMX,WMY},radius=0.5}[1] melt.get_or_create_control_behavior().circuit_read_contents=true local c=ri.get_wire_connector(W.circuit_green,true) c.disconnect_all() c.connect_to(melt.get_wire_connector(W.circuit_green,true),false) "
          "local dc=s.find_entities_filtered{name='decider-combinator',position={DCX,DCY},radius=0.6}[1] local cu=s.find_entities_filtered{name='foundry',position={CMX,CMY},radius=0.6}[1] cu.get_or_create_control_behavior().circuit_read_contents=true "
          "for _,id in pairs{W.combinator_input_red,W.combinator_input_green,W.combinator_output_red,W.combinator_output_green} do dc.get_wire_connector(id,true).disconnect_all() end "
          "dc.get_wire_connector(W.combinator_input_green,true).connect_to(melt.get_wire_connector(W.circuit_green,true),false) dc.get_wire_connector(W.combinator_input_red,true).connect_to(cu.get_wire_connector(W.circuit_red,true),false) "
          "dc.get_or_create_control_behavior().parameters={conditions={{first_signal={type='item',name='ice'},first_signal_networks={red=false,green=true},comparator='<',constant=20},"
          "{first_signal={type='item',name='copper-ore'},first_signal_networks={red=true,green=false},comparator='<',constant=30,compare_type='or'}},outputs={{signal={type='virtual',name='signal-A'},copy_count_from_input=false,constant=1}}} "
          "c.disconnect_all() local cr2=ri.get_wire_connector(W.circuit_red,true) cr2.disconnect_all() cr2.connect_to(dc.get_wire_connector(W.combinator_output_red,true),false) "
          "local cb=ri.get_or_create_control_behavior() cb.circuit_enable_disable=true cb.circuit_condition={first_signal={type='virtual',name='signal-A'},comparator='>',constant=0} "
          "local mi=at('inserter',MIX,MIY) if mi then mi.get_or_create_control_behavior().circuit_enable_disable=false end "
          "local tap=at('inserter',-66.5,0.5) if tap then local tb=tap.get_or_create_control_behavior() tb.circuit_enable_disable=true tb.circuit_condition={first_signal={type='item',name='metallic-asteroid-chunk'},comparator='>',constant=1000000} end "
          "o[#o+1]='reshuffler on carbonic chunks while ice or copper ore is short; metallic tap shut, metallic crusher ungated' end "
          "local old=s.find_entities_filtered{name='assembling-machine-3',position={OPX,OPY},radius=0.3}[1] if old then old.direction=defines.direction.south o[#o+1]='old processing unit assembler turned south' end "
          "local g=0 for _,q in pairs(GATED) do g=g+cond(at('inserter',q[1],q[2]),q[3],'<',q[4],lb) end local sd=0 for _,q in pairs(SIDE) do sd=sd+cond(at('inserter',q[1],q[2]),q[3],'>=',q[4],lb) end "
          "local x=0 for _,q in pairs(CAPS) do x=x+cond(at('inserter',q[1],q[2]),q[3],'<',q[4],hub) end hub.providing_to_other_platforms=true "
          "local rq={} for _,sec in pairs(hub.get_logistic_sections().sections) do for k=1,sec.filters_count do local f=sec.get_slot(k) if f and f.value and f.value.name=='EXPORT' and (f.max or f.min<RMIN) then "
          "local was=f.min..'-'..tostring(f.max) f.min=math.max(f.min,RMIN) f.max=nil sec.set_slot(k,f) local r=sec.get_slot(k) rq[#rq+1]=(sec.group or '')..' '..was..' -> '..r.min..'-'..tostring(r.max) end end end "
          "rcon.print('filters '..nf..', plants '..nr..', loop gates '..g..', side products gated on the export '..sd..', hub caps '..x..', providing '..tostring(hub.providing_to_other_platforms)..', requests changed ['..table.concat(rq,'; ')..'] '..table.concat(o,', '))")
STATUS = ("local s=game.surfaces['SURF'] local hub=s.platform.hub local inv=hub.get_inventory(defines.inventory.hub_main) local tr=hub.get_inventory(defines.inventory.hub_trash) local f=game.forces.player.get_item_production_statistics(s) local o={} "
          "local function sn(e) for n,x in pairs(defines.entity_status) do if x==e.status then return n end end return '?' end "
          "for _,n in pairs{'processing-unit','rocket-fuel','low-density-structure','advanced-circuit','electronic-circuit','plastic-bar','coal'} do local t={} for _,p in pairs{'one_minute','ten_minutes','one_hour'} do t[#t+1]=string.format('%.1f',f.get_flow_count{name=n,category='input',precision_index=defines.flow_precision_index[p]}) end "
          "o[#o+1]=n..' made a minute (1 min / 10 min / 1 h) '..table.concat(t,' / ')..', hub '..inv.get_item_count(n)..', trash '..(tr and tr.get_item_count(n) or 0) end "
          "for _,c in pairs(s.find_entities_filtered{type='assembling-machine',area={{X0,Y0},{X1,Y1}}}) do local rc=c.get_recipe() o[#o+1]=string.format('  %-36s %-22s %s made %d',rc and rc.name or 'none',c.name,sn(c),c.products_finished) end "
          "local rq={} for _,sec in pairs(hub.get_logistic_sections().sections) do for k=1,sec.filters_count do local q=sec.get_slot(k) if q and q.value and q.value.name=='EXPORT' then rq[#rq+1]='['..(sec.group or '')..'] '..q.min..'-'..tostring(q.max) end end end "
          "o[#o+1]='hub requests for EXPORT: '..table.concat(rq,'; ')..' | providing to other platforms '..tostring(hub.providing_to_other_platforms)..' | hub carbon '..inv.get_item_count('carbon')..', free slots '..inv.count_empty_stacks() rcon.print(table.concat(o,'\\n'))")
LOOP = ("local s=game.surfaces['SURF'] local b={} for _,p in pairs(RING) do local e=s.find_entities_filtered{type='transport-belt',position={p[1]+0.5,p[2]+0.5},radius=0.3}[1] if e then for l=1,2 do for _,it in pairs(e.get_transport_line(l).get_contents()) do "
        "local k=it.name..' L'..l b[k]=(b[k] or 0)+it.count end end end end local q={} for k,v in pairs(b) do q[#q+1]=k..' '..v end table.sort(q) rcon.print('on the loop: '..table.concat(q,', '))")
TRIM = ("local s=game.surfaces['SURF'] local hub=s.platform.hub local have={} local lines={} for _,p in pairs(RING) do local e=s.find_entities_filtered{type='transport-belt',position={p[1]+0.5,p[2]+0.5},radius=0.3}[1] if e then for l=1,2 do "
        "local tl=e.get_transport_line(l) lines[#lines+1]=tl for _,it in pairs(tl.get_contents()) do have[it.name]=(have[it.name] or 0)+it.count end end end end local o={} "
        "for name,k in pairs(TGT) do local over=(have[name] or 0)-k if over>0 then local took=0 for _,tl in pairs(lines) do local c=math.min(over-took,tl.get_item_count(name)) if c>0 then took=took+tl.remove_item{name=name,count=c} end end if took>0 then "
        "hub.insert{name=name,count=took} o[#o+1]=name..' '..took end end end rcon.print('loop trimmed to its targets, handed to the hub: '..table.concat(o,', '))")
RATE = ("local s=game.surfaces['SURF'] local o={game.tick,s.platform.hub.get_inventory(defines.inventory.hub_main).get_item_count('EXPORT')} for _,c in pairs(s.find_entities_filtered{type='assembling-machine',area={{X0,Y0},{X1,Y1}}}) do local rc=c.get_recipe() "
        "local k='?' for n,x in pairs(defines.entity_status) do if x==c.status then k=n end end o[#o+1]=string.format('%.1f,%.1f|%s|%d|%s|%.2f',c.position.x,c.position.y,rc and rc.name or 'none',c.products_finished,k,1+c.productivity_bonus) end rcon.print(table.concat(o,';'))")


def lua_rows(rows):
    def v(x):
        if isinstance(x, str):
            return "'%s'" % x
        if isinstance(x, list):
            return "{" + ",".join("'%s'" % f for f in x) + "}"
        return str(x)
    return "{" + ",".join("{" + ",".join(v(x) for x in r) + "}" for r in rows) + "}"


def run(code, surface, **kw):
    code = code.replace("SURF", surface).replace("X0", str(HX - 3)).replace("Y0", str(HY + 10)).replace("X1", str(HX + 48)).replace("Y1", str(HY + 49))
    for k, val in kw.items():
        code = code.replace(k, str(val))
    return tools["run_lua"](code).strip()


def place(ents, surface, apply):
    r = json.loads(tools["place_entities"](json.dumps(ents), surface=surface, dry_run=not apply))
    return "%s %s, failed %s" % ("placed" if apply else "dry run", r.get("placed"), json.dumps(r.get("failed") or {})[:400])


def has_em(surface):
    px, py = PLANTS[0][0] + HX + 2, 12 + HY + 2
    return run(HAS_EM, surface, PX=px, PY=py) != "0"


def config(surface, export):
    em = has_em(surface)
    gated = [(x, y, item, TARGETS[item]) for x, y, item, t in wr.gated] + [hc(x, y) + (item, TARGETS[item]) for x, y, item in CRUSH_GATES]
    filt = [hc(x, y) + (names,) for x, y, names in CRUSH_FILTERS + COAL_FILTERS]
    water = run(HAS_EM.replace("name='electromagnetic-plant'", "name='fast-inserter'"), surface, PX=hc(6, 45)[0], PY=hc(6, 45)[1]) != "0"
    if water:
        filt += [hc(x, y) + (names,) for x, y, names in WATER_FILTERS]
    rec = []
    if em:
        gated += [hc(x, y) + (item, TARGETS[item]) for x, y, item in EM_GATES]
        filt += [hc(x, y) + (names,) for x, y, names in EM_FILTERS]
        rec = [(x + HX + 2, 12 + HY + 2, r, d, "electromagnetic-plant") for x, r, d in PLANTS] + EC2_REC
        filt += [hc(x, y) + (names,) for x, y, names in EC2_FILTERS]
    sig, k = SURPLUS[export]
    side = [hc(*SIDE_INTAKE[p]) + (sig, k) for p in wr.PRODUCTS if p != export]
    caps = [hc(*EXPORT_INS[p]) + (p, CAP_EXPORT if p == export else CAP_SIDE) for p in wr.PRODUCTS]
    # the first carbonic crusher's belt intake follows the loop's carbon; with the reshuffler on carbonic chunks it is shut (carbon < 0), so
    # that crusher is free for the chunks the reshuffler hands back (two in five crafts): they were what held the reshuffler at full output
    gated.append(hc(1, 45) + ("carbon", 0 if water else TARGETS["carbon"]))
    lb = hc(*[(t[0] - HX, t[1] - HY) for t in wr.loop_tiles][0])
    return run(CONFIG, surface, FILT=lua_rows(filt), REC=lua_rows(rec), GATED=lua_rows(gated), SIDE=lua_rows(side), CAPS=lua_rows(caps),
               LBX=lb[0], LBY=lb[1], RPX=HX + 6.5, RPY=HY + 44, RIX=hc(6, 45)[0], RIY=hc(6, 45)[1], WMX=HX + 45.5, WMY=HY + 27.5, DCX=8 + HX, DCY=48.5 + HY, CMX=HX + 34.5, CMY=HY + 37.5, MIX=hc(13, 45)[0], MIY=hc(13, 45)[1], CRX=CRUSH_ENTS[0]["x"], CRY=CRUSH_ENTS[0]["y"], OPX=OLD_MACH[0][0] + HX, OPY=OLD_MACH[0][1] + HY, EXPORT=export, RMIN=REQUEST_MIN)


def rate(surface, export, secs):
    def snap():
        p = run(RATE, surface, EXPORT=export).split(";")
        return int(p[0]), int(p[1]), {q.split("|")[0]: q.split("|")[1:] for q in p[2:]}
    t0, h0, a = snap()
    hist = {}
    n = max(1, secs // 6)
    for i in range(n):
        time.sleep(secs / n)
        t1, h1, b = snap()
        for key, val in b.items():
            hist.setdefault(key, {})
            hist[key][val[2]] = hist[key].get(val[2], 0) + 1
    mins = (t1 - t0) / 3600.0
    print("window %.2f game minutes; %s in the hub %d -> %d (%+.1f a minute)" % (mins, export, h0, h1, (h1 - h0) / mins))
    for key in sorted(b, key=lambda q: b[q][0]):
        if key in a:
            d = int(b[key][1]) - int(a[key][1])
            print("  %-36s %6.1f crafts a minute (x%s products)  %s" % (b[key][0], d / mins, b[key][3], ", ".join("%s %d%%" % (st, 100 * c // n) for st, c in sorted(hist[key].items(), key=lambda q: -q[1]))))


def main():
    step = sys.argv[1]
    apply = "--apply" in sys.argv
    wr.layout()
    for name, planet, surface, turrets in wheels():
        print("==", name, surface or "(not created)")
        if not surface:
            continue
        export = PRODUCT[planet]
        if step == "check":
            print("export", export, "| plants standing", has_em(surface))
            print(place(EM_ENTS + EXTRA_ENTS, surface, False))
        elif step == "tap":
            print(place([{"name": "express-transport-belt", "x": -64.5, "y": 2.5, "direction": W, "params": dict(Q)}], surface, True))
            print(run(TAP, surface, PATH="{" + ",".join("{%d,%d}" % t for t in wr.poly(wr.IN1)) + "}"))
        elif step == "em":
            if has_em(surface):
                print("the plants already stand here: nothing done (run config)")
                continue
            if not apply:
                print("dry run: would remove 3 assemblers and 6 inserters above the loop (contents to the hub) and place", len(EM_ENTS + EXTRA_ENTS), "pieces")
                print(place(EXTRA_ENTS, surface, False))
                continue
            print(tools["save_game"]("before-wheel-export-%s" % planet))
            print(run(EMCLEAR, surface, MACH=lua_rows([(x + HX, y + HY) for x, y in OLD_MACH]), INS=lua_rows([hc(x, y) for x, y in OLD_INS])))
            print(place(EM_ENTS + EXTRA_ENTS, surface, True))
            print(config(surface, export))
            print(run(MODULES, surface, MODA=HX + 17, MODB=HY + 12, MODC=HX + 33, MODD=HY + 16))
        elif step == "crusher":
            if run(HAS_EM.replace("electromagnetic-plant", "crusher"), surface, PX=CRUSH_ENTS[0]["x"], PY=CRUSH_ENTS[0]["y"]) != "0":
                print("the second carbonic crusher already stands here: nothing done (run config)")
                continue
            print(place(CRUSH_ENTS, surface, apply))
            if apply:
                print(config(surface, export))
                print(run(MODULES, surface, MODA=HX + 17, MODB=HY + 43, MODC=HX + 20, MODD=HY + 45))
        elif step == "ec2":
            if run(HAS_EM, surface, PX=EC2_REC[1][0], PY=EC2_REC[1][1]) != "0":
                print("the second circuit plant already stands here: nothing done (run config)")
                continue
            print(place(EC2_ENTS, surface, apply))
            if apply:
                print(config(surface, export))
        elif step == "water":
            if run(HAS_EM.replace("name='electromagnetic-plant'", "name='fast-inserter'"), surface, PX=hc(6, 45)[0], PY=hc(6, 45)[1]) != "0":
                print("the reshuffler already runs on carbonic chunks here: nothing done (run config)")
                continue
            if not apply:
                print("dry run: would swap the reshuffler's long-handed intake for a fast inserter and add two return inserters")
                print(place(WATER_ENTS[1:], surface, False))
                continue
            print(run(WATERCLEAR, surface, IX=hc(5, 45)[0], IY=hc(5, 45)[1]))
            print(place(WATER_ENTS, surface, True))
            print(config(surface, export))
            print(run(MODSWAP, surface, AX=HX + 2.5, AY=HY + 44, BX=HX + 14.5, BY=HY + 44))
        elif step == "decider":                                                     # one-off for a wheel that got `water` before the decider existed
            print(place(WATER_ENTS[3:], surface, apply))
            if apply:
                print(config(surface, export))
        elif step == "power":
            spokes = [k for k in sys.argv[2:] if k in POWER_SPOKES] or ["w"]
            ents = power_ents(spokes)
            r = json.loads(tools["place_entities"](json.dumps(ents), surface=surface, dry_run=True))
            bad = {f["i"] for f in (r.get("failed") or [])}
            ok = [e for i, e in enumerate(ents, 1) if i not in bad]
            print("spokes", spokes, "panels planned", len(ents), "free spots", len(ok))
            if apply:
                print(place(ok, surface, True))
            print(run(POWER, surface))
        elif step == "modswap":
            print(run(MODSWAP, surface, AX=HX + 2.5, AY=HY + 44, BX=HX + 14.5, BY=HY + 44))
        elif step == "coal":
            print(place(COAL_ENTS, surface, apply))
            if apply:
                print(config(surface, export))
        elif step == "modules":
            print(run(MODULES, surface, MODA=HX + 17, MODB=HY + 12, MODC=HX + 33, MODD=HY + 16))
            print(run(MODULES, surface, MODA=HX + 17, MODB=HY + 43, MODC=HX + 20, MODD=HY + 45))
        elif step == "config":
            print(config(surface, export))
        elif step == "trim":
            print(run(TRIM, surface, RING=lua_rows(wr.loop_tiles), TGT="{" + ",".join("['%s']=%d" % kv for kv in TARGETS.items()) + ",['electronic-circuit']=0}"))
        elif step == "status":
            print(run(STATUS, surface, EXPORT=export))
            print(run(LOOP, surface, RING=lua_rows(wr.loop_tiles)))
        elif step == "rate":
            secs = [int(a) for a in sys.argv[2:] if a.isdigit()]
            rate(surface, export, secs[0] if secs else 60)


if __name__ == "__main__":
    main()
