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
Usage: omni_fluid.py build [--apply] | config | status"""
import json
import sys

from _game import tools

CX, CY = 15, -388            # the plant's centre tile
RX, RY = 4, -398             # top-left tile of the recipe table (two rows of deciders, two columns a recipe)
RY2 = -382                   # its second block, south of the plant
DEMAND = (-28, -398)         # the roboport of scripts/omni_maker.py that reads missing requests
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
    first = len(ents)
    for i in range(n):
        for dx, dy in ((0, 0), (1, 0), (0, 2), (1, 2)):
            e("decider-combinator", RX + 2 * i + dx, RY + dy, 1, 2)
    second = len(ents)
    for i in range(n):                                          # the second block: a decider puts its outputs on both wires, so one
        for dx, dy in ((0, 0), (1, 0), (0, 2), (1, 2)):         # decider can serve only one machine or chest (eight a recipe)
            e("decider-combinator", RX + 2 * i + dx, RY2 + dy, 1, 2)
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
          "local n=0 for i,r in pairs(rs) do local x0=TX+2*(i-1) local d={} for j,p in pairs{{0,0},{1,0},{0,2},{1,2}} do d[j]=s.find_entities_filtered{name='decider-combinator',position={x0+p[1]+0.5,TY+p[2]+1},radius=0.3}[1] "
          "d[j+4]=s.find_entities_filtered{name='decider-combinator',position={x0+p[1]+0.5,TY2+p[2]+1},radius=0.3}[1] end local all=true for j=1,8 do if not d[j] then all=false end end "
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


def sub(code):
    return (code.replace("CX", str(CX)).replace("CY", str(CY)).replace("TY2", str(RY2)).replace("TX", str(RX)).replace("TY", str(RY)).replace("DX", str(DEMAND[0])).replace("DY", str(DEMAND[1])).replace("BATCH", str(BATCH)))


def main():
    step = sys.argv[1]
    apply = "--apply" in sys.argv
    if step == "build":
        n = int(tools["run_lua"](LIST + "rcon.print(#rs)").strip())
        r = json.loads(tools["place_entities"](json.dumps(layout(n, "--more" in sys.argv)), surface="nauvis", dry_run=not apply))
        print("recipes", n, "placed" if apply else "dry run", r.get("placed"), "failed", json.dumps(r.get("failed") or [])[:400])
    if step == "config" or (step == "build" and apply):
        print(tools["run_lua"](sub(CONFIG)))
    elif step == "status":
        print(tools["run_lua"](sub(STATUS)).replace(" ;; ", "\n"))


if __name__ == "__main__":
    main()
