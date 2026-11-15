#!/usr/bin/env python3
"""Menus for the planet Replicators (the Captain, 2026-11-14): each other planet gets its own Replicator that serves only what is UNIQUE to that
planet or what its Wheel makes in great plenty; Nauvis keeps serving the standard menu. READ-ONLY: this prints the candidate menus, it builds nothing.

unique(P)  items that planet P can make from its OWN resources with the enabled recipes, that Nauvis cannot make from its own (so the planet is the only
           source in the solar system short of imports). Recipes whose surface conditions the planet fails are skipped (the game's own check).
plenty(P)  the Wheel mission items (memory wheel-roles): Nauvis foundations, Fulgora processing units, Gleba rocket fuel, Vulcanus low-density structure.
           Reported with whether the planet can make them alone or needs imports (which ingredients).
machine    the crafting category of the recipe that makes each unique item, so the planet unit knows which machine type it needs
           (assembler, foundry, electromagnetic plant, biochamber, cryogenic plant, chemical plant via barrels).

Planet resources are read from the game (autoplace settings and fluid tiles), plus the planet's living inputs (Gleba seeds, spoilage; Aquilo ice).
Usage: scripts/planet_menus.py [--write]   (--write saves docs/planet-menus.md)"""
import json
import sys
from pathlib import Path

from _game import tools

ROOT = Path(__file__).resolve().parent.parent

RAWS = {
    "nauvis": {"items": ["iron-ore", "copper-ore", "coal", "stone", "uranium-ore", "wood", "raw-fish"], "fluids": ["crude-oil", "water"]},
    "vulcanus": {"items": ["calcite", "coal", "tungsten-ore"], "fluids": ["sulfuric-acid", "lava"]},
    "fulgora": {"items": ["scrap"], "fluids": ["heavy-oil"]},
    "gleba": {"items": ["stone", "yumako-seed", "jellynut-seed", "yumako", "jellynut", "spoilage", "pentapod-egg"], "fluids": ["water"]},
    "aquilo": {"items": ["ice"], "fluids": ["crude-oil", "fluorine", "lithium-brine", "ammoniacal-solution"]},
}
PLENTY = {"nauvis": ["space-platform-foundation"], "fulgora": ["processing-unit"], "gleba": ["rocket-fuel"], "vulcanus": ["low-density-structure"], "aquilo": []}

LUA = r'''
local f = game.forces.player
local RAWS = RAWSJSON
local PLENTY = PLENTYJSON
local function props(pn)
  local t = {}
  for name, proto in pairs(prototypes.surface_property) do t[name] = proto.default_value end
  local ok = pcall(function() for name, v in pairs(game.planets[pn].prototype.surface_properties) do t[name] = v end end)
  return t
end
local function cond_ok(r, pr)
  local ok, conds = pcall(function() return r.prototype.surface_conditions end)
  if not ok or not conds then return true end
  for _, c in pairs(conds) do
    local v = pr[c.property]
    if v == nil then return false end
    if c.min and v < c.min then return false end
    if c.max and v > c.max then return false end
  end
  return true
end
local function closure(pn, withn)
  local pr = props(pn)
  local feas, warn = {}, {}
  for _, n in pairs(RAWS[pn].items) do if prototypes.item[n] then feas[n] = true else warn[#warn + 1] = n end end
  for _, n in pairs(RAWS[pn].fluids) do if prototypes.fluid[n] then feas[n] = true else warn[#warn + 1] = n end end
  if withn then
    for _, n in pairs(RAWS.nauvis.items) do if prototypes.item[n] then feas[n] = true end end
    for _, n in pairs(RAWS.nauvis.fluids) do if prototypes.fluid[n] then feas[n] = true end end
  end
  local live = {}
  for name, r in pairs(f.recipes) do
    local p = r.prototype
    local rec = false
    for _, c in pairs(p.categories) do if c:find('recycling') then rec = true end end
    if rec and r.name == 'scrap-recycling' then rec = false end
    if r.enabled and not p.hidden and not rec and cond_ok(r, pr) then live[#live + 1] = r end
  end
  local made, changed, it = {}, true, 0
  while changed and it < 80 do
    changed = false
    it = it + 1
    for _, r in ipairs(live) do
      if not made[r.name] then
        local ok = true
        for _, i in ipairs(r.ingredients) do if not feas[i.name] then ok = false break end end
        if ok then
          made[r.name] = true
          changed = true
          for _, p in ipairs(r.products) do feas[p.name] = true end
        end
      end
    end
  end
  return feas, made, warn, live
end
local function cats(r) local t = {} for _, c in pairs(r.prototype.categories) do t[#t + 1] = c end table.sort(t) return table.concat(t, '+') end
local out = {}
local nfeas = closure('nauvis')
for pn, _ in pairs(RAWS) do
  local feas, made, warn, live = closure(pn)
  local rec = {items = 0, unique = {}, plenty = {}, warn = warn}
  local byitem = {}
  for _, r in ipairs(live) do
    if made[r.name] then
      for _, p in ipairs(r.products) do
        if p.type == 'item' then byitem[p.name] = byitem[p.name] or r end
      end
    end
  end
  for it, r in pairs(byitem) do
    rec.items = rec.items + 1
    local proto = prototypes.item[it]
    if proto and not proto.hidden and not nfeas[it] and pn ~= 'nauvis' then
      table.insert(rec.unique, {item = it, recipe = r.name, cat = cats(r)})
    end
  end
  table.sort(rec.unique, function(a, b) return a.item < b.item end)
  for _, it in pairs(PLENTY[pn] or {}) do
    local entry = {item = it, makeable = feas[it] and true or false}
    if not feas[it] then
      local miss = {}
      for name, r in pairs(f.recipes) do
        if r.enabled and #r.products >= 1 and r.products[1].name == it and not r.prototype.hidden then
          for _, i in ipairs(r.ingredients) do if not feas[i.name] then miss[#miss + 1] = i.name end end
          break
        end
      end
      entry.needs = miss
    end
    table.insert(rec.plenty, entry)
  end
  if pn ~= 'nauvis' then
    local feas2, made2, _, live2 = closure(pn, true)
    local by2 = {}
    for _, r in ipairs(live2) do
      if made2[r.name] then for _, p in ipairs(r.products) do if p.type == 'item' then by2[p.name] = by2[p.name] or r end end end
    end
    rec.with_nauvis = {}
    for it, r in pairs(by2) do
      local proto = prototypes.item[it]
      if proto and not proto.hidden and not nfeas[it] then table.insert(rec.with_nauvis, {item = it, recipe = r.name, cat = cats(r)}) end
    end
    table.sort(rec.with_nauvis, function(a, b) return a.item < b.item end)
  end
  rec.names = {}
  if DEBUGPN == pn then for it in pairs(byitem) do rec.names[#rec.names + 1] = it end table.sort(rec.names) end
  out[pn] = rec
end
rcon.print(helpers.table_to_json(out))
'''.replace("RAWSJSON", "__RAWS__").replace("PLENTYJSON", "__PLENTY__")


def to_lua(d):
    def val(v):
        if isinstance(v, dict):
            return "{" + ",".join(f"['{k}']={val(x)}" for k, x in v.items()) + "}"
        if isinstance(v, list):
            return "{" + ",".join(val(x) for x in v) + "}"
        return "'" + str(v) + "'"
    return val(d)


def main():
    dbg = sys.argv[sys.argv.index("--debug") + 1] if "--debug" in sys.argv else "none"
    code = LUA.replace("__RAWS__", to_lua(RAWS)).replace("__PLENTY__", to_lua(PLENTY)).replace("DEBUGPN", "'" + dbg + "'")
    data = json.loads(tools["run_lua"](code))
    if dbg != "none":
        print("DEBUG reachable on", dbg, ":", ", ".join(data[dbg].get("names", [])))
    print("Nauvis reachable items (with surface conditions):", data["nauvis"]["items"])
    lines = ["# Planet Replicator menus (read-only analysis, 2026-11-14)", "",
             "Each non-Nauvis planet gets a Replicator that serves only what is unique to it or what its Wheel makes in great plenty. Nauvis keeps the standard menu.", ""]
    for pn in ("vulcanus", "fulgora", "gleba", "aquilo"):
        d = data[pn]
        lines.append(f"## {pn.capitalize()}")
        lines.append(f"- Reachable from its own resources: {d['items']} items")
        by = {}
        for u in d["unique"]:
            by.setdefault(u["cat"], []).append(u["item"])
        lines.append(f"- **Unique** (Nauvis cannot make them from its own resources): **{len(d['unique'])}**")
        for cat, its in sorted(by.items(), key=lambda kv: -len(kv[1])):
            lines.append(f"  - machine `{cat}`: {len(its)}: " + ", ".join(its))
        wn = d.get("with_nauvis") or []
        extra = [u for u in wn if u["item"] not in {x["item"] for x in d["unique"]}]
        by2 = {}
        for u in extra:
            by2.setdefault(u["cat"], []).append(u["item"])
        lines.append(f"- **Also unique when Nauvis ships the basics** (needs this planet's resources plus Nauvis iron, copper, coal and so on): **{len(extra)}** more")
        for cat, its in sorted(by2.items(), key=lambda kv: -len(kv[1])):
            lines.append(f"  - machine `{cat}`: {len(its)}: " + ", ".join(its))
        for p in d["plenty"]:
            if p["makeable"]:
                lines.append(f"- **Wheel mission item** `{p['item']}`: makeable from the planet's own resources")
            else:
                lines.append(f"- **Wheel mission item** `{p['item']}`: needs imports of {', '.join(p.get('needs', [])) or '?'}")
        if not d["plenty"]:
            lines.append("- No Wheel (the Captain's four wheels are Nauvis, Fulgora, Gleba, Vulcanus): the menu is the unique items only.")
        if d["warn"]:
            lines.append(f"- (unknown raw names skipped: {', '.join(d['warn'])})")
        lines.append("")
    text = "\n".join(lines)
    print(text)
    if "--write" in sys.argv:
        (ROOT / "docs" / "planet-menus.md").write_text(text, encoding="utf-8")
        print("written docs/planet-menus.md")


if __name__ == "__main__":
    main()
