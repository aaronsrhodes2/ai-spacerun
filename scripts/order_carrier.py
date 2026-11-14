#!/usr/bin/env python3
"""Orders that cross space (the Captain, 2026-11-13: "there must be a way of transferring a planet-to-planet signal, or at least
storing it on a ship so the ship can carry the request"). No wire crosses from a planet to orbit, but a landing pad and a ship's
hub can both take their requests from a circuit, and a ship can read its own cargo. So the ship carries a MENU: at least one of
every catalog item. The planet orders by taking.
  planet B  a roboport reads the network's missing requests; that signal sets the landing pad's requests. When the ship is overhead
            the pad takes down whatever B is missing and the ship has.
  the ship  a constant combinator lists the menu (every catalog item, 1). A decider compares it with the hub's contents: every menu
            item the ship has NONE of becomes an order; a selector turns each order into one rocket load; that sets the hub's
            requests. At planet A the silos see them as orbital requests and A's stock, or its make-anything machines
            (scripts/omni_maker.py), fill them. So what B took is what the ship brings more of, and the ship is a flying warehouse
            of the rest.
  wiring    the hub puts its contents on both wires, so two arithmetic combinators stand first: one puts minus twice the contents
            on green (the circuit requests then see only the orders), one copies the magazine count to signal M for the schedule
            (item wait conditions would otherwise read zero).
First try, abandoned: an uncommon-quality sample sent UP from planet B as the order form. It needs a rocket from B for every order,
and the silo on Gleba had no rocket parts. `unbuild` removes the catalog chest and combinators of that try and gives the samples
back as normal items.
Steps: ground PLANET [--apply] | unbuild PLANET | ship "NAME" [--apply] | status PLANET "NAME"
Usage: order_carrier.py ground gleba --apply ; order_carrier.py ship "Nauvis-Gleba 5 Shuttle II" --apply"""
import json
import sys

from _game import tools
from kit_shipping import KIT
from nauvis_mall import ITEMS

CAT = sorted(set(KIT + ITEMS) - {"iron-gear-wheel", "iron-stick"})     # a rocket load of those two is 30 hub slots
SITES = {"gleba": (151, 13)}
Q = {"quality": "epic"}
HEAD = ("local f=game.forces.player local W=defines.wire_connector_id local function wire(a,ia,b,ib) a.get_wire_connector(ia,true).connect_to(b.get_wire_connector(ib,true),false) end "
        "local function clear(e) for _,id in pairs{W.combinator_input_red,W.combinator_input_green,W.combinator_output_red,W.combinator_output_green} do e.get_wire_connector(id,true).disconnect_all() end end local o={} local cat={CAT} ")


def ground(planet):
    x, y = SITES[planet]
    return [{"name": "roboport", "x": x + 2, "y": y + 2, "direction": 0, "params": dict(Q)},
            {"name": "substation", "x": x + 5, "y": y + 2, "direction": 0, "params": dict(Q)}]


GROUND = HEAD + (
    "local s=game.surfaces['SURF'] local rp=s.find_entities_filtered{name='roboport',position={OX+2,OY+2},radius=0.6}[1] "
    "local rc=rp.get_or_create_control_behavior() rc.read_items_mode=defines.control_behavior.roboport.read_items_mode.missing_requests rc.read_robot_stats=false "
    "local pad=s.find_entities_filtered{type='cargo-landing-pad'}[1] wire(pad,W.circuit_red,rp,W.circuit_red) local pb=pad.get_or_create_control_behavior() pb.set_requests=true pb.read_contents=false "
    "rcon.print('ground wired: the pad on SURF asks for whatever the network is missing')")
UNBUILD = HEAD + (
    "local s=game.surfaces['SURF'] local X,Y=OX,OY local pad=s.find_entities_filtered{type='cargo-landing-pad'}[1] local pi=pad.get_inventory(defines.inventory.cargo_landing_pad_main) local back,gone=0,0 "
    "local rq=s.find_entities_filtered{name='requester-chest',position={X+0.5,Y+5.5},radius=0.6}[1] if rq then for _,it in pairs(rq.get_inventory(defines.inventory.chest).get_contents()) do back=back+pi.insert{name=it.name,count=it.count,quality='normal'} end rq.destroy() gone=gone+1 end "
    "local net=s.find_logistic_network_by_position({X+2,Y+2},'player') if net then for _,it in pairs(cat) do local n=net.get_item_count({name=it,quality='uncommon'}) if n>0 then local r=net.remove_item({name=it,count=n,quality='uncommon'}) back=back+pi.insert{name=it,count=r,quality='normal'} end end end "
    "for _,q in pairs{{'constant-combinator',1.5,5.5},{'selector-combinator',2.5,6},{'selector-combinator',3.5,6},{'arithmetic-combinator',4.5,6}} do local e=s.find_entities_filtered{name=q[1],position={X+q[2],Y+q[3]},radius=0.6}[1] if e then e.destroy() gone=gone+1 end end "
    "rcon.print('removed '..gone..' pieces of the first try; '..back..' samples back on the pad as normal items')")
SHIP_ENTS = [("arithmetic-combinator", -10.5, -1), ("arithmetic-combinator", -8.5, -1), ("constant-combinator", -10.5, 0.5),
             ("decider-combinator", -10.5, 6), ("selector-combinator", -8.5, 1)]
SHIP = HEAD + (
    "local p for _,q in pairs(f.platforms) do if q.name=='NAME' then p=q end end local s=p.surface local hub=p.hub local function at(n,x,y) return s.find_entities_filtered{name=n,position={x,y},radius=0.6}[1] end "
    "for _,q in pairs{{-10.5,2},{-10.5,4}} do local e=at('selector-combinator',q[1],q[2]) if e then e.destroy() end end "
    "local a1,am,cc,rq,rc=at('arithmetic-combinator',-10.5,-1),at('arithmetic-combinator',-8.5,-1),at('constant-combinator',-10.5,0.5),at('decider-combinator',-10.5,6),at('selector-combinator',-8.5,1) "
    "clear(a1) clear(am) clear(rq) clear(rc) for _,id in pairs{W.circuit_red,W.circuit_green} do cc.get_wire_connector(id,true).disconnect_all() end "
    "wire(a1,W.combinator_input_red,hub,W.circuit_red) wire(a1,W.combinator_output_green,hub,W.circuit_green) a1.get_or_create_control_behavior().parameters={first_signal={type='virtual',name='signal-each'},second_constant=-2,operation='*',output_signal={type='virtual',name='signal-each'}} "
    "wire(am,W.combinator_input_red,hub,W.circuit_red) wire(am,W.combinator_output_green,hub,W.circuit_green) am.get_or_create_control_behavior().parameters={first_signal={type='item',name='firearm-magazine'},second_constant=1,operation='*',output_signal={type='virtual',name='signal-M'}} "
    "local cb=cc.get_or_create_control_behavior() while cb.sections_count>0 do cb.remove_section(1) end local sec=cb.add_section() for i,it in pairs(cat) do sec.set_slot(i,{value={type='item',name=it,quality='normal'},min=1}) end "
    "wire(rq,W.combinator_input_green,cc,W.circuit_green) wire(rq,W.combinator_input_red,hub,W.circuit_red) "
    "rq.get_or_create_control_behavior().parameters={conditions={{first_signal={type='virtual',name='signal-each'},first_signal_networks={red=false,green=true},comparator='>',constant=0},"
    "{first_signal={type='virtual',name='signal-each'},first_signal_networks={red=true,green=false},comparator='<',constant=1,compare_type='and'}},outputs={{signal={type='virtual',name='signal-each'},copy_count_from_input=false,constant=1}}} "
    "wire(rc,W.combinator_input_red,rq,W.combinator_output_red) rc.get_or_create_control_behavior().parameters={operation='rocket-capacity'} wire(rc,W.combinator_output_green,hub,W.circuit_green) "
    "hub.get_or_create_control_behavior().set_requests=true local pt for _,q in pairs(hub.get_logistic_point()) do if q.mode==defines.logistic_mode.requester then pt=q end end "
    "for i=pt.sections_count,1,-1 do local x=pt.sections[i] if x.is_manual and x.filters_count>0 and x.filters[1].value and x.filters[1].value.quality=='uncommon' then pt.remove_section(i) end end "
    "rcon.print('carrier wired on '..p.name..': menu of '..#cat..' items')")
STATUS = HEAD + (
    "local s=game.surfaces['SURF'] local rp=s.find_entities_filtered{name='roboport',position={OX+2,OY+2},radius=0.6}[1] "
    "local function sig(n,max) local t={} if n and n.signals then local l=n.signals table.sort(l,function(a,b) return a.count>b.count end) for i,x in pairs(l) do if i<=max then t[#t+1]=x.signal.name..' '..x.count end end end return table.concat(t,', ') end "
    "o[#o+1]='missing on SURF (top 12): '..sig(rp.get_circuit_network(W.circuit_red),12) "
    "local pad=s.find_entities_filtered{type='cargo-landing-pad'}[1] local pt={} for _,q in pairs(pad.get_logistic_point()) do if q.mode==defines.logistic_mode.requester then for _,sec in pairs(q.sections) do if not sec.is_manual then for _,fl in pairs(sec.filters) do if fl.value then pt[#pt+1]=fl.value.name..' '..fl.min end end end end end end o[#o+1]='pad asks (by circuit): '..table.concat(pt,', ') "
    "for _,p in pairs(f.platforms) do if p.name=='NAME' then local hub=p.hub local inv=hub.get_inventory(defines.inventory.hub_main) local have=0 for _,it in pairs(cat) do if inv.get_item_count(it)>0 then have=have+1 end end local rqs={} "
    "for _,q in pairs(hub.get_logistic_point()) do if q.mode==defines.logistic_mode.requester then for _,sec in pairs(q.sections) do if not sec.is_manual then for _,fl in pairs(sec.filters) do if fl.value then rqs[#rqs+1]=fl.value.name..' '..fl.min end end end end end end "
    "o[#o+1]='ship at '..(p.space_location and p.space_location.name or 'flight')..': menu items aboard '..have..' of '..#cat..', free slots '..inv.count_empty_stacks()..' | orders ('..#rqs..'): '..table.concat(rqs,', ') end end rcon.print(table.concat(o,' ;; '))")


def main():
    step = sys.argv[1]
    apply = "--apply" in sys.argv
    cat = ",".join("'%s'" % c for c in CAT)

    def run(code, planet="gleba", name=""):
        x, y = SITES[planet]
        return tools["run_lua"](code.replace("{CAT}", "{" + cat + "}").replace("SURF", planet).replace("OX", str(x)).replace("OY", str(y)).replace("NAME", name))

    if step == "ground":
        have = tools["run_lua"]("rcon.print(#game.surfaces['%s'].find_entities_filtered{name='roboport',position={%d,%d},radius=0.6})" % (sys.argv[2], SITES[sys.argv[2]][0] + 2, SITES[sys.argv[2]][1] + 2)).strip()
        if have == "0":
            r = json.loads(tools["place_entities"](json.dumps(ground(sys.argv[2])), surface=sys.argv[2], dry_run=not apply))
            print("placed" if apply else "dry run", r.get("placed"), "failed", json.dumps(r.get("failed") or [])[:300])
        if apply:
            print(run(GROUND, sys.argv[2]))
    elif step == "unbuild":
        print(run(UNBUILD, sys.argv[2]))
    elif step == "ship":
        name = sys.argv[2]
        sf = tools["run_lua"]("for _,p in pairs(game.forces.player.platforms) do if p.name=='%s' then rcon.print(p.surface.name) end end" % name).strip()
        have = tools["run_lua"]("local s=game.surfaces['%s'] local t={} for _,q in pairs({%s}) do t[#t+1]=#s.find_entities_filtered{name=q[1],position={q[2],q[3]},radius=0.6} end rcon.print(table.concat(t,','))"
                                % (sf, ",".join("{'%s',%s,%s}" % e for e in SHIP_ENTS))).strip().split(",")
        todo = [{"name": n, "x": x, "y": y, "direction": 0, "params": dict(Q)} for (n, x, y), h in zip(SHIP_ENTS, have) if h == "0"]
        r = json.loads(tools["place_entities"](json.dumps(todo), surface=sf, dry_run=not apply)) if todo else {"placed": 0}
        print("placed" if apply else "dry run", r.get("placed"), "failed", json.dumps(r.get("failed") or [])[:300])
        if apply:
            print(run(SHIP, name=name))
    elif step == "status":
        print(run(STATUS, sys.argv[2], sys.argv[3]).replace(" ;; ", "\n"))


if __name__ == "__main__":
    main()
