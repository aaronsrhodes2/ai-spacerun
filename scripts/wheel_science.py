#!/usr/bin/env python3
"""Space science on every wheel, the first pack line (the Captain, 2026-11-13: "Yes, pack lines").
It stands in the north avenue of the round centre (scripts/wheel_hub.py), widened by taking out the 21 cargo bays west of it.
  hub edge   three filtered inserters take carbon, iron ore and ice out of the hub (tiles 0..2 of the north edge); the product belt still
             comes in through one bulk inserter (tile 3)
  feed       carbon and ice side-load onto one belt, a lane each, which runs west along row -10 and north up column -9; the ore dives
             under that junction and runs north up column 1
  units      eight, north to south: ore -> electric furnace -> plates straight into an assembler (space science), which takes carbon and ice
             from the feed belt; a long-handed inserter lifts the packs over the feed belt onto the return belt (column -10)
  return     runs north, then east along row -39 into a splitter on the avenue's product belt with input priority, so packs go into the hub
             ahead of ore (side-loading them onto the product belt jammed: its one lane was already full and six assemblers stopped)
The avenue belt carries packs only: `clear` cuts the north crushers' product belt off it (tiles 3,-40 and 3,-39), because one inserter fed a
mixed belt moved about 3 packs a second and the line makes 5. The step `products` gives the north crushers their own way in. Nothing is thrown away: every belt is a dead end, and a full hub stops the line.
Steps, each on every wheel (--only gleba|nauvis for one):
  check   the layout only
  clear   removes the bays, lamps and old hub-edge pieces in the way
  build   dry run; build --apply places. Never apply twice on the same wheel.
  config  filters and recipes
  products --apply   run once after build: bridges the west avenue with a bay, frees the hub's north edge and brings the north
          crushers' products in there, so they work again
  status  what the line is doing
Usage: wheel_science.py check | clear | build [--apply] | config | status  [--only PLANET]"""
import sys

from wheel import Q
from _game import tools
from _wheels import place_all, wheels

N, E, S, W = 0, 4, 8, 12
UNITS = 8
ents, cfg, recipes, occ, late = [], [], [], {}, []
BAYS = [(tx + 2, ty + 2) for tx in (-12, -8, -4) for ty in range(-36, -8, 4)]


def put(name, tx, ty, w=1, h=1, d=N, filt=None, recipe=None, **params):
    for c in [(tx + i, ty + j) for i in range(w) for j in range(h)]:
        assert c not in occ, "%s at %s overlaps %s" % (name, c, occ[c])
        occ[c] = name
    p = dict(Q)
    p.update(params)
    e = {"name": name, "x": tx + w / 2, "y": ty + h / 2, "direction": d, "params": p}
    ents.append(e)
    if filt:
        cfg.append((e["x"], e["y"], filt))
    if recipe:
        recipes.append((e["x"], e["y"], recipe))


def belt(tx, ty, d):
    put("express-transport-belt", tx, ty, d=d)


def layout():
    put("fast-inserter", 0, -5, d=S, filt=["carbon"])                 # out of the hub
    put("fast-inserter", 1, -5, d=S, filt=["iron-ore"])
    put("fast-inserter", 2, -5, d=S, filt=["ice"])
    put("bulk-inserter", 3, -5, d=N)                                  # products in
    belt(3, -6, S)
    for y in (-6, -7, -8):
        belt(0, y, N)
        belt(2, y, N)
    belt(0, -9, E)                                                    # carbon from the west, ice from the east: a lane each
    belt(2, -9, W)
    belt(1, -9, N)
    for x in range(1, -9, -1):
        belt(x, -10, W)
    for y in range(-10, -37, -1):
        belt(-9, y, N)
    put("express-underground-belt", 1, -6, d=N, type="input")         # ore under the junction
    put("express-underground-belt", 1, -11, d=N, type="output")
    for y in range(-12, -37, -1):
        belt(1, y, N)
    for j in range(UNITS):
        y0 = -36 + 3 * j
        put("fast-inserter", 0, y0 + 1, d=E, filt=["iron-ore"])
        put("electric-furnace", -3, y0, 3, 3)
        put("fast-inserter", -4, y0 + 1, d=E)
        put("assembling-machine-3", -7, y0, 3, 3, recipe="space-science-pack")
        put("fast-inserter", -8, y0, d=W, filt=["carbon", "ice"])
        put("long-handed-inserter", -8, y0 + 2, d=E, filt=["space-science-pack"])
    for y in range(-13, -39, -1):
        belt(-10, y, N)
    for x in range(-10, 2):                                           # the return belt joins the product belt through a splitter that lets packs
        belt(x, -39, E)                                               # in first: one bulk inserter is all the hub edge left for coming in
    belt(2, -39, S)
    put("express-splitter", 2, -38, 2, 1, d=S)
    first = len(ents)                                                 # --- step `products`: the north crushers back into the hub ---
    put("cargo-bay", -36, -4, 4, 4)                                   # a bay bridging the west avenue joins the north-west bays to the
    put("express-underground-belt", -37, -4, d=E, type="input")       # south-west ones, so the bay on the hub's north edge can go and
    put("express-underground-belt", -32, -4, d=E, type="output")      # its four edge tiles take inserters; the avenue belt dives under
    belt(3, -40, W)                                                   # the whole north product row now flows west ...
    for y in range(-40, -9):
        belt(-12, y, S)                                               # ... down the west side of the science line ...
    for x in range(-12, -1):
        belt(x, -9, E)
    for y in (-9, -8, -7):
        belt(-1, y, S)
    for x in range(-1, -5, -1):
        belt(x, -6, W)                                                # ... to four bulk inserters on the freed edge tiles
        put("bulk-inserter", x, -5, d=N)
    late.extend(ents[first:])
    return {"entities": len(ents), "units": UNITS}


CLEAR = ("local s=game.surfaces['SURF'] local n,l=0,0 for _,p in pairs(BAYS) do local b=s.find_entities_filtered{name='cargo-bay',position=p,radius=0.5}[1] if b then b.destroy() n=n+1 end end "
         "for _,e in pairs(s.find_entities_filtered{name='small-lamp',area={{-12,-39},{3,-5}}}) do e.destroy() l=l+1 end "
         "local h=0 for _,e in pairs(s.find_entities_filtered{type={'inserter','transport-belt'},area={{0.1,-5.9},{3.9,-4.1}}}) do e.destroy() h=h+1 end "
         "for _,y in pairs{-37.5,-38.5,-39.5} do for _,e in pairs(s.find_entities_filtered{type='transport-belt',position={3.5,y},radius=0.3}) do e.destroy() h=h+1 end end "
         "local inv=s.platform.hub.get_inventory(defines.inventory.hub_main) rcon.print('bays removed '..n..', lamps '..l..', hub-edge pieces '..h..', hub slots '..#inv..' free '..inv.count_empty_stacks())")
CONFIG = ("local s=game.surfaces['SURF'] local n,r=0,0 for _,q in pairs(FILT) do local i=s.find_entities_filtered{type='inserter',position={q[1],q[2]},radius=0.3}[1] if i then i.use_filters=true i.inserter_filter_mode='whitelist' "
          "for k,name in pairs(q[3]) do i.set_filter(k,name) end n=n+1 end end for _,sp in pairs(s.find_entities_filtered{type='splitter',position={3,-37.5},radius=1}) do sp.splitter_input_priority='right' end for _,q in pairs(REC) do local m=s.find_entities_filtered{type='assembling-machine',position={q[1],q[2]},radius=0.5}[1] if m then m.set_recipe(q[3]) r=r+1 end end "
          "rcon.print('inserters filtered '..n..', recipes '..r)")
PRODUCTS = ("local s=game.surfaces['SURF'] local hub=s.platform.hub local n=0 local function gone(e) if e.type=='transport-belt' then for l=1,2 do for _,it in pairs(e.get_transport_line(l).get_contents()) do hub.insert{name=it.name,count=it.count,quality=it.quality} end end end e.destroy() n=n+1 end "
            "for _,e in pairs(s.find_entities_filtered{type={'transport-belt','lamp'},area={{-36.9,-3.9},{-31.1,-0.1}}}) do gone(e) end "
            "for _,e in pairs(s.find_entities_filtered{type='lamp',area={{-12.9,-39.9},{-0.1,-5.1}}}) do if e.position.x<-11 or e.position.y>-10 then gone(e) end end "
            "for _,e in pairs(s.find_entities_filtered{type='transport-belt',area={{-11.9,-39.9},{2.9,-39.1}}}) do e.direction=defines.direction.west end "
            "for _,e in pairs(s.find_entities_filtered{type='transport-belt',position={-11.5,-39.5},radius=0.3}) do gone(e) end rcon.print('removed '..n)")
UNBAY = ("local s=game.surfaces['SURF'] local b=s.find_entities_filtered{name='cargo-bay',position={-2,-6},radius=0.5}[1] if b then b.destroy() end local inv=s.platform.hub.get_inventory(defines.inventory.hub_main) rcon.print('hub slots '..#inv..' free '..inv.count_empty_stacks())")
STATUS = ("local s=game.surfaces['SURF'] local st={} for _,c in pairs(s.find_entities_filtered{name={'assembling-machine-3','electric-furnace'}}) do local k='?' for n,v in pairs(defines.entity_status) do if v==c.status then k=n end end "
          "k=c.name..' '..k st[k]=(st[k] or 0)+1 end local o={} for k,v in pairs(st) do o[#o+1]=k..' '..v end local f=game.forces.player.get_item_production_statistics(s) "
          "local inv=s.platform.hub.get_inventory(defines.inventory.hub_main) "
          "rcon.print(table.concat(o,', ')..' | space science made a minute (10 min window) '..string.format('%.0f',f.get_flow_count{name='space-science-pack',category='input',precision_index=defines.flow_precision_index.ten_minutes})"
          "..', in hub '..inv.get_item_count('space-science-pack')..', hub free slots '..inv.count_empty_stacks())")


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
        if step == "clear":
            print(tools["run_lua"](CLEAR.replace("SURF", surface).replace("BAYS", "{" + ",".join("{%s,%s}" % c for c in BAYS) + "}")))
        elif step == "build":
            ok, bad = place_all([e for e in ents if e not in late], surface, apply)
            print("placed" if apply else "dry run", ok, "failed", bad)
        elif step == "products":                     # after build: bridge first, then the edge bay out, then the belts
            if not apply:
                sys.exit("products changes the wheel at once: pass --apply")
            print(tools["run_lua"](PRODUCTS.replace("SURF", surface)))
            print("bridge", place_all(late[:3], surface, True))
            print(tools["run_lua"](UNBAY.replace("SURF", surface)))
            print("belts", place_all(late[3:], surface, True))
        if step == "config" or (step == "build" and apply):   # straight after placing: an unfiltered hub inserter pulls anything out (sulfur once
                                                               # filled the far end of the ore belt and starved a unit)
            filt = "{" + ",".join("{%s,%s,{%s}}" % (x, y, ",".join("'%s'" % f for f in fl)) for x, y, fl in cfg) + "}"
            rec = "{" + ",".join("{%s,%s,'%s'}" % r for r in recipes) + "}"
            print(tools["run_lua"](CONFIG.replace("SURF", surface).replace("FILT", filt).replace("REC", rec)))
        elif step == "status":
            print(tools["run_lua"](STATUS.replace("SURF", surface)))


if __name__ == "__main__":
    main()
