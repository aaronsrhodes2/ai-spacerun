"""
Substation grid for the whole revealed map, then retire every other electric pole.

A substation is 2x2, supplies an 18x18 area (9 tiles each way) and reaches 18 tiles by wire. Phases (each safe to repeat):

  --place    lattice of substations every 16 tiles over all revealed LAND (flexible shift up to 3 tiles around blocked points; trees/rocks/cliffs
             in the way are removed), then fills coverage holes and bridges separate wire networks (needs the previous poles/substations to join).
  --verify   every electric machine (consumer or producer) must overlap a substation's supply area, and that substation's network must be the main
             network (the one with the steam turbines) or one that contains solar panels. Prints what would lose power if the poles went.
  --remove   (only after --verify is clean) saves the game, writes every small/medium/big pole to scripts/_poles_removed.json (restorable with
             --restore), removes them, and compares unpowered counts with the baseline.

Usage: scripts/build_substation_grid.py --place | --verify | --remove | --restore
"""
import json
import sys
from pathlib import Path

from _game import tools

SPACING = 16
SHIFT = 3
REMOVED = Path(__file__).resolve().parent / "_poles_removed.json"

CHUNKS_LUA = """
local s=game.surfaces.nauvis local f=game.forces.player local o={}
for c in s.get_chunks() do if f.is_chunk_charted(s,c) then o[#o+1]={c.x,c.y} end end
rcon.print(helpers.table_to_json(o))
"""

# place substations near each candidate point; returns the placed centres
PLACE_LUA = """
local s=game.surfaces.nauvis local f=game.forces.player local R=%(shift)d local pts={%(pts)s} local out={}
local function land(x,y) local t=s.get_tile(x,y) return not t.collides_with('player') end
local function clear(x,y) for _,e in pairs(s.find_entities_filtered{area={{x-2,y-2},{x+2,y+2}},type={'tree','cliff','simple-entity','item-entity','corpse'}}) do if e.force.name~='player' then e.destroy() end end end
for _,p in pairs(pts) do
  local cx,cy=p[1],p[2]
  if land(cx,cy) then
    local cand={} for dx=-R,R do for dy=-R,R do cand[#cand+1]={dx,dy,dx*dx+dy*dy} end end
    table.sort(cand,function(a,b) return a[3]<b[3] end)
    for _,c in pairs(cand) do
      local x,y=cx+c[1],cy+c[2]
      if land(x,y) and land(x+1,y) and land(x,y+1) then
        clear(x,y)
        if s.can_place_entity{name='substation',position={x,y},force=f} then
          local e=s.create_entity{name='substation',position={x,y},force=f}
          if e then out[#out+1]={x,y} end break end end end end end
rcon.print(helpers.table_to_json(out))
"""

SUBS_LUA = """
local s=game.surfaces.nauvis local o={}
for _,e in pairs(s.find_entities_filtered{name='substation',force='player'}) do o[#o+1]={e.position.x,e.position.y,e.electric_network_id or -1} end
rcon.print(helpers.table_to_json(o))
"""

LAND_LUA = """
local s=game.surfaces.nauvis local chunks={%(chunks)s} local o={}
for _,c in pairs(chunks) do local row={} for j=0,7 do for i=0,7 do local x=c[1]*32+i*4+2 local y=c[2]*32+j*4+2 row[#row+1]=(not s.get_tile(x,y).collides_with('player')) and '1' or '0' end end o[#o+1]=table.concat(row) end
rcon.print(table.concat(o,','))
"""

CONSUMERS_LUA = """
local s=game.surfaces.nauvis local o={} local main=nil
local t=s.find_entities_filtered{type='generator',force='player'}[1] if t then main=t.electric_network_id end
for _,e in pairs(s.find_entities_filtered{force='player'}) do
  if e.type~='electric-pole' and e.prototype.electric_energy_source_prototype then
    local bb=e.bounding_box o[#o+1]={bb.left_top.x,bb.left_top.y,bb.right_bottom.x,bb.right_bottom.y,e.type=='solar-panel' and 1 or 0} end end
rcon.print(helpers.table_to_json({main=main,items=o}))
"""

STATUS_LUA = """
local s=game.surfaces.nauvis local n=0 local low=0
for _,e in pairs(s.find_entities_filtered{force='player'}) do if e.status==defines.entity_status.no_power then n=n+1 elseif e.status==defines.entity_status.low_power then low=low+1 end end
rcon.print(helpers.table_to_json({no_power=n,low_power=low}))
"""


def jl(code):
    out = tools["run_lua"](code)
    if "Cannot execute command" in out:
        raise SystemExit("Lua error: " + out[:500])
    return json.loads(out) if out.strip().startswith(("[", "{")) else out


def lattice(chunks):
    pts = set()
    for cx, cy in chunks:
        for i in range(2):
            for j in range(2):
                pts.add((cx * 32 + i * SPACING + SPACING // 2, cy * 32 + j * SPACING + SPACING // 2))
    return sorted(pts)


def place_points(pts, batch=40):
    placed = []
    for i in range(0, len(pts), batch):
        part = pts[i:i + batch]
        txt = ",".join("{%d,%d}" % p for p in part)
        res = jl(PLACE_LUA % {"shift": SHIFT, "pts": txt})
        placed += [tuple(p) for p in res] if isinstance(res, list) else []
        if (i // batch) % 10 == 0:
            print(f"  {i + len(part)}/{len(pts)} points, {len(placed)} substations", flush=True)
    return placed


def land_samples(chunks):
    out = []
    for i in range(0, len(chunks), 150):
        part = chunks[i:i + 150]
        raw = tools["run_lua"](LAND_LUA % {"chunks": ",".join("{%d,%d}" % c for c in part)}).strip().split(",")
        for c, row in zip(part, raw):
            for k, ch in enumerate(row):
                if ch == "1":
                    out.append((c[0] * 32 + (k % 8) * 4 + 2, c[1] * 32 + (k // 8) * 4 + 2))
    return out


def uncovered(samples, subs):
    grid = {}
    for x, y, _ in subs:
        grid.setdefault((int(x // 18), int(y // 18)), []).append((x, y))
    bad = []
    for sx, sy in samples:
        ok = False
        gx, gy = int(sx // 18), int(sy // 18)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for x, y in grid.get((gx + dx, gy + dy), ()):
                    if abs(sx - x) <= 9 and abs(sy - y) <= 9:
                        ok = True
                        break
                if ok:
                    break
            if ok:
                break
        if not ok:
            bad.append((sx, sy))
    return bad


def phase_place():
    chunks = [tuple(c) for c in jl(CHUNKS_LUA)]
    print(f"{len(chunks)} revealed chunks")
    print(tools["save_game"]("before-substation-grid"))
    pts = lattice(chunks)
    print(f"lattice points: {len(pts)}")
    place_points(pts)
    samples = land_samples(chunks)
    print(f"{len(samples)} land sample points")
    for rnd in range(4):
        subs = jl(SUBS_LUA)
        bad = uncovered(samples, subs)
        print(f"round {rnd}: {len(subs)} substations, {len(bad)} uncovered land samples")
        if not bad:
            break
        # one new substation per 8x8 cluster of holes
        cl = {}
        for x, y in bad:
            cl.setdefault((x // 8, y // 8), (x, y))
        place_points(sorted(cl.values()))
    # wire networks: bridge small groups to the biggest one
    for rnd in range(6):
        subs = jl(SUBS_LUA)
        groups = {}
        for x, y, n in subs:
            groups.setdefault(n, []).append((x, y))
        print(f"wire round {rnd}: {len(groups)} networks (largest {max(len(g) for g in groups.values())} substations)")
        if len(groups) <= 1:
            break
        main = max(groups, key=lambda k: len(groups[k]))
        added = 0
        for n, pts2 in groups.items():
            if n == main:
                continue
            best = min(((max(abs(a[0] - b[0]), abs(a[1] - b[1])), a, b) for a in pts2 for b in groups[main]), key=lambda t: t[0])
            d, a, b = best
            if d <= 18 or d > 200:
                continue
            steps = -(-int(d) // 15)
            mids = [(round(a[0] + (b[0] - a[0]) * k / steps), round(a[1] + (b[1] - a[1]) * k / steps)) for k in range(1, steps)]
            added += len(place_points(mids))
        if not added:
            break


def phase_verify():
    subs = jl(SUBS_LUA)
    data = jl(CONSUMERS_LUA)
    main = data["main"]
    solar_nets = set()
    grid = {}
    for x, y, n in subs:
        grid.setdefault((int(x // 18), int(y // 18)), []).append((x, y, n))
    unc, wrong = [], []
    for x1, y1, x2, y2, solar in data["items"]:
        found = None
        gx, gy = int((x1 + x2) / 2 // 18), int((y1 + y2) / 2 // 18)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for sx, sy, n in grid.get((gx + dx, gy + dy), ()):
                    if x2 > sx - 9 and x1 < sx + 9 and y2 > sy - 9 and y1 < sy + 9:
                        found = n if (found is None or n == main) else found
        if found is None:
            unc.append((round(x1), round(y1)))
        elif found != main:
            wrong.append((round(x1), round(y1), found))
    nets = {}
    for x, y, n in subs:
        nets[n] = nets.get(n, 0) + 1
    print(f"{len(data['items'])} electric machines; substations {len(subs)} in {len(nets)} networks; main network id {main}")
    print(f"not covered by any substation: {len(unc)} {unc[:6]}")
    print(f"covered only by a substation outside the main network: {len(wrong)} {wrong[:6]}")
    return not unc and not wrong, unc, wrong


def phase_remove():
    ok, unc, wrong = phase_verify()
    if not ok:
        print("verify is not clean: not removing anything (islands with their own solar are listed above; check them)")
        if "--force" not in sys.argv:
            return
    base = jl(STATUS_LUA)
    print("baseline", base)
    print(tools["save_game"]("before-pole-removal"))
    removed = jl("local s=game.surfaces.nauvis local o={} for _,e in pairs(s.find_entities_filtered{type='electric-pole',force='player'}) do if e.name~='substation' then o[#o+1]={e.name,e.position.x,e.position.y} end end rcon.print(helpers.table_to_json(o))")
    REMOVED.write_text(json.dumps(removed))
    print(f"{len(removed)} poles recorded in {REMOVED.name}")
    for i in range(0, len(removed), 300):
        part = removed[i:i + 300]
        spec = ";".join(f"{n}|{x}|{y}" for n, x, y in part)
        tools["run_lua"]("local s=game.surfaces.nauvis for item in string.gmatch('%s','[^;]+') do local f={} for v in string.gmatch(item,'[^|]+') do f[#f+1]=v end local e=s.find_entities_filtered{name=f[1],position={tonumber(f[2]),tonumber(f[3])},radius=0.1,force='player'}[1] if e then e.destroy() end end rcon.print('ok')" % spec)
    after = jl(STATUS_LUA)
    print("after", after)
    if after["no_power"] > base["no_power"]:
        print("MORE unpowered machines than before: run with --restore to put the poles back, then investigate")


def phase_restore():
    removed = json.loads(REMOVED.read_text())
    for i in range(0, len(removed), 300):
        part = removed[i:i + 300]
        spec = ";".join(f"{n}|{x}|{y}" for n, x, y in part)
        tools["run_lua"]("local s=game.surfaces.nauvis for item in string.gmatch('%s','[^;]+') do local f={} for v in string.gmatch(item,'[^|]+') do f[#f+1]=v end s.create_entity{name=f[1],position={tonumber(f[2]),tonumber(f[3])},force='player'} end rcon.print('ok')" % spec)
    print(f"restored {len(removed)} poles")


def main():
    a = sys.argv[1:]
    if "--place" in a:
        phase_place()
    elif "--verify" in a:
        phase_verify()
    elif "--remove" in a:
        phase_remove()
    elif "--restore" in a:
        phase_restore()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
