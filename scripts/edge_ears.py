#!/usr/bin/env python3
"""Edgerunner RAILGUN EARS (the Captain, 2026-11-18: a railgun damages everything of ours in the cone in front of it; "make the railguns all
the way on the outside of the triangle"; "you have my permission to change the shape of the ship").

WHAT WAS WRONG (measured, `check`): a railgun shot is a LINE 50 tiles long and 1 wide, 10,000 damage to everything on it, ours included.
The 42 flank railguns and the 6 on the apex stretch stood INSIDE the strip (edge+4 .. edge+6) facing north, and each had about 150 of our
own belts, inserters, turrets and collectors inside its arc (range 50, 36 degrees each way). The 29 on the base face south: nothing there.

THE EAR. A railgun turret can be placed in 8 directions. Every north-facing railgun moves to a pad of new deck OUTSIDE the strip, on its
old feed row, facing NORTH-WEST on the west flank and NORTH-EAST on the east flank. Its arc is then 9..81 degrees off north on the outer
side; the strip runs 30 degrees off north on the INNER side toward the apex and 150 degrees toward the base, so nothing of ours can be in
it, at any range. It guards the stretch of flank BELOW itself (an asteroid falling on a point down-flank is up and outward of it).
  feed     the old inner feed inserter stays. Where the old turret stood, a belt leads outward; an underground belt takes the rounds under
           the ammunition belt, the chunk belt and the edge; outside: exit, one bulk inserter (railgun rounds only), the turret.
  turret   centre three tiles outward of the inserter, same row (tested on spare deck: the inserter's drop point is inside the box and
           the box, turned 45 degrees, touches 17 tiles: those are the pad).
  deck     tile ghosts; the hub lays them from its foundation stock.
The old turret is removed by script (a placed entity, no item comes back); its rounds are put in the hub and from there into the new turret
(the ship's own rounds, moved, none created).
NOT COVERED: the nose. An ear guards the flank below it, so the stretch above the topmost ear on each side has no railgun cover.

Steps: check | plan | deck | build [--apply] [--only N] | config | status
Usage: edge_ears.py check ; edge_ears.py plan ; edge_ears.py deck ; edge_ears.py build --apply ; edge_ears.py check"""
import json
import sys

import triangle_miner as TM
from _game import tools

L = tools["run_lua"]
Q = {"quality": "legendary"}
BELT, UG, BULK, RAIL = "express-transport-belt", "express-underground-belt", "bulk-inserter", "railgun-turret"
SPAN = 26                       # tiles scanned outward from the feed inserter
ROWS = 4                        # rows scanned above and below the feed row
MAXHOP = 9                      # express underground belt: exit at most this many tiles from the entrance
# tiles the turned turret touches, as (dx, dy) from its centre tile, read from the game for north-west; north-east is the mirror
NW = {(-1, -2), (0, -2), (-2, -1), (-1, -1), (0, -1), (1, -1), (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0), (-1, 1), (0, 1), (1, 1), (2, 1), (0, 2), (1, 2)}
FREE = " .g"

CHECK = (TM.AT + "local o={} local function w(x) o[#o+1]=x end local R=52 local half=39 local zone={} local tot={} "
         "local face={[0]={0,-1},[2]={0.7071,-0.7071},[4]={1,0},[6]={0.7071,0.7071},[8]={0,1},[10]={-0.7071,0.7071},[12]={-1,0},[14]={-0.7071,-0.7071}} "
         "for _,r in pairs(s.find_entities_filtered{name='railgun-turret'}) do local f=face[r.direction] local cnt=0 "
         "for _,e in pairs(s.find_entities_filtered{position=r.position,radius=R}) do if e~=r and e.is_entity_with_health and e.force==r.force then local dx,dy=e.position.x-r.position.x,e.position.y-r.position.y local d=math.sqrt(dx*dx+dy*dy) "
         "if d>3 and (dx*f[1]+dy*f[2])/d>=math.cos(math.rad(half)) then cnt=cnt+1 tot[e.type]=(tot[e.type] or 0)+1 end end end "
         "local k='facing '..r.direction zone[k]=zone[k] or {0,0,0} zone[k][1]=zone[k][1]+1 zone[k][2]=zone[k][2]+cnt if cnt==0 then zone[k][3]=zone[k][3]+1 end end "
         "local ks={} for k in pairs(zone) do ks[#ks+1]=k end table.sort(ks) for _,k in pairs(ks) do local v=zone[k] w(k..': '..v[1]..' railguns, clean '..v[3]..', own entities in their arcs '..v[2]) end "
         "local t={} for k,v in pairs(tot) do t[#t+1]=k..' '..v end table.sort(t) w('in arcs by type: '..(#t>0 and table.concat(t,', ') or 'nothing')) rcon.print(table.concat(o,string.char(10)))")

SURVEY = (TM.AT + "local ch={['transport-belt']='=',['underground-belt']='u',['splitter']='Y',['inserter']='i',['ammo-turret']='G',['asteroid-collector']='C'} local out={} "
          "for _,r in pairs(s.find_entities_filtered{name='railgun-turret'}) do if r.direction==0 then local side=r.position.x<0 and -1 or 1 local ins local others=0 "
          "for _,i in pairs(s.find_entities_filtered{type='inserter',position=r.position,radius=4}) do if i.drop_target==r then if (i.position.x-r.position.x)*side<0 then ins=i else others=others+1 end end end "
          "local rec={x=r.position.x,y=r.position.y,side=side,ammo=r.get_inventory(defines.inventory.turret_ammo).get_item_count('railgun-ammo'),others=others} "
          "if ins then local ix,iy=math.floor(ins.position.x),math.floor(ins.position.y) rec.ix=ix rec.iy=iy rec.grid={} "
          "for dy=-ROWS,ROWS do local row={} for k=0,SPAN do local x,y=ix+side*k,iy+dy local c=(s.get_tile(x,y).name=='empty-space') and ' ' or '.' "
          "for _,e in pairs(s.find_entities_filtered{area={{x+0.05,y+0.05},{x+0.95,y+0.95}}}) do if e==r then c='R' elseif e.type=='tile-ghost' then if c==' ' then c='g' end else c=ch[e.type] or '?' break end end row[#row+1]=c end "
          "rec.grid[#rec.grid+1]=table.concat(row) end end out[#out+1]=rec end end rcon.print(helpers.table_to_json(out))").replace("ROWS", str(ROWS)).replace("SPAN", str(SPAN))


def survey():
    return sorted(json.loads(L(SURVEY)) or [], key=lambda r: (r["side"], r["y"]))


def plan_one(rec):
    """Where the ear of one railgun goes. Returns (entities, deck tiles, note) or (None, None, why not)."""
    if "grid" not in rec:
        return None, None, "no feed inserter on the inner side"
    side, ix, iy, g = rec["side"], rec["ix"], rec["iy"], rec["grid"]
    row = g[ROWS]
    X = lambda k: ix + side * k
    a = 0
    while a + 1 <= SPAN and row[a + 1] in "R.":
        a += 1
    if a < 1:
        return None, None, "nothing free beside the feed inserter"
    box = NW if side < 0 else {(-dx, dy) for dx, dy in NW}
    b = None
    for k in range(a + 1, SPAN - 6):
        if any(c not in FREE for c in row[k:]):
            continue                                                    # something of ours still further out on this row
        kc = k + 4                                                      # exit k, inserter k+1, turret centre k+4
        cells = [(kc + side * dx, ROWS + dy) for dx, dy in box]         # (index outward, grid row); dx is in real x
        if all(0 <= c[0] <= SPAN and g[c[1]][c[0]] in FREE for c in cells):
            b = k
            break
    if b is None:
        return None, None, "no free place outside"
    if b - a > MAXHOP:
        return None, None, "hop of %d tiles is too long" % (b - a)
    if "u" in row[a + 1:b]:
        return None, None, "another underground belt on the row"
    out_dir, in_dir = (12, 4) if side < 0 else (4, 12)                 # belts flow outward; an inserter's direction is its pick-up side
    e = [TM.E(BELT, X(k) + 0.5, iy + 0.5, out_dir, **Q) for k in range(1, a)]
    e += [TM.E(UG, X(a) + 0.5, iy + 0.5, out_dir, type="input", **Q), TM.E(UG, X(b) + 0.5, iy + 0.5, out_dir, type="output", **Q),
          TM.E(BULK, X(b + 1) + 0.5, iy + 0.5, in_dir, **Q), TM.E(RAIL, X(b + 4) + 0.5, iy + 0.5, 14 if side < 0 else 2, **Q)]
    tiles = {(X(b), iy), (X(b + 1), iy)} | {(X(b + 4) + dx, iy + dy) for dx, dy in box}
    return e, tiles, "belts %d, hop %d, turret centre %d,%d" % (a - 1, b - a, X(b + 4), iy)


def plans():
    out = []
    for rec in survey():
        e, tiles, note = plan_one(rec)
        out.append((rec, e, tiles, note))
    return out


def lua_cells(cells):
    return "{" + ",".join("{%d,%d}" % c for c in sorted(cells)) + "}"


def missing(tiles):
    return json.loads(L(TM.AT + "local need,ghost=0,0 for _,q in pairs(" + lua_cells(tiles) + ") do if s.get_tile(q[1],q[2]).name~='space-platform-foundation' then need=need+1 "
                        "if s.count_entities_filtered{type='tile-ghost',position={q[1]+0.5,q[2]+0.5},radius=0.3}>0 then ghost=ghost+1 end end end "
                        "rcon.print(helpers.table_to_json({need=need,ghost=ghost,stock=p.hub.get_inventory(defines.inventory.hub_main).get_item_count('space-platform-foundation')}))"))


MOVE_OUT = (TM.AT + "local r=s.find_entities_filtered{name='railgun-turret',position={RX,RY},radius=0.3}[1] if not r or r.direction~=0 then rcon.print('no north-facing railgun at RX,RY') else "
            "local inv=r.get_inventory(defines.inventory.turret_ammo) local n=inv.get_item_count('railgun-ammo') local put=0 if n>0 then put=p.hub.get_inventory(defines.inventory.hub_main).insert{name='railgun-ammo',count=n} end "
            "r.destroy() rcon.print('removed, rounds to the hub '..put..' of '..n) end")
CONFIG = (TM.AT + "local hub=p.hub.get_inventory(defines.inventory.hub_main) local n,fed,moved,armed=0,0,0,0 for _,r in pairs(s.find_entities_filtered{name='railgun-turret'}) do if r.direction==14 or r.direction==2 then n=n+1 "
          "local k=0 for _,kind in pairs({'metallic','carbonic','oxide'}) do k=k+1 r.set_priority_target(k,'huge-'..kind..'-asteroid') end r.ignore_unprioritised_targets=true "
          "for _,i in pairs(s.find_entities_filtered{type='inserter',position=r.position,radius=5}) do if i.drop_target==r then fed=fed+1 i.use_filters=true i.inserter_filter_mode='whitelist' i.set_filter(1,{name='railgun-ammo',quality='normal',comparator='='}) end end "
          "local inv=r.get_inventory(defines.inventory.turret_ammo) if inv.is_empty() then local want=math.min(10,hub.get_item_count('railgun-ammo')) if want>0 then local got=r.insert{name='railgun-ammo',count=want} if got>0 then hub.remove{name='railgun-ammo',count=got} moved=moved+got end end end "
          "if not inv.is_empty() then armed=armed+1 end end end rcon.print('ears '..n..', with a feed inserter '..fed..', armed '..armed..', rounds moved in from the hub '..moved..', rounds left in the hub '..hub.get_item_count('railgun-ammo'))")

STATUS = (TM.AT + "local h={} local n=0 for _,r in pairs(s.find_entities_filtered{name='railgun-turret'}) do n=n+1 local k='facing '..r.direction h[k]=h[k] or {0,0} h[k][1]=h[k][1]+1 if r.get_inventory(defines.inventory.turret_ammo).get_item_count()>0 then h[k][2]=h[k][2]+1 end end "
          "local t={} for k,v in pairs(h) do t[#t+1]=k..': '..v[1]..' (armed '..v[2]..')' end table.sort(t) "
          "rcon.print('railguns '..n..' | '..table.concat(t,' | ')..' | tile ghosts '..s.count_entities_filtered{type='tile-ghost'}..' | hub foundations '..p.hub.get_inventory(defines.inventory.hub_main).get_item_count('space-platform-foundation')..', railgun rounds '..p.hub.get_inventory(defines.inventory.hub_main).get_item_count('railgun-ammo'))")


def main():
    a = sys.argv[1:]
    step = a[0] if a else "status"
    if step == "check":
        return print(L(CHECK))
    if step == "status":
        return print(L(STATUS))
    if step == "config":
        return print(L(CONFIG))
    ps = plans()
    good = [p for p in ps if p[1]]
    tiles = set().union(*[p[2] for p in good]) if good else set()
    if step == "plan":
        for rec, e, t, note in ps:
            print("%s railgun %7.1f,%7.1f rounds %2d: %s" % ("west" if rec["side"] < 0 else "east", rec["x"], rec["y"], rec["ammo"], note))
        m = missing(tiles) if tiles else {}
        print("north-facing railguns %d, ears planned %d, deck tiles %d, missing %s" % (len(ps), len(good), len(tiles), m))
    elif step == "deck":
        print(L(TM.AT + "local n=0 for _,q in pairs(" + lua_cells(tiles) + ") do if s.get_tile(q[1],q[2]).name~='space-platform-foundation' and "
                "s.count_entities_filtered{type='tile-ghost',position={q[1]+0.5,q[2]+0.5},radius=0.3}==0 then "
                "if s.create_entity{name='tile-ghost',inner_name='space-platform-foundation',position={q[1],q[2]},force='player'} then n=n+1 end end end rcon.print('tile ghosts laid '..n)").strip())
    elif step == "build":
        apply = "--apply" in a
        only = int(a[a.index("--only") + 1]) if "--only" in a else None
        done = 0
        for rec, e, t, note in good:
            if only is not None and done >= only:
                break
            m = missing(t)
            where = "%.1f,%.1f" % (rec["x"], rec["y"])
            if m["need"]:
                print(where, "waits for deck (%d tiles missing)" % m["need"])
                continue
            if not apply:
                print(where, "ready:", note)
                done += 1
                continue
            print(where, L(MOVE_OUT.replace("RX", str(rec["x"])).replace("RY", str(rec["y"]))).strip())
            ok, bad = TM.place(e, True)
            print("   placed", ok, "of", len(e), "failed", bad)
            done += 1
        print("ears", "built" if apply else "ready", done, "of", len(good))
        if apply:
            print(L(CONFIG))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
