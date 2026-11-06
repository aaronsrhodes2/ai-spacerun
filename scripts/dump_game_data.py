"""
Dump every game component from the live server into the skill's reference folder.

The game itself is the source, so numbers match the exact version and mods in play.
Re-run after a game or mod update:  .venv/Scripts/python.exe scripts/dump_game_data.py

Writes .claude/skills/factorio/reference/:
  recipes, items, entities, technologies, fluids, resources, planets  (.json, raw data)
  science-packs.md  how each pack is made, from raw materials up, and what it unlocks
  items-that-spoil.md, planet-only-recipes.md, machines.md  digests for planning
"""

import json
from pathlib import Path

from _game import tools

OUT = Path(__file__).resolve().parent.parent / ".claude" / "skills" / "factorio" / "reference"
PAGE = 120

PRELUDE = """
local function get(p, k) local ok, v = pcall(function() return p[k] end) if ok then return v end return nil end
local function call(p, k) local ok, v = pcall(function() return p[k]() end) if ok then return v end return nil end
local function names(t) local o = {} for n, _ in pairs(t) do o[#o+1] = n end table.sort(o) return o end
"""

SOURCES = {
    "recipes": ("prototypes.recipe", """
        local f = game.forces.player
        local function row(p) return {
          name=p.name, category=(get(p,'category') or (get(p,'categories') or {})[1]), categories=get(p,'categories'), seconds=get(p,'energy'), hidden=get(p,'hidden'), subgroup=get(p,'subgroup') and get(p,'subgroup').name,
          ingredients=get(p,'ingredients'), products=get(p,'products'),
          surface_conditions=get(p,'surface_conditions'), allow_productivity=get(p,'allow_productivity'),
          enabled_now=f.recipes[p.name] and f.recipes[p.name].enabled or false } end
    """),
    "items": ("prototypes.item", """
        local function row(p)
          local spoil = get(p,'spoil_result')
          local place = get(p,'place_result')
          return {
          name=p.name, type=get(p,'type'), subgroup=get(p,'subgroup') and get(p,'subgroup').name, stack_size=get(p,'stack_size'), hidden=get(p,'hidden'),
          weight=get(p,'weight'), fuel_MJ=(get(p,'fuel_value') or 0)/1000000, fuel_category=get(p,'fuel_category'),
          spoil_ticks=call(p,'get_spoil_ticks') or get(p,'spoil_ticks'), spoil_result=spoil and spoil.name,
          places=place and place.name } end
    """),
    "entities": ("prototypes.entity", """
        local function row(p)
          local items = get(p,'items_to_place_this')
          if not items or #items == 0 then return nil end
          local placed_by = {}
          for _, i in pairs(items) do placed_by[#placed_by+1] = i.name end
          return {
          name=p.name, type=get(p,'type'), placed_by=placed_by,
          crafting_speed=call(p,'get_crafting_speed'), crafting_categories=get(p,'crafting_categories'),
          mining_speed=get(p,'mining_speed'), resource_categories=get(p,'resource_categories'),
          belt_items_per_s=get(p,'belt_speed') and get(p,'belt_speed')*60*8,
          energy_kW=get(p,'energy_usage') and get(p,'energy_usage')*60/1000,
          max_kW=get(p,'max_energy_usage') and get(p,'max_energy_usage')*60/1000,
          produces_kW=get(p,'max_energy_production') and get(p,'max_energy_production')*60/1000,
          inserter_rotation=get(p,'inserter_rotation_speed'), module_slots=get(p,'module_inventory_size'),
          lab_inputs=get(p,'lab_inputs'), surface_conditions=get(p,'surface_conditions'),
          tile_width=get(p,'tile_width'), tile_height=get(p,'tile_height'), supply_radius=get(p,'supply_area_distance') } end
    """),
    "technologies": ("prototypes.technology", """
        local f = game.forces.player
        local function row(p)
          local effects = {}
          for _, e in pairs(get(p,'effects') or {}) do effects[#effects+1] = e.recipe and ('recipe:'..e.recipe) or e.type end
          return {
          name=p.name, prerequisites=names(get(p,'prerequisites') or {}), units=get(p,'research_unit_count'),
          unit_seconds=get(p,'research_unit_energy') and get(p,'research_unit_energy')/60, packs=get(p,'research_unit_ingredients'),
          trigger=get(p,'research_trigger'), effects=effects, essential=get(p,'essential'), hidden=get(p,'hidden'),
          researched_now=f.technologies[p.name] and f.technologies[p.name].researched or false } end
    """),
    "fluids": ("prototypes.fluid", """
        local function row(p) return {name=p.name, default_temperature=get(p,'default_temperature'), max_temperature=get(p,'max_temperature'),
          fuel_MJ=(get(p,'fuel_value') or 0)/1000000, hidden=get(p,'hidden')} end
    """),
    "resources": ("prototypes.get_entity_filtered{{filter='type', type='resource'}}", """
        local function row(p) local m = get(p,'mineable_properties') return {name=p.name, category=get(p,'resource_category'),
          mining_seconds=m and m.mining_time, products=m and m.products, needs_fluid=m and m.required_fluid,
          fluid_amount=m and m.fluid_amount, infinite=get(p,'infinite_resource')} end
    """),
    "planets": ("prototypes.space_location", """
        local function row(p) return {name=p.name, type=get(p,'type'), surface_properties=get(p,'surface_properties'),
          distance=get(p,'distance'), solar_power=get(p,'solar_power_in_space'), hidden=get(p,'hidden')} end
    """),
    "space_connections": ("prototypes.space_connection", """
        local function row(p) return {name=p.name, from=get(p,'from') and get(p,'from').name, to=get(p,'to') and get(p,'to').name, length=get(p,'length')} end
    """),
}


def fetch(kind):
    source, row_lua = SOURCES[kind]
    rows, start = [], 1
    while True:
        lua = PRELUDE + row_lua + f"""
            local src = {source}
            local list = names(src)
            local out = {{}}
            for i = {start}, math.min({start + PAGE - 1}, #list) do
              local r = row(src[list[i]])
              if r then out[#out+1] = r end
            end
            rcon.print(helpers.table_to_json({{total=#list, rows=out}}))
        """
        reply = tools["run_lua"](" ".join(line.strip() for line in lua.splitlines() if line.strip()))
        try:
            page = json.loads(reply)
        except ValueError:
            raise SystemExit(f"{kind} page at {start}: {reply[:400]}")
        got = page.get("rows") or []
        rows.extend(got if isinstance(got, list) else [])
        start += PAGE
        if start > page["total"]:
            return rows


def aslist(v):
    return v if isinstance(v, list) else (list(v.values()) if isinstance(v, dict) else [])


def conditions_text(rec):
    parts = []
    for c in aslist(rec.get("surface_conditions")):
        low, high = c.get("min"), c.get("max")
        parts.append(f"{c.get('property')} {low if low is not None else ''}..{high if high is not None else ''}")
    return "; ".join(parts)


class Trees:
    def __init__(self, recipes, resources):
        self.by_product = {}
        for r in recipes:
            if r.get("hidden") or r["name"].endswith("-recycling") or r.get("category") == "recycling":
                continue
            for p in aslist(r.get("products")):
                self.by_product.setdefault(p["name"], []).append(r)
        self.raw = {p["name"] for res in resources for p in aslist(res.get("products"))}

    def recipe_for(self, item):
        options = self.by_product.get(item, [])
        for r in options:
            if r["name"] == item:
                return r, options
        return (options[0] if options else None), options

    def write(self, item, lines, amount=1.0, depth=0, seen=()):
        rec, options = self.recipe_for(item)
        pad = "  " * depth + "- "
        amt = f"{amount:.3g} × {item}"
        if item in self.raw or item == "water":
            lines.append(f"{pad}{amt} (mined or pumped)")
            return
        if rec is None:
            lines.append(f"{pad}{amt} (no recipe: raw or special)")
            return
        if item in seen:
            lines.append(f"{pad}{amt} (loop, see above)")
            return
        made = 1.0
        for p in aslist(rec.get("products")):
            if p["name"] == item:
                made = p.get("amount") or ((p.get("amount_min", 1) + p.get("amount_max", 1)) / 2)
                made = made * (p.get("probability") or 1) or 1
        note = f"{rec['category']}, {rec['seconds']}s"
        cond = conditions_text(rec)
        if cond:
            note += f", only where {cond}"
        others = [o["name"] for o in options if o["name"] != rec["name"]]
        if others:
            note += f"; other recipes: {', '.join(others[:4])}"
        lines.append(f"{pad}{amt} [{note}]")
        for ing in aslist(rec.get("ingredients")):
            self.write(ing["name"], lines, amount * ing["amount"] / made, depth + 1, seen + (item,))


    def totals(self, item, amount=1.0, acc=None, seen=()):
        """Raw materials for `amount` of item, using each item's main recipe."""
        acc = {} if acc is None else acc
        rec, _ = self.recipe_for(item)
        if item in self.raw or item == "water" or rec is None or item in seen:
            acc[item] = acc.get(item, 0) + amount
            return acc
        made = 1.0
        for p in aslist(rec.get("products")):
            if p["name"] == item:
                made = p.get("amount") or ((p.get("amount_min", 1) + p.get("amount_max", 1)) / 2)
                made = made * (p.get("probability") or 1) or 1
        for ing in aslist(rec.get("ingredients")):
            self.totals(ing["name"], amount * ing["amount"] / made, acc, seen + (item,))
        return acc


def science_doc(data):
    trees = Trees(data["recipes"], data["resources"])
    techs = data["technologies"]
    packs = sorted({p["name"] for t in techs for p in aslist(t.get("packs"))})
    unlocked_by = {}
    for t in techs:
        for e in t.get("effects") or []:
            if e.startswith("recipe:"):
                unlocked_by.setdefault(e[7:], []).append(t["name"])
    lines = ["# Science packs: how progress is made", "",
             "Generated from the live game by scripts/dump_game_data.py. Don't edit by hand.", "",
             "Progress is research. Each tech needs a set number of units, and one unit consumes one of each listed pack in a lab. "
             "A few techs are unlocked by a trigger (doing something) instead. Each pack below is traced back to raw materials. "
             "Amounts are per one pack, before productivity.", "",
             "## Total research needed", "",
             "| Pack | Packs for all finite techs | Techs that use it | Unlocked by |", "|---|---:|---:|---|"]
    for pack in packs:
        total = uses = 0
        for t in techs:
            for p in aslist(t.get("packs")):
                if p["name"] == pack:
                    uses += 1
                    total += (t.get("units") or 0) * p.get("amount", 1)
        lines.append(f"| {pack} | {total:,.0f} | {uses} | {', '.join(unlocked_by.get(pack, ['-']))} |")
    triggers = [t for t in techs if t.get("trigger")]
    lines += ["", "## Trigger techs (no labs)", "", "| Tech | Needs |", "|---|---|"]
    for t in sorted(triggers, key=lambda x: x["name"]):
        lines.append(f"| {t['name']} | {json.dumps(t['trigger'], separators=(',', ':'))} |")
    for pack in packs:
        lines += ["", f"## {pack}", ""]
        raw = trees.totals(pack)
        lines += ["Raw per pack: " + ", ".join(f"{v:.3g} {k}" for k, v in sorted(raw.items(), key=lambda kv: -kv[1])), ""]
        trees.write(pack, lines)
    return "\n".join(lines) + "\n"


def spoil_doc(data):
    rows = [i for i in data["items"] if i.get("spoil_ticks")]
    rows.sort(key=lambda i: i["spoil_ticks"])
    lines = ["# Items that spoil", "", "Generated from the live game. Shortest life first. Spoilage clocks are why Gleba is hard: "
             "belts must keep moving, and a backed-up line turns into spoilage that can block it.", "",
             "| Item | Life (minutes) | Becomes |", "|---|---:|---|"]
    for i in rows:
        lines.append(f"| {i['name']} | {i['spoil_ticks'] / 3600:.1f} | {i.get('spoil_result') or '-'} |")
    return "\n".join(lines) + "\n"


def planet_doc(data):
    lines = ["# Recipes limited by surface", "", "Generated from the live game. Conditions are surface properties, listed in planets.json.", "",
             "| Recipe | Category | Condition |", "|---|---|---|"]
    for r in sorted(data["recipes"], key=lambda x: x["name"]):
        if r.get("hidden") or r["name"].endswith("-recycling"):
            continue
        cond = conditions_text(r)
        if cond:
            lines.append(f"| {r['name']} | {r['category']} | {cond} |")
    lines += ["", "# Planets and routes", "", "| Location | Type | Surface properties |", "|---|---|---|"]
    for p in data["planets"]:
        if not p.get("hidden"):
            lines.append(f"| {p['name']} | {p['type']} | {json.dumps(p.get('surface_properties') or {}, separators=(',', ':'))} |")
    lines += ["", "| Route | From | To | Length |", "|---|---|---|---:|"]
    for c in data["space_connections"]:
        lines.append(f"| {c['name']} | {c.get('from')} | {c.get('to')} | {c.get('length')} |")
    return "\n".join(lines) + "\n"


def machine_doc(data):
    lines = ["# Machines", "", "Generated from the live game. Every entity a player can place, by type.", ""]
    by_type = {}
    for e in data["entities"]:
        by_type.setdefault(e["type"], []).append(e)
    for kind in sorted(by_type):
        lines += [f"## {kind}", ""]
        for e in sorted(by_type[kind], key=lambda x: x["name"]):
            bits = []
            for key, label in (("crafting_speed", "speed"), ("mining_speed", "mining"), ("belt_items_per_s", "items/s"),
                               ("energy_kW", "kW"), ("max_kW", "max kW"), ("produces_kW", "produces kW"), ("module_slots", "modules")):
                if e.get(key):
                    bits.append(f"{label} {e[key]:g}")
            cond = conditions_text(e)
            if cond:
                bits.append(f"only where {cond}")
            lines.append(f"- **{e['name']}**" + (": " + ", ".join(bits) if bits else ""))
        lines.append("")
    return "\n".join(lines)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    data = {}
    for kind in SOURCES:
        data[kind] = fetch(kind)
        (OUT / f"{kind}.json").write_text(json.dumps(data[kind], indent=0, sort_keys=True), encoding="utf-8")
        print(kind, len(data[kind]))
    (OUT / "science-packs.md").write_text(science_doc(data), encoding="utf-8")
    (OUT / "items-that-spoil.md").write_text(spoil_doc(data), encoding="utf-8")
    (OUT / "planet-only-recipes.md").write_text(planet_doc(data), encoding="utf-8")
    (OUT / "machines.md").write_text(machine_doc(data), encoding="utf-8")


if __name__ == "__main__":
    main()
