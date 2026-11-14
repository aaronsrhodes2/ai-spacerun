-- Travel between planets, the way a player does it (docs/solver-plan.md, increment 1): empty the pockets, walk to a
-- rocket silo with a rocket ready, ride the rocket up to a platform in orbit, ride the platform to the other planet,
-- drop to the surface. Nothing here moves the character except the game's own rocket, platform and cargo pod.
--
-- The platform is never re-routed: the avatar only boards a ship whose schedule already goes where it wants, so the
-- trip cannot upset the factory's shipping. If no such ship is in orbit, the tool says so.
local R = require("scripts.registry")
local V = require("scripts.avatar")
local I = V.internals

local ASCEND_TICKS = 60 * 180           -- three minutes for the rocket to reach the platform
local RIDE_TICKS = 60 * 60 * 90         -- an hour and a half for the crossing
local DESCEND_TICKS = 60 * 180

local function planet_name(surface)
  local ok, planet = pcall(function() return surface.planet end)
  return ok and planet and planet.name or nil
end

local function platform_of(surface)
  local ok, platform = pcall(function() return surface.platform end)
  return ok and platform or nil
end

local function goes_to(platform, planet)
  local schedule = platform.schedule
  for _, record in pairs(schedule and schedule.records or {}) do
    if record.station == planet then return true end
  end
  return false
end

local function at(platform)
  local loc = platform.space_location
  return loc and loc.name or nil
end

-- The player whose character the body is, if any.
local function owner(body)
  for _, p in pairs(game.connected_players) do
    if p.character == body then return p end
  end
end

-- Where the traveller really is. A player riding a rocket or a pod has no character on a surface for a while; the
-- player's physical surface is the truth then.
local function surface_now(job, body)
  if job.player and job.player.valid then
    local ok, s = pcall(function() return job.player.physical_surface end)
    if ok and s then return s end
  end
  if body and body.valid then return body.surface end
  return nil
end

local function tick_travel(body, job)
  local now = surface_now(job, body)
  local ship = job.ship
  if not (ship and ship.valid) then return I.finish(false, "the ship is gone", { stage = job.stage }) end
  local waited = game.tick - job.stage_tick

  if job.stage == "to_silo" then
    if not (body and job.silo.valid) then return I.finish(false, "the rocket silo is gone", { stage = job.stage }) end
    if job.walk.no_path then return I.finish(false, "there is no way on foot to the rocket silo", { stage = job.stage }) end
    local state, why = I.step_walk(body, job.walk)
    if state == "failed" then return I.finish(false, why, { stage = job.stage }) end
    if state == "arrived" then
      I.stop_moving(body)
      job.walk = nil
      job.stage, job.stage_tick = "board", game.tick
    end

  elseif job.stage == "board" then
    if job.silo.rocket_silo_status ~= defines.rocket_silo_status.rocket_ready then
      return I.finish(false, "the rocket is not ready any more", { stage = job.stage })
    end
    if at(ship) ~= job.from then return I.finish(false, "the ship has left orbit", { stage = job.stage }) end
    local ok = job.silo.launch_rocket({ type = defines.cargo_destination.station, station = ship.hub }, body)
    if not ok then return I.finish(false, "the silo would not launch the avatar", { stage = job.stage }) end
    job.stage, job.stage_tick = "ascend", game.tick

  elseif job.stage == "ascend" then
    if now and now == ship.surface then
      job.stage, job.stage_tick = "ride", game.tick
    elseif waited > ASCEND_TICKS then
      return I.finish(false, "the rocket did not reach the ship", { stage = job.stage })
    end

  elseif job.stage == "ride" then
    if at(ship) == job.to then
      job.stage, job.stage_tick = "drop", game.tick
    elseif ship.paused then
      return I.finish(false, "the ship is paused in flight; the avatar is aboard '" .. ship.name .. "'", { stage = job.stage })
    elseif waited > RIDE_TICKS then
      return I.finish(false, "the ship has not arrived after a long wait; the avatar is aboard '" .. ship.name .. "'", { stage = job.stage })
    end

  elseif job.stage == "drop" then
    local planet = game.planets[job.to]
    local ground = planet.surface or planet.create_surface()         -- the first landing opens the planet
    local ok
    if job.player and job.player.valid then
      ok = job.player.land_on_planet()
    elseif body and body.valid then
      local pod = ship.hub.create_cargo_pod()
      if pod then
        pod.set_passenger(body)
        pod.cargo_pod_destination = { type = defines.cargo_destination.surface, surface = ground }
        ok = true
      end
    end
    if not ok then return I.finish(false, "the avatar could not leave the ship for the surface", { stage = job.stage }) end
    job.ground = ground
    job.stage, job.stage_tick = "descend", game.tick

  elseif job.stage == "descend" then
    if now and now == job.ground then
      return I.finish(true, nil, { planet = job.to, from = job.from, ship = ship.name })
    elseif waited > DESCEND_TICKS then
      return I.finish(false, "the avatar did not reach the surface", { stage = job.stage })
    end
  end
end

V.TICKS.travel = tick_travel

R.register {
  name = "avatar_travel",
  description = "For the bridge: start the avatar travelling to another planet as a player does: walk to a rocket silo with a rocket ready, ride it to a ship in orbit whose schedule goes there, ride the ship, drop to the surface. The avatar must carry nothing (the game lets nobody board a rocket with items). Returns a job id at once; the trip takes many minutes.",
  params = {
    planet = { type = "string", required = true, description = "where to go, such as 'vulcanus'" },
    ship = { type = "string", description = "name of the platform to ride; leave out to take any ship in orbit whose schedule goes there" },
  },
  run = function(a)
    local off = I.no_avatar()
    if off then return off end
    local b = I.busy()
    if b then return b end
    local body = I.need_body(true)
    if not body then return { error = "there is no character to travel with" } end
    if not game.planets[a.planet] then
      local names = {}
      for name in pairs(game.planets) do names[#names + 1] = name end
      table.sort(names)
      return { error = "there is no planet named '" .. a.planet .. "'", hint = "planets: " .. table.concat(names, ", ") }
    end
    local force = body.force
    local ok, unlocked = pcall(function() return force.is_space_location_unlocked(a.planet) end)
    if ok and unlocked == false then return { error = a.planet .. " has not been discovered yet", hint = "research its planet discovery first" } end

    local here = planet_name(body.surface)
    local aboard = platform_of(body.surface)
    if here == a.planet then return { error = "the avatar is already on " .. a.planet } end

    -- which ship
    local ship, seen = nil, {}
    if aboard then
      ship = aboard
      if not goes_to(ship, a.planet) then
        return { error = "the avatar is aboard '" .. ship.name .. "', whose schedule does not go to " .. a.planet, hint = "add " .. a.planet .. " to that ship's schedule" }
      end
    else
      if not here then return { error = "the avatar is not on a planet" } end
      for _, p in pairs(force.platforms) do
        if p.valid and p.hub and p.hub.valid and at(p) == here then
          seen[#seen + 1] = p.name
          if (a.ship and p.name == a.ship) or (not a.ship and not ship and goes_to(p, a.planet)) then ship = p end
        end
      end
      if not ship then
        local list = (#seen > 0) and table.concat(seen, ", ") or "none"
        if a.ship then return { error = "no ship named '" .. a.ship .. "' is in orbit over " .. here, hint = "ships in orbit here: " .. list } end
        return { error = "no ship in orbit over " .. here .. " has " .. a.planet .. " on its schedule", hint = "ships in orbit here: " .. list .. ". Give one a schedule that includes " .. a.planet .. ", or wait for one that has" }
      end
      if not goes_to(ship, a.planet) then
        return { error = "the ship '" .. ship.name .. "' does not have " .. a.planet .. " on its schedule" }
      end
    end

    local player = owner(body)
    if aboard then
      local id = I.start { kind = "travel", stage = "ride", stage_tick = game.tick, ship = ship, to = a.planet, from = at(ship), player = player }
      return { job = id, ship = ship.name, note = "already aboard; waiting for the ship to arrive" }
    end

    -- empty pockets
    local carrying = {}
    local inv = body.get_main_inventory()
    for _, it in pairs(inv and inv.get_contents() or {}) do
      if #carrying < 6 then carrying[#carrying + 1] = it.count .. " " .. it.name end
    end
    if #carrying > 0 then
      return { error = "the avatar must carry nothing to board a rocket; it carries " .. table.concat(carrying, ", "),
               hint = "walk to a chest and put everything in with avatar_carry" }
    end

    -- which silo: the nearest with a rocket ready
    local silo, best
    for _, s in pairs(body.surface.find_entities_filtered { type = "rocket-silo", force = force }) do
      if s.rocket_silo_status == defines.rocket_silo_status.rocket_ready then
        local d = I.dist(body.position, s.position)
        if not best or d < best then silo, best = s, d end
      end
    end
    if not silo then return { error = "no rocket silo on " .. here .. " has a rocket ready", hint = "a silo needs a finished rocket; check its rocket parts" } end

    local walk = I.new_walk({ x = silo.position.x, y = silo.position.y }, math.max(2, body.reach_distance - 3))
    local id = I.start { kind = "travel", stage = "to_silo", stage_tick = game.tick, silo = silo, ship = ship, to = a.planet, from = here, player = player, walk = walk }
    return { job = id, ship = ship.name, from = here, to = a.planet, silo_x = math.floor(silo.position.x), silo_y = math.floor(silo.position.y) }
  end,
}
