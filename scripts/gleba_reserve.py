#!/usr/bin/env python3
"""Gleba keeper life support, built from the rot (2026-11-12, after the fruit-cut test).
Test: with all fruit cut the nutrient belt was empty in 3 minutes and every egg chamber stopped; eggs hatch after 15, so an outage much
over 10 minutes would end the egg line. Spoilage never spoils, so it is the reserve:
  * inserter (73.5,1.5) takes spoilage off the junk belt into a red chest (73.5,0.5); the rest still goes to the burner
  * robots carry it to a blue chest (130.5,10.5) asking for 9,600
  * an electric assembler (127.5,10.5) turns it into nutrients (about 48 a minute) and puts them on the nutrient belt at the turn, right
    before the keeper pair. Its feed inserter works only while six tiles of the nutrient belt before the turn are empty (red wire), i.e.
    only in an outage. 9,600 spoilage is about 20 more minutes; raise the request or add chests for more.
Usage: gleba_reserve.py [--apply]"""
import json
import sys

from _game import tools

R = {"quality": "rare"}
E = [{"name": "assembling-machine-3", "x": 127.5, "y": 10.5, "recipe": "nutrients-from-spoilage"},
     {"name": "bulk-inserter", "x": 125.5, "y": 10.5, "direction": 4}, {"name": "bulk-inserter", "x": 129.5, "y": 10.5, "direction": 4},
     {"name": "requester-chest", "x": 130.5, "y": 10.5},
     {"name": "bulk-inserter", "x": 73.5, "y": 1.5, "direction": 8}, {"name": "passive-provider-chest", "x": 73.5, "y": 0.5},
     # the egg belt's tail carries most of the rot (about 150 a minute): a second catch there
     {"name": "bulk-inserter", "x": 64.5, "y": 19.5, "direction": 8}, {"name": "passive-provider-chest", "x": 64.5, "y": 18.5}]
CFG = ("local s=game.surfaces.gleba local R=defines.wire_connector_id.circuit_red local function at(t,x,y) return s.find_entities_filtered{type=t,position={x,y},radius=0.3}[1] end "
       "local c=at('logistic-container',130.5,10.5) local ss=c.get_logistic_sections() local se=ss.sections[1] or ss.add_section() se.set_slot(1,{value={name='spoilage',quality='normal'},min=9600}) "
       "for _,q in pairs{{73.5,1.5},{64.5,19.5}} do local k=at('inserter',q[1],q[2]) k.use_filters=true k.inserter_filter_mode='whitelist' k.set_filter(1,'spoilage') end "
       "local chain={} for x=118.5,123.5 do local b=at('transport-belt',x,9.5) local cb=b.get_or_create_control_behavior() cb.read_contents=true cb.read_contents_mode=defines.control_behavior.transport_belt.content_read_mode.hold cb.circuit_enable_disable=false chain[#chain+1]=b end "
       "local col=at('transport-belt',124.5,9.5) local cb=col.get_or_create_control_behavior() cb.read_contents=false cb.circuit_enable_disable=false chain[#chain+1]=col chain[#chain+1]=at('inserter',125.5,10.5) "
       "local i=at('inserter',129.5,10.5) local ib=i.get_or_create_control_behavior() ib.circuit_enable_disable=true ib.circuit_condition={first_signal={type='item',name='nutrients'},comparator='=',constant=0} chain[#chain+1]=i "
       "local ok=0 for n=2,#chain do local a,b=chain[n-1].get_wire_connector(R,true),chain[n].get_wire_connector(R,true) if a.is_connected_to(b) or a.connect_to(b,false) then ok=ok+1 end end "
       "rcon.print('reserve wired '..ok..' of '..(#chain-1))")
for e in E:
    e["params"] = dict(R)
apply = "--apply" in sys.argv
print(tools["place_entities"](json.dumps(E), surface="gleba", dry_run=not apply)[:400])
if apply:
    print(tools["run_lua"](CFG))
