-- The model's eyes: a labelled text picture of a window of the map, one character per tile, and exact answers
-- to the questions a picture is bad at (what stands on this tile, where is a free rectangle). The picture is for
-- orientation; coordinates always come from the exact tools, never from counting characters.
local R = require("scripts.registry")

local MAX_W, MAX_H = 60, 40

local CHAR = {
  ["transport-belt"] = "b", ["underground-belt"] = "u", ["splitter"] = "s", ["loader"] = "l", ["loader-1x1"] = "l",
  ["inserter"] = "i", ["pipe"] = "p", ["pipe-to-ground"] = "q", ["pump"] = "j", ["offshore-pump"] = "J", ["storage-tank"] = "K",
  ["assembling-machine"] = "A", ["furnace"] = "F", ["mining-drill"] = "M", ["lab"] = "L",
  ["container"] = "C", ["logistic-container"] = "C", ["electric-pole"] = "P", ["roboport"] = "O",
  ["solar-panel"] = "S", ["accumulator"] = "a", ["generator"] = "G", ["boiler"] = "B", ["reactor"] = "N", ["heat-pipe"] = "h",
  ["straight-rail"] = "R", ["curved-rail-a"] = "R", ["curved-rail-b"] = "R", ["half-diagonal-rail"] = "R", ["train-stop"] = "X",
  ["ammo-turret"] = "T", ["electric-turret"] = "T", ["fluid-turret"] = "T", ["artillery-turret"] = "T",
  ["wall"] = "W", ["gate"] = "g", ["beacon"] = "E", ["rocket-silo"] = "Z", ["cargo-landing-pad"] = "D",
  ["asteroid-collector"] = "Y", ["thruster"] = "H", ["space-platform-hub"] = "U", ["cargo-bay"] = "y",
  ["tree"] = "t", ["plant"] = "t", ["simple-entity"] = "r", ["cliff"] = "c", ["resource"] = ":",
  ["entity-ghost"] = "?", ["character"] = "@", ["unit-spawner"] = "!", ["unit"] = "!", ["turret"] = "!",
}
local MEANING = {
  b = "belt", u = "underground belt", s = "splitter", l = "loader", i = "inserter", p = "pipe", q = "underground pipe",
  j = "pump", J = "offshore pump", K = "storage tank", A = "assembling machine", F = "furnace", M = "mining drill", L = "lab",
  C = "chest", P = "electric pole", O = "roboport", S = "solar panel", a = "accumulator", G = "generator or turbine",
  B = "boiler or heat exchanger", N = "reactor or heating tower", h = "heat pipe", R = "rail", X = "train stop", T = "turret",
  W = "wall", g = "gate", E = "beacon", Z = "rocket silo", D = "cargo landing pad", Y = "asteroid collector", H = "thruster",
  U = "platform hub", y = "cargo bay", t = "tree or plant", r = "rock", c = "cliff", [":"] = "ore or other resource",
  ["?"] = "ghost (planned, not built)", ["@"] = "player character", ["!"] = "enemy", ["#"] = "other building",
  ["."] = "free ground", ["~"] = "water", [" "] = "no ground (space or out of map)",
}
-- Things that are on the map but take no room for building purposes.
local SKIP = {
  ["logistic-robot"] = true, ["construction-robot"] = true, ["corpse"] = true, ["character-corpse"] = true, ["item-entity"] = true,
  ["fish"] = true, ["cargo-pod"] = true, ["smoke-with-trigger"] = true, ["explosion"] = true, ["particle-source"] = true,
  ["projectile"] = true, ["beam"] = true, ["fire"] = true, ["sticker"] = true, ["speech-bubble"] = true, ["flying-text"] = true,
  ["highlight-box"] = true, ["rocket-silo-rocket"] = true, ["rocket-silo-rocket-shadow"] = true, ["asteroid"] = true,
  ["lightning"] = true, ["segment"] = true, ["spider-leg"] = true, ["arrow"] = true, ["stream"] = true,
}
-- Low things are drawn first so a building on top of ore shows as the building.
local LOW = { ["resource"] = true, ["tree"] = true, ["plant"] = true, ["simple-entity"] = true, ["cliff"] = true }

local function surface_of(name)
  if name then
    local s = game.surfaces[name]
    if not s then
      local all = {}
      for _, x in pairs(game.surfaces) do all[#all + 1] = x.name end
      return nil, { error = "there is no surface named '" .. name .. "'", hint = "surfaces: " .. table.concat(all, ", ") }
    end
    return s
  end
  local p = game.connected_players[1]
  return (p and p.surface) or game.surfaces.nauvis or game.surfaces[1]
end

local function tile_char(surface, x, y)
  local t = surface.get_tile(x, y)
  if not t.valid then return " " end
  local n = t.name
  if n == "out-of-map" or n == "empty-space" then return " " end
  if t.collides_with("water_tile") then return "~" end
  return "."
end

local function footprint(e)
  local b = e.bounding_box
  return math.floor(b.left_top.x + 0.05), math.floor(b.left_top.y + 0.05), math.ceil(b.right_bottom.x - 0.05) - 1, math.ceil(b.right_bottom.y - 0.05) - 1
end

local function window(a)
  local w = math.max(1, math.min(math.floor(a.width), MAX_W))
  local h = math.max(1, math.min(math.floor(a.height), MAX_H))
  local x0, y0 = math.floor(a.x), math.floor(a.y)
  return x0, y0, w, h
end

R.register {
  name = "map",
  description = "A text picture of part of the map, one character per tile, with x labels on top and the y of each row at the left. Use it to see what is where and where there is room. Do not count characters to get coordinates: use 'tile' for what stands at a spot and 'find_free' for room to build. At most 60 wide and 40 high per call.",
  params = {
    x = { type = "number", required = true, description = "x of the left column (tiles)" },
    y = { type = "number", required = true, description = "y of the top row (tiles; y grows downward, north is up)" },
    width = { type = "number", default = 40, description = "columns, at most 60" },
    height = { type = "number", default = 24, description = "rows, at most 40" },
    surface = { type = "string", description = "surface name such as 'nauvis'; leave out for where the player is" },
  },
  run = function(a)
    local surface, err = surface_of(a.surface)
    if not surface then return err end
    local x0, y0, w, h = window(a)
    local cells, used, count = {}, {}, {}
    local function paint(e, low)
      if SKIP[e.type] or LOW[e.type] ~= low then return end
      local ch = CHAR[e.type] or "#"
      local ax, ay, bx, by = footprint(e)
      for x = math.max(ax, x0), math.min(bx, x0 + w - 1) do
        for y = math.max(ay, y0), math.min(by, y0 + h - 1) do cells[y * 100000 + x] = ch end
      end
      local label = (e.type == "entity-ghost") and ("ghost of " .. e.ghost_name) or e.name
      count[ch] = count[ch] or {}
      count[ch][label] = (count[ch][label] or 0) + 1
    end
    local found = surface.find_entities_filtered { area = { { x0, y0 }, { x0 + w, y0 + h } } }
    for _, e in pairs(found) do paint(e, true) end
    for _, e in pairs(found) do paint(e, nil) end
    local lines = {}
    local ruler, marks = {}, {}
    for i = 0, w - 1 do
      local x = x0 + i
      marks[#marks + 1] = (x % 5 == 0) and "|" or " "
    end
    local label = string.rep(" ", w + 8)
    for i = 0, w - 1 do
      local x = x0 + i
      if x % 10 == 0 then
        local s = tostring(x)
        label = string.sub(label, 1, i) .. s .. string.sub(label, i + #s + 1)
      end
    end
    lines[#lines + 1] = "     " .. string.sub(label, 1, w + 4)
    lines[#lines + 1] = "     " .. table.concat(marks)
    for y = y0, y0 + h - 1 do
      local row = {}
      for x = x0, x0 + w - 1 do
        local ch = cells[y * 100000 + x] or tile_char(surface, x, y)
        used[ch] = true
        row[#row + 1] = ch
      end
      lines[#lines + 1] = string.format("%4d ", y) .. table.concat(row)
    end
    local legend = {}
    for ch in pairs(used) do
      local entry = { char = ch, means = MEANING[ch] or "other" }
      if count[ch] then
        local list = {}
        for name, n in pairs(count[ch]) do list[#list + 1] = name .. " x" .. n end
        table.sort(list)
        entry.here = list
      end
      legend[#legend + 1] = entry
    end
    table.sort(legend, function(p, q) return p.char < q.char end)
    return {
      surface = surface.name, left_x = x0, top_y = y0, width = w, height = h,
      picture = table.concat(lines, "\n"), legend = legend,
      reading = "the '|' marks on the second line stand over x values divisible by 5; the number at the start of each row is its y",
    }
  end,
}

local function status_name(e)
  local ok, st = pcall(function() return e.status end)
  if not ok or not st then return nil end
  for name, v in pairs(defines.entity_status) do
    if v == st then return name end
  end
end

R.register {
  name = "tile",
  description = "Exactly what stands on one tile: ground type and every building, resource or plant there, with its exact position, direction, recipe and working state.",
  params = {
    x = { type = "number", required = true, description = "tile x" },
    y = { type = "number", required = true, description = "tile y" },
    surface = { type = "string", description = "surface name; leave out for where the player is" },
  },
  run = function(a)
    local surface, err = surface_of(a.surface)
    if not surface then return err end
    local x, y = math.floor(a.x), math.floor(a.y)
    local things = {}
    for _, e in pairs(surface.find_entities_filtered { area = { { x + 0.05, y + 0.05 }, { x + 0.95, y + 0.95 } } }) do
      if not SKIP[e.type] then
        local recipe = nil
        pcall(function() local r = e.get_recipe() recipe = r and r.name or nil end)
        local ax, ay, bx, by = footprint(e)
        things[#things + 1] = {
          name = (e.type == "entity-ghost") and e.ghost_name or e.name, type = e.type,
          centre_x = e.position.x, centre_y = e.position.y,
          covers = { from_x = ax, from_y = ay, to_x = bx, to_y = by },
          direction = helpers.direction_to_string(e.direction), recipe = recipe, state = status_name(e),
          amount = (e.type == "resource") and e.amount or nil,
        }
      end
    end
    local t = surface.get_tile(x, y)
    return { surface = surface.name, x = x, y = y, ground = t.valid and t.name or "none", free = (#things == 0) and tile_char(surface, x, y) == ".", things = things }
  end,
}

R.register {
  name = "find_free",
  description = "The nearest empty rectangle of ground of a given size, searching outward from a point. Empty means no building, resource, tree, rock, cliff or water on any of its tiles. Returns the rectangle's top-left tile.",
  params = {
    x = { type = "number", required = true, description = "search around this x" },
    y = { type = "number", required = true, description = "search around this y" },
    width = { type = "number", required = true, description = "tiles wide" },
    height = { type = "number", required = true, description = "tiles high" },
    radius = { type = "number", default = 32, description = "how far to search, at most 64 tiles" },
    allow_resources = { type = "boolean", default = false, description = "true if ore under the rectangle is acceptable" },
    surface = { type = "string", description = "surface name; leave out for where the player is" },
  },
  run = function(a)
    local surface, err = surface_of(a.surface)
    if not surface then return err end
    local w, h = math.max(1, math.floor(a.width)), math.max(1, math.floor(a.height))
    if w > 100 or h > 100 then return { error = "at most 100 by 100 tiles" } end
    local cx, cy = math.floor(a.x - w / 2), math.floor(a.y - h / 2)
    local radius = math.max(0, math.min(math.floor(a.radius), 64))
    local function empty(x, y)
      local area = { { x + 0.05, y + 0.05 }, { x + w - 0.05, y + h - 0.05 } }
      for _, e in pairs(surface.find_entities_filtered { area = area }) do
        if not SKIP[e.type] and not (a.allow_resources and e.type == "resource") then return false end
      end
      if surface.count_tiles_filtered { area = { { x, y }, { x + w, y + h } }, collision_mask = "water_tile" } > 0 then return false end
      for _, n in pairs { "out-of-map", "empty-space" } do
        if prototypes.tile[n] and surface.count_tiles_filtered { area = { { x, y }, { x + w, y + h } }, name = n } > 0 then return false end
      end
      return true
    end
    local step = (radius > 24) and 2 or 1
    for r = 0, radius, step do
      for dx = -r, r, step do
        for dy = -r, r, step do
          if math.max(math.abs(dx), math.abs(dy)) == r and empty(cx + dx, cy + dy) then
            return { found = true, surface = surface.name, left_x = cx + dx, top_y = cy + dy, width = w, height = h, tiles_from_start = r }
          end
        end
      end
    end
    return { found = false, surface = surface.name, searched_radius = radius, hint = "try a larger radius, a smaller rectangle, or another starting point" }
  end,
}

return { surface_of = surface_of, status_name = status_name, SKIP = SKIP }
