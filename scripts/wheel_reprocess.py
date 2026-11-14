#!/usr/bin/env python3
"""Asteroid reprocessing on every wheel (the Captain, 2026-11-13: with a surplus of some resources and a shortage of others, use the
crusher's reprocessing recipes to get the ratio you need).
Why: the Nauvis Wheel caught 104 metallic, 76 carbonic and 36 oxide chunks a minute; the pack lines used all the carbon and an eighth of
the ore, so the hub stood at 12 carbon while the valve threw ore overboard.
  where    the four free slots between the crushers on each flat of the loop (scripts/wheel_hub.py): 16 crushers a wheel,
           8 metallic, 4 oxide, 4 carbonic. A reprocessing crusher takes its chunk off the loop and puts every chunk it makes back on.
  control  each intake inserter is wired to the hub and works only while the hub holds more than GATE of that chunk's main product
           (iron ore, ice, carbon). So a chunk kind is reshuffled only when its own product is piled up, and the valve
           (scripts/wheel_valve.py, 36,000) is the last resort. With everything piled up all three kinds churn; nothing is short then.
  wires    inserter to hub is far beyond wire reach (connect_to with the reach check off). A quality upgrade drops such wires: run
           `config` again after one.
The lamps of scripts/wheel_lights.py that stood in the slots are removed by `build --apply`.
Steps on every wheel (--only gleba|nauvis): check | build [--apply] | config | balance [--apply] | status. Never apply twice on the same wheel.
Usage: wheel_reprocess.py check | build [--apply] | config | status  [--only PLANET]"""
import sys

from wheel import CHUNKS, Q, turn
from wheel_hub import RL
from _game import tools
from _wheels import place_all, wheels

GATE = 30000
N, S = 0, 8
KIND = {"metallic": ("metallic-asteroid-reprocessing", "metallic-asteroid-chunk", "iron-ore"),
        "oxide": ("oxide-asteroid-reprocessing", "oxide-asteroid-chunk", "ice"),
        "carbonic": ("carbonic-asteroid-reprocessing", "carbonic-asteroid-chunk", "carbon")}
SLOTS = ((-10, "metallic"), (-6, "oxide"), (4, "metallic"), (8, "carbonic"))
ents, crushers, intakes, outs, cells = [], [], [], [], []


def put(name, tx, ty, w, h, d, k):
    tx, ty, w, h, d = turn(tx, ty, w, h, d, k)
    cells.extend((tx + i, ty + j) for i in range(w) for j in range(h))
    e = {"name": name, "x": tx + w / 2, "y": ty + h / 2, "direction": d, "params": dict(Q)}
    ents.append(e)
    return e


def layout():
    for k in range(4):
        for tx, kind in SLOTS:
            rec, chunk, gate = KIND[kind]
            c = put("crusher", tx, -RL + 2, 2, 3, N, k)
            i = put("fast-inserter", tx, -RL + 1, 1, 1, N, k)
            o = put("fast-inserter", tx + 1, -RL + 1, 1, 1, S, k)
            crushers.append((c["x"], c["y"], rec))
            intakes.append((i["x"], i["y"], chunk, gate))
            outs.append((o["x"], o["y"]))
    return {"crushers": len(crushers), "entities": len(ents)}


LAMPS = ("local s=game.surfaces['SURF'] local n=0 for _,p in pairs(CELLS) do for _,e in pairs(s.find_entities_filtered{type='lamp',position=p,radius=0.3}) do e.destroy() n=n+1 end end rcon.print('lamps removed '..n)")
CONFIG = ("local s=game.surfaces['SURF'] local hub=s.platform.hub local W=defines.wire_connector_id local r,a,b=0,0,0 pcall(function() hub.get_or_create_control_behavior().read_contents=true end) "
          "for _,q in pairs(REC) do local m=s.find_entities_filtered{name='crusher',position={q[1],q[2]},radius=0.5}[1] if m then m.set_recipe(q[3]) r=r+1 end end "
          "for _,q in pairs(INS) do local i=s.find_entities_filtered{type='inserter',position={q[1],q[2]},radius=0.3}[1] if i then i.use_filters=true i.inserter_filter_mode='whitelist' i.set_filter(1,q[3]) "
          "i.get_wire_connector(W.circuit_red,true).connect_to(hub.get_wire_connector(W.circuit_red,true),false) local cb=i.get_or_create_control_behavior() cb.circuit_enable_disable=true "
          "cb.circuit_condition={first_signal={type='item',name=q[4]},comparator='>',constant=GATE} if i.get_wire_connector(W.circuit_red,true).connection_count>0 then a=a+1 end end end "
          "for _,q in pairs(OUT) do local i=s.find_entities_filtered{type='inserter',position={q[1],q[2]},radius=0.3}[1] if i then i.use_filters=true i.inserter_filter_mode='whitelist' "
          "for n,c in pairs(CHUNKS) do i.set_filter(n,c) end b=b+1 end end rcon.print('recipes '..r..', intakes wired to the hub '..a..', outputs '..b)").replace("GATE", str(GATE))
STATUS = ("local s=game.surfaces['SURF'] local st={} for _,c in pairs(s.find_entities_filtered{name='crusher'}) do local rc=c.get_recipe() if rc and rc.name:find('reprocessing') then local k='?' for n,v in pairs(defines.entity_status) do if v==c.status then k=n end end "
          "k=rc.name:gsub('%-asteroid%-reprocessing','')..' '..k st[k]=(st[k] or 0)+1 end end local o={} for k,v in pairs(st) do o[#o+1]=k..' '..v end "
          "local inv=s.platform.hub.get_inventory(defines.inventory.hub_main) local f=game.forces.player.get_item_production_statistics(s) "
          "for _,n in pairs{'iron-ore','ice','carbon'} do o[#o+1]=n..' in hub '..inv.get_item_count(n) end "
          "for _,n in pairs{'metallic-asteroid-chunk','carbonic-asteroid-chunk','oxide-asteroid-chunk'} do o[#o+1]=n:sub(1,4)..' chunks used a minute '..string.format('%.0f',f.get_flow_count{name=n,category='output',precision_index=defines.flow_precision_index.one_minute}) end rcon.print(table.concat(o,', '))")

# Step `balance` (2026-11-13, after measuring: the 24 normal crushers stand first on the loop, took the chunks and their ore went overboard;
# only 3 of 8 metallic reprocessors found a chunk). Three deciders at DEC read the hub: a kind is in surplus when BOTH its products are
# above SURPLUS. While it is, the normal crushers of that kind stop and its reprocessors run; otherwise the other way round.
# This replaces the single-product gate of `config`: run `balance` after `config`, and again after a quality upgrade (over-reach wires).
SURPLUS = 32000
DEC = (-23, -46)
PAIRS = (("metallic", "M", "iron-ore", "copper-ore"), ("carbonic", "C", "carbon", "sulfur"), ("oxide", "O", "ice", "calcite"))
BALANCE = ("local s=game.surfaces['SURF'] local hub=s.platform.hub local W=defines.wire_connector_id local o={} pcall(function() hub.get_or_create_control_behavior().read_contents=true end) "
           "local prev_in,prev_out=nil,nil local last=nil for _,q in pairs(PAIRS) do local d=s.find_entities_filtered{name='decider-combinator',position={q[5],q[6]},radius=0.4}[1] "
           "d.get_or_create_control_behavior().parameters={conditions={{first_signal={type='item',name=q[3]},comparator='>',constant=SURPLUS},{first_signal={type='item',name=q[4]},comparator='>',constant=SURPLUS,compare_type='and'}},"
           "outputs={{signal={type='virtual',name='signal-'..q[2]},copy_count_from_input=false,constant=1}}} "
           "local i=d.get_wire_connector(W.combinator_input_green,true) if prev_in then i.connect_to(prev_in,false) else i.connect_to(hub.get_wire_connector(W.circuit_green,true),false) end prev_in=i "
           "local u=d.get_wire_connector(W.combinator_output_red,true) if prev_out then u.connect_to(prev_out,false) end prev_out=u end "
           "local a,b=0,0 for _,c in pairs(s.find_entities_filtered{name='crusher'}) do local r=c.get_recipe() if r then local sig=nil for _,q in pairs(PAIRS) do if r.name:find(q[1],1,true) then sig=q[2] end end "
           "for _,i in pairs(s.find_entities_filtered{type='inserter',position=c.position,radius=3}) do if sig and i.drop_target==c then local w=i.get_wire_connector(W.circuit_red,true) w.disconnect_all() w.connect_to(prev_out,false) "
           "local cb=i.get_or_create_control_behavior() cb.circuit_enable_disable=true local rep=r.name:find('reprocessing',1,true) "
           "cb.circuit_condition={first_signal={type='virtual',name='signal-'..sig},comparator=rep and '>' or '=',constant=0} if rep then a=a+1 else b=b+1 end end end end end "
           "rcon.print('reprocessor intakes '..a..', crusher intakes '..b)").replace("SURPLUS", str(SURPLUS))


def balance(surface, apply):
    import json
    decs = [{"name": "decider-combinator", "x": DEC[0] + i + .5, "y": DEC[1] + 1, "direction": 0, "params": dict(Q)} for i in range(3)]
    have = tools["run_lua"]("rcon.print(game.surfaces['%s'].count_entities_filtered{name='decider-combinator',area={{%s,%s},{%s,%s}}})" % (surface, DEC[0], DEC[1], DEC[0] + 3, DEC[1] + 2)).strip()
    if have == "0":
        r = json.loads(tools["place_entities"](json.dumps(decs), surface=surface, dry_run=not apply))
        print("deciders", "placed" if apply else "dry run", r.get("placed"), r.get("failed") or "")
    if apply:
        pairs = "{" + ",".join("{'%s','%s','%s','%s',%s,%s}" % (k, sg, a, b, DEC[0] + i + .5, DEC[1] + 1) for i, (k, sg, a, b) in enumerate(PAIRS)) + "}"
        print(tools["run_lua"](BALANCE.replace("SURF", surface).replace("PAIRS", pairs)))


def lua(rows):
    return "{" + ",".join("{" + ",".join(("'%s'" % v) if isinstance(v, str) else str(v) for v in r) + "}" for r in rows) + "}"


def main():
    step = sys.argv[1]
    apply = "--apply" in sys.argv
    print(layout())
    if step == "check":
        return
    for name, planet, surface, turrets in wheels():
        print("==", name, surface or "(not created)")
        if not surface:
            continue
        if step == "build":
            if apply:
                print(tools["run_lua"](LAMPS.replace("SURF", surface).replace("CELLS", lua([(x + .5, y + .5) for x, y in cells]))))
            ok, bad = place_all(ents, surface, apply)
            print("placed" if apply else "dry run", ok, "failed", bad)
        if step == "config" or (step == "build" and apply):
            print(tools["run_lua"](CONFIG.replace("SURF", surface).replace("REC", lua(crushers)).replace("INS", lua(intakes)).replace("OUT", lua(outs))
                                   .replace("CHUNKS", "{" + ",".join("'%s'" % c for c in CHUNKS) + "}")))
        elif step == "balance":
            balance(surface, apply)
        elif step == "status":
            print(tools["run_lua"](STATUS.replace("SURF", surface)))


if __name__ == "__main__":
    main()
