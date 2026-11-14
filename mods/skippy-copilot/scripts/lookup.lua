-- Game facts, read live from the game's own object library (what the Factoriopedia shows). Nothing here is
-- remembered or looked up online: with other mods installed the answers change with them.
local R = require("scripts.registry")

-- Read a field that may not exist in this game version without stopping the tool.
local function at(obj, key)
  local ok, v = pcall(function() return obj[key] end)
  if ok then return v end
  return nil
end

local function call(obj, method, ...)
  local args = { ... }
  local ok, v = pcall(function() return obj[method](table.unpack(args)) end)
  if ok then return v end
  return nil
end

local function names(t)
  local out = {}
  for k, v in pairs(t or {}) do
    out[#out + 1] = (type(k) == "string") and k or ((type(v) == "table" and v.name) or tostring(v))
  end
  table.sort(out)
  return out
end

local function parts(list)
  local out = {}
  for _, p in pairs(list or {}) do
    local amount = p.amount or (p.amount_min and ((p.amount_min + p.amount_max) / 2))
    out[#out + 1] = { name = p.name, type = p.type, amount = amount, probability = (p.probability and p.probability < 1) and p.probability or nil }
  end
  return out
end

-- An empty list says nothing: leave the field out.
local function some(list)
  if list and next(list) ~= nil then return list end
  return nil
end

local function conditions(list)
  local out = {}
  for _, c in pairs(list or {}) do
    out[#out + 1] = { property = c.property, min = (c.min and c.min > -1e100) and c.min or nil, max = (c.max and c.max < 1e100) and c.max or nil }
  end
  return some(out)
end

local function is_recycling(r)
  for k, v in pairs(at(r, "categories") or {}) do
    if k == "recycling" or v == "recycling" then return true end
  end
  return false
end

local function recipe(name)
  local p = prototypes.recipe[name]
  if not p then return nil end
  local force = game.forces.player
  local cats = names(at(p, "categories") or { at(p, "category") })
  local made_in = {}
  for ename, e in pairs(prototypes.get_entity_filtered { { filter = "crafting-machine" } }) do
    local ec = at(e, "crafting_categories") or {}
    for _, c in pairs(cats) do
      if ec[c] then made_in[#made_in + 1] = ename break end
    end
  end
  table.sort(made_in)
  local unlocked_by = {}
  for tname, t in pairs(prototypes.technology) do
    for _, eff in pairs(t.effects or {}) do
      if eff.type == "unlock-recipe" and eff.recipe == name then unlocked_by[#unlocked_by + 1] = tname end
    end
  end
  return {
    kind = "recipe", name = name,
    available_now = force.recipes[name] and force.recipes[name].enabled or false,
    seconds = p.energy,
    ingredients = parts(p.ingredients), products = parts(p.products),
    categories = cats, made_in = some(made_in), unlocked_by = some(unlocked_by),
    only_where = conditions(at(p, "surface_conditions")),
  }
end

local function item(name)
  local p = prototypes.item[name]
  if not p then return nil end
  local made_by, recycled = {}, 0
  for rname, r in pairs(prototypes.recipe) do
    for _, prod in pairs(r.products or {}) do
      if prod.type == "item" and prod.name == name then
        if is_recycling(r) then recycled = recycled + 1 else made_by[#made_by + 1] = rname end
        break
      end
    end
  end
  table.sort(made_by)
  local place = at(p, "place_result")
  local spoil = call(p, "get_spoil_ticks")
  local weight = at(p, "weight")
  return {
    kind = "item", name = name, stack_size = p.stack_size,
    weight_kg = weight and weight / 1000 or nil,
    fits_in_one_rocket = (weight and weight > 0) and math.floor(1000000 / weight) or nil,
    fuel_megajoules = (at(p, "fuel_value") or 0) > 0 and p.fuel_value / 1000000 or nil,
    places = place and place.name or nil,
    spoils_after_seconds = (spoil and spoil > 0) and spoil / 60 or nil,
    spoils_into = at(p, "spoil_result") and p.spoil_result.name or nil,
    made_by_recipes = some(made_by),
    also_comes_out_of_recycling = (recycled > 0) and (recycled .. " other items give it back in a recycler") or nil,
  }
end

local function entity(name)
  local p = prototypes.entity[name]
  if not p then return nil end
  local heat = nil
  local hb = at(p, "heat_buffer_prototype")
  if hb then
    heat = { max_temperature = at(hb, "max_temperature"), connections = {} }
    for _, c in pairs(at(hb, "connections") or {}) do
      local pos = c.position
      heat.connections[#heat.connections + 1] = { x = pos.x or pos[1], y = pos.y or pos[2] }
    end
  end
  local items = {}
  for _, it in pairs(at(p, "items_to_place_this") or {}) do items[#items + 1] = it.name end
  local speed = call(p, "get_crafting_speed")
  local usage = call(p, "get_max_energy_usage")
  local supply = call(p, "get_supply_area_distance")
  local wire = call(p, "get_max_wire_distance")
  return {
    kind = "entity", name = name, type = p.type,
    tiles_wide = at(p, "tile_width"), tiles_high = at(p, "tile_height"),
    crafting_speed = speed, crafting_categories = some(names(at(p, "crafting_categories"))),
    power_kilowatts = (usage and usage > 0) and usage * 60 / 1000 or nil,
    module_slots = ((at(p, "module_inventory_size") or 0) > 0) and p.module_inventory_size or nil,
    mining_speed = at(p, "mining_speed"),
    belt_items_per_second = at(p, "belt_speed") and p.belt_speed * 480 or nil,
    pole_supply_tiles = (p.type == "electric-pole" and supply and supply > 0) and supply * 2 or nil,
    pole_wire_reach = (p.type == "electric-pole" and wire and wire > 0) and wire or nil,
    heat = heat,
    placed_with_item = some(items),
    only_where = conditions(at(p, "surface_conditions")),
    note = "numbers are for normal quality",
  }
end

local function technology(name)
  local p = prototypes.technology[name]
  if not p then return nil end
  local t = game.forces.player.technologies[name]
  local pre = {}
  for pname, pt in pairs(t.prerequisites or {}) do pre[#pre + 1] = { name = pname, researched = pt.researched } end
  local packs = {}
  for _, ing in pairs(p.research_unit_ingredients or {}) do packs[#packs + 1] = ing.name end
  local unlocks = {}
  for _, eff in pairs(p.effects or {}) do
    if eff.type == "unlock-recipe" then unlocks[#unlocks + 1] = eff.recipe end
  end
  local trig = at(p, "research_trigger")
  local trigger = nil
  if trig then
    trigger = { type = trig.type, item = trig.item and (trig.item.name or trig.item) or nil, entity = trig.entity and (trig.entity.name or trig.entity) or nil, count = trig.count }
  end
  return {
    kind = "technology", name = name, researched = t.researched,
    prerequisites = some(pre), science_packs = some(packs),
    units = (not trig) and p.research_unit_count or nil,
    earned_by = trigger, unlocks_recipes = some(unlocks),
  }
end

local function fluid(name)
  local p = prototypes.fluid[name]
  if not p then return nil end
  local made_by = {}
  for rname, r in pairs(prototypes.recipe) do
    for _, prod in pairs(r.products or {}) do
      if prod.type == "fluid" and prod.name == name then made_by[#made_by + 1] = rname break end
    end
  end
  table.sort(made_by)
  return { kind = "fluid", name = name, default_temperature = p.default_temperature, made_by_recipes = made_by }
end

local KINDS = { recipe = recipe, item = item, entity = entity, technology = technology, fluid = fluid }
local ORDER = { "recipe", "item", "entity", "technology", "fluid" }

local function search(text, kind, limit)
  local needle = string.lower(text)
  local out = {}
  for _, k in ipairs(ORDER) do
    if not kind or kind == k then
      local hits = {}
      for name in pairs(prototypes[k]) do
        if string.find(name, needle, 1, true) then hits[#hits + 1] = name end
      end
      table.sort(hits)
      for _, name in ipairs(hits) do
        if #out >= limit then return out, true end
        out[#out + 1] = { kind = k, name = name }
      end
    end
  end
  return out, false
end

R.register {
  name = "lookup",
  description = "Facts about one recipe, item, entity (machine or building), technology or fluid, read from the running game. Use it before stating any game number. Names are the game's internal names, such as 'electronic-circuit' or 'assembling-machine-2'; use 'search' if unsure of a name.",
  params = {
    name = { type = "string", required = true, description = "internal name, lower case with hyphens" },
    kind = { type = "string", description = "recipe, item, entity, technology or fluid; leave out to get every kind that has this name" },
  },
  run = function(a)
    if a.kind and not KINDS[a.kind] then
      return { error = "kind must be one of: recipe, item, entity, technology, fluid" }
    end
    local found = {}
    for _, k in ipairs(ORDER) do
      if not a.kind or a.kind == k then
        local r = KINDS[k](a.name)
        if r then found[#found + 1] = r end
      end
    end
    if #found == 0 then
      local close = search(a.name, a.kind, 10)
      if #close == 0 and #a.name > 4 then close = search(string.sub(a.name, 1, 4), a.kind, 10) end
      return { error = "nothing is named '" .. a.name .. "'" .. (a.kind and (" among " .. a.kind .. " names") or ""),
               hint = (#close > 0) and "these names are similar; call lookup again with one of them" or "try 'search' with part of the name",
               similar = (#close > 0) and close or nil }
    end
    return found
  end,
}

R.register {
  name = "search",
  description = "Find internal names that contain a piece of text, for use with 'lookup'. Example: text 'circuit' finds electronic-circuit, advanced-circuit and the technologies and recipes named after them.",
  params = {
    text = { type = "string", required = true, description = "part of a name, lower case" },
    kind = { type = "string", description = "recipe, item, entity, technology or fluid; leave out for all" },
    limit = { type = "number", default = 30, description = "most names to return" },
  },
  run = function(a)
    if a.kind and not KINDS[a.kind] then
      return { error = "kind must be one of: recipe, item, entity, technology, fluid" }
    end
    local hits, more = search(a.text, a.kind, math.max(1, math.min(a.limit, 100)))
    return { matches = hits, more_exist = more }
  end,
}
