#!/usr/bin/env python3
"""The make-anything chemical plant: fluids go in and out as barrels (the Captain, 2026-11-13: "putting the fluids in barrels and
swapping them about, because barrels are much easier to clear than pipes"). One chemical plant whose recipe is set by circuit, with
four assembling machines 3 standing on its four fluid ports:
  A, B   emptying machines on the two fluid inputs (A straight on the port, B by one pipe tile). Each has a blue chest that asks for
         barrels of the fluid the chosen recipe needs and a red chest for the empty barrels.
  C, D   filling machines on the two fluid outputs. Each has a blue chest that always holds 10 empty barrels and a red chest for the
         full ones.
  plant  a blue chest for the solid ingredients, a red chest for the solid products.
Control is the same as scripts/omni_maker.py: the demand wire of its first roboport, a list of what this plant can make, a decider
and a selector that picks the most-missing item. A fluid product is ordered as its barrel (lubricant-barrel). The recipe table has
eight deciders per recipe, one for each machine and each circuit-set chest (a decider puts every output on both of its wires, so
it can serve only one of them): plant recipe, plant requests, A recipe, A barrels, B recipe, B barrels, C recipe, D recipe.
Machines get RECIPE signals (no ambiguity, and none of them can make another's recipe on its own wire).
Only recipes whose fluids all have barrels are listed (no steam, ammonia, thruster fuel). Base fluids come from scripts/nauvis_taps.py.
Steps: build [--more] [--apply] | config | status. Never apply twice (--more places only the second block of the recipe table).
PER-FLUID DESIGN (2026-11-16, sites in PER_FLUID; proven on the bench site, see docs/replicator-compaction-plan.md): no recipe table.
  plant   a RECIPE signal from an item -> recipe lookup (D1, A1, D2 + ring constant); it reads its own ingredients: x BATCH -> its blue chest
  A, B    the plant's fluid readings are split into two buses (first input / second input: every two-fluid recipe starts with the same PRIMARY
          fluid, water today), and each bus has, per fluid, one decider (empty-barrel recipe) and one arithmetic (barrels, rounded up)
  C       the product fluid is not in "read ingredients": a second ring holds the FILL recipe of each recipe with a fluid product (1 decider)
  D       unused (no recipe today has two fluid products; one that did is refused)
  caps    A, B and C read their contents; the feed inserters of A and B run only while everything in their machine AND in C is < 400
          (a machine blocked with a full fluid box cannot change recipe: the deadlock found on the fluid-assembler unit)
`config` places what is missing and re-wires; `retire-table [--apply]` removes the old table deciders; `--old-design` keeps the 8-a-recipe table path;
`demand ITEM N | none` sets the fake demand of a bench site. `flush` (and `cycle()` for the autopilot) empties the one pipe tile beside B and D when it
still holds the previous recipe's fluid: a pipe never flushes itself and no circuit can do it.
Usage: omni_fluid.py build [--apply] | config | status | retire-table [--apply] | demand ITEM N   [--site old|replicator|bench] [--old-design]
The Replicator (the Captain's name, 2026-11-14) has its own fluid unit: --site replicator, plant centre (-300,-224) beside the
launch pad, demand roboport of omni_maker site `replicator`; the old copy is --site old (the default)."""
import json
import sys

from _game import tools

SITES = {"old": {"c": (15, -388), "demand": (-28, -398), "maker": "nauvis"},         # the first copy, retired by replicator_move.py
         "replicator": {"c": (-300, -224), "demand": (-352, -229), "maker": "replicator"}}  # the Replicator (see omni_maker.py)
SITES["bench"] = {"c": (-246, -309), "demand": (-252, -317), "demand_const": True, "maker": None, "sub": (-239, -318)}    # test bench north of the Nauvis pad (fake demand: a constant combinator)
# Per-fluid design: site -> top-left tiles of the 1 x 2 control combinators (in slot order) and of the two ring constants.
PER_FLUID = {"replicator": {"slots": [(-328 + k, -220) for k in range(24)] + [(-342 + k, -225) for k in range(4)], "ring": (-338, -225), "ringc": (-337, -225)},
             "bench": {"slots": [(-252 + k, -300) for k in range(14)] + [(-252 + k, -298) for k in range(14)], "ring": (-251, -315), "ringc": (-250, -315)}}
OLD_DESIGN = "--old-design" in sys.argv
ECAP = 400                   # feed inserters of the emptiers stop at this much fluid (or anything else) in the machine or in the filler
SITE = "old"                 # chosen by --site NAME (default old: history keeps working)
CX, CY = SITES[SITE]["c"]    # the plant's centre tile
RX, RY = 4, -398             # old site: top-left tile of the recipe table (two rows of deciders, two columns a recipe)
RY2 = -382                   # its second block, south of the plant
DEMAND = SITES[SITE]["demand"]   # the roboport of scripts/omni_maker.py that reads missing requests


def use(name):
    global SITE, CX, CY, DEMAND
    SITE = name
    CX, CY = SITES[name]["c"]
    DEMAND = SITES[name]["demand"]


def slots(n):
    """Top-left tile of the 8 deciders of each of n recipes, index i*8+j (j 0-3 first block, 4-7 second block).
    Old site: two blocks of 2 x 4 tiles a recipe in a row. Replicator: two free strips of the area (tile rows y -231..-222 east
    of the furnace unit, and y -215..-212 under the machines), filled 1 x 2 at a time."""
    if SITE == "old":
        return [(RX + 2 * i + dx, (RY if j < 4 else RY2) + dy) for i in range(n) for j in range(8) for dx, dy in [((0, 0), (1, 0), (0, 2), (1, 2))[j % 4]]]
    pool = [(-323 + k, ty) for ty in (-231, -229, -227, -225, -223) for k in range(17)] + [(-350 + k, ty) for ty in (-215, -213) for k in range(36)]
    assert 8 * n <= len(pool), "fluid recipe table does not fit"
    return pool[:8 * n]


def lua_slots(sl):
    return "{" + ",".join("{%d,%d}" % t for t in sl) + "}"
BATCH = 10
Q = {"quality": "epic"}
N, E, S, W = 0, 4, 8, 12

LIST = ("local f=game.forces.player local bar={} for name,r in pairs(f.recipes) do if name:find('^empty%-') and r.enabled and #r.ingredients==1 then for _,p in pairs(r.products) do if p.type=='fluid' then bar[p.name]=r.ingredients[1].name end end end end "
        "local rs,seen={},{} local names={} for name,_ in pairs(f.recipes) do names[#names+1]=name end table.sort(names) for _,name in pairs(names) do local r=f.recipes[name] local pr=r.prototype local chem=false for _,c in pairs(pr.categories) do if c:find('chemistry') then chem=true end end "
        "if r.enabled and chem and not pr.hidden then local fi,fo,si,key={},{},{},nil local ok=true for _,i in pairs(r.ingredients) do if i.type=='fluid' then if bar[i.name] then fi[#fi+1]=i else ok=false end else si[#si+1]=i end end "
        "for _,p in pairs(r.products) do if p.type=='fluid' then if bar[p.name] then fo[#fo+1]=p else ok=false end elseif not key then key=p.name end end if not key and fo[1] then key=bar[fo[1].name] end "
        "if ok and key and #fi<=2 and #fo<=2 and (#fi>0 or #fo>0) and not seen[key] then seen[key]=true rs[#rs+1]={name=name,key=key,fi=fi,fo=fo,si=si} end end end ")


def layout(n, more=False):
    ents = []

    def e(name, tx, ty, w=1, h=1, d=N):
        ents.append({"name": name, "x": tx + w / 2, "y": ty + h / 2, "direction": d, "params": dict(Q)})

    c, y = CX, CY
    e("chemical-plant", c - 1, y - 1, 3, 3)
    e("requester-chest", c - 3, y)
    e("fast-inserter", c - 2, y, d=W)
    e("fast-inserter", c + 2, y, d=W)
    e("passive-provider-chest", c + 3, y)
    e("assembling-machine-3", c - 2, y - 4, 3, 3, d=N)          # A: its bottom centre stands on the plant's first input
    e("requester-chest", c - 1, y - 6)
    e("fast-inserter", c - 1, y - 5, d=N)
    e("fast-inserter", c - 3, y - 3, d=E)
    e("passive-provider-chest", c - 4, y - 3)
    e("pipe", c + 1, y - 2)                                     # second input
    e("assembling-machine-3", c + 2, y - 3, 3, 3, d=E)          # B: its west centre faces that pipe
    e("requester-chest", c + 3, y - 5)
    e("fast-inserter", c + 3, y - 4, d=N)
    e("fast-inserter", c + 5, y - 2, d=W)
    e("passive-provider-chest", c + 6, y - 2)
    e("assembling-machine-3", c - 2, y + 2, 3, 3, d=N)          # C: its top centre stands on the plant's first output
    e("requester-chest", c - 1, y + 6)
    e("fast-inserter", c - 1, y + 5, d=S)
    e("fast-inserter", c - 3, y + 3, d=E)
    e("passive-provider-chest", c - 4, y + 3)
    e("pipe", c + 1, y + 2)                                     # second output
    e("assembling-machine-3", c + 2, y + 1, 3, 3, d=W)          # D: its west centre faces that pipe
    e("requester-chest", c + 3, y + 5)
    e("fast-inserter", c + 3, y + 4, d=S)
    e("fast-inserter", c + 5, y + 2, d=W)
    e("passive-provider-chest", c + 6, y + 2)
    e("constant-combinator", c - 6, y - 6)
    e("decider-combinator", c - 6, y - 4, 1, 2)
    e("selector-combinator", c - 5, y - 4, 1, 2)
    sl = slots(n)
    for i in range(n):
        for j in range(4):
            e("decider-combinator", sl[8 * i + j][0], sl[8 * i + j][1], 1, 2)
    second = len(ents)
    for i in range(n):                                          # the second block: a decider puts its outputs on both wires, so one
        for j in range(4, 8):                                   # decider can serve only one machine or chest (eight a recipe)
            e("decider-combinator", sl[8 * i + j][0], sl[8 * i + j][1], 1, 2)
    return ents[second:] if more else ents


CONFIG = ("local s=game.surfaces.nauvis local W=defines.wire_connector_id local function at(n,x,y) return s.find_entities_filtered{name=n,position={x+0.5,y+0.5},radius=0.4}[1] end "
          "local function wire(a,ia,b,ib) a.get_wire_connector(ia,true).connect_to(b.get_wire_connector(ib,true),false) end local function clr(e,ids) for _,id in pairs(ids) do e.get_wire_connector(id,true).disconnect_all() end end "
          "local CB={W.combinator_input_red,W.combinator_input_green,W.combinator_output_red,W.combinator_output_green} local CC={W.circuit_red,W.circuit_green} " + LIST +
          "local c,y=CX,CY local plant=s.find_entities_filtered{name='chemical-plant',position={c+0.5,y+0.5},radius=0.6}[1] local function am(x,yy) return s.find_entities_filtered{name='assembling-machine-3',position={x+0.5,yy+0.5},radius=0.6}[1] end "
          "local A,B,C,D=am(c-1,y-3),am(c+3,y-2),am(c-1,y+3),am(c+3,y+2) local qm,qa,qb,qc,qd=at('requester-chest',c-3,y),at('requester-chest',c-1,y-6),at('requester-chest',c+3,y-5),at('requester-chest',c-1,y+6),at('requester-chest',c+3,y+5) "
          "local cc=at('constant-combinator',c-6,y-6) local dec=s.find_entities_filtered{name='decider-combinator',position={c-5.5,y-3},radius=0.6}[1] local sel=s.find_entities_filtered{name='selector-combinator',position={c-4.5,y-3},radius=0.6}[1] "
          "local rp=s.find_entities_filtered{name='roboport',position={DX,DY},radius=0.6}[1] "
          "local cb=cc.get_or_create_control_behavior() while cb.sections_count>0 do cb.remove_section(1) end local sec=cb.add_section() for i,r in pairs(rs) do sec.set_slot(i,{value={type='item',name=r.key,quality='normal'},min=1}) end "
          "clr(dec,CB) clr(sel,CB) wire(dec,W.combinator_input_red,rp,W.circuit_red) wire(dec,W.combinator_input_green,cc,W.circuit_green) "
          "dec.get_or_create_control_behavior().parameters={conditions={{first_signal={type='virtual',name='signal-each'},first_signal_networks={red=true,green=false},comparator='>',constant=0},"
          "{first_signal={type='virtual',name='signal-each'},first_signal_networks={red=false,green=true},comparator='>',constant=0,compare_type='and'}},outputs={{signal={type='virtual',name='signal-each'},copy_count_from_input=true,networks={red=true,green=false}}}} "
          "wire(sel,W.combinator_input_red,dec,W.combinator_output_red) sel.get_or_create_control_behavior().parameters={operation='select',select_max=true,index_constant=0} "
          "for _,m in pairs{plant,A,B,C,D} do clr(m,CC) local b=m.get_or_create_control_behavior() b.circuit_set_recipe=true b.circuit_read_ingredients=false end "
          "for _,q in pairs{qm,qa,qb} do clr(q,CC) local b=q.get_or_create_control_behavior() b.set_requests=true b.read_contents=false q.get_logistic_point(defines.logistic_member_index.logistic_container).trash_not_requested=true end "
          "for _,q in pairs{qc,qd} do local lp=q.get_logistic_point(defines.logistic_member_index.logistic_container) local se=lp.get_section(1) or lp.add_section() se.set_slot(1,{value={type='item',name='barrel',quality='normal'},min=10}) end "
          "local function R(n) return {type='recipe',name=n} end "
          "local FS=FSTAB local n=0 for i,r in pairs(rs) do local d={} for j=1,8 do local sp=FS[(i-1)*8+j] d[j]=s.find_entities_filtered{name='decider-combinator',position={sp[1]+0.5,sp[2]+1},radius=0.3}[1] end local all=true for j=1,8 do if not d[j] then all=false end end "
          "if all then local cond={{first_signal={type='item',name=r.key},comparator='>',constant=0}} local function K(sg,k) return {signal=sg,copy_count_from_input=false,constant=k} end local o={{K(R(r.name),1)},{},{},{},{},{},{},{}} "
          "for _,ing in pairs(r.si) do o[2][#o[2]+1]=K({type='item',name=ing.name},ing.amount*BATCH) end local fa,fb=r.fi[1],r.fi[2] if fa and fb and (fa.fluidbox_index==2 or fb.fluidbox_index==1) then fa,fb=fb,fa end "
          "if fa then o[3]={K(R('empty-'..bar[fa.name]),1)} o[4]={K({type='item',name=bar[fa.name]},math.ceil(fa.amount*BATCH/50))} end if fb then o[5]={K(R('empty-'..bar[fb.name]),1)} o[6]={K({type='item',name=bar[fb.name]},math.ceil(fb.amount*BATCH/50))} end "
          "if r.fo[1] then o[7]={K(R(bar[r.fo[1].name]),1)} end if r.fo[2] then o[8]={K(R(bar[r.fo[2].name]),1)} end "
          "local tgt={{plant,W.circuit_red},{qm,W.circuit_green},{A,W.circuit_red},{qa,W.circuit_green},{B,W.circuit_red},{qb,W.circuit_green},{C,W.circuit_red},{D,W.circuit_red}} "
          "for j=1,8 do clr(d[j],CB) d[j].get_or_create_control_behavior().parameters={conditions=cond,outputs=o[j]} wire(d[j],W.combinator_input_green,sel,W.combinator_output_green) "
          "local oc=(tgt[j][2]==W.circuit_red) and W.combinator_output_red or W.combinator_output_green wire(d[j],oc,tgt[j][1],tgt[j][2]) end n=n+1 end end "
          "local t={} for _,r in pairs(rs) do t[#t+1]=r.key end rcon.print('recipes wired '..n..' of '..#rs..': '..table.concat(t,', '))")
STATUS = ("local s=game.surfaces.nauvis local W=defines.wire_connector_id local c,y=CX,CY local o={} local function st(e) local k='?' for a,v in pairs(defines.entity_status) do if v==e.status then k=a end end local r=e.get_recipe() "
          "local fl={} for n,v in pairs(e.get_fluid_contents()) do fl[#fl+1]=n..' '..math.floor(v) end return (r and r.name or 'no recipe')..', '..k..', made '..e.products_finished..(#fl>0 and (' ['..table.concat(fl,', ')..']') or '') end "
          "local function inv(x,yy,n) local e=s.find_entities_filtered{name=n,position={x+0.5,yy+0.5},radius=0.4}[1] local t={} for _,it in pairs(e.get_inventory(defines.inventory.chest).get_contents()) do t[#t+1]=it.name..' '..it.count end return table.concat(t,', ') end "
          "local function am(x,yy) return s.find_entities_filtered{name='assembling-machine-3',position={x+0.5,yy+0.5},radius=0.6}[1] end local plant=s.find_entities_filtered{name='chemical-plant',position={c+0.5,y+0.5},radius=0.6}[1] "
          "local sel=s.find_entities_filtered{name='selector-combinator',position={c-4.5,y-3},radius=0.6}[1] local n=sel.get_circuit_network(W.combinator_output_green) local ch={} if n and n.signals then for _,x in pairs(n.signals) do ch[#ch+1]=x.signal.name..' '..x.count end end "
          "o[#o+1]='chosen: '..table.concat(ch,', ') o[#o+1]='plant: '..st(plant)..' | blue: '..inv(c-3,y,'requester-chest')..' | red: '..inv(c+3,y,'passive-provider-chest') "
          "o[#o+1]='A (empties in 1): '..st(am(c-1,y-3))..' | blue: '..inv(c-1,y-6,'requester-chest') o[#o+1]='B (empties in 2): '..st(am(c+3,y-2))..' | blue: '..inv(c+3,y-5,'requester-chest') "
          "o[#o+1]='C (fills out 1): '..st(am(c-1,y+3))..' | blue: '..inv(c-1,y+6,'requester-chest')..' | red: '..inv(c-4,y+3,'passive-provider-chest') o[#o+1]='D (fills out 2): '..st(am(c+3,y+2))..' | blue: '..inv(c+3,y+5,'requester-chest') rcon.print(table.concat(o,' ;; '))")


PLAN = (LIST + "local first,second,prim={}, {}, nil local bad=nil for _,r in pairs(rs) do local a,b=r.fi[1],r.fi[2] if a and b and (a.fluidbox_index==2 or b.fluidbox_index==1) then a,b=b,a end "
        "if a then first[a.name]=true end if b then second[b.name]=true if prim and prim~=a.name then bad='two-fluid recipes start with different fluids: '..prim..' and '..a.name end prim=a.name end "
        "if r.fo[2] then bad='recipe '..r.name..' has two fluid products (filler D is not wired in the per-fluid design)' end end "
        "local seen={} for _,r in pairs(rs) do if r.fo[1] then local k=bar[r.fo[1].name] if seen[k] then bad='two recipes make '..r.fo[1].name end seen[k]=true end end "
        "local fa,fb={}, {} for k,_ in pairs(first) do fa[#fa+1]=k end for k,_ in pairs(second) do fb[#fb+1]=k end table.sort(fa) table.sort(fb) "
        "rcon.print((bad or 'ok')..'|'..(prim or 'water')..'|'..table.concat(fa,',')..'|'..table.concat(fb,',')..'|'..#rs)")

CONFIG_NEW = r'''
local s=game.surfaces.nauvis local W=defines.wire_connector_id
local function at(n,x,y) return s.find_entities_filtered{name=n,position={x+0.5,y+0.5},radius=0.4}[1] end
local function at2(n,x,y) return s.find_entities_filtered{name=n,position={x+0.5,y+1},radius=0.3}[1] end
local function wire(a,ia,b,ib) a.get_wire_connector(ia,true).connect_to(b.get_wire_connector(ib,true),false) end
local function clr(e,ids) for _,id in pairs(ids) do local k=e.get_wire_connector(id,true) k.disconnect_all() k.disconnect_all(defines.wire_origin.script) end end
local CB={W.combinator_input_red,W.combinator_input_green,W.combinator_output_red,W.combinator_output_green} local CC={W.circuit_red,W.circuit_green}
@LIST@
local c,y=CX,CY
local plant=s.find_entities_filtered{name='chemical-plant',position={c+0.5,y+0.5},radius=0.6}[1]
local function am(x,yy) return s.find_entities_filtered{name='assembling-machine-3',position={x+0.5,yy+0.5},radius=0.6}[1] end
local A,B,C,D=am(c-1,y-3),am(c+3,y-2),am(c-1,y+3),am(c+3,y+2)
local qm,qa,qb,qc,qd=at('requester-chest',c-3,y),at('requester-chest',c-1,y-6),at('requester-chest',c+3,y-5),at('requester-chest',c-1,y+6),at('requester-chest',c+3,y+5)
local cc=at('constant-combinator',c-6,y-6)
local dec=s.find_entities_filtered{name='decider-combinator',position={c-5.5,y-3},radius=0.6}[1]
local sel=s.find_entities_filtered{name='selector-combinator',position={c-4.5,y-3},radius=0.6}[1]
local dem=@DEMFIND@
local SL=@SLOTS@
local function sd(i) return at2('decider-combinator',SL[i][1],SL[i][2]) end
local function sa(i) return at2('arithmetic-combinator',SL[i][1],SL[i][2]) end
local D1,A1,D2,SC,GA1,GA2,GB,HA,HB,D2c=sd(1),sa(2),sd(3),sa(4),sd(5),sd(6),sd(7),sa(8),sa(9),sd(10)
local ring,ringc=at('constant-combinator',@RINGX@,@RINGY@),at('constant-combinator',@RINCX@,@RINCY@)
local inA,inB=at('fast-inserter',c-1,y-5),at('fast-inserter',c+3,y-4)
if not (plant and A and B and C and D and qm and qa and qb and qc and qd and cc and dec and sel and dem and D1 and A1 and D2 and SC and GA1 and GA2 and GB and HA and HB and D2c and ring and ringc and inA and inB) then rcon.print('unit incomplete: build it first') return end
local AF,BF,PRIM=@AF@,@BF@,'@PRIM@'
local EACH={type='virtual',name='signal-each'} local RSIG={type='virtual',name='signal-R'} local PF={type='fluid',name=PRIM}
local function setlist(e,fn) local cb=e.get_or_create_control_behavior() while cb.sections_count>0 do cb.remove_section(1) end local sec=cb.add_section() local k=0 for i,r in pairs(rs) do local v=fn(i,r) if v then k=k+1 sec.set_slot(k,{value=v,min=i}) end end end
setlist(cc,function(i,r) return {type='item',name=r.key,quality='normal'} end)
setlist(ring,function(i,r) return {type='recipe',name=r.name,quality='normal'} end)
setlist(ringc,function(i,r) if r.fo[1] then return {type='recipe',name=bar[r.fo[1].name],quality='normal'} end end)
for _,e in pairs{cc,ring,ringc} do clr(e,CC) end
for _,e in pairs{dec,sel,D1,A1,D2,SC,GA1,GA2,GB,HA,HB,D2c} do clr(e,CB) end
local function both(net_a,net_b) return {{first_signal=EACH,first_signal_networks=net_a,comparator='>',constant=0},{first_signal=EACH,first_signal_networks=net_b,comparator='>',constant=0,compare_type='and'}} end
local RED,GRN={red=true,green=false},{red=false,green=true}
wire(dec,W.combinator_input_red,dem,W.circuit_red) wire(dec,W.combinator_input_green,cc,W.circuit_green)
dec.get_or_create_control_behavior().parameters={conditions=both(RED,GRN),outputs={{signal=EACH,copy_count_from_input=true,networks=RED}}}
wire(sel,W.combinator_input_red,dec,W.combinator_output_red) sel.get_or_create_control_behavior().parameters={operation='select',select_max=true,index_constant=0}
wire(D1,W.combinator_input_green,sel,W.combinator_output_green) wire(D1,W.combinator_input_red,cc,W.circuit_red)
D1.get_or_create_control_behavior().parameters={conditions=both(GRN,RED),outputs={{signal=EACH,copy_count_from_input=true,networks=RED}}}
wire(A1,W.combinator_input_red,D1,W.combinator_output_red) A1.get_or_create_control_behavior().parameters={first_signal=EACH,second_constant=0,operation='+',output_signal=RSIG}
local function pick(d,rg) wire(d,W.combinator_input_green,A1,W.combinator_output_green) wire(d,W.combinator_input_red,rg,W.circuit_red)
  d.get_or_create_control_behavior().parameters={conditions={{first_signal=EACH,first_signal_networks=RED,comparator='=',second_signal=RSIG,second_signal_networks=GRN}},outputs={{signal=EACH,copy_count_from_input=false,constant=1}}} end
pick(D2,ring) pick(D2c,ringc)
for _,m in pairs{plant,A,B,C,D} do clr(m,CC) local b=m.get_or_create_control_behavior() b.circuit_set_recipe=true b.circuit_read_ingredients=(m==plant) b.circuit_read_contents=(m==A or m==B or m==C) end
for _,q in pairs{qm,qa,qb} do clr(q,CC) local b=q.get_or_create_control_behavior() b.set_requests=true b.read_contents=false q.get_logistic_point(defines.logistic_member_index.logistic_container).trash_not_requested=true end
for _,q in pairs{qc,qd} do local lp=q.get_logistic_point(defines.logistic_member_index.logistic_container) local se=lp.get_section(1) or lp.add_section() se.set_slot(1,{value={type='item',name='barrel',quality='normal'},min=10}) end
wire(D2,W.combinator_output_red,plant,W.circuit_red) wire(D2c,W.combinator_output_red,C,W.circuit_red)
wire(SC,W.combinator_input_green,plant,W.circuit_green) SC.get_or_create_control_behavior().parameters={first_signal=EACH,second_constant=BATCH,operation='*',output_signal=EACH} wire(SC,W.combinator_output_green,qm,W.circuit_green)
for _,g in pairs{GA1,GA2,GB} do wire(g,W.combinator_input_green,plant,W.circuit_green) end
GA1.get_or_create_control_behavior().parameters={conditions={{first_signal=PF,comparator='>',constant=0}},outputs={{signal=PF,copy_count_from_input=true}}}
GA2.get_or_create_control_behavior().parameters={conditions={{first_signal=EACH,comparator='>',constant=0},{first_signal=PF,comparator='=',constant=0,compare_type='and'}},outputs={{signal=EACH,copy_count_from_input=true}}}
GB.get_or_create_control_behavior().parameters={conditions={{first_signal=EACH,comparator='>',constant=0},{first_signal=PF,comparator='>',constant=0,compare_type='and'}},outputs={{signal=EACH,copy_count_from_input=true}}}
wire(HA,W.combinator_input_green,GA1,W.combinator_output_green) wire(HA,W.combinator_input_green,GA2,W.combinator_output_green) wire(HB,W.combinator_input_green,GB,W.combinator_output_green)
for _,h in pairs{HA,HB} do h.get_or_create_control_behavior().parameters={first_signal=EACH,second_constant=@RNDUP@,operation='+',output_signal=EACH} end
local n=0
local function tab(list,off,H,M,q) for k,fl in ipairs(list) do local d,ar=sd(off+2*k-1),sa(off+2*k) if d and ar then clr(d,CB) clr(ar,CB)
    wire(d,W.combinator_input_green,H,W.combinator_output_green) wire(ar,W.combinator_input_green,H,W.combinator_output_green)
    d.get_or_create_control_behavior().parameters={conditions={{first_signal={type='fluid',name=fl},comparator='>',constant=0}},outputs={{signal={type='recipe',name='empty-'..bar[fl]},copy_count_from_input=false,constant=1}}}
    ar.get_or_create_control_behavior().parameters={first_signal={type='fluid',name=fl},second_constant=@PERBAR@,operation='/',output_signal={type='item',name=bar[fl]}}
    wire(d,W.combinator_output_red,M,W.circuit_red) wire(ar,W.combinator_output_green,q,W.circuit_green) n=n+1 end end end
tab(AF,10,HA,A,qa) tab(BF,10+2*#AF,HB,B,qb)
for _,pr in pairs{{inA,A},{inB,B}} do local i,m=pr[1],pr[2] clr(i,CC) wire(i,W.circuit_green,m,W.circuit_green) wire(i,W.circuit_red,C,W.circuit_red)
  local ib=i.get_or_create_control_behavior() ib.circuit_enable_disable=true ib.circuit_condition={first_signal={type='virtual',name='signal-everything'},comparator='<',constant=@ECAP@} end
pcall(function() B.direction=defines.direction.east end) pcall(function() D.direction=defines.direction.west end)
local t={} for _,r in pairs(rs) do t[#t+1]=r.key end
rcon.print('per-fluid design wired: '..#rs..' items ('..table.concat(t,', ')..'); fluid entries '..n..' of '..(#AF+#BF)..' (first input '..#AF..', second '..#BF..', primary '..PRIM..')')
'''


# The one pipe tile between B and the plant's second input (and between the plant's second output and D) keeps its fluid when the recipe changes, and a pipe
# never flushes itself: the next recipe's fluid cannot enter (bench, 2026-11-16: petroleum gas left from sulfur blocked light oil for cracking). No circuit
# can empty a pipe, so this is a script step: clear the pipe when its fluid is not what the machine beside it makes or takes now. Also turns B and D to
# face their pipes (a facing only sticks while the machine has a fluid recipe). Run it from the autopilot (`cycle()`), or by hand: `flush`.
FLUSH = ("local s=game.surfaces.nauvis local c,y=CX,CY local o={} local function am(x,yy) return s.find_entities_filtered{name='assembling-machine-3',position={x+0.5,yy+0.5},radius=0.6}[1] end "
         "local function want(m,out) local r=m and m.get_recipe() if not r then return nil end for _,p in pairs(out and r.products or r.ingredients) do if p.type=='fluid' then return p.name end end end "
         "for _,t in pairs{{am(c+3,y-2),c+1,y-2,true,defines.direction.east,'B'},{am(c+3,y+2),c+1,y+2,false,defines.direction.west,'D'}} do local m,px,py,out,dir,nm=t[1],t[2],t[3],t[4],t[5],t[6] "
         "local pipe=s.find_entities_filtered{name='pipe',position={px+0.5,py+0.5},radius=0.4}[1] if m and pipe then local w=want(m,out) if w and m.direction~=dir then m.direction=dir o[#o+1]=nm..' turned' end if not w and not out then local plant=s.find_entities_filtered{name='chemical-plant',position={c+0.5,y+0.5},radius=0.6}[1] w=want(plant,true) end "
         "local have=next(pipe.get_fluid_contents()) if have and have~=w then pipe.clear_fluid_inside() o[#o+1]=nm..' pipe flushed ('..have..(w and (', now '..w) or '')..')' end end end "
         "rcon.print(#o>0 and table.concat(o,', ') or 'nothing to flush')")


# A quality upgrade replaces the control combinators and drops every wire longer than a hand-laid one (found 2026-11-16: the autopilot upgraded the new
# epic control row to legendary within the hour and the unit went deaf; the parity test caught it). HEALCHK counts control combinators that have lost all
# their input wires or all their output wires, and constants with no wire; `cycle()` re-runs the config when any is found.
HEALCHK = ("local s=game.surfaces.nauvis local W=defines.wire_connector_id local bad=0 local function n(e,ids) local c=0 for _,id in pairs(ids) do c=c+e.get_wire_connector(id,true).connection_count end return c end "
           "for i,t in ipairs(@SLOTS@) do if i<=@USED@ then local e=s.find_entities_filtered{type={'decider-combinator','arithmetic-combinator'},position={t[1]+0.5,t[2]+1},radius=0.3}[1] "
           "if not e or n(e,{W.combinator_input_red,W.combinator_input_green})==0 or n(e,{W.combinator_output_red,W.combinator_output_green})==0 then bad=bad+1 end end end "
           "for _,t in ipairs(@CONSTS@) do local e=s.find_entities_filtered{name='constant-combinator',position={t[1]+0.5,t[2]+0.5},radius=0.4}[1] if not e or n(e,{W.circuit_red,W.circuit_green})==0 then bad=bad+1 end end rcon.print(bad)")


def heal():
    """Re-wire the per-fluid control of the current site if a wire has gone. Returns '' when healthy."""
    if SITE not in PER_FLUID or OLD_DESIGN:
        return ""
    prim, fa, fb, n = plan_new()
    g = PER_FLUID[SITE]
    used = 10 + 2 * (len(fa) + len(fb))
    consts = [g["ring"], g["ringc"], (CX - 6, CY - 6)]
    bad = int(tools["run_lua"](HEALCHK.replace("@SLOTS@", lua_slots(g["slots"])).replace("@USED@", str(used)).replace("@CONSTS@", lua_slots(consts))).strip())
    if not bad:
        return ""
    return "chemical unit: %d control parts had lost their wires, re-wired: %s" % (bad, config_new()[:120])


def cycle(site="replicator"):
    """Autopilot hook: flush stale pipe fluid, keep B and D facing their pipes, and re-wire the per-fluid control of the chemical unit and of the
    fluid-assembler unit when a quality upgrade has dropped wires. Never raises."""
    out = []
    try:
        use(site)
        fl = tools["run_lua"](FLUSH.replace("CX", str(CX)).replace("CY", str(CY))).strip()
        if fl != "nothing to flush":
            out.append(fl)
        h = heal()
        if h:
            out.append(h)
    except Exception as exc:  # noqa: BLE001
        out.append("omni_fluid cycle error " + repr(exc))
    if site == "replicator":
        try:
            import omni_fluid_asm
            h = omni_fluid_asm.heal_all()
            if h:
                out.append(h)
        except Exception as exc:  # noqa: BLE001
            out.append("omni_fluid_asm heal error " + repr(exc))
    return ", ".join(out) or "nothing to flush"


def plan_new():
    bad, prim, fa, fb, n = tools["run_lua"](PLAN).strip().split("|")
    if bad != "ok":
        sys.exit("the per-fluid design cannot route this recipe list: " + bad)
    return prim, [x for x in fa.split(",") if x], [x for x in fb.split(",") if x], int(n)


def new_entities(nfa, nfb):
    g = PER_FLUID[SITE]
    kinds = ["decider", "arithmetic", "decider", "arithmetic", "decider", "decider", "decider", "arithmetic", "arithmetic", "decider"] + ["decider", "arithmetic"] * (nfa + nfb)
    if len(kinds) > len(g["slots"]):
        sys.exit("%d control combinators, the site has %d slots: add slots to PER_FLUID" % (len(kinds), len(g["slots"])))
    out = [{"name": k + "-combinator", "x": g["slots"][i][0] + 0.5, "y": g["slots"][i][1] + 1.0, "direction": N, "params": dict(Q)} for i, k in enumerate(kinds)]
    for key in ("ring", "ringc"):
        out.append({"name": "constant-combinator", "x": g[key][0] + 0.5, "y": g[key][1] + 0.5, "direction": N, "params": dict(Q)})
    if SITES[SITE].get("demand_const"):
        out.append({"name": "constant-combinator", "x": DEMAND[0] + 0.5, "y": DEMAND[1] + 0.5, "direction": N, "params": dict(Q)})
    return out


def config_new():
    prim, fa, fb, n = plan_new()
    g = PER_FLUID[SITE]
    r = json.loads(tools["place_entities"](json.dumps(new_entities(len(fa), len(fb))), surface="nauvis", dry_run=False))
    dem = ("at('constant-combinator',%d,%d)" % DEMAND) if SITES[SITE].get("demand_const") else "s.find_entities_filtered{name='roboport',position={%d,%d},radius=0.6}[1]" % DEMAND
    lua = lambda names: "{" + ",".join("'%s'" % x for x in names) + "}"
    code = CONFIG_NEW
    for k, v in (("@LIST@", LIST), ("@DEMFIND@", dem), ("@SLOTS@", lua_slots(g["slots"])), ("@RINGX@", g["ring"][0]), ("@RINGY@", g["ring"][1]), ("@RINCX@", g["ringc"][0]),
                 ("@RINCY@", g["ringc"][1]), ("@AF@", lua(fa)), ("@BF@", lua(fb)), ("@PRIM@", prim), ("@RNDUP@", 50 // BATCH - 1), ("@PERBAR@", 50 // BATCH), ("@ECAP@", ECAP)):
        code = code.replace(k, str(v))
    code = code.replace("CX", str(CX)).replace("CY", str(CY)).replace("BATCH", str(BATCH))
    return "new control entities placed %d | " % (r.get("placed") or 0) + tools["run_lua"](code)


def sub(code):
    if "FSTAB" in code:
        code = code.replace("FSTAB", lua_slots(slots(int(tools["run_lua"](LIST + "rcon.print(#rs)").strip()))))
    return (code.replace("CX", str(CX)).replace("CY", str(CY)).replace("DX", str(DEMAND[0])).replace("DY", str(DEMAND[1])).replace("BATCH", str(BATCH)))


def main():
    step = sys.argv[1]
    apply = "--apply" in sys.argv
    if "--site" in sys.argv:
        use(sys.argv[sys.argv.index("--site") + 1])
    if step == "build" and not (SITE in PER_FLUID and not OLD_DESIGN):
        n = int(tools["run_lua"](LIST + "rcon.print(#rs)").strip())
        r = json.loads(tools["place_entities"](json.dumps(layout(n, "--more" in sys.argv)), surface="nauvis", dry_run=not apply, clear_trees=apply))
        print("recipes", n, "placed" if apply else "dry run", r.get("placed"), "failed", json.dumps(r.get("failed") or [])[:400])
    new = SITE in PER_FLUID and not OLD_DESIGN
    if step == "build" and new:
        base = layout(0)                                                                    # the unit without a table
        if SITES[SITE].get("sub"):
            base.append({"name": "substation", "x": SITES[SITE]["sub"][0] + 1, "y": SITES[SITE]["sub"][1] + 1, "direction": N, "params": dict(Q)})
        r = json.loads(tools["place_entities"](json.dumps(base), surface="nauvis", dry_run=not apply, clear_trees=apply))
        print("per-fluid unit:", "placed" if apply else "dry run", r.get("placed"), "failed", json.dumps(r.get("failed") or [])[:400])
        if apply:
            print(config_new())
        return
    if step == "demand":
        if not SITES[SITE].get("demand_const"):
            sys.exit("this site reads a roboport, not a fake demand")
        item = sys.argv[2]
        slot = "" if item == "none" else "sec.set_slot(1,{value={type='item',name='%s',quality='normal'},min=%d})" % (item, int(sys.argv[3]))
        print(tools["run_lua"]("local s=game.surfaces.nauvis local dm=s.find_entities_filtered{name='constant-combinator',position={%s,%s},radius=0.4}[1] local cb=dm.get_or_create_control_behavior() "
                               "while cb.sections_count>0 do cb.remove_section(1) end local sec=cb.add_section() %s rcon.print('demand set: %s')" % (DEMAND[0] + 0.5, DEMAND[1] + 0.5, slot, item)))
        return
    if step == "flush":
        print(cycle(SITE))
        return
    if step == "retire-table":
        if SITE != "replicator":
            sys.exit("only the Replicator site has a folded table to retire")
        pool = [(-323 + k, ty) for ty in (-231, -229, -227, -225, -223) for k in range(17)] + [(-350 + k, ty) for ty in (-215, -213) for k in range(36)]
        pool = pool[:8 * int(tools["run_lua"](LIST + "rcon.print(#rs)").strip())]          # only the slots the table used (8 a recipe)
        flag = "true" if apply else "false"
        print(tools["run_lua"]("local s=game.surfaces.nauvis local f=game.forces.player local n,w=0,0 local W=defines.wire_connector_id for _,t in ipairs(%s) do local d=s.find_entities_filtered{name='decider-combinator',position={t[1]+0.5,t[2]+1},radius=0.3,force=f}[1] "
                               "if d then local c=0 for _,id in pairs({W.combinator_output_red,W.combinator_output_green}) do c=c+d.get_wire_connector(id,true).connection_count end if c>0 then w=w+1 else if %s then d.order_deconstruction(f) end n=n+1 end end end "
                               "rcon.print('old table deciders with no output wire: '..n..(%s and ' marked for deconstruction' or ' (dry run)')..'; still wired to a target (left alone): '..w)" % (lua_slots(pool), flag, flag)))
        return
    if step == "config" and new:
        print(config_new())
    elif step == "config" or (step == "build" and apply):
        print(tools["run_lua"](sub(CONFIG)))
    elif step == "status":
        print(tools["run_lua"](sub(STATUS)).replace(" ;; ", "\n"))


if __name__ == "__main__":
    main()
