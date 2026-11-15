#!/usr/bin/env python3
"""The Replicator's fluid-assembler unit (the Captain, 2026-11-14: "use the barrel-fed design"): makes the items whose ASSEMBLER recipe needs a fluid,
which scripts/omni_maker.py leaves out (its machines have no pipes) and scripts/omni_fluid.py (chemistry only) cannot make.

Items (generated from the game's recipes, not typed): processing-unit (sulfuric acid), electric-engine-unit and the three express belt parts
(lubricant), concrete and refined-concrete (water), rocket-fuel (light oil), superconductor (light oil, electromagnetic plant). Rule: an enabled recipe the
unit's MAKER machine can run, one item product, exactly ONE fluid ingredient that has a barrel, no fluid product, product not already on the assembler list,
product not a barrel. The crude-oil and heavy-oil barrels are not made here: they are the raw barrels the fluid units ask for (scripts/nauvis_taps.py).

Barrel-fed, like omni_fluid.py: no pipes to the network. Two machines, the maker P and an emptier E (an assembling machine 3 whose recipe is
empty-<fluid>-barrel) whose fluid OUTPUT touches P's fluid INPUT. The geometry depends on P (prototype fluid ports, read from the game):
  --maker assembling-machine-3 (default)   E stands directly above P, both facing north (input top centre, output bottom centre)
  --maker electromagnetic-plant            a 4 x 4 plant with its fluid inputs on the WEST and EAST faces: E stands west of it, facing west (output east)
  blue requester chests, one for each machine (P: the solid ingredients; E: the barrels of the fluid P needs, never more than a batch)
  red provider chests, one for each machine (P: the product; E: the empty barrels), emptied by inserters; robots do the rest
Control is omni_maker's: the demand roboport's MISSING REQUESTS, the unit's item list (constant combinator), a decider that passes only what
this unit can make, a selector that picks the most-missing item, and a table of 4 deciders a recipe (P recipe, P solids, E recipe, E barrels).
A decider puts its outputs on both wires, so one decider serves one target: the recipe table is 4 deciders wide for each item.

Planet Replicators (docs/planet-replicators-plan.md): --planet fulgora --menu superconductor --demand 124 -76 (the planet unit's roboport).
Steps (read-only unless --apply):  list | sites | build --at X Y [--apply] | config --at X Y | status --at X Y
(X, Y = the tile under P's centre.) Never apply `build` twice at one site. Run `config` after `build --apply` and after any new recipe is researched.
Options: --planet NAME (default nauvis)  --maker ENTITY  --menu a,b (only those products)  --demand X Y (default: the Nauvis Replicator's roboport)."""
import json
import sys

from _game import tools

BATCH = 10
Q = {"quality": "epic"}
N, E, S, W = 0, 4, 8, 12


def opt(name, n=1, default=None):
    if name not in sys.argv:
        return default
    i = sys.argv.index(name)
    vals = sys.argv[i + 1:i + 1 + n]
    return vals[0] if n == 1 else vals


PLANET = opt("--planet", default="nauvis")
MAKER = opt("--maker", default="assembling-machine-3")
MENU = [m for m in (opt("--menu", default="") or "").split(",") if m]
DEMAND = tuple(int(v) for v in opt("--demand", 2, ["-352", "-229"]))        # the roboport whose red wire carries the demand
EM = MAKER == "electromagnetic-plant"
FOUNDRY = MAKER == "foundry"
BIOCH = MAKER == "biochamber"
RECIPES = [m for m in (opt("--recipes", default="") or "").split(",") if m]      # only these recipe names (a product may have several)
SOLID = "--solid" in sys.argv                                                    # also allow recipes with NO fluid (the emptier then idles)
FUEL = (opt("--fuel", default="") or "").split(":")                              # item:amount asked for every order, for a burner maker (biochamber: nutrients)
FUEL_ITEM, FUEL_AMT = (FUEL[0], int(FUEL[1])) if len(FUEL) == 2 else ("", 0)

# Entity centres relative to the site tile (cx, cy). name -> (dx, dy[, direction]).
if FOUNDRY:
    # a 5 x 5 foundry has its fluid inputs on the SOUTH face (orientation north: first input at x-1); the emptier stands directly south of it, facing south
    # (assembler output on its top centre), x-1 from the foundry's centre; chests west and east like the stacked unit.
    GEOM = {"P": (0.5, 0.5), "E": (-0.5, 4.5, S), "reqP": (-3.5, 0.5), "inP": (-2.5, 0.5, W), "outP": (3.5, 0.5, W), "chP": (4.5, 0.5),
            "reqE": (-3.5, 4.5), "inE": (-2.5, 4.5, W), "outE": (1.5, 4.5, W), "chE": (2.5, 4.5),
            "cc": (-6.5, -3.5), "dec": (-6.5, -1.0), "sel": (-5.5, -1.0), "sub": (7.0, -3.0), "table": (-6, 9)}
elif BIOCH:
    GEOM = {"P": (0.5, 0.5), "E": (-0.5, -2.5, N), "reqP": (-2.5, 0.5), "inP": (-1.5, 0.5, W), "outP": (2.5, 0.5, W), "chP": (3.5, 0.5),
            "reqE": (-3.5, -2.5), "inE": (-2.5, -2.5, W), "outE": (1.5, -2.5, W), "chE": (2.5, -2.5),
            "cc": (-5.5, -5.5), "dec": (-5.5, -3.0), "sel": (-4.5, -3.0), "sub": (6.0, -5.0), "table": (-6, 4)}
elif EM:
    GEOM = {"P": (0.0, 0.0), "E": (-3.5, 0.5, W), "reqP": (0.5, -3.5), "inP": (0.5, -2.5, N), "outP": (0.5, 2.5, N), "chP": (0.5, 3.5),
            "reqE": (-3.5, -2.5), "inE": (-3.5, -1.5, N), "outE": (-3.5, 2.5, N), "chE": (-3.5, 3.5),
            "cc": (-6.5, -6.5), "dec": (-6.5, -4.0), "sel": (-5.5, -4.0), "sub": (4.0, -4.0), "table": (-6, 6)}
else:
    GEOM = {"P": (0.5, 0.5), "E": (0.5, -2.5, N), "reqP": (-2.5, 0.5), "inP": (-1.5, 0.5, W), "outP": (2.5, 0.5, W), "chP": (3.5, 0.5),
            "reqE": (-2.5, -2.5), "inE": (-1.5, -2.5, W), "outE": (2.5, -2.5, W), "chE": (3.5, -2.5),
            "cc": (-5.5, -5.5), "dec": (-5.5, -3.0), "sel": (-4.5, -3.0), "sub": (6.0, -5.0), "table": (-6, 4)}


def pos(cx, cy, key):
    g = GEOM[key]
    return cx + g[0], cy + g[1]


LIST = r'''
local f=game.forces.player
local am3=prototypes.entity['assembling-machine-3'].crafting_categories
local mk=prototypes.entity['MAKERENT'].crafting_categories
local MENU={MENUTAB}
local RECS={RECTAB}
local SOLIDOK=SOLIDFLAG
local function recok(n) return next(RECS)==nil or RECS[n]==true end
local function menuok(it) return next(MENU)==nil or MENU[it]==true end
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
  if r.enabled and has_cat(p,mk) and not p.hidden and #r.products==1 and r.products[1].type=='item' then
    local it=r.products[1].name
    if menuok(it) and recok(name) and not it:find('%-barrel$') and not plain[it] and not seen[it] and not name:find('recycling') then
      local nf,fl,si,ok=0,nil,{},true
      for _,i in pairs(r.ingredients) do
        if i.type=='fluid' then nf=nf+1 fl=i if not bar[i.name] then ok=false end else si[#si+1]=i end
      end
      if ok and (nf==1 or (SOLIDOK and nf==0)) then seen[it]=true rs[#rs+1]={name=name,key=it,fl=fl,si=si} end
    end
  end
end
'''.replace("MAKERENT", MAKER).replace("MENUTAB", ",".join(f"['{m}']=true" for m in MENU)).replace("RECTAB", ",".join(f"['{m}']=true" for m in RECIPES)).replace("SOLIDFLAG", "true" if SOLID else "false")


def layout(cx, cy):
    """Entities of one unit; positions are entity centres."""
    out = []

    def add(name, key, d=None):
        x, y = pos(cx, cy, key)
        g = GEOM[key]
        out.append({"name": name, "x": x, "y": y, "direction": g[2] if len(g) > 2 and d is None else (d or 0), "params": dict(Q)})

    add(MAKER, "P")
    out[-1]["direction"] = N
    add("assembling-machine-3", "E")
    for q, i, o, c in (("reqP", "inP", "outP", "chP"), ("reqE", "inE", "outE", "chE")):
        add("requester-chest", q)
        add("fast-inserter", i)
        add("fast-inserter", o)
        add("passive-provider-chest", c)
    add("constant-combinator", "cc")
    add("decider-combinator", "dec")
    add("selector-combinator", "sel")
    add("substation", "sub")
    return out


def table_slots(cx, cy, n):
    """Top-left tile of the 4 deciders of each of n recipes (1 x 2 each), one long row south of the unit."""
    tx, ty = GEOM["table"]
    return [(cx + tx + 4 * i + j, cy + ty) for i in range(n) for j in range(4)]


def recipes():
    code = LIST + "local o={} for _,r in ipairs(rs) do o[#o+1]=r.key..'|'..r.name..'|'..(r.fl and (r.fl.name..' x'..r.fl.amount..'|'..bar[r.fl.name]) or 'solid|-') end rcon.print(helpers.table_to_json(o))"
    return json.loads(tools["run_lua"](code))


def table_entities(cx, cy, n):
    return [{"name": "decider-combinator", "x": tx + 0.5, "y": ty + 1.0, "direction": N, "params": dict(Q)} for tx, ty in table_slots(cx, cy, n)]


def place(cx, cy, apply):
    n = len(recipes())
    ents = layout(cx, cy) + table_entities(cx, cy, n)
    r = json.loads(tools["place_entities"](json.dumps(ents), surface=PLANET, dry_run=not apply, clear_trees=apply))
    return n, r


GLUA = "local P,Em,reqP,reqE,cc,dec,sel=GP,GE,GRP,GRE,GCC,GDEC,GSEL "

CONFIG = LIST + r'''
local s=game.surfaces['SURF']
local W=defines.wire_connector_id
local CB={W.combinator_input_red,W.combinator_input_green,W.combinator_output_red,W.combinator_output_green}
local CC={W.circuit_red,W.circuit_green}
local function wire(a,ia,b,ib) a.get_wire_connector(ia,true).connect_to(b.get_wire_connector(ib,true),false) end
local function clr(e,ids) for _,id in pairs(ids) do e.get_wire_connector(id,true).disconnect_all() end end
local function at(n,x,y) return s.find_entities_filtered{name=n,position={x,y},radius=0.4}[1] end
local P=at('MAKERENT',PX,PY)
local Em=at('assembling-machine-3',EX,EY)
local reqP=at('requester-chest',RPX,RPY)
local reqE=at('requester-chest',REX,REY)
local cc=at('constant-combinator',CCX,CCY)
local dec=at('decider-combinator',DCX,DCY)
local sel=at('selector-combinator',SLX,SLY)
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
    local o={{K(R(r.name),1)},{},{},{}}
    if r.fl then o[3]={K(R('empty-'..bar[r.fl.name]),1)} o[4]={K({type='item',name=bar[r.fl.name]},math.ceil(r.fl.amount*BATCH/50))} end
    for _,ing in pairs(r.si) do o[2][#o[2]+1]=K({type='item',name=ing.name},ing.amount*BATCH) end
    if 'FUELITEM'~='' then o[2][#o[2]+1]=K({type='item',name='FUELITEM'},FUELAMT) end
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
local s=game.surfaces['SURF']
local W=defines.wire_connector_id
local function at(n,x,y) return s.find_entities_filtered{name=n,position={x,y},radius=0.4}[1] end
local function st(e) local k='?' for a,v in pairs(defines.entity_status) do if v==e.status then k=a end end local r=e.get_recipe() local fl={} for n,v in pairs(e.get_fluid_contents()) do fl[#fl+1]=n..' '..math.floor(v) end return (r and r.name or 'no recipe')..', '..k..', made '..e.products_finished..(#fl>0 and (' ['..table.concat(fl,', ')..']') or '') end
local function inv(e) local t={} for _,it in pairs(e.get_inventory(defines.inventory.chest).get_contents()) do t[#t+1]=it.name..' '..it.count end return table.concat(t,', ') end
local P=at('MAKERENT',PX,PY)
local Em=at('assembling-machine-3',EX,EY)
local o={}
if not (P and Em) then rcon.print('unit not built') return end
local sel=at('selector-combinator',SLX,SLY)
local ch={}
local n=sel and sel.get_circuit_network(W.combinator_output_green)
if n and n.signals then for _,x in pairs(n.signals) do ch[#ch+1]=x.signal.name..' '..x.count end end
o[#o+1]='chosen: '..table.concat(ch,', ')
o[#o+1]='P (makes): '..st(P)..' | blue: '..inv(at('requester-chest',RPX,RPY))..' | red: '..inv(at('passive-provider-chest',CPX,CPY))
o[#o+1]='E (empties): '..st(Em)..' | blue: '..inv(at('requester-chest',REX,REY))..' | red: '..inv(at('passive-provider-chest',CEX,CEY))
rcon.print(table.concat(o,'\n'))
'''


def sub(code, cx, cy):
    n = len(recipes())
    sl = "{" + ",".join("{%d,%d}" % t for t in table_slots(cx, cy, n)) + "}"
    rep = {"PX": pos(cx, cy, "P"), "EX": pos(cx, cy, "E"), "RPX": pos(cx, cy, "reqP"), "REX": pos(cx, cy, "reqE"), "CCX": pos(cx, cy, "cc"), "DCX": pos(cx, cy, "dec"),
           "SLX": pos(cx, cy, "sel"), "CPX": pos(cx, cy, "chP"), "CEX": pos(cx, cy, "chE")}
    import re
    for k, (x, y) in rep.items():
        code = re.sub(r"\b%s\b" % k, str(x), code)
        code = re.sub(r"\b%s\b" % (k[:-1] + "Y"), str(y), code)
    code = re.sub(r"\bDX\b", str(DEMAND[0]), code)
    code = re.sub(r"\bDY\b", str(DEMAND[1]), code)
    return code.replace("FUELITEM", FUEL_ITEM).replace("FUELAMT", str(FUEL_AMT)).replace("MAKERENT", MAKER).replace("SLOTS", sl).replace("SURF", PLANET).replace("BATCH", str(BATCH))


SITE_PROBE = r'''
local s=game.surfaces['SURF']
local f=game.forces.player
local x,y=PX0,PY0
local nets=s.find_logistic_networks_by_construction_area({x,y},f)
local pole=s.find_entities_filtered{type='electric-pole',position={x,y},radius=30}
local near=1e9
for _,p in pairs(pole) do local d=math.sqrt((p.position.x-x)^2+(p.position.y-y)^2) if d<near then near=d end end
rcon.print('network '..#nets..', nearest pole '..(near<1e9 and string.format('%.0f',near) or 'none within 30'))
'''

PATCHES = r'''
local s=game.surfaces['SURF']
local f=game.forces.player
local big,mainid=0,nil
for _,rp in pairs(s.find_entities_filtered{name='roboport'}) do local n=rp.logistic_network if n and #n.cells>big then big=#n.cells mainid=n.network_id end end
local function land(x,y) local t=s.get_tile(x,y).name return not (t:find('oil') or t:find('out%-of%-map') or t:find('lava') or t:find('water')) end
local out={}
local W,H=16,14
for x=XMIN,XMAX do for y=YMIN,YMAX do
  local ok=true
  for gx=0,W-1,3 do for gy=0,H-1,3 do if not land(x+gx,y+gy) then ok=false break end end if not ok then break end end
  if ok and land(x+W-1,y+H-1) then
    local area={{x,y},{x+W,y+H}}
    if s.count_entities_filtered{area=area,type={'resource','tree','corpse','projectile','simple-entity','decorative'},invert=true}==0 then
      local nets=s.find_logistic_networks_by_construction_area({x+W/2,y+H/2},f)
      for _,n in pairs(nets) do if n.network_id==mainid then out[#out+1]=x..','..y break end end
    end
  end
end end
rcon.print(table.concat(out,';'))
'''


def at_arg():
    a = opt("--at", 2)
    if not a:
        sys.exit("give the site: --at X Y (the tile under P's centre)")
    return int(a[0]), int(a[1])


def main():
    step = sys.argv[1] if len(sys.argv) > 1 else "list"
    apply = "--apply" in sys.argv
    if step == "list":
        rows = recipes()
        print(f"{len(rows)} items this unit ({MAKER}) can make on {PLANET} (item | recipe | fluid | barrel):")
        for r in rows:
            print("  ", r)
    elif step == "sites":
        box = opt("--box", 4, ["90", "240", "-230", "-30"])
        patches = tools["run_lua"](PATCHES.replace("SURF", PLANET).replace("XMIN", box[0]).replace("XMAX", box[1]).replace("YMIN", box[2]).replace("YMAX", box[3])).strip()
        found = 0
        for p in patches.split(";") if patches else []:
            px, py = (int(v) for v in p.split(","))
            cx, cy = px + 8, py + 7
            n, r = place(cx, cy, False)
            if not r.get("failed"):
                probe = tools["run_lua"](SITE_PROBE.replace("SURF", PLANET).replace("PX0", str(cx)).replace("PY0", str(cy)))
                print(f"clean site --at {cx} {cy}: {n} item(s), {r.get('placed')} entities | {probe.strip()}")
                found += 1
                if found >= int(opt("--max", default="6")):
                    break
        if not found:
            print("no clean site among", len(patches.split(";")) if patches else 0, "land patches")
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
