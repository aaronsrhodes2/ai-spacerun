"""
Prepares a planet for building after the first landing (scripts/planet_landing.py). Every step works on the square of --radius tiles
around --centre (default 0 0, radius 128) on --surface, and every step is safe to run again.

  generate   generates and charts the chunks, switches the surface to peaceful (the standing rule: biters are off everywhere)
  survey     land share, tiles, natural entities by name, resource patches with their centres
  clear      removes trees, rocks, cliffs, ruins, enemies, decoratives; KEEPS resources, plants (Gleba's yumako trees and jellystems),
             stromatolites, lightning attractors and anything in --keep (name fragments)
  power      lattice of substations at the best researched quality (rare: 22x22 supply, 22 wire reach, pitch 20), land only
  drones     roboports at the best researched quality, one per 48x48 cell with land, on the substation grid
  sites      prints the proposed work sites (resource patch centres) and paves a pad at each plus a 6-wide path from the centre to it
             (refined concrete; ore tiles and Gleba's farm soils are left alone). The Foundation tile is an Aquilo research: liquid stays liquid.
  solar / rods   generation: a block of panels and accumulators, or lightning rods with accumulators (Fulgora), fitted into free land

Entities are placed only when their recipe is researched and the quality is unlocked (the friendly build rule).

Usage: scripts/planet_base.py STEP --surface vulcanus [--centre X Y] [--radius 128] [--apply] [step options]
"""
import argparse
import json

from _game import tools

HEAD = ("local s=game.surfaces['%(surface)s'] local f=game.forces.player local CX,CY,R=%(cx)d,%(cy)d,%(r)d local A={{CX-R,CY-R},{CX+R,CY+R}} local apply=%(apply)s "
        "local best=nil for n,q in pairs(prototypes.quality) do if n~='quality-unknown' and f.is_quality_unlocked(n) and (best==nil or q.level>best.level) then best=q end end "
        "local function land(x,y) local t=s.get_tile(x,y) return t.valid and not t.collides_with('water_tile') end "
        "local function ok(n) local r=f.recipes[n] return r and r.enabled end "
        "local function put(n,x,y) if not ok(n) then return nil end if not s.can_place_entity{name=n,position={x,y},force=f} then return nil end return s.create_entity{name=n,position={x,y},force=f,quality=best.name} end ")

GENERATE = ("s.request_to_generate_chunks({CX,CY},math.ceil(R/32)+1) s.force_generate_chunk_requests() f.chart(s,A) s.peaceful_mode=true local n=0 for _ in s.get_chunks() do n=n+1 end "
            "rcon.print('chunks '..n..' peaceful '..tostring(s.peaceful_mode))")

SURVEY = ("local tiles={} local L,T=0,0 for x=CX-R,CX+R-1,4 do for y=CY-R,CY+R-1,4 do local t=s.get_tile(x,y) T=T+1 if not t.collides_with('water_tile') then L=L+1 end tiles[t.name]=(tiles[t.name] or 0)+1 end end "
          "local nat={} for _,e in pairs(s.find_entities_filtered{area=A}) do if e.force.name~='player' and e.type~='resource' then local k=e.type..'/'..e.name..(e.force.name=='enemy' and '(enemy)' or '') nat[k]=(nat[k] or 0)+1 end end "
          "local res={} for _,e in pairs(s.find_entities_filtered{area=A,type='resource'}) do local gx,gy=math.floor(e.position.x/64),math.floor(e.position.y/64) local k=e.name..'|'..gx..'|'..gy "
          "local r=res[k] or {n=0,x=0,y=0,a=0} r.n=r.n+1 r.x=r.x+e.position.x r.y=r.y+e.position.y r.a=r.a+e.amount res[k]=r end "
          "local out={} for k,r in pairs(res) do out[#out+1]={k=k,n=r.n,x=math.floor(r.x/r.n),y=math.floor(r.y/r.n),amount=r.a} end "
          "rcon.print(helpers.table_to_json({land=L/T,tiles=tiles,natural=nat,resources=out,ours=s.count_entities_filtered{area=A,force=f}}))")

CLEAR = ("local keep={%(keep)s} local out={} local function kept(e) if e.type=='plant' or e.type=='resource' or e.type=='lightning-attractor' then return true end for _,k in pairs(keep) do if e.name:find(k,1,true) then return true end end return false end "
         "for _,e in pairs(s.find_entities_filtered{area=A,type={'tree','simple-entity','cliff','fish','corpse','rail-remnants','unit','unit-spawner','turret','segmented-unit','spider-unit','segment','spider-leg'}}) do "
         "if e.valid and e.force.name~='player' then if kept(e) then out['kept '..e.name]=(out['kept '..e.name] or 0)+1 else out[e.type]=(out[e.type] or 0)+1 if apply then e.destroy() end end end end "
         "for _,e in pairs(s.find_entities_filtered{area=A,force='enemy'}) do if e.valid then out['enemy '..e.type]=(out['enemy '..e.type] or 0)+1 if apply then e.destroy() end end end "
         "local d=0 for _,x in pairs(s.find_decoratives_filtered{area=A}) do d=d+(x.amount or 1) end out.decoratives=d if apply then s.destroy_decoratives{area=A} end "
         "for _,e in pairs(s.find_entities_filtered{area=A,type='plant'}) do out['kept '..e.name]=(out['kept '..e.name] or 0)+1 end "
         "rcon.print(helpers.table_to_json(out))")

# lattice of one entity: pitch P, shift up to SH tiles around a blocked point; a point is used when its tile is land and nothing of that name stands within NEAR
LATTICE = ("local name,P,SH,NEAR,W='%(name)s',%(pitch)d,%(shift)d,%(near)d,%(w)d local n,miss,have=0,0,0 "
           "for gx=math.ceil((CX-R)/P),math.floor((CX+R)/P) do for gy=math.ceil((CY-R)/P),math.floor((CY+R)/P) do local x0,y0=gx*P,gy*P "
           "if s.count_entities_filtered{name=name,force=f,area={{x0-NEAR,y0-NEAR},{x0+NEAR,y0+NEAR}}}>0 then have=have+1 else local done=false local anyland=false "
           "for d=0,SH do if done then break end for dx=-d,d do if done then break end for dy=-d,d do if math.max(math.abs(dx),math.abs(dy))==d then local x,y=x0+dx,y0+dy "
           "local fits=true for ix=0,W-1 do for iy=0,W-1 do if not land(x-W/2+ix,y-W/2+iy) then fits=false end end end "
           "if fits then anyland=true if s.can_place_entity{name=name,position={x,y},force=f} and ok(name) then if apply then put(name,x,y) end n=n+1 done=true break end end end end end end "
           "if not done and anyland then miss=miss+1 end end end end "
           "rcon.print(helpers.table_to_json({placed=n,already=have,no_room=miss,quality=best.name,researched=ok(name)}))")

# refined concrete pads at the work sites and 6-wide paths from the centre (east-west first, then north-south); liquids, ore and Gleba's farm soils stay
SITES = ("local sites={%(sites)s} local PAD=%(pad)d local tiles={} local seen={} local wet,soil,ore=0,0,0 "
         "local function pave(x,y) local k=x..','..y if seen[k] then return end seen[k]=true local t=s.get_tile(x,y) if not t.valid then return end if t.collides_with('water_tile') then wet=wet+1 return end "
         "if t.name=='refined-concrete' then return end if t.name:find('yumako',1,true) or t.name:find('jellynut',1,true) then soil=soil+1 return end "
         "if s.count_entities_filtered{area={{x,y},{x+1,y+1}},type='resource'}>0 then ore=ore+1 return end tiles[#tiles+1]={name='refined-concrete',position={x,y}} end "
         "for _,q in pairs(sites) do for dx=-PAD,PAD-1 do for dy=-PAD,PAD-1 do pave(q[1]+dx,q[2]+dy) end end "
         "for x=math.min(CX,q[1])-3,math.max(CX,q[1])+2 do for w=-3,2 do pave(x,CY+w) end end for y=math.min(CY,q[2])-3,math.max(CY,q[2])+2 do for w=-3,2 do pave(q[1]+w,y) end end end "
         "local can=ok('refined-concrete') if apply and can then s.set_tiles(tiles) end rcon.print(helpers.table_to_json({paved=#tiles,liquid_skipped=wet,soil_skipped=soil,ore_skipped=ore,researched=can}))")

# solar cells: the 18x18 inside of a substation lattice cell holds 24 panels and 27 accumulators; only cells that are all land, unpaved and empty, nearest the centre first
SOLAR = ("local P,N=20,%(cells)d local cells={} for gx=math.ceil((CX-R)/P),math.floor((CX+R)/P)-1 do for gy=math.ceil((CY-R)/P),math.floor((CY+R)/P)-1 do cells[#cells+1]={gx*P,gy*P,(gx*P+10-CX)^2+(gy*P+10-CY)^2} end end "
         "table.sort(cells,function(a,b) return a[3]<b[3] end) local used,pan,acc=0,0,0 for _,c in ipairs(cells) do if used>=N then break end local x0,y0=c[1]+1,c[2]+1 local B={{x0,y0},{x0+18,y0+18}} "
         "if s.count_tiles_filtered{area=B,collision_mask='water_tile'}==0 and s.count_tiles_filtered{area=B,name='refined-concrete'}==0 and s.count_entities_filtered{area=B}==0 "
         "and s.count_entities_filtered{area={{c[1]-8,c[2]-8},{c[1]+28,c[2]+28}},name='substation',force=f}>0 then used=used+1 local y=y0 for row=1,7 do "
         "if row%%2==1 then for i=0,5 do if (not apply) or put('solar-panel',x0+i*3+1.5,y+1.5) then pan=pan+1 end end y=y+3 else for i=0,8 do if (not apply) or put('accumulator',x0+i*2+1,y+1) then acc=acc+1 end end y=y+2 end end end end "
         "rcon.print(helpers.table_to_json({cells=used,panels=pan,accumulators=acc,quality=best.name,researched=ok('solar-panel') and ok('accumulator')}))")

# Fulgora: a lightning rod and four accumulators at every substation
RODS = ("local rods,acc,have=0,0,0 for _,e in pairs(s.find_entities_filtered{area=A,name='substation',force=f}) do local x,y=e.position.x,e.position.y "
        "if s.count_entities_filtered{name='lightning-rod',force=f,area={{x-3,y-3},{x+3,y+3}}}>0 then have=have+1 else "
        "if s.can_place_entity{name='lightning-rod',position={x+1.5,y+0.5},force=f} and ok('lightning-rod') then rods=rods+1 if apply then put('lightning-rod',x+1.5,y+0.5) end end "
        "for _,d in pairs({{-2,0},{0,-2},{0,2},{3,0}}) do if s.can_place_entity{name='accumulator',position={x+d[1],y+d[2]},force=f} and ok('accumulator') then acc=acc+1 if apply then put('accumulator',x+d[1],y+d[2]) end end end end end "
        "rcon.print(helpers.table_to_json({rods=rods,accumulators=acc,already=have,quality=best.name,researched=ok('lightning-rod')}))")

NETS = ("local ids={} local n=0 for _,e in pairs(s.find_entities_filtered{area=A,force=f,type='%s'}) do n=n+1 local id=(e.type=='roboport') and (e.logistic_network and e.logistic_network.network_id or -1) or e.electric_network_id "
        "ids[id]=(ids[id] or 0)+1 end local o={} for k,v in pairs(ids) do o[#o+1]=k..':'..v end rcon.print(n..' entities, networks '..table.concat(o,' '))")


def lua(a, body, **kw):
    cx, cy = a.centre
    code = (HEAD % dict(surface=a.surface, cx=cx, cy=cy, r=a.radius, apply="true" if a.apply else "false")) + (body % kw if kw else body)
    return tools["run_lua"](" ".join(code.split())).strip()


def jl(a, body, **kw):
    out = lua(a, body, **kw)
    if not out.startswith(("{", "[")):
        raise SystemExit("unexpected reply: " + out[:800])
    d = json.loads(out)
    return json.loads(d["result"]) if isinstance(d, dict) and isinstance(d.get("result"), str) else d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["generate", "survey", "clear", "power", "drones", "sites", "solar", "rods"])
    ap.add_argument("--surface", required=True)
    ap.add_argument("--centre", nargs=2, type=int, default=[0, 0])
    ap.add_argument("--radius", type=int, default=128)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--keep", nargs="*", default=["stromatolite", "vault"])
    ap.add_argument("--cells", type=int, default=8, help="solar: how many lattice cells to fill")
    ap.add_argument("--pad", type=int, default=16, help="sites: half width of the paved pad")
    ap.add_argument("--min-tiles", type=int, default=20, help="sites: smallest resource patch that counts as a work site")
    a = ap.parse_args()
    if a.step == "generate":
        print(lua(a, GENERATE))
    elif a.step == "survey":
        d = jl(a, SURVEY)
        print(f"{a.surface}: land {d['land']:.0%}, ours {d['ours']}")
        print("  tiles:", ", ".join(f"{k} {v}" for k, v in sorted((d["tiles"] or {}).items(), key=lambda kv: -kv[1])))
        print("  natural:", ", ".join(f"{k} {v}" for k, v in sorted((d["natural"] or {}).items(), key=lambda kv: -kv[1])))
        for r in sorted(d["resources"] or [], key=lambda r: r["k"]):
            print(f"  resource {r['k'].split('|')[0]} at ({r['x']},{r['y']}): {r['n']} tiles, {r['amount']}")
    elif a.step == "clear":
        d = jl(a, CLEAR, keep=",".join("'%s'" % k for k in a.keep))
        print(("CLEARED" if a.apply else "DRY RUN"), a.surface, json.dumps(d, sort_keys=True))
    elif a.step == "power":
        print(("PLACED" if a.apply else "DRY RUN"), "substations:", jl(a, LATTICE, name="substation", pitch=20, shift=6, near=7, w=2))
        print("  " + lua(a, NETS % "electric-pole"))
    elif a.step == "drones":
        print(("PLACED" if a.apply else "DRY RUN"), "roboports:", jl(a, LATTICE, name="roboport", pitch=48, shift=12, near=16, w=4))
        print("  " + lua(a, NETS % "roboport"))
    elif a.step == "sites":
        sites = []  # the survey counts per 64-tile square: pieces of one patch (same resource, centres within 64 tiles) are merged
        for r in sorted(jl(a, SURVEY)["resources"] or [], key=lambda r: -r["n"]):
            name = r["k"].split("|")[0]
            for q in sites:
                if q["k"] == name and abs(q["x"] - r["x"]) <= 64 and abs(q["y"] - r["y"]) <= 64:
                    n = q["n"] + r["n"]
                    q["x"], q["y"], q["n"] = round((q["x"] * q["n"] + r["x"] * r["n"]) / n), round((q["y"] * q["n"] + r["y"] * r["n"]) / n), n
                    break
            else:
                sites.append(dict(k=name, x=r["x"], y=r["y"], n=r["n"]))
        sites = [q for q in sites if q["n"] >= a.min_tiles]
        for r in sites:
            print(f"  work site {r['k'].split('|')[0]} at ({r['x']},{r['y']})")
        print(("PAVED" if a.apply else "DRY RUN"), jl(a, SITES, sites=",".join("{%d,%d}" % (r["x"], r["y"]) for r in sites), pad=a.pad))
    elif a.step == "solar":
        print(("PLACED" if a.apply else "DRY RUN"), "solar:", jl(a, SOLAR, cells=a.cells))
    elif a.step == "rods":
        print(("PLACED" if a.apply else "DRY RUN"), "lightning rods:", jl(a, RODS))


if __name__ == "__main__":
    main()
