-- The avatar: a character that walks, reaches, mines, crafts and builds under the game's own limits. No teleport
-- anywhere in this file. It is the second executor (docs/solver-plan.md, increment 1): with the executor set to
-- "avatar", `build` hands its checked plan to the avatar, which walks to each piece and places it from its inventory.
--
-- The body is the player's own character when a player is in the game (the player IS the avatar, hands off the
-- keyboard), otherwise a character the mod keeps for itself (for runs with nobody connected).
--
-- Work is done as one job at a time, advanced every tick:
--   walk   ask the game's pathfinder for a path, follow it waypoint by waypoint, notice being stuck, ask again
--   build  for each piece: walk within building reach, check the item is carried and the spot is free, place it
--   mine   walk within mining reach of a spot, mine until enough is carried or nothing is left
-- A job ends with a result that says what was done and, if it stopped, why. The bridge waits for it.
local R = require("scripts.registry")
local A = require("scripts.alerts")

local ARRIVE = 0.35             -- tiles from a waypoint that count as there
local STUCK_TICKS = 45          -- ticks without progress before asking for a new path
local MAX_REPATHS = 3
local PATH_WAIT_TICKS = 600     -- give the pathfinder ten seconds
local MINE_TIMEOUT = 60 * 60    -- a minute without a new item ends a mining job

local V = {}

local DIRS = {                  -- the eight ways a character can walk: {dx, dy, direction}
  { 0, -1, defines.direction.north }, { 1, -1, defines.direction.northeast }, { 1, 0, defines.direction.east },
  { 1, 1, defines.direction.southeast }, { 0, 1, defines.direction.south }, { -1, 1, defines.direction.southwest },
  { -1, 0, defines.direction.west }, { -1, -1, defines.direction.northwest },
}

function V.init()
  storage.avatar = storage.avatar or { next_id = 1 }
  storage.executor = storage.executor or "god"
end

local function dist(a, b)
  local dx, dy = a.x - b.x, a.y - b.y
  return math.sqrt(dx * dx + dy * dy)
end

-- The way to face to walk from a to b: the nearest of the eight directions.
local function heading(a, b)
  local dx, dy = b.x - a.x, b.y - a.y
  local best, best_dot
  local len = math.sqrt(dx * dx + dy * dy)
  if len == 0 then return nil end
  for _, d in ipairs(DIRS) do
    local dl = math.sqrt(d[1] * d[1] + d[2] * d[2])
    local dot = (dx * d[1] + dy * d[2]) / (len * dl)
    if not best_dot or dot > best_dot then best, best_dot = d[3], dot end
  end
  return best
end

-- ---------------------------------------------------------------- the body

function V.body()
  local av = storage.avatar
  local p = A.any_player()
  if p and p.character and p.character.valid then
    av.body = p.character
    av.own = false
    return av.body
  end
  if av.body and av.body.valid then return av.body end
  return nil
end

-- A body of the mod's own, for a game with nobody in it. Placed like any character entering the world, at the spawn.
local function make_body(surface)
  local av = storage.avatar
  local pos = surface.find_non_colliding_position("character", { 0, 0 }, 32, 0.5) or { 0, 0 }
  av.body = surface.create_entity { name = "character", position = pos, force = "player" }
  av.own = true
  return av.body
end

local function stop_moving(body)
  if body and body.valid then
    body.walking_state = { walking = false, direction = defines.direction.north }
    body.mining_state = { mining = false }
  end
end

local function carried(body, name)
  local inv = body.get_main_inventory()
  return inv and inv.get_item_count(name) or 0
end

-- ---------------------------------------------------------------- jobs

local function finish(ok, reason, extra)
  local av = storage.avatar
  local job = av.job
  stop_moving(av.body)
  local result = extra or {}
  result.id, result.kind, result.ok, result.reason, result.ticks = job.id, job.kind, ok, reason, game.tick - job.started
  av.last = result
  av.job = nil
end

local function start(job)
  local av = storage.avatar
  job.id = av.next_id
  job.started = game.tick
  av.next_id = av.next_id + 1
  av.job = job
  return job.id
end

-- A walk, used on its own and inside build and mine. Returns "going", "arrived" or "failed", with a reason.
local function new_walk(goal, radius)
  return { goal = goal, radius = radius or 0.5, repaths = 0 }
end

local function ask_path(body, walk)
  local proto = prototypes.entity["character"]
  walk.path, walk.i = nil, nil
  walk.asked_tick = game.tick
  walk.path_id = body.surface.request_path {
    bounding_box = proto.collision_box, collision_mask = proto.collision_mask,
    start = body.position, goal = walk.goal, force = body.force, radius = walk.radius,
    pathfind_flags = { allow_destroy_friendly_entities = false, cache = false, prefer_straight_paths = true },
    can_open_gates = true, entity_to_ignore = body,
  }
end

local function step_walk(body, walk)
  if dist(body.position, walk.goal) <= walk.radius + ARRIVE then return "arrived" end
  if not walk.path then
    if not walk.path_id then
      ask_path(body, walk)
    elseif game.tick - walk.asked_tick > PATH_WAIT_TICKS then
      return "failed", "the game's pathfinder did not answer"
    end
    return "going"
  end
  local wp = walk.path[walk.i]
  while wp and dist(body.position, wp) <= ARRIVE do
    walk.i = walk.i + 1
    wp = walk.path[walk.i]
  end
  if not wp then                                           -- the path is used up; the goal check above ends the walk
    if dist(body.position, walk.goal) <= walk.radius + 1 then return "arrived" end
    walk.path_id = nil
    walk.path = nil
    return "going"
  end
  -- stuck? compare with where we were a moment ago
  if not walk.mark or game.tick - walk.mark_tick >= STUCK_TICKS then
    if walk.mark and dist(body.position, walk.mark) < 0.2 then
      walk.repaths = walk.repaths + 1
      if walk.repaths > MAX_REPATHS then return "failed", "the way is blocked: the avatar could not get past " .. math.floor(body.position.x) .. "," .. math.floor(body.position.y) end
      walk.mark = nil
      walk.path_id = nil
      walk.path = nil
      return "going"
    end
    walk.mark = { x = body.position.x, y = body.position.y }
    walk.mark_tick = game.tick
  end
  body.walking_state = { walking = true, direction = heading(body.position, wp) }
  return "going"
end

function V.on_path(event)
  local av = storage.avatar
  local job = av and av.job
  if not job then return end
  local walk = job.walk
  if not walk or walk.path_id ~= event.id then return end
  if event.try_again_later then
    walk.path_id = nil                                     -- ask again next tick
    return
  end
  if not event.path or #event.path == 0 then
    walk.no_path = true
    return
  end
  walk.path, walk.i = {}, 1
  for _, wp in ipairs(event.path) do
    walk.path[#walk.path + 1] = { x = wp.position.x, y = wp.position.y }
  end
end

local function tick_walk(body, job)
  if job.walk.no_path then return finish(false, "there is no way on foot to " .. job.walk.goal.x .. "," .. job.walk.goal.y) end
  local state, why = step_walk(body, job.walk)
  if state == "arrived" then return finish(true, nil, { x = math.floor(body.position.x), y = math.floor(body.position.y) }) end
  if state == "failed" then return finish(false, why) end
end

-- The item that places a piece, and whether it may be placed right now.
local function place_one(body, piece)
  local proto = prototypes.entity[piece.name]
  local item = proto.items_to_place_this and proto.items_to_place_this[1] and proto.items_to_place_this[1].name
  if not item then return false, "nothing the avatar can carry places a '" .. piece.name .. "'" end
  if carried(body, item) < 1 then return false, "the avatar carries no " .. item end
  local surface = body.surface
  if not surface.can_place_entity { name = piece.name, position = { piece.x, piece.y }, direction = piece.direction or 0, force = body.force, build_check_type = defines.build_check_type.manual } then
    return false, "something is in the way at " .. piece.x .. "," .. piece.y
  end
  local e = surface.create_entity { name = piece.name, position = { piece.x, piece.y }, direction = piece.direction or 0, force = body.force,
                                    type = piece.type, raise_built = true, create_build_effect_smoke = false }
  if not (e and e.valid) then return false, "the game refused the piece at " .. piece.x .. "," .. piece.y end
  body.get_main_inventory().remove { name = item, count = 1 }
  if piece.recipe then pcall(function() e.set_recipe(piece.recipe) end) end
  return true
end

-- Half the size of a piece, in tiles, plus the room a character takes.
local function half_size(piece)
  local proto = prototypes.entity[piece.name]
  return (proto.tile_width or 1) / 2 + 0.4, (proto.tile_height or 1) / 2 + 0.4
end

local function standing_on(body, piece)
  local hw, hh = half_size(piece)
  return math.abs(body.position.x - piece.x) < hw and math.abs(body.position.y - piece.y) < hh
end

-- A spot beside a piece to step to, clear of the piece itself and of the pieces still to come, within reach of it.
local function beside(body, job, piece)
  local hw, hh = half_size(piece)
  local spots = { { piece.x - hw - 1, piece.y }, { piece.x + hw + 1, piece.y }, { piece.x, piece.y - hh - 1 }, { piece.x, piece.y + hh + 1 } }
  local fallback
  for _, s in ipairs(spots) do
    local pos = { x = s[1], y = s[2] }
    if body.surface.can_place_entity { name = "character", position = pos } then
      local clear = true
      for i = job.k + 1, #job.pieces do
        if standing_on({ position = pos }, job.pieces[i]) then clear = false break end
      end
      if clear then return pos end
      fallback = fallback or pos
    end
  end
  return fallback
end

local function tick_build(body, job)
  local piece = job.pieces[job.k]
  if not piece then return finish(true, nil, { placed = job.placed, of = #job.pieces }) end
  local target = { x = piece.x, y = piece.y }
  local reach = body.build_distance
  local counts = { placed = job.placed, of = #job.pieces }
  if job.stepping then                                     -- getting out of the way of the piece about to be placed
    local state, why = step_walk(body, job.walk)
    if job.walk.no_path or state == "failed" then
      return finish(false, "the avatar is standing where the " .. piece.name .. " goes and cannot step aside" .. (why and (": " .. why) or ""), counts)
    end
    if state == "arrived" then
      job.stepping, job.walk = nil, nil
      stop_moving(body)
    end
    return
  end
  if dist(body.position, target) <= reach then
    stop_moving(body)
    job.walk = nil
    if standing_on(body, piece) and (job.steps_aside or 0) < 3 then
      local spot = beside(body, job, piece)
      if spot then
        job.steps_aside = (job.steps_aside or 0) + 1
        job.stepping = true
        job.walk = new_walk(spot, 0.3)
        return
      end
    end
    local ok, why = place_one(body, piece)
    if not ok then return finish(false, why, { placed = job.placed, of = #job.pieces, stopped_at = { name = piece.name, x = piece.x, y = piece.y } }) end
    job.placed = job.placed + 1
    job.k = job.k + 1
    job.steps_aside = 0
    return
  end
  if not job.walk then job.walk = new_walk(target, math.max(1, reach - 2)) end
  if job.walk.no_path then
    return finish(false, "there is no way on foot to within reach of " .. piece.x .. "," .. piece.y, { placed = job.placed, of = #job.pieces })
  end
  local state, why = step_walk(body, job.walk)
  if state == "failed" then return finish(false, why, { placed = job.placed, of = #job.pieces }) end
  if state == "arrived" and dist(body.position, target) > reach then
    return finish(false, "the avatar cannot get within reach of " .. piece.x .. "," .. piece.y, { placed = job.placed, of = #job.pieces })
  end
end

local function tick_mine(body, job)
  local have = carried(body, job.item)
  if have - job.had >= job.count then return finish(true, nil, { item = job.item, mined = have - job.had }) end
  if have ~= job.seen then
    job.seen = have
    job.progress_tick = game.tick
  end
  if game.tick - job.progress_tick > MINE_TIMEOUT then
    return finish(false, "nothing more could be mined at " .. job.target.x .. "," .. job.target.y, { item = job.item, mined = have - job.had })
  end
  local reach = body.resource_reach_distance
  if dist(body.position, job.target) > reach then
    if not job.walk then job.walk = new_walk(job.target, math.max(0.5, reach - 1)) end
    if job.walk.no_path then return finish(false, "there is no way on foot to " .. job.target.x .. "," .. job.target.y, { item = job.item, mined = have - job.had }) end
    local state, why = step_walk(body, job.walk)
    if state == "failed" then return finish(false, why, { item = job.item, mined = have - job.had }) end
    job.progress_tick = game.tick                          -- walking is progress
    return
  end
  job.walk = nil
  body.walking_state = { walking = false, direction = defines.direction.north }
  if body.surface.count_entities_filtered { position = job.target, radius = 1.5, name = job.entity } == 0 then
    return finish(have - job.had > 0, "there is no more " .. job.entity .. " at " .. job.target.x .. "," .. job.target.y, { item = job.item, mined = have - job.had })
  end
  body.mining_state = { mining = true, position = job.target }
end

local TICKS = { walk = tick_walk, build = tick_build, mine = tick_mine }

function V.on_tick()
  local av = storage.avatar
  if not av or not av.job then return end
  local body = V.body()
  if not body then
    av.last = { id = av.job.id, kind = av.job.kind, ok = false, reason = "the avatar's body is gone" }
    av.job = nil
    return
  end
  TICKS[av.job.kind](body, av.job)
end

local function busy()
  local job = storage.avatar.job
  if job then return { error = "the avatar is busy with a " .. job.kind .. " job (id " .. job.id .. ")", hint = "wait for it, or call avatar_stop" } end
end

local function need_body(create)
  local body = V.body()
  if body then return body end
  if create then
    local s = game.surfaces.nauvis or game.surfaces[1]
    return make_body(s)
  end
  return nil
end

-- Called by the build tool when the executor is "avatar": the checked pieces become a build job.
function V.queue_build(pieces)
  local b = busy()
  if b then return b end
  local body = need_body(true)
  -- nearest piece first, then each next piece nearest to the one before: a short walk, not the plan's own order
  local left, ordered, at = {}, {}, body.position
  for _, p in ipairs(pieces) do left[#left + 1] = p end
  while #left > 0 do
    local best, best_d
    for i, p in ipairs(left) do
      local d = dist(at, p)
      if not best_d or d < best_d then best, best_d = i, d end
    end
    local p = table.remove(left, best)
    ordered[#ordered + 1] = p
    at = { x = p.x, y = p.y }
  end
  local id = start { kind = "build", pieces = ordered, k = 1, placed = 0 }
  return { job = id, queued = #ordered }
end

-- What the avatar lacks for a list of pieces: { item = how many short }.
function V.missing_for(pieces)
  local body = need_body(false)
  local need = {}
  for _, p in pairs(pieces) do
    local proto = prototypes.entity[p.name]
    local item = proto and proto.items_to_place_this and proto.items_to_place_this[1] and proto.items_to_place_this[1].name
    if item then need[item] = (need[item] or 0) + 1 end
  end
  local short = {}
  for item, n in pairs(need) do
    local have = body and carried(body, item) or 0
    if have < n then short[item] = n - have end
  end
  return short
end

-- ---------------------------------------------------------------- tools

R.register {
  name = "avatar",
  description = "The avatar's state: where it is, what it carries, how far it can reach, what job it is doing and how its last job ended. The avatar is the character that walks and builds by hand.",
  params = {},
  run = function()
    local av = storage.avatar
    local body = V.body()
    local out = { executor = storage.executor, has_body = body ~= nil, last_job = av.last }
    if av.job then
      local j = av.job
      out.job = { id = j.id, kind = j.kind, running_ticks = game.tick - j.started,
                  placed = j.placed, of = j.pieces and #j.pieces or nil }
    end
    if body then
      out.surface, out.x, out.y = body.surface.name, math.floor(body.position.x), math.floor(body.position.y)
      out.reach = { build = body.build_distance, mine = body.resource_reach_distance, touch = body.reach_distance }
      local carries = {}
      local inv = body.get_main_inventory()
      if inv then
        for _, it in pairs(inv.get_contents()) do carries[it.name] = (carries[it.name] or 0) + it.count end
      end
      out.carries = carries
      out.crafting_queue = body.crafting_queue_size
    end
    return out
  end,
}

R.register {
  name = "avatar_walk",
  description = "For the bridge: start the avatar walking to a tile, by the game's own pathfinder. Returns a job id at once; the walk goes on over the following seconds. 'near' is how close counts as there.",
  params = {
    x = { type = "number", required = true, description = "tile x to walk to" },
    y = { type = "number", required = true, description = "tile y to walk to" },
    near = { type = "number", default = 1, description = "how many tiles from the spot count as arrived" },
  },
  run = function(a)
    local b = busy()
    if b then return b end
    local body = need_body(true)
    if not body then return { error = "there is no character to walk with" } end
    local id = start { kind = "walk", walk = new_walk({ x = a.x + 0.5, y = a.y + 0.5 }, math.max(0.5, a.near)) }
    return { job = id, from_x = math.floor(body.position.x), from_y = math.floor(body.position.y) }
  end,
}

R.register {
  name = "avatar_mine",
  description = "For the bridge: start the avatar mining by hand at a tile (ore, a tree, a rock) until it carries `count` more of what that gives. It walks there first. Returns a job id at once.",
  params = {
    x = { type = "number", required = true, description = "tile x of what to mine" },
    y = { type = "number", required = true, description = "tile y of what to mine" },
    count = { type = "number", default = 10, description = "how many to gather" },
  },
  run = function(a)
    local b = busy()
    if b then return b end
    local body = need_body(true)
    if not body then return { error = "there is no character to mine with" } end
    local target = { x = math.floor(a.x) + 0.5, y = math.floor(a.y) + 0.5 }
    local found = body.surface.find_entities_filtered { position = target, radius = 1.5, type = { "resource", "tree", "simple-entity" }, limit = 1 }[1]
    if not found then return { error = "there is nothing to mine at " .. a.x .. "," .. a.y, hint = "use 'tile' or 'map' to find ore, a tree or a rock" } end
    local product = found.prototype.mineable_properties and found.prototype.mineable_properties.products and found.prototype.mineable_properties.products[1]
    if not product then return { error = "a '" .. found.name .. "' gives nothing when mined by hand" } end
    local id = start { kind = "mine", target = target, entity = found.name, item = product.name, count = math.max(1, math.floor(a.count)),
                       had = carried(body, product.name), seen = -1, progress_tick = game.tick }
    return { job = id, mining = found.name, gives = product.name }
  end,
}

R.register {
  name = "avatar_stop",
  description = "Stop whatever the avatar is doing, at once. Use it when the player says stop.",
  params = {},
  run = function()
    local av = storage.avatar
    if not av.job then
      stop_moving(V.body())
      return { stopped = false, note = "the avatar was not doing anything" }
    end
    local kind = av.job.kind
    finish(false, "stopped on request", { placed = av.job.placed, of = av.job.pieces and #av.job.pieces or nil })
    return { stopped = true, was = kind }
  end,
}

R.register {
  name = "avatar_craft",
  description = "Have the avatar craft by hand from what it carries. Crafting takes the time the game says; check the 'avatar' tool's crafting_queue and carries to see it finish.",
  params = {
    recipe = { type = "string", required = true, description = "internal recipe name" },
    count = { type = "number", default = 1, description = "how many times to craft it" },
  },
  run = function(a)
    local body = need_body(true)
    if not body then return { error = "there is no character to craft with" } end
    local recipe = body.force.recipes[a.recipe]
    if not recipe then return { error = "there is no recipe named '" .. a.recipe .. "'", hint = "use 'search' with kind 'recipe'" } end
    if not recipe.enabled then return { error = "the recipe '" .. a.recipe .. "' is not researched yet" } end
    local want = math.max(1, math.floor(a.count))
    local can = body.get_craftable_count(a.recipe)
    if can < 1 then
      local lacks = {}
      for _, ing in pairs(recipe.ingredients) do
        if ing.type == "item" and carried(body, ing.name) < ing.amount then lacks[#lacks + 1] = ing.name end
      end
      return { error = "the avatar cannot craft '" .. a.recipe .. "' by hand from what it carries",
               hint = (#lacks > 0) and ("it lacks: " .. table.concat(lacks, ", ")) or "this recipe may need a machine or a fluid" }
    end
    local started = body.begin_crafting { recipe = a.recipe, count = math.min(want, can) }
    return { crafting = a.recipe, started = started, asked = want, note = (started < want) and "only this many could be started from what is carried" or nil }
  end,
}

R.register {
  name = "avatar_carry",
  description = "Move items between the avatar and a chest or machine it is standing next to. direction 'take' takes from the chest or machine into the avatar; 'put' puts from the avatar into it. The avatar must be within reach: walk there first.",
  params = {
    x = { type = "number", required = true, description = "tile x of the chest or machine" },
    y = { type = "number", required = true, description = "tile y of the chest or machine" },
    item = { type = "string", required = true, description = "internal item name" },
    count = { type = "number", default = 1, description = "how many" },
    direction = { type = "string", required = true, description = "'take' or 'put'" },
  },
  run = function(a)
    if a.direction ~= "take" and a.direction ~= "put" then return { error = "direction must be 'take' or 'put'" } end
    local body = need_body(false)
    if not body then return { error = "there is no character" } end
    local e = body.surface.find_entities_filtered { area = { { a.x + 0.05, a.y + 0.05 }, { a.x + 0.95, a.y + 0.95 } }, force = "player", limit = 1 }[1]
    if not e then return { error = "nothing of ours stands at " .. a.x .. "," .. a.y } end
    if dist(body.position, e.position) > body.reach_distance then
      return { error = "the " .. e.name .. " is out of reach", hint = "walk to within " .. body.reach_distance .. " tiles of it first" }
    end
    local n = math.max(1, math.floor(a.count))
    local from, to = e, body
    if a.direction == "put" then from, to = body, e end
    local removed = from.remove_item { name = a.item, count = n }
    if removed == 0 then return { error = "there is no " .. a.item .. " to " .. a.direction, moved = 0 } end
    local inserted = to.insert { name = a.item, count = removed }
    if inserted < removed then from.insert { name = a.item, count = removed - inserted } end      -- what did not fit goes back
    return { moved = inserted, item = a.item, direction = a.direction, with = e.name }
  end,
}

R.register {
  name = "set_executor",
  description = "For the run's operator, not the model: how things get built. 'god' places pieces freely once researched; 'avatar' makes the character walk to each piece and place it from what it carries.",
  params = {
    mode = { type = "string", required = true, description = "'god' or 'avatar'" },
  },
  run = function(a)
    if a.mode ~= "god" and a.mode ~= "avatar" then return { error = "mode must be 'god' or 'avatar'" } end
    storage.executor = a.mode
    return { executor = a.mode }
  end,
}

return V
