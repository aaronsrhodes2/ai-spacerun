#!/usr/bin/env python3
"""Iron plates and steel on every wheel from the hub's own iron ore: the plate works (2026-11-14). The hubs stood full of iron ore
(33,000+) with no iron plate at all and little or no steel: the only source was the spiral's goods caster, which needs 8,000 molten
iron in a tank that is always empty. So the K loop of the blue block never got its 150 iron plates and the Ring (military and
production science, scripts/wheel_grey_purple.py) and the battery plant starved.
  where    the free deck between the ore loop's north row (O, wheel y=-32, flowing east) and the K loop's north row (wheel y=-41,
           flowing west), east of the Ring's stone and steel inserters: two foundries side by side, both facing east, so the
           melter's outputs (east edge) sit on the caster's inputs (west edge) and the molten iron passes port to port
           (place_entities leaves a foundry facing north whatever direction is asked, and a foundry with no recipe yet does not turn:
           `config` turns both east after the recipes are set; it must print `facing 4` twice)
  melter   108..112, -38..-34, iron-ore-melting: a fast inserter at 110,-33 lifts iron ore off the ore loop, a long-handed
           inserter at 110,-39 takes calcite off the K row
  caster   113..117, -38..-34, recipe set by circuit: casting-steel while the ore loop carries fewer than STEEL steel plates,
           otherwise casting-iron while the K loop carries fewer than PLATES iron plates, otherwise nothing
           a fast inserter at 115,-39 lays plates on a one-tile stub belt (115,-40) that side-loads onto the K row's near lane:
           on this row the far lane is the coal lane, which stands full, and an inserter always drops on the far lane (the
           first build did, and the plates stuck in the caster, which then refuses a new recipe until it is empty). A fast
           inserter at 115,-33 lays steel on the ore loop (where the Ring's inserters at 104..105,-33 take it); each is
           filtered and gated on the same count
  control  two deciders at 119,-37 (iron) and 119,-35 (steel). Steel reads the ore loop's belts (green), iron reads the K loop's
           belts (green) and, on red, the steel decider's output, so the caster sees one recipe signal at a time, steel first
           (a foundry given two takes iron and steel never comes). PLATES and STEEL lie a little above the hub inserters'
           targets in wheel_blue.py (150 and 20), so the wheel's own metal is used first and the hub's stock is the reserve.
A foundry makes 2.25 plates from an ore (furnace: 1) and a steel plate from 1.3 ore (furnace: 5).
`clear` removes the three electric furnaces of this script's first version (their contents go to the hub).
Steps on every wheel (--only PLANET): check | clear | build [--apply] | config | status. Never apply twice. After a quality upgrade: config.
Usage: wheel_plates.py check | clear | build [--apply] | config | status  [--only PLANET]"""
import sys

from _game import tools
from _wheels import place_all, wheels

Q = {"quality": "epic"}
N, E, S = 0, 4, 8
PLATES, STEEL = 170, 28
ents = [
    {"name": "foundry", "x": 110.5, "y": -35.5, "direction": E, "params": dict(Q)},
    {"name": "foundry", "x": 115.5, "y": -35.5, "direction": E, "params": dict(Q)},
    {"name": "fast-inserter", "x": 110.5, "y": -32.5, "direction": S, "params": dict(Q)},            # ore: picks up from the south (the ore loop)
    {"name": "long-handed-inserter", "x": 110.5, "y": -38.5, "direction": N, "params": dict(Q)},     # calcite: picks up from the north (K)
    {"name": "fast-inserter", "x": 115.5, "y": -38.5, "direction": S, "params": dict(Q)},            # plates: from the caster onto the stub
    {"name": "express-transport-belt", "x": 115.5, "y": -39.5, "direction": N, "params": dict(Q)},   # stub: side-loads onto K's near (supply) lane
    {"name": "fast-inserter", "x": 115.5, "y": -32.5, "direction": N, "params": dict(Q)},            # steel: from the caster to the ore loop
    {"name": "decider-combinator", "x": 119.5, "y": -36.0, "direction": N, "params": dict(Q)},
    {"name": "decider-combinator", "x": 119.5, "y": -34.0, "direction": N, "params": dict(Q)},
]

CHECK = ("local s=game.surfaces['SURF'] local n=s.count_entities_filtered{area={{107,-40},{120,-33}}} local t=0 for x=107,119 do for y=-40,-33 do local tl=s.get_tile(x,y) if tl.name~='space-platform-foundation' then t=t+1 end end end "
         "local function b(x,y) local e=s.find_entities_filtered{type='transport-belt',position={x+0.5,y+0.5},radius=0.3}[1] return e and (e.name..' dir '..e.direction) or 'NONE' end "
         "rcon.print('entities on the site '..n..', tiles without deck '..t..', ore row at 110,-32: '..b(110,-32)..', K row at 110,-41: '..b(110,-41))")
CLEAR = ("local s=game.surfaces['SURF'] local hub=s.platform.hub local n,m=0,0 if s.count_entities_filtered{name='electric-furnace',area={{107,-40},{120,-33}}}==0 then rcon.print('no first-version furnaces here') return end for _,e in pairs(s.find_entities_filtered{name={'electric-furnace','long-handed-inserter'},area={{107,-40},{120,-33}}}) do "
         "for i=1,e.get_max_inventory_index() do local inv=e.get_inventory(i) if inv then for _,it in pairs(inv.get_contents()) do if it.name:find('module',1,true)==nil then m=m+hub.insert{name=it.name,count=it.count,quality=it.quality} end end end end "
         "if e.type=='inserter' and e.held_stack.valid_for_read then m=m+hub.insert(e.held_stack) end e.destroy() n=n+1 end rcon.print('first-version entities removed '..n..', items returned to the hub '..m)")
CONFIG = ("local s=game.surfaces['SURF'] local W=defines.wire_connector_id local function at(t,x,y) return s.find_entities_filtered{type=t,position={x,y},radius=0.4}[1] end "
          "local melt=s.find_entities_filtered{name='foundry',position={110.5,-35.5},radius=0.6}[1] local cast=s.find_entities_filtered{name='foundry',position={115.5,-35.5},radius=0.6}[1] "
          "local ore,cal,pl,st=at('inserter',110.5,-32.5),at('inserter',110.5,-38.5),at('inserter',115.5,-38.5),at('inserter',115.5,-32.5) local di,ds=at('decider-combinator',119.5,-36),at('decider-combinator',119.5,-34) "
          "local kb=at('transport-belt',115.5,-40.5) local ob=at('transport-belt',115.5,-31.5) melt.set_recipe('iron-ore-melting') "
          "local function filt(i,name) i.use_filters=true i.inserter_filter_mode='whitelist' i.set_filter(1,name) end filt(ore,'iron-ore') filt(cal,'calcite') filt(pl,'iron-plate') filt(st,'steel-plate') "
          "local function gate(i,belt,name,cap) local c=i.get_wire_connector(W.circuit_green,true) c.disconnect_all() c.connect_to(belt.get_wire_connector(W.circuit_green,true),false) local cb=i.get_or_create_control_behavior() cb.circuit_enable_disable=true "
          "cb.circuit_condition={first_signal={type='item',name=name},comparator='<',constant=cap} end gate(pl,kb,'iron-plate',PLATES) gate(st,ob,'steel-plate',STEEL) "
          "for _,d in pairs{di,ds} do for _,id in pairs{W.combinator_input_red,W.combinator_input_green,W.combinator_output_red,W.combinator_output_green} do d.get_wire_connector(id,true).disconnect_all() end end "
          "for _,id in pairs{W.circuit_red,W.circuit_green} do cast.get_wire_connector(id,true).disconnect_all() end "
          "ds.get_wire_connector(W.combinator_input_green,true).connect_to(ob.get_wire_connector(W.circuit_green,true),false) di.get_wire_connector(W.combinator_input_green,true).connect_to(kb.get_wire_connector(W.circuit_green,true),false) "
          "local cr=cast.get_wire_connector(W.circuit_red,true) ds.get_wire_connector(W.combinator_output_red,true).connect_to(cr,false) di.get_wire_connector(W.combinator_output_red,true).connect_to(cr,false) di.get_wire_connector(W.combinator_input_red,true).connect_to(cr,false) "
          "ds.get_or_create_control_behavior().parameters={conditions={{first_signal={type='item',name='steel-plate'},first_signal_networks={red=false,green=true},comparator='<',constant=STEEL}},outputs={{signal={type='recipe',name='casting-steel'},copy_count_from_input=false,constant=1}}} "
          "di.get_or_create_control_behavior().parameters={conditions={{first_signal={type='item',name='iron-plate'},first_signal_networks={red=false,green=true},comparator='<',constant=PLATES},"
          "{first_signal={type='recipe',name='casting-steel'},first_signal_networks={red=true,green=false},comparator='=',constant=0,compare_type='and'}},outputs={{signal={type='recipe',name='casting-iron'},copy_count_from_input=false,constant=1}}} "
          "cast.get_or_create_control_behavior().circuit_set_recipe=true melt.direction=defines.direction.east cast.direction=defines.direction.east rcon.print('plate works configured: melter '..tostring(melt.get_recipe() and melt.get_recipe().name)..' facing '..melt.direction..', caster facing '..cast.direction..', K belt wired '..tostring(kb~=nil)..', ore belt wired '..tostring(ob~=nil))")
STATUS = ("local s=game.surfaces['SURF'] local function sn(e) for n,x in pairs(defines.entity_status) do if x==e.status then return n end end return '?' end "
          "local melt=s.find_entities_filtered{name='foundry',position={110.5,-35.5},radius=0.6}[1] local cast=s.find_entities_filtered{name='foundry',position={115.5,-35.5},radius=0.6}[1] if not melt or not cast then rcon.print('no plate works') return end "
          "local function at(x,y) return s.find_entities_filtered{type='inserter',position={x,y},radius=0.4}[1] end local pl,st=at(115.5,-38.5),at(115.5,-32.5) local G=defines.wire_connector_id.circuit_green "
          "local kn,on=pl.get_circuit_network(G),st.get_circuit_network(G) local rc=cast.get_recipe() local fl={} for k,v in pairs(cast.get_fluid_contents()) do fl[#fl+1]=k..' '..math.floor(v) end "
          "local inv=s.platform.hub.get_inventory(defines.inventory.hub_main) "
          "rcon.print('melter '..sn(melt)..' made '..melt.products_finished..' | caster '..(rc and rc.name or 'no recipe')..' '..sn(cast)..' made '..cast.products_finished..' holds '..table.concat(fl,',')..' | ore in '..sn(at(110.5,-32.5))..', calcite in '..sn(at(110.5,-38.5))..', plates out '..sn(pl)..', steel out '..sn(st)"
          "..' | K iron plates '..(kn and kn.get_signal({type='item',name='iron-plate'}) or -1)..', ore loop steel '..(on and on.get_signal({type='item',name='steel-plate'}) or -1)..' | hub iron plate '..inv.get_item_count('iron-plate')..', steel '..inv.get_item_count('steel-plate')..', iron ore '..inv.get_item_count('iron-ore'))")


def main():
    step = sys.argv[1]
    apply = "--apply" in sys.argv
    for name, planet, surface, turrets in wheels():
        print("==", name, surface or "(not created)")
        if not surface:
            continue
        code = None
        if step == "check":
            code = CHECK
        elif step == "clear":
            code = CLEAR
        elif step == "build":
            ok, bad = place_all(ents, surface, apply)
            print("placed" if apply else "dry run", ok, "failed", bad)
        if step == "config" or (step == "build" and apply):
            code = CONFIG
        elif step == "status":
            code = STATUS
        if code:
            print(tools["run_lua"](code.replace("SURF", surface).replace("PLATES", str(PLATES)).replace("STEEL", str(STEEL))).strip())


if __name__ == "__main__":
    main()
