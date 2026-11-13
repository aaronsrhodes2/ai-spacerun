#!/usr/bin/env python3
"""Automation (red) science on every wheel, in the south avenue of the round centre (the Captain, 2026-11-13: pack lines).
Written for the north side like scripts/wheel_science.py, then turned half round (K = 2), so read the numbers as if looking north.
  hub edge   tile 0 iron ore out, tile 1 copper ore out, tile 2 packs in, tile 3 the south crushers' products in
  ore belt   copper goes straight up column 1 (an inserter drops on the right lane of a belt running away from it), iron side-loads
             from the west onto the left lane: one belt, a lane each. It dives under the pack belt at the top, runs west along row -39
             and comes back down column -19 for the second column of units.
  units      six, three each side of the pack belt (column -9). Each: iron furnace -> gear assembler -> pack assembler <- copper furnace,
             all by direct insertion; filtered inserters pick each ore off its lane.
  packs      north up column -9, east along row -37, south down column 2 to their own bulk inserter: a pure belt into the hub
  cap        the two ore inserters switch off above PACKS stored packs
Steps on every wheel (--only gleba|nauvis): check | clear | build [--apply] | config | status. Never apply twice on the same wheel.
Usage: wheel_red.py check | clear | build [--apply] | config | status  [--only PLANET]"""
import sys

from wheel import Q, turn
from _game import tools
from _wheels import place_all, wheels

K = 2
PACKS = 20000
N, E, S, W = 0, 4, 8, 12
ents, cfg, recipes, occ = [], [], [], {}
BAYS = [turn(tx, ty, 4, 4, 0, K)[:2] for tx in range(-20, 0, 4) for ty in range(-36, -8, 4)]
EDGE = [turn(x, y, 1, 1, 0, K)[:2] for x in range(4) for y in (-5, -6)]


def put(name, tx, ty, w=1, h=1, d=N, filt=None, recipe=None, **params):
    tx, ty, w, h, d = turn(tx, ty, w, h, d, K)
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


def unit(y0, m):
    """One unit; m = 1 east of the pack belt (ore belt at column 1), m = -1 the mirror image west of it (ore belt at column -19)."""
    def X(x, w=1):
        return x if m == 1 else -18 - x - (w - 1)
    side = E if m == 1 else W
    put("fast-inserter", X(0), y0 + 1, d=side, filt=["iron-ore"])
    put("fast-inserter", X(0), y0 + 4, d=side, filt=["copper-ore"])
    put("electric-furnace", X(-3, 3), y0, 3, 3)
    put("electric-furnace", X(-3, 3), y0 + 3, 3, 3)
    put("fast-inserter", X(-4), y0 + 1, d=side)
    put("assembling-machine-3", X(-7, 3), y0, 3, 3, recipe="iron-gear-wheel")
    put("fast-inserter", X(-6), y0 + 3, d=N)
    put("assembling-machine-3", X(-7, 3), y0 + 4, 3, 3, recipe="automation-science-pack")
    put("fast-inserter", X(-4), y0 + 5, d=side)
    put("fast-inserter", X(-8), y0 + 5, d=side, filt=["automation-science-pack"])


def layout():
    put("fast-inserter", 0, -5, d=S, filt=["iron-ore"])
    put("fast-inserter", 1, -5, d=S, filt=["copper-ore"])
    put("bulk-inserter", 2, -5, d=N)
    put("bulk-inserter", 3, -5, d=N)
    belt(3, -6, S)
    belt(0, -6, N)
    belt(0, -7, N)
    belt(0, -8, E)
    for y in range(-6, -36, -1):
        belt(1, y, N)
    put("express-underground-belt", 1, -36, d=N, type="input")
    put("express-underground-belt", 1, -38, d=N, type="output")
    for x in range(1, -19, -1):
        belt(x, -39, W)
    for y in range(-39, -16):
        belt(-19, y, S)
    for y0 in (-36, -29, -22):
        unit(y0, 1)
        unit(y0, -1)
    for y in range(-17, -37, -1):
        belt(-9, y, N)
    for x in range(-9, 2):
        belt(x, -37, E)
    for y in range(-37, -5):
        belt(2, y, S)
    return {"entities": len(ents), "units": 6}


def lua_list(cells, off=0.0):
    return "{" + ",".join("{%s,%s}" % (c[0] + off, c[1] + off) for c in cells) + "}"


CLEAR = ("local s=game.surfaces['SURF'] local hub=s.platform.hub local n,l,h=0,0,0 for _,p in pairs(BAYS) do local b=s.find_entities_filtered{name='cargo-bay',position=p,radius=0.5}[1] if b then b.destroy() n=n+1 end end "
         "for _,p in pairs(EDGE) do for _,e in pairs(s.find_entities_filtered{type={'inserter','transport-belt'},position=p,radius=0.3}) do if e.type=='transport-belt' then for i=1,2 do for _,it in pairs(e.get_transport_line(i).get_contents()) do hub.insert{name=it.name,count=it.count,quality=it.quality} end end end e.destroy() h=h+1 end end "
         "for _,p in pairs(TILES) do for _,e in pairs(s.find_entities_filtered{type='lamp',position=p,radius=0.3}) do e.destroy() l=l+1 end end "
         "local inv=hub.get_inventory(defines.inventory.hub_main) rcon.print('bays removed '..n..', lamps '..l..', hub-edge pieces '..h..', hub slots '..#inv..' free '..inv.count_empty_stacks())")
CONFIG = ("local s=game.surfaces['SURF'] local hub=s.platform.hub local W=defines.wire_connector_id local n,r,g=0,0,0 for _,q in pairs(FILT) do local i=s.find_entities_filtered{type='inserter',position={q[1],q[2]},radius=0.3}[1] if i then i.use_filters=true i.inserter_filter_mode='whitelist' "
          "for k,name in pairs(q[3]) do i.set_filter(k,name) end n=n+1 if i.pickup_target==hub then i.get_wire_connector(W.circuit_red,true).connect_to(hub.get_wire_connector(W.circuit_red,true)) local cb=i.get_or_create_control_behavior() cb.circuit_enable_disable=true "
          "cb.circuit_condition={first_signal={type='item',name='automation-science-pack'},comparator='<',constant=PACKS} g=g+1 end end end "
          "for _,q in pairs(REC) do local m=s.find_entities_filtered{type='assembling-machine',position={q[1],q[2]},radius=0.5}[1] if m then m.set_recipe(q[3]) r=r+1 end end rcon.print('inserters filtered '..n..', gated on stored packs '..g..', recipes '..r)").replace("PACKS", str(PACKS))
STATUS = ("local s=game.surfaces['SURF'] local st={} for _,c in pairs(s.find_entities_filtered{name='assembling-machine-3'}) do local rc=c.get_recipe() if rc and rc.name~='space-science-pack' then local k='?' for n,v in pairs(defines.entity_status) do if v==c.status then k=n end end "
          "k=rc.name..' '..k st[k]=(st[k] or 0)+1 end end local o={} for k,v in pairs(st) do o[#o+1]=k..' '..v end local f=game.forces.player.get_item_production_statistics(s) local inv=s.platform.hub.get_inventory(defines.inventory.hub_main) "
          "rcon.print(table.concat(o,', ')..' | red science a minute (10 min window) '..string.format('%.0f',f.get_flow_count{name='automation-science-pack',category='input',precision_index=defines.flow_precision_index.ten_minutes})"
          "..', in hub '..inv.get_item_count('automation-science-pack')..', hub free slots '..inv.count_empty_stacks())")


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
            print(tools["run_lua"](CLEAR.replace("SURF", surface).replace("BAYS", lua_list(BAYS, 2)).replace("EDGE", lua_list(EDGE, .5)).replace("TILES", lua_list(sorted(occ), .5))))
        elif step == "build":
            ok, bad = place_all(ents, surface, apply)
            print("placed" if apply else "dry run", ok, "failed", bad)
        elif step == "config":
            filt = "{" + ",".join("{%s,%s,{%s}}" % (x, y, ",".join("'%s'" % f for f in fl)) for x, y, fl in cfg) + "}"
            rec = "{" + ",".join("{%s,%s,'%s'}" % r for r in recipes) + "}"
            print(tools["run_lua"](CONFIG.replace("SURF", surface).replace("FILT", filt).replace("REC", rec)))
        elif step == "status":
            print(tools["run_lua"](STATUS.replace("SURF", surface)))


if __name__ == "__main__":
    main()
