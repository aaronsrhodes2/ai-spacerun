#!/usr/bin/env python3
"""Many fruit towers for the Gleba cell (the Captain, 2026-11-15: "fruit towers are the thing you can't have too many of").

Finds free tower sites on natural soil (greedy by soil count, fields not overlapping), then for each site plans:
  tower + seed requester/inserter (gated like the cell) + fruit chest/inserter (gated by tune()),
  a substation chain from the nearest powered pole, and a roboport where the robot network does not reach.
Wild plants in footprints are harvested (clear_plants) and the fruit goes into the new fruit chests.

Usage: gleba_farms.py sites yumako|jellynut N     (list the sites)
       gleba_farms.py dry yumako|jellynut N       (plan + dry run)
       gleba_farms.py build yumako|jellynut N
"""
import json
import math
import sys

from _game import tools
import gleba_cell as G

def L(code):
    """One RCON line: newlines end an RCON command, so every Lua string is flattened first."""
    return tools["run_lua"](" ".join(code.split("\n")))


KIND = {
    "yumako": dict(soil="natural-yumako-soil", seed="yumako-seed", box=(-205, -130, -170, -100), min_soil=30),
    "jellynut": dict(soil="natural-jellynut-soil", seed="jellynut-seed", box=(150, 260, 20, 160), min_soil=25),
}
SPACING = 9           # towers 9 apart: fields overlap (a tower cuts plants faster than they grow, so a denser pack just means more towers on the same plants)
NET_REACH = 20        # a roboport this close covers the chests (logistic radius 25)

HELP = """
local s=game.surfaces.gleba local f=game.forces.player
local function ok(p,h) local a={{p[1]-h+0.02,p[2]-h+0.02},{p[1]+h-0.02,p[2]+h-0.02}}
  return s.count_tiles_filtered{area=a,collision_mask='water_tile'}==0 and s.count_entities_filtered{area=a,force=f,limit=1}==0 and s.count_entities_filtered{area=a,type='cliff',limit=1}==0 end
"""


def find_sites(kind, n, avoid):
    k = KIND[kind]
    x0, x1, y0, y1 = k["box"]
    av = ",".join("{%s,%s}" % a for a in avoid)
    code = HELP + (
        "local res={} for x=%d,%d do for y=%d,%d do local p={x+0.5,y+0.5} if ok(p,1.5) and ok({p[1],p[2]+3},0.5) and ok({p[1],p[2]+2},0.5) and ok({p[1]+3,p[2]},0.5) and ok({p[1]+2,p[2]},0.5) then "
        "local c=s.count_tiles_filtered{area={{p[1]-10.5,p[2]-10.5},{p[1]+10.5,p[2]+10.5}},name='%s'} if c>=%d then res[#res+1]={c,p[1],p[2]} end end end end "
        "table.sort(res,function(a,b) return a[1]>b[1] end) local picked={} local avoid={%s} for _,r in ipairs(res) do local far=true "
        "for _,a in pairs(avoid) do if math.abs(r[2]-a[1])<%d and math.abs(r[3]-a[2])<%d then far=false end end "
        "for _,a in pairs(picked) do if math.abs(r[2]-a[2])<%d and math.abs(r[3]-a[3])<%d then far=false end end "
        "if far then picked[#picked+1]=r if #picked>=%d then break end end end rcon.print(helpers.table_to_json(picked))"
    ) % (x0, x1, y0, y1, k["soil"], k["min_soil"], av, SPACING, SPACING, SPACING, SPACING, n)
    return json.loads(L(code))


def existing_towers():
    r = json.loads(L("local o={} for _,t in pairs(game.surfaces.gleba.find_entities_filtered{name='agricultural-tower'}) do o[#o+1]={t.position.x,t.position.y} end rcon.print(helpers.table_to_json(o))"))
    return [tuple(p) for p in r]


def existing_infra():
    code = ("local s=game.surfaces.gleba local f=game.forces.player local p={} local r={} "
            "for _,e in pairs(s.find_entities_filtered{force=f,name={'substation','big-electric-pole'}}) do p[#p+1]={e.position.x,e.position.y} end "
            "for _,e in pairs(s.find_entities_filtered{force=f,name='roboport'}) do r[#r+1]={e.position.x,e.position.y} end "
            "rcon.print(helpers.table_to_json({poles=p,ports=r}))")
    return json.loads(L(code))


def snap(name, h, x, y, taken, radius=4):
    """Nearest spot that is free in the game and clear of every footprint planned so far (taken = list of (x, y, half))."""
    odd = name in ("agricultural-tower",)
    code = HELP + (
        "local c={} for x=%d,%d do for y=%d,%d do local p=%s if ok(p,%s) then c[#c+1]={p[1],p[2],(p[1]-(%s))^2+(p[2]-(%s))^2} end end end "
        "table.sort(c,function(a,b) return a[3]<b[3] end) local o={} for i=1,math.min(80,#c) do o[#o+1]={c[i][1],c[i][2]} end rcon.print(helpers.table_to_json(o))"
    ) % (int(x) - radius, int(x) + radius, int(y) - radius, int(y) + radius, "{x+0.5,y+0.5}" if odd else "{x,y}", h, x, y)
    cand = json.loads(L(code) or "[]")
    for cx, cy in cand:
        if all(abs(cx - t[0]) >= h + t[2] or abs(cy - t[1]) >= h + t[2] for t in taken):
            return (cx, cy)
    return None


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def plan(kind, n):
    k = KIND[kind]
    infra = existing_infra()
    poles = [tuple(p) for p in infra["poles"]]
    ports = [tuple(p) for p in infra["ports"]]
    towers = existing_towers()
    sites = find_sites(kind, n, towers)
    P = G.Plan()
    notes = []
    taken = []
    for c, x, y in sites:      # every tower's footprint is reserved first, so no roboport or substation lands on another tower's chests
        taken += [(x, y, 1.5), (x, y + 2, .5), (x, y + 3, .5), (x + 2, y, .5), (x + 3, y, .5)]
    for c, x, y in sites:
        tower = (x, y)
        # robots: roboport within reach of both chests
        if min(dist(tower, p) for p in ports) > NET_REACH:
            rp = snap("roboport", 2, x - 7, y - 7, taken, 6) or snap("roboport", 2, x + 7, y + 7, taken, 6)
            if not rp:
                notes.append("no roboport spot for %s" % (tower,))
                continue
            if min(dist(rp, p) for p in ports) > 48:
                notes.append("site %s: roboport at %s is %.0f from the network (>48): needs an intermediate roboport, skipped" % (tower, rp, min(dist(rp, p) for p in ports)))
                continue
            taken.append((rp[0], rp[1], 2))
            ports.append(rp)
            P.add("roboport", rp[0], rp[1], 0, None, G.Q)
        # power: substation beside the tower (supply 9 reaches tower, chests, inserters, roboport), chained from the nearest pole
        sub = snap("substation", 1, x + 5, y - 5, taken, 4)
        if not sub:
            notes.append("no substation spot for %s" % (tower,))
            continue
        near = min(poles, key=lambda p: dist(p, sub))
        chain = []
        cur = near
        guard = 0
        while dist(cur, sub) > 16 and guard < 12:
            guard += 1
            t = 16.0 / dist(cur, sub)
            tx, ty = cur[0] + (sub[0] - cur[0]) * t, cur[1] + (sub[1] - cur[1]) * t
            sp = snap("substation", 1, tx, ty, taken, 6)
            if not sp or dist(cur, sp) > 17.5:
                notes.append("chain broke near %s" % ((tx, ty),))
                chain = None
                break
            chain.append(sp)
            taken.append((sp[0], sp[1], 1))
            poles.append(sp)
            cur = sp
        if chain is None:
            continue
        for sp in chain:
            P.add("substation", sp[0], sp[1], 0, None, G.Q)
        if dist(cur, sub) > 17.5:
            notes.append("final hop too long near %s" % (tower,))
            continue
        taken.append((sub[0], sub[1], 1))
        poles.append(sub)
        P.add("substation", sub[0], sub[1], 0, None, G.Q)
        G.farm(P, tower, k["seed"], kind, side_in=True)
        towers.append(tower)
        notes.append("%s tower at %s (soil %d)%s" % (kind, tower, c, ", chain %d substations" % len(chain) if chain else ""))
    return P, notes


def run(cmd, kind, n):
    P, notes = plan(kind, n)
    for line in notes:
        print(line)
    print("entities", len(P.ents))
    if cmd == "sites" or not P.ents:
        return
    print(G.clear_plants(P, cmd == "build"))
    if cmd == "dry":
        placed, failed = G.place(P, True)
        print("dry run ok", placed, "failed", json.dumps(failed)[:2500])
        return
    tools["save_game"]("skippy")
    placed, failed = G.place(P, False)
    print("placed", placed, "failed", json.dumps(failed)[:2500])
    for r in G.cfg_lua(P):
        print(r)
    print(deliver(kind))


def deliver(kind):
    """Harvested fruit from the cleared plants goes to the newest fruit chests of that kind."""
    code = ("local s=game.surfaces.gleba local inv=storage.gleba_cell_harvest if not inv then rcon.print('nothing harvested') return end "
            "local c=inv.get_item_count('%s') if c==0 then rcon.print('no %s to deliver') return end local best=nil for _,t in pairs(s.find_entities_filtered{name='agricultural-tower'}) do "
            "local ch=s.find_entities_filtered{name='passive-provider-chest',position={t.position.x,t.position.y+3},radius=0.3}[1] if ch and ch.get_item_count('%s')==0 and (not best) then best=ch end end "
            "if best then local m=best.insert{name='%s',count=c} inv.remove{name='%s',count=m} rcon.print('delivered %s '..m) else rcon.print('no empty fruit chest') end"
            ) % ((kind,) * 6)
    return L(code)


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)
    run(sys.argv[1], sys.argv[2], int(sys.argv[3]))
