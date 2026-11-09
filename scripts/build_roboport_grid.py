"""
Logistic coverage for the whole factory so construction/logistic robots can work anywhere (and long belts can later be replaced by bots).

A roboport's logistic area is 50x50 tiles, so roboports 48 tiles apart overlap and join one network. The script covers every 48x48 cell that holds at least
one player entity (belts, rails and pipes count, so long lines stay covered), skips cells already served by a roboport, and gives each new roboport a
self-contained power kit (3 solar panels, 2 accumulators, a medium pole) so it works far from the grid. Trees, rocks and cliffs in the way are removed.
Afterwards it checks that all roboports share one network and bridges any gap with extra roboports.

Kit (R = roboport centre, integers): roboport 4x4 at R; medium pole (R.x+2.5, R.y+0.5); solar panels at (R.x+4.5, R.y-2.5/+0.5/+3.5);
accumulators at (R.x, R.y-3) and (R.x+2, R.y-3).
Usage: scripts/build_roboport_grid.py [--revealed] [--build]   (--revealed = every charted 48x48 cell that is mostly land, not only cells with our entities)
"""
import json
import sys

from _game import tools

CELL = 48

KIT_LUA = """
local s=game.surfaces.nauvis local f=game.forces.player local cx,cy=%d,%d local R=%d
local function pieces(rx,ry) return {
  {'roboport',rx,ry},{'medium-electric-pole',rx+2.5,ry+0.5},
  {'solar-panel',rx+4.5,ry-2.5},{'solar-panel',rx+4.5,ry+0.5},{'solar-panel',rx+4.5,ry+3.5},
  {'accumulator',rx,ry-3},{'accumulator',rx+2,ry-3}} end
local function clear(rx,ry)
  local a={{rx-3,ry-5},{rx+7,ry+6}}
  for _,e in pairs(s.find_entities_filtered{area=a,type={'tree','cliff','simple-entity','item-entity','corpse'}}) do if e.force.name~='player' then e.destroy() end end
end
local cand={} for dx=-R,R do for dy=-R,R do cand[#cand+1]={dx,dy,dx*dx+dy*dy} end end
table.sort(cand,function(a,b) return a[3]<b[3] end)
for _,c in pairs(cand) do
  local rx,ry=cx+c[1],cy+c[2]
  if %s then clear(rx,ry) end
  local ok=true for _,p in pairs(pieces(rx,ry)) do if not s.can_place_entity{name=p[1],position={p[2],p[3]},force=f} then ok=false break end end
  if ok then
    if %s then for _,p in pairs(pieces(rx,ry)) do s.create_entity{name=p[1],position={p[2],p[3]},force=f} end end
    rcon.print(helpers.table_to_json({rx,ry})) return end
end
rcon.print('null')
"""

CELLS_LUA = """
local s=game.surfaces.nauvis local f=game.forces.player local cells={}
local function land(x,y) local t=s.get_tile(x,y) return not t.collides_with('player') end
local function mostly_land(cx,cy) local n=0 for _,dx in pairs({-18,0,18}) do for _,dy in pairs({-18,0,18}) do if land(cx+dx,cy+dy) then n=n+1 end end end return n>=2 end
if %(everything)s then
  for c in s.get_chunks() do if f.is_chunk_charted(s,c) then local x,y=c.x*32+16,c.y*32+16 local ix,iy=math.floor(x/48),math.floor(y/48)
    if mostly_land(ix*48+24,iy*48+24) then cells[ix..','..iy]={ix,iy} end end end
end
for _,e in pairs(s.find_entities_filtered{force='player'}) do if e.type~='roboport' then
  local ix,iy=math.floor(e.position.x/48),math.floor(e.position.y/48) cells[ix..','..iy]={ix,iy} end end
local o={} for _,c in pairs(cells) do o[#o+1]=c end
local rp={} for _,r in pairs(s.find_entities_filtered{type='roboport',force='player'}) do rp[#rp+1]={r.position.x,r.position.y} end
rcon.print(helpers.table_to_json({cells=o,roboports=rp}))
"""

NET_LUA = """
local s=game.surfaces.nauvis local o={} for _,r in pairs(s.find_entities_filtered{type='roboport',force='player'}) do
  local n=r.logistic_network o[#o+1]={r.position.x,r.position.y,n and n.network_id or -1} end
rcon.print(helpers.table_to_json(o))
"""


def place(cx, cy, build, radius=14):
    for r in (radius, 28, 40):
        out = tools["run_lua"](KIT_LUA % (cx, cy, r, "true" if build else "false", "true" if build else "false")).strip()
        if out != "null":
            return json.loads(out)
    return None


def main():
    build = "--build" in sys.argv
    data = json.loads(tools["run_lua"](CELLS_LUA % {"everything": "true" if "--revealed" in sys.argv else "false"}))
    existing = data["roboports"]
    todo = []
    for ix, iy in data["cells"]:
        cx, cy = ix * CELL + CELL // 2, iy * CELL + CELL // 2
        if any(abs(cx - x) <= 30 and abs(cy - y) <= 30 for x, y in existing):
            continue
        todo.append((cx, cy))
    print(f"{len(data['cells'])} occupied cells, {len(existing)} existing roboports, {len(todo)} new roboports needed")
    if build:
        print(tools["save_game"]("before-roboport-grid"))
    placed, failed = [], []
    for cx, cy in todo:
        r = place(cx, cy, build)
        (placed if r else failed).append(r or (cx, cy))
    print(f"placed {len(placed)}" if build else f"fits: {len(placed)} cells have room for a kit", f"| no room near {len(failed)} cells: {failed[:8]}")
    if not build:
        return
    # connectivity: all roboports in one network? bridge gaps
    for round_ in range(6):
        net = json.loads(tools["run_lua"](NET_LUA))
        ids = sorted({n[2] for n in net})
        print(f"round {round_}: {len(net)} roboports in {len(ids)} networks")
        if len(ids) <= 1:
            break
        groups = {i: [(n[0], n[1]) for n in net if n[2] == i] for i in ids}
        main_id = max(groups, key=lambda i: len(groups[i]))
        for i, pts in groups.items():
            if i == main_id:
                continue
            best = min(((abs(a[0] - b[0]) + abs(a[1] - b[1]), a, b) for a in pts for b in groups[main_id]), key=lambda t: t[0])
            _, a, b = best
            steps = max(1, -(-int(max(abs(a[0] - b[0]), abs(a[1] - b[1]))) // 46))
            for k in range(1, steps):
                px, py = a[0] + (b[0] - a[0]) * k / steps, a[1] + (b[1] - a[1]) * k / steps
                place(int(round(px)), int(round(py)), True)


if __name__ == "__main__":
    main()
