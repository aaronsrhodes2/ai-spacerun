"""
Turn every storage chest back into a steel chest and take the robot-dumped junk out of them.

Why: a storage chest joins the logistic network. Once fx.py upgraded the plain chests to storage chests, robots filled them with
whatever they carried (old belts, inserters, wood, machines) and the network treated every buffer chest as free stock.
A steel chest is invisible to the network again.

What is kept, what moves (nothing is destroyed):
  - a chest with an inserter on it keeps its main item (the one that is at least 70 % of its contents): that is its job (science pack
    buffer, plate stock, uranium ore, ...);
  - everything else (all contents of a chest no inserter touches, and the odd items in the others) is moved into a stash of plain steel chests
    placed near --stash X Y, which are not in the network. Delete them later if you really want the items gone.

Usage: scripts/revert_storage_chests.py [--stash X Y] [--apply]
"""
import argparse

import fx

LUA = """
local s=game.surfaces.nauvis local f=game.forces.player local apply=%(apply)s local cx,cy=%(cx)s,%(cy)s
local function key(it) return it.name..'|'..(it.quality or 'normal') end
local cs=s.find_entities_filtered{name='storage-chest',force=f}
local plan={} local tally={} local stacks=0 local kept={}
for _,c in pairs(cs) do
  local x,y=c.position.x,c.position.y local links=0
  for _,i in pairs(s.find_entities_filtered{type='inserter',area={{x-1.6,y-1.6},{x+1.6,y+1.6}}}) do
    local pp,dp=i.pickup_position,i.drop_position
    if (math.abs(pp.x-x)<0.5 and math.abs(pp.y-y)<0.5) or (math.abs(dp.x-x)<0.5 and math.abs(dp.y-y)<0.5) then links=links+1 end
  end
  local cont=c.get_inventory(defines.inventory.chest).get_contents() local tot=0 local top=nil
  for _,it in pairs(cont) do tot=tot+it.count if not top or it.count>top.count then top=it end end
  local keep=nil if links>0 and top and top.count>=0.7*tot then keep=key(top) kept[top.name]=(kept[top.name] or 0)+top.count end
  local junk={}
  for _,it in pairs(cont) do if key(it)~=keep then junk[#junk+1]={name=it.name,quality=it.quality or 'normal',count=it.count} tally[it.name]=(tally[it.name] or 0)+it.count stacks=stacks+math.ceil(it.count/prototypes.item[it.name].stack_size) end end
  plan[#plan+1]={pos=c.position,junk=junk}
end
local need=math.ceil(stacks/48)+2
local res={chests=#cs,junk_stacks=stacks,stash_chests=need,junk=tally,kept=kept}
if not apply then rcon.print(helpers.table_to_json(res)) return end
local stash={}
for k=1,need do
  local p=s.find_non_colliding_position('steel-chest',{cx,cy},80,1)
  local e=p and s.create_entity{name='steel-chest',position=p,force=f}
  if not e then res.error='no room for the stash' rcon.print(helpers.table_to_json(res)) return end
  stash[#stash+1]=e
end
local swapped,left,moved=0,0,0
for _,pl in pairs(plan) do
  local ne=s.create_entity{name='steel-chest',position=pl.pos,force=f,fast_replace=true,spill=false}
  if ne then swapped=swapped+1
    local inv=ne.get_inventory(defines.inventory.chest)
    for _,j in pairs(pl.junk) do
      local remaining=j.count
      for _,st in pairs(stash) do
        if remaining>0 then local n=st.get_inventory(defines.inventory.chest).insert{name=j.name,count=remaining,quality=j.quality}
          if n>0 then inv.remove{name=j.name,count=n,quality=j.quality} remaining=remaining-n moved=moved+n end end
      end
      left=left+remaining
    end
  end
end
local pos={} for _,st in pairs(stash) do pos[#pos+1]={st.position.x,st.position.y} end
res.swapped=swapped res.moved=moved res.left_in_place=left res.stash_at=pos
res.storage_left=#s.find_entities_filtered{name='storage-chest',force=f}
rcon.print(helpers.table_to_json(res))
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stash", nargs=2, type=float, default=[-226.5, -262.5])
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    code = " ".join(line.strip() for line in (LUA % {"apply": "true" if a.apply else "false", "cx": a.stash[0], "cy": a.stash[1]}).splitlines())
    res = fx.jlua(code)
    print(("APPLIED" if a.apply else "DRY RUN (add --apply)"))
    for k in ("chests", "junk_stacks", "stash_chests", "swapped", "moved", "left_in_place", "storage_left", "error"):
        if k in res:
            print(f"  {k}: {res[k]}")
    print("  kept in place:", dict(sorted((res.get("kept") or {}).items(), key=lambda kv: -kv[1])))
    print("  junk to the stash:", dict(sorted((res.get("junk") or {}).items(), key=lambda kv: -kv[1])))
    if res.get("stash_at"):
        print("  stash chests at:", res["stash_at"])


if __name__ == "__main__":
    main()
