#!/usr/bin/env python3
"""A robot-fed mall on Nauvis for building items (the Captain, 2026-11-13: trashed and spare items should reach the planet that needs them;
Nauvis held 540,000 iron plate and 446,000 advanced circuits but no poles, inserters, turrets or repair packs to ship).
  site   40 x 17 tiles of free ground at X0,Y0 inside the main robot network
  unit   blue requester chest -> inserter -> assembling machine 3 -> inserter -> red provider chest (chest rules: blue starts a line,
         red ends it). The requester asks for CRAFTS crafts' worth of each ingredient; the provider chest is barred to BAR slots, so a
         unit stops when its stock stands. Intermediates (gear, stick, pipe, inserter, fast inserter) are units too: robots carry them on.
  rows   two rows of 13 units, mirrored about a strip with three substations
Nothing is spawned: every ingredient comes out of the network, made by the factory.
Steps: check | build [--apply] | config | status. Never apply twice.
Usage: nauvis_mall.py check | build [--apply] | config | status"""
import json
import sys

from _game import tools

X0, Y0 = -70, -394
CRAFTS, BAR = 10, 2
Q = {"quality": "epic"}
N, S = 0, 8
ITEMS = ["iron-gear-wheel", "iron-stick", "pipe", "inserter", "fast-inserter", "long-handed-inserter", "bulk-inserter",
         "medium-electric-pole", "big-electric-pole", "substation", "laser-turret", "repair-pack", "small-lamp",
         "constant-combinator", "decider-combinator", "arithmetic-combinator", "pump", "roboport", "construction-robot",
         "passive-provider-chest", "requester-chest", "steel-chest", "pipe-to-ground", "radar", "beacon", "electric-mining-drill"]
ents, units = [], []


def put(name, tx, ty, w=1, h=1, d=N):
    ents.append({"name": name, "x": tx + w / 2, "y": ty + h / 2, "direction": d, "params": dict(Q)})


def layout():
    for i, item in enumerate(ITEMS):
        col, top = i % 13, i < 13
        ux = X0 + 3 * col
        ys = (Y0, Y0 + 1, Y0 + 2, Y0 + 5, Y0 + 6) if top else (Y0 + 16, Y0 + 15, Y0 + 12, Y0 + 11, Y0 + 10)
        d = N if top else S
        put("requester-chest", ux + 1, ys[0])
        put("fast-inserter", ux + 1, ys[1], d=d)
        put("assembling-machine-3", ux, ys[2], 3, 3)
        put("fast-inserter", ux + 1, ys[3], d=d)
        put("passive-provider-chest", ux + 1, ys[4])
        units.append((ux + 1.5, ys[0] + .5, ux + 1.5, ys[2] + 1.5, ux + 1.5, ys[4] + .5, item))
    for sx in (5, 19, 33):
        put("substation", X0 + sx, Y0 + 7, 2, 2)
    return {"units": len(units), "entities": len(ents)}


CONFIG = ("local s=game.surfaces.nauvis local f=game.forces.player local n=0 local bad={} for _,u in pairs(UNITS) do local m=s.find_entities_filtered{name='assembling-machine-3',position={u[3],u[4]},radius=0.5}[1] "
          "local rq=s.find_entities_filtered{name='requester-chest',position={u[1],u[2]},radius=0.3}[1] local pv=s.find_entities_filtered{name='passive-provider-chest',position={u[5],u[6]},radius=0.3}[1] local r=f.recipes[u[7]] "
          "if m and rq and pv and r and r.enabled then m.set_recipe(u[7]) local lp=rq.get_logistic_point(defines.logistic_member_index.logistic_container) local sec=lp.get_section(1) or lp.add_section() local k=0 "
          "for _,ing in pairs(r.ingredients) do if ing.type=='item' then k=k+1 sec.set_slot(k,{value={type='item',name=ing.name,quality='normal'},min=ing.amount*CRAFTS}) else bad[#bad+1]=u[7]..' needs '..ing.name end end "
          "pv.get_inventory(defines.inventory.chest).set_bar(BAR+1) n=n+1 else bad[#bad+1]=u[7]..' not set' end end rcon.print('units set '..n..' '..table.concat(bad,', '))").replace("CRAFTS", str(CRAFTS)).replace("BAR", str(BAR))
STATUS = ("local s=game.surfaces.nauvis local o={} for _,u in pairs(UNITS) do local m=s.find_entities_filtered{name='assembling-machine-3',position={u[3],u[4]},radius=0.5}[1] local pv=s.find_entities_filtered{name='passive-provider-chest',position={u[5],u[6]},radius=0.3}[1] "
          "if m then local k='?' for a,v in pairs(defines.entity_status) do if v==m.status then k=a end end o[#o+1]=u[7]..' '..k..' made '..m.products_finished..' stock '..(pv and pv.get_inventory(defines.inventory.chest).get_item_count() or -1) end end rcon.print(table.concat(o,' ; '))")


def lua_units():
    return "{" + ",".join("{%s,%s,%s,%s,%s,%s,'%s'}" % u for u in units) + "}"


def main():
    step = sys.argv[1]
    apply = "--apply" in sys.argv
    print(layout())
    if step == "build":
        r = json.loads(tools["place_entities"](json.dumps(ents), surface="nauvis", dry_run=not apply))
        print("placed" if apply else "dry run", r.get("placed"), "failed", json.dumps(r.get("failed") or [])[:400])
    if step == "config" or (step == "build" and apply):
        print(tools["run_lua"](CONFIG.replace("UNITS", lua_units())))
    elif step == "status":
        print(tools["run_lua"](STATUS.replace("UNITS", lua_units())).replace(" ; ", "\n"))


if __name__ == "__main__":
    main()
