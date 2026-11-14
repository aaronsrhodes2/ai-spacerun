#!/usr/bin/env python3
"""Batteries from the wheels' surplus sulfur (the Captain, 2026-11-13: "Yes, batteries"; waste is an opportunity). Sulfur sat at the
hub's cap with no product; Fulgora was asking for 330 batteries.
It stands in the west end of the blue block (scripts/wheel_blue.py; coordinates below are that block's local ones, local 0,0 =
wheel 57,-29), in the free rows just south of the K belt (local row -1):
  supply   the K loop of the blue block (carbon, sulfur, calcite) now also carries iron plates and copper plates (TARGETS in
           wheel_blue.py; everything else that takes from K has a filtered inserter). K is a loop, so what is not taken comes round
           again. The first try used the ore line O: its feed passes only once and the plates then circled the cluster for ever.
           The plates are the cast ones the hub stocks since scripts/wheel_goods.py.
  acid     chemical plant 3..5, 1..3 facing west: sulfur and an iron plate from the K belt (inserter 4,0), water from the block's
           water main by three pipes (0..2, 3)
  battery  chemical plant 6..8, 1..3 facing west, side by side with the acid plant: acid passes port to port, no pipe. Iron plate
           (inserter 6,0) and copper plate (inserter 8,0) from the K belt.
  out      inserter 9,2 onto a belt that dives under the feed belt and the water main (10,5 to 10,9) and side-loads onto the blue
           line's pack belt at 10,14, which already runs into the hub
  cap      that inserter is wired to the hub (over reach) and works while the hub holds fewer than CAP batteries; behind it the
           battery plant fills up, then the acid plant: nothing is thrown away
Steps on every wheel (--only PLANET): check | build [--apply] | config | status. Never apply twice. After a quality upgrade: config.
Run `wheel_blue.py config` once after changing its TARGETS (done on all four wheels on 2026-11-13).
Usage: wheel_battery.py check | build [--apply] | config | status  [--only PLANET]"""
import sys

from _game import tools
from _wheels import place_all, wheels

Q = {"quality": "epic"}
N, E, S, W = 0, 4, 8, 12
OX, OY = 57, -29
CAP = 2000
ents, cfg, recipes = [], [], []


def put(name, tx, ty, w=1, h=1, d=N, filt=None, recipe=None, **params):
    e = {"name": name, "x": tx + OX + w / 2, "y": ty + OY + h / 2, "direction": d, "params": dict(Q, **params)}
    ents.append(e)
    if filt:
        cfg.append((e["x"], e["y"], filt))
    if recipe:
        recipes.append((e["x"], e["y"], recipe))
    return e


def layout():
    for x in (0, 1, 2):
        put("pipe", x, 3)                                               # water from the main's column at -1
    put("chemical-plant", 3, 1, 3, 3, d=W, recipe="sulfuric-acid")
    put("chemical-plant", 6, 1, 3, 3, d=W, recipe="battery")
    put("fast-inserter", 4, 0, d=N, filt=["sulfur", "iron-plate"])
    put("fast-inserter", 6, 0, d=N, filt=["iron-plate"])
    put("fast-inserter", 8, 0, d=N, filt=["copper-plate"])
    put("fast-inserter", 9, 2, d=W, filt=["battery"])
    for y in (2, 3, 4):
        put("express-transport-belt", 10, y, d=S)
    put("express-underground-belt", 10, 5, d=S, type="input")
    put("express-underground-belt", 10, 9, d=S, type="output")
    for y in (10, 11, 12, 13):
        put("express-transport-belt", 10, y, d=S)
    return {"entities": len(ents)}


CONFIG = ("local s=game.surfaces['SURF'] local hub=s.platform.hub local W=defines.wire_connector_id local n,r=0,0 for _,q in pairs(FILT) do local i=s.find_entities_filtered{type='inserter',position={q[1],q[2]},radius=0.3}[1] "
          "if i then i.use_filters=true i.inserter_filter_mode='whitelist' local ok={} for k,name in pairs(q[3]) do i.set_filter(k,name) ok[name]=true end n=n+1 local h=i.held_stack if h.valid_for_read and not ok[h.name] then hub.insert{name=h.name,count=h.count,quality=h.quality} h.clear() end end end "
          "for _,q in pairs(REC) do local m=s.find_entities_filtered{name='chemical-plant',position={q[1],q[2]},radius=0.5}[1] if m then m.set_recipe(q[3]) r=r+1 end end "
          "pcall(function() hub.get_or_create_control_behavior().read_contents=true end) local g=s.find_entities_filtered{type='inserter',position={GX,GY},radius=0.3}[1] local gw=g.get_wire_connector(W.circuit_red,true) gw.disconnect_all() "
          "gw.connect_to(hub.get_wire_connector(W.circuit_red,true),false) local cb=g.get_or_create_control_behavior() cb.circuit_enable_disable=true cb.circuit_condition={first_signal={type='item',name='battery'},comparator='<',constant=CAP} "
          "rcon.print('inserters filtered '..n..', recipes '..r..', cap wired '..tostring(gw.connection_count>0))")
STATUS = ("local s=game.surfaces['SURF'] local inv=s.platform.hub.get_inventory(defines.inventory.hub_main) local o={} for _,q in pairs(REC) do local m=s.find_entities_filtered{name='chemical-plant',position={q[1],q[2]},radius=0.5}[1] "
          "local k='?' for a,v in pairs(defines.entity_status) do if v==m.status then k=a end end local fl={} for n,v in pairs(m.get_fluid_contents()) do fl[#fl+1]=n..' '..math.floor(v) end o[#o+1]=q[3]..': '..k..', made '..m.products_finished..(#fl>0 and (' ['..table.concat(fl,', ')..']') or '') end "
          "local f=game.forces.player.get_item_production_statistics(s) local t={} for _,n in pairs{'battery','sulfur','iron-plate','copper-plate','ice'} do t[#t+1]=n..' '..inv.get_item_count(n) end "
          "rcon.print(table.concat(o,' | ')..' | batteries a minute '..string.format('%.1f',f.get_flow_count{name='battery',category='input',precision_index=defines.flow_precision_index.one_minute})..' (10 min window '"
          "..string.format('%.1f',f.get_flow_count{name='battery',category='input',precision_index=defines.flow_precision_index.ten_minutes})..') | in hub: '..table.concat(t,', '))")


def main():
    step = sys.argv[1]
    apply = "--apply" in sys.argv
    print(layout())
    if step == "check":
        return
    filt = "{" + ",".join("{%s,%s,{%s}}" % (x, y, ",".join("'%s'" % f for f in fl)) for x, y, fl in cfg) + "}"
    rec = "{" + ",".join("{%s,%s,'%s'}" % r for r in recipes) + "}"
    for name, planet, surface, turrets in wheels():
        print("==", name, surface or "(not created)")
        if not surface:
            continue
        if step == "build":
            ok, bad = place_all(ents, surface, apply)
            print("placed" if apply else "dry run", ok, "failed", bad)
        if step == "config" or (step == "build" and apply):
            print(tools["run_lua"](CONFIG.replace("SURF", surface).replace("FILT", filt).replace("REC", rec).replace("GX", str(9 + OX + .5)).replace("GY", str(2 + OY + .5)).replace("CAP", str(CAP))))
        elif step == "status":
            print(tools["run_lua"](STATUS.replace("SURF", surface).replace("REC", rec)))


if __name__ == "__main__":
    main()
