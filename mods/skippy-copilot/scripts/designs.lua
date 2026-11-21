-- Designs: blueprints as the source of truth for what stands on the map (the Captain, 2026-11-20). A design is kept and
-- improved in the mod's own blueprint library, never by editing the map; the map only ever receives a version of it.
--   the library      = the repository: every design has numbered versions; each save or edit is a new version with a note
--   design_deploy    = a deployment: a version placed at a spot, as ghosts the robots build (the mod remembers where)
--   design_redeploy  = moving a deployment to another version. When only building names or recipes changed, the pieces
--                      are given upgrade orders (the upgrade planner's mechanism) and recipes are set. When the layout
--                      changed, everything of ours inside the deployment's footprint is marked for deconstruction first
--                      and the new version's ghosts are placed over it: the robots clear and rebuild, so no old belt,
--                      pipe or inserter is left standing in a gap the new layout leaves (the Captain's warning: placing
--                      a blueprint over an older copy leaves such pieces behind)
--   design_undeploy  = taking a deployment away again, by deconstruction orders
-- Everything placed carries tags (design, version, deployment), which what_is reads back. Nothing here spawns items:
-- ghosts and orders only, except build_now in 'builds on its own' mode, which the free-placement allowance governs.
local R = require("scripts.registry")
local G = require("scripts.grid")
local V = require("scripts.avatar")
local AL = require("scripts.allowances")
local B = require("scripts.build")
local P = require("scripts.places")

local D = {}
local MAX_AREA = 200
local DIRS = { north = 0, east = 4, south = 8, west = 12 }
local DIR_NAMES = { [0] = "north", [4] = "east", [8] = "south", [12] = "west" }
local NOT_CLEARED = { character = true, resource = true, ["entity-ghost"] = true, ["tile-ghost"] = true, ["item-request-proxy"] = true,
                      tree = true, ["simple-entity"] = true, cliff = true, fish = true, corpse = true, ["item-entity"] = true }

-- ---------------------------------------------------------------- the library
function D.init()
  storage.designs = storage.designs or {}                  -- name -> { description, versions = { [v] = { slot, kind, note, tick, replaced, recipes } }, latest }
  storage.deployments = storage.deployments or {}          -- id -> { id, design, version, surface, x, y, dir, shift, box, tick, at }
  storage.deployment_next = storage.deployment_next or 1
  storage.design_marks = storage.design_marks or {}        -- unit_number -> deployment id, for pieces built from our ghosts
  if not storage.design_inventory or not storage.design_inventory.valid then storage.design_inventory = game.create_inventory(64) end
end

local function inv()
  if not storage.design_inventory then D.init() end
  return storage.design_inventory
end

local function free_slot()
  local i = inv()
  for n = 1, #i do
    if not i[n].valid_for_read then return n end
  end
  local n = #i + 1
  i.resize(#i * 2)
  return n
end

local function design_of(name)
  local d = storage.designs[name]
  if not d then
    local names = {}
    for n in pairs(storage.designs) do names[#names + 1] = n end
    table.sort(names)
    return nil, { error = "there is no design named '" .. tostring(name) .. "'", hint = (#names > 0) and ("designs: " .. table.concat(names, ", ")) or "the library is empty: design_save captures one" }
  end
  return d
end

local function stack_of(d, version)
  local v = d.versions[version or d.latest]
  if not v then return nil, { error = "that design has no version " .. tostring(version), hint = "versions 1 to " .. d.latest } end
  return inv()[v.slot], v
end

-- The pieces of a stack: { name, x, y, direction, recipe, tags }, positions as the blueprint holds them.
local function pieces(stack)
  local out = {}
  for _, e in pairs(stack.get_blueprint_entities() or {}) do
    out[#out + 1] = { name = e.name, x = e.position.x, y = e.position.y, direction = e.direction or 0, recipe = e.recipe, tags = e.tags }
  end
  return out
end

local ROT = {
  [0] = function(x, y) return x, y end,
  [4] = function(x, y) return -y, x end,
  [8] = function(x, y) return -x, -y end,
  [12] = function(x, y) return y, -x end,
}

local function size_of(name, dir)
  local p = prototypes.entity[name]
  local w, h = (p and p.tile_width) or 1, (p and p.tile_height) or 1
  if dir == 4 or dir == 12 then w, h = h, w end
  return w, h
end

-- Where a version's pieces stand when placed at x,y turned by dir (and moved by the shift the game applied).
local function placed(list, x, y, dir, shift)
  local out = {}
  local sx, sy = shift and shift.x or 0, shift and shift.y or 0
  for _, p in ipairs(list) do
    local rx, ry = ROT[dir](p.x, p.y)
    local d = (p.direction + dir) % 16
    out[#out + 1] = { name = p.name, x = x + rx + sx, y = y + ry + sy, direction = d, recipe = p.recipe, tags = p.tags }
  end
  return out
end

-- The tiles a placed list covers, as an area.
local function box_of(list)
  local x0, y0, x1, y1
  for _, p in ipairs(list) do
    local w, h = size_of(p.name, p.direction)
    local ax, ay, bx, by = p.x - w / 2, p.y - h / 2, p.x + w / 2, p.y + h / 2
    x0, y0 = math.min(x0 or ax, ax), math.min(y0 or ay, ay)
    x1, y1 = math.max(x1 or bx, bx), math.max(y1 or by, by)
  end
  if not x0 then return nil end
  return { { x0, y0 }, { x1, y1 } }
end

local function union(a, b)
  if not a then return b end
  if not b then return a end
  return { { math.min(a[1][1], b[1][1]), math.min(a[1][2], b[1][2]) }, { math.max(a[2][1], b[2][1]), math.max(a[2][2], b[2][2]) } }
end

local function shrink(area)                                -- a hair inside, so the neighbours just outside are not caught
  return { { area[1][1] + 0.1, area[1][2] + 0.1 }, { area[2][1] - 0.1, area[2][2] - 0.1 } }
end

local function cost(stack)
  local out = {}
  local c = stack.cost_to_build or {}
  for k, v in pairs(c) do
    if type(v) == "table" then out[#out + 1] = { item = v.name, count = v.count, quality = v.quality }
    else out[#out + 1] = { item = k, count = v } end
  end
  table.sort(out, function(a, b) return a.count > b.count end)
  return out
end

local function size_text(list)
  local b = box_of(list)
  if not b then return "0x0" end
  return math.floor(b[2][1] - b[1][1] + 0.5) .. "x" .. math.floor(b[2][2] - b[1][2] + 0.5)
end

local function behind(dep)
  local d = storage.designs[dep.design]
  return d and dep.version < d.latest or false
end

local function count_deployments(name)
  local n, old = 0, 0
  for _, dep in pairs(storage.deployments) do
    if dep.design == name then
      n = n + 1
      if behind(dep) then old = old + 1 end
    end
  end
  return n, old
end

-- A new version of `name` from a stack already filled. -> the version number.
local function commit(name, stack_slot, kind, note, description, extra)
  local d = storage.designs[name]
  if not d then
    d = { description = description or "", versions = {}, latest = 0, created = game.tick }
    storage.designs[name] = d
  end
  if description and description ~= "" then d.description = description end
  d.latest = d.latest + 1
  local v = { slot = stack_slot, kind = kind, note = note or "", tick = game.tick }
  for k, x in pairs(extra or {}) do v[k] = x end
  d.versions[d.latest] = v
  local stack = inv()[stack_slot]
  stack.label = name .. " v" .. d.latest
  pcall(function() stack.blueprint_description = d.description end)
  return d.latest
end

-- ---------------------------------------------------------------- reading the library
R.register {
  name = "designs",
  description = "The design library: our blueprints, the source every build is deployed from, with each one's description, latest version, size, cost and deployments on the map. Choose a design here before laying anything out by hand. With a name: its full cost and version history.",
  params = {
    name = { type = "string", description = "one design; leave out for all" },
  },
  run = function(a)
    local out = {}
    local names = {}
    for n in pairs(storage.designs) do
      if not a.name or n == a.name then names[#names + 1] = n end
    end
    table.sort(names)
    if a.name and #names == 0 then local _, err = design_of(a.name) return err end
    for _, n in ipairs(names) do
      local d = storage.designs[n]
      local stack = stack_of(d)
      local list = pieces(stack)
      local deployed, old = count_deployments(n)
      local c = cost(stack)
      if not a.name then
        local short = {}
        for i = 1, math.min(6, #c) do short[i] = c[i] end
        c = short
      end
      local row = { name = n, description = d.description, version = d.latest, pieces = #list, size = size_text(list),
                    cost = c, deployments = deployed, deployments_behind = old }
      if a.name then                                       -- the log, newest first
        row.versions = {}
        for v = d.latest, 1, -1 do
          local x = d.versions[v]
          row.versions[#row.versions + 1] = { version = v, kind = x.kind, note = x.note, tick = x.tick, replaced = x.replaced, recipes = x.recipes }
        end
      end
      out[#out + 1] = row
    end
    return { designs = out, hint = (#out == 0) and "the library is empty: design_save writes or captures one" or nil }
  end,
}

-- ---------------------------------------------------------------- changing the library
R.register {
  name = "design_save",
  description = "Keep a design choice so it outlives this chat: write a design as pieces (nothing is built), capture an area of the map, or import a blueprint string. An existing name gets a new version. Describe it so a later reader can choose it: what it does, inputs and outputs, where it fits, what was learned.",
  params = {
    name = { type = "string", required = true, description = "short and plain, such as 'smelter-row-48'" },
    description = { type = "string", description = "required for a new design" },
    note = { type = "string", description = "what this version changes" },
    pieces = { type = "table", list = "object", description = "the pieces {name, x, y, direction?, recipe?} by their centres" },
    x = { type = "number", description = "or capture: the area's left column" },
    y = { type = "number", description = "its top row" },
    width = { type = "number", description = "columns, at most 200" },
    height = { type = "number", description = "rows, at most 200" },
    surface = { type = "string", description = "surface name; leave out for where the player is" },
    string = { type = "string", description = "or a blueprint string to import" },
  },
  run = function(a)
    local name = string.match(a.name, "^%s*(.-)%s*$")
    if name == "" then return { error = "a design needs a name" } end
    if not storage.designs[name] and (not a.description or a.description == "") then
      return { error = "a new design needs a description", hint = "say what it makes or does and when to use it" }
    end
    local slot = free_slot()
    local stack = inv()[slot]
    stack.set_stack { name = "blueprint" }
    local kind
    if a.string then
      local r = stack.import_stack(a.string)
      if r == -1 or not stack.valid_for_read or not stack.is_blueprint or not stack.is_blueprint_setup() then
        stack.clear()
        return { error = "that string is not a blueprint the game can read", hint = "a single blueprint, not a book or a planner" }
      end
      kind = "import"
    elseif a.pieces then
      local list = {}
      for _, p in pairs(a.pieces) do list[#list + 1] = p end
      if #list == 0 then stack.clear() return { error = "the list of pieces is empty" } end
      local sx, sy = 0, 0
      for _, p in ipairs(list) do
        if type(p.name) ~= "string" or not prototypes.entity[p.name] then stack.clear() return { error = "there is no building named '" .. tostring(p.name) .. "'" } end
        if type(p.x) ~= "number" or type(p.y) ~= "number" then stack.clear() return { error = "every piece needs x and y" } end
        sx, sy = sx + p.x, sy + p.y
      end
      local cx, cy = math.floor(sx / #list), math.floor(sy / #list)        -- a whole-tile centre keeps every piece on its grid
      local ents = {}
      for i, p in ipairs(list) do
        local dir = type(p.direction) == "string" and DIRS[p.direction] or p.direction or 0
        ents[i] = { entity_number = i, name = p.name, position = { x = p.x - cx, y = p.y - cy }, direction = dir, recipe = p.recipe }
      end
      stack.set_blueprint_entities(ents)
      if not stack.is_blueprint_setup() then stack.clear() return { error = "the game did not accept those pieces as a blueprint" } end
      kind = "written"
    else
      if not (a.x and a.y and a.width and a.height) then
        stack.clear()
        return { error = "give an area (x, y, width, height) to capture, a list of pieces, or a blueprint string" }
      end
      local s, err = G.surface_of(a.surface)
      if not s then stack.clear() return err end
      local w, h = math.floor(a.width), math.floor(a.height)
      if w < 1 or h < 1 or w > MAX_AREA or h > MAX_AREA then stack.clear() return { error = "width and height must be between 1 and " .. MAX_AREA } end
      stack.create_blueprint { surface = s, force = game.forces.player, area = { { a.x, a.y }, { a.x + w, a.y + h } },
                               always_include_tiles = false, include_entities = true, include_modules = true,
                               include_station_names = true, include_trains = false, include_fuel = false }
      if not stack.is_blueprint_setup() then
        stack.clear()
        return { error = "there is nothing of ours in that area to capture" }
      end
      kind = "capture"
    end
    local v = commit(name, slot, kind, a.note, a.description)
    local list = pieces(stack)
    return { name = name, version = v, kind = kind, pieces = #list, size = size_text(list),
             note = (v > 1) and "a new version; deployments on older versions are moved to it with design_redeploy" or nil }
  end,
}

R.register {
  name = "design_edit",
  description = "Improve a design in the library, not on the map: swap buildings for others of the same size (a faster belt or machine) and swap recipes. Makes a new version, which design_redeploy rolls out by upgrade orders, no rebuild.",
  params = {
    name = { type = "string", required = true, description = "the design" },
    replace = { type = "table", description = "{old building = new building}" },
    recipes = { type = "table", description = "{old recipe = new recipe}" },
    description = { type = "string", description = "a new description" },
    note = { type = "string", required = true, description = "what changes and why" },
  },
  run = function(a)
    local d, err = design_of(a.name)
    if not d then return err end
    local replace, recipes = a.replace or {}, a.recipes or {}
    for from, to in pairs(replace) do
      local pf, pt = prototypes.entity[from], prototypes.entity[to]
      if not pf or not pt then return { error = "there is no building named '" .. tostring(pf and to or from) .. "'" } end
      if (pf.tile_width or 1) ~= (pt.tile_width or 1) or (pf.tile_height or 1) ~= (pt.tile_height or 1) then
        return { error = "'" .. from .. "' and '" .. to .. "' are not the same size", hint = "a different size changes the layout: edit it on a test spot and design_save it as a new version" }
      end
    end
    for _, to in pairs(recipes) do
      if not prototypes.recipe[to] then return { error = "there is no recipe named '" .. tostring(to) .. "'" } end
    end
    local old = stack_of(d)
    local ents = old.get_blueprint_entities() or {}
    local swapped, reset = 0, 0
    for _, e in pairs(ents) do
      if replace[e.name] then e.name = replace[e.name] swapped = swapped + 1 end
      if e.recipe and recipes[e.recipe] then e.recipe = recipes[e.recipe] reset = reset + 1 end
    end
    if swapped + reset == 0 and not a.description then return { error = "nothing in the design matches what is to be swapped" } end
    local slot = free_slot()
    local stack = inv()[slot]
    stack.set_stack(old)
    stack.set_blueprint_entities(ents)
    local v = commit(a.name, slot, "edit", a.note, a.description, { replaced = next(replace) and replace or nil, recipes = next(recipes) and recipes or nil })
    local deployed, behind_n = count_deployments(a.name)
    return { name = a.name, version = v, buildings_swapped = swapped, recipes_swapped = reset, deployments_behind = behind_n,
             note = (deployed > 0) and "the map is unchanged; design_redeploy rolls this version out" or nil }
  end,
}

R.register {
  name = "design_export",
  description = "A design's blueprint string, for the player's own library.",
  params = {
    name = { type = "string", required = true, description = "the design" },
    version = { type = "number", description = "which version; leave out for the latest" },
  },
  run = function(a)
    local d, err = design_of(a.name)
    if not d then return err end
    local stack, e2 = stack_of(d, a.version)
    if not stack then return e2 end
    return { name = a.name, version = a.version or d.latest, string = stack.export_stack() }
  end,
}

-- ---------------------------------------------------------------- deploying
local function where(a)
  if a.at then
    local p, err = P.resolve(a.at, a.surface)
    if not p then return nil, err end
    return p.surface, p.x, p.y, p.name
  end
  if not (a.x and a.y) then return nil, { error = "say where: a place name (at) or x and y" } end
  local s, err = G.surface_of(a.surface)
  if not s then return nil, err end
  return s, a.x, a.y
end

local function in_coverage(s, f, x, y)
  if not s.find_logistic_network_by_position then return true end
  local n = s.find_logistic_network_by_position({ x, y }, f)
  return n ~= nil
end

-- Place a version as ghosts; tag them; return the ghosts and the shift the game applied to our expected positions.
local function place_ghosts(s, f, stack, x, y, dir, expected, tags)
  local ghosts = stack.build_blueprint { surface = s, force = f, position = { x, y }, direction = dir,
                                         build_mode = defines.build_mode and defines.build_mode.forced or nil, skip_fog_of_war = false, raise_built = true } or {}
  local gx, gy, ex, ey, n = 0, 0, 0, 0, 0
  local by_name = {}
  for _, p in ipairs(expected) do
    local same = by_name[p.name] or {}
    same[#same + 1] = p
    by_name[p.name] = same
  end
  local used = {}
  for _, g in pairs(ghosts) do
    if g.valid and g.type == "entity-ghost" then
      local t = g.tags or {}
      for k, v in pairs(tags) do t[k] = v end
      g.tags = t
      local best, bd
      for _, p in ipairs(by_name[g.ghost_name] or {}) do
        if not used[p] then
          local dd = (p.x - g.position.x) ^ 2 + (p.y - g.position.y) ^ 2
          if not bd or dd < bd then best, bd = p, dd end
        end
      end
      if best and bd < 4 then
        used[best] = true
        gx, gy, ex, ey, n = gx + g.position.x, gy + g.position.y, ex + best.x, ey + best.y, n + 1
      end
    end
  end
  local shift = (n > 0) and { x = (gx - ex) / n, y = (gy - ey) / n } or { x = 0, y = 0 }
  return ghosts, shift
end

local function check(s, f, list)
  local failed, ok = {}, 0
  local known = {}
  for _, p in ipairs(list) do
    local why
    local proto = prototypes.entity[p.name]
    if not proto then why = "the game has no building named '" .. p.name .. "'"
    else
      if known[p.name] == nil then known[p.name] = B.researched(f, proto) end
      if not known[p.name] then why = "not researched yet"
      elseif not s.can_place_entity { name = p.name, position = { p.x, p.y }, direction = p.direction, force = f,
                                      build_check_type = defines.build_check_type.blueprint_ghost or defines.build_check_type.manual, forced = true } then
        why = "something is in the way, or the ground does not allow it"
      end
    end
    if why then
      if #failed < 15 then failed[#failed + 1] = { name = p.name, x = p.x, y = p.y, why = why } end
    else
      ok = ok + 1
    end
  end
  return ok, failed
end

-- One copy of a version at x,y turned by dir: checked, and unless a dry run, placed as ghosts and remembered.
-- -> { design, version, surface, x, y, facing, pieces, would_place, failed?, outside_roboport_coverage?, deployment?, ghosts?, built_now? }
local function deploy_at(s, f, name, version, stack, x, y, dir, opts)
  local expected = placed(pieces(stack), x, y, dir)
  local ok, failed = check(s, f, expected)
  local outside = 0
  for _, p in ipairs(expected) do
    if not in_coverage(s, f, p.x, p.y) then outside = outside + 1 end
  end
  local out = { design = name, version = version, surface = s.name, x = math.floor(x), y = math.floor(y), facing = DIR_NAMES[dir],
                pieces = #expected, would_place = ok, failed = (#failed > 0) and failed or nil, outside_roboport_coverage = (outside > 0) and outside or nil }
  if opts.dry_run or #failed > 0 then return out end
  local id = storage.deployment_next
  storage.deployment_next = id + 1
  local ghosts, shift = place_ghosts(s, f, stack, x, y, dir, expected, { skippy_design = name, skippy_version = version, skippy_deployment = id })
  local n_ghosts, built = 0, 0
  for _, g in pairs(ghosts) do
    if g.valid and g.type == "entity-ghost" then n_ghosts = n_ghosts + 1 end
  end
  if n_ghosts == 0 and #expected > 0 then return { error = "the game placed no ghosts there", hint = "dry-run again: something may have moved in" } end
  storage.deployments[id] = { id = id, design = name, version = version, surface = s.name, x = x, y = y, dir = dir, shift = shift,
                              box = box_of(placed(pieces(stack), x, y, dir, shift)), tick = game.tick, at = opts.at }
  if opts.build_now then
    for _, g in pairs(ghosts) do
      if g.valid and g.type == "entity-ghost" then
        local _, e = g.revive { raise_revive = true }
        if e and e.valid then
          built = built + 1
          if e.unit_number then storage.design_marks[e.unit_number] = id end
        end
      end
    end
  end
  out.would_place = nil
  out.deployment = id
  out.ghosts = n_ghosts - built
  out.built_now = (built > 0) and built or nil
  if opts.build_now and built < n_ghosts then           -- found live: a revive waits on what is under it, so say what that is
    local tiles = 0
    for _, g in pairs(ghosts) do
      if g.valid and g.type == "tile-ghost" then tiles = tiles + 1 end
    end
    local b = storage.deployments[id].box
    local marked = s.count_entities_filtered { area = b, type = { "tree", "simple-entity", "cliff" }, to_be_deconstructed = true }
    local why = {}
    if tiles > 0 then why[#why + 1] = tiles .. " tiles of ground (landfill over water, or the design's floor) must be laid first" end
    if marked > 0 then why[#why + 1] = marked .. " trees or rocks under them are marked for deconstruction" end
    out.waiting = (n_ghosts - built) .. " pieces stay ghosts: " .. ((#why > 0) and table.concat(why, "; ") or "the game would not build them yet")
      .. ". Robots or the player clear and lay that, then the ghosts can be built"
  end
  return out
end

R.register {
  name = "design_deploy",
  description = "Deploy a design at a spot as ghosts the robots build (ghost_requests brings the goods). Dry run unless dry_run is false. The deployment is remembered, so later versions roll out to it with design_redeploy.",
  params = {
    name = { type = "string", required = true, description = "the design" },
    version = { type = "number", description = "leave out for the latest" },
    at = { type = "string", description = "a place name: the design's centre goes there" },
    x = { type = "number", description = "or the centre's x" },
    y = { type = "number", description = "and y" },
    facing = { type = "string", default = "north", description = "north (as saved), east, south or west" },
    surface = { type = "string", description = "surface name; leave out for where the player is" },
    dry_run = { type = "boolean", default = true, description = "true to only check" },
    build_now = { type = "boolean", default = false, description = "place at once, not as ghosts ('builds on its own' mode only)" },
  },
  run = function(a)
    local d, err = design_of(a.name)
    if not d then return err end
    local version = a.version or d.latest
    local stack, e2 = stack_of(d, version)
    if not stack then return e2 end
    local dir = DIRS[a.facing]
    if not dir then return { error = "facing must be north, east, south or west" } end
    local s, x, y, at = where(a)
    if not s then return x end
    local f = game.forces.player
    if a.build_now and (V.executor() ~= "god" or not AL.on("free-placement")) then
      return { error = "build_now needs the 'builds on its own' mode and the free-placement allowance", hint = "leave build_now out: the robots build the ghosts" }
    end
    local base = deploy_at(s, f, a.name, version, stack, x, y, dir, { dry_run = a.dry_run, build_now = a.build_now, at = at })
    if base.error then return base end
    if a.dry_run then
      base.note = base.failed and "fix these before deploying (another spot, or another facing)" or "every piece can be placed"
    elseif base.failed then
      base.note = "nothing was placed because some pieces could not be"
    else
      base.note = a.build_now and "placed" or "ghosts placed: the robots build them; ghost_requests brings what the network lacks"
    end
    return base
  end,
}

R.register {
  name = "design_tile",
  description = "Repeat one design over an area or along a line, as a player drags a blueprint: roboport and power grids, pole lines, walls, solar fields. Copies sit on a grid fixed to the map, so separate calls line up; copies that collide are skipped. Each copy is a deployment. Dry run unless dry_run is false.",
  params = {
    name = { type = "string", required = true, description = "the design: one cell or segment" },
    version = { type = "number", description = "leave out for the latest" },
    x = { type = "number", required = true, description = "the area's left column" },
    y = { type = "number", required = true, description = "its top row" },
    width = { type = "number", required = true, description = "columns to cover" },
    height = { type = "number", required = true, description = "rows to cover" },
    step_x = { type = "number", description = "tiles between copies across; default the design's width" },
    step_y = { type = "number", description = "tiles between copies down; default its height" },
    facing = { type = "string", default = "north", description = "north, east, south or west" },
    surface = { type = "string", description = "surface name" },
    dry_run = { type = "boolean", default = true, description = "true to only check" },
  },
  run = function(a)
    local d, err = design_of(a.name)
    if not d then return err end
    local version = a.version or d.latest
    local stack, e2 = stack_of(d, version)
    if not stack then return e2 end
    local dir = DIRS[a.facing]
    if not dir then return { error = "facing must be north, east, south or west" } end
    local s, e3 = G.surface_of(a.surface)
    if not s then return e3 end
    local f = game.forces.player
    local shape = box_of(placed(pieces(stack), 0, 0, dir))
    if not shape then return { error = "that design is empty" } end
    local w, h = shape[2][1] - shape[1][1], shape[2][2] - shape[1][2]
    local sx, sy = math.ceil(a.step_x or w), math.ceil(a.step_y or h)
    if sx < 1 or sy < 1 then return { error = "the steps must be at least 1" } end
    local x0, y0 = math.ceil(a.x / sx) * sx, math.ceil(a.y / sy) * sy           -- grid fixed to the map
    local copies = {}
    local cx = x0
    while cx + w <= a.x + a.width + 0.01 do
      local cy = y0
      while cy + h <= a.y + a.height + 0.01 do
        copies[#copies + 1] = { cx - shape[1][1], cy - shape[1][2] }            -- the design's centre for a copy whose corner is cx,cy
        cy = cy + sy
      end
      cx = cx + sx
    end
    if #copies == 0 then return { error = "the area is smaller than one copy (" .. math.ceil(w) .. "x" .. math.ceil(h) .. ")" } end
    if #copies > 100 then return { error = #copies .. " copies is too many for one call (at most 100)", hint = "tile it in parts" } end
    local placed_ids, skipped, outside, ghosts = {}, {}, 0, 0
    for _, c in ipairs(copies) do
      local r = deploy_at(s, f, a.name, version, stack, c[1], c[2], dir, { dry_run = a.dry_run })
      outside = outside + (r.outside_roboport_coverage or 0)
      if r.failed then
        if #skipped < 15 then skipped[#skipped + 1] = { x = math.floor(c[1]), y = math.floor(c[2]), why = r.failed[1].name .. ": " .. r.failed[1].why } end
      elseif r.error then
        if #skipped < 15 then skipped[#skipped + 1] = { x = math.floor(c[1]), y = math.floor(c[2]), why = r.error } end
      else
        placed_ids[#placed_ids + 1] = r.deployment or true
        ghosts = ghosts + (r.ghosts or 0)
      end
    end
    local out = { design = a.name, version = version, copies = #copies, step_x = sx, step_y = sy,
                  [a.dry_run and "would_place" or "placed"] = #placed_ids, skipped = (#skipped > 0) and skipped or nil,
                  skipped_count = #copies - #placed_ids, outside_roboport_coverage = (outside > 0) and outside or nil }
    if not a.dry_run then
      out.deployments = placed_ids
      out.ghosts = ghosts
      out.note = "ghosts placed: the robots build them"
    else
      out.note = "dry run: nothing was placed; copies that collide would be skipped"
    end
    return out
  end,
}

local function dep_of(id)
  local dep = storage.deployments[math.floor(tonumber(id) or -1)]
  if not dep then return nil, { error = "there is no deployment " .. tostring(id), hint = "the 'deployments' tool lists them" } end
  return dep
end

R.register {
  name = "deployments",
  description = "Where the designs stand on the map: each deployment's id, design, version, spot, and whether a newer version exists.",
  params = { name = { type = "string", description = "only this design's" } },
  run = function(a)
    local out = {}
    for _, dep in pairs(storage.deployments) do
      if not a.name or dep.design == a.name then
        local d = storage.designs[dep.design]
        out[#out + 1] = { deployment = dep.id, design = dep.design, version = dep.version, latest = d and d.latest or nil, behind = behind(dep),
                          surface = dep.surface, x = math.floor(dep.x), y = math.floor(dep.y), facing = DIR_NAMES[dep.dir], at = dep.at }
      end
    end
    table.sort(out, function(p, q) return p.deployment < q.deployment end)
    return { deployments = out }
  end,
}

-- What a move from version `from` to `to` needs: "upgrade" (only names and recipes changed) or "rebuild"; and the swaps.
local function plan_move(d, from, to)
  if to < from then return "rebuild" end
  local names, recipes = {}, {}
  for v = from + 1, to do
    local x = d.versions[v]
    if x.kind ~= "edit" then return "rebuild" end
    for old, new in pairs(x.replaced or {}) do
      local hit = false
      for k, cur in pairs(names) do
        if cur == old then names[k] = new hit = true end
      end
      if not names[old] and not hit then names[old] = new end
    end
    for old, new in pairs(x.recipes or {}) do
      local hit = false
      for k, cur in pairs(recipes) do
        if cur == old then recipes[k] = new hit = true end
      end
      if not recipes[old] and not hit then recipes[old] = new end
    end
  end
  return "upgrade", names, recipes
end

-- The entity standing for a placed piece: the building of that name, or its ghost.
local function standing(s, f, p)
  for _, e in pairs(s.find_entities_filtered { position = { p.x, p.y }, radius = 0.75, force = f }) do
    if e.valid and (e.name == p.name or (e.type == "entity-ghost" and e.ghost_name == p.name)) then return e end
  end
end

-- Everything of ours inside an area that a rebuild clears: buildings get deconstruction orders, old ghosts go.
local function in_the_way(s, f, area)
  local builds, ghosts = {}, {}
  for _, e in pairs(s.find_entities_filtered { area = shrink(area), force = f }) do
    if e.valid then
      if e.type == "entity-ghost" or e.type == "tile-ghost" then ghosts[#ghosts + 1] = e
      elseif not NOT_CLEARED[e.type] then builds[#builds + 1] = e end
    end
  end
  return builds, ghosts
end

local function tally(list)
  local by = {}
  for _, e in ipairs(list) do
    local n = (e.type == "entity-ghost") and ("ghost of " .. e.ghost_name) or e.name
    by[n] = (by[n] or 0) + 1
  end
  return by
end

R.register {
  name = "design_redeploy",
  description = "Move a deployment to another version (latest unless told; older is a rollback). Swapped buildings or recipes get upgrade orders. A changed layout is cleared whole (everything of ours in its footprint marked for deconstruction) and rebuilt from the new ghosts, so nothing old is left in the gaps. Dry run unless dry_run is false.",
  params = {
    deployment = { type = "number", required = true, description = "the deployment's id" },
    version = { type = "number", description = "leave out for the latest" },
    rebuild = { type = "boolean", default = false, description = "clear and rebuild even when upgrades would do" },
    dry_run = { type = "boolean", default = true, description = "true to only say what would happen" },
  },
  run = function(a)
    local dep, err = dep_of(a.deployment)
    if not dep then return err end
    local d, e2 = design_of(dep.design)
    if not d then return e2 end
    local to = a.version or d.latest
    local new_stack, e3 = stack_of(d, to)
    if not new_stack then return e3 end
    if to == dep.version and not a.rebuild then return { deployment = dep.id, version = to, note = "it is already on that version" } end
    local s = game.surfaces[dep.surface]
    if not s then return { error = "its surface '" .. dep.surface .. "' is gone" } end
    local f = game.forces.player
    local how, names, recipes = plan_move(d, dep.version, to)
    if a.rebuild then how = "rebuild" end
    local out = { deployment = dep.id, design = dep.design, from_version = dep.version, to_version = to, how = how }
    if how == "upgrade" then
      local old = placed(pieces(stack_of(d, dep.version)), dep.x, dep.y, dep.dir, dep.shift)
      local upgrades, reset, missing = 0, 0, 0
      local orders = {}
      for _, p in ipairs(old) do
        local e = standing(s, f, p)
        if not e then missing = missing + 1
        else
          if names[p.name] then orders[#orders + 1] = { e = e, to = names[p.name] } end
          if p.recipe and recipes[p.recipe] then orders[#orders + 1] = { e = e, recipe = recipes[p.recipe] } end
        end
      end
      for _, o in ipairs(orders) do
        if o.to then upgrades = upgrades + 1 else reset = reset + 1 end
      end
      out.upgrade_orders, out.recipes_set, out.pieces_missing = upgrades, reset, (missing > 0) and missing or nil
      if a.dry_run then
        out.note = "dry run: nothing was ordered" .. ((missing > 0) and "; some pieces are not where the design has them (rebuild true clears and rebuilds)" or "")
        return out
      end
      for _, o in ipairs(orders) do
        if o.to then
          if o.e.type == "entity-ghost" then
            local g = o.e
            local pos, dirn, tags = g.position, g.direction, g.tags
            g.destroy()
            local ng = s.create_entity { name = "entity-ghost", inner_name = o.to, position = pos, direction = dirn, force = f }
            if ng then ng.tags = tags end
          else
            o.e.order_upgrade { force = f, target = { name = o.to } }
          end
        else
          pcall(function() o.e.set_recipe(o.recipe) end)
        end
      end
      local planner = inv()[free_slot()]
      planner.set_stack { name = "upgrade-planner" }
      local i = 0
      for from, toname in pairs(names) do
        i = i + 1
        planner.set_mapper(i, "from", { type = "entity", name = from })
        planner.set_mapper(i, "to", { type = "entity", name = toname })
      end
      out.planner = (i > 0) and planner.export_stack() or nil
      planner.clear()
      dep.version = to
      out.note = "upgrade orders given: the robots swap the pieces. The planner string does the same by hand anywhere."
      return out
    end
    local new_list = placed(pieces(new_stack), dep.x, dep.y, dep.dir, dep.shift)
    local area = union(dep.box, box_of(new_list))
    local builds, ghosts = in_the_way(s, f, area)
    out.deconstruct = #builds
    out.old_ghosts_removed = #ghosts
    out.cleared = tally(builds)
    out.new_pieces = #new_list
    if a.dry_run then
      out.note = "dry run: everything listed would be marked for deconstruction and the new version's ghosts placed over it"
      return out
    end
    for _, g in ipairs(ghosts) do g.destroy() end
    for _, e in ipairs(builds) do e.order_deconstruction(f) end
    local placed_ghosts, shift = place_ghosts(s, f, new_stack, dep.x, dep.y, dep.dir, placed(pieces(new_stack), dep.x, dep.y, dep.dir),
                                              { skippy_design = dep.design, skippy_version = to, skippy_deployment = dep.id })
    local n = 0
    for _, g in pairs(placed_ghosts) do
      if g.valid and g.type == "entity-ghost" then n = n + 1 end
    end
    dep.version, dep.shift = to, shift
    dep.box = box_of(placed(pieces(new_stack), dep.x, dep.y, dep.dir, shift))
    dep.tick = game.tick
    out.ghosts = n
    out.note = "marked for deconstruction and the new ghosts placed: the robots clear and rebuild it. Run ghost_requests if the network lacks goods."
    return out
  end,
}

R.register {
  name = "design_undeploy",
  description = "Take a deployment off the map: everything of ours in its footprint is marked for deconstruction. The design stays in the library. Dry run unless dry_run is false.",
  params = {
    deployment = { type = "number", required = true, description = "the deployment's id" },
    dry_run = { type = "boolean", default = true, description = "true to only list" },
  },
  run = function(a)
    local dep, err = dep_of(a.deployment)
    if not dep then return err end
    local s = game.surfaces[dep.surface]
    local f = game.forces.player
    local builds, ghosts = {}, {}
    if s and dep.box then builds, ghosts = in_the_way(s, f, dep.box) end
    local out = { deployment = dep.id, design = dep.design, deconstruct = #builds, ghosts_removed = #ghosts, cleared = tally(builds) }
    if a.dry_run then out.note = "dry run: nothing was marked" return out end
    for _, g in ipairs(ghosts) do g.destroy() end
    for _, e in ipairs(builds) do e.order_deconstruction(f) end
    storage.deployments[dep.id] = nil
    out.note = "marked for deconstruction; the deployment is forgotten"
    return out
  end,
}

-- ---------------------------------------------------------------- reading the map back
R.register {
  name = "what_is",
  description = "What stands on a tile and what it is for: the building or ghost, its design, version and deployment, its tags and the nearest named place.",
  params = {
    x = { type = "number", required = true, description = "tile x" },
    y = { type = "number", required = true, description = "tile y" },
    surface = { type = "string", description = "surface name; leave out for where the player is" },
  },
  run = function(a)
    local s, err = G.surface_of(a.surface)
    if not s then return err end
    local cx, cy = a.x + 0.5, a.y + 0.5
    local out = { surface = s.name, x = math.floor(a.x), y = math.floor(a.y) }
    local hit
    for _, e in pairs(s.find_entities_filtered { area = { { a.x, a.y }, { a.x + 1, a.y + 1 } } }) do
      if e.valid and e.type ~= "resource" and e.type ~= "character" then hit = e break end
    end
    local dep_id
    if hit then
      out.name = (hit.type == "entity-ghost") and hit.ghost_name or hit.name
      out.ghost = (hit.type == "entity-ghost") or nil
      if hit.type == "entity-ghost" and hit.tags then
        out.tags = hit.tags
        dep_id = hit.tags.skippy_deployment
      elseif hit.unit_number then
        dep_id = storage.design_marks[hit.unit_number]
      end
    end
    if not dep_id then
      for _, dep in pairs(storage.deployments) do
        local b = dep.box
        if dep.surface == s.name and b and cx > b[1][1] and cx < b[2][1] and cy > b[1][2] and cy < b[2][2] then dep_id = dep.id break end
      end
    end
    local dep = dep_id and storage.deployments[dep_id]
    if dep then
      local d = storage.designs[dep.design]
      out.design = { name = dep.design, description = d and d.description, deployment = dep.id, version = dep.version, latest = d and d.latest }
    end
    local best, bd
    for _, t in pairs(game.forces.player.find_chart_tags(s)) do
      if t.valid and t.text and t.text ~= "" then
        local dd = (t.position.x - cx) ^ 2 + (t.position.y - cy) ^ 2
        if not bd or dd < bd then best, bd = t, dd end
      end
    end
    if best and bd <= 60 * 60 then out.nearest_place = { name = best.text, tiles_away = math.floor(math.sqrt(bd)) } end
    if not hit and not dep then out.note = "nothing of ours stands there" end
    return out
  end,
}

-- A piece built from one of our ghosts (by robots or by a player) keeps its deployment.
function D.on_built(event)
  local e = event.entity
  local tags = event.tags
  if e and e.valid and e.unit_number and tags and tags.skippy_deployment then
    storage.design_marks = storage.design_marks or {}
    storage.design_marks[e.unit_number] = tags.skippy_deployment
  end
end

return D
