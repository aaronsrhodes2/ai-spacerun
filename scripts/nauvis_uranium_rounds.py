#!/usr/bin/env python3
"""Nauvis: a dedicated line for URANIUM ROUNDS, Edgerunner's gun ammunition (the Captain, 2026-11-18: "uranium rounds to protect the frame").
Uranium rounds are a continuous consumable, so they get a line of their own and not the Replicator (rule of 2026-11-14); the Replicator
had the order for ten minutes and made none (it takes the smallest order first).
  recipe   1 piercing rounds magazine + 1 uranium-238 -> 1 uranium rounds magazine, 10 s. Nauvis holds 24,000 magazines and 172,000 U-238.
  unit     blue requester chest (start of the line: 400 magazines, 400 U-238) -> inserter -> assembling machine 3 -> inserter -> red
           passive provider chest (end of the line), limited to 3 stacks so the line stops at 300 rounds a unit.
  block    N units side by side, two substations, a wall ring and a hazard-concrete floor (tile ghosts: robots lay them from stock).
The silos send the rounds up when Edgerunner's hub asks (request group `edge-ammo 37`); a rocket carries 25.
Steps: plan | build [--apply] | config | status
Usage: nauvis_uranium_rounds.py plan ; nauvis_uranium_rounds.py build --apply ; nauvis_uranium_rounds.py status"""
import sys

import triangle_miner as TM
from _game import tools
from edge_works import T

L = tools["run_lua"]
X0, Y0, W, H = -378, -253, 32, 15         # free ground west of the silos, inside the robot network (searched 2026-11-18)
N_UNITS = 8
N, E, S, WEST = 0, 4, 8, 12


def units():
    return [X0 + 5 + 3 * k for k in range(N_UNITS)]


def layout():
    e = []
    for x in range(X0, X0 + W):
        e += [T("stone-wall", x, Y0), T("stone-wall", x, Y0 + H - 1)]
    for y in range(Y0 + 1, Y0 + H - 1):
        e += [T("stone-wall", X0, y), T("stone-wall", X0 + W - 1, y)]
    e += [T("substation", X0 + 9, Y0 + 2, 0, 2, 2), T("substation", X0 + 21, Y0 + 2, 0, 2, 2)]
    for cx in units():
        e += [T("requester-chest", cx, Y0 + 5), T("bulk-inserter", cx, Y0 + 6, N),
              T("assembling-machine-3", cx - 1, Y0 + 7, 0, 3, 3, "uranium-rounds-magazine"),
              T("bulk-inserter", cx, Y0 + 10, N), T("passive-provider-chest", cx, Y0 + 11)]
    return e


XS = "{" + ",".join(str(x) for x in units()) + "}"
CONFIG = ("local s=game.surfaces.nauvis local n,r=0,0 for _,cx in pairs(" + XS + ") do "
          "local b=s.find_entities_filtered{name='requester-chest',position={cx+0.5,%d+0.5},radius=0.3}[1] if b then local pt=b.get_logistic_point(defines.logistic_member_index.logistic_container) "
          "local sec=pt.sections[1] or pt.add_section() sec.set_slot(1,{value={type='item',name='piercing-rounds-magazine',quality='normal',comparator='='},min=400}) "
          "sec.set_slot(2,{value={type='item',name='uranium-238',quality='normal',comparator='='},min=400}) n=n+1 end "
          "local c=s.find_entities_filtered{name='passive-provider-chest',position={cx+0.5,%d+0.5},radius=0.3}[1] if c then c.get_inventory(defines.inventory.chest).set_bar(4) r=r+1 end end "
          "rcon.print('requester chests set '..n..', provider chests limited to 3 stacks '..r)") % (Y0 + 5, Y0 + 11)
FLOOR = ("local s=game.surfaces.nauvis local n=0 for x=%d,%d do for y=%d,%d do local nm=((x+y)%%2==0) and 'refined-hazard-concrete-left' or 'refined-hazard-concrete-right' "
         "if s.get_tile(x,y).name:find('hazard')==nil and s.count_entities_filtered{type='tile-ghost',position={x+0.5,y+0.5},radius=0.3}==0 then "
         "if s.create_entity{name='tile-ghost',inner_name='refined-hazard-concrete-left',position={x,y},force='player'} then n=n+1 end end end end rcon.print('floor tile ghosts '..n)") % (X0 + 1, X0 + W - 2, Y0 + 1, Y0 + H - 2)
STATUS = ("local s=game.surfaces.nauvis local m={} for k,v in pairs(defines.entity_status) do m[v]=k end local st={} local made=0 "
          "for _,a in pairs(s.find_entities_filtered{name='assembling-machine-3',area={{%d,%d},{%d,%d}}}) do local k=tostring(m[a.status]) st[k]=(st[k] or 0)+1 made=made+a.products_finished end "
          "local have=0 for _,c in pairs(s.find_entities_filtered{name='passive-provider-chest',area={{%d,%d},{%d,%d}}}) do have=have+c.get_inventory(defines.inventory.chest).get_item_count('uranium-rounds-magazine') end "
          "local net=s.find_logistic_network_by_position({%d,%d},'player') local t={} for k,v in pairs(st) do t[#t+1]=k..' '..v end "
          "rcon.print('assemblers: '..table.concat(t,', ')..' | made '..made..' | in the red chests '..have..' | in the network '..(net and net.get_item_count('uranium-rounds-magazine') or -1)..' | floor ghosts left '..s.count_entities_filtered{type='tile-ghost',area={{%d,%d},{%d,%d}}})"
          ) % (X0, Y0, X0 + W, Y0 + H, X0, Y0, X0 + W, Y0 + H, X0 + 5, Y0 + 5, X0, Y0, X0 + W, Y0 + H)


def main():
    a = sys.argv[1:]
    step = a[0] if a else "status"
    if step in ("plan", "build"):
        apply = step == "build" and "--apply" in a
        ok, bad = TM.place(layout(), apply, surf="nauvis")
        print("placed" if apply else "dry run: would place", ok, "of", len(layout()), "failed", bad)
        if apply:
            print(L(CONFIG))
            print(L(FLOOR))
    elif step == "config":
        print(L(CONFIG))
    elif step == "status":
        print(L(STATUS))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
