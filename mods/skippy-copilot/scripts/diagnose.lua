-- What is running and what is not. Read this before deciding what to build or fix.
local R = require("scripts.registry")
local G = require("scripts.grid")

local MACHINES = { "assembling-machine", "furnace", "mining-drill", "lab", "rocket-silo", "boiler", "generator", "reactor", "agricultural-tower", "asteroid-collector" }
-- States that mean the machine is fine and nothing needs doing.
local FINE = { working = true, normal = true, fully_charged = true, charging = true, discharging = true }
local ADVICE = {
  item_ingredient_shortage = "starved: look upstream, at what feeds it",
  fluid_ingredient_shortage = "starved of a fluid: look at the pipe that feeds it",
  full_output = "backed up: look downstream, at what takes its product away",
  no_power = "not connected to power",
  low_power = "the power network cannot keep up: fix power first, every other reading is misleading until then",
  no_fuel = "out of fuel",
  no_recipe = "no recipe set",
  no_minable_resources = "the ore under it has run out",
  no_ingredients = "starved: look upstream",
  no_research_in_progress = "no research is queued",
  missing_science_packs = "the labs lack a science pack the current research needs",
  waiting_for_space_in_destination = "backed up: its output has nowhere to go",
  frozen = "frozen: it needs a heat pipe from a heat source next to it",
  low_temperature = "its heat source is too cold",
}

R.register {
  name = "diagnose",
  description = "Counts every machine by what it is doing (working, starved, backed up, unpowered and so on) with up to three example positions for each problem, and what that problem usually means. Covers the whole surface unless an area is given.",
  params = {
    surface = { type = "string", description = "surface name; leave out for where the player is" },
    x = { type = "number", description = "left of an area to limit the check to" },
    y = { type = "number", description = "top of that area" },
    width = { type = "number", description = "width of that area in tiles" },
    height = { type = "number", description = "height of that area in tiles" },
  },
  run = function(a)
    local surface, err = G.surface_of(a.surface)
    if not surface then return err end
    local filter = { type = MACHINES, force = "player" }
    if a.x and a.y and a.width and a.height then
      filter.area = { { a.x, a.y }, { a.x + a.width, a.y + a.height } }
    elseif a.x or a.y or a.width or a.height then
      return { error = "give all four of x, y, width and height for an area, or none of them" }
    end
    local by, total = {}, 0
    for _, e in pairs(surface.find_entities_filtered(filter)) do
      total = total + 1
      local st = G.status_name(e) or "unknown"
      local g = by[st]
      if not g then
        g = { state = st, count = 0, machines = {}, examples = {} }
        by[st] = g
      end
      g.count = g.count + 1
      g.machines[e.name] = (g.machines[e.name] or 0) + 1
      if #g.examples < 3 and not FINE[st] then
        local recipe = nil
        pcall(function() local r = e.get_recipe() recipe = r and r.name or nil end)
        g.examples[#g.examples + 1] = { name = e.name, x = e.position.x, y = e.position.y, recipe = recipe }
      end
    end
    local problems, fine = {}, {}
    for st, g in pairs(by) do
      local list = {}
      for name, n in pairs(g.machines) do list[#list + 1] = name .. " x" .. n end
      table.sort(list)
      local entry = { state = st, count = g.count, machines = list }
      if FINE[st] then
        fine[#fine + 1] = entry
      else
        entry.examples = g.examples
        entry.means = ADVICE[st]
        problems[#problems + 1] = entry
      end
    end
    table.sort(problems, function(p, q) return p.count > q.count end)
    local research = game.forces.player.current_research
    return {
      surface = surface.name, machines_checked = total, problems = problems, fine = fine,
      research = research and { name = research.name, progress = game.forces.player.research_progress } or "nothing is being researched",
    }
  end,
}
