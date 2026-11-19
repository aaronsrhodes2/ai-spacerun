#!/usr/bin/env python3
"""Edgerunner MEND after a breach (2026-11-18: both flanks holed on the Gleba -> Nauvis leg, Nauvis out of rocket parts, hub out of foundation).

  revive   every entity ghost whose tiles all have deck is revived by script (collectors and turned railguns, whose box reaches over open
           space by design, once no tile ghost is left near them; the game's own rules decide) (a placed entity is free; revive keeps filters and wires).
  peel N   lifts up to N tiles of UNUSED deck from the two free wedges north of the station (rows -35..-12, |x| >= 16), working inward from
           each row's outer end and stopping three tiles short of anything built, and puts the foundation in the hub. The hub then lays the
           tile ghosts of the breach from it. The ship's own deck, moved; nothing is created. A row is only shortened from its open end, so
           nothing is cut off.
  status   ghosts, damage, empty turrets
Usage: edge_mend.py status ; edge_mend.py revive ; edge_mend.py peel 800"""
import json
import sys

import triangle_miner as TM
from _game import tools

L = tools["run_lua"]

REVIVE = (TM.AT + "local n,wait,fail=0,0,0 for _,g in pairs(s.find_entities_filtered{type='entity-ghost'}) do local b=g.bounding_box local ok=true "
          "for y=math.floor(b.left_top.y+0.05),math.floor(b.right_bottom.y-0.05) do for x=math.floor(b.left_top.x+0.05),math.floor(b.right_bottom.x-0.05) do if s.get_tile(x,y).name~='space-platform-foundation' then ok=false end end end "
          "if g.ghost_name=='asteroid-collector' or g.ghost_name=='railgun-turret' then ok=s.count_entities_filtered{type='tile-ghost',position=g.position,radius=4}==0 end "
          "if ok then local c,e=g.revive() if e then n=n+1 else fail=fail+1 end else wait=wait+1 end end rcon.print('revived '..n..', waiting for deck '..wait..', could not '..fail)")

STATUS = (TM.AT + "local eg,er=0,0 for _,t in pairs(s.find_entities_filtered{name='gun-turret'}) do if t.get_inventory(defines.inventory.turret_ammo).is_empty() then eg=eg+1 end end "
          "local dmg=0 for _,e in pairs(s.find_entities_filtered{force='player'}) do if e.is_entity_with_health and e.get_health_ratio()<1 then dmg=dmg+1 end end local inv=p.hub.get_inventory(defines.inventory.hub_main) "
          "rcon.print('entity ghosts '..s.count_entities_filtered{type='entity-ghost'}..' | tile ghosts '..s.count_entities_filtered{type='tile-ghost'}..' | damaged '..dmg..' | empty guns '..eg..' | hub: foundation '..inv.get_item_count('space-platform-foundation')..', uranium rounds '..inv.get_item_count('uranium-rounds-magazine')..' | asteroids near '..s.count_entities_filtered{type='asteroid'}..' | paused '..tostring(p.paused)..' at '..(p.space_location and p.space_location.name or 'flying'))")

SCAN = (TM.AT + "local rows={} for y=-35,-12 do local r={} for x=-75,75 do local c=' ' if s.get_tile(x,y).name=='space-platform-foundation' then c='.' if s.count_entities_filtered{area={{x+0.05,y+0.05},{x+0.95,y+0.95}}}>0 then c='#' end end r[#r+1]=c end rows[#rows+1]=table.concat(r) end rcon.print(helpers.table_to_json(rows))")


def peel(n):
    rows = json.loads(L(SCAN))
    take = []
    for j, row in enumerate(rows):
        y = -35 + j
        for side in (-1, 1):
            xs = range(-75, -15) if side < 0 else range(75, 15, -1)
            run = []
            started = False
            for x in xs:
                c = row[x + 75]
                if c == " " and not started:
                    continue
                started = True
                if c != ".":
                    break
                run.append(x)
            # stop three tiles short of whatever ended the run, and never touch a tile next to something built on the rows around it
            run = run[:-3] if len(run) > 3 else []
            for x in run:
                near = False
                for dj in (-1, 0, 1):
                    if 0 <= j + dj < len(rows):
                        for dx in (-1, 0, 1):
                            if 0 <= x + dx + 75 < 151 and rows[j + dj][x + dx + 75] == "#":
                                near = True
                if near:
                    break
                take.append((x, y))
    take = take[:n]
    if not take:
        return print("nothing to peel")
    lst = "{" + ",".join("{%d,%d}" % t for t in take) + "}"
    print(L(TM.AT + "local inv=p.hub.get_inventory(defines.inventory.hub_main) local n=0 local t={} for _,q in pairs(" + lst + ") do if s.get_tile(q[1],q[2]).name=='space-platform-foundation' and s.count_entities_filtered{area={{q[1]+0.05,q[2]+0.05},{q[1]+0.95,q[2]+0.95}}}==0 then t[#t+1]={name='empty-space',position={q[1],q[2]}} end end "
            "s.set_tiles(t) n=#t local put=inv.insert{name='space-platform-foundation',count=n} rcon.print('deck tiles lifted from the wedges '..n..', foundation put in the hub '..put)"))


def main():
    a = sys.argv[1:]
    step = a[0] if a else "status"
    if step == "status":
        print(L(STATUS))
    elif step == "revive":
        print(L(REVIVE))
    elif step == "peel":
        peel(int(a[1]) if len(a) > 1 else 400)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
