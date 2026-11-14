#!/usr/bin/env python3
"""The Replicator's fluid-assembler unit (the Captain, 2026-11-14: "use the barrel-fed design"): makes the items whose ASSEMBLER recipe needs a fluid,
which scripts/omni_maker.py leaves out (its machines have no pipes) and scripts/omni_fluid.py (chemistry only) cannot make.

Items (generated from the game's recipes, not typed): processing-unit (sulfuric acid), electric-engine-unit and the three express belt parts
(lubricant), concrete and refined-concrete (water), rocket-fuel (light oil). Rule: an enabled recipe an assembling machine 3 can run, one item
product, exactly ONE fluid ingredient that has a barrel, no fluid product, product not already on the assembler list, product not a barrel.
The crude-oil and heavy-oil barrels are not made here: they are the raw barrels the fluid units ask for (scripts/nauvis_taps.py fills them).

Barrel-fed, like omni_fluid.py: no pipes to the network. Two assembling machines 3 face north, one above the other, same x:
  E  (above)  empties barrels: its recipe is empty-<fluid>-barrel; its fluid OUTPUT (bottom centre) touches P's fluid INPUT (top centre)
  P  (below)  makes the item, recipe set by circuit
  blue requester chests, one for each machine (P: the solid ingredients; E: the barrels of the fluid P needs, never more than a batch)
  red provider chests, one for each machine (P: the product; E: the empty barrels), emptied by inserters; robots do the rest
Control is omni_maker's: the demand roboport's MISSING REQUESTS, the unit's item list (constant combinator), a decider that passes only what
this unit can make, a selector that picks the most-missing item, and a table of 4 deciders a recipe (P recipe, P solids, E recipe, E barrels).
A decider puts its outputs on both wires, so one decider serves one target: the recipe table is 4 deciders wide for each item.

Steps (read-only unless --apply):  list | check [--at X Y ...] | build --at X Y [--apply] | config --at X Y | status --at X Y
(X, Y = the tile under P's centre.) Never apply `build` twice at one site. Run `config` after `build --apply` and after any new recipe is researched.
Demand wire: the Replicator's demand roboport (omni_maker site `replicator`), over-reach script wire."""
import json
import sys

from _game import tools

BATCH = 10
DEMAND = (-352, -229)          # the Replicator's demand roboport (omni_fluid.SITES['replicator']['demand'])
Q = {"quality": "epic"}
N, E, S, W = 0, 4, 8, 12

LIST = r'''
local f=game.forces.player
local am3=prototypes.entity['assembling-machine-3'].crafting_categories
local function has_cat(p,set) for _,c in pairs(p.categories) do if set[c] then return true end end return false end
local bar={}
for name,r in pairs(f.recipes) do if name:find('^empty%-') and r.enabled and #r.ingredients==1 then for _,p in pairs(r.products) do if p.type=='fluid' then bar[p.name]=r.ingredients[1].name end end end end
local plain={}
for name,r in pairs(f.recipes) do
  local p=r.prototype
  if r.enabled and has_cat(p,am3) and not p.hidden and #r.products==1 and r.products[1].type=='item' and not name:find('science%-pack') and not name:find('recycling') then
    local solid=true
    for _,i in pairs(r.ingredients) do if i.type~='item' then solid=false end end
    if solid then plain[r.products[1].name]=true end
  end
end
local names={}
for name,_ in pairs(f.recipes) do names[#names+1]=name end
table.sort(names)
local rs,seen={},{}
for _,name in pairs(names) do
  local r=f.recipes[name]
  local p=r.prototype
  if r.enabled and has_cat(p,am3) and not p.hidden and #r.products==1 and r.products[1].type=='item' then
    local it=r.products[1].name
    if not it:find('%-barrel$') and not plain[it] and not seen[it] and not name:find('recycling') then
      local nf,fl,si,ok=0,nil,{},true
      for _,i in pairs(r.ingredients) do
        if i.type=='fluid' then nf=nf+1 fl=i if not bar[i.name] then ok=false end else si[#si+1]=i end
      end
      if ok and nf==1 then seen[it]=true rs[#rs+1]={name=name,key=it,fl=fl,si=si} end
    end
  end
end
'''


def layout(cx, cy):
    """Entities of one unit; (cx, cy) is the tile under P's centre. Positions are entity centres."""
    out = []

    def add(name, x, y, d=N):
        out.append({"name": name, "x": x, "y": y, "direction": d, "params": dict(Q)})

    add("assembling-machine-3", cx + 0.5, cy + 0.5)               # P, fluid input at its top centre
    add("assembling-machine-3", cx + 0.5, cy - 2.5)               # E, fluid output at its bottom centre
    for dy, tag in ((0, "P"), (-3, "E")):
        add("requester-chest", cx - 2.5, cy + dy + 0.5)           # blue: solids for P, barrels for E
        add("fast-inserter", cx - 1.5, cy + dy + 0.5, W)          # direction = pickup side: takes from the chest on its west
        add("fast-inserter", cx + 2.5, cy + dy + 0.5, W)          # takes from the machine on its west, drops east
        add("passive-provider-chest", cx + 3.5, cy + dy + 0.5)    # red: product / empty barrels
    add("constant-combinator", cx - 5.5, cy - 5.5)
    add("decider-combinator", cx - 5.5, cy - 3.0)
    add("selector-combinator", cx - 4.5, cy - 3.0)
    add("substation", cx + 6.0, cy - 5.0)
    return out


def table_slots(cx, cy, n):
    """Top-left tile of the 4 deciders of each of n recipes (1 x 2 each), one long row south of the unit."""
    return [(cx - 6 + 4 * i + j, cy + 4) for i in range(n) for j in range(4)]


def recipes():
    return json.loads(tools["run_lua"](LIST + "local o={} for _,r in ipairs(rs) do o[#o+1]=r.key..'|'..r.name..'|'..r.fl.name..' x'..r.fl.amount..'|'..bar[r.fl.name] end rcon.print(table.concat(o,'\\n'))".replace("rcon.print(table.concat(o,'\\n'))", "rcon.print(helpers.table_to_json(o))")))


def table_entities(cx, cy, n):
    return [{"name": "decider-combinator", "x": tx + 0.5, "y": ty + 1.0, "direction": N, "params": dict(Q)} for tx, ty in table_slots(cx, cy, n)]


def place(cx, cy, apply):
    n = len(recipes())
    ents = layout(cx, cy) + table_entities(cx, cy, n)
    r = json.loads(tools["place_entities"](json.dumps(ents), surface="nauvis", dry_run=not apply, clear_trees=apply))
    return n, r


CONFIG = LIST + r'''
local s=game.surfaces.nauvis
local W=defines.wire_connector_id
local CB={W.combinator_input_red,W.combinator_input_green,W.combinator_output_red,W.combinator_output_green}
local CC={W.circuit_red,W.circuit_green}
local function wire(a,ia,b,ib) a.get_wire_connector(ia,true).connect_to(b.get_wire_connector(ib,true),false) end
local function clr(e,ids) for _,id in pairs(ids) do e.get_wire_connector(id,true).disconnect_all() end end
local function at(n,x,y) return s.find_entities_filtered{name=n,position={x,y},radius=0.4}[1] end
local cx,cy=CX,CY
local P=at('assembling-machine-3',cx+0.5,cy+0.5)
local Em=at('assembling-machine-3',cx+0.5,cy-2.5)
local reqP=at('requester-chest',cx-2.5,cy+0.5)
local reqE=at('requester-chest',cx-2.5,cy-2.5)
local cc=at('constant-combinator',cx-5.5,cy-5.5)
local dec=at('decider-combinator',cx-5.5,cy-3.0)
local sel=at('selector-combinator',cx-4.5,cy-3.0)
local rp=s.find_entities_filtered{name='roboport',position={DX,DY},radius=0.6}[1]
if not (P and Em and reqP and reqE and cc and dec and sel and rp) then rcon.print('unit incomplete: build it first') return end
local cb=cc.get_or_create_control_behavior()
while cb.sections_count>0 do cb.remove_section(1) end
local sec=cb.add_section()
for i,r in pairs(rs) do sec.set_slot(i,{value={type='item',name=r.key,quality='normal'},min=1}) end
clr(dec,CB) clr(sel,CB)
wire(dec,W.combinator_input_red,rp,W.circuit_red)
wire(dec,W.combinator_input_green,cc,W.circuit_green)
dec.get_or_create_control_behavior().parameters={conditions={{first_signal={type='virtual',name='signal-each'},first_signal_networks={red=true,green=false},comparator='>',constant=0},{first_signal={type='virtual',name='signal-each'},first_signal_networks={red=false,green=true},comparator='>',constant=0,compare_type='and'}},outputs={{signal={type='virtual',name='signal-each'},copy_count_from_input=true,networks={red=true,green=false}}}}
wire(sel,W.combinator_input_red,dec,W.combinator_output_red)
sel.get_or_create_control_behavior().parameters={operation='select',select_max=true,index_constant=0}
for _,m in pairs{P,Em} do clr(m,CC) local b=m.get_or_create_control_behavior() b.circuit_set_recipe=true b.circuit_read_ingredients=false end
for _,q in pairs{reqP,reqE} do clr(q,CC) local b=q.get_or_create_control_behavior() b.set_requests=true b.read_contents=false q.get_logistic_point(defines.logistic_member_index.logistic_container).trash_not_requested=true end
local function R(n) return {type='recipe',name=n} end
local function K(sg,k) return {signal=sg,copy_count_from_input=false,constant=k} end
local SL=SLOTS
local n=0
for i,r in pairs(rs) do
  local d={}
  for j=1,4 do local sp=SL[(i-1)*4+j] d[j]=s.find_entities_filtered{name='decider-combinator',position={sp[1]+0.5,sp[2]+1},radius=0.3}[1] end
  if d[1] and d[2] and d[3] and d[4] then
    local cond={{first_signal={type='item',name=r.key},comparator='>',constant=0}}
    local o={{K(R(r.name),1)},{},{K(R('empty-'..bar[r.fl.name]),1)},{K({type='item',name=bar[r.fl.name]},math.ceil(r.fl.amount*BATCH/50))}}
    for _,ing in pairs(r.si) do o[2][#o[2]+1]=K({type='item',name=ing.name},ing.amount*BATCH) end
    local tgt={{P,W.circuit_red},{reqP,W.circuit_green},{Em,W.circuit_red},{reqE,W.circuit_green}}
    for j=1,4 do
      clr(d[j],CB)
      d[j].get_or_create_control_behavior().parameters={conditions=cond,outputs=o[j]}
      wire(d[j],W.combinator_input_green,sel,W.combinator_output_green)
      local oc=(tgt[j][2]==W.circuit_red) and W.combinator_output_red or W.combinator_output_green
      wire(d[j],oc,tgt[j][1],tgt[j][2])
    end
    n=n+1
  end
end
local t={} for _,r in pairs(rs) do t[#t+1]=r.key end
rcon.print('recipes wired '..n..' of '..#rs..': '..table.concat(t,', '))
'''

STATUS = LIST + r'''
local s=game.surfaces.nauvis
local W=defines.wire_connector_id
local cx,cy=CX,CY
local function at(n,x,y) return s.find_entities_filtered{name=n,position={x,y},radius=0.4}[1] end
local function st(e) local k='?' for a,v in pairs(defines.entity_status) do if v==e.status then k=a end end local r=e.get_recipe() local fl={} for n,v in pairs(e.get_fluid_contents()) do fl[#fl+1]=n..' '..math.floor(v) end return (r and r.name or 'no recipe')..', '..k..', made '..e.products_finished..(#fl>0 and (' ['..table.concat(fl,', ')..']') or '') end
local function inv(e) local t={} for _,it in pairs(e.get_inventory(defines.inventory.chest).get_contents()) do t[#t+1]=it.name..' '..it.count end return table.concat(t,', ') end
local P=at('assembling-machine-3',cx+0.5,cy+0.5)
local Em=at('assembling-machine-3',cx+0.5,cy-2.5)
local o={}
if not (P and Em) then rcon.print('unit not built') return end
local sel=at('selector-combinator',cx-4.5,cy-3.0)
local ch={}
local n=sel and sel.get_circuit_network(W.combinator_output_green)
if n and n.signals then for _,x in pairs(n.signals) do ch[#ch+1]=x.signal.name..' '..x.count end end
o[#o+1]='chosen: '..table.concat(ch,', ')
o[#o+1]='P (makes): '..st(P)..' | blue: '..inv(at('requester-chest',cx-2.5,cy+0.5))..' | red: '..inv(at('passive-provider-chest',cx+3.5,cy+0.5))
o[#o+1]='E (empties): '..st(Em)..' | blue: '..inv(at('requester-chest',cx-2.5,cy-2.5))..' | red: '..inv(at('passive-provider-chest',cx+3.5,cy-2.5))
rcon.print(table.concat(o,'\n'))
'''


def sub(code, cx, cy):
    n = len(recipes())
    sl = "{" + ",".join("{%d,%d}" % t for t in table_slots(cx, cy, n)) + "}"
    return code.replace("SLOTS", sl).replace("CX", str(cx)).replace("CY", str(cy)).replace("DX", str(DEMAND[0])).replace("DY", str(DEMAND[1])).replace("BATCH", str(BATCH))


SITE_PROBE = r'''
local s=game.surfaces.nauvis
local f=game.forces.player
local x,y=PX,PY
local nets=s.find_logistic_networks_by_construction_area({x,y},f)
local pole=s.find_entities_filtered{type='electric-pole',position={x,y},radius=30}
local near=1e9
for _,p in pairs(pole) do local d=math.sqrt((p.position.x-x)^2+(p.position.y-y)^2) if d<near then near=d end end
rcon.print('network '..#nets..', nearest pole '..(near<1e9 and string.format('%.0f',near) or 'none within 30'))
'''


def at_arg():
    if "--at" not in sys.argv:
        sys.exit("give the site: --at X Y (the tile under P's centre)")
    i = sys.argv.index("--at")
    return int(sys.argv[i + 1]), int(sys.argv[i + 2])


def main():
    step = sys.argv[1] if len(sys.argv) > 1 else "list"
    apply = "--apply" in sys.argv
    if step == "list":
        rows = recipes()
        print(f"{len(rows)} items this unit can make (item | recipe | fluid | barrel):")
        for r in rows:
            print("  ", r)
    elif step == "check":
        cands = []
        if "--at" in sys.argv:
            cands.append(at_arg())
        else:
            cands = [(-330, -178), (-300, -178), (-270, -178), (-340, -184), (-282, -215), (-282, -200), (-270, -240), (-330, -246)]
        for cx, cy in cands:
            n, r = place(cx, cy, False)
            probe = tools["run_lua"](SITE_PROBE.replace("PX", str(cx)).replace("PY", str(cy)))
            print(f"site ({cx},{cy}): items {n}, placeable {r.get('placed')}, failed {len(r.get('failed') or [])} | {probe.strip()}")
            if r.get("failed"):
                print("    first failure:", json.dumps(r["failed"][:2])[:300])
    elif step == "build":
        cx, cy = at_arg()
        n, r = place(cx, cy, apply)
        print("items", n, "placed" if apply else "dry run", r.get("placed"), "failed", json.dumps(r.get("failed") or [])[:400])
        if apply:
            print(tools["run_lua"](sub(CONFIG, cx, cy)))
    elif step == "config":
        cx, cy = at_arg()
        print(tools["run_lua"](sub(CONFIG, cx, cy)))
    elif step == "status":
        cx, cy = at_arg()
        print(tools["run_lua"](sub(STATUS, cx, cy)))


if __name__ == "__main__":
    main()
