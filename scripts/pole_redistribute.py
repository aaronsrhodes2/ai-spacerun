#!/usr/bin/env python3
"""Re-distribute electric poles after a quality upgrade (the Captain, 2026-11-15: "anything that had an area of effect like power poles ... remove them all and
re-distribute them according to their new ranges ... it will have to follow up looking for machines without power").

Why not "remove all, then place again": a pole is a wire between machines and the grid; pulling every pole of a planet at once is a blackout (Gleba had one
the same day) and the robots that would rebuild them need that power. So the same result is reached pole by pole, safely. Legendary changes the ranges a lot
(substation supply 9 -> 14, wire 18 -> 28; medium pole 3.5 -> 8.5, wire 9 -> 19; big pole 2 -> 7); roboport radii and beacon range do not change with quality.

A pole is REMOVED only if (1) every machine in its supply area that is connected today is still inside the supply area of another pole, and (2) its wire
neighbours can be joined to each other (existing wires, or new ones within both poles' wire reach and the 5-wire limit) so no part of the grid is cut off.
Smallest supply areas go first. Every batch is followed by a scan for machines that LOST power; if any, the batch is put back (poles re-created, wires restored)
and the run stops. At the end `followup` lists every machine without power on the planet.

Usage: pole_redistribute.py baseline|plan|apply|followup|rollback SURFACE [--limit N] [--batch N]
  baseline  remember which machines are without power now (do this first; apply refuses without it)
  plan      count what could be removed, change nothing
  apply     remove in batches, verify after each, roll the batch back on any new unpowered machine
  followup  list machines without power now (new ones since the baseline are marked)
  rollback  put back the last batch
"""
import json
import sys
import time

from _game import tools

LIB = """
local f=game.forces.player local s=game.surfaces['%(surf)s']
storage.pole_undo=storage.pole_undo or {} storage.pole_cursor=storage.pole_cursor or {} storage.pole_base=storage.pole_base or {}
local WC=defines.wire_connector_id.pole_copper local WO=defines.wire_origin.script
local function sd(p) return p.prototype.get_supply_area_distance(p.quality) end
local function wr(p) return p.prototype.get_max_wire_distance(p.quality) end
local function covers(q,bb) local d=sd(q) local x,y=q.position.x,q.position.y return not (bb.right_bottom.x<=x-d or bb.left_top.x>=x+d or bb.right_bottom.y<=y-d or bb.left_top.y>=y+d) end
local function conn(p) return p.get_wire_connector(WC,true) end
local function nbrs(p) local r={} local c=p.get_wire_connector(WC,false) if c then for _,cn in pairs(c.connections) do local t=cn.target if t and t.owner and t.owner.valid and t.owner~=p then r[#r+1]=t.owner end end end return r end
local function wired(a,b) for _,n in pairs(nbrs(a)) do if n==b then return true end end return false end
local function powered(e) if e.type=='electric-pole' or e.type=='entity-ghost' then return false end if not e.prototype.electric_energy_source_prototype then return false end local ok,id=pcall(function() return e.electric_network_id end) return ok and id~=nil end
local function covered_by_other(e,p) local bb=e.bounding_box local ex=16 for _,q in pairs(s.find_entities_filtered{type='electric-pole',force=f,area={{bb.left_top.x-ex,bb.left_top.y-ex},{bb.right_bottom.x+ex,bb.right_bottom.y+ex}}}) do if q~=p and q.valid and covers(q,bb) then return true end end return false end
"""

UNPOWERED = LIB + """
local list={} for _,e in pairs(s.find_entities_filtered{force=f}) do if e.type~='electric-pole' and e.type~='entity-ghost' and e.type~='solar-panel' and e.type~='accumulator' and e.prototype.electric_energy_source_prototype and e.unit_number then
if e.status==defines.entity_status.no_power then list[#list+1]={e.unit_number,e.name,e.position.x,e.position.y} end end end
rcon.print(helpers.table_to_json(list))
"""

BASELINE = LIB + """
local base={} local n=0 for _,e in pairs(s.find_entities_filtered{force=f}) do if e.type~='electric-pole' and e.type~='entity-ghost' and e.type~='solar-panel' and e.type~='accumulator' and e.prototype.electric_energy_source_prototype and e.unit_number then
if e.status==defines.entity_status.no_power then base[e.unit_number]=true n=n+1 end end end
local sd0=0 for _,e in pairs(s.find_entities_filtered{force=f,type={'solar-panel','accumulator'}}) do local ok,id=pcall(function() return e.electric_network_id end) if not(ok and id~=nil) then sd0=sd0+1 end end storage.pole_solar=storage.pole_solar or {} storage.pole_solar['%(surf)s']=sd0
storage.pole_base['%(surf)s']=base storage.pole_undo['%(surf)s']=nil storage.pole_cursor['%(surf)s']=nil
local np=s.count_entities_filtered{force=f,type='electric-pole'}
rcon.print(helpers.table_to_json({unpowered_now=n,poles=np,solar_unconnected=sd0}))
"""

# one batch: examine up to %(batch)d candidate poles, remove the removable ones if apply
STEP = LIB + """
local apply=%(apply)s local batch=%(batch)d local sname='%(surf)s'
local cur=storage.pole_cursor[sname]
if not cur then cur={} local arr={} for _,p in pairs(s.find_entities_filtered{type='electric-pole',force=f}) do arr[#arr+1]={sd(p),p.position.x,p.position.y} end table.sort(arr,function(a,b) return a[1]<b[1] end) for i,a in ipairs(arr) do cur[i]={a[2],a[3]} end storage.pole_cursor[sname]=cur storage.pole_pos=1 end
storage.pole_pos=storage.pole_pos or 1
local res={examined=0,removed=0,kept_cover=0,kept_wire=0,gone=0,total=#cur}
local undo={}
local want=%(limit)d
while storage.pole_pos<=#cur and res.examined<batch and res.removed<want do
  local pos=cur[storage.pole_pos] storage.pole_pos=storage.pole_pos+1
  local p=s.find_entities_filtered{type='electric-pole',force=f,position=pos,radius=0.2}[1]
  if not(p and p.valid) then res.gone=res.gone+1 else
    res.examined=res.examined+1
    local d=sd(p) local x,y=p.position.x,p.position.y
    local ok=true
    for _,e in pairs(s.find_entities_filtered{area={{x-d,y-d},{x+d,y+d}}}) do if powered(e) and covers(p,e.bounding_box) and not covered_by_other(e,p) then ok=false break end end
    if not ok then res.kept_cover=res.kept_cover+1 else
      local N=nbrs(p) local comp={} for i=1,#N do comp[i]=i end
      local function find(i) while comp[i]~=i do i=comp[i] end return i end
      for i=1,#N do for j=i+1,#N do if wired(N[i],N[j]) then comp[find(i)]=find(j) end end end
      local edges={} local good=true
      local function ncomp() local c={} local k=0 for i=1,#N do local r=find(i) if not c[r] then c[r]=true k=k+1 end end return k end
      local guard=0
      while ncomp()>1 and guard<8 do guard=guard+1 local bi,bj,bd=nil,nil,1e9
        for i=1,#N do for j=i+1,#N do if find(i)~=find(j) then local dx,dy=N[i].position.x-N[j].position.x,N[i].position.y-N[j].position.y local dist=math.sqrt(dx*dx+dy*dy)
          if dist<=math.min(wr(N[i]),wr(N[j])) and #conn(N[i]).connections<5 and #conn(N[j]).connections<5 and dist<bd then bd=dist bi=i bj=j end end end end
        if bi then edges[#edges+1]={bi,bj} comp[find(bi)]=find(bj) else good=false break end end
      if not good or ncomp()>1 then res.kept_wire=res.kept_wire+1 else
        res.removed=res.removed+1
        if apply then
          local rec={name=p.name,q=p.quality.name,x=x,y=y,nb={},added={}}
          for _,n in pairs(N) do rec.nb[#rec.nb+1]={n.position.x,n.position.y} end
          for _,ed in pairs(edges) do local a,b=N[ed[1]],N[ed[2]] conn(a).connect_to(conn(b),false,WO) rec.added[#rec.added+1]={a.position.x,a.position.y,b.position.x,b.position.y} end
          p.destroy() undo[#undo+1]=rec
        end
      end
    end
  end
end
if apply and #undo>0 then storage.pole_undo[sname]=storage.pole_undo[sname] or {} local b=storage.pole_undo[sname] b[#b+1]=undo end
res.left=#cur-storage.pole_pos+1
rcon.print(helpers.table_to_json(res))
"""

VERIFY = LIB + """
local base=storage.pole_base['%(surf)s'] or {} local new={} local n=0
for _,e in pairs(s.find_entities_filtered{force=f}) do if e.type~='electric-pole' and e.type~='entity-ghost' and e.type~='solar-panel' and e.type~='accumulator' and e.prototype.electric_energy_source_prototype and e.unit_number then
if e.status==defines.entity_status.no_power and not base[e.unit_number] then n=n+1 if #new<12 then new[#new+1]=e.name..'@'..string.format('%%.0f,%%.0f',e.position.x,e.position.y) end end end end
local sdn=0 for _,e in pairs(s.find_entities_filtered{force=f,type={'solar-panel','accumulator'}}) do local ok,id=pcall(function() return e.electric_network_id end) if not(ok and id~=nil) then sdn=sdn+1 end end local sb=(storage.pole_solar or {})['%(surf)s'] or 0 if sdn>sb then n=n+(sdn-sb) new[#new+1]='solar panels / accumulators cut off: '..(sdn-sb) end
rcon.print(helpers.table_to_json({new_unpowered=n,sample=new}))
"""

ROLLBACK = LIB + """
local b=storage.pole_undo['%(surf)s'] if not b or #b==0 then rcon.print(helpers.table_to_json({restored=0})) return end
local undo=table.remove(b) local made=0 local wires=0
for _,rec in pairs(undo) do local p=s.create_entity{name=rec.name,position={rec.x,rec.y},force=f,quality=rec.q,raise_built=true} if p then made=made+1
  for _,pos in pairs(rec.nb) do local o=s.find_entities_filtered{type='electric-pole',force=f,position=pos,radius=0.2}[1] if o and o~=p and not wired(p,o) then local dx,dy=o.position.x-p.position.x,o.position.y-p.position.y if math.sqrt(dx*dx+dy*dy)<=math.min(wr(p),wr(o)) then conn(p).connect_to(conn(o),false,WO) wires=wires+1 end end end end end
rcon.print(helpers.table_to_json({restored=made,wires=wires}))
"""


def run(code, **kw):
    out = tools["run_lua"](" ".join((code % kw).split("\n"))).strip()
    if out.startswith("{") and '"result"' in out[:12]:
        out = json.loads(out)["result"]
    try:
        return json.loads(out)
    except ValueError:
        raise SystemExit("unexpected reply: " + out[:600])


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return
    cmd, surf = sys.argv[1], sys.argv[2]
    args = sys.argv[3:]
    limit = int(args[args.index("--limit") + 1]) if "--limit" in args else 10 ** 6
    batch = int(args[args.index("--batch") + 1]) if "--batch" in args else 40
    if cmd == "baseline":
        print(run(BASELINE, surf=surf))
    elif cmd == "followup":
        new = run(VERIFY, surf=surf)
        lst = run(UNPOWERED, surf=surf)
        names = {}
        for _, n, _, _ in lst:
            names[n] = names.get(n, 0) + 1
        print("%s: %d machines without power now; %d are new since the baseline %s" % (surf, len(lst), new["new_unpowered"], new["sample"]))
        print("by kind:", json.dumps(dict(sorted(names.items(), key=lambda kv: -kv[1])[:15])))
    elif cmd == "rollback":
        print(run(ROLLBACK, surf=surf))
    elif cmd in ("plan", "apply"):
        if cmd == "apply":
            have = run("local b=storage.pole_base and storage.pole_base['%(surf)s'] rcon.print(helpers.table_to_json({baseline=b~=nil}))", surf=surf)
            if not have["baseline"]:
                raise SystemExit("run `baseline %s` first" % surf)
        run("storage.pole_cursor=storage.pole_cursor or {} storage.pole_cursor['%(surf)s']=nil rcon.print('{}')", surf=surf)
        tot = {"examined": 0, "removed": 0, "kept_cover": 0, "kept_wire": 0}
        removed_total = 0
        while True:
            r = run(STEP, surf=surf, apply="true" if cmd == "apply" else "false", batch=batch, limit=max(0, limit - removed_total))
            for k in tot:
                tot[k] += r[k]
            removed_total += r["removed"]
            print("  batch: %s" % json.dumps(r), flush=True)
            if cmd == "apply" and r["removed"] > 0:
                time.sleep(3)          # machine statuses update on the next ticks, not in the tick the pole is removed
                v = run(VERIFY, surf=surf)
                if v["new_unpowered"] > 0:
                    print("  !! %d machines lost power %s: putting the batch back" % (v["new_unpowered"], v["sample"]))
                    print("  rollback:", run(ROLLBACK, surf=surf))
                    break
            if r["left"] <= 0 or removed_total >= limit or r["examined"] == 0:
                break
        print("%s %s: %s" % (surf, cmd, json.dumps(tot)))


if __name__ == "__main__":
    main()
