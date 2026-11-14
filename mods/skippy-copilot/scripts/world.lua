-- Finding things in the world and changing what stands in it: where the ore, oil and water are; where a piece that
-- is fussy about its ground can go; taking something away; changing a machine's recipe.
local R = require("scripts.registry")
local G = require("scripts.grid")
local A = require("scripts.alerts")
local V = require("scripts.avatar")

local CELL = 8                      -- patches are found on a grid of this many tiles: ore within a cell of ore is one patch

local function centre_for(a, surface)
  if a.x and a.y then return a.x, a.y end
  local p = A.any_player()
  if p and p.surface == surface then return p.position.x, p.position.y end
  return 0, 0
end

R.register {
  name = "find_resources",
  description = "Where the ore, oil and other resources are: each patch with what it is, how much is left, the rectangle it covers, its centre and how far it is. Nearest first. Give a kind (such as 'iron-ore') for one resource only, or 'water' for the nearest water. Searches around the player unless a point is given.",
  params = {
    kind = { type = "string", description = "internal name of a resource such as 'iron-ore', 'crude-oil', or 'water'; leave out for every resource" },
    x = { type = "number", description = "centre x of the search; leave out for around the player" },
    y = { type = "number", description = "centre y of the search" },
    radius = { type = "number", default = 150, description = "how far to look, in tiles, at most 500" },
    surface = { type = "string", description = "surface name; leave out for where the player is" },
  },
  run = function(a)
    local surface, err = G.surface_of(a.surface)
    if not surface then return err end
    local cx, cy = centre_for(a, surface)
    local r = math.max(8, math.min(a.radius, 500))
    if a.kind == "water" then
      local best, best_d
      for x = math.floor(cx - r), math.floor(cx + r), 2 do
        for y = math.floor(cy - r), math.floor(cy + r), 2 do
          local t = surface.get_tile(x, y)
          if t.valid and t.collides_with("water_tile") then
            local d = math.abs(x - cx) + math.abs(y - cy)
            if not best_d or d < best_d then best, best_d = { x = x, y = y }, d end
          end
        end
      end
      if not best then return { found = false, hint = "no water within " .. r .. " tiles; try a larger radius or reveal more of the map" } end
      return { found = true, kind = "water", x = best.x, y = best.y, tiles_away = math.floor(math.sqrt((best.x - cx) ^ 2 + (best.y - cy) ^ 2)),
               note = "this is a water tile at the nearest shore; an offshore pump goes on the land beside it (use find_placement)" }
    end
    if a.kind and not prototypes.entity[a.kind] then
      return { error = "there is no resource named '" .. a.kind .. "'", hint = "use 'search' with kind 'entity', or leave kind out to see every resource nearby" }
    end
    local found = surface.find_entities_filtered { type = "resource", name = a.kind, area = { { cx - r, cy - r }, { cx + r, cy + r } } }
    -- gather ore into grid cells, then join neighbouring cells of the same resource into patches
    local cells = {}
    for _, e in pairs(found) do
      local key = e.name .. "|" .. math.floor(e.position.x / CELL) .. "|" .. math.floor(e.position.y / CELL)
      local c = cells[key]
      if not c then
        c = { name = e.name, gx = math.floor(e.position.x / CELL), gy = math.floor(e.position.y / CELL), tiles = 0, amount = 0,
              l = e.position.x, t = e.position.y, r = e.position.x, b = e.position.y }
        cells[key] = c
      end
      c.tiles, c.amount = c.tiles + 1, c.amount + (e.amount or 0)
      c.l, c.t, c.r, c.b = math.min(c.l, e.position.x), math.min(c.t, e.position.y), math.max(c.r, e.position.x), math.max(c.b, e.position.y)
    end
    local patches = {}
    for key, c in pairs(cells) do
      if not c.seen then
        local p = { kind = c.name, tiles = 0, amount = 0, l = c.l, t = c.t, r = c.r, b = c.b }
        local todo = { c }
        c.seen = true
        while #todo > 0 do
          local cur = table.remove(todo)
          p.tiles, p.amount = p.tiles + cur.tiles, p.amount + cur.amount
          p.l, p.t, p.r, p.b = math.min(p.l, cur.l), math.min(p.t, cur.t), math.max(p.r, cur.r), math.max(p.b, cur.b)
          for dx = -1, 1 do
            for dy = -1, 1 do
              local n = cells[cur.name .. "|" .. (cur.gx + dx) .. "|" .. (cur.gy + dy)]
              if n and not n.seen then
                n.seen = true
                todo[#todo + 1] = n
              end
            end
          end
        end
        local mx, my = (p.l + p.r) / 2, (p.t + p.b) / 2
        patches[#patches + 1] = {
          kind = p.kind, tiles = p.tiles, amount = p.amount,
          from_x = math.floor(p.l), from_y = math.floor(p.t), to_x = math.floor(p.r), to_y = math.floor(p.b),
          centre_x = math.floor(mx), centre_y = math.floor(my), tiles_away = math.floor(math.sqrt((mx - cx) ^ 2 + (my - cy) ^ 2)),
        }
      end
    end
    table.sort(patches, function(p, q) return p.tiles_away < q.tiles_away end)
    local out = {}
    for i = 1, math.min(12, #patches) do out[#out + 1] = patches[i] end
    return { surface = surface.name, searched_around = { x = math.floor(cx), y = math.floor(cy) }, radius = r, patches = out,
             more_not_shown = math.max(0, #patches - #out),
             hint = (#patches == 0) and "nothing found: try a larger radius or reveal more of the map" or nil }
  end,
}

R.register {
  name = "find_placement",
  description = "Where a piece can really be placed near a spot, by trying it: for pieces that are fussy about their ground or their neighbours, such as an offshore pump (which must touch water), a pumpjack (on oil) or a mining drill (on ore). Returns up to five places that the game accepts, nearest first, each with the direction that worked.",
  params = {
    name = { type = "string", required = true, description = "internal name of the piece" },
    x = { type = "number", required = true, description = "look around this x" },
    y = { type = "number", required = true, description = "look around this y" },
    radius = { type = "number", default = 8, description = "how far to try, at most 20 tiles" },
    surface = { type = "string", description = "surface name; leave out for where the player is" },
  },
  run = function(a)
    local surface, err = G.surface_of(a.surface)
    if not surface then return err end
    local proto = prototypes.entity[a.name]
    if not proto then return { error = "there is no building named '" .. a.name .. "'", hint = "use 'search' with kind 'entity'" } end
    local w, h = proto.tile_width or 1, proto.tile_height or 1
    local r = math.max(0, math.min(math.floor(a.radius), 20))
    local bx, by = math.floor(a.x), math.floor(a.y)
    local names = { [0] = "north", [4] = "east", [8] = "south", [12] = "west" }
    local out = {}
    for ring = 0, r do
      for dx = -ring, ring do
        for dy = -ring, ring do
          if math.max(math.abs(dx), math.abs(dy)) == ring and #out < 5 then
            local tx, ty = bx + dx, by + dy
            for _, d in ipairs { 0, 4, 8, 12 } do
              local turned = (d == 4 or d == 12)
              local pw, ph = turned and h or w, turned and w or h
              local pos = { tx + pw / 2, ty + ph / 2 }
              if surface.can_place_entity { name = a.name, position = pos, direction = d, force = "player", build_check_type = defines.build_check_type.manual } then
                out[#out + 1] = { x = pos[1], y = pos[2], direction = names[d], tile_x = tx, tile_y = ty, tiles_away = ring }
                break
              end
            end
          end
        end
      end
    end
    if #out == 0 then return { found = false, hint = "the game accepts '" .. a.name .. "' nowhere within " .. r .. " tiles of that spot; try a larger radius or another spot" } end
    return { found = true, name = a.name, places = out, note = "x and y are the piece's centre, as plan_pieces wants them" }
  end,
}

R.register {
  name = "remove",
  description = "Take away what stands in a rectangle: buildings of ours only, never ore, trees or rock. With dry_run true (the default) nothing is removed and the list of what would go is returned. Say what you will remove and ask the player before removing anything that is working.",
  params = {
    x = { type = "number", required = true, description = "x of the left column" },
    y = { type = "number", required = true, description = "y of the top row" },
    width = { type = "number", default = 1, description = "columns, at most 60" },
    height = { type = "number", default = 1, description = "rows, at most 60" },
    name = { type = "string", description = "only pieces with this name; leave out for everything of ours" },
    dry_run = { type = "boolean", default = true, description = "true to only list" },
    surface = { type = "string", description = "surface name; leave out for where the player is" },
  },
  run = function(a)
    local surface, err = G.surface_of(a.surface)
    if not surface then return err end
    local w, h = math.floor(a.width), math.floor(a.height)
    if w < 1 or h < 1 or w > 60 or h > 60 then return { error = "width and height must be between 1 and 60" } end
    local x0, y0 = math.floor(a.x), math.floor(a.y)
    local list = surface.find_entities_filtered { area = { { x0 + 0.05, y0 + 0.05 }, { x0 + w - 0.05, y0 + h - 0.05 } }, force = "player", name = a.name }
    local counts, working, keep = {}, 0, {}
    for _, e in pairs(list) do
      -- ours only: the filter above asks for our force, and this makes sure of it whatever the game hands back
      local ours = e.force and e.force.name == "player"
      if ours and e.type ~= "character" and e.type ~= "resource" and e.type ~= "tree" and e.type ~= "simple-entity" and e.type ~= "cliff" and not G.SKIP[e.type] then
        keep[#keep + 1] = e
        local label = (e.type == "entity-ghost") and ("ghost of " .. e.ghost_name) or e.name
        counts[label] = (counts[label] or 0) + 1
        if G.status_name(e) == "working" then working = working + 1 end
      end
    end
    if #keep == 0 then return { removed = 0, would_remove = 0, note = "nothing of ours stands there" } end
    if a.dry_run then
      return { would_remove = #keep, pieces = counts, working_now = working,
               note = (working > 0) and (working .. " of these are working: ask the player before removing them") or "none of these is working" }
    end
    if V.executor() ~= "god" then
      return { error = "taking things down by hand is not built yet", hint = "the player can remove it, or switch to free-hand mode" }
    end
    for _, e in ipairs(keep) do e.destroy() end
    return { removed = #keep, pieces = counts }
  end,
}

R.register {
  name = "set_recipe",
  description = "Set or change the recipe of a machine that is already standing. Changing the recipe of a working machine stops what it was making: ask the player first.",
  params = {
    x = { type = "number", required = true, description = "tile x of the machine" },
    y = { type = "number", required = true, description = "tile y of the machine" },
    recipe = { type = "string", required = true, description = "internal recipe name" },
    surface = { type = "string", description = "surface name; leave out for where the player is" },
  },
  run = function(a)
    local surface, err = G.surface_of(a.surface)
    if not surface then return err end
    local x, y = math.floor(a.x), math.floor(a.y)
    local e
    for _, o in pairs(surface.find_entities_filtered { area = { { x + 0.05, y + 0.05 }, { x + 0.95, y + 0.95 } }, force = "player" }) do
      if o.type == "assembling-machine" or o.type == "furnace" or o.type == "rocket-silo" then e = o end
    end
    if not e then return { error = "no machine that takes a recipe stands at " .. x .. "," .. y, hint = "use 'tile' to see what is there" } end
    local recipe = game.forces.player.recipes[a.recipe]
    if not recipe then return { error = "there is no recipe named '" .. a.recipe .. "'", hint = "use 'search' with kind 'recipe'" } end
    if not recipe.enabled then return { error = "the recipe '" .. a.recipe .. "' is not researched yet" } end
    local before
    pcall(function() local r = e.get_recipe() before = r and r.name or nil end)
    local ok, why = pcall(function() e.set_recipe(a.recipe) end)
    if not ok then return { error = "the " .. e.name .. " cannot run '" .. a.recipe .. "'", hint = "use lookup on the recipe to see which machines make it" } end
    return { machine = e.name, recipe = a.recipe, was = before }
  end,
}
