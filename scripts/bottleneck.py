"""
Read-only bottleneck finder (plan: docs/bottleneck-plan.md, parts A and B).
A: made vs used per item (1 min). B: machines by status, and for every starved machine the exact missing ingredient.
Usage: scripts/bottleneck.py [x1 y1 x2 y2]
"""
import sys

from _game import tools

AREA = [int(a) for a in sys.argv[1:5]] if len(sys.argv) >= 5 else [-400, -450, 300, 50]
ITEMS = ("iron-plate copper-plate steel-plate stone-brick plastic-bar sulfur copper-cable electronic-circuit advanced-circuit processing-unit "
         "battery low-density-structure electric-engine-unit flying-robot-frame automation-science-pack logistic-science-pack "
         "military-science-pack chemical-science-pack production-science-pack utility-science-pack space-science-pack rocket-part rocket-fuel").split()

LEDGER = """local s=game.surfaces.nauvis local ps=game.forces.player.get_item_production_statistics(s) local o={} for _,n in pairs({%s}) do
local m=ps.get_flow_count{name=n,category='input',precision_index=defines.flow_precision_index.one_minute}/60
local u=ps.get_flow_count{name=n,category='output',precision_index=defines.flow_precision_index.one_minute}/60
o[#o+1]=string.format('%%s|%%.2f|%%.2f',n,m,u) end rcon.print(table.concat(o,';'))""" % ",".join(f"'{i}'" for i in ITEMS)

CENSUS = """local s=game.surfaces.nauvis local agg={} local E=defines.entity_status local SN={} for k,v in pairs(E) do SN[v]=k end
for _,e in pairs(s.find_entities_filtered{force='player',type={'assembling-machine','furnace','chemical-plant','oil-refinery','lab'},area={{%d,%d},{%d,%d}}}) do
 local st=e.status local r=(e.type~='lab') and e.get_recipe() or nil local name=r and r.name or e.type
 if e.type=='furnace' and not r then local fr=e.previous_recipe name=fr and fr.name.name or 'furnace' end
 local key=name..'|'..tostring(SN[st])
 local miss=''
 if r and (st==E.item_ingredient_shortage or st==E.fluid_ingredient_shortage) then
  local inv=e.get_inventory(defines.inventory.crafter_input) or e.get_inventory(defines.inventory.furnace_source)
  local ms={} for _,ing in pairs(r.ingredients) do if ing.type=='item' then local have=inv and inv.get_item_count(ing.name) or 0 if have<ing.amount then ms[#ms+1]=ing.name end else if e.get_fluid_count(ing.name)<ing.amount then ms[#ms+1]=ing.name..'(fluid)' end end end
  miss=table.concat(ms,'+') end
 key=key..'|'..miss agg[key]=(agg[key] or 0)+1 end
local o={} for k,v in pairs(agg) do o[#o+1]=v..'|'..k end rcon.print(table.concat(o,';'))"""


def main():
    print("== A. made vs used per second (1 min)")
    rows = []
    for part in tools["run_lua"](LEDGER).split(";"):
        n, m, u = part.split("|")
        rows.append((n, float(m), float(u)))
    for n, m, u in rows:
        flag = "  <-- short" if u > m * 1.05 and u > 0.05 else ("  surplus" if m > 2 * u + 0.2 else "")
        print(f"  {n:28s} made {m:6.2f}  used {u:6.2f}{flag}")
    print("== B. machines by recipe and status (non-working only), with the missing ingredient")
    by = {}
    for part in tools["run_lua"](CENSUS % tuple(AREA)).split(";"):
        cnt, name, st, miss = part.split("|")
        by.setdefault(name, []).append((int(cnt), st, miss))
    for name in sorted(by):
        total = sum(c for c, _, _ in by[name])
        bad = [(c, st, miss) for c, st, miss in by[name] if st not in ("working", "normal", "waiting_for_source_items", "waiting_for_space_in_destination")]
        if bad:
            print(f"  {name} ({total} machines): " + "; ".join(f"{c}x {st}" + (f" missing {miss}" if miss else "") for c, st, miss in bad))


if __name__ == "__main__":
    main()
