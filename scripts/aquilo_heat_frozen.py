#!/usr/bin/env python3
"""Lay heat pipes so every FROZEN entity of ours on Aquilo touches a WARM heat network (2026-11-14: the north pipe line and pumpjacks were
ghosted with no heat pipes beside them; 115 frozen).

BFS grows from warm heat tiles only (heat pipes >= 100 C, heating towers, reactors). Cold heat pipes (an island not joined to the warm
network) are passable for free: the path runs through them and joins the island. New pipes go on free snow/concrete tiles; NOT on bare
ice-platform (can_place_entity says no there, verified 2026-11-14: pave with concrete first).
Usage: aquilo_heat_frozen.py [--apply] [--box X0 Y0 X1 Y1]"""
import json
import sys
from collections import deque

from _game import tools

FROZEN = ("local s=game.surfaces.aquilo local t={} for _,e in pairs(s.find_entities_filtered{force='player',area={{%d,%d},{%d,%d}}}) do "
          "if e.status==defines.entity_status.frozen then local b=e.bounding_box t[#t+1]=e.name..','..math.floor(b.left_top.x+0.01)..','..math.floor(b.left_top.y+0.01)..','"
          "..(math.ceil(b.right_bottom.x-0.01)-1)..','..(math.ceil(b.right_bottom.y-0.01)-1) end end rcon.print(table.concat(t,';'))")
HEAT = ("local s=game.surfaces.aquilo local w,c={},{} for _,e in pairs(s.find_entities_filtered{name={'heat-pipe','heating-tower','nuclear-reactor'},area={{%d,%d},{%d,%d}}}) do "
        "local bb=e.bounding_box local hot=e.name~='heat-pipe' or e.temperature>=100 for y=math.floor(bb.left_top.y+0.01),math.ceil(bb.right_bottom.y-0.01)-1 do "
        "for x=math.floor(bb.left_top.x+0.01),math.ceil(bb.right_bottom.x-0.01)-1 do if hot then w[#w+1]=x..','..y else c[#c+1]=x..','..y end end end end "
        "rcon.print(table.concat(w,' ')..'|'..table.concat(c,' '))")
FREE = ("local s=game.surfaces.aquilo local ok={['snow-crests']=1,['snow-flat']=1,['snow-lumpy']=1,['snow-patchy']=1,['frozen-concrete']=1,['concrete']=1,['refined-concrete']=1} "
        "local rows={} for y=%d,%d do local r={} for x=%d,%d do local tn=s.get_tile(x,y).name local c=ok[tn] and '.' or (tn=='ice-platform' and 'i' or 'x') "
        "if c~='x' and s.count_entities_filtered{area={{x+0.05,y+0.05},{x+0.95,y+0.95}}}>0 then c='#' end r[#r+1]=c end rows[#rows+1]=table.concat(r) end rcon.print(table.concat(rows,'|'))")


def tiles(s):
    return {tuple(int(v) for v in t.split(",")) for t in s.split() if t}


def adj(t):
    x, y = t
    return ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))


def main():
    apply = "--apply" in sys.argv
    box = (-95, -170, 10, -40)
    if "--box" in sys.argv:
        i = sys.argv.index("--box")
        box = tuple(int(v) for v in sys.argv[i + 1:i + 5])
    x0, y0, x1, y1 = box
    frozen = []
    for r in tools["run_lua"](FROZEN % box).strip().split(";"):
        if r:
            n, a, b, c, d = r.split(",")
            frozen.append((n, {(x, y) for x in range(int(a), int(c) + 1) for y in range(int(b), int(d) + 1)}))
    print("frozen in box:", len(frozen))
    w, c = tools["run_lua"](HEAT % box).strip().split("|")
    warm, cold = tiles(w), tiles(c)
    rows = tools["run_lua"](FREE % (y0, y1, x0, x1)).strip().split("|")
    free = {(x0 + i, y0 + j) for j, row in enumerate(rows) for i, ch in enumerate(row) if ch in ".i"}
    ice = {(x0 + i, y0 + j) for j, row in enumerate(rows) for i, ch in enumerate(row) if ch == "i"}
    print("warm heat tiles %d, cold %d, free %d" % (len(warm), len(cold), len(free)))
    added, stuck = [], 0
    for _ in range(2):
        for name, tl in frozen:
            if any(n in warm for t in tl for n in adj(t)):
                continue
            goal = {n for t in tl for n in adj(t) if n in free or n in cold}
            seen, q, found = {t: None for t in warm}, deque(warm), None
            while q and not found:
                cur = q.popleft()
                for n in adj(cur):
                    if n in seen or not (n in free or n in cold):
                        continue
                    seen[n] = cur
                    if n in goal:
                        found = n
                        break
                    q.append(n)
            if not found:
                stuck += 1
                continue
            cur = found
            while cur is not None and cur not in warm:
                warm.add(cur)
                if cur in free:
                    added.append(cur)
                    free.discard(cur)
                elif cur in cold:   # joining a cold island warms all of it
                    isl, st = set(), [cur]
                    while st:
                        k = st.pop()
                        if k in cold and k not in isl:
                            isl.add(k)
                            st.extend(adj(k))
                    warm |= isl
                    cold -= isl
                cur = seen[cur]
    print("heat pipes to add: %d, frozen with no path: %d" % (len(added), stuck))
    pipes = [{"name": "heat-pipe", "x": x + 0.5, "y": y + 0.5, "direction": 0, "params": {"quality": "epic"}} for x, y in added]
    if not pipes:
        return
    pave = [t for t in added if t in ice]
    print("ice-platform tiles to pave with concrete first:", len(pave))
    if apply and pave:
        print(tools["save_game"]("skippy"))
        lst = ",".join("{%d,%d}" % t for t in pave)
        print(tools["run_lua"]("local s=game.surfaces.aquilo local n=s.find_logistic_networks_by_construction_area({%d,%d},'player')[1] local tl={} for _,p in pairs({%s}) do "
                               "if n.remove_item{name='concrete',count=1}==1 then tl[#tl+1]={name='concrete',position=p} end end s.set_tiles(tl,true,true,true,true) rcon.print('paved '..#tl)"
                               % (pave[0][0], pave[0][1], lst)))
    r = json.loads(tools["place_entities"](json.dumps(pipes), surface="aquilo", dry_run=not apply))
    print("placed" if apply else "dry run", r.get("placed"), "failed", len(r.get("failed") or []), json.dumps((r.get("failed") or [])[:4]))


if __name__ == "__main__":
    main()
