-- The spider commander (the Captain, 2026-11-21). The player lives in remote view: the map, the surface list and ghost
-- placement, hardly ever local view. The body belongs to the assistant: the player's character rides a spidertron as
-- its driver, the assistant drives the spider by autopilot, and the robots in its roboports build the ghosts from its
-- trunk, which asks the logistic network for what the ghosts near it need (ghost_requests with spider). Nothing here
-- moves the player's view unless asked, and nothing is teleported.
--   Switched on by the map setting 'skippy-commander', in a new game or a running one. A force with no spidertron gets
--   one, once per player, with a starter kit, under the allowance 'commander-kit'; otherwise it must build its own.
local R = require("scripts.registry")
local AL = require("scripts.allowances")
local E = require("scripts.events")
local P = require("scripts.places")

local M = {}

-- The starter kit: what a new player needs to build a first base with robots (counted in run stats when given).
local EQUIPMENT = { "fission-reactor-equipment", "personal-roboport-mk2-equipment", "personal-roboport-mk2-equipment",
                    "personal-roboport-mk2-equipment", "energy-shield-mk2-equipment", "battery-mk2-equipment" }
local KIT = {
  { "construction-robot", 50 }, { "transport-belt", 200 }, { "underground-belt", 20 }, { "splitter", 10 }, { "inserter", 50 },
  { "burner-mining-drill", 10 }, { "electric-mining-drill", 20 }, { "stone-furnace", 48 }, { "assembling-machine-1", 20 },
  { "small-electric-pole", 100 }, { "pipe", 50 }, { "offshore-pump", 2 }, { "boiler", 4 }, { "steam-engine", 8 },
  { "wooden-chest", 20 }, { "lab", 4 }, { "coal", 100 },
}

function M.init()
  storage.commander = storage.commander or { spiders = {}, kits = {} }
end

local function on()
  local s = settings.global["skippy-commander"]
  return s ~= nil and s.value == true
end

local function valid(e) return e and e.valid end

-- The spiders the assistant drives, made valid: the ones it was given, then any of the force's own.
local function all_spiders(f)
  M.init()
  local out, seen = {}, {}
  for _, e in pairs(storage.commander.spiders) do
    if valid(e) then out[#out + 1] = e seen[e.unit_number] = true end
  end
  for _, s in pairs(game.surfaces) do
    for _, e in pairs(s.find_entities_filtered { type = "spider-vehicle", force = f }) do
      if not seen[e.unit_number] then out[#out + 1] = e seen[e.unit_number] = true end
    end
  end
  return out
end

-- A spider by its label or unit number; leave out for the first one.
local function spider_of(key)
  local list = all_spiders(game.forces.player)
  if #list == 0 then return nil, { error = "there is no spidertron", hint = "switch on the spider commander, or build one" } end
  if key == nil or key == "" then return list[1] end
  for _, e in ipairs(list) do
    if tostring(e.unit_number) == tostring(key) or e.entity_label == key then return e end
  end
  local names = {}
  for _, e in ipairs(list) do names[#names + 1] = e.entity_label or tostring(e.unit_number) end
  return nil, { error = "there is no spider called '" .. tostring(key) .. "'", hint = "spiders: " .. table.concat(names, ", ") }
end

local function give_kit(spider)
  local grid = spider.grid
  local placed = 0
  if grid then
    for _, name in ipairs(EQUIPMENT) do
      if prototypes.equipment[name] and grid.put { name = name } then placed = placed + 1 end
    end
  end
  local trunk = spider.get_inventory(defines.inventory.spider_trunk)
  local given = {}
  for _, row in ipairs(KIT) do
    if prototypes.item[row[1]] then
      local n = trunk.insert { name = row[1], count = row[2] }
      if n > 0 then given[row[1]] = n end
    end
  end
  if storage.run then storage.run.kits_given = (storage.run.kits_given or 0) + 1 end
  return placed, given
end

-- Make a player a commander: a spider for the body, the character in its seat, the player in remote view.
function M.take(player)
  if not (player and player.valid) or not on() then return nil end
  M.init()
  local state = storage.commander
  local spider = state.spiders[player.index]
  if not valid(spider) then
    local f = player.force
    local at = (player.character and player.character.position) or player.position
    local surface = (player.character and player.character.surface) or player.surface
    spider = surface.find_entities_filtered { type = "spider-vehicle", force = f, position = at, radius = 200, limit = 1 }[1]
    if not spider then
      for _, e in ipairs(all_spiders(f)) do
        local mine = false
        for _, s in pairs(state.spiders) do if s == e then mine = true end end
        if not mine then spider = e break end
      end
    end
    if not spider then
      if state.kits[player.index] then return nil, "the starter spider was given once already" end
      if not AL.on("commander-kit") then
        E.push { kind = "commander", text = player.name .. " has no spidertron: build one, or allow the starter kit (commander-kit)" }
        return nil, "no spidertron, and the starter kit is switched off"
      end
      local spot = surface.find_non_colliding_position("spidertron", at, 20, 1) or at
      spider = surface.create_entity { name = "spidertron", position = spot, force = f }
      state.kits[player.index] = true
      spider.entity_label = "Skippy " .. player.index
      local placed = give_kit(spider)
      E.push { kind = "commander", text = player.name .. " got a starter spidertron with " .. placed .. " pieces of equipment and a kit in its trunk" }
    end
    state.spiders[player.index] = spider
  end
  if player.character and player.character.valid and not spider.get_driver() then
    spider.set_driver(player.character)                 -- the body rides; the assistant drives
  end
  if player.controller_type ~= defines.controllers.remote then
    player.set_controller { type = defines.controllers.remote, position = spider.position, surface = spider.surface }
  end
  return spider
end

function M.on_setting(event)
  if event.setting ~= "skippy-commander" then return end
  if on() then
    for _, p in pairs(game.players) do
      if p.connected then M.take(p) end
    end
  end
end

function M.on_player(event)
  local p = game.get_player(event.player_index)
  if p and on() then M.take(p) end
end

-- The player stepped out of remote view into local view: back to the map, the commander's place.
function M.on_controller(event)
  local p = game.get_player(event.player_index)
  if p and on() and storage.commander and p.controller_type == defines.controllers.character and storage.commander.spiders[p.index] then
    local s = storage.commander.spiders[p.index]
    if valid(s) then p.set_controller { type = defines.controllers.remote, position = s.position, surface = s.surface } end
  end
end

function M.on_arrived(event)
  local s = event.vehicle
  if not valid(s) then return end
  local job = storage.commander and storage.commander.going and storage.commander.going[s.unit_number]
  if not job then return end
  storage.commander.going[s.unit_number] = nil
  E.push { kind = "spider_arrived", text = (s.entity_label or ("spider " .. s.unit_number)) .. " arrived at " .. math.floor(s.position.x) .. "," .. math.floor(s.position.y),
           spider = s.entity_label or s.unit_number, x = math.floor(s.position.x), y = math.floor(s.position.y) }
end

local function count(inv, name)
  return inv and inv.get_item_count(name) or 0
end

local function describe(e)
  local trunk = e.get_inventory(defines.inventory.spider_trunk)
  local driver = e.get_driver()
  local dest = e.autopilot_destination
  return { spider = e.entity_label or tostring(e.unit_number), unit = e.unit_number, surface = e.surface.name,
           x = math.floor(e.position.x), y = math.floor(e.position.y),
           driver = driver and (driver.player and driver.player.name or "a character") or nil,
           going_to = dest and { x = math.floor(dest.x), y = math.floor(dest.y) } or nil,
           construction_robots = count(trunk, "construction-robot"),
           free_trunk_slots = trunk and trunk.count_empty_stacks() or 0 }
end

R.register {
  name = "spiders",
  description = "The spidertrons: where each is and is going, its driver, construction robots and free trunk slots. In commander play the body rides one and its robots build the ghosts.",
  params = {},
  run = function()
    M.init()
    local out = {}
    for _, e in ipairs(all_spiders(game.forces.player)) do out[#out + 1] = describe(e) end
    return { spiders = out, commander = on(), note = (#out == 0) and "no spidertron yet" or nil }
  end,
}

local MOVERS = { "spider-vehicle", "car", "locomotive", "cargo-wagon", "character" }

R.register {
  name = "spider_go",
  description = "Send a spidertron to x,y or a named place (its robots build ghosts in reach on the way; news 'spider_arrived' on arrival), or with follow true make it follow the moving thing at x,y, or stop it. The player's view stays put.",
  params = {
    spider = { type = "string", description = "label or unit number; leave out for the first" },
    x = { type = "number", description = "where" },
    y = { type = "number", description = "where" },
    at = { type = "string", description = "or a place name" },
    follow = { type = "boolean", default = false, description = "follow what moves at x,y" },
    stop = { type = "boolean", default = false, description = "stop walking or following" },
  },
  run = function(a)
    M.init()
    local s, err = spider_of(a.spider)
    if not s then return err end
    local name = s.entity_label or tostring(s.unit_number)
    storage.commander.going = storage.commander.going or {}
    if a.stop then
      s.follow_target, s.autopilot_destination = nil, nil
      storage.commander.going[s.unit_number] = nil
      return { spider = name, stopped = true }
    end
    local x, y = a.x, a.y
    if a.at then
      local p, perr = P.resolve(a.at, s.surface.name)
      if not p then return perr end
      x, y = p.x, p.y
    end
    if not (x and y) then return { error = "say where: x and y, or a place name (at)" } end
    if a.follow then
      local t = s.surface.find_entities_filtered { position = { x, y }, radius = 2, type = MOVERS, limit = 1 }[1]
      if not t or t == s then return { error = "nothing that moves stands at " .. x .. "," .. y } end
      s.autopilot_destination = nil
      s.follow_target = t
      return { spider = name, following = t.name, at = { x = math.floor(t.position.x), y = math.floor(t.position.y) } }
    end
    s.follow_target = nil
    s.autopilot_destination = { x = x, y = y }
    storage.commander.going[s.unit_number] = { x = x, y = y, tick = game.tick }
    return { spider = name, from = { x = math.floor(s.position.x), y = math.floor(s.position.y) },
             to = { x = x, y = y }, note = "on its way; news 'spider_arrived' says when it is there" }
  end,
}

-- Where the ghosts the network cannot reach are: a ghost counts when no roboport network with construction robots covers it.
local function stranded(s, f, near, radius)
  local found = s.find_entities_filtered { type = { "entity-ghost", "tile-ghost" }, force = f, position = near, radius = radius, limit = 2000 }
  local out = {}
  for _, g in pairs(found) do
    local cell = s.find_logistic_network_by_position(g.position, f)
    if not (cell and cell.all_construction_robots > 0) then out[#out + 1] = g end
  end
  return out
end

R.register {
  name = "spider_tend_step",
  description = "For spider_tend's timed job: unless walking or building, send the spider to the nearest ghost the roboport network cannot reach.",
  params = {
    spider = { type = "string", description = "its label or unit number; leave out for the first spider" },
    radius = { type = "number", default = 300, description = "how far to look for ghosts, at most 1000" },
  },
  run = function(a)
    M.init()
    local s, err = spider_of(a.spider)
    if not s then return err end
    if s.autopilot_destination then return { spider = s.entity_label or tostring(s.unit_number), doing = "walking" } end
    local f = game.forces.player
    local here = stranded(s.surface, f, s.position, 20)
    if #here > 0 then return { spider = s.entity_label or tostring(s.unit_number), doing = "building", ghosts_in_reach = #here } end
    local list = stranded(s.surface, f, s.position, math.max(20, math.min(a.radius, 1000)))
    if #list == 0 then return { spider = s.entity_label or tostring(s.unit_number), doing = "nothing", note = "no ghost out of the network's reach" } end
    local best, bd
    for _, g in ipairs(list) do
      local d = (g.position.x - s.position.x) ^ 2 + (g.position.y - s.position.y) ^ 2
      if not bd or d < bd then best, bd = g, d end
    end
    s.autopilot_destination = { x = best.position.x, y = best.position.y }
    storage.commander.going = storage.commander.going or {}
    storage.commander.going[s.unit_number] = { x = best.position.x, y = best.position.y, tick = game.tick }
    return { spider = s.entity_label or tostring(s.unit_number), doing = "going", to = { x = math.floor(best.position.x), y = math.floor(best.position.y) }, stranded_ghosts = #list }
  end,
}

R.register {
  name = "spider_tend",
  description = "Tending on or off: every minute a timed job sends the spider to ghosts the roboport network cannot reach, for its robots to build.",
  params = {
    spider = { type = "string", default = "", description = "its label or unit number; leave out for the first spider" },
    on = { type = "boolean", default = true, description = "false to stop tending" },
  },
  run = function(a)
    local s, err = spider_of(a.spider ~= "" and a.spider or nil)
    if not s then return err end
    local name = "tend " .. (s.entity_label or tostring(s.unit_number))
    local r
    if not a.on then
      r = R.call("cron_change", { name = name, action = "remove" })
    else
      r = R.call("cron_add", { name = name, every_minutes = 1, tool = "spider_tend_step", args = { spider = tostring(s.unit_number) },
                               purpose = "build the ghosts the roboport network cannot reach, with the spider's robots",
                               expect_ok = "the spider walks to stranded ghosts and they get built",
                               expect_bad = "the spider stands still while stranded ghosts wait, or walks back and forth",
                               retire_when = "the roboport network reaches everywhere we build", replace = true })
    end
    if not r.ok then return { error = r.error, hint = r.hint } end
    return r.result
  end,
}

M.spider_of = spider_of
return M
