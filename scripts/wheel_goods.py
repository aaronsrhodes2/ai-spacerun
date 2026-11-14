#!/usr/bin/env python3
"""Goods from the wheels' surplus metal (the Captain, 2026-11-13: "space stations can turn all of their excess materials into products
that are in short supply across the network, like steel plates ... there's a lot of ore in the wheels ... we can send it down to the
planet"). Two more foundries in the free west part of the spiral's heart (scripts/wheel_spiral.py), whose recipe is set by circuit
from what the hub is short of:
  iron caster    -99..-95, -44..-40 on the molten iron pipe row (extended west): casting-steel while the hub holds fewer than CAPS
                 steel plates, casting-iron for iron plates, casting-iron-gear-wheel for gears. Output by a belt along y=-46 onto the
                 out-belt (x=-107).
  copper caster  -105..-101, -44..-40 with a copper melter of its own under it (-105..-101, -38..-34, fed with leftover copper
                 ore and calcite from the passing out-belt): casting-copper for copper plates, casting-copper-cable for cable. Output straight onto the out-belt.
  control        five deciders in the gap column x=-100 read the hub (red, over reach): item below its cap -> the recipe signal. A
                 foundry that sees several recipe signals takes one of them; when its cap is reached that signal goes and the next
                 one rules. With every cap reached the foundries have no recipe and the crushers stop on their own gates.
The goods ride the out-belt into the hub. A landing pad whose requests follow the planet's missing requests
(scripts/order_carrier.py ground) takes them down when the planet is short of them.
Steps on every wheel (--only PLANET): check | build [--apply] | config | status. Never apply twice. Run config after a quality upgrade.
Usage: wheel_goods.py check | build [--apply] | config | status  [--only PLANET]"""
import sys

from _game import tools
from _wheels import place_all, wheels

Q = {"quality": "epic"}
N, E, S, W = 0, 4, 8, 12
RESERVE = 8000          # the iron caster works only while the spiral's tank holds more molten iron than this: green science has first call
# (on the Gleba Wheel, short of metallic chunks, the steel caster drained the tank and green science stood at 0)
CAPS = {"steel-plate": 4000, "iron-plate": 4000, "iron-gear-wheel": 2000, "copper-plate": 4000, "copper-cable": 2000}
RULES = [(-100, -44, "steel-plate", "casting-steel", "iron"), (-100, -42, "iron-plate", "casting-iron", "iron"), (-100, -40, "iron-gear-wheel", "casting-iron-gear-wheel", "iron"),
         (-100, -38, "copper-plate", "casting-copper", "copper"), (-100, -36, "copper-cable", "casting-copper-cable", "copper")]
ents = []


def put(name, tx, ty, w=1, h=1, d=N, **params):
    ents.append({"name": name, "x": tx + w / 2, "y": ty + h / 2, "direction": d, "params": dict(Q, **params)})


def layout():
    for x in range(-98, -92):
        put("pipe", x, -39)                                      # molten iron, on from the row's west end at -92
    put("foundry", -99, -44, 5, 5)                               # iron caster
    put("fast-inserter", -97, -45, d=S)
    for x in range(-97, -107, -1):
        put("express-transport-belt", x, -46, d=W)               # side-loads onto the out-belt at -107,-46
    put("foundry", -105, -38, 5, 5)                              # copper melter
    put("fast-inserter", -106, -36, d=W)                         # from the out-belt: the ore belt south of it never carries calcite that far west
    put("pipe", -104, -39)
    put("foundry", -105, -44, 5, 5)                              # copper caster
    put("fast-inserter", -106, -42, d=E)
    for x, y, item, rec, metal in RULES:
        put("decider-combinator", x, y, 1, 2)
    return {"entities": len(ents)}


CONFIG = ("local s=game.surfaces['SURF'] local hub=s.platform.hub local W=defines.wire_connector_id local function f(x,y) return s.find_entities_filtered{name='foundry',position={x,y},radius=0.6}[1] end "
          "local fi,fc,mc=f(-96.5,-41.5),f(-102.5,-41.5),f(-102.5,-35.5) local tank=s.find_entities_filtered{name='storage-tank',position={-84.5,-36.5},radius=0.5}[1] mc.set_recipe('copper-ore-melting') local i=s.find_entities_filtered{type='inserter',position={-105.5,-35.5},radius=0.3}[1] i.use_filters=true i.inserter_filter_mode='whitelist' i.set_filter(1,'copper-ore') i.set_filter(2,'calcite') "
          "pcall(function() hub.get_or_create_control_behavior().read_contents=true end) for _,m in pairs{fi,fc} do for _,id in pairs{W.circuit_red,W.circuit_green} do m.get_wire_connector(id,true).disconnect_all() end m.get_or_create_control_behavior().circuit_set_recipe=true end local n=0 "
          "for _,q in pairs(RULES) do local d=s.find_entities_filtered{name='decider-combinator',position={q[1]+0.5,q[2]+1},radius=0.3}[1] for _,id in pairs{W.combinator_input_red,W.combinator_input_green,W.combinator_output_red,W.combinator_output_green} do d.get_wire_connector(id,true).disconnect_all() end "
          "local cond={{first_signal={type='item',name=q[3]},first_signal_networks={red=true,green=false},comparator='<',constant=q[5]}} if q[6]=='iron' then cond[2]={first_signal={type='fluid',name='molten-iron'},first_signal_networks={red=false,green=true},comparator='>',constant=RESERVE,compare_type='and'} d.get_wire_connector(W.combinator_input_green,true).connect_to(tank.get_wire_connector(W.circuit_green,true),false) end d.get_or_create_control_behavior().parameters={conditions=cond,outputs={{signal={type='recipe',name=q[4]},copy_count_from_input=false,constant=1}}} "
          "d.get_wire_connector(W.combinator_input_red,true).connect_to(hub.get_wire_connector(W.circuit_red,true),false) d.get_wire_connector(W.combinator_output_green,true).disconnect_all() local m=(q[6]=='iron') and fi or fc d.get_wire_connector(W.combinator_output_green,true).connect_to(m.get_wire_connector(W.circuit_green,true),false) n=n+1 end "
          "rcon.print('rules wired '..n)")
STATUS = ("local s=game.surfaces['SURF'] local inv=s.platform.hub.get_inventory(defines.inventory.hub_main) local o={} for _,q in pairs{{-96.5,-41.5,'iron caster'},{-102.5,-41.5,'copper caster'},{-102.5,-35.5,'copper melter'}} do local m=s.find_entities_filtered{name='foundry',position={q[1],q[2]},radius=0.6}[1] "
          "local k='?' for a,v in pairs(defines.entity_status) do if v==m.status then k=a end end local r=m.get_recipe() o[#o+1]=q[3]..': '..(r and r.name or 'no recipe')..', '..k..', made '..m.products_finished end "
          "local t={} for _,n in pairs{'steel-plate','iron-plate','iron-gear-wheel','copper-plate','copper-cable'} do t[#t+1]=n..' '..inv.get_item_count(n) end rcon.print(table.concat(o,' | ')..' | in hub: '..table.concat(t,', '))")


def main():
    step = sys.argv[1]
    apply = "--apply" in sys.argv
    print(layout())
    if step == "check":
        return
    rules = "{" + ",".join("{%d,%d,'%s','%s',%d,'%s'}" % (x, y, item, rec, CAPS[item], metal) for x, y, item, rec, metal in RULES) + "}"
    for name, planet, surface, turrets in wheels():
        print("==", name, surface or "(not created)")
        if not surface:
            continue
        if step == "build":
            ok, bad = place_all(ents, surface, apply)
            print("placed" if apply else "dry run", ok, "failed", bad)
        if step == "config" or (step == "build" and apply):
            print(tools["run_lua"](CONFIG.replace("SURF", surface).replace("RULES", rules).replace("RESERVE", str(RESERVE))))
        elif step == "status":
            print(tools["run_lua"](STATUS.replace("SURF", surface)))


if __name__ == "__main__":
    main()
