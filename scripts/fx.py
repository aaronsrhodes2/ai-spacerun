#!/usr/bin/env python3
"""
fx - cheap, scripted Factorio helpers for the AI co-pilot (one RCON round trip per step, no screenshots, no hand-built Lua).

    fx.py clear       AREA [--trees --rocks --cliffs --biters --decoratives --fish --items --corpses | --all | --planner] [--apply]
    fx.py upgrade     AREA [--belts --inserters --chests --machines --poles --furnaces --bulk | --all | --planner]
                           [--modules speed|productivity|efficiency --from-chest X Y | --from-hub] [--apply]
    fx.py bottlenecks [AREA] [--json] [--top N]
    fx.py compact     AREA [--keep N] [--apply]
    fx.py mine        AREA --resource ORE [--out N|E|S|W] [--belt NAME] [--min-tiles N] [--apply]

AREA is `--area X1 Y1 X2 Y2` (tiles, inclusive) or `--around X Y R`. Surface defaults to nauvis (`--surface NAME`).
Everything except `bottlenecks` is a dry run unless `--apply` is given, and prints what it would do. See .claude/skills/factorio/SKILL.md.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _game import tools  # noqa: E402

from bridge.factorio import fx_compact  # noqa: E402


def lua(code):
    out = tools["run_lua"](code)
    if "Cannot execute command" in out or out.startswith("{\"error"):
        raise SystemExit("Lua error: " + out[:600])
    return out


def jlua(code):
    out = lua(code)
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        raise SystemExit("unexpected reply: " + out[:600])


def area_of(a):
    if a.around:
        x, y, r = a.around
        return int(x - r), int(y - r), int(x + r), int(y + r)
    if a.area:
        return tuple(int(v) for v in a.area)
    raise SystemExit("give --area X1 Y1 X2 Y2 or --around X Y R")


def a_box(area):
    x1, y1, x2, y2 = area
    return "{{%d,%d},{%d,%d}}" % (x1, y1, x2 + 1, y2 + 1)


def surf(a):
    return "game.surfaces['%s']" % a.surface



COVERAGE = """
local s=%(surf)s local A=%(box)s local n=0 local bots=0 local ex={}
local cx,cy=(A[1][1]+A[2][1])/2,(A[1][2]+A[2][2])/2
for _,r in pairs(s.find_entities_filtered{type='roboport',force='player'}) do
  local cell=r.logistic_cell local rad=cell and cell.construction_radius or 0
  local dx=math.max(A[1][1]-r.position.x,0,r.position.x-A[2][1]) local dy=math.max(A[1][2]-r.position.y,0,r.position.y-A[2][2])
  if dx*dx+dy*dy<=rad*rad then n=n+1 local net=r.logistic_network if net then bots=math.max(bots,net.all_construction_robots) end end
end
rcon.print(helpers.table_to_json({roboports=n,construction_robots=bots}))
"""


def coverage_note(a, area):
    cov = jlua(COVERAGE % {"surf": surf(a), "box": a_box(area)})
    if not cov["roboports"]:
        return "NO roboport covers this area: marks would sit until a roboport is built nearby (use the direct mode instead)"
    return f"{cov['roboports']} roboport(s) reach the area, up to {cov['construction_robots']} construction robots will do the work"

# --------------------------------------------------------------------------------------------- clear
def cmd_clear(a):
    area = area_of(a)
    if a.planner:
        code = f"""
local s={surf(a)} local A={a_box(area)} local apply={'true' if a.apply else 'false'} local f=game.forces.player
local inv=game.create_inventory(1) local st=inv[1] st.set_stack{{name='deconstruction-planner'}} st.trees_and_rocks_only=true
local before=#s.find_entities_filtered{{area=A,type={{'tree','simple-entity'}},to_be_deconstructed=false}}
if apply then s.deconstruct_area{{area=A,force=f,item=st}} end
local marked=#s.find_entities_filtered{{area=A,to_be_deconstructed=true}} inv.destroy()
rcon.print(helpers.table_to_json({{candidates=before,marked=marked}}))
"""
        res = jlua(code)
        print(("MARKED" if a.apply else "DRY RUN (add --apply)"), f"deconstruction planner (trees and rocks only), area {area}:", json.dumps(res))
        print("  " + coverage_note(a, area))
        print("  bots pick the marked trees/rocks up (wood, stone and coal go into the logistic network). Biters and decoratives are not planner jobs: use the direct mode for those.")
        return
    every = a.all or not any([a.trees, a.rocks, a.cliffs, a.biters, a.decoratives, a.fish, a.items, a.corpses])
    want = {k: (every or getattr(a, k)) for k in ("trees", "rocks", "cliffs", "biters", "decoratives", "fish", "items", "corpses")}
    code = f"""
local s={surf(a)} local A={a_box(area)} local apply={'true' if a.apply else 'false'} local out={{}}
local function add(k,e) out[k]=(out[k] or 0)+1 if apply and e.valid then e.destroy() end end
if {str(want['trees']).lower()} then for _,e in pairs(s.find_entities_filtered{{area=A,type='tree'}}) do add('tree',e) end end
if {str(want['rocks']).lower()} then for _,e in pairs(s.find_entities_filtered{{area=A,type={{'simple-entity','simple-entity-with-owner'}}}}) do if e.force.name~='player' and (e.name:find('rock') or e.name:find('stalagmite') or e.name:find('crater')) then add('rock:'..e.name,e) end end end
if {str(want['cliffs']).lower()} then for _,e in pairs(s.find_entities_filtered{{area=A,type='cliff'}}) do add('cliff',e) end end
if {str(want['fish']).lower()} then for _,e in pairs(s.find_entities_filtered{{area=A,type='fish'}}) do add('fish',e) end end
if {str(want['corpses']).lower()} then for _,e in pairs(s.find_entities_filtered{{area=A,type={{'corpse','rail-remnants'}}}}) do add('corpse',e) end end
if {str(want['items']).lower()} then for _,e in pairs(s.find_entities_filtered{{area=A,type='item-entity'}}) do add('item-on-ground',e) end end
if {str(want['biters']).lower()} then local en=game.forces['enemy'] if en then for _,e in pairs(s.find_entities_filtered{{area=A,force=en}}) do add('enemy:'..e.type,e) end end end
if {str(want['decoratives']).lower()} then local d=s.find_decoratives_filtered{{area=A}} local n=0 for _,x in pairs(d) do n=n+(x.amount or 1) end out['decoratives']=n if apply then s.destroy_decoratives{{area=A}} end end
rcon.print(helpers.table_to_json(out))
"""
    res = jlua(code)
    print(("CLEARED" if a.apply else "DRY RUN (add --apply)"), f"area {area} surface {a.surface}:", json.dumps(res) if res else "nothing to clear")


# --------------------------------------------------------------------------------------------- upgrade
CATS = {
    "belts": ["transport-belt", "fast-transport-belt", "underground-belt", "fast-underground-belt", "splitter", "fast-splitter"],
    "inserters": ["inserter", "burner-inserter"],
    "chests": ["wooden-chest", "iron-chest"],
    "storage": ["wooden-chest", "iron-chest", "steel-chest"],
    "machines": ["assembling-machine-1", "assembling-machine-2"],
    "poles": ["small-electric-pole"],
    "furnaces": ["stone-furnace", "steel-furnace"],
}


def cmd_upgrade(a):
    area = area_of(a)
    if a.planner:
        code = f"""
local s={surf(a)} local A={a_box(area)} local apply={'true' if a.apply else 'false'} local f=game.forces.player
local MAP={{{{'transport-belt','fast-transport-belt'}},{{'fast-transport-belt','express-transport-belt'}},{{'underground-belt','fast-underground-belt'}},{{'fast-underground-belt','express-underground-belt'}},{{'splitter','fast-splitter'}},{{'fast-splitter','express-splitter'}},{{'inserter','fast-inserter'}},{{'wooden-chest','iron-chest'}},{{'iron-chest','steel-chest'}},{{'assembling-machine-1','assembling-machine-2'}},{{'assembling-machine-2','assembling-machine-3'}},{{'small-electric-pole','medium-electric-pole'}}}}
local function enabled(n) local r=f.recipes[n] return r and r.enabled end
local by={{}} for _,m in pairs(MAP) do by[m[1]]=m[2] end
local inv=game.create_inventory(1) local st=inv[1] st.set_stack{{name='upgrade-planner'}} local slot=0 local used={{}}
for from,_ in pairs(by) do local t=by[from] local best=nil while t and enabled(t) do best=t t=by[t] end
  if best and slot<24 then slot=slot+1 st.set_mapper(slot,'from',{{type='entity',name=from}}) st.set_mapper(slot,'to',{{type='entity',name=best}}) used[#used+1]=from..'->'..best end end
local n=0 for _,e in pairs(s.find_entities_filtered{{area=A,force='player'}}) do if by[e.name] then n=n+1 end end
if apply then s.upgrade_area{{area=A,force=f,item=st}} end
inv.destroy()
rcon.print(helpers.table_to_json({{mappings=used,upgradable_entities=n}}))
"""
        res = jlua(code)
        print(("MARKED for upgrade" if a.apply else "DRY RUN (add --apply)"), f"upgrade planner, area {area}: {res['upgradable_entities']} entities can go up a tier")
        print("  mappings:", ", ".join(res["mappings"]))
        print("  " + coverage_note(a, area))
        print("  bots do the swaps and use items from the logistic network (a real cost, unlike the direct mode). Modules are not part of an upgrade planner: use --modules.")
        if a.modules:
            fill_modules(a, area)
        return
    every = a.all or not any([a.belts, a.inserters, a.chests, a.machines, a.poles, a.furnaces, a.bulk, a.modules, a.storage])
    cats = {k: (every and k != "furnaces" or getattr(a, k)) for k in CATS}
    names = [n for k, v in CATS.items() if cats[k] for n in v]
    if a.bulk:
        names += ["fast-inserter"]
    if every and not a.modules:
        pass
    code = f"""
local s={surf(a)} local A={a_box(area)} local apply={'true' if a.apply else 'false'} local f=game.forces.player
local MAP={{['transport-belt']='fast-transport-belt',['fast-transport-belt']='express-transport-belt',['underground-belt']='fast-underground-belt',['fast-underground-belt']='express-underground-belt',['splitter']='fast-splitter',['fast-splitter']='express-splitter',['inserter']='fast-inserter',['burner-inserter']='inserter',['wooden-chest']='iron-chest',['iron-chest']='steel-chest',['assembling-machine-1']='assembling-machine-2',['assembling-machine-2']='assembling-machine-3',['small-electric-pole']='medium-electric-pole',['stone-furnace']='steel-furnace',['steel-furnace']='electric-furnace'}}
if {str(bool(a.bulk)).lower()} then MAP['fast-inserter']='bulk-inserter' end
if {str(bool(a.storage)).lower()} then MAP['wooden-chest']='storage-chest' MAP['iron-chest']='storage-chest' MAP['steel-chest']='storage-chest' end
local function enabled(n) local r=f.recipes[n] return r and r.enabled end
local function target(n) local t=MAP[n] local best=nil while t and enabled(t) do best=t t=MAP[t] end return best end
local want={{{",".join("['%s']=1" % n for n in names)}}}
local counts={{}} local fail=0
for _,e in pairs(s.find_entities_filtered{{area=A,force='player'}}) do
  if want[e.name] then local t=target(e.name)
    if t then local k=e.name..' -> '..t counts[k]=(counts[k] or 0)+1
      if apply then local pos,dir,force,ty=e.position,e.direction,e.force,nil local flt,ip,op
        if e.type=='underground-belt' then ty=e.belt_to_ground_type end
        if e.type=='splitter' then flt=e.splitter_filter ip=e.splitter_input_priority op=e.splitter_output_priority end
        local p={{name=t,position=pos,direction=dir,force=force,fast_replace=true,spill=false}} if ty then p.type=ty end
        local ne=s.create_entity(p)
        if ne then if flt then ne.splitter_filter=flt end if ip then ne.splitter_input_priority=ip ne.splitter_output_priority=op end else fail=fail+1 end end end end end
rcon.print(helpers.table_to_json({{counts=counts,failed=fail}}))
"""
    res = jlua(code)
    print(("UPGRADED" if a.apply else "DRY RUN (add --apply)"), f"area {area}:")
    for k, v in sorted((res.get("counts") or {}).items()):
        print(f"  {v:5d}  {k}")
    if not res.get("counts"):
        print("  nothing to upgrade (everything at the best researched tier, or not in the selected categories)")
    if res.get("failed"):
        print("  FAILED to replace:", res["failed"])
    if a.modules:
        fill_modules(a, area)


def fill_modules(a, area):
    kind = a.modules
    src = ""
    if a.from_chest:
        src = ("local c=s.find_entities_filtered{name={'steel-chest','iron-chest','wooden-chest','storage-chest','passive-provider-chest','buffer-chest','requester-chest'},"
               "position={%s,%s},radius=1.5}[1] if c then src=c.get_inventory(defines.inventory.chest) end" % tuple(a.from_chest))
    elif a.from_hub:
        src = "for _,sf in pairs(game.surfaces) do if sf.platform and sf.platform.hub then src=sf.platform.hub.get_inventory(defines.inventory.hub_main) break end end"
    pick = (f"local best='{a.module_name}' if not (f.recipes[best] and f.recipes[best].enabled) then rcon.print(helpers.table_to_json({{error=best..' is not researched'}})) return end"
            if a.module_name else
            "local best=nil for _,k in pairs({3,2,1}) do local n=(k==1) and (kind..'-module') or (kind..'-module-'..k) local r=f.recipes[n] if r and r.enabled and (not src or src.get_item_count(n)>0) then best=n break end end "
            "if not best then rcon.print(helpers.table_to_json({error='no '..kind..' module is researched'..(src and ' / none in the source' or '')})) return end")
    budget = a.budget_mw if a.budget_mw is not None else -1
    code = f"""
local s={surf(a)} local A={a_box(area)} local apply={'true' if a.apply else 'false'} local f=game.forces.player local kind='{kind}'
local src=nil
{src}
{pick}
local spawn={'true' if a.spawn else 'false'}
local mod=prototypes.item[best] local per=(mod.module_effects and mod.module_effects.consumption or 0)
local budget={budget}*1e6 local used=0
local need,filled,machines,skipped=0,0,0,0
local order={{'lab','assembling-machine','furnace','mining-drill'}}
for _,ty in pairs(order) do
for _,e in pairs(s.find_entities_filtered{{area=A,force='player',type=ty}}) do
  local mi=e.get_module_inventory()
  if mi and #mi>0 then local empty=mi.count_empty_stacks()
    if empty>0 then machines=machines+1 need=need+empty
      local base=e.prototype.get_max_energy_usage and e.prototype.get_max_energy_usage(e.quality) or 0
      local cost=base*per*empty*60
      if budget>=0 and used+cost>budget then skipped=skipped+empty
      else used=used+cost
        if apply then
          if spawn then filled=filled+mi.insert{{name=best,count=empty}}
          elseif src then local have=src.get_item_count(best) local take=math.min(empty,have)
            if take>0 then local got=src.remove{{name=best,count=take}} local ins=mi.insert{{name=best,count=got}} filled=filled+ins if ins<got then src.insert{{name=best,count=got-ins}} end end end end end end end end end
rcon.print(helpers.table_to_json({{module=best,machines_with_empty_slots=machines,slots_empty=need,inserted=filled,left_for_budget=skipped,estimated_extra_mw=used/1e6,source=spawn and 'spawned' or (src and 'found' or 'none')}}))
"""
    res = jlua(code)
    if res.get("error"):
        print("modules:", res["error"])
        return
    print(("MODULES" if a.apply else "MODULES DRY RUN"), json.dumps(res))
    if a.apply and res.get("source") == "none":
        print("  no source given: pass --from-chest X Y, --from-hub or --spawn")


# --------------------------------------------------------------------------------------------- bottlenecks
STATUS_BAD = ("no_power", "low_power", "no_fuel", "no_minable_resources", "missing_required_fluid", "fluid_ingredient_shortage",
              "no_input_fluid", "disabled_by_control_behavior", "marked_for_deconstruction")

CENSUS = """
local s=%(surf)s local A=%(box)s local SN={} for k,v in pairs(defines.entity_status) do SN[v]=k end
local types={'assembling-machine','furnace','lab','mining-drill','boiler','reactor','generator','pump','offshore-pump','rocket-silo','inserter','roboport','radar','beacon'}
local stat={} local shortage={} local nm=0 local norecipe=0
local function lanes(b) local l={} for i=1,2 do local t={} for _,c in pairs(b.get_transport_line(i).get_contents()) do t[#t+1]={c.name,c.count} end l[#l+1]=t end return l end
for _,e in pairs(s.find_entities_filtered{area=A,force='player',type=types}) do
  local st=SN[e.status] or tostring(e.status)
  if st~='working' and st~='normal' and st~='waiting_for_source_items' and st~='waiting_for_space_in_destination' and st~='waiting_for_train' and st~='waiting_for_other_machines' then
    local k=e.type..':'..st stat[k]=(stat[k] or 0)+1 end
  if e.type=='assembling-machine' and not e.get_recipe() and e.name~='rocket-silo' then norecipe=norecipe+1 end
  if (st=='item_ingredient_shortage' or st=='fluid_ingredient_shortage') and nm<%(limit)d then
    local r=(e.type~='lab') and e.get_recipe() or nil
    if r then nm=nm+1
      local inv=e.get_inventory(defines.inventory.crafter_input) or e.get_inventory(defines.inventory.furnace_source)
      local miss={} for _,ing in pairs(r.ingredients) do if ing.type=='item' then if (inv and inv.get_item_count(ing.name) or 0)<ing.amount then miss[#miss+1]=ing.name end else if e.get_fluid_count(ing.name)<ing.amount then miss[#miss+1]=ing.name end end end
      local feeds={} local bb=e.bounding_box
      for _,i in pairs(s.find_entities_filtered{type='inserter',area={{bb.left_top.x-2.5,bb.left_top.y-2.5},{bb.right_bottom.x+2.5,bb.right_bottom.y+2.5}}}) do
        if i.drop_target==e then local p=i.pickup_target local d={ins=i.name,st=SN[i.status]}
          if p and (p.type=='transport-belt' or p.type=='underground-belt' or p.type=='splitter') then d.belt=lanes(p) elseif p then d.src=p.name end
          feeds[#feeds+1]=d end end
      local ing={} for _,q in pairs(r.ingredients) do ing[#ing+1]=q.name end
      shortage[#shortage+1]={r=r.name,x=math.floor(e.position.x),y=math.floor(e.position.y),miss=miss,ing=ing,fluid=(st=='fluid_ingredient_shortage'),feeds=feeds} end end
end
rcon.print(helpers.table_to_json({stat=stat,shortage=shortage,norecipe=norecipe}))
"""

PRODUCERS = """
local s=%(surf)s local want={%(items)s} local SN={} for k,v in pairs(defines.entity_status) do SN[v]=k end
local prod={} for name,r in pairs(prototypes.recipe) do for _,p in pairs(r.products) do if want[p.name] then prod[p.name]=prod[p.name] or {} table.insert(prod[p.name],name) end end end
local byrecipe={} for _,e in pairs(s.find_entities_filtered{force='player',type={'assembling-machine','furnace','mining-drill','boiler','generator','offshore-pump'}}) do
  local r=(e.type=='assembling-machine') and e.get_recipe() or nil local rn=r and r.name or nil
  if e.type=='furnace' then local pr=e.previous_recipe rn=pr and pr.name and pr.name.name or nil end
  if rn then local t=byrecipe[rn] or {} byrecipe[rn]=t local k=SN[e.status] or '?' t[k]=(t[k] or 0)+1 end end
local out={} for item,recs in pairs(prod) do local o={} for _,rn in pairs(recs) do if byrecipe[rn] then o[rn]=byrecipe[rn] end end out[item]=o end
rcon.print(helpers.table_to_json(out))
"""

LEDGER = """
local s=%(surf)s local ps=game.forces.player.get_item_production_statistics(s) local o={}
for _,n in pairs({%(items)s}) do o[n]={ps.get_flow_count{name=n,category='input',precision_index=defines.flow_precision_index.one_minute}/60,ps.get_flow_count{name=n,category='output',precision_index=defines.flow_precision_index.one_minute}/60} end
rcon.print(helpers.table_to_json(o))
"""


def cmd_bottlenecks(a):
    area = area_of(a) if (a.area or a.around) else (-1000, -1000, 1000, 1000)
    cen = jlua(CENSUS % {"surf": surf(a), "box": a_box(area), "limit": 800})
    groups = {}
    for m in cen["shortage"]:
        for item in m["miss"] or ["?"]:
            g = groups.setdefault((m["r"], item), {"n": 0, "ex": (m["x"], m["y"]), "belt_has_item": 0, "belt_other": {}, "belt_empty": 0, "no_feed": 0, "fluid": m["fluid"]})
            g["n"] += 1
            if not m["feeds"]:
                g["no_feed"] += 1
            for f in m["feeds"]:
                lanes = f.get("belt") or []
                items = {n for lane in lanes for n, _ in lane}
                if lanes and not items:
                    g["belt_empty"] += 1
                if item in items:
                    g["belt_has_item"] += 1
                else:
                    for lane in lanes:
                        if lane and sum(c for _, c in lane) >= 4:
                            for n, _ in lane:
                                if n not in m["ing"]:          # only items the recipe never uses are a jam; other ingredients are normal
                                    g["belt_other"][n] = g["belt_other"].get(n, 0) + 1
    ranked = sorted(groups.items(), key=lambda kv: -kv[1]["n"])[: a.top]
    items = sorted({item for (_, item), _ in ranked if item != "?"})
    prod = jlua(PRODUCERS % {"surf": surf(a), "items": ",".join(f"['{i}']=1" for i in items)}) if items else {}
    plan = []
    for (recipe, item), g in ranked:
        producers = prod.get(item, {}) if isinstance(prod, dict) else {}
        agg = {}
        for rec, st in producers.items():
            for k, v in st.items():
                agg[k] = agg.get(k, 0) + v
        total = sum(agg.values())
        if g["belt_other"] and not g["belt_empty"]:
            jam = ", ".join(sorted(g["belt_other"], key=lambda n: -g["belt_other"][n])[:3])
            fix = f"SUSPECTED LANE JAM: every feed belt is non-empty but none carries {item}, and some lanes are full of {jam} which this recipe never uses. If such a lane should carry {item}, find where {jam} enters, clear it (remove_item on every line incl. undergrounds) and add a filtered splitter / side-load at the entry."
        elif g["no_feed"] == g["n"]:
            fix = f"no inserter delivers to these machines: place a feeder for {item} (belt tap + inserter) or check the belt side."
        elif total == 0:
            fix = f"nothing in the area makes {item}: build a producer (recipe(s): {', '.join(sorted(producers) or ['see prototypes'])}) and a belt to here."
        elif agg.get("full_output", 0) >= total * 0.6:
            fix = f"{item} is made ({agg}) but not arriving: producers sit full_output, so the transport is broken. Trace the belt from the producer to a consumer at {g['ex']}: look for a missing belt, wrong inserter direction, closed splitter priority/filter, or an underground gap."
        elif agg.get("item_ingredient_shortage", 0) + agg.get("fluid_ingredient_shortage", 0) >= total * 0.5:
            fix = f"producers of {item} are themselves starved ({agg}): fix their missing ingredient first (see the next rows)."
        elif agg.get("no_power", 0) or agg.get("low_power", 0):
            fix = f"producers of {item} lack power: fix the grid first."
        else:
            fix = f"producers of {item} are working ({agg}) but demand is higher: add machines, upgrade to assembling-machine-3, add speed modules (fx.py upgrade --modules speed)."
        plan.append({"recipe": recipe, "missing": item, "machines": g["n"], "example": g["ex"], "producers": agg, "fix": fix})
    ledger = {}
    if a.ledger:
        led = jlua(LEDGER % {"surf": surf(a), "items": ",".join(f"'{i}'" for i in a.ledger)})
        ledger = {k: {"made": round(v[0], 2), "used": round(v[1], 2)} for k, v in led.items()}
    report = {"area": area, "alerts": cen["stat"], "recipe_unset_machines": cen["norecipe"], "starved": plan, "ledger": ledger}
    if a.json:
        print(json.dumps(report, indent=1))
        return
    print(f"== ALERTS in {area}")
    if cen["stat"]:
        for k, v in sorted(cen["stat"].items(), key=lambda kv: -kv[1]):
            print(f"  {v:5d}  {k}")
    else:
        print("  none (no unpowered / unfueled / blocked-by-fluid machines)")
    if cen["norecipe"]:
        print(f"  {cen['norecipe']} assembling machines have NO recipe set")
    print(f"== STARVED MACHINES ({len(plan)} groups, most machines first)")
    for p in plan:
        print(f"  {p['machines']:3d}x {p['recipe']} missing {p['missing']} (e.g. at {p['example']})")
        print(f"        -> {p['fix']}")
    for k, v in ledger.items():
        print(f"  ledger {k}: made {v['made']}/s used {v['used']}/s")


# --------------------------------------------------------------------------------------------- compact
ALLOWED = {"transport-belt", "underground-belt", "splitter", "inserter", "assembling-machine", "furnace", "lab", "container", "logistic-container",
           "electric-pole", "pipe", "pipe-to-ground", "storage-tank", "pump", "mining-drill", "lamp", "power-switch", "arithmetic-combinator",
           "decider-combinator", "constant-combinator", "heat-pipe", "radar", "solar-panel", "accumulator", "boiler", "generator", "reactor",
           "heat-exchanger", "beacon", "roboport", "wall", "gate", "turret", "ammo-turret", "electric-turret", "fluid-turret", "offshore-pump",
           "loader", "loader-1x1", "linked-belt", "lane-splitter", "valve"}

EXPORT = """
local s=%(surf)s local A=%(box)s local o={}
for _,e in pairs(s.find_entities_filtered{area=A,force='player'}) do
  local p=e.prototype local tw,th=p.tile_width or 1,p.tile_height or 1
  if (e.direction==4 or e.direction==12) and e.type~='assembling-machine' and e.type~='furnace' then tw,th=th,tw end
  local left=math.floor(e.position.x-tw/2+0.5) local top=math.floor(e.position.y-th/2+0.5)
  o[#o+1]={e.name,e.type,e.position.x,e.position.y,left,top,left+tw-1,top+th-1,e.direction}
end
rcon.print(helpers.table_to_json(o))
"""

SNAP = """
local s=%(surf)s local A=%(box)s local n={} local nets={} local nop=0 local ins=0 local belts=0
for _,e in pairs(s.find_entities_filtered{area=A,force='player'}) do
  n[e.name]=(n[e.name] or 0)+1
  if e.type=='electric-pole' then nets[e.electric_network_id or 0]=true end
  if e.status==defines.entity_status.no_power then nop=nop+1 end
  if e.type=='inserter' then if e.pickup_target then ins=ins+1 end if e.drop_target then ins=ins+1 end end
  if e.type=='transport-belt' or e.type=='underground-belt' or e.type=='splitter' then local bn=e.belt_neighbours belts=belts+#bn.outputs+#bn.inputs end
end
local nn=0 for _ in pairs(nets) do nn=nn+1 end
rcon.print(helpers.table_to_json({counts=n,pole_networks=nn,no_power=nop,inserter_links=ins,belt_links=belts}))
"""


def cmd_compact(a):
    area = area_of(a)
    ents = jlua(EXPORT % {"surf": surf(a), "box": a_box(area)})
    if not ents:
        print("no player entities in the area")
        return
    bad_types = sorted({e[1] for e in ents if e[1] not in ALLOWED})
    if bad_types:
        raise SystemExit(f"refusing: unsupported entity types in the area: {bad_types} (rails, signals, train stops, vehicles and anything not on the allow-list are not moved)")
    x1, y1, x2, y2 = area
    outside = [e for e in ents if e[4] < x1 or e[5] < y1 or e[6] > x2 or e[7] > y2]
    if outside:
        raise SystemExit(f"refusing: {len(outside)} entities cross the area border (e.g. {outside[0][0]} at {outside[0][2]},{outside[0][3]}); widen or shift the area so blocks are whole")
    fps = [(e[4], e[5], e[6], e[7]) for e in ents]
    pt = [(e[1] == "transport-belt" and e[8] in (4, 12), e[1] == "transport-belt" and e[8] in (0, 8)) for e in ents]
    p = fx_compact.plan(fps, area, keep=a.keep, passthrough=pt)
    if not fx_compact.fits_after(fps, p["xs"], p["ys"], skip=p["destroy"]):
        raise SystemExit("internal error: plan would overlap entities; nothing changed")
    mv = fx_compact.moves([((e[0], e[2], e[3]), e[4], e[5]) for e in ents], p["xs"], p["ys"], skip=p["destroy"])
    saved = 1 - (p["width_after"] * p["height_after"]) / (p["width_before"] * p["height_before"])
    print(f"area {area}: {len(ents)} entities, {p['width_before']}x{p['height_before']} -> {p['width_after']}x{p['height_after']} "
          f"({saved:.0%} smaller), {len(p['xs'])} empty columns and {len(p['ys'])} empty rows removed (gap kept: {a.keep}), {len(mv)} entities move, {len(p['destroy'])} straight belt tiles dropped")
    if not a.apply:
        print("DRY RUN (add --apply). Compaction only deletes fully empty rows/columns, so every belt, pipe and wire keeps its shape.")
        return
    before = jlua(SNAP % {"surf": surf(a), "box": a_box(area)})
    print(tools["save_game"]("before-compact"))
    drop = ";".join(f"{ents[i][0]}|{ents[i][2]}|{ents[i][3]}" for i in p["destroy"])
    if drop:
        lua(f"local s={surf(a)} local n=0 for item in string.gmatch('{drop}','[^;]+') do local f={{}} for v in string.gmatch(item,'[^|]+') do f[#f+1]=v end local e=s.find_entities_filtered{{name=f[1],position={{tonumber(f[2]),tonumber(f[3])}},radius=0.05,force='player'}}[1] if e then e.destroy() n=n+1 end end rcon.print(n)")
    chunk, failed = 300, []
    for i in range(0, len(mv), chunk):
        part = mv[i:i + chunk]
        spec = ";".join(f"{k[0]}|{k[1]}|{k[2]}|{dx}|{dy}" for k, dx, dy in part)
        code = f"""
local s={surf(a)} local list={{}} for item in string.gmatch('{spec}','[^;]+') do local f={{}} for v in string.gmatch(item,'[^|]+') do f[#f+1]=v end list[#list+1]={{f[1],tonumber(f[2]),tonumber(f[3]),tonumber(f[4]),tonumber(f[5])}} end
local pending=list local bad={{}}
for pass=1,6 do local nxt={{}}
  for _,m in pairs(pending) do
    local e=s.find_entities_filtered{{name=m[1],position={{m[2],m[3]}},radius=0.05,force='player'}}[1]
    if e then local np={{m[2]+m[4],m[3]+m[5]}} local ne=nil
      if e.type=='electric-pole' then ne=s.create_entity{{name=e.name,position=np,force=e.force}} else ne=e.clone{{position=np,surface=s,force=e.force}} end
      if ne then e.destroy() else nxt[#nxt+1]=m end end end
  pending=nxt if #pending==0 then break end end
for _,m in pairs(pending) do bad[#bad+1]=m[1]..'@'..m[2]..','..m[3] end
rcon.print(helpers.table_to_json(bad))
"""
        res = lua(code)
        try:
            lst = json.loads(res)
        except json.JSONDecodeError:
            raise SystemExit("compaction stopped, unexpected reply: " + res[:300])
        failed += lst if isinstance(lst, list) else []
    after = jlua(SNAP % {"surf": surf(a), "box": a_box(area)})
    before2 = before
    problems = []
    expect = dict(before2["counts"])
    for i in p["destroy"]:
        expect[ents[i][0]] = expect.get(ents[i][0], 0) - 1
    expect = {k: v for k, v in expect.items() if v}
    if expect != after["counts"]:
        problems.append(f"entity counts differ from expected: {expect} vs {after['counts']}")
    if after["no_power"] > before2["no_power"]:
        problems.append(f"no_power {before2['no_power']} -> {after['no_power']}")
    if after["pole_networks"] > before2["pole_networks"]:
        problems.append(f"pole networks {before2['pole_networks']} -> {after['pole_networks']}")
    if after["inserter_links"] < before2["inserter_links"]:
        problems.append(f"inserter links {before2['inserter_links']} -> {after['inserter_links']}")
    expected_links = before2["belt_links"] - 2 * len(p["destroy"])
    if after["belt_links"] < expected_links:
        problems.append(f"belt links {before2['belt_links']} -> {after['belt_links']} (expected about {expected_links})")
    if failed:
        problems.append(f"{len(failed)} entities could not move: {failed[:5]}")
    print("VERIFY:", "OK, nothing broke" if not problems else "PROBLEMS - reload the 'before-compact' save or fix by hand:")
    for pr in problems:
        print("  ", pr)


# --------------------------------------------------------------------------------------------- mine
RES_LUA = """
local s=%(surf)s local A=%(box)s local o={}
for _,e in pairs(s.find_entities_filtered{area=A,type='resource'}) do
  o[#o+1]={math.floor(e.position.x),math.floor(e.position.y),e.name,e.amount} end
rcon.print(helpers.table_to_json({tiles=o,bonus=game.forces.player.mining_drill_productivity_bonus}))
"""

OUT_DIR = {"S": 8, "N": 0, "E": 4, "W": 12}


def _to_world(out, u, v):
    """Local frame: belts flow toward +v, belt columns spread along u. out = N/E/S/W."""
    return {"S": (u, v), "N": (u, -v), "E": (v, u), "W": (-v, u)}[out]


def _inv(out, x, y):
    return {"S": (x, y), "N": (x, -y), "E": (y, x), "W": (y, -x)}[out]


def _dir_of(out, du, dv):
    x, y = _to_world(out, du, dv)
    return {(0, -1): 0, (1, 0): 4, (0, 1): 8, (-1, 0): 12}[(x, y)]


def _floor(v):
    return int(v // 1)


def cmd_mine(a):
    area = area_of(a)
    data = jlua(RES_LUA % {"surf": surf(a), "box": a_box(area)})
    tiles, foreign = {}, set()
    for x, y, name, amount in data["tiles"]:
        if name == a.resource:
            tiles[(x, y)] = amount
        else:
            foreign.add((x, y))
    if not tiles:
        raise SystemExit(f"no {a.resource} in the area (found: {sorted({t[2] for t in data['tiles']}) or 'nothing'})")
    out = a.out.upper()
    pts = [_inv(out, x + 0.5, y + 0.5) for (x, y) in tiles]
    umin, umax = _floor(min(p[0] for p in pts)) - 4, _floor(max(p[0] for p in pts)) + 4
    vmin, vmax = _floor(min(p[1] for p in pts)) - 4, _floor(max(p[1] for p in pts)) + 4

    def mining_tiles(cu, cv):
        wx, wy = _to_world(out, cu, cv)
        x0, y0 = _floor(wx - 2.5 + 1e-6), _floor(wy - 2.5 + 1e-6)
        return [(x0 + i, y0 + j) for i in range(5) for j in range(5)]

    best = None
    for ou in range(7):
        for ov in range(7):
            drills = []
            u = umin + ((ou - umin) % 7)
            while u <= umax:
                v = vmin + ((ov - vmin) % 7)
                while v <= vmax:
                    for dv in (0, 3):                                    # two drills, then a one-tile gap row (pole)
                        for cu_off, face in ((1.5, 1), (5.5, -1)):
                            cu, cv = u + cu_off, v + dv + 1.5
                            mt = mining_tiles(cu, cv)
                            n_ore = sum(1 for t in mt if t in tiles)
                            if n_ore >= a.min_tiles and (a.allow_mixed or not any(t in foreign for t in mt)):
                                drills.append((cu, cv, face, sum(tiles.get(t, 0) for t in mt), u))
                    v += 7
                u += 7
            score = sum(d[3] for d in drills)
            if best is None or score > best[0]:
                best = (score, drills)
    drills = best[1]
    if not drills:
        raise SystemExit("no drill position fits (lower --min-tiles, or use --allow-mixed)")
    cols = {}
    for cu, cv, face, ore, col in drills:
        cols.setdefault(col, []).append(cv)
    ents = []
    for cu, cv, face, ore, col in drills:
        wx, wy = _to_world(out, cu, cv)
        ents.append({"name": a.drill, "x": wx, "y": wy, "direction": _dir_of(out, face, 0)})
    v_end = max(max(v) for v in cols.values()) + 1.5            # local v where the last drill ends
    for col, vs in cols.items():
        v0, v1 = min(vs) - 1.5, max(vs) + 1.5
        v = v0
        while v < v_end + 2:
            wx, wy = _to_world(out, col + 3.5, v + 0.5)
            ents.append({"name": a.belt, "x": wx, "y": wy, "direction": OUT_DIR[out]})
            v += 1
        wx, wy = _to_world(out, col + 2.5, v0 - 0.5)                     # a pole above the first drill pair (the gap rows only reach the pair below)
        ents.append({"name": a.pole, "x": wx, "y": wy})
        pv = v0 + 6
        while pv <= v1:
            wx, wy = _to_world(out, col + 2.5, pv + 0.5)
            ents.append({"name": a.pole, "x": wx, "y": wy})
            pv += 7
    ucols = sorted(cols)
    cv = v_end + 2 + 0.5                                         # collector row (local v)
    last = ucols[-1] + 3.5 + 2
    flow = {"S": 4, "N": 4, "E": 8, "W": 8}[out]                  # +u in world terms
    u = ucols[0] + 3.5
    while u < last:
        wx, wy = _to_world(out, u, cv)
        ents.append({"name": a.belt, "x": wx, "y": wy, "direction": flow})
        u += 1
    for k in range(0, 4):                                         # corner turns toward the output, then 3 belts leave
        wx, wy = _to_world(out, last, cv + k)
        ents.append({"name": a.belt, "x": wx, "y": wy, "direction": OUT_DIR[out]})
    if getattr(a, "plan_only", False):
        return ents, {"out": out, "last": last, "cv": cv, "bonus": data["bonus"]}
    dropped, other = 0, []
    for _ in range(3):
        res = json.loads(tools["place_entities"](json.dumps(ents), dry_run=True))
        fails = res.get("failed") or []
        bad = {f["i"] for f in fails if ents[f["i"]]["name"] == a.drill}
        other = [f for f in fails if ents[f["i"]]["name"] != a.drill]
        if not bad:
            break
        ents = [e for i, e in enumerate(ents) if i not in bad]
        dropped += len(bad)
    n_dr = sum(1 for e in ents if e["name"] == a.drill)
    rate = n_dr * 0.5 * (1 + data["bonus"])
    ox, oy = _to_world(out, last, cv + 3)
    print(f"layout: {n_dr} {a.drill}s on {a.resource} in {len(cols)} belt column(s), {sum(1 for e in ents if e['name'] == a.belt)} belts, "
          f"{sum(1 for e in ents if e['name'] == a.pole)} poles; about {rate:.1f} ore/s (mining productivity +{data['bonus']:.0%}); {dropped} drill spots dropped (blocked ground)")
    print(f"output: the belt ends at ({_floor(ox)},{_floor(oy)}) flowing {out}; connect your belt there. The pole chain is NOT joined to the power grid: link it.")
    if other:
        print(f"  blocked non-drill pieces: {len(other)} (e.g. {other[0]['name']} at {other[0]['x']},{other[0]['y']}: {other[0]['why']})")
    if not a.apply:
        print("DRY RUN (add --apply to build)")
        return
    from bridge.factorio.planner import batches
    print(tools["save_game"]("before-mine"))
    for part in batches(ents):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        print("placed", r.get("placed"), "failed", len(r.get("failed") or []))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p, area_required=True):
        p.add_argument("--area", nargs=4, metavar=("X1", "Y1", "X2", "Y2"))
        p.add_argument("--around", nargs=3, type=float, metavar=("X", "Y", "R"))
        p.add_argument("--surface", default="nauvis")
        p.add_argument("--apply", action="store_true")

    p = sub.add_parser("clear"); common(p)
    for f in ("trees", "rocks", "cliffs", "biters", "decoratives", "fish", "items", "corpses", "all", "planner"):
        p.add_argument("--" + f, action="store_true")
    p.set_defaults(fn=cmd_clear)
    p = sub.add_parser("upgrade"); common(p)
    for f in ("belts", "inserters", "chests", "machines", "poles", "furnaces", "bulk", "all", "planner", "storage"):
        p.add_argument("--" + f, action="store_true")
    p.add_argument("--module-name", help="exact module item, e.g. speed-module-2")
    p.add_argument("--spawn", action="store_true", help="modules appear from nowhere (Captain's order); without it they are taken from --from-chest / --from-hub")
    p.add_argument("--budget-mw", type=float, help="stop filling when the estimated extra power demand would exceed this")
    p.add_argument("--modules", choices=["speed", "productivity", "efficiency"])
    p.add_argument("--from-chest", nargs=2, type=float, metavar=("X", "Y"))
    p.add_argument("--from-hub", action="store_true")
    p.set_defaults(fn=cmd_upgrade)
    p = sub.add_parser("bottlenecks"); common(p)
    p.add_argument("--json", action="store_true")
    p.add_argument("--top", type=int, default=12)
    p.add_argument("--ledger", nargs="*", help="items for a made/used table, e.g. iron-plate copper-plate")
    p.set_defaults(fn=cmd_bottlenecks)
    p = sub.add_parser("compact"); common(p)
    p.add_argument("--keep", type=int, default=1, help="empty tiles to keep in every gap (default 1)")
    p.set_defaults(fn=cmd_compact)
    p = sub.add_parser("mine"); common(p)
    p.add_argument("--resource", required=True, help="iron-ore, copper-ore, coal, stone, uranium-ore ...")
    p.add_argument("--out", default="S", choices=["N", "E", "S", "W", "n", "e", "s", "w"], help="direction the output belt leaves in")
    p.add_argument("--drill", default="electric-mining-drill")
    p.add_argument("--belt", default="transport-belt")
    p.add_argument("--pole", default="medium-electric-pole")
    p.add_argument("--min-tiles", type=int, default=6, help="ore tiles a drill's 5x5 area must cover (default 6)")
    p.add_argument("--allow-mixed", action="store_true", help="let drills sit where another ore is in reach")
    p.set_defaults(fn=cmd_mine)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
