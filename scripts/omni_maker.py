#!/usr/bin/env python3
"""The make-anything machines (the Captain, 2026-11-13: a machine per planet, wired to the logistics network, that builds whatever
any request anywhere is missing, sub-components included). Assembling machines 3 whose recipe is set by circuit, in a chain of DEPTH.
  demand    a roboport of its own reads the network's MISSING REQUESTS; the planet's rocket silos read ORBITAL REQUESTS (what a
            shuttle overhead asks this planet for), less what the network already holds (stock_stage). Both end on one red wire.
  filter    a constant combinator lists every item an assembler can make from solid ingredients (generated from the game's
            recipes, science packs left out); a decider per machine passes only the demanded items on that list
  choice    smallest order first (a big order used to hold all three machines while small ones waited): the decider gives every
            missing makeable item a million, the arithmetic combinator beside the machine subtracts the missing count (of the
            raw demand: what cannot be made ends up negative), and a selector picks the largest score; that signal sets the
            assembler's recipe. A decider puts every output on BOTH its wires; `networks` in an output only says which INPUT
            wire the copied count comes from.
  supply    a recipe table: one decider per makeable item (step `rom`, 35 x 5 a machine, south of the machines) that answers the
            chosen item with its ingredients times BATCH and so sets the requests of a blue requester chest (which trashes what is
            no longer asked for). The assembler's own "read ingredients" cannot be used: an assembler obeys the FIRST recipe signal
            in the game's item order, not the largest, and it reads its own ingredient signals, so it slid down the recipe tree
            (assembler 3 -> 2 -> 1 -> gears). The arithmetic combinators beside the machines are left over from that try, unwired.
  output    an inserter empties the assembler into a red provider chest; robots carry the goods to whoever asked
  nesting   one machine alone deadlocks: it keeps choosing the big order and never switches to the part it is waiting for. So
            machine 2 gives first call to whatever machine 1's chest asks for and the network lacks (a decider adds ten million
            to those scores), and machine 3 does the same for machine 2. Three levels: assembler 3 <- assembler 2 <- assembler 1.
Limits: slow; nothing that needs a fluid, a furnace, a foundry or another special machine; raw materials must already be in the
network; deeper than DEPTH levels waits; across planets it only sees what a shuttle in orbit asks for.
Steps: build PLANET [--from K] [--apply] | rom PLANET [--apply] | furnace PLANET [--apply | --config] | config PLANET | status PLANET. SITES: top-left tile of a free 24 x 14 area in the robot
network. Never apply twice (--from 1 places only machines 2 and up). Run config again after a quality upgrade (over-reach wires).
Usage: omni_maker.py build nauvis [--apply] | config nauvis | status nauvis"""
import json
import sys

from _game import tools

SITES = {"nauvis": (-30, -400)}
BATCH, DEPTH, PITCH = 5, 3, 7
Q = {"quality": "epic"}


def stock_stage(planet):
    """Added after the first build: a second roboport reads what the network HOLDS, an arithmetic combinator negates it, and a
    decider lets an orbital request through only for the part the network cannot cover (the silos report every open request of a
    shuttle overhead, also for items the planet has plenty of)."""
    x, y = SITES[planet]
    return [{"name": "roboport", "x": x + 2, "y": y + 16, "direction": 0, "params": dict(Q)},
            {"name": "arithmetic-combinator", "x": x + 4.5, "y": y + 1, "direction": 0, "params": dict(Q)},
            {"name": "decider-combinator", "x": x + 4.5, "y": y + 3, "direction": 0, "params": dict(Q)}]


def layout(planet, first=0, extra_only=False):
    x, y = SITES[planet]
    out = []

    def e(name, tx, ty, w=1, h=1):
        out.append({"name": name, "x": x + tx + w / 2, "y": y + ty + h / 2, "direction": 0, "params": dict(Q)})

    for k in range(first, DEPTH):
        ox = PITCH * k
        if k == 0:
            e("roboport", 0, 0, 4, 4)
            e("constant-combinator", 5, 6)
        else:
            e("arithmetic-combinator", ox + 6, 10, 1, 2)      # copies the demand onto this machine's own wire
            e("decider-combinator", ox + 5, 12, 1, 2)         # first call for what the machine before is waiting for
        e("substation", ox + 5, 1, 2, 2)
        e("requester-chest", ox + 2, 6)
        e("fast-inserter", ox + 2, 7)
        e("assembling-machine-3", ox + 1, 8, 3, 3)
        e("fast-inserter", ox + 2, 11)
        e("passive-provider-chest", ox + 2, 12)
        e("decider-combinator", ox + 5, 7, 1, 2)
        e("selector-combinator", ox + 6, 7, 1, 2)
        e("arithmetic-combinator", ox + 5, 10, 1, 2)
    return out


FX = 23        # the furnace unit stands at this offset east of machine 1


def furnace_layout(planet, n):
    """A furnace needs no recipe signal (it smelts what it is given): its own item list, decider, selector and a small recipe table
    (n deciders in a row south of it) set what the blue chest asks for."""
    x, y = SITES[planet]

    def e(name, tx, ty, w=1, h=1):
        return {"name": name, "x": x + FX + tx + w / 2, "y": y + ty + h / 2, "direction": 0, "params": dict(Q)}

    return ([e("substation", 5, 1, 2, 2), e("requester-chest", 2, 6), e("fast-inserter", 2, 7), e("electric-furnace", 1, 8, 3, 3), e("fast-inserter", 2, 11),
             e("passive-provider-chest", 2, 12), e("constant-combinator", 5, 6), e("decider-combinator", 5, 7, 1, 2), e("selector-combinator", 6, 7, 1, 2)]
            + [e("decider-combinator", i, 14, 1, 2) for i in range(n)])


SMELT = ("local cats=prototypes.entity['electric-furnace'].crafting_categories local mk,rec={},{} for name,r in pairs(f.recipes) do local p=r.prototype local okc=false for _,c in pairs(p.categories) do if cats[c] then okc=true end end "
         "if r.enabled and okc and not p.hidden and #r.products==1 and r.products[1].type=='item' and #r.ingredients==1 and r.ingredients[1].type=='item' and not rec[r.products[1].name] then mk[#mk+1]=r.products[1].name rec[r.products[1].name]=r end end ")
FURNACE = ("local s=game.surfaces['SURF'] local f=game.forces.player local W=defines.wire_connector_id local X,Y=OX+FX,OY local function at(n,dx,dy) return s.find_entities_filtered{name=n,position={X+dx,Y+dy},radius=0.6}[1] end "
           "local function wire(a,ia,b,ib) a.get_wire_connector(ia,true).connect_to(b.get_wire_connector(ib,true),false) end " + SMELT +
           "local rp=s.find_entities_filtered{name='roboport',position={OX+2,OY+2},radius=0.6}[1] local rq,cc,dec,sel=at('requester-chest',2.5,6.5),at('constant-combinator',5.5,6.5),at('decider-combinator',5.5,8),at('selector-combinator',6.5,8) "
           "local cb=cc.get_or_create_control_behavior() while cb.sections_count>0 do cb.remove_section(1) end local sec=cb.add_section() for i,it in pairs(mk) do sec.set_slot(i,{value={type='item',name=it,quality='normal'},min=1}) end "
           "for _,id in pairs{W.combinator_input_red,W.combinator_input_green,W.combinator_output_red,W.combinator_output_green} do dec.get_wire_connector(id,true).disconnect_all() sel.get_wire_connector(id,true).disconnect_all() end "
           "for _,id in pairs{W.circuit_red,W.circuit_green} do rq.get_wire_connector(id,true).disconnect_all() end "
           "wire(dec,W.combinator_input_red,rp,W.circuit_red) wire(dec,W.combinator_input_green,cc,W.circuit_green) "
           "dec.get_or_create_control_behavior().parameters={conditions={{first_signal={type='virtual',name='signal-each'},first_signal_networks={red=true,green=false},comparator='>',constant=0},"
           "{first_signal={type='virtual',name='signal-each'},first_signal_networks={red=false,green=true},comparator='>',constant=0,compare_type='and'}},outputs={{signal={type='virtual',name='signal-each'},copy_count_from_input=true,networks={red=true,green=false}}}} "
           "wire(sel,W.combinator_input_red,dec,W.combinator_output_red) sel.get_or_create_control_behavior().parameters={operation='select',select_max=true,index_constant=0} "
           "local qb=rq.get_or_create_control_behavior() qb.set_requests=true qb.read_contents=false rq.get_logistic_point(defines.logistic_member_index.logistic_container).trash_not_requested=true local n=0 "
           "for i,it in pairs(mk) do local d=at('decider-combinator',i-0.5,15) if d then local ing=rec[it].ingredients[1] d.get_or_create_control_behavior().parameters={conditions={{first_signal={type='item',name=it},comparator='>',constant=0}},"
           "outputs={{signal={type='item',name=ing.name},copy_count_from_input=false,constant=ing.amount*BATCH*4}}} for _,id in pairs{W.combinator_input_red,W.combinator_input_green,W.combinator_output_red,W.combinator_output_green} do d.get_wire_connector(id,true).disconnect_all() end "
           "wire(d,W.combinator_input_green,sel,W.combinator_output_green) wire(d,W.combinator_output_green,rq,W.circuit_green) n=n+1 end end rcon.print('furnace unit: smeltable items '..#mk..' ('..table.concat(mk,', ')..'), table entries wired '..n)").replace("BATCH", str(BATCH))
HEAD = ("local s=game.surfaces['SURF'] local f=game.forces.player local W=defines.wire_connector_id local X,Y,P,D=OX,OY,PITCH,DEPTH "
        "local function at(n,dx,dy) return s.find_entities_filtered{name=n,position={X+dx,Y+dy},radius=0.6}[1] end local o={} "
        "local function wire(a,ia,b,ib) a.get_wire_connector(ia,true).connect_to(b.get_wire_connector(ib,true),false) end ")
CONFIG = HEAD + (
    "local rp,cc=at('roboport',2,2),at('constant-combinator',5.5,6.5) "
    "local cats=prototypes.entity['assembling-machine-3'].crafting_categories local seen,list,rec={},{},{} for name,r in pairs(f.recipes) do local p=r.prototype local okc=false for _,c in pairs(p.categories) do if cats[c] then okc=true end end "
    "if r.enabled and okc and not p.hidden and #r.products==1 and r.products[1].type=='item' and not name:find('science%-pack') and not name:find('recycling') then local solid=true for _,i in pairs(r.ingredients) do if i.type~='item' then solid=false end end local it=r.products[1].name "
    "if solid then if seen[it] then seen[it]=2 else seen[it]=1 list[#list+1]=it rec[it]=r end end end end local mk={} for _,it in pairs(list) do if seen[it]==1 then mk[#mk+1]=it end end "
    "local cb=cc.get_or_create_control_behavior() while cb.sections_count>0 do cb.remove_section(1) end local sec=cb.add_section() local k=0 for _,it in pairs(list) do if seen[it]==1 then k=k+1 if k>900 then break end sec.set_slot(k,{value={type='item',name=it,quality='normal'},min=1}) end end o[#o+1]='makeable items '..k "
    "local rc=rp.get_or_create_control_behavior() rc.read_items_mode=defines.control_behavior.roboport.read_items_mode.missing_requests rc.read_robot_stats=false "
    "local demand=rp.get_wire_connector(W.circuit_red,true) local ns=0 "
    "local rp2,neg,gate=at('roboport',2,16),at('arithmetic-combinator',4.5,1),at('decider-combinator',4.5,3) rp2.get_or_create_control_behavior().read_items_mode=defines.control_behavior.roboport.read_items_mode.logistics rp2.get_or_create_control_behavior().read_robot_stats=false "
    "for _,id in pairs{W.combinator_input_red,W.combinator_input_green,W.combinator_output_red,W.combinator_output_green} do neg.get_wire_connector(id,true).disconnect_all() gate.get_wire_connector(id,true).disconnect_all() end "
    "wire(neg,W.combinator_input_red,rp2,W.circuit_red) neg.get_or_create_control_behavior().parameters={first_signal={type='virtual',name='signal-each'},second_constant=-1,operation='*',output_signal={type='virtual',name='signal-each'}} "
    "wire(gate,W.combinator_input_green,neg,W.combinator_output_green) gate.get_or_create_control_behavior().parameters={conditions={{first_signal={type='virtual',name='signal-each'},comparator='>',constant=0}},outputs={{signal={type='virtual',name='signal-each'},copy_count_from_input=true}}} "
    "gate.get_wire_connector(W.combinator_output_red,true).connect_to(demand,false) local gin=gate.get_wire_connector(W.combinator_input_green,true) "
    "local sg_ok=function(si) local n=0 for _,w in pairs(si.get_wire_connectors(false) or {}) do n=n+w.connection_count end local sr,sg=si.get_wire_connector(W.circuit_red,true),si.get_wire_connector(W.circuit_green,true) return n==0 or sr.network_id==demand.network_id or sg.network_id==gin.network_id end "
    "for _,si in pairs(s.find_entities_filtered{type='rocket-silo',force=f}) do if sg_ok(si) then si.get_wire_connector(W.circuit_red,true).disconnect_all() si.get_or_create_control_behavior().read_mode=defines.control_behavior.rocket_silo.read_mode.orbital_requests si.get_wire_connector(W.circuit_green,true).connect_to(gin,false) ns=ns+1 end end o[#o+1]='silos read for orbital requests '..ns "
    "local prev,nrom=nil,0 for u=0,D-1 do local ox=P*u local rq,am,dec,sel,ar=at('requester-chest',ox+2.5,6.5),at('assembling-machine-3',ox+2.5,9.5),at('decider-combinator',ox+5.5,8),at('selector-combinator',ox+6.5,8),at('arithmetic-combinator',ox+5.5,11) "
    "for _,id in pairs{W.combinator_input_red,W.combinator_input_green,W.combinator_output_red,W.combinator_output_green} do if u>0 then dec.get_wire_connector(id,true).disconnect_all() end sel.get_wire_connector(id,true).disconnect_all() ar.get_wire_connector(id,true).disconnect_all() end "
    "for _,id in pairs{W.circuit_red,W.circuit_green} do am.get_wire_connector(id,true).disconnect_all() rq.get_wire_connector(id,true).disconnect_all() end "
    "dec.get_wire_connector(W.combinator_input_red,true).connect_to(demand,false) if u>0 then local cp,bo=at('arithmetic-combinator',ox+6.5,11),at('decider-combinator',ox+5.5,13) "
    "for _,id in pairs{W.combinator_input_red,W.combinator_input_green,W.combinator_output_red,W.combinator_output_green} do cp.get_wire_connector(id,true).disconnect_all() bo.get_wire_connector(id,true).disconnect_all() end "
    "wire(bo,W.combinator_input_red,dec,W.combinator_output_red) wire(bo,W.combinator_input_green,prev,W.circuit_green) "
    "bo.get_or_create_control_behavior().parameters={conditions={{first_signal={type='virtual',name='signal-each'},first_signal_networks={red=true,green=false},comparator='>',constant=0},"
    "{first_signal={type='virtual',name='signal-each'},first_signal_networks={red=false,green=true},comparator='>',constant=0,compare_type='and'}},outputs={{signal={type='virtual',name='signal-each'},copy_count_from_input=false,constant=10000000}}} "
    "wire(bo,W.combinator_output_red,dec,W.combinator_output_red) end "
    "wire(dec,W.combinator_input_green,cc,W.circuit_green) "
    "dec.get_or_create_control_behavior().parameters={conditions={{first_signal={type='virtual',name='signal-each'},first_signal_networks={red=true,green=false},comparator='>',constant=0},"
    "{first_signal={type='virtual',name='signal-each'},first_signal_networks={red=false,green=true},comparator='>',constant=0,compare_type='and'}},outputs={{signal={type='virtual',name='signal-each'},copy_count_from_input=false,constant=1000000}}} "
    "ar.get_wire_connector(W.combinator_input_red,true).connect_to(demand,false) ar.get_or_create_control_behavior().parameters={first_signal={type='virtual',name='signal-each'},second_constant=-1,operation='*',output_signal={type='virtual',name='signal-each'}} wire(ar,W.combinator_output_red,dec,W.combinator_output_red) "
    "wire(sel,W.combinator_input_red,dec,W.combinator_output_red) sel.get_or_create_control_behavior().parameters={operation='select',select_max=true,index_constant=0} "
    "wire(am,W.circuit_green,sel,W.combinator_output_green) local ab=am.get_or_create_control_behavior() ab.circuit_set_recipe=true ab.circuit_read_ingredients=false "
    "local qb=rq.get_or_create_control_behavior() qb.set_requests=true qb.read_contents=false rq.get_logistic_point(defines.logistic_member_index.logistic_container).trash_not_requested=true "
    "for i,it in pairs(mk) do local d=s.find_entities_filtered{name='decider-combinator',position={X+u*35+(i-1)%35+0.5,Y+25+math.floor((i-1)/35)*2+1},radius=0.3}[1] if d then local outs={} "
    "for _,ing in pairs(rec[it].ingredients) do outs[#outs+1]={signal={type='item',name=ing.name},copy_count_from_input=false,constant=ing.amount*BATCH} end "
    "d.get_or_create_control_behavior().parameters={conditions={{first_signal={type='item',name=it},comparator='>',constant=0}},outputs=outs} "
    "for _,id in pairs{W.combinator_input_red,W.combinator_input_green,W.combinator_output_red,W.combinator_output_green} do d.get_wire_connector(id,true).disconnect_all() end "
    "wire(d,W.combinator_input_green,sel,W.combinator_output_green) wire(d,W.combinator_output_green,rq,W.circuit_green) nrom=nrom+1 end end prev=rq end o[#o+1]='machines wired '..D..', recipe table entries wired '..nrom rcon.print(table.concat(o,', '))").replace("BATCH", str(BATCH))
ROM = HEAD + ("local cats=prototypes.entity['assembling-machine-3'].crafting_categories local seen,list={},{} for name,r in pairs(f.recipes) do local p=r.prototype local okc=false for _,c in pairs(p.categories) do if cats[c] then okc=true end end "
              "if r.enabled and okc and not p.hidden and #r.products==1 and r.products[1].type=='item' and not name:find('science%-pack') and not name:find('recycling') then local solid=true for _,i in pairs(r.ingredients) do if i.type~='item' then solid=false end end local it=r.products[1].name "
              "if solid then if seen[it] then seen[it]=2 else seen[it]=1 list[#list+1]=it end end end end local n=0 for _,it in pairs(list) do if seen[it]==1 then n=n+1 end end "
              "local made,had,bad=0,0,0 if not f.recipes['decider-combinator'].enabled then rcon.print('decider not researched') return end for u=0,D-1 do for i=1,n do local pos={X+u*35+(i-1)%35+0.5,Y+25+math.floor((i-1)/35)*2+1} "
              "if s.find_entities_filtered{name='decider-combinator',position=pos,radius=0.3}[1] then had=had+1 elseif s.can_place_entity{name='decider-combinator',position=pos,force=f,build_check_type=defines.build_check_type.manual} then "
              "if APPLY then s.create_entity{name='decider-combinator',position=pos,force=f,quality='epic'} end made=made+1 else bad=bad+1 end end end rcon.print('recipe table: '..n..' entries a machine, placed '..made..', already there '..had..', blocked '..bad)")
STATUS = HEAD + (
    "local function sig(ent,id,max) local n=ent.get_circuit_network(id) local t={} if n and n.signals then local l=n.signals table.sort(l,function(a,b) return a.count>b.count end) for i,x in pairs(l) do if i<=max then t[#t+1]=x.signal.name..' '..x.count end end end return table.concat(t,', ') end "
    "local function inv(c) local t={} for _,it in pairs(c.get_inventory(defines.inventory.chest).get_contents()) do t[#t+1]=it.name..' '..it.count end return table.concat(t,', ') end "
    "o[#o+1]='demand (top 10): '..sig(at('decider-combinator',5.5,8),W.combinator_input_red,10) "
    "for u=0,D-1 do local ox=P*u local am,rq,pv,sel=at('assembling-machine-3',ox+2.5,9.5),at('requester-chest',ox+2.5,6.5),at('passive-provider-chest',ox+2.5,12.5),at('selector-combinator',ox+6.5,8) "
    "local k='?' for a,v in pairs(defines.entity_status) do if v==am.status then k=a end end local r=am.get_recipe() "
    "o[#o+1]='machine '..(u+1)..': '..(r and r.name or 'no recipe')..', '..k..', made '..am.products_finished..' | chosen: '..sig(sel,W.combinator_output_green,1)..' | wants: '..sig(rq,W.circuit_green,6)..' | blue chest: '..inv(rq)..' | red chest: '..inv(pv) end rcon.print(table.concat(o,' ;; '))")


def main():
    step, planet = sys.argv[1], sys.argv[2]
    apply = "--apply" in sys.argv
    x, y = SITES[planet]

    def run(code):
        return tools["run_lua"](code.replace("SURF", planet).replace("OX", str(x)).replace("OY", str(y)).replace("PITCH", str(PITCH)).replace("DEPTH", str(DEPTH)))

    if step == "build":
        first = int(sys.argv[sys.argv.index("--from") + 1]) if "--from" in sys.argv else 0
        ents = stock_stage(planet) if "--stock" in sys.argv else layout(planet, first) + (stock_stage(planet) if first == 0 else [])
        r = json.loads(tools["place_entities"](json.dumps(ents), surface=planet, dry_run=not apply))
        print("placed" if apply else "dry run", r.get("placed"), "failed", json.dumps(r.get("failed") or [])[:400])
    if step == "furnace":
        n = int(run("local f=game.forces.player " + SMELT + "rcon.print(#mk)").strip())
        r = json.loads(tools["place_entities"](json.dumps(furnace_layout(planet, n)), surface=planet, dry_run=not apply)) if "--config" not in sys.argv else {}
        print("placed" if apply else "dry run", r.get("placed"), "failed", json.dumps(r.get("failed") or [])[:400])
        if apply or "--config" in sys.argv:
            print(run(FURNACE.replace("FX", str(FX))))
    if step == "rom":
        print(run(ROM.replace("APPLY", "true" if apply else "false")))
    if step == "config" or (step in ("build", "rom") and apply):
        print(run(CONFIG))
    elif step == "status":
        print(run(STATUS).replace(" ;; ", "\n"))


if __name__ == "__main__":
    main()
