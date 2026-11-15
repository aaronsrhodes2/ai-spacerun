#!/usr/bin/env python3
"""Gleba nuclear heat for the cold exchanger pairs (2026-11-15, the Captain: "build more reactors for the cold pairs", after the spoilage / jellynut burners were
retired). Three exchanger/turbine pairs have heat-pipe clusters but no heat source: (119.5,27), (134.5,15), (130.5,47). Their old heating towers are gone and the cells
are packed with belts, so this script finds a free 5x5 spot near each cluster, links it to the cluster with a heat-pipe path (BFS over free tiles), and builds the
same fuel feed the Gleba reactor (57.5,3.5) has: a requester chest for 6 uranium fuel cells -> inserter into the reactor, run only while the reactor is below 700 degrees
(circuit: the reactor reports its temperature as signal-R, the inserter's enable condition is signal-R < 700), and an inserter taking spent cells out into a passive
provider chest. Cells reach Gleba through the pad request "reactor cells (gleba)" (raised here so every reactor has its 6 plus a reserve).

Usage: gleba_reactors.py plan | build [--apply] | status
  plan    shows the chosen site, pipe path length and feed tiles per cluster (reads only)
  build   place_entities dry run, with --apply places and configures (circuit, request)
  status  reactors, temperatures, fuel, exchanger states"""
import json
import sys

from _game import tools

L = tools["run_lua"]
SURF = "gleba"
CLUSTERS = [(119.5, 20.5, 123.5, 25.5), (131.5, 13.5, 134.5, 16.5), (129.5, 45.5, 130.5, 45.5)]   # heat-pipe clusters of the cold pairs (x1, y1, x2, y2)
RANGE = 26          # how far from a cluster a reactor may sit
MAXPIPE = 45        # longest heat-pipe link allowed

PLAN = r"""
local g=game.surfaces.gleba local f=game.forces.player
local function can(n,x,y,d) return g.can_place_entity{name=n,position={x,y},direction=d or 0,force=f} end
local CL=CLUSTERS
local hp=g.find_entities_filtered{name='heat-pipe',force=f}
local pipeAt={} for _,p in pairs(hp) do pipeAt[p.position.x..','..p.position.y]=1 end
local out={} local used={}
local DIR={{0,-1},{1,0},{0,1},{-1,0}}
for ci,cl in ipairs(CL) do
  local cx0,cy0=(cl[1]+cl[3])/2,(cl[2]+cl[4])/2
  local mine={} for _,p in pairs(hp) do local x,y=p.position.x,p.position.y if x>=cl[1] and x<=cl[3] and y>=cl[2] and y<=cl[4] then mine[x..','..y]=1 end end
  local cands={}
  for dx=-RANGE,RANGE do for dy=-RANGE,RANGE do local x,y=cx0+dx,cy0+dy x=math.floor(x)+0.5 y=math.floor(y)+0.5
    if can('nuclear-reactor',x,y) then cands[#cands+1]={x,y,math.abs(x-cx0)+math.abs(y-cy0)} end end end
  table.sort(cands,function(a,b) return a[3]<b[3] end)
  local best
  for ci2=1,math.min(#cands,150) do local c=cands[ci2] local rx,ry=c[1],c[2]
    local foot={} for ax=-2,2 do for ay=-2,2 do foot[(rx+ax)..','..(ry+ay)]=1 end end
    local function pair(side,off,input)
      local d=DIR[side] local ix,iy=rx+d[1]*3,ry+d[2]*3 local cx,cy=rx+d[1]*4,ry+d[2]*4
      if d[1]==0 then ix=ix+off cx=cx+off else iy=iy+off cy=cy+off end
      local toward={[1]=0,[2]=4,[3]=8,[4]=12} local dirChest=toward[side] local dirReactor=toward[(side+1)%4+1]
      local idir=input and dirChest or dirReactor
      if can('bulk-inserter',ix,iy,idir) and can(input and 'requester-chest' or 'passive-provider-chest',cx,cy) then return {ix,iy,idir,cx,cy} end end
    local inp,outp,inpSide
    for side=1,4 do for _,off in ipairs{0,-1,1,-2,2} do if not inp then inp=pair(side,off,true) if inp then inpSide=side end end end end
    if inp then for side=1,4 do for _,off in ipairs{0,-1,1,-2,2} do if not outp and not (side==inpSide and math.abs(off)<1) then local o2=pair(side,off,false) if o2 and not (o2[1]==inp[1] and o2[2]==inp[2]) and not (o2[4]==inp[4] and o2[5]==inp[5]) then outp=o2 end end end end end
    if inp and outp then
      local blocked={} blocked[inp[1]..','..inp[2]]=1 blocked[inp[4]..','..inp[5]]=1 blocked[outp[1]..','..outp[2]]=1 blocked[outp[4]..','..outp[5]]=1
      local starts={}
      for _,k in ipairs{-2,0,2} do starts[#starts+1]={rx+k,ry-3} starts[#starts+1]={rx+k,ry+3} starts[#starts+1]={rx-3,ry+k} starts[#starts+1]={rx+3,ry+k} end
      local prev={} local dist={} local q={} local goal
      local function free(x,y) local key=x..','..y return not foot[key] and not blocked[key] and not used[key] and can('heat-pipe',x,y) end
      for _,s in ipairs(starts) do local key=s[1]..','..s[2] if free(s[1],s[2]) and not dist[key] then dist[key]=1 q[#q+1]=s prev[key]=false end end
      local qi=1
      while qi<=#q and not goal do local e=q[qi] qi=qi+1 local ek=e[1]..','..e[2]
        for _,d in ipairs(DIR) do local nx,ny=e[1]+d[1],e[2]+d[2] if mine[nx..','..ny] then goal=e break end end
        if not goal and dist[ek]<MAXPIPE then for _,d in ipairs(DIR) do local nx,ny=e[1]+d[1],e[2]+d[2] local nk=nx..','..ny if not dist[nk] and free(nx,ny) then dist[nk]=dist[ek]+1 prev[nk]=ek q[#q+1]={nx,ny} end end end end
      if goal then local path={} local k=goal[1]..','..goal[2] while k do local x,y=k:match('(%S+),(%S+)') path[#path+1]={tonumber(x),tonumber(y)} k=prev[k] end
        if not best or #path<#best.path then best={reactor={rx,ry},path=path,inp=inp,outp=outp} end
        if #path<=6 then break end end end end
  if best then
    out[#out+1]={cluster=ci,reactor=best.reactor,pipes=best.path,inp=best.inp,outp=best.outp}
    for _,p in ipairs(best.path) do used[p[1]..','..p[2]]=1 end
  else out[#out+1]={cluster=ci,none=true} end
end
rcon.print(helpers.table_to_json(out))
"""


def plan():
    code = PLAN.replace("CLUSTERS", "{" + ",".join("{%s,%s,%s,%s}" % c for c in CLUSTERS) + "}").replace("RANGE", str(RANGE)).replace("MAXPIPE", str(MAXPIPE))
    out = L(" ".join(code.split())).strip()
    try:
        return json.loads(out)
    except Exception:
        raise SystemExit("plan failed: " + out[:600])


def entities(p):
    ents = []
    for c in p:
        if c.get("none"):
            continue
        rx, ry = c["reactor"]
        ents.append({"name": "nuclear-reactor", "x": rx, "y": ry})
        for x, y in c["pipes"]:
            ents.append({"name": "heat-pipe", "x": x, "y": y})
        i = c["inp"]
        o = c["outp"]
        ents.append({"name": "requester-chest", "x": i[3], "y": i[4]})
        ents.append({"name": "bulk-inserter", "x": i[0], "y": i[1], "direction": i[2]})
        ents.append({"name": "bulk-inserter", "x": o[0], "y": o[1], "direction": o[2]})
        ents.append({"name": "passive-provider-chest", "x": o[3], "y": o[4]})
    return ents


CONFIG = r"""
local g=game.surfaces.gleba local f=game.forces.player local o={}
local ref=g.find_entities_filtered{name='nuclear-reactor',position={57.5,3.5},radius=0.5}[1]
local sig=ref and ref.get_control_behavior() and ref.get_control_behavior().temperature_signal
for _,c in ipairs(PLAN) do
  local rx=g.find_entities_filtered{name='nuclear-reactor',position=c.reactor,radius=0.5,force=f}[1]
  local ins=g.find_entities_filtered{name='bulk-inserter',position={c.inp[1],c.inp[2]},radius=0.3,force=f}[1]
  local ch=g.find_entities_filtered{name='requester-chest',position={c.inp[4],c.inp[5]},radius=0.3,force=f}[1]
  if rx and ins and ch then
    local cb=rx.get_or_create_control_behavior() cb.read_temperature=true if sig then cb.temperature_signal=sig else cb.temperature_signal={type='virtual',name='signal-R'} end
    local a=rx.get_wire_connector(defines.wire_connector_id.circuit_red,true) local b=ins.get_wire_connector(defines.wire_connector_id.circuit_red,true) a.connect_to(b,false,defines.wire_origin.script)
    local icb=ins.get_or_create_control_behavior() icb.circuit_enable_disable=true icb.circuit_condition={first_signal={type='virtual',name='signal-R'},comparator='<',constant=700}
    local pt=ch.get_logistic_point(defines.logistic_member_index.logistic_container) if pt==nil then local p2=ch.get_logistic_point() pt=p2.mode and p2 or p2[1] end
    local sec=pt.sections[1] or pt.add_section() sec.set_slot(1,{value={type='item',name='uranium-fuel-cell',quality='normal'},min=6})
    o[#o+1]='cluster '..c.cluster..' configured reactor '..rx.position.x..','..rx.position.y
  else o[#o+1]='cluster '..c.cluster..' MISSING parts (reactor '..tostring(rx~=nil)..' inserter '..tostring(ins~=nil)..' chest '..tostring(ch~=nil)..')' end end
rcon.print(table.concat(o,string.char(10)))
"""

PAD = r"""
local g=game.surfaces.gleba local pad=g.find_entities_filtered{type='cargo-landing-pad'}[1] local n=0
for _,pt in pairs(pad.get_logistic_point()) do if pt.mode==defines.logistic_mode.requester then for _,sec in ipairs(pt.sections) do if sec.group=='reactor cells (gleba)' then
  for k=1,sec.filters_count do local fl=sec.get_slot(k) if fl and fl.value and fl.value.name=='uranium-fuel-cell' then
    local nf={value=fl.value,min=MINCELLS,max=fl.max,import_from=fl.import_from and fl.import_from.name,request_from=fl.request_from} pcall(function() sec.set_slot(k,nf) n=n+1 end) end end end end end end
rcon.print('pad reactor-cell request raised on '..n..' slots')
"""

STATUS = r"""
local g=game.surfaces.gleba local f=game.forces.player local o={} local SN={} for k,v in pairs(defines.entity_status) do SN[v]=k end
for _,r in pairs(g.find_entities_filtered{name='nuclear-reactor',force=f}) do o[#o+1]='reactor '..r.position.x..','..r.position.y..' '..tostring(SN[r.status])..' temp '..math.floor(r.temperature)..' cells '..r.get_fuel_inventory().get_item_count('uranium-fuel-cell') end
for _,b in pairs(g.find_entities_filtered{type='boiler',name='heat-exchanger',force=f}) do o[#o+1]='exchanger '..b.position.x..','..b.position.y..' '..tostring(SN[b.status])..' temp '..math.floor(b.temperature or -1) end
for _,t in pairs(g.find_entities_filtered{type='generator',force=f}) do o[#o+1]='turbine '..t.position.x..','..t.position.y..' '..tostring(SN[t.status]) end
rcon.print(table.concat(o,string.char(10)))
"""


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "status":
        print(L(" ".join(STATUS.split())))
        return
    p = plan()
    for c in p:
        if c.get("none"):
            print("cluster %d: no site found within %d tiles (or no pipe path within %d)" % (c["cluster"], RANGE, MAXPIPE))
        else:
            print("cluster %d: reactor at %s, heat-pipe link %d tiles, fuel chest %s, spent-cell chest %s" % (c["cluster"], c["reactor"], len(c["pipes"]), c["inp"][3:5], c["outp"][3:5]))
    if cmd == "plan":
        return
    ents = entities(p)
    dry = "--apply" not in sys.argv
    res = tools["place_entities"](json.dumps(ents), surface=SURF, dry_run=dry)
    print(("dry run: " if dry else "placed: ") + res[:1200])
    if dry:
        return
    cfg = "local PLAN=" + json.dumps([c for c in p if not c.get("none")]).replace("[", "{").replace("]", "}").replace('"cluster":', "cluster=").replace('"reactor":', "reactor=").replace('"pipes":', "pipes=").replace('"inp":', "inp=").replace('"outp":', "outp=") + " " + CONFIG
    print(L(" ".join(cfg.split())))
    print(L(" ".join(PAD.replace("MINCELLS", "120").split())))


if __name__ == "__main__":
    main()
