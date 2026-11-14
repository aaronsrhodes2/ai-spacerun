-- Everything moving (the Captain, 2026-11-13): some players want every machine working at once, none standing idle,
-- because the factory is balanced so exactly. The measure is the share of machines that are working, now and over
-- the last while, with the groups that stand idle and why.
--
-- The game has no dial for a machine's effort. What balances a factory is: how many machines run each recipe (the
-- ratios), how much the belts and inserters between them carry, and modules and beacons that change a machine's speed.
local R = require("scripts.registry")
local G = require("scripts.grid")

local MACHINES = { "assembling-machine", "furnace", "mining-drill", "lab", "rocket-silo" }
local KEEP = 12                 -- samples kept: with one every ten seconds, the last two minutes
local EVERY = 600

local B = {}

function B.init()
  storage.busy = storage.busy or { samples = {} }
end

local function count(surface)
  local working, total, groups = 0, 0, {}
  for _, e in pairs(surface.find_entities_filtered { type = MACHINES, force = "player" }) do
    local st = G.status_name(e) or "unknown"
    total = total + 1
    local recipe
    pcall(function() local r = e.get_recipe() recipe = r and r.name or nil end)
    local key = e.name .. "|" .. (recipe or "-")
    local g = groups[key]
    if not g then
      g = { machine = e.name, recipe = recipe, total = 0, working = 0, states = {}, x = e.position.x, y = e.position.y }
      groups[key] = g
    end
    g.total = g.total + 1
    if st == "working" then
      working = working + 1
      g.working = g.working + 1
    else
      g.states[st] = (g.states[st] or 0) + 1
    end
  end
  return working, total, groups
end

-- One sample of every surface that has machines, kept for the average.
function B.on_tick(event)
  if event.tick % EVERY ~= 0 or not storage.busy then return end
  local working, total = 0, 0
  for _, s in pairs(game.surfaces) do
    local w, t = count(s)
    working, total = working + w, total + t
  end
  local samples = storage.busy.samples
  samples[#samples + 1] = { working = working, total = total }
  while #samples > KEEP do table.remove(samples, 1) end
end

local WHY = {
  item_ingredient_shortage = "starved: more machines here than their supply can feed, so either supply more or run fewer",
  fluid_ingredient_shortage = "starved of a fluid: supply more or run fewer",
  no_ingredients = "starved: supply more or run fewer",
  full_output = "backed up: more is made here than is taken away, so add what uses it or run fewer",
  waiting_for_space_in_destination = "backed up: nothing takes its product away",
  no_power = "no power",
  low_power = "too little power",
  no_recipe = "no recipe set: give it work or remove it",
  no_minable_resources = "the ore under it has run out: move or remove it",
  no_research_in_progress = "no research queued",
  missing_science_packs = "the labs lack a science pack",
}

R.register {
  name = "utilisation",
  description = "How much of the factory is working: the share of machines working right now and averaged over the last two minutes, and the groups of machines that stand idle, with why and how many. For players who want every machine moving at once. The game has no dial for a machine's effort: balance comes from how many machines run each recipe, what the belts and inserters between them carry, and modules and beacons.",
  params = {
    surface = { type = "string", description = "surface name; leave out for where the player is" },
    top = { type = "number", default = 8, description = "how many idle groups to list, the largest first" },
  },
  run = function(a)
    local surface, err = G.surface_of(a.surface)
    if not surface then return err end
    local working, total, groups = count(surface)
    if total == 0 then return { machines = 0, note = "there are no machines here yet" } end
    local idle = {}
    for _, g in pairs(groups) do
      if g.working < g.total then
        local worst, worst_n
        for st, n in pairs(g.states) do
          if not worst_n or n > worst_n then worst, worst_n = st, n end
        end
        idle[#idle + 1] = { machine = g.machine, recipe = g.recipe, idle = g.total - g.working, of = g.total, mostly = worst, why = WHY[worst],
                            example_x = g.x, example_y = g.y }
      end
    end
    table.sort(idle, function(p, q) return p.idle > q.idle end)
    local top = math.max(1, math.min(a.top, 30))
    local shown = {}
    for i = 1, math.min(top, #idle) do shown[#shown + 1] = idle[i] end
    local sw, st = 0, 0
    for _, s in ipairs(storage.busy and storage.busy.samples or {}) do sw, st = sw + s.working, st + s.total end
    return {
      surface = surface.name, machines = total, working_now = working, percent_now = math.floor(working / total * 1000 + 0.5) / 10,
      percent_lately = (st > 0) and (math.floor(sw / st * 1000 + 0.5) / 10) or nil,
      idle_groups = shown, more_groups_not_shown = math.max(0, #idle - #shown),
      how_to_balance = "use plan_production for the exact number of machines each recipe needs at the rate wanted; where machines are starved run fewer of them or supply more; where they are backed up add what uses the product or run fewer",
    }
  end,
}

return B
