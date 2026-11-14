-- Ranked bottlenecks. A bottleneck is named by the ITEM that machines are waiting for, or cannot get rid of, because
-- that is what the player has to fix: "nine machines are starved of copper cable" rather than a list of nine machines.
-- Built for the requests players really make: "fix the worst bottleneck", "the top three", "the one next to me".
local R = require("scripts.registry")
local G = require("scripts.grid")
local A = require("scripts.alerts")

local MACHINES = { "assembling-machine", "furnace", "lab", "rocket-silo" }

local function input_inventory(e)
  for _, key in pairs { "crafter_input", "assembling_machine_input", "furnace_source", "lab_input" } do
    local id = defines.inventory[key]
    if id then
      local ok, inv = pcall(function() return e.get_inventory(id) end)
      if ok and inv then return inv end
    end
  end
end

-- Which of its ingredients a starved machine lacks.
local function missing(e)
  local out = {}
  local ok, recipe = pcall(function() return e.get_recipe() end)
  if not ok or not recipe then return out end
  local inv = input_inventory(e)
  local fluids = e.get_fluid_contents()
  for _, ing in pairs(recipe.ingredients) do
    local have
    if ing.type == "fluid" then
      have = fluids[ing.name] or 0
    else
      have = inv and inv.get_item_count(ing.name) or 0
    end
    if have < ing.amount then out[#out + 1] = ing.name end
  end
  return out
end

local function products(e)
  local out = {}
  local ok, recipe = pcall(function() return e.get_recipe() end)
  if ok and recipe then
    for _, p in pairs(recipe.products) do out[#out + 1] = p.name end
  end
  return out
end

R.register {
  name = "bottlenecks",
  description = "The worst bottlenecks, ranked: for each, the item that machines are starved of (or cannot get rid of), how many machines wait on it, what they make, and example positions. Use it for 'fix the worst bottleneck' or 'the top three'. With near_player true it only looks around the player, for 'the bottleneck next to me'.",
  params = {
    top = { type = "number", default = 3, description = "how many to return, worst first" },
    near_player = { type = "boolean", default = false, description = "true to look only around the player" },
    radius = { type = "number", default = 40, description = "how far around the player or the given point to look, in tiles" },
    x = { type = "number", description = "centre x of an area to look in, instead of the whole surface" },
    y = { type = "number", description = "centre y of that area" },
    surface = { type = "string", description = "surface name; leave out for where the player is" },
  },
  run = function(a)
    local surface, err = G.surface_of(a.surface)
    if not surface then return err end
    local filter = { type = MACHINES, force = "player" }
    local cx, cy = a.x, a.y
    if a.near_player then
      local p = A.any_player()
      if not p then return { error = "no player is in the game, so there is no 'near the player'" } end
      surface, cx, cy = p.surface, p.position.x, p.position.y
    end
    if cx and cy then
      local r = math.max(1, math.min(a.radius, 200))
      filter.area = { { cx - r, cy - r }, { cx + r, cy + r } }
    elseif cx or cy then
      return { error = "give both x and y, or neither" }
    end
    local groups, power = {}, 0
    local function note(kind, item, e)
      local key = kind .. "|" .. item
      local g = groups[key]
      if not g then
        g = { kind = kind, item = item, machines_waiting = 0, they_make = {}, examples = {}, sx = 0, sy = 0 }
        groups[key] = g
      end
      g.machines_waiting = g.machines_waiting + 1
      g.sx, g.sy = g.sx + e.position.x, g.sy + e.position.y
      for _, p in pairs(products(e)) do g.they_make[p] = (g.they_make[p] or 0) + 1 end
      if #g.examples < 3 then g.examples[#g.examples + 1] = { name = e.name, x = e.position.x, y = e.position.y } end
    end
    for _, e in pairs(surface.find_entities_filtered(filter)) do
      local st = G.status_name(e)
      if st == "item_ingredient_shortage" or st == "fluid_ingredient_shortage" or st == "no_ingredients" or st == "missing_science_packs" then
        for _, item in pairs(missing(e)) do note("starved of", item, e) end
      elseif st == "full_output" or st == "waiting_for_space_in_destination" then
        for _, item in pairs(products(e)) do note("backed up with", item, e) end
      elseif st == "no_power" or st == "low_power" then
        power = power + 1
      end
    end
    local list = {}
    for _, g in pairs(groups) do
      local make = {}
      for name, n in pairs(g.they_make) do make[#make + 1] = name .. " x" .. n end
      table.sort(make)
      list[#list + 1] = {
        problem = g.kind .. " " .. g.item, item = g.item, kind = g.kind, machines_waiting = g.machines_waiting,
        those_machines_make = make, examples = g.examples,
        centre_x = math.floor(g.sx / g.machines_waiting), centre_y = math.floor(g.sy / g.machines_waiting),
        look = (g.kind == "starved of") and ("find what makes or carries " .. g.item .. " and why too little arrives")
          or ("find what takes " .. g.item .. " away and why it has stopped"),
      }
    end
    table.sort(list, function(p, q) return p.machines_waiting > q.machines_waiting end)
    local top = math.max(1, math.min(a.top, 20))
    local out = {}
    for i = 1, math.min(top, #list) do
      list[i].rank = i
      out[#out + 1] = list[i]
    end
    return {
      surface = surface.name, bottlenecks = out, others_not_shown = math.max(0, #list - #out),
      power_first = (power > 0) and (power .. " machines have no power or too little: fix power before any bottleneck below") or nil,
    }
  end,
}
