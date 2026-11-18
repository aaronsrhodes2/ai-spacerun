#!/usr/bin/env python3
"""Nauvis: dedicated lines for Edgerunner's imported ammunition, one walled block each (the same block as nauvis_uranium_rounds.py, which
built the first one). Continuous consumables get lines of their own, not the Replicator.
  uranium   uranium rounds = piercing magazine + uranium-238            at -378,-253  (built 2026-11-18 by nauvis_uranium_rounds.py)
  rockets   explosive rocket = rocket + 2 explosives                    at -412,-253  (for the Aquilo leg: big asteroids)
A unit: blue requester chest (400 of each ingredient) -> inserter -> assembling machine 3 -> inserter -> red provider chest limited to
3 stacks. Eight units, two substations, wall ring, hazard-concrete floor as tile ghosts. A rocket lifts 25 of either.
Steps: plan LINE | build LINE [--apply] | config LINE | status [LINE]
Usage: nauvis_ammo_line.py plan rockets ; nauvis_ammo_line.py build rockets --apply ; nauvis_ammo_line.py status"""
import sys

import triangle_miner as TM
from _game import tools
from edge_works import T

L = tools["run_lua"]
W, H, N_UNITS = 32, 15, 8
LINES = {"uranium": dict(x0=-378, y0=-253, recipe="uranium-rounds-magazine", product="uranium-rounds-magazine", needs=("piercing-rounds-magazine", "uranium-238")),
         "rockets": dict(x0=-412, y0=-253, recipe="explosive-rocket", product="explosive-rocket", needs=("rocket", "explosives"))}
N = 0


def units(c):
    return [c["x0"] + 5 + 3 * k for k in range(N_UNITS)]


def layout(c):
    x0, y0 = c["x0"], c["y0"]
    e = []
    for x in range(x0, x0 + W):
        e += [T("stone-wall", x, y0), T("stone-wall", x, y0 + H - 1)]
    for y in range(y0 + 1, y0 + H - 1):
        e += [T("stone-wall", x0, y), T("stone-wall", x0 + W - 1, y)]
    e += [T("substation", x0 + 9, y0 + 2, 0, 2, 2), T("substation", x0 + 21, y0 + 2, 0, 2, 2)]
    for cx in units(c):
        e += [T("requester-chest", cx, y0 + 5), T("bulk-inserter", cx, y0 + 6, N), T("assembling-machine-3", cx - 1, y0 + 7, 0, 3, 3, c["recipe"]),
              T("bulk-inserter", cx, y0 + 10, N), T("passive-provider-chest", cx, y0 + 11)]
    return e


def config(c):
    xs = "{" + ",".join(str(x) for x in units(c)) + "}"
    slots = " ".join("sec.set_slot(%d,{value={type='item',name='%s',quality='normal',comparator='='},min=400})" % (i + 1, n) for i, n in enumerate(c["needs"]))
    print(L("local s=game.surfaces.nauvis local n,r=0,0 for _,cx in pairs(" + xs + ") do "
            "local b=s.find_entities_filtered{name='requester-chest',position={cx+0.5,%d+0.5},radius=0.3}[1] if b then local pt=b.get_logistic_point(defines.logistic_member_index.logistic_container) "
            "local sec=pt.sections[1] or pt.add_section() %s n=n+1 end "
            "local ch=s.find_entities_filtered{name='passive-provider-chest',position={cx+0.5,%d+0.5},radius=0.3}[1] if ch then ch.get_inventory(defines.inventory.chest).set_bar(4) r=r+1 end end "
            "local g=0 for x=%d,%d do for y=%d,%d do if s.get_tile(x,y).name:find('hazard')==nil and s.count_entities_filtered{type='tile-ghost',position={x+0.5,y+0.5},radius=0.3}==0 then "
            "if s.create_entity{name='tile-ghost',inner_name='refined-hazard-concrete-left',position={x,y},force='player'} then g=g+1 end end end end "
            "rcon.print('requester chests set '..n..', provider chests limited '..r..', floor tile ghosts '..g)"
            % (c["y0"] + 5, slots, c["y0"] + 11, c["x0"] + 1, c["x0"] + W - 2, c["y0"] + 1, c["y0"] + H - 2)))


def status(name, c):
    a = (c["x0"], c["y0"], c["x0"] + W, c["y0"] + H)
    print(name, L("local s=game.surfaces.nauvis local m={} for k,v in pairs(defines.entity_status) do m[v]=k end local st={} local made=0 "
                  "for _,a in pairs(s.find_entities_filtered{name='assembling-machine-3',area={{%d,%d},{%d,%d}}}) do local k=tostring(m[a.status]) st[k]=(st[k] or 0)+1 made=made+a.products_finished end "
                  "local net=s.find_logistic_network_by_position({%d,%d},'player') local t={} for k,v in pairs(st) do t[#t+1]=k..' '..v end "
                  "rcon.print('assemblers: '..table.concat(t,', ')..' | made '..made..' | in the network '..(net and net.get_item_count('%s') or -1))"
                  % (a + (c["x0"] + 5, c["y0"] + 5, c["product"]))).strip())


if __name__ == "__main__":
    a = sys.argv[1:]
    step = a[0] if a else "status"
    if step == "status":
        for k, c in LINES.items():
            if len(a) < 2 or a[1] == k:
                status(k, c)
    elif step in ("plan", "build", "config"):
        c = LINES[a[1]]
        if step == "config":
            config(c)
        else:
            apply = step == "build" and "--apply" in a
            ok, bad = TM.place(layout(c), apply, surf="nauvis")
            print("placed" if apply else "dry run: would place", ok, "of", len(layout(c)), "failed", bad)
            if apply:
                config(c)
    else:
        sys.exit(__doc__)
