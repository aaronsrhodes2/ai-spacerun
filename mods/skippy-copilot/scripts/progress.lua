-- How far the game has come, as plain facts the bridge can test milestones against: what is researched, how much of
-- given items has ever been made, how many of given buildings stand, rockets launched, where the platforms are, which
-- planets have been reached, and whether the game is won. The bridge names the items and buildings it cares about, so
-- the answer stays small.
local R = require("scripts.registry")

R.register {
  name = "progress",
  description = "For the bridge: the facts milestones are tested against. Give the items and buildings to count.",
  params = {
    items = { type = "table", description = "item names whose total production (all surfaces, all time) to report" },
    entities = { type = "table", description = "building names to count (all surfaces)" },
  },
  run = function(a)
    local force = game.forces.player
    local researched = {}
    for name, t in pairs(force.technologies) do
      if t.researched then researched[#researched + 1] = name end
    end
    table.sort(researched)

    local surfaces = {}
    for _, s in pairs(game.surfaces) do
      if not surfaces[s.index] then surfaces[s.index] = s end       -- a surface can be listed under its name and its index
    end

    local produced = {}
    for _, item in pairs(a.items or {}) do
      local total = 0
      if prototypes.item[item] then
        for _, s in pairs(surfaces) do
          local ok, n = pcall(function() return force.get_item_production_statistics(s).get_input_count(item) end)
          if ok and n then total = total + n end
        end
      end
      produced[item] = total
    end

    local built = {}
    for _, name in pairs(a.entities or {}) do
      local total = 0
      if prototypes.entity[name] then
        for _, s in pairs(surfaces) do
          total = total + s.count_entities_filtered { name = name, force = force }
        end
      end
      built[name] = total
    end

    local platforms = {}
    for _, p in pairs(force.platforms or {}) do
      if p.valid then
        local loc = p.space_location
        platforms[#platforms + 1] = { name = p.name, at = loc and loc.name or "in flight" }
      end
    end

    local reached = {}
    for name, planet in pairs(game.planets or {}) do
      local s = planet.surface
      if s and s.count_entities_filtered { force = force, limit = 1 } > 0 then reached[#reached + 1] = name end
    end
    table.sort(reached)

    return {
      tick = game.tick, hours_played = math.floor(game.tick / 216000 * 10) / 10,
      researched = researched, produced = produced, built = built,
      rockets_launched = force.rockets_launched or 0,
      platforms = platforms, planets_reached = reached,
      won = (game.finished or game.finished_but_continuing) and true or false,
    }
  end,
}
