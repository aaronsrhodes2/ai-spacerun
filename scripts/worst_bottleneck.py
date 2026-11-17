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
  full       storage with no room left (2026-11-16, the Captain: a full Aquilo pad blocked every delivery and no finding said so):
             a cargo landing pad (0 free slots = 400, under 10% free = 150, under 20% = 40), a platform hub (0 free = 120, under 10% = 50),
             a surface's storage chests as a whole (0 free = 300, under 10% = 120, else 1 per full chest: robots have nowhere to put things),
             full provider chests (count / 2: an output that is not being collected) and full storage tanks (count x 0.3; often by design)
Two honesty rules (2026-11-14): a `short` finding is scaled down by its RUNWAY (network stock / deficit): a deficit that a big stockpile covers for
hours is not urgent (iron plate: 577k in stock); and a machine whose feed inserters are disabled by a circuit is GATED (idle on purpose), not starved; a starved machine whose product has 20,000+ in stock is skipped (surplus, 2026-11-14: 103k foundations).

Usage: scripts/worst_bottleneck.py [top_n] [--science]   (default 5; --science keeps science-pack and lab findings and prints a pack table)"""
import sys

from _game import tools

SCIENCE = "--science" in sys.argv        # only findings about science packs and labs, plus a made/used table for every pack
_nums = [a for a in sys.argv[1:] if a.isdigit()]
TOP = int(_nums[0]) if _nums else 5

MACHINES = r'''
local E = defines.entity_status
local SN = {}
for k, v in pairs(E) do SN[v] = k end
local agg = {}
for _, s in pairs(game.surfaces) do
  for _, e in pairs(s.find_entities_filtered{type = {'assembling-machine', 'furnace', 'chemical-plant', 'oil-refinery', 'lab', 'rocket-silo', 'recycler'}}) do
    local st = SN[e.status] or tostring(e.status)
    if (st == 'no_ingredients' or st == 'item_ingredient_shortage') and e.type ~= 'lab' then
      for _, i in pairs(s.find_entities_filtered{type = 'inserter', position = e.position, radius = 4}) do
        if i.drop_target == e and i.status == defines.entity_status.disabled_by_control_behavior then st = 'gated' break end
      end
    end
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
    local nets = {}
    for _, p in pairs(s.find_entities_filtered{name = 'roboport'}) do
      local inv = p.get_inventory(defines.inventory.roboport_robot)
      if inv then bots = bots + inv.get_item_count('logistic-robot') end
      local n = p.logistic_network
      if n and not nets[n.network_id] then
        nets[n.network_id] = true
        bots = bots + n.all_logistic_robots
      end
    end
    agg['ROBOTS|' .. s.name .. '|' .. rp .. '|' .. bots] = 1
  end
end
local o = {}
for k, v in pairs(agg) do o[#o + 1] = v .. '#' .. k end
rcon.print(table.concat(o, ';'))
'''

STORAGE = ("local o={} local f=game.forces.player for _,s in pairs(game.surfaces) do "
           "for _,p in pairs(s.find_entities_filtered{type='cargo-landing-pad',force=f}) do local i=p.get_inventory(defines.inventory.cargo_landing_pad_main) o[#o+1]='PAD|'..s.name..'|'..#i..'|'..i.count_empty_stacks() end "
           "local n,full,slots,free=0,0,0,0 local prv={} for _,c in pairs(s.find_entities_filtered{type='logistic-container',force=f}) do local i=c.get_inventory(defines.inventory.chest) local e=i.count_empty_stacks() "
           "if c.name=='storage-chest' then n=n+1 slots=slots+#i free=free+e if e==0 then full=full+1 end elseif c.name=='passive-provider-chest' or c.name=='active-provider-chest' then local t=prv[c.name] or {0,0} t[2]=t[2]+1 if e==0 then t[1]=t[1]+1 end prv[c.name]=t end end "
           "if n>0 then o[#o+1]='STO|'..s.name..'|'..n..'|'..full..'|'..slots..'|'..free end for k,t in pairs(prv) do if t[1]>0 then o[#o+1]='PRV|'..s.name..'|'..k..'|'..t[1]..'|'..t[2] end end "
           "local tk={} for _,t in pairs(s.find_entities_filtered{type='storage-tank',force=f}) do local fl,amt=next(t.get_fluid_contents()) if fl then local cap=t.prototype.fluid_capacity*(1+0.3*t.quality.level) local x=tk[fl] or {0,0} x[2]=x[2]+1 if amt>=cap*0.99 then x[1]=x[1]+1 end tk[fl]=x end end "
           "for k,t in pairs(tk) do if t[1]>0 then o[#o+1]='TNK|'..s.name..'|'..k..'|'..t[1]..'|'..t[2] end end end "
           "for _,p in pairs(f.platforms) do if p.valid and p.hub then local i=p.hub.get_inventory(defines.inventory.hub_main) o[#o+1]='HUB|'..p.name:gsub('%[.-%]%s*','')..'|'..#i..'|'..i.count_empty_stacks() end end rcon.print(table.concat(o,';'))")


def storage_findings():
    """Full storage: landing pads, platform hubs, a surface's storage chests, full provider chests, full tanks (see the docstring for the scores)."""
    out = []
    try:
        raw = tools["run_lua"](STORAGE)
    except Exception:
        return out
    for part in raw.split(";"):
        f = part.split("|")
        try:
            if f[0] in ("PAD", "HUB"):
                slots, free = int(f[2]), int(f[3])
                frac = free / slots if slots else 1.0
                tiers = ((400, 150, 40) if f[0] == "PAD" else (120, 50, 0))
                score = tiers[0] if free == 0 else tiers[1] if frac < 0.1 else tiers[2] if frac < 0.2 else 0
                if score:
                    what = "landing pad" if f[0] == "PAD" else "hub"
                    out.append((score, "full", f"{f[1]}: {what} {free} of {slots} slots free" + (": nothing can be delivered" if free == 0 and f[0] == "PAD" else "")))
            elif f[0] == "STO":
                n, full, slots, free = int(f[2]), int(f[3]), int(f[4]), int(f[5])
                frac = free / slots if slots else 1.0
                score = 300 if free == 0 else 120 if frac < 0.1 else full
                if score:
                    out.append((score, "full", f"{f[1]}: storage chests {full} of {n} full, {free} of {slots} slots free ({100 * frac:.0f}%)"))
            elif f[0] == "PRV":
                out.append((int(f[3]) / 2, "full", f"{f[1]}: {f[3]} of {f[4]} {f[2]}s full (output not collected)"))
            elif f[0] == "TNK" and not f[1].startswith("platform-"):      # a ship keeps its fuel tanks full on purpose
                out.append((int(f[3]) * 0.3, "full", f"{f[1]}: {f[3]} of {f[4]} tanks of {f[2]} full"))
        except (ValueError, IndexError):
            continue
    return out


LEDGER = """local s=game.surfaces.nauvis local rp=s.find_entities_filtered{name='roboport',position={-352,-229},radius=0.6}[1] local net=rp and rp.logistic_network local ps=game.forces.player.get_item_production_statistics(s) local o={} for _,n in pairs({%s}) do
local m=ps.get_flow_count{name=n,category='input',precision_index=defines.flow_precision_index.one_minute}/60
local u=ps.get_flow_count{name=n,category='output',precision_index=defines.flow_precision_index.one_minute}/60
o[#o+1]=string.format('%%s|%%.2f|%%.2f|%%d',n,m,u,net and net.get_item_count(n) or 0) end rcon.print(table.concat(o,';'))""" % ",".join(
    f"'{i}'" for i in ("iron-plate copper-plate steel-plate stone-brick plastic-bar sulfur copper-cable electronic-circuit advanced-circuit "
                        "electromagnetic-science-pack processing-unit battery low-density-structure electric-engine-unit flying-robot-frame logistic-science-pack "
                        "military-science-pack chemical-science-pack production-science-pack utility-science-pack space-science-pack rocket-part space-platform-foundation").split())


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
    out = alert_findings() + storage_findings()
    ledger = tools["run_lua"](LEDGER)
    stocks = {}
    for part in ledger.split(";"):
        fl = part.split("|")
        if len(fl) > 3:
            try:
                stocks[fl[0]] = int(fl[3])
            except ValueError:
                pass
    try:                       # the scrap gate reads the FULGORA network, not Nauvis's
        stocks["fulgora-em"] = int(tools["run_lua"]("local s=game.surfaces.fulgora local rc=s.find_entities_filtered{name='requester-chest',position={125.5,-110.5},radius=3}[1] "
                                                   "rcon.print(rc and rc.logistic_network and rc.logistic_network.get_item_count('electromagnetic-science-pack') or 0)").strip())
    except Exception:
        stocks["fulgora-em"] = 0
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
            if surf.startswith("platform-") and etype == "furnace":
                continue        # platform furnaces idle by design while the ship waits; hubs hold 30k+ ore (checked 2026-11-14)
            if recipe.endswith("-recycling") and st == "no_ingredients":
                # Fulgora scrap is gated by backpressure (SKILL.md, "turn the miners off when nothing is needed"): the unload inserters run only while electromagnetic packs < 6,000.
                # Trash-yard recyclers idle when there is no surplus to recycle. Both are idle on purpose; only scrap-recycling below the gate is a real finding.
                if not (recipe == "scrap-recycling" and stocks.get("fulgora-em", 0) < 6000):
                    continue
            if etype == "lab":
                out.append((cnt, "labs", f"{surf}: {cnt} labs missing packs"))
            elif st in ("item_ingredient_shortage", "fluid_ingredient_shortage", "no_ingredients"):
                if surf == "nauvis" and stocks.get(recipe, 0) >= 20000:
                    continue                                           # product is in surplus: idle on purpose (void-surplus doctrine)
                what = f" missing {miss}" if miss else ""
                out.append((cnt, "starved", f"{surf}: {cnt}x {recipe} ({etype}) {st}{what}"))
            elif st == "full_output":
                out.append((cnt / 2, "backed", f"{surf}: {cnt}x {recipe} ({etype}) full output"))
    for part in ledger.split(";"):
        if not part:
            continue
        fields = part.split("|")
        name, made, used = fields[0], float(fields[1]), float(fields[2])
        stock = int(fields[3]) if len(fields) > 3 else 0
        if used > made * 1.05 and used > 0.05:
            deficit = used - made
            runway = stock / deficit if stock > 0 else 0.0           # seconds the stock would last at this deficit
            factor = 1.0 if runway < 600 else max(0.05, 600.0 / runway)
            note = f", stock {stock}, lasts {runway / 3600:.1f} h" if stock > 0 else ", stock 0"
            out.append((deficit * 20 * factor, "short", f"nauvis: {name} made {made:.2f}/s, used {used:.2f}/s{note}"))
    return out


PACKS = ["automation", "logistic", "military", "chemical", "production", "utility", "space", "metallurgic", "electromagnetic", "agricultural", "cryogenic", "promethium"]


def pack_table():
    names = ",".join("'%s-science-pack'" % p for p in PACKS)
    code = ("local o={} for _,n in pairs({%s}) do local m,u=0,0 for _,s in pairs(game.surfaces) do local ps=game.forces.player.get_item_production_statistics(s) "
            "m=m+ps.get_flow_count{name=n,category='input',precision_index=defines.flow_precision_index.one_minute}/60 "
            "u=u+ps.get_flow_count{name=n,category='output',precision_index=defines.flow_precision_index.one_minute}/60 end o[#o+1]=string.format('%%s|%%.2f|%%.2f',n,m,u) end rcon.print(table.concat(o,';'))") % names
    print("science packs, all surfaces (one minute, per second): made / used")
    for part in tools["run_lua"](code).split(";"):
        n, m, u = part.split("|")
        print(f"  {n.replace('-science-pack', ''):16s} made {float(m):6.2f}  used {float(u):6.2f}")


def main():
    rows = sorted(findings(), key=lambda r: -r[0])
    if SCIENCE:
        pack_table()
        rows = [r for r in rows if "science" in r[2] or r[1] == "labs"]
    print(f"worst {min(TOP, len(rows))} of {len(rows)} findings (score, kind, detail)")
    for score, kind, detail in rows[:TOP]:
        print(f"  {score:9.1f}  {kind:8s}  {detail}")


if __name__ == "__main__":
    main()
