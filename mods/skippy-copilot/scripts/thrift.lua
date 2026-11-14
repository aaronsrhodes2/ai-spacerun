-- Thrift: wasting nothing, and using as little ground as the work needs. Two aims players drive toward (the Captain,
-- 2026-11-13): every surplus and every thing thrown away is an opening to make something useful of it, and a working
-- block squeezed into as few tiles as it can be is easy to copy and repeat.
--
--   surplus     what is made faster than it is used, what is used faster than it is made, and where stock sits full
--   footprint   how much ground a rectangle of factory really uses, and what it does there, as the measure for
--               compacting it: the same work in fewer tiles
local R = require("scripts.registry")
local G = require("scripts.grid")

local function surfaces()
  local out = {}
  for _, s in pairs(game.surfaces) do out[s.index] = s end
  return out
end

local function rate(force, s, item, category)
  local ok, n = pcall(function()
    return force.get_item_production_statistics(s).get_flow_count { name = item, category = category, precision_index = defines.flow_precision_index.ten_minutes }
  end)
  return (ok and n) or 0
end

R.register {
  name = "surplus",
  description = "Where the factory wastes or runs short: for every item moving through it, how many are made and used a minute (last ten minutes, all surfaces), sorted into surpluses (made much faster than used: an opening to make something useful of it, or to make less) and shortfalls (used as fast as made, with machines waiting). Also the chests that stand full. Use it for 'what are we wasting' and before throwing anything away.",
  params = {
    top = { type = "number", default = 8, description = "how many surpluses and shortfalls to list" },
    surface = { type = "string", description = "one surface only; leave out for all of them together" },
  },
  run = function(a)
    local force = game.forces.player
    local where = surfaces()
    if a.surface then
      local s, err = G.surface_of(a.surface)
      if not s then return err end
      where = { [s.index] = s }
    end
    -- every item the statistics know of
    local seen = {}
    for _, s in pairs(where) do
      local ok, stats = pcall(function() return force.get_item_production_statistics(s) end)
      if ok and stats then
        for name in pairs(stats.input_counts or {}) do seen[name] = true end
        for name in pairs(stats.output_counts or {}) do seen[name] = true end
      end
    end
    local over, under = {}, {}
    for item in pairs(seen) do
      local made, used = 0, 0
      for _, s in pairs(where) do
        made = made + rate(force, s, item, "input")
        used = used + rate(force, s, item, "output")
      end
      made, used = math.floor(made * 10 + 0.5) / 10, math.floor(used * 10 + 0.5) / 10
      if made > 0 or used > 0 then
        local entry = { item = item, made_per_minute = made, used_per_minute = used, spare_per_minute = math.floor((made - used) * 10 + 0.5) / 10 }
        if made > used * 1.25 and made - used >= 1 then
          over[#over + 1] = entry
        elseif used > 0 and made <= used * 1.02 then
          under[#under + 1] = entry
        end
      end
    end
    table.sort(over, function(p, q) return p.spare_per_minute > q.spare_per_minute end)
    table.sort(under, function(p, q) return p.used_per_minute > q.used_per_minute end)
    local top = math.max(1, math.min(a.top, 30))
    local function first(list)
      local out = {}
      for i = 1, math.min(top, #list) do out[#out + 1] = list[i] end
      return out
    end
    -- chests with no room left: stock that has stopped moving
    local full, full_n = {}, 0
    for _, s in pairs(where) do
      for _, c in pairs(s.find_entities_filtered { type = { "container", "logistic-container" }, force = force }) do
        local ok, inv = pcall(function() return c.get_inventory(defines.inventory.chest) end)
        if ok and inv and inv.is_full() then
          full_n = full_n + 1
          if #full < 5 then
            local best, best_n
            for _, it in pairs(inv.get_contents()) do
              if not best_n or it.count > best_n then best, best_n = it.name, it.count end
            end
            full[#full + 1] = { chest = c.name, surface = s.name, x = c.position.x, y = c.position.y, mostly = best }
          end
        end
      end
    end
    return {
      surpluses = first(over), shortfalls = first(under), full_chests = full_n, full_chest_examples = full,
      what_to_do_with_a_surplus = "in this order: make less of it; make something useful from it; only then recycle or void it. On a space platform, reprocess surplus asteroid chunks into the kinds that are short before throwing any overboard.",
      note = "a surplus is made at least a quarter faster than it is used; a shortfall is used as fast as it is made",
    }
  end,
}

R.register {
  name = "footprint",
  description = "How much ground a rectangle of factory really uses, and what it does there: the tiles its buildings cover against the tiles of the rectangle around them, how many of each building, which recipes run, and how many empty tiles lie inside. This is the measure for compacting: plan the same work again in fewer tiles and compare. Give the rectangle, such as one from 'locate'.",
  params = {
    x = { type = "number", required = true, description = "x of the left column" },
    y = { type = "number", required = true, description = "y of the top row" },
    width = { type = "number", required = true, description = "columns, at most 100" },
    height = { type = "number", required = true, description = "rows, at most 100" },
    surface = { type = "string", description = "surface name; leave out for where the player is" },
  },
  run = function(a)
    local surface, err = G.surface_of(a.surface)
    if not surface then return err end
    local w, h = math.floor(a.width), math.floor(a.height)
    if w < 1 or h < 1 or w > 100 or h > 100 then return { error = "width and height must be between 1 and 100" } end
    local x0, y0 = math.floor(a.x), math.floor(a.y)
    local covered, counts, recipes = {}, {}, {}
    local l, t, r, b
    local n = 0
    for _, e in pairs(surface.find_entities_filtered { area = { { x0 + 0.05, y0 + 0.05 }, { x0 + w - 0.05, y0 + h - 0.05 } }, force = "player" }) do
      if e.type ~= "character" and e.type ~= "entity-ghost" and not G.SKIP[e.type] then
        n = n + 1
        counts[e.name] = (counts[e.name] or 0) + 1
        local box = e.bounding_box
        local ax, ay = math.floor(box.left_top.x + 0.05), math.floor(box.left_top.y + 0.05)
        local bx, by = math.ceil(box.right_bottom.x - 0.05) - 1, math.ceil(box.right_bottom.y - 0.05) - 1
        l, t, r, b = math.min(l or ax, ax), math.min(t or ay, ay), math.max(r or bx, bx), math.max(b or by, by)
        for x = ax, bx do
          for y = ay, by do covered[y * 100000 + x] = true end
        end
        local ok, recipe = pcall(function() return e.get_recipe() end)
        if ok and recipe then recipes[recipe.name] = (recipes[recipe.name] or 0) + 1 end
      end
    end
    if n == 0 then return { buildings = 0, note = "nothing of ours stands in that rectangle" } end
    local used = 0
    for _ in pairs(covered) do used = used + 1 end
    local box_tiles = (r - l + 1) * (b - t + 1)
    local runs = {}
    for name, c in pairs(recipes) do runs[#runs + 1] = name .. " x" .. c end
    table.sort(runs)
    return {
      surface = surface.name, buildings = n, pieces = counts, recipes = runs,
      tight_rectangle = { from_x = l, from_y = t, to_x = r, to_y = b, width = r - l + 1, height = b - t + 1 },
      tiles_in_rectangle = box_tiles, tiles_covered = used, tiles_empty = box_tiles - used,
      filled = math.floor(used / box_tiles * 100 + 0.5) .. "%",
      to_compact = "plan the same recipes and counts again (plan_production for the numbers, plan_row and joints for the layout) in a rectangle with fewer tiles than tiles_in_rectangle; build it beside the old one, see it working, and ask the player before removing the old one",
    }
  end,
}
