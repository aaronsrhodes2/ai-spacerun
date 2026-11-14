#!/usr/bin/env python3
"""The science sink on Nauvis (the Captain, 2026-11-13: when there is nothing to research the packs back up, one stalled flow stops the
next, "a cascade failure"; so keep chewing up the surplus research in a recycler: "it keeps the lines running and it keeps our
automation flowing". No mods, so the in-game black hole is the recycler).
  pair     two recyclers nose to nose in the same two columns: each one's output lands in the other, so whatever a pack breaks down
           into is recycled again until nothing is left
  intake   a blue requester chest and an inserter into the lower recycler of each pair
  control  the chest's requests are set by circuit: a roboport reads the network's stock (the one of scripts/omni_maker.py), a constant
           combinator lists the science packs, and a decider asks for 400 of every pack the network holds MORE than KEEP of. Below
           KEEP nothing is taken, so the labs and the shuttles always find their packs.
Steps: build [--apply] | config | status. Never apply twice.
Usage: science_sink.py build --apply"""
import json
import sys

from _game import tools

KEEP = 20000
PAIRS = [45, 51, 59, 65]                 # centre x of each pair; lower recycler centre y -394, upper -398
PACKS = ["automation-science-pack", "logistic-science-pack", "military-science-pack", "chemical-science-pack", "production-science-pack",
         "utility-science-pack", "space-science-pack", "metallurgic-science-pack", "electromagnetic-science-pack"]
STOCK = (-28, -384)                      # roboport reading the network's contents
Q = {"quality": "epic"}


def layout(skip_first=False):
    ents = []
    for i, x in enumerate(PAIRS):
        if not (skip_first and i == 0):
            ents.append({"name": "recycler", "x": x, "y": -394, "direction": 0, "params": dict(Q)})
        ents.append({"name": "recycler", "x": x, "y": -398, "direction": 8, "params": dict(Q)})
        ents.append({"name": "fast-inserter", "x": x + 1.5, "y": -393.5, "direction": 4, "params": dict(Q)})
        ents.append({"name": "requester-chest", "x": x + 2.5, "y": -393.5, "direction": 0, "params": dict(Q)})
    ents.append({"name": "constant-combinator", "x": 48.5, "y": -398.5, "direction": 0, "params": dict(Q)})
    ents.append({"name": "decider-combinator", "x": 48.5, "y": -397, "direction": 0, "params": dict(Q)})
    return ents


CONFIG = ("local s=game.surfaces.nauvis local W=defines.wire_connector_id local cc=s.find_entities_filtered{name='constant-combinator',position={48.5,-398.5},radius=0.4}[1] local dec=s.find_entities_filtered{name='decider-combinator',position={48.5,-397},radius=0.6}[1] "
          "local rp=s.find_entities_filtered{name='roboport',position={SX,SY},radius=0.6}[1] local cb=cc.get_or_create_control_behavior() while cb.sections_count>0 do cb.remove_section(1) end local sec=cb.add_section() for i,p in pairs(PACKS) do sec.set_slot(i,{value={type='item',name=p,quality='normal'},min=1}) end "
          "for _,id in pairs{W.combinator_input_red,W.combinator_input_green,W.combinator_output_red,W.combinator_output_green} do dec.get_wire_connector(id,true).disconnect_all() end "
          "dec.get_wire_connector(W.combinator_input_red,true).connect_to(rp.get_wire_connector(W.circuit_red,true),false) dec.get_wire_connector(W.combinator_input_green,true).connect_to(cc.get_wire_connector(W.circuit_green,true),false) "
          "dec.get_or_create_control_behavior().parameters={conditions={{first_signal={type='virtual',name='signal-each'},first_signal_networks={red=true,green=false},comparator='>',constant=KEEP},"
          "{first_signal={type='virtual',name='signal-each'},first_signal_networks={red=false,green=true},comparator='>',constant=0,compare_type='and'}},outputs={{signal={type='virtual',name='signal-each'},copy_count_from_input=false,constant=400}}} local n=0 "
          "for _,x in pairs(XS) do local q=s.find_entities_filtered{name='requester-chest',position={x+2.5,-393.5},radius=0.4}[1] for _,id in pairs{W.circuit_red,W.circuit_green} do q.get_wire_connector(id,true).disconnect_all() end "
          "q.get_wire_connector(W.circuit_green,true).connect_to(dec.get_wire_connector(W.combinator_output_green,true),false) local b=q.get_or_create_control_behavior() b.set_requests=true b.read_contents=false q.get_logistic_point(defines.logistic_member_index.logistic_container).trash_not_requested=true n=n+1 end "
          "rcon.print('sink chests wired '..n..', packs above KEEP are recycled')")
STATUS = ("local s=game.surfaces.nauvis local o={} local net=s.find_logistic_network_by_position({-27.5,-393.5},'player') for _,p in pairs(PACKS) do o[#o+1]=p:gsub('%-science%-pack','')..' '..net.get_item_count(p) end "
          "local t={} for _,r in pairs(s.find_entities_filtered{name='recycler',area={{40,-401},{70,-391}}}) do local k='?' for a,v in pairs(defines.entity_status) do if v==r.status then k=a end end t[k]=(t[k] or 0)+1 end local q={} for k,v in pairs(t) do q[#q+1]=k..' '..v end "
          "local made=0 for _,r in pairs(s.find_entities_filtered{name='recycler',area={{40,-401},{70,-391}}}) do made=made+r.products_finished end rcon.print('stock: '..table.concat(o,', ')..' ;; recyclers: '..table.concat(q,', ')..', recycled so far '..made)")


def sub(code):
    return (code.replace("PACKS", "{" + ",".join("'%s'" % p for p in PACKS) + "}").replace("KEEP", str(KEEP)).replace("XS", "{" + ",".join(str(x) for x in PAIRS) + "}")
            .replace("SX", str(STOCK[0])).replace("SY", str(STOCK[1])))


def main():
    step = sys.argv[1]
    apply = "--apply" in sys.argv
    if step == "build":
        r = json.loads(tools["place_entities"](json.dumps(layout("--skip-first" in sys.argv)), surface="nauvis", dry_run=not apply))
        print("placed" if apply else "dry run", r.get("placed"), "failed", json.dumps(r.get("failed") or [])[:300])
    if step == "config" or (step == "build" and apply):
        print(tools["run_lua"](sub(CONFIG)))
    elif step == "status":
        print(tools["run_lua"](sub(STATUS)).replace(" ;; ", "\n"))


if __name__ == "__main__":
    main()
