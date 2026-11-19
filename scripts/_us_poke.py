"""Universal shuttle: wake tile ghosts the hub has stopped building.
Found 2026-11-18: the hub builds a tile ghost when the ghost is laid next to deck or when a neighbouring tile is built. Ghosts that were lifted and
laid again while the hub was at work (my staged deck) are not picked up again: they sit beside standing deck with foundation in the hub. One built
tile wakes its neighbours, one every two seconds, along the whole run. This lays ONE tile per connected run of stuck ghosts with set_tiles and takes one
foundation out of the hub for it (nothing is created; raw Lua because place_entities does not lay tiles).
Usage: _us_poke.py [--apply]"""
import sys

import universal_shuttle as U

r = U.L(U.AT + "local g={} for _,t in pairs(s.find_entities_filtered{type='tile-ghost'}) do g[#g+1]=math.floor(t.position.x)..','..math.floor(t.position.y) end rcon.print(table.concat(g,';'))").strip()
gh = {tuple(int(v) for v in c.split(",")) for c in r.split(";") if c}
have = U.standing()[0]
runs, seen = [], set()
for g in sorted(gh):
    if g in seen:
        continue
    run, todo = [], [g]
    seen.add(g)
    while todo:
        x, y = todo.pop()
        run.append((x, y))
        for dx, dy in U.DIR:
            n = (x + dx, y + dy)
            if n in gh and n not in seen:
                seen.add(n)
                todo.append(n)
    runs.append(run)
print("tile ghosts %d in %d runs" % (len(gh), len(runs)))
for run in runs:
    heads = [c for c in run if any((c[0] + dx, c[1] + dy) in have for dx, dy in U.DIR)]
    if not heads:
        print("  run of %d at %s touches no deck: left alone" % (len(run), run[0]))
        continue
    x, y = heads[0]
    if "--apply" not in sys.argv:
        print("  run of %d: would lay %d,%d" % (len(run), x, y))
        continue
    print("  run of %d:" % len(run), U.L(U.AT + "local inv=hub.get_inventory(defines.inventory.hub_main) if inv.get_item_count('space-platform-foundation')<1 then rcon.print('no foundation aboard') return end "
                                       "s.set_tiles({{name='space-platform-foundation',position={%d,%d}}},true,false,false,true) local paid=0 if s.get_tile(%d,%d).name=='space-platform-foundation' then paid=inv.remove{name='space-platform-foundation',count=1} end "
                                       "rcon.print('laid %d,%d, foundation taken from the hub '..paid)" % (x, y, x, y, x, y)).strip())
