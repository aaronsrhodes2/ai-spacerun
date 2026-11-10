"""
fx.py logistics survey | convert | retire   (called from fx.py)

Turn a belt-fed factory chunk into a drone-fed one.

  survey   what is in the area: machines (solid or fluid recipes), the belt pieces, the inserters that move items between machines and belts.
  convert  for every assembling machine and furnace with a solid recipe: each belt tile that one of its inserters picks from becomes a blue requester chest
           asking for the recipe's ingredients (about --minutes of work, at most two stacks of an item); each belt tile an inserter drops its product on becomes a
           red passive provider chest. A tile used both ways becomes a provider chest (the machines still hand items on through it). The inserters stay.
           Fluid recipes are skipped. Belts are NOT removed (the cut line keeps carrying what is left); run retire when the area is converted.
  retire   remove belt, underground and splitter groups that lie wholly inside the area and that no inserter, drill or other piece still uses. What they carry is
           salvaged into red provider chests next to the area (nothing is destroyed). Groups that cross the area border are never touched.

Always check with the dry run first (no --apply). --apply saves the game first.
"""
import json

BELT_TYPES = "{'transport-belt','underground-belt','splitter'}"

SURVEY = """
local s=game.surfaces.nauvis local f=game.forces.player local A=%(box)s
local mach={solid=0,fluid=0,idle=0} local recipes={}
for _,m in pairs(s.find_entities_filtered{area=A,force=f,type={'assembling-machine','furnace'}}) do
  local r=m.get_recipe() or (m.type=='furnace' and m.previous_recipe)
  if not r then mach.idle=mach.idle+1 else
    local fl=false for _,i in pairs(r.ingredients) do if i.type=='fluid' then fl=true end end for _,p in pairs(r.products) do if p.type=='fluid' then fl=true end end
    if fl then mach.fluid=mach.fluid+1 else mach.solid=mach.solid+1 recipes[r.name]=(recipes[r.name] or 0)+1 end end
end
local belts={} for _,e in pairs(s.find_entities_filtered{area=A,force=f,type=%(bt)s}) do belts[e.name]=(belts[e.name] or 0)+1 end
local ins={from_belt=0,to_belt=0,other=0}
for _,i in pairs(s.find_entities_filtered{area=A,force=f,type='inserter'}) do
  local pt,dt=i.pickup_target,i.drop_target local pb=pt and (pt.type=='transport-belt' or pt.type=='underground-belt' or pt.type=='splitter') local db=dt and (dt.type=='transport-belt' or dt.type=='underground-belt' or dt.type=='splitter')
  if pb then ins.from_belt=ins.from_belt+1 elseif db then ins.to_belt=ins.to_belt+1 else ins.other=ins.other+1 end end
local items={} for _,e in pairs(s.find_entities_filtered{area=A,force=f,type='transport-belt'}) do for i=1,e.get_max_transport_line_index() do for _,c in pairs(e.get_transport_line(i).get_contents()) do items[c.name]=(items[c.name] or 0)+c.count end end end
rcon.print(helpers.table_to_json({machines=mach,recipes=recipes,belts=belts,inserters=ins,belt_items=items}))
"""

CONVERT = """
local s=game.surfaces.nauvis local f=game.forces.player local A=%(box)s local apply=%(apply)s local minutes=%(minutes)s
local function isbelt(e) return e and (e.name=='transport-belt' or e.name=='fast-transport-belt' or e.name=='express-transport-belt') end
local function isbeltlike(e) return e and (e.type=='transport-belt' or e.type=='underground-belt' or e.type=='splitter') end
local tiles={} local machines,fluid,idle,ugskip=0,0,0,0
for _,m in pairs(s.find_entities_filtered{area=A,force=f,type={'assembling-machine','furnace'}}) do
  local r=m.get_recipe() or (m.type=='furnace' and m.previous_recipe)
  if not r then idle=idle+1 else
    local fl=false for _,i in pairs(r.ingredients) do if i.type=='fluid' then fl=true end end for _,p in pairs(r.products) do if p.type=='fluid' then fl=true end end
    if fl then fluid=fluid+1 else
      machines=machines+1
      local per_min=60*m.crafting_speed/r.energy
      local b=m.bounding_box
      for _,i in pairs(s.find_entities_filtered{type='inserter',area={{b.left_top.x-1.6,b.left_top.y-1.6},{b.right_bottom.x+1.6,b.right_bottom.y+1.6}}}) do
        local pt,dt=i.pickup_target,i.drop_target
        if dt and dt.unit_number==m.unit_number and pt and isbeltlike(pt) then
          if not isbelt(pt) then ugskip=ugskip+1 else
            local k=math.floor(i.pickup_position.x)..','..math.floor(i.pickup_position.y)
            local t=tiles[k] or {x=pt.position.x,y=pt.position.y,req={},prov=false} tiles[k]=t
            for _,ing in pairs(r.ingredients) do local a=math.max(ing.amount,math.ceil(ing.amount*per_min*minutes)) local cap=2*prototypes.item[ing.name].stack_size if a>cap then a=cap end if a>(t.req[ing.name] or 0) then t.req[ing.name]=a end end
          end
        elseif pt and pt.unit_number==m.unit_number and dt and isbeltlike(dt) then
          if not isbelt(dt) then ugskip=ugskip+1 else
            local k=math.floor(i.drop_position.x)..','..math.floor(i.drop_position.y)
            local t=tiles[k] or {x=dt.position.x,y=dt.position.y,req={},prov=false} tiles[k]=t t.prov=true
          end
        end
      end
    end
  end
end
local nreq,nprov=0,0 for _,t in pairs(tiles) do if t.prov then nprov=nprov+1 else nreq=nreq+1 end end
local made_r,made_p=0,0
if apply then
  for _,t in pairs(tiles) do
    local old=s.find_entities_filtered{position={t.x,t.y},radius=0.3,force=f}
    local ok=true for _,e in pairs(old) do if isbelt(e) then e.destroy() end end
    if t.prov then local c=s.create_entity{name='passive-provider-chest',position={t.x,t.y},force=f} if c then made_p=made_p+1 end
    else local c=s.create_entity{name='requester-chest',position={t.x,t.y},force=f}
      if c then made_r=made_r+1 local sec=c.get_logistic_sections().add_section() local n=1
        for name,a in pairs(t.req) do sec.set_slot(n,{value={name=name,quality='normal'},min=a}) n=n+1 end end end
  end
end
rcon.print(helpers.table_to_json({machines=machines,fluid_skipped=fluid,idle_skipped=idle,underground_or_splitter_skipped=ugskip,requesters=nreq,providers=nprov,placed_requesters=made_r,placed_providers=made_p}))
"""

RETIRE = """
local s=game.surfaces.nauvis local f=game.forces.player local A=%(box)s local apply=%(apply)s
local function inA(p) return p.x>=A[1][1] and p.x<=A[2][1] and p.y>=A[1][2] and p.y<=A[2][2] end
local used={} local function mark(p) used[math.floor(p.x)..','..math.floor(p.y)]=true end
local W={{A[1][1]-4,A[1][2]-4},{A[2][1]+4,A[2][2]+4}}
for _,i in pairs(s.find_entities_filtered{area=W,force=f,type='inserter'}) do mark(i.pickup_position) mark(i.drop_position) end
for _,d in pairs(s.find_entities_filtered{area=W,force=f,type='mining-drill'}) do mark(d.drop_position) end
for _,d in pairs(s.find_entities_filtered{area=W,force=f,type={'loader','loader-1x1','pump','offshore-pump'}}) do mark(d.position) end
local seen={} local comps={}
local function nb(e) local out={} local bn=e.belt_neighbours if bn then for _,l in pairs({bn.inputs,bn.outputs}) do for _,n in pairs(l) do out[#out+1]=n end end end
  if e.type=='underground-belt' then local ok,n=pcall(function() return e.neighbours end) if ok and n and n.valid then out[#out+1]=n end end return out end
for _,e in pairs(s.find_entities_filtered{area=A,force=f,type=%(bt)s}) do
  if not seen[e.unit_number] then
    local comp={} local stack={e} seen[e.unit_number]=true local cross,inuse=false,false
    while #stack>0 do local c=table.remove(stack) comp[#comp+1]=c
      if not inA(c.position) then cross=true end
      if used[math.floor(c.position.x)..','..math.floor(c.position.y)] then inuse=true end
      if c.type=='splitter' then for _,o in pairs({{0.5,0},{-0.5,0},{0,0.5},{0,-0.5}}) do if used[math.floor(c.position.x+o[1])..','..math.floor(c.position.y+o[2])] then inuse=true end end end
      for _,n in pairs(nb(c)) do if not seen[n.unit_number] then seen[n.unit_number]=true stack[#stack+1]=n end end
    end
    comps[#comps+1]={comp=comp,cross=cross,inuse=inuse}
  end
end
local retire,keep_cross,keep_use,pieces=0,0,0,0 local items={} local doomed={}
for _,c in pairs(comps) do
  if c.cross then keep_cross=keep_cross+1 elseif c.inuse then keep_use=keep_use+1 else
    retire=retire+1 pieces=pieces+#c.comp
    for _,e in pairs(c.comp) do
      for i=1,e.get_max_transport_line_index() do for _,it in pairs(e.get_transport_line(i).get_contents()) do items[it.name..'|'..(it.quality or 'normal')]=(items[it.name..'|'..(it.quality or 'normal')] or 0)+it.count end end
      doomed[#doomed+1]=e end
  end
end
local chests=0 local left=0
if apply and #doomed>0 then
  for _,e in pairs(doomed) do if e.valid then e.destroy() end end
  local cx,cy=(A[1][1]+A[2][1])/2,(A[1][2]+A[2][2])/2 local pool={}
  for key,n in pairs(items) do local name,q=key:match('([^|]+)|(.+)') local remaining=n
    while remaining>0 do
      local placed=false for _,ch in pairs(pool) do if remaining>0 then local k=ch.get_inventory(defines.inventory.chest).insert{name=name,count=remaining,quality=q} remaining=remaining-k end end
      if remaining>0 then local p=s.find_non_colliding_position('passive-provider-chest',{cx,cy},80,1) local ch=p and s.create_entity{name='passive-provider-chest',position=p,force=f}
        if not ch then left=left+remaining break end pool[#pool+1]=ch chests=chests+1 end
    end end
end
local tot=0 for _,n in pairs(items) do tot=tot+n end
rcon.print(helpers.table_to_json({groups_retired=retire,pieces=pieces,groups_kept_crossing_border=keep_cross,groups_kept_in_use=keep_use,items_salvaged=tot,salvage_chests=chests,not_salvaged=left}))
"""


def box(a):
    import fx
    x1, y1, x2, y2 = fx.area_of(a)
    return "{{%d,%d},{%d,%d}}" % (x1, y1, x2, y2)


def run(a):
    import fx
    if a.what == "survey":
        res = fx.jlua(" ".join(SURVEY.split("\n")) % {"box": box(a), "bt": BELT_TYPES})
        print(json.dumps(res, indent=1))
        return
    if a.apply:
        print(fx.tools["save_game"]("before-logistics-" + a.what))
    if a.what == "convert":
        res = fx.jlua(" ".join(CONVERT.split("\n")) % {"box": box(a), "apply": "true" if a.apply else "false", "minutes": a.minutes})
    else:
        res = fx.jlua(" ".join(RETIRE.split("\n")) % {"box": box(a), "apply": "true" if a.apply else "false", "bt": BELT_TYPES})
    print(("APPLIED" if a.apply else "DRY RUN (add --apply)"), json.dumps(res))
