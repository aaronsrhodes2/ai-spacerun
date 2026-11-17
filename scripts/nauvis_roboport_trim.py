#!/usr/bin/env python3
"""Trim the Nauvis roboport grid to what is needed (the Captain, 2026-11-16: "too many drone ports ... maximize coverage and minimize power and machine use;
roboports connected to signal wires stay where they are").
A roboport is removed only if, without it:
  1 every occupied 8x8 block of our entities (belts, pipes, rails, machines: robots must be able to build and repair there) is still inside the CONSTRUCTION area
    (55 tiles each way) of another roboport, all four block corners;
  2 every block that holds a logistic chest is still inside the LOGISTIC area (25 tiles each way) of another roboport;
  3 the remaining roboports still form ONE network (logistic areas overlapping: centres within 50 tiles on both axes, kept to 49);
  4 it carries no circuit wire.
Removal order: roboports that cover the least on their own first. The robots stored in a roboport (about 80 each) are moved into the nearest roboports first, then
into the logistic network, so none are lost. Their solar kits are left standing (they feed the grid).
Usage: nauvis_roboport_trim.py plan | apply [--batch N] [--max-batches N]"""
import json
import sys
from collections import defaultdict
from pathlib import Path

from _game import tools

SNAP = Path(__file__).resolve().parent.parent / "snapshots"
LOGF = SNAP / "nauvis_roboports_removed.json"
LOG_R, CON_R = 25.0, 55.0
LINK = 49.0

EXPORT = """
local s=game.surfaces.nauvis local f=game.forces.player local W=defines.wire_connector_id local o={}
for _,e in pairs(s.find_entities_filtered{name='roboport',force=f}) do local w=0 for _,id in pairs{W.circuit_red,W.circuit_green} do local c=e.get_wire_connector(id,false) if c and c.connection_count>0 then w=1 end end
  o[#o+1]=e.position.x..','..e.position.y..','..w end rcon.print(table.concat(o,';'))
"""
BLOCKS = """
local s=game.surfaces.nauvis local f=game.forces.player local seen={} local chest={}
for _,e in pairs(s.find_entities_filtered{force=f}) do local t=e.type if t~='electric-pole' and t~='roboport' then local k=math.floor(e.position.x/8)..','..math.floor(e.position.y/8) seen[k]=true if t=='logistic-container' then chest[k]=true end end end
local o={} for k in pairs(seen) do o[#o+1]=k..(chest[k] and 'c' or '') end rcon.print(table.concat(o,';'))
"""
MOVE = """
local s=game.surfaces.nauvis local f=game.forces.player local out={} local lost=0
for _,p in pairs({PTS}) do local e=s.find_entities_filtered{name='roboport',position={p[1],p[2]},radius=0.5,force=f}[1]
  if e then local inv=e.get_inventory(defines.inventory.roboport_robot) local items=inv and inv.get_contents() or {}
    local nb={} for _,o in pairs(s.find_entities_filtered{name='roboport',position=e.position,radius=75,force=f}) do if o~=e then nb[#nb+1]=o end end
    table.sort(nb,function(a,b) return (a.position.x-e.position.x)^2+(a.position.y-e.position.y)^2<(b.position.x-e.position.x)^2+(b.position.y-e.position.y)^2 end)
    for _,it in pairs(items) do local left=it.count for _,o in pairs(nb) do if left<=0 then break end local oi=o.get_inventory(defines.inventory.roboport_robot) if oi then left=left-oi.insert{name=it.name,count=left,quality=it.quality} end end
      if left>0 then local net=e.logistic_network if net then left=left-(net.insert{name=it.name,count=left,quality=it.quality} or 0) end end lost=lost+math.max(0,left) end
    out[#out+1]={e.position.x,e.position.y} e.destroy() end end
rcon.print(helpers.table_to_json({removed=out,lost=lost}))
"""


def flat(code):
    return " ".join(code.split(chr(10)))


def load():
    rp = [tuple(float(v) for v in t.split(",")) for t in tools["run_lua"](flat(EXPORT)).strip().split(";") if t]
    blocks = []
    for t in tools["run_lua"](flat(BLOCKS)).strip().split(";"):
        if not t:
            continue
        chest = t.endswith("c")
        bx, by = [int(v) for v in t.rstrip("c").split(",")]
        blocks.append((bx * 8, by * 8, chest))
    return rp, blocks


def inside(rx, ry, bx, by, radius):
    return all(abs(rx - cx) <= radius and abs(ry - cy) <= radius for cx in (bx, bx + 8) for cy in (by, by + 8))


def plan(rp, blocks):
    n = len(rp)
    gridb = defaultdict(list)
    for i, b in enumerate(blocks):
        gridb[(b[0] // 64, b[1] // 64)].append(i)
    ccount = [0] * len(blocks)
    lcount = [0] * len(blocks)
    cover = [[] for _ in range(n)]
    for r, (rx, ry, w) in enumerate(rp):
        for gx in range(int((rx - 64) // 64), int((rx + 64) // 64) + 1):
            for gy in range(int((ry - 64) // 64), int((ry + 64) // 64) + 1):
                for i in gridb.get((gx, gy), ()):
                    b = blocks[i]
                    if inside(rx, ry, b[0], b[1], CON_R):
                        ccount[i] += 1
                        cover[r].append((i, 0))
                    if b[2] and inside(rx, ry, b[0], b[1], LOG_R):
                        lcount[i] += 1
                        cover[r].append((i, 1))
    adj = defaultdict(set)
    gr = defaultdict(list)
    for i, (x, y, _) in enumerate(rp):
        gr[(int(x // 50), int(y // 50))].append(i)
    for i, (x, y, _) in enumerate(rp):
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for j in gr.get((int(x // 50) + dx, int(y // 50) + dy), ()):
                    if j != i and abs(x - rp[j][0]) <= LINK and abs(y - rp[j][1]) <= LINK:
                        adj[i].add(j)
    alive = set(range(n))

    def components(skip=None):
        seen, cnt = set(), 0
        for s0 in alive:
            if s0 == skip or s0 in seen:
                continue
            cnt += 1
            seen.add(s0)
            stack = [s0]
            while stack:
                a = stack.pop()
                for b in adj[a]:
                    if b != skip and b in alive and b not in seen:
                        seen.add(b)
                        stack.append(b)
        return cnt

    comps0 = components()
    unique = [sum(1 for (i, k) in cover[r] if (ccount[i] if k == 0 else lcount[i]) == 1) for r in range(n)]
    order = sorted((r for r in range(n) if not rp[r][2]), key=lambda r: (unique[r], -len(adj[r])))
    removed = []
    for r in order:
        if all((ccount[i] if k == 0 else lcount[i]) >= 2 for (i, k) in cover[r]) and components(r) <= comps0:
            for (i, k) in cover[r]:
                if k == 0:
                    ccount[i] -= 1
                else:
                    lcount[i] -= 1
            alive.discard(r)
            removed.append(r)
    return removed, comps0, sum(1 for i in range(len(blocks)) if ccount[i] == 0), sum(1 for i in range(len(blocks)) if blocks[i][2] and lcount[i] == 0)


def main():
    step = sys.argv[1] if len(sys.argv) > 1 else "plan"
    rp, blocks = load()
    removed, comps0, bad_c, bad_l = plan(rp, blocks)
    print("roboports %d (circuit-wired %d, kept), occupied blocks %d (chest blocks %d), network components now %d"
          % (len(rp), sum(1 for r in rp if r[2]), len(blocks), sum(1 for b in blocks if b[2]), comps0))
    print("removable: %d (%.1f%%); blocks left without construction cover %d, chest blocks without logistic cover %d (these were already uncovered)"
          % (len(removed), 100.0 * len(removed) / max(1, len(rp)), bad_c, bad_l))
    if step != "apply":
        return
    batch = int(sys.argv[sys.argv.index("--batch") + 1]) if "--batch" in sys.argv else 25
    maxb = int(sys.argv[sys.argv.index("--max-batches") + 1]) if "--max-batches" in sys.argv else 10 ** 9
    log = json.loads(LOGF.read_text()) if LOGF.exists() else []
    done = lost = 0
    for bi, i in enumerate(range(0, len(removed), batch)):
        if bi >= maxb:
            break
        part = [rp[r] for r in removed[i:i + batch]]
        res = json.loads(tools["run_lua"](flat(MOVE.replace("PTS", ",".join("{%.1f,%.1f}" % (p[0], p[1]) for p in part)))))
        log += res["removed"]
        LOGF.write_text(json.dumps(log))
        done += len(res["removed"])
        lost += res["lost"]
        print("batch %d: removed %d (total %d), robots that did not fit anywhere %d" % (bi + 1, len(res["removed"]), done, lost), flush=True)


if __name__ == "__main__":
    main()
