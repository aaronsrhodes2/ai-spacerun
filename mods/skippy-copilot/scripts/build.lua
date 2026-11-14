-- Changing the game. `occupancy` tells the planner what is in the way; `build` places a planned list of pieces,
-- as a dry run unless told otherwise. The model never calls these directly: the bridge's planning tools do, after the
-- plan has been checked for overlaps in code.
--
-- The executor is the one place that decides HOW a piece gets placed. Today there is one way, the "god hand": the
-- piece appears. The walking avatar (docs/solver-plan.md, increment 1) becomes a second way behind the same call, so
-- no tool changes when the rules get stricter.
--
-- Rule kept in every mode: nothing can be built before it is researched.
local R = require("scripts.registry")
local G = require("scripts.grid")
local V = require("scripts.avatar")

local MAX_SIDE = 100
local MAX_PIECES = 600

R.register {
  name = "occupancy",
  description = "For planning tools: which tiles of a window cannot be built on. Rows of characters, one per tile: '.' free, '#' taken (building, tree, rock, cliff, water, no ground), 'p' a pipe (taken, and a new pipe beside it would join it). Ore does not block.",
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
    if w < 1 or h < 1 or w > MAX_SIDE or h > MAX_SIDE then return { error = "width and height must be between 1 and " .. MAX_SIDE } end
    local x0, y0 = math.floor(a.x), math.floor(a.y)
    local cells = {}
    for _, e in pairs(surface.find_entities_filtered { area = { { x0, y0 }, { x0 + w, y0 + h } } }) do
      if not G.SKIP[e.type] and e.type ~= "resource" then
        local ch = (e.type == "pipe" or e.type == "pipe-to-ground") and "p" or "#"
        local b = e.bounding_box
        for x = math.max(math.floor(b.left_top.x + 0.05), x0), math.min(math.ceil(b.right_bottom.x - 0.05) - 1, x0 + w - 1) do
          for y = math.max(math.floor(b.left_top.y + 0.05), y0), math.min(math.ceil(b.right_bottom.y - 0.05) - 1, y0 + h - 1) do
            cells[y * 100000 + x] = ch
          end
        end
      end
    end
    local rows = {}
    for y = y0, y0 + h - 1 do
      local row = {}
      for x = x0, x0 + w - 1 do
        local ch = cells[y * 100000 + x]
        if not ch then
          local t = surface.get_tile(x, y)
          if not t.valid or t.name == "out-of-map" or t.name == "empty-space" or t.collides_with("water_tile") then ch = "#" else ch = "." end
        end
        row[#row + 1] = ch
      end
      rows[#rows + 1] = table.concat(row)
    end
    return { surface = surface.name, left_x = x0, top_y = y0, width = w, height = h, rows = rows }
  end,
}

-- A piece may be built once any recipe that makes its item is unlocked.
local function researched(force, proto)
  local items = proto.items_to_place_this
  if not items or #items == 0 then return false end
  for _, it in pairs(items) do
    for _, recipe in pairs(force.recipes) do
      if recipe.enabled then
        for _, p in pairs(recipe.products) do
          if p.name == it.name then return true end
        end
      end
    end
  end
  return false
end

-- The god hand: the piece appears. Returns the entity or nil.
local function place_by_hand(surface, force, piece)
  local e = surface.create_entity {
    name = piece.name, position = { piece.x, piece.y }, direction = piece.direction or 0, force = force,
    type = piece.type,                                   -- "input" or "output" for underground belts
    raise_built = true, create_build_effect_smoke = false,
  }
  if e and e.valid and piece.recipe then
    pcall(function() e.set_recipe(piece.recipe) end)
  end
  return e
end

-- "avatar" is not in this table: the avatar does not place at once, it takes the whole plan as a job (scripts/avatar.lua).
local EXECUTORS = { god = place_by_hand }

R.register {
  name = "build",
  description = "For planning tools: place a list of pieces, each {name, x, y, direction, recipe?, type?} by its centre. With dry_run true nothing is placed and every piece is checked: known name, researched, and room on the map. Without dry_run, pieces that pass are placed and the rest are reported.",
  params = {
    entities = { type = "table", required = true, description = "the pieces" },
    dry_run = { type = "boolean", default = true, description = "true to only check" },
    surface = { type = "string", description = "surface name; leave out for where the player is" },
  },
  run = function(a)
    local surface, err = G.surface_of(a.surface)
    if not surface then return err end
    local force = game.forces.player
    local n = 0
    for _ in pairs(a.entities) do n = n + 1 end
    if n == 0 then return { error = "the list of pieces is empty" } end
    if n > MAX_PIECES then return { error = "at most " .. MAX_PIECES .. " pieces in one call", hint = "build it in parts" } end
    local mode = V.executor()
    local place = EXECUTORS[mode]
    local ok_count, placed, failed, checked = 0, 0, {}, {}
    local allowed = {}
    for _, piece in pairs(a.entities) do
      local why
      local proto = (type(piece.name) == "string") and prototypes.entity[piece.name] or nil
      if type(piece.x) ~= "number" or type(piece.y) ~= "number" then
        why = "it has no position"
      elseif not proto then
        why = "there is no building named '" .. tostring(piece.name) .. "'"
      else
        if allowed[piece.name] == nil then allowed[piece.name] = researched(force, proto) end
        if not allowed[piece.name] then
          why = "it is not researched yet"
        elseif not surface.can_place_entity { name = piece.name, position = { piece.x, piece.y }, direction = piece.direction or 0, force = force, build_check_type = defines.build_check_type.manual } then
          why = "something is in the way, or the ground there does not allow it"
        elseif piece.recipe and not (force.recipes[piece.recipe] and force.recipes[piece.recipe].enabled) then
          why = "its recipe '" .. tostring(piece.recipe) .. "' is not researched yet"
        end
      end
      if why then
        if #failed < 20 then failed[#failed + 1] = { name = piece.name, x = piece.x, y = piece.y, why = why } end
      else
        ok_count = ok_count + 1
        checked[#checked + 1] = piece
      end
    end
    local failures = n - ok_count
    -- under the avatar every piece must also be carried: the avatar places from its own inventory
    local lacks, lacks_any = nil, false
    if mode == "avatar" then
      lacks = V.missing_for(checked)
      lacks_any = next(lacks) ~= nil
    end
    if not a.dry_run and mode == "avatar" then
      if failures > 0 or lacks_any then
        return { placed = 0, failed_count = failures, failed = (#failed > 0) and failed or nil, avatar_lacks = lacks_any and lacks or nil, executor = mode,
                 note = "nothing was started: " .. (lacks_any and "the avatar does not carry every piece" or "some pieces could not be placed") }
      end
      local q = V.queue_build(checked)
      if q.error then return q end
      return { placed = 0, queued = q.queued, job = q.job, executor = mode, surface = surface.name,
               note = "the avatar is walking to each piece and placing it; this takes time. Its result comes with the job." }
    end
    if not a.dry_run then
      -- nothing is placed unless every piece passed: half a line is worse than none
      if failures > 0 then
        return { placed = 0, failed_count = failures, failed = failed, note = "nothing was placed because some pieces could not be; fix the plan and dry-run again" }
      end
      for _, piece in ipairs(checked) do
        local e = place(surface, force, piece)
        if e and e.valid then
          placed = placed + 1
        elseif #failed < 20 then
          failed[#failed + 1] = { name = piece.name, x = piece.x, y = piece.y, why = "the game refused it at the moment of placing" }
        end
      end
      return { placed = placed, failed_count = n - placed, failed = (#failed > 0) and failed or nil, surface = surface.name, executor = mode }
    end
    return { would_place = ok_count, failed_count = failures, failed = (#failed > 0) and failed or nil, surface = surface.name, executor = mode,
             avatar_lacks = lacks_any and lacks or nil,
             note = (failures > 0) and "fix these before building" or (lacks_any and "the avatar must carry these items first" or "every piece can be placed") }
  end,
}
