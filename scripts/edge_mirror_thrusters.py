#!/usr/bin/env python3
"""Edgerunner: copy the east thruster groups to the west half (the Captain, 2026-11-20: "duplicate the thrusters on the right half").

The Captain rebuilt the engines on the east side as two stepped rows of 12 (each thruster 4 right and 2 up from the last, so every one has
open space behind it): group A at x 56..100, y 140..162 and group B at x 199..243, y -131..-109, each with its stepped pipe run.
This copies them mirrored about x = 0 (centre x -> -x), with these facts read from the game:
  * A thruster's inlets are NOT mirror images: fuel is top-left and right-middle, oxidizer top-right and left-middle. A mirrored pipe run
    therefore meets the OTHER inlet: where an east run carries fuel, its west twin carries oxidizer. The thrusters of a stepped row pass
    both fluids along the row, so one pipe per fluid per row is enough (group A east: 67 pipes of fuel, 1 pipe of oxidizer).
  * The west belt staircase beside group B stands one row lower than the east one, so group B is copied with DY = +1.
  * Deck comes from foundation ITEMS: `deck` lays tile ghosts once (skill note: lay once and leave them) and the hub asks for the items.
  * Pipes and thrusters are placed entities (free): `build` places those whose deck is there; run it again as the deck grows.
Steps: plan | deck | build [--apply] | poke [--apply] (wakes tile ghosts the hub has stopped building) | status
Usage: edge_mirror_thrusters.py plan ; edge_mirror_thrusters.py deck ; edge_mirror_thrusters.py build --apply"""
import json
import sys

import triangle_miner as TM
from _game import tools

L = tools["run_lua"]
# name: (east box x0, y0, x1, y1, dy on the west side)
GROUPS = {"A": (40, 130, 112, 166, 0), "B": (118, -137, 252, -66, 1)}

# east thrusters and every pipe on a fluid segment one of them is on, as {name,x,y,quality}
EAST = (TM.AT + "local x0,y0,x1,y1=%d,%d,%d,%d local segs={} local o={} for _,t in pairs(s.find_entities_filtered{type='thruster',area={{x0,y0},{x1,y1}}}) do "
        "for i=1,t.fluids_count do local ok,id=pcall(function() return t.get_fluid_segment_id(i) end) if ok and id then segs[id]=true end end o[#o+1]={n=t.name,x=t.position.x,y=t.position.y,q=t.quality.name} end "
        "for _,e in pairs(s.find_entities_filtered{type={'pipe','pipe-to-ground'},area={{x0-80,y0-10},{x1,y1+80}}}) do local ok,id=pcall(function() return e.get_fluid_segment_id(1) end) "
        "if ok and id and segs[id] then o[#o+1]={n=e.name,x=e.position.x,y=e.position.y,q=e.quality.name,d=e.direction} end end rcon.print(helpers.table_to_json(o))")

# east deck tiles of the box with no deck at the mirrored place, as a list of west {x,y}; also what stands in the way
NEED = (TM.AT + "local x0,y0,x1,y1,dy=%d,%d,%d,%d,%d local o={} for y=y0,y1 do for x=x0,x1 do if s.get_tile(x,y).name=='space-platform-foundation' and s.get_tile(-1-x,y+dy).name~='space-platform-foundation' then o[#o+1]={-1-x,y+dy} end end end "
        "rcon.print(helpers.table_to_json(o))")

GHOST = (TM.AT + "local n,had=0,0 for _,q in pairs({%s}) do local pos={q[1]+0.5,q[2]+0.5} if s.get_tile(q[1],q[2]).name=='space-platform-foundation' then had=had+1 "
         "elseif s.count_entities_filtered{type='tile-ghost',area={{q[1]+0.1,q[2]+0.1},{q[1]+0.9,q[2]+0.9}}}==0 then if s.create_entity{name='tile-ghost',inner_name='space-platform-foundation',position=pos,force='player'} then n=n+1 end end end rcon.print(n..' '..had)")

STATUS = (TM.AT + "local inv=p.hub.get_inventory(defines.inventory.hub_main) local w,e=0,0 for _,t in pairs(s.find_entities_filtered{type='thruster'}) do if t.position.x<0 then w=w+1 else e=e+1 end end "
          "rcon.print('thrusters east '..e..', west '..w..' | tile ghosts '..s.count_entities_filtered{type='tile-ghost'}..' | foundation in the hub '..inv.get_item_count('space-platform-foundation')..' | paused '..tostring(p.paused)..' at '..tostring(p.space_location and p.space_location.name))")

HASDECK = (TM.AT + "local o={} for i,q in pairs({%s}) do local ok=true for y=q[2],q[4] do for x=q[1],q[3] do if s.get_tile(x,y).name~='space-platform-foundation' then ok=false end end end o[i]=ok and 1 or 0 end rcon.print(table.concat(o,''))")


# tile ghosts the hub has stopped building, with whether each touches standing deck: "x,y,1;..."
STUCK = (TM.AT + "local o={} for _,t in pairs(s.find_entities_filtered{type='tile-ghost'}) do local x,y=math.floor(t.position.x),math.floor(t.position.y) local d=0 "
         "for _,q in pairs{{1,0},{-1,0},{0,1},{0,-1}} do if s.get_tile(x+q[1],y+q[2]).name=='space-platform-foundation' then d=1 end end o[#o+1]=x..','..y..','..d end rcon.print(table.concat(o,';'))")
LAY = (TM.AT + "local inv=p.hub.get_inventory(defines.inventory.hub_main) if inv.get_item_count('space-platform-foundation')<1 then rcon.print('no foundation aboard') return end "
       "s.set_tiles({{name='space-platform-foundation',position={%d,%d}}},true,false,false,true) local paid=0 if s.get_tile(%d,%d).name=='space-platform-foundation' then paid=inv.remove{name='space-platform-foundation',count=1} end "
       "rcon.print('laid, foundation taken from the hub '..paid)")


def poke(apply):
    """One tile per connected run of stuck tile ghosts, paid for with one foundation from the hub; the built tile wakes its neighbours
    (the lesson of _us_poke.py). Raw Lua because place_entities does not lay tiles; nothing is created."""
    r = L(STUCK).strip()
    gh = {}
    for c in r.split(";"):
        if c:
            x, y, d = (int(v) for v in c.split(","))
            gh[(x, y)] = d
    seen = set()
    for g in sorted(gh):
        if g in seen:
            continue
        run, todo = [], [g]
        seen.add(g)
        while todo:
            c = todo.pop()
            run.append(c)
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (c[0] + dx, c[1] + dy)
                if n in gh and n not in seen:
                    seen.add(n)
                    todo.append(n)
        heads = [c for c in run if gh[c]]
        if not heads:
            print("  run of %d at %s touches no deck: left alone" % (len(run), run[0]))
        elif apply:
            x, y = heads[0]
            print("  run of %d: %d,%d %s" % (len(run), x, y, L(LAY % (x, y, x, y)).strip()))
        else:
            print("  run of %d: would lay %d,%d" % (len(run), heads[0][0], heads[0][1]))


STANDS = (TM.AT + "local o={} for i,q in pairs({%s}) do o[i]=s.count_entities_filtered{name=q[1],position={q[2],q[3]},radius=0.3}>0 and 1 or 0 end rcon.print(table.concat(o,''))")


def east(g):
    x0, y0, x1, y1, dy = GROUPS[g]
    return json.loads(L(EAST % (x0, y0, x1, y1)))


def west_ents(g):
    dy = GROUPS[g][4]
    out = []
    for e in east(g):
        d = {"name": e["n"], "x": -e["x"], "y": e["y"] + dy, "direction": e.get("d", 0), "params": {"quality": e["q"]}}
        out.append(d)
    return out


def need_tiles(g):
    x0, y0, x1, y1, dy = GROUPS[g]
    r = json.loads(L(NEED % (x0, y0, x1, y1, dy)))
    return [tuple(t) for t in r] if isinstance(r, list) else []


def box(e):
    w, h = (4, 5) if e["name"] == "thruster" else (1, 1)
    x0, y0 = int(round(e["x"] - w / 2)), int(round(e["y"] - h / 2))
    return x0, y0, x0 + w - 1, y0 + h - 1


def main():
    a = sys.argv[1:]
    step = a[0] if a else "plan"
    apply = "--apply" in a
    if step == "status":
        print(L(STATUS).strip())
        return
    if step == "poke":
        poke(apply)
        print(L(STATUS).strip())
        return
    for g in GROUPS:
        ents = west_ents(g)
        tiles = need_tiles(g)
        thr = sum(1 for e in ents if e["name"] == "thruster")
        print("group %s: %d thrusters, %d pipes to copy; %d deck tiles missing on the west side" % (g, thr, len(ents) - thr, len(tiles)))
        if step == "deck":
            n = had = 0
            for i in range(0, len(tiles), 1500):
                r = L(GHOST % ",".join("{%d,%d}" % t for t in tiles[i:i + 1500])).split()
                n, had = n + int(r[0]), had + int(r[1])
            print("  tile ghosts laid %d (already deck %d)" % (n, had))
        elif step == "build":
            flags = ""
            for i in range(0, len(ents), 300):
                flags += L(HASDECK % ",".join("{%d,%d,%d,%d}" % box(e) for e in ents[i:i + 300])).strip()
            ready = [e for e, f in zip(ents, flags) if f == "1"]
            here = ""
            for i in range(0, len(ready), 300):
                here += L(STANDS % ",".join("{'%s',%s,%s}" % (e["name"], e["x"], e["y"]) for e in ready[i:i + 300])).strip()
            ready = [e for e, f in zip(ready, here) if f == "0"]
            print("  to place now %d of %d (the rest stand already or wait for deck)" % (len(ready), len(ents)))
            # pipes first, thrusters last: a thruster placed before its deck neighbours changes nothing, but a failed one is reported
            ready.sort(key=lambda e: e["name"] == "thruster")
            if ready:
                ok, bad = TM.place(ready, apply)
                print("  %s %d, refused %d" % ("placed" if apply else "would place", ok, bad))
    print(L(STATUS).strip())


if __name__ == "__main__":
    main()
