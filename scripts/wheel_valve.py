#!/usr/bin/env python3
"""The surplus valve of every wheel, and the cap on stored space science.
Why: asteroids arrive in a fixed mix and the pack lines use a different one, so one product always piles up. On 2026-11-13 the Nauvis
hub held 115,000 iron ore and had 1,164 of 7,579 slots left; a full hub cannot take packs, and capping the intake instead starves the
line of the scarce product (ice) behind the plentiful one (iron) on the same belt. The Captain's surplus rule: stop making it, then make
useful goods, then void. Until more pack lines use the ore, the valve is the third step:
  bridge   a cargo bay over the east avenue joins the north-east bays to the south-east ones (the avenue belt dives under it), which
           frees the four tiles of the hub's east edge that the north-east contact bay took
  valve    a bulk inserter on the first of those tiles takes from the hub and drops into a slot cut in the deck (open space): overboard
           (there were four; scripts/wheel_blue.py took the other three tiles for the blue science line, so run this before that script)
  control  a decider reads the hub: every item above CAP becomes a filter for the valve inserters; with nothing above CAP they are off
  packs    the three inserters that feed the space science line switch off above PACKS stored packs, so packs are never voided
Run once per wheel (it does nothing where the decider already stands, except set the numbers again).
Usage: wheel_valve.py [--only PLANET]"""
import json

from _game import tools
from _wheels import wheels

CAP, PACKS = 36000, 20000   # 36,000 since the blue line (scripts/wheel_blue.py): salvaged chunks hold 1,460 slots and the Nauvis hub stood full at 40,000
Q = {"quality": "epic"}
BRIDGE = [{"name": "cargo-bay", "x": 34, "y": 2, "direction": 0, "params": Q},
          {"name": "express-underground-belt", "x": 36.5, "y": 3.5, "direction": 12, "params": dict(Q, type="input")},
          {"name": "express-underground-belt", "x": 31.5, "y": 3.5, "direction": 12, "params": dict(Q, type="output")}]
VALVE = [{"name": "bulk-inserter", "x": 4.5, "y": y + .5, "direction": 12, "params": Q} for y in range(-4, -3)] + \
        [{"name": "decider-combinator", "x": 7, "y": -3.5, "direction": 4, "params": Q}]

PRE = ("local s=game.surfaces['SURF'] if s.count_entities_filtered{name='decider-combinator',area={{4,-5},{9,0}}}>0 then rcon.print('present') return end local hub=s.platform.hub local n=0 "
       "for _,e in pairs(s.find_entities_filtered{type={'transport-belt','lamp'},area={{31.1,0.1},{36.9,3.9}}}) do if e.type=='transport-belt' then for l=1,2 do for _,it in pairs(e.get_transport_line(l).get_contents()) do hub.insert{name=it.name,count=it.count,quality=it.quality} end end end e.destroy() n=n+1 end rcon.print('cleared '..n)")
CUT = ("local s=game.surfaces['SURF'] local b=s.find_entities_filtered{name='cargo-bay',position={6,-2},radius=0.5}[1] if b then b.destroy() end for _,e in pairs(s.find_entities_filtered{type='lamp',area={{4.1,-3.9},{7.9,-0.1}}}) do e.destroy() end "
       "local t={} for y=-4,-1 do t[#t+1]={name='empty-space',position={5,y}} end s.set_tiles(t) local inv=s.platform.hub.get_inventory(defines.inventory.hub_main) rcon.print('slot cut, hub slots '..#inv..' free '..inv.count_empty_stacks())")
WIRE = ("local s=game.surfaces['SURF'] local hub=s.platform.hub local W=defines.wire_connector_id local o={} local hc=hub.get_or_create_control_behavior() pcall(function() hc.read_contents=true end) "
        "local dec=s.find_entities_filtered{name='decider-combinator',area={{4,-5},{9,0}}}[1] local dc=dec.get_or_create_control_behavior() "
        "dc.parameters={conditions={{first_signal={type='virtual',name='signal-each'},comparator='>',constant=CAP}},outputs={{signal={type='virtual',name='signal-each'},copy_count_from_input=false}}} "
        "o[#o+1]='hub-decider '..tostring(dec.get_wire_connector(W.combinator_input_green,true).connect_to(hub.get_wire_connector(W.circuit_green,true))) "
        "for _,i in pairs(s.find_entities_filtered{name='bulk-inserter',area={{4.1,-3.9},{4.9,-3.1}}}) do i.get_wire_connector(W.circuit_red,true).connect_to(dec.get_wire_connector(W.combinator_output_red,true)) "
        "i.use_filters=true i.inserter_filter_mode='whitelist' local cb=i.get_or_create_control_behavior() cb.circuit_set_filters=true cb.circuit_enable_disable=true "
        "cb.circuit_condition={first_signal={type='virtual',name='signal-anything'},comparator='>',constant=0} o[#o+1]='valve '..tostring(i.get_wire_connector(W.circuit_red,true).is_connected_to(dec.get_wire_connector(W.combinator_output_red,true))) end "
        "for _,i in pairs(s.find_entities_filtered{name='fast-inserter',area={{0.1,-4.9},{2.9,-4.1}}}) do i.get_wire_connector(W.circuit_red,true).connect_to(hub.get_wire_connector(W.circuit_red,true)) local cb=i.get_or_create_control_behavior() "
        "cb.circuit_enable_disable=true cb.circuit_condition={first_signal={type='item',name='space-science-pack'},comparator='<',constant=PACKS} o[#o+1]='feed '..tostring(i.get_wire_connector(W.circuit_red,true).is_connected_to(hub.get_wire_connector(W.circuit_red,true))) end "
        "rcon.print(table.concat(o,', '))").replace("CAP", str(CAP)).replace("PACKS", str(PACKS))


def place(ents, surface):
    d = json.loads(tools["place_entities"](json.dumps(ents), surface=surface, dry_run=True))
    if d.get("failed"):
        raise SystemExit("dry run failed, nothing placed: %s" % d["failed"])
    return json.loads(tools["place_entities"](json.dumps(ents), surface=surface, dry_run=False)).get("placed")


for name, planet, surface, turrets in wheels():
    if not surface:
        continue
    print("==", name)
    pre = tools["run_lua"](PRE.replace("SURF", surface)).strip()
    print(pre)
    if pre != "present":
        print("bridge placed", place(BRIDGE, surface))
        print(tools["run_lua"](CUT.replace("SURF", surface)))
        print("valve placed", place(VALVE, surface))
    print(tools["run_lua"](WIRE.replace("SURF", surface)))
