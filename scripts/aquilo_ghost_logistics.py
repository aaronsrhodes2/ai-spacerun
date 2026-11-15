#!/usr/bin/env python3
"""Aquilo ghost logistics (2026-11-14): what limits the Captain's tile ghosts, and the coverage fix.

Findings that shaped it (measured 2026-11-14):
  * Two kinds of tile ghost: `ice-platform` (water, made by the ice platform works) and `concrete` (land: snow, rough ice; the works make NO concrete).
    Concrete ghosts inside coverage wait for the item `concrete` (network stock 0): that is the biggest wall, fixed only by import (delivery list).
  * Construction radius of an epic roboport is 55 (a square), logistic radius 25. The old 3 roboports (-26,-27) (4,-11) (35,2) left the far
    north (y < -90) and the south (y > 20) outside: every ice-platform ghost inside coverage was already built, 1,900 finished platforms sat idle.
  * Robots were not the limit (30 of 30 construction robots idle).
Steps (read-only unless --apply):
  status            ghost totals by kind, inside / outside coverage, robots, stock, ghosts built per minute (--secs N, default 0 = skip the rate)
  coverage          outside ghosts by 20 x 20 box (bounding boxes), per roboport cell
  frontier [--apply] [--max K]   repeatable: pick the best next roboport site (4 x 4 on snow/concrete, within 46 tiles of the network so it links, a
                                 heat pipe touching it or at most 3 new heat pipes, maximum newly covered ghosts), dry-run, place, verify it joined
                                 the main network and has power / heat. Run again after each growth ring of platforms.
  robots            construction robots needed for the platform rate over the real distance, vs what the network holds
  stuck             entity ghosts and the item they lack, concrete ghosts (stock), concrete ghosts on water, ghosts in front of offshore pumps, Nauvis ghosts
Heat route: a breadth-first search from the heat network over free tiles (snow, or ice / ice platform paved with concrete, never under a tile ghost) finds the pipe
path to a site, up to --gap pipes. NOT automated: power. The step prints the nearest pole; when it is far (the far north site: none within 40) a chain of
substations along the route must be added by hand before the roboport works. The far-north site (-38,-108) needs 37 heat pipes (about 3,000 solid fuel to soak)
and a pole chain; it was left unbuilt for the power/fuel agents to agree.
Usage: aquilo_ghost_logistics.py status [--secs 120] | coverage | frontier [--apply] [--max 4] [--gap 3] | robots | stuck
"""
import json
import sys
import time

from _game import tools

SURF = "aquilo"
RADIUS = 55            # epic roboport construction radius (square)
LINK = 46              # centre-to-centre distance within which a new roboport joins the network (logistic radius 25 each = 50, with margin)
PLATFORMS_PER_MIN = 28
GAP = 3                # most new heat pipes per site (each soaks ~82 solid fuel); --gap N raises it


def lua(code):
    return tools["run_lua"](code).strip()


def ports():
    out = lua("local s=game.surfaces.aquilo local o={} for _,r in pairs(s.find_entities_filtered{type='roboport'}) do o[#o+1]=string.format('%d,%d,%d',r.position.x,r.position.y,r.logistic_network and r.logistic_network.network_id or -1) end rcon.print(table.concat(o,' '))")
    return [tuple(int(v) for v in p.split(",")) for p in out.split()]


COVER = ("local s=game.surfaces.aquilo local R={} for _,r in pairs(s.find_entities_filtered{type='roboport'}) do R[#R+1]=r.position end "
         "local function cov(p) for _,r in ipairs(R) do if math.abs(p.x-r.x)<=55 and math.abs(p.y-r.y)<=55 then return true end end return false end ")


def ghost_table():
    """(kind, inside) -> count."""
    out = lua(COVER + "local h={} for _,g in pairs(s.find_entities_filtered{type='tile-ghost'}) do local k=g.ghost_name..(cov(g.position) and ' IN' or ' OUT') h[k]=(h[k] or 0)+1 end "
              "local o={} for k,v in pairs(h) do o[#o+1]=k..'='..v end rcon.print(table.concat(o,';'))")
    t = {}
    for kv in out.split(";"):
        if "=" in kv:
            k, v = kv.rsplit("=", 1)
            t[k] = int(v)
    return t


def status(secs=0):
    t = ghost_table()
    print("tile ghosts:", ", ".join("%s %d" % kv for kv in sorted(t.items())), "| total", sum(t.values()))
    p = ports()
    print("roboports:", len(p), p)
    print(lua("local s=game.surfaces.aquilo local rp=s.find_entities_filtered{type='roboport'}[1] local n=rp.logistic_network "
              "rcon.print(string.format('network %d cells %d construction robots %d (idle %d) logistic robots %d (idle %d) | stock ice-platform %d concrete %d refined-concrete %d construction-robot %d',"
              "n.network_id,#n.cells,n.all_construction_robots,n.available_construction_robots,n.all_logistic_robots,n.available_logistic_robots,"
              "n.get_item_count('ice-platform'),n.get_item_count('concrete'),n.get_item_count('refined-concrete'),n.get_item_count('construction-robot')))"))
    if secs:
        a = sum(t.values())
        t0 = lua("rcon.print(game.tick)")
        time.sleep(secs)
        b = sum(ghost_table().values())
        t1 = lua("rcon.print(game.tick)")
        mins = (int(t1) - int(t0)) / 3600.0
        print("ghosts %d -> %d over %.2f game minutes: %.1f built per minute" % (a, b, mins, (a - b) / max(mins, 1e-9)))


def coverage():
    print(lua(COVER + "local b={} for _,g in pairs(s.find_entities_filtered{type='tile-ghost'}) do if not cov(g.position) then local p=g.position local k=g.ghost_name..' x'..(math.floor(p.x/20)*20)..' y'..(math.floor(p.y/20)*20) "
              "local e=b[k] if not e then e={1e9,1e9,-1e9,-1e9,0} b[k]=e end e[1]=math.min(e[1],p.x) e[2]=math.min(e[2],p.y) e[3]=math.max(e[3],p.x) e[4]=math.max(e[4],p.y) e[5]=e[5]+1 end end "
              "local o={} for k,e in pairs(b) do o[#o+1]=string.format('%s: %d ghosts, x %.0f..%.0f y %.0f..%.0f',k,e[5],e[1],e[3],e[2],e[4]) end table.sort(o) rcon.print(table.concat(o,'|'))").replace("|", "\n"))
    print("construction radius 55 (square) around:", [(x, y) for x, y, _ in ports()])


def buckets():
    out = lua(COVER + "local b={} for _,g in pairs(s.find_entities_filtered{type='tile-ghost'}) do if not cov(g.position) then local k=math.floor(g.position.x/4)*4+2 local l=math.floor(g.position.y/4)*4+2 b[k..','..l]=(b[k..','..l] or 0)+1 end end "
              "local o={} for k,v in pairs(b) do o[#o+1]=k..','..v end rcon.print(table.concat(o,' '))")
    return [tuple(int(v) for v in e.split(",")) for e in out.split()]


FIND = ("local s=game.surfaces.aquilo local R={%(R)s} local B={%(B)s} local V={%(V)s} local X={%(X)s} "
        "local snow={['dust-flat']=1,['dust-crests']=1,['dust-lumpy']=1,['dust-patchy']=1,['snow-crests']=1,['snow-flat']=1,['snow-lumpy']=1,['snow-patchy']=1,['frozen-concrete']=1,['concrete']=1,['refined-concrete']=1} "
        "local hs={} for _,h in pairs(s.find_entities_filtered{name='heat-pipe'}) do hs[math.floor(h.position.x)..','..math.floor(h.position.y)]=1 end for _,v in ipairs(V) do hs[v[1]..','..v[2]]=1 end "
        "local melt={['ice-smooth']=1,['ice-rough']=1,['brash-ice']=1,['ice-platform']=1} "
        "local function kind(x,y) local n=s.get_tile(x+0.5,y+0.5).name if snow[n] then return 1 end if melt[n] and #s.find_entities_filtered{type='tile-ghost',position={x+0.5,y+0.5}}==0 then return 2 end return nil end "
        "local function free(x0,y0,x1,y1) for _,e in pairs(s.find_entities_filtered{area={{x0+0.01,y0+0.01},{x1-0.01,y1-0.01}}}) do local t=e.type if t~='tile-ghost' and t~='construction-robot' and t~='logistic-robot' then return false end end return true end "
        "local function covered(bx,by) for _,r in ipairs(R) do if math.abs(bx-r[1])<=55 and math.abs(by-r[2])<=55 then return true end end return false end "
        "local U={} for _,b in ipairs(B) do if not covered(b[1],b[2]) then U[#U+1]=b end end "
        "local hd={} local par={} local pk={} local q={} for k,_ in pairs(hs) do hd[k]=0 q[#q+1]=k end local head=1 "
        "while head<=#q do local k=q[head] head=head+1 local d=hd[k] if d<%(G)d then local xs,ys=k:match('(-?%%d+),(-?%%d+)') local x,y=tonumber(xs),tonumber(ys) for _,dd in ipairs({{1,0},{-1,0},{0,1},{0,-1}}) do local nx,ny=x+dd[1],y+dd[2] local nk=nx..','..ny "
        "if hd[nk]==nil then local kk=kind(nx,ny) if kk and free(nx,ny,nx+1,ny+1) then hd[nk]=d+1 par[nk]=k pk[nk]=kk q[#q+1]=nk end end end end end "
        "local seen={} local cands={} "
        "for _,r in ipairs(R) do for cx=r[1]-%(L)d,r[1]+%(L)d do for cy=r[2]-%(L)d,r[2]+%(L)d do local key=cx..','..cy if not seen[key] then seen[key]=true "
        "local ok=false for _,q in ipairs(R) do local dx,dy=cx-q[1],cy-q[2] if dx*dx+dy*dy<=%(L)d*%(L)d then ok=true break end end "
        "if ok then local gain=0 for _,b in ipairs(U) do if math.abs(b[1]-cx)<=55 and math.abs(b[2]-cy)<=55 then gain=gain+b[3] end end "
        "for _,xq in ipairs(X) do if math.abs(cx-xq[1])<7 and math.abs(cy-xq[2])<7 then gain=0 end end "
        "if gain>=%(MING)d then cands[#cands+1]={cx,cy,gain} end end end end end end "
        "table.sort(cands,function(a,b) return a[3]>b[3] end) local out={} local checked=0 "
        "for _,c in ipairs(cands) do if checked>=%(MAXC)d then break end checked=checked+1 local cx,cy=c[1],c[2] local x0,y0=cx-2,cy-2 local good=true "
        "local pave={} for x=x0,x0+3 do for y=y0,y0+3 do local k=kind(x,y) if not k then good=false break end if k==2 then pave[#pave+1]=x..':'..y end end if not good then break end end "
        "if good and free(x0,y0,x0+4,y0+4) then local best=nil "
        "local best=nil local nb={} for t=0,3 do nb[#nb+1]={x0-1,y0+t} nb[#nb+1]={x0+4,y0+t} nb[#nb+1]={x0+t,y0-1} nb[#nb+1]={x0+t,y0+4} end "
        "local bl=1e9 for _,q in ipairs(nb) do local nk=q[1]..','..q[2] local d=hd[nk] if d and d<bl then local line={} local ok2=true local cur=nk while hd[cur] and hd[cur]>0 do local cxx,cyy=cur:match('(-?%%d+),(-?%%d+)') cxx=tonumber(cxx) cyy=tonumber(cyy) if cxx>=x0 and cxx<x0+4 and cyy>=y0 and cyy<y0+4 then ok2=false break end line[#line+1]={cxx,cyy,pk[cur]} cur=par[cur] end if ok2 then best=line bl=d end end end "
        "if best then local sp='' local pv=table.concat(pave,'/') for _,p in ipairs(best) do sp=sp..p[1]..':'..p[2]..'/' if p[3]==2 then pv=pv..'/'..p[1]..':'..p[2] end end out[#out+1]=cx..','..cy..','..c[3]..','..#best..','..sp..','..pv end end "
        "if #out>=3 then break end end rcon.print(#out>0 and table.concat(out,' ') or ('DBG cands '..#cands..' checked '..checked..' U '..#U))")


def pick(R, B, V, minGain=60, maxc=7000):
    code = FIND % {"R": ",".join("{%d,%d}" % (x, y) for x, y in R), "B": ",".join("{%d,%d,%d}" % b for b in B),
                   "V": ",".join("{%d,%d}" % v for v in V), "X": ",".join("{%d,%d}" % r for r in R), "G": GAP, "L": LINK, "MING": minGain, "MAXC": maxc}
    out = lua(code)
    res = []
    if out.startswith('DBG'):
        print(out)
        return res
    for e in out.split():
        a = e.split(",", 5)
        pipes = [tuple(int(v) for v in q.split(":")) for q in a[4].split("/") if q]
        pave = [tuple(int(v) for v in q.split(":")) for q in a[5].split("/") if q]
        res.append({"cx": int(a[0]), "cy": int(a[1]), "gain": int(a[2]), "g": int(a[3]), "pipes": pipes, "pave": pave})
    return res


def power_need(cx, cy):
    """Nearest electric pole (name, position, Chebyshev distance): a roboport needs one within its supply area, else add a substation."""
    return lua("local s=game.surfaces.aquilo local best,bd=nil,1e9 for _,p in pairs(s.find_entities_filtered{type='electric-pole',position={%d,%d},radius=40}) do "
               "local d=math.max(math.abs(p.position.x-(%d)),math.abs(p.position.y-(%d))) if d<bd then bd=d best=p end end "
               "rcon.print(best and (best.name..' '..best.position.x..' '..best.position.y..' d='..bd) or 'none')" % (cx, cy, cx, cy))


def frontier(apply, maxn=4):
    p = ports()
    main = max(set(n for _, _, n in p), key=lambda n: sum(1 for q in p if q[2] == n))
    R = [(x, y) for x, y, n in p if n == main]
    B = buckets()
    print("main network", main, "roboports", R, "| uncovered ghosts", sum(b[2] for b in B))
    V = []
    chosen = []
    for i in range(maxn):
        c = pick(R, B, V)
        if not c:
            print("no further site with enough gain")
            break
        c = c[0]
        print("site %d: roboport centre (%d,%d) newly covers ~%d ghosts, %d new heat pipes %s, %d tiles to pave with concrete" % (i + 1, c["cx"], c["cy"], c["gain"], c["g"], c["pipes"], len(c["pave"])))
        print("   nearest pole:", power_need(c["cx"], c["cy"]))
        chosen.append(c)
        R.append((c["cx"], c["cy"]))
        V += c["pipes"]
    ents = []
    if apply:
        for c in chosen:
            if c["pave"]:       # heated things melt ice and ice platform: a concrete pad under them (the way aquilo_cryo.build does it; no ghost lies on these tiles)
                print("paved", lua("local s=game.surfaces.aquilo local t={} for _,p in pairs({%s}) do t[#t+1]={name='concrete',position=p} end s.set_tiles(t) rcon.print(#t)" % ",".join("{%d,%d}" % q for q in c["pave"])))
    for c in chosen:
        ents += [{"name": "heat-pipe", "x": x + 0.5, "y": y + 0.5, "direction": 0, "params": {"quality": "epic"}} for x, y in c["pipes"]]
        ents.append({"name": "roboport", "x": float(c["cx"]), "y": float(c["cy"]), "direction": 0, "params": {"quality": "epic"}})
    if not ents:
        return
    r = json.loads(tools["place_entities"](json.dumps(ents), surface=SURF, dry_run=not apply, clear_trees=False))
    print("placed" if apply else "dry run", r.get("placed"), "failed", json.dumps(r.get("failed") or [])[:600])
    if apply:
        lua("local s=game.surfaces.aquilo for _,c in pairs({%s}) do game.forces.player.chart(s,{{c[1]-30,c[2]-30},{c[1]+30,c[2]+30}}) end rcon.print('charted')" % ",".join("{%d,%d}" % (c["cx"], c["cy"]) for c in chosen))
        time.sleep(3)
        for c in chosen:
            print("verify (%d,%d):" % (c["cx"], c["cy"]), lua("local s=game.surfaces.aquilo local r=s.find_entities_filtered{name='roboport',position={%d,%d},radius=0.6}[1] "
                  "rcon.print(r and ('network '..tostring(r.logistic_network and r.logistic_network.network_id)..' status '..tostring(r.status)..' main %d') or 'missing')" % (c["cx"], c["cy"], main)))


def robots():
    out = lua("local s=game.surfaces.aquilo local n=s.find_entities_filtered{type='roboport'}[1].logistic_network local sp=prototypes.entity['construction-robot'].speed or 0 "
              "local cx,cy,k=0,0,0 for _,c in pairs(s.find_entities_filtered{name='passive-provider-chest',area={{-20,-40},{25,-24}}}) do cx=cx+c.position.x cy=cy+c.position.y k=k+1 end if k>0 then cx=cx/k cy=cy/k end "
              "local d,m=0,0 for _,g in pairs(s.find_entities_filtered{type='tile-ghost'}) do if g.ghost_name=='ice-platform' then d=d+math.sqrt((g.position.x-cx)^2+(g.position.y-cy)^2) m=m+1 end end "
              "rcon.print(string.format('%d %d %.4f %.1f %.1f %d %.0f',n.all_construction_robots,n.available_construction_robots,sp,cx,cy,k,m==0 and 0 or d/m))")
    allc, av, sp, cx, cy, k, avgd = out.split()
    allc, av, k, avgd, sp = int(allc), int(av), int(k), int(float(avgd)), float(sp)
    speed = (sp if sp > 0 else 0.06) * 60
    cycle = 2 * avgd / speed + 4          # fetch from the chest, fly out, place, fly back, charge share
    need = PLATFORMS_PER_MIN / 60.0 * cycle
    print("construction robots %d (idle %d), speed %.1f tiles/s, red chests %d at (%s,%s), mean distance to remaining platform ghosts %d tiles" % (allc, av, speed, k, cx, cy, avgd))
    print("one trip takes about %.0f s -> %.0f robots keep %d platforms/min going; burning a stock of 1,900 in 20 minutes wants about %.0f" % (cycle, need, PLATFORMS_PER_MIN, 1900 / 20.0 / 60.0 * cycle))
    print("verdict:", "enough robots" if allc >= need * 1.5 else "short by about %d (add to scripts/aquilo_delivery_list.txt)" % int(need * 1.5 - allc))


def stuck():
    print("entity ghosts on aquilo:")
    print(lua("local s=game.surfaces.aquilo local n=s.find_entities_filtered{type='roboport'}[1].logistic_network local h={} for _,g in pairs(s.find_entities_filtered{type='entity-ghost'}) do local it=g.ghost_prototype.items_to_place_this[1] local k=g.ghost_name..' needs '..(it and it.name or '?')..' stock '..(it and n.get_item_count(it.name) or -1) h[k]=(h[k] or 0)+1 end "
              "local o={} for k,v in pairs(h) do o[#o+1]=k..' x'..v end rcon.print(table.concat(o,'|'))").replace("|", "\n"))
    print("tile ghosts on water that need a land item (concrete cannot stand on water; they wait for an ice platform first):")
    print(lua("local s=game.surfaces.aquilo local k,w=0,0 for _,g in pairs(s.find_entities_filtered{type='tile-ghost'}) do if g.ghost_name=='concrete' then k=k+1 if s.get_tile(g.position).collides_with('water_tile') then w=w+1 end end end "
              "rcon.print('concrete ghosts '..k..', on water '..w..'; network stock concrete '..s.find_entities_filtered{type='roboport'}[1].logistic_network.get_item_count('concrete'))"))
    print("ghosts within 3 tiles of an offshore pump (inlet blockers):")
    print(lua("local s=game.surfaces.aquilo local o={} for _,p in pairs(s.find_entities_filtered{name='offshore-pump'}) do local n=#s.find_entities_filtered{type='tile-ghost',position=p.position,radius=3} o[#o+1]=string.format('pump (%.1f,%.1f): %d tile ghosts',p.position.x,p.position.y,n) end rcon.print(table.concat(o,'|'))").replace("|", "\n"))
    print("nauvis entity ghosts:", lua("rcon.print(#game.surfaces.nauvis.find_entities_filtered{type='entity-ghost'})"), "(scripts/ghost_demand.py status; omni_maker.py status replicator)")


def main():
    global GAP
    step = sys.argv[1] if len(sys.argv) > 1 else "status"
    a = sys.argv
    if step == "status":
        status(int(a[a.index("--secs") + 1]) if "--secs" in a else 0)
    elif step == "coverage":
        coverage()
    elif step == "frontier":
        if "--gap" in a:
            GAP = int(a[a.index("--gap") + 1])
        frontier("--apply" in a, int(a[a.index("--max") + 1]) if "--max" in a else 4)
    elif step == "robots":
        robots()
    elif step == "stuck":
        stuck()
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
