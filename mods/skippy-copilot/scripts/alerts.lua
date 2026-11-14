-- The game's own alerts (the icons that flash at the bottom of the screen), and where the player is. Alerts are the
-- commonest way a problem first shows, so the bridge reads them at the start of every turn (the Captain, 2026-11-13).
local R = require("scripts.registry")

local MEANS = {
  entity_destroyed = "something of ours was destroyed",
  entity_under_attack = "something of ours is under attack",
  not_enough_construction_robots = "there are ghosts to build and too few construction robots free",
  no_material_for_construction = "robots cannot build a ghost because the item is not in the logistic network",
  not_enough_repair_packs = "damaged buildings and no repair packs in the network",
  no_platform_storage = "a space platform's hub is full",
  turret_out_of_ammo = "a turret has run out of ammunition",
  turret_fire = "a turret is firing",
  no_storage = "robots have nowhere to put an item: storage chests are full or missing",
  train_out_of_fuel = "a train has no fuel",
  train_no_path = "a train cannot find a path to its stop",
  pipeline_overextended = "a pipeline is too long to carry fluid without pumps",
  collector_path_blocked = "an asteroid collector's arm is blocked",
  unclaimed_cargo = "cargo is waiting in orbit with no landing pad request for it",
  frozen = "a building is frozen and needs heat",
  custom = "an alert raised by a mod or a circuit",
}

local function kind_name(v)
  for name, value in pairs(defines.alert_type) do
    if value == v then return name end
  end
  return "alert_" .. tostring(v)
end

-- Alerts belong to a player. Any player of the force will do; with nobody in the game there is nothing to read.
local function any_player()
  return game.connected_players[1] or game.players[1]
end

R.register {
  name = "alerts",
  description = "The alerts the game is showing right now, by kind and surface, with a count, up to three positions and what each kind means. Read these before anything else when asked what is wrong.",
  params = {},
  run = function()
    local player = any_player()
    if not player then return { alerts = {}, note = "no player has joined the game, so there are no alerts to read" } end
    local out = {}
    for surface_index, by_type in pairs(player.get_alerts {}) do
      local surface = game.get_surface(surface_index)
      for alert_type, list in pairs(by_type) do
        local kind = kind_name(alert_type)
        local entry = { surface = surface and surface.name or tostring(surface_index), kind = kind, count = #list, means = MEANS[kind], examples = {} }
        for i = 1, math.min(3, #list) do
          local a = list[i]
          local pos = a.position or (a.target and a.target.valid and a.target.position)
          entry.examples[#entry.examples + 1] = {
            x = pos and pos.x or nil, y = pos and pos.y or nil,
            what = (a.target and a.target.valid) and ((a.target.type == "entity-ghost") and ("ghost of " .. a.target.ghost_name) or a.target.name) or nil,
          }
        end
        out[#out + 1] = entry
      end
    end
    table.sort(out, function(p, q) return p.count > q.count end)
    return { alerts = out }
  end,
}

R.register {
  name = "player",
  description = "Where the player is: surface and position, and what they have selected (are pointing at). Use it for requests such as 'the thing next to me' or 'this machine'.",
  params = {
    name = { type = "string", description = "player name; leave out for the first player in the game" },
  },
  run = function(a)
    local p
    if a.name then p = game.get_player(a.name) else p = any_player() end          -- a name that is not in the game is an error, not somebody else
    if not p then return { error = "no such player is in the game" } end
    local sel = p.selected
    return {
      name = p.name, surface = p.surface.name, x = math.floor(p.position.x), y = math.floor(p.position.y),
      pointing_at = (sel and sel.valid) and { name = sel.name, type = sel.type, x = sel.position.x, y = sel.position.y } or nil,
    }
  end,
}

return { any_player = any_player }
