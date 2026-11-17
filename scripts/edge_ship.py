#!/usr/bin/env python3
"""The edge ship = Edgerunner, platform-14, called Nauvis Triangle 1 until 2026-11-16 (the Captain, 2026-11-16: "arm the whole triangle", ammunition made on board). Design and stages:
docs/fusion-and-galaxy-edge-plan.md. This script is STAGE 1: turret pads and an outward ammunition belt on a stretch of both slanted sides.

A slanted side, seen from its outer edge inward (left side: west to east; the right side is the mirror):
  edge       the outer strip tile (collector inserters stand here every 26 rows)
  edge+1     the chunk belt (existing, flows down to the base)
  edge+2     the AMMUNITION belt (new): a staircase beside the chunk belt, flowing UP toward the apex; a dead end at the top row, so it backs up in order
  edge+3     the turret's feed inserter, on the turret's top row (picked so the belt takes no sideways step there)
  edge+4...  the turret: gun 2x2, rocket 3x3, railgun 3x4 facing north (it turns only a fifth of a circle and the ship flies north)
Turrets take only the ammunition they can fire, so one mixed belt serves all three kinds; an inserter stops when its turret is full.
Foundation for the pads is laid as TILE GHOSTS (the hub builds them from its own stock and asks for more, as the frame was built); entities go on once it stands.
Pattern on a 100-row stretch (rows from the stretch's top): guns at 5, 20, 35, 50, 65, 80, 95; rockets at 10, 40, 70; railguns at 25, 55, 85.

Steps: plan [Y0 ROWS] | deck [Y0 ROWS] | build [Y0 ROWS] | status [Y0 ROWS] | load [Y0 ROWS] N   (default stretch: Y0 -555, 100 rows)
  plan    counts, the foundation still missing, what stands in the way (read-only)
  deck    lays the tile ghosts
  build   removes substations that stand on the ammunition lane (foundation carries power on a platform), places belt, inserters and turrets
  status  turrets by state and ammunition, belt contents
  load N  TEST ONLY: moves N firearm magazines and N explosive rockets from the Nauvis network onto the bottom of each ammunition belt
Usage: edge_ship.py plan | deck | build | status | load 40"""
import json
import sys

import triangle_miner as TM
from _game import tools

L = tools["run_lua"]
Q = "legendary"
GUNS, ROCKETS, RAILS = (5, 20, 35, 50, 65, 80, 95), (10, 40, 70), (25, 55, 85)
SIZE = {"gun-turret": (2, 2), "rocket-turret": (3, 3), "railgun-turret": (3, 4)}


def edge(y, side):
    lo, hi = TM.row_span(y)
    return lo if side < 0 else hi


def stretch(y0, rows, side):
    """(belt cells bottom to top with directions, turrets, inserters, tiles needed) for one side."""
    s = 1 if side < 0 else -1                      # inward step
    a = {y: edge(y, side) + 2 * s for y in range(y0 - 1, y0 + rows + 1)}
    path = []
    for y in range(y0 + rows - 1, y0 - 1, -1):     # bottom row first, going north
        path.append((a[y], y))
        if y > y0 and a[y - 1] != a[y]:
            path.append((a[y - 1], y))             # the sideways step, on the lower row
    belts = []
    for i, c in enumerate(path):
        n = path[i + 1] if i + 1 < len(path) else (c[0], c[1] - 1)
        belts.append((c[0], c[1], TM.DIRS[(n[0] - c[0], n[1] - c[1])]))
    turrets, inserters, tiles = [], [], set(path)
    used = set(path)
    for name, offs in (("gun-turret", GUNS), ("rocket-turret", ROCKETS), ("railgun-turret", RAILS)):
        w, h = SIZE[name]
        for off in offs:
            if off + h > rows:
                continue
            y = y0 + off
            for cand in (y, y + 1, y - 1, y + 2):   # a row where the ammunition belt takes no step beside the inserter
                if a[cand - 1] == a[cand] and cand + h <= y0 + rows:
                    y = cand
                    break
            ix = edge(y, side) + 3 * s
            x0 = edge(y, side) + 4 * s if side < 0 else edge(y, side) + 4 * s - (w - 1)
            # the railgun's collision box runs 0.1 past its fourth row (y -1.9 .. +2.1 about the centre), so it needs deck under a FIFTH row (found 2026-11-16: "blocked")
            cells = {(x0 + i, y + j) for i in range(w) for j in range(h + (1 if name == "railgun-turret" else 0))}
            if (ix, y) in used or cells & used:
                print("skipped", name, "at row", y, "(collides)")
                continue
            turrets.append((name, x0, y, w, h))
            inserters.append((ix, y, 12 if side < 0 else 4))
            used |= cells | {(ix, y)}
            tiles |= cells | {(ix, y)}
    return belts, turrets, inserters, tiles


def both(y0, rows):
    out = {}
    for side in (-1, 1):
        out[side] = stretch(y0, rows, side)
    return out


def lua_cells(cells):
    return "{" + ",".join("{%d,%d}" % c for c in sorted(cells)) + "}"


def plan(y0, rows, show=True):
    sides = both(y0, rows)
    tiles = set().union(*(v[3] for v in sides.values()))
    belt_cells = set().union(*({(b[0], b[1]) for b in v[0]} for v in sides.values()))
    r = L(TM.AT + "local need,ghost=0,0 for _,q in pairs(" + lua_cells(tiles) + ") do if s.get_tile(q[1],q[2]).name~='space-platform-foundation' then need=need+1 "
          "if s.count_entities_filtered{name='tile-ghost',position={q[1]+0.5,q[2]+0.5},radius=0.3}>0 then ghost=ghost+1 end end end "
          "local blk={} for _,q in pairs(" + lua_cells(tiles) + ") do for _,e in pairs(s.find_entities_filtered{area={{q[1]+0.1,q[2]+0.1},{q[1]+0.9,q[2]+0.9}}}) do "
          "if e.type~='tile-ghost' then blk[e.name]=(blk[e.name] or 0)+1 end end end local t={} for k,v in pairs(blk) do t[#t+1]=k..' '..v end "
          "rcon.print(need..'|'..ghost..'|'..table.concat(t,', ')..'|'..p.hub.get_inventory(defines.inventory.hub_main).get_item_count('space-platform-foundation'))")
    need, ghost, blk, stock = r.split("|")
    if show:
        for side, (belts, turrets, inserters, _) in sides.items():
            kinds = {}
            for t in turrets:
                kinds[t[0]] = kinds.get(t[0], 0) + 1
            print("side %+d: ammunition belt %d tiles, turrets %s" % (side, len(belts), kinds))
        print("tiles used %d, foundation missing %s (ghosts already laid %s), hub holds %s foundations" % (len(tiles), need, ghost, stock))
        print("in the way now (tile hits by entity):", blk or "nothing")
    return sides, tiles, int(need)


def deck(y0, rows):
    _, tiles, need = plan(y0, rows, show=False)
    r = L(TM.AT + "local n=0 for _,q in pairs(" + lua_cells(tiles) + ") do if s.get_tile(q[1],q[2]).name~='space-platform-foundation' and "
          "s.count_entities_filtered{name='tile-ghost',position={q[1]+0.5,q[2]+0.5},radius=0.3}==0 then "
          "if s.create_entity{name='tile-ghost',inner_name='space-platform-foundation',position={q[1],q[2]},force='player'} then n=n+1 end end end rcon.print(n)")
    print("foundation missing %d, tile ghosts laid %s" % (need, r.strip()))


def build(y0, rows):
    sides, tiles, need = plan(y0, rows, show=False)
    if need:
        sys.exit("foundation still missing on %d tiles: run `deck` and wait for the hub to lay it" % need)
    print("save:", tools["save_game"]("pre-edge-stage1"))
    print(L(TM.AT + "local n=0 for _,q in pairs(" + lua_cells(tiles) + ") do for _,e in pairs(s.find_entities_filtered{name='substation',area={{q[1]+0.1,q[2]+0.1},{q[1]+0.9,q[2]+0.9}}}) do "
            "if e.valid then e.destroy() n=n+1 end end end rcon.print('substations removed from the lane: '..n)"))
    ents = []
    for side, (belts, turrets, inserters, _) in sides.items():
        ents += [{"name": "express-transport-belt", "x": x + 0.5, "y": y + 0.5, "direction": d, "params": {"quality": Q}} for x, y, d in belts]
        ents += [{"name": "bulk-inserter", "x": x + 0.5, "y": y + 0.5, "direction": d, "params": {"quality": Q}} for x, y, d in inserters]
        ents += [{"name": n, "x": x + w / 2, "y": y + h / 2, "direction": 0, "params": {"quality": Q}} for n, x, y, w, h in turrets]
    ok, bad = TM.place(ents, True)
    print("placed", ok, "of", len(ents), "failed", bad)


STATUS = (TM.AT + "local m={} for k,v in pairs(defines.entity_status) do m[v]=k end local o={} local c={} for _,e in pairs(s.find_entities_filtered{type={'ammo-turret','electric-turret'},area={{-200,Y0-2},{200,Y1+2}}}) do "
          "local inv=e.get_inventory(defines.inventory.turret_ammo) local am=0 if inv then for _,i in pairs(inv.get_contents()) do am=am+i.count end end local k=e.name..' '..tostring(m[e.status])..(am>0 and ' armed' or ' empty') c[k]=(c[k] or 0)+1 end "
          "local t={} for k,v in pairs(c) do t[#t+1]=k..' x'..v end table.sort(t) o[#o+1]=table.concat(t,string.char(10)) local items={} for _,b in pairs(s.find_entities_filtered{name='express-transport-belt',area={{-200,Y0-2},{200,Y1+2}}}) do "
          "for li=1,2 do for _,i in pairs(b.get_transport_line(li).get_contents()) do if not i.name:find('chunk') then items[i.name]=(items[i.name] or 0)+i.count end end end end local it={} for k,v in pairs(items) do it[#it+1]=k..' '..v end "
          "o[#o+1]='ammunition on belts: '..(#it>0 and table.concat(it,', ') or 'none') local np=0 for _,e in pairs(s.find_entities_filtered{area={{-200,Y0-2},{200,Y1+2}}}) do if e.status==defines.entity_status.no_power or e.status==defines.entity_status.low_power then np=np+1 end end "
          "o[#o+1]='without power in the stretch: '..np rcon.print(table.concat(o,string.char(10)))")


def status(y0, rows):
    print(L(STATUS.replace("Y0", str(y0)).replace("Y1", str(y0 + rows))))


def load(y0, rows, n):
    """TEST ONLY: real ammunition moved from the Nauvis network onto the bottom tiles of each ammunition belt (nothing is created)."""
    sides = both(y0, rows)
    for side, (belts, _, _, _) in sides.items():
        cells = "{" + ",".join("{%d,%d}" % (b[0], b[1]) for b in belts[:60]) + "}"
        print("side %+d:" % side, L(TM.AT + "local N=game.surfaces.nauvis local net=N.find_logistic_network_by_position({-314,-170},game.forces.player) local put={} "
              "for _,it in pairs({'firearm-magazine','explosive-rocket'}) do local want=%d local got=net.remove_item({name=it,count=want}) local left=got "
              "for _,q in pairs(%s) do local b=s.find_entities_filtered{name='express-transport-belt',position={q[1]+0.5,q[2]+0.5},radius=0.3}[1] if b and left>0 then for li=1,2 do local tl=b.get_transport_line(li) "
              "for pos=0.1,0.9,0.25 do if left>0 and tl.can_insert_at(pos) and tl.insert_at(pos,{name=it,count=1}) then left=left-1 end end end end end "
              "if left>0 then net.insert({name=it,count=left}) end put[#put+1]=it..' '..(got-left) end rcon.print(table.concat(put,', '))" % (n, cells)))


def main():
    a = sys.argv[1:]
    step = a[0] if a else "plan"
    nums = [int(x) for x in a[1:] if x.lstrip("-").isdigit()]
    y0, rows = (nums[0], nums[1]) if len(nums) >= 2 else (TM.Y_TOP, 100)
    if step == "plan":
        plan(y0, rows)
    elif step == "deck":
        deck(y0, rows)
    elif step == "build":
        build(y0, rows)
    elif step == "status":
        status(y0, rows)
    elif step == "load":
        load(y0, rows, nums[-1] if len(nums) in (1, 3) else 40)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
