-- News from the game for the model: things that happened which may deserve a word to the player. The first kind is
-- a finished research, with what it unlocked (read live) and our design note for it, so the model can say
-- "you just unlocked this, we could now improve that" without the player having to think of it.
local R = require("scripts.registry")
local NOTES = require("scripts.notes")

local KEEP = 100
local E = {}

function E.init()
  storage.events = storage.events or {}
  storage.events_next = storage.events_next or 1
end

local function push(event)
  event.id = storage.events_next
  event.tick = game.tick
  storage.events_next = storage.events_next + 1
  storage.events[#storage.events + 1] = event
  while #storage.events > KEEP do table.remove(storage.events, 1) end
end

local function describe(tech)
  local recipes, other = {}, {}
  for _, eff in pairs(tech.prototype.effects or {}) do
    if eff.type == "unlock-recipe" then
      recipes[#recipes + 1] = eff.recipe
    else
      other[eff.type] = (other[eff.type] or 0) + 1
    end
  end
  local kinds = {}
  for k in pairs(other) do kinds[#kinds + 1] = k end
  table.sort(kinds)
  local base = string.gsub(tech.name, "%-%d+$", "")          -- "speed-module-2" also gets the note for "speed-module"
  return {
    technology = tech.name,
    unlocks_recipes = (#recipes > 0) and recipes or nil,
    other_effects = (#kinds > 0) and kinds or nil,
    design_note = NOTES[tech.name] or NOTES[base],
  }
end

function E.on_research(event)
  local tech = event.research
  if tech.force.name ~= "player" then return end
  local d = describe(tech)
  d.kind = "research_finished"
  push(d)
end

R.register {
  name = "events_read",
  description = "News from the game since a given event: research that finished, with what it unlocked and a design note on what can now be improved. Pass the last id you have seen as 'after'.",
  params = {
    after = { type = "number", default = 0, description = "id of the last event already read; 0 for everything remembered" },
  },
  run = function(a)
    local out = {}
    for _, ev in ipairs(storage.events) do
      if ev.id > a.after then out[#out + 1] = ev end
    end
    return { events = out, last_id = storage.events_next - 1 }
  end,
}

R.register {
  name = "design_note",
  description = "What a researched technology makes possible: what it unlocks and our note on what can now be improved, simplified or removed in the factory. Use it when deciding what to do next, or with no name to get the notes for the most recently researched technologies.",
  params = {
    technology = { type = "string", description = "internal technology name; leave out for the five most recent researches" },
  },
  run = function(a)
    local force = game.forces.player
    if a.technology then
      local t = force.technologies[a.technology]
      if not t then return { error = "there is no technology named '" .. a.technology .. "'", hint = "use 'search' with kind 'technology'" } end
      local d = describe(t)
      d.researched = t.researched
      return d
    end
    local out = {}
    for i = #storage.events, 1, -1 do
      local ev = storage.events[i]
      if ev.kind == "research_finished" then out[#out + 1] = ev end
      if #out >= 5 then break end
    end
    return { recent = out }
  end,
}

return E
