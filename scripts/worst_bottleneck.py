#!/usr/bin/env python3
"""Ranks the bottlenecks across every surface and prints the worst ones. Read-only: it finds, it does not fix.

Scores (higher = worse), each finding is one line:
  starved    machines idle for lack of an ingredient, grouped by surface, recipe and missing ingredient (score = machine count)
  backed     machines with full output, grouped the same way (score = machine count / 2; often a symptom of a starved consumer)
  short      an item used faster than it is made, from the one-minute production ledger on Nauvis (score = deficit per second x 20)
  nopower    machines with no power (score = count x 3)
  robots     a surface with roboports but no logistic robots (score = 500; nothing moves there)
  labs       labs missing science packs (score = count)
  alert      a game alert from the in-game alert overview (score = 25 per instance; the Captain's rule: read alerts first)

Usage: scripts/worst_bottleneck.py [top_n]   (default 5)"""
import sys

from _game import tools

TOP = int(sys.argv[1]) if len(sys.argv) > 1 else 5

MACHINES = r'''
local E = defines.entity_status
local SN = {}
for k, v in pairs(E) do SN[v] = k end
local agg = {}
for _, s in pairs(game.surfaces) do
  for _, e in pairs(s.find_entities_filtered{type = {'assembling-machine', 'furnace', 'chemical-plant', 'oil-refinery', 'lab', 'rocket-silo', 'recycler'}}) do
    local st = SN[e.status] or tostring(e.status)
    local rn = e.type
    if e.type ~= 'lab' and e.type ~= 'rocket-silo' and e.type ~= 'recycler' then
      local ok, r = pcall(function() if e.type == 'furnace' then return e.previous_recipe end return e.get_recipe() end)
      if ok and r then
        local nm = r.name
        if type(nm) == 'string' then rn = nm elseif type(nm) == 'userdata' and nm.name then rn = nm.name end
      end
    end
    local miss = ''
    if st == 'item_ingredient_shortage' or st == 'fluid_ingredient_shortage' then
      local inv = e.get_inventory(defines.inventory.crafter_input) or e.get_inventory(defines.inventory.furnace_source)
      local r = e.type == 'assembling-machine' and e.get_recipe() or nil
      if r then
        local ms = {}
        for _, ing in pairs(r.ingredients) do
          if ing.type == 'item' then
            if (inv and inv.get_item_count(ing.name) or 0) < ing.amount then ms[#ms + 1] = ing.name end
          elseif e.get_fluid_count(ing.name) < ing.amount then ms[#ms + 1] = ing.name .. '(fluid)' end
        end
        miss = table.concat(ms, '+')
      end
    end
    if e.type == 'lab' and st == 'missing_science_packs' then miss = 'packs' end
    local key = s.name .. '|' .. e.type .. '|' .. rn .. '|' .. st .. '|' .. miss
    agg[key] = (agg[key] or 0) + 1
    if st == 'no_power' then
      local pk = 'POWER|' .. s.name
      agg[pk] = (agg[pk] or 0) + 1
    end
  end
  local rp = #s.find_entities_filtered{name = 'roboport'}
  if rp > 0 then
    local bots = #s.find_entities_filtered{name = 'logistic-robot'}
    agg['ROBOTS|' .. s.name .. '|' .. rp .. '|' .. bots] = 1
  end
end
local o = {}
for k, v in pairs(agg) do o[#o + 1] = v .. '#' .. k end
rcon.print(table.concat(o, ';'))
'''

LEDGER = """local s=game.surfaces.nauvis local ps=game.forces.player.get_item_production_statistics(s) local o={} for _,n in pairs({%s}) do
local m=ps.get_flow_count{name=n,category='input',precision_index=defines.flow_precision_index.one_minute}/60
local u=ps.get_flow_count{name=n,category='output',precision_index=defines.flow_precision_index.one_minute}/60
o[#o+1]=string.format('%%s|%%.2f|%%.2f',n,m,u) end rcon.print(table.concat(o,';'))""" % ",".join(
    f"'{i}'" for i in ("iron-plate copper-plate steel-plate stone-brick plastic-bar sulfur copper-cable electronic-circuit advanced-circuit "
                        "processing-unit battery low-density-structure electric-engine-unit flying-robot-frame logistic-science-pack "
                        "military-science-pack chemical-science-pack production-science-pack utility-science-pack space-science-pack rocket-part").split())


def alert_findings():
    """Game alerts (the in-game alert overview) as findings: each alert type scored by how many instances, with the first place it is at."""
    import json
    out = []
    try:
        data = json.loads(tools["factory_problems"]())
    except Exception:
        return out
    alerts = data.get("alerts") or []
    # Current build returns a list of {type, count, at, what}; older builds returned a dict keyed by type.
    if isinstance(alerts, dict):
        alerts = [dict(val, type=kind) if isinstance(val, dict) else {"type": kind, "count": len(val) if isinstance(val, (list, dict)) else 1}
                  for kind, val in alerts.items()]
    for entry in alerts:
        if not isinstance(entry, dict):
            continue
        kind = entry.get("type", "unknown")
        count = int(entry.get("count", 0) or 0)
        at = entry.get("at") or []
        where = ""
        if at:
            first = at[0]
            where = f" first at ({first.get('x')}, {first.get('y')})" if isinstance(first, dict) else f" first {first}"
        what = entry.get("what")
        detail = f" [{', '.join(f'{k} {v}' for k, v in what.items())}]" if isinstance(what, dict) and what else ""
        out.append((count * 25, "alert", f"{kind}: {count} instance(s){where}{detail}"))
    return out


def findings():
    out = alert_findings()
    raw = tools["run_lua"](MACHINES)
    for part in raw.split(";"):
        if not part:
            continue
        try:
            cnt, rest = part.split("#", 1)
            cnt = int(cnt)
        except ValueError:
            continue
        f = rest.split("|")
        if f[0] == "POWER":
            out.append((cnt * 3, "nopower", f"{f[1]}: {cnt} machines with no power"))
        elif f[0] == "ROBOTS":
            _, surf, ports, bots = f
            if int(bots) == 0:
                out.append((500, "robots", f"{surf}: {ports} roboports, 0 logistic robots, nothing moves here"))
        elif len(f) == 5:
            surf, etype, recipe, st, miss = f
            if etype == "lab":
                out.append((cnt, "labs", f"{surf}: {cnt} labs missing packs"))
            elif st in ("item_ingredient_shortage", "fluid_ingredient_shortage", "no_ingredients"):
                what = f" missing {miss}" if miss else ""
                out.append((cnt, "starved", f"{surf}: {cnt}x {recipe} ({etype}) {st}{what}"))
            elif st == "full_output":
                out.append((cnt / 2, "backed", f"{surf}: {cnt}x {recipe} ({etype}) full output"))
    for part in tools["run_lua"](LEDGER).split(";"):
        if not part:
            continue
        name, made, used = part.split("|")
        made, used = float(made), float(used)
        if used > made * 1.05 and used > 0.05:
            out.append(((used - made) * 20, "short", f"nauvis: {name} made {made:.2f}/s, used {used:.2f}/s"))
    return out


def main():
    rows = sorted(findings(), key=lambda r: -r[0])
    print(f"worst {min(TOP, len(rows))} of {len(rows)} findings (score, kind, detail)")
    for score, kind, detail in rows[:TOP]:
        print(f"  {score:9.1f}  {kind:8s}  {detail}")


if __name__ == "__main__":
    main()
