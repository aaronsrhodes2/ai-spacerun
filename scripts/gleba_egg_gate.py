#!/usr/bin/env python3
"""Gleba: starved chambers must not take eggs (2026-11-13, after the 60-minute fruit cut: 161 hatchlings killed by the turrets because the
second keeper pair and the production chambers kept taking eggs off the belt with no nutrients to use them).
A decider combinator (95.5,20) reads the red network (egg sensor at the egg belt's tail, plus six nutrient belt tiles at x 100..105, y 11.5)
and puts out signal A only while eggs at the tail = 0 AND nutrients on those tiles > 10. The six belt egg inserters now work on A > 0 (green).
Also: revives ghosts in the core (free rebuild, friendly build mode) and moves 200 repair packs from Nauvis stock for the robots.
Usage: gleba_egg_gate.py [--apply]"""
import json
import sys

from _game import tools

LUA = ("local s=game.surfaces.gleba local f=game.forces.player local W=defines.wire_connector_id local function at(t,x,y) return s.find_entities_filtered{type=t,position={x,y},radius=0.4}[1] end "
       "local d=at('decider-combinator',95.5,20) local cb=d.get_or_create_control_behavior() "
       "cb.parameters={conditions={{first_signal={type='item',name='pentapod-egg'},comparator='=',constant=0},{first_signal={type='item',name='nutrients'},comparator='>',constant=10,compare_type='and'}},"
       "outputs={{signal={type='virtual',name='signal-A'},copy_count_from_input=false,constant=1}}} "
       "local ins={} for _,x in pairs{92.5,96.5,100.5,104.5,108.5,112.5} do local i=at('inserter',x,16.5) local ib=i.get_or_create_control_behavior() ib.circuit_enable_disable=true "
       "ib.circuit_condition={first_signal={type='virtual',name='signal-A'},comparator='>',constant=0} ins[#ins+1]=i end "
       "local ok=0 local function link(a,ca,b,cbn) local x,y=a.get_wire_connector(ca,true),b.get_wire_connector(cbn,true) if x.is_connected_to(y) or x.connect_to(y,false) then ok=ok+1 end end "
       "link(d,W.combinator_input_red,ins[2],W.circuit_red) link(d,W.combinator_output_green,ins[2],W.circuit_green) for k=2,#ins do link(ins[k-1],W.circuit_green,ins[k],W.circuit_green) end "
       "local prev=ins[3] for x=100.5,105.5 do local b=at('transport-belt',x,11.5) local bb=b.get_or_create_control_behavior() bb.read_contents=true bb.read_contents_mode=defines.control_behavior.transport_belt.content_read_mode.hold bb.circuit_enable_disable=false "
       "link(prev,W.circuit_red,b,W.circuit_red) prev=b end "
       "local g=0 for _,e in pairs(s.find_entities_filtered{type='entity-ghost',force=f}) do if e.revive() then g=g+1 end end "
       "local nb,bn=nil,0 for _,net in pairs(f.logistic_networks.nauvis or {}) do if net.all_logistic_robots>bn then nb=net bn=net.all_logistic_robots end end "
       "local yard=at('logistic-container',2.5,2.5) local have=s.find_logistic_network_by_position({2.5,2.5},f).get_item_count('repair-pack') local moved=0 if have<100 then moved=nb.remove_item{name='repair-pack',count=200} if moved>0 then yard.insert{name='repair-pack',count=moved} end end "
       "rcon.print('wires '..ok..', ghosts revived '..g..', repair packs moved from Nauvis '..moved)")
apply = "--apply" in sys.argv
print(tools["place_entities"](json.dumps([{"name": "decider-combinator", "x": 95.5, "y": 20, "direction": 0, "params": {"quality": "rare"}}]), surface="gleba", dry_run=not apply)[:200])
if apply:
    print(tools["run_lua"](LUA))
