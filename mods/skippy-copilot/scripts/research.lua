-- Research. The assistant does not choose research on its own by default: when research runs out it is told so, and
-- that is its moment to come to the player with one suggestion and the reason for it (the Captain, 2026-11-13: an
-- opportunity for the AI to engage with the player). Research itself is only ever queued, never written: packs and
-- labs do the rest.
local R = require("scripts.registry")
local NOTES = require("scripts.notes")

local Q = {}

local function trigger_text(trig)
  if not trig then return nil end
  local what = trig.item and (trig.item.name or trig.item) or (trig.entity and (trig.entity.name or trig.entity)) or nil
  local kinds = { ["craft-item"] = "make", ["mine-entity"] = "mine", ["build-entity"] = "build", ["craft-fluid"] = "make the fluid",
                  ["send-item-to-orbit"] = "send into orbit", ["capture-spawner"] = "capture a spawner", ["create-space-platform"] = "create a space platform" }
  return (kinds[trig.type] or trig.type) .. (what and (" " .. what) or "") .. (trig.count and trig.count > 1 and (" x" .. trig.count) or "")
end

local function describe(t)
  local p = t.prototype
  local packs, unlocks = {}, {}
  for _, ing in pairs(p.research_unit_ingredients or {}) do packs[#packs + 1] = ing.name end
  for _, eff in pairs(p.effects or {}) do
    if eff.type == "unlock-recipe" and #unlocks < 8 then unlocks[#unlocks + 1] = eff.recipe end
  end
  local base = string.gsub(t.name, "%-%d+$", "")
  local trig = p.research_trigger
  return {
    technology = t.name, science_packs = (#packs > 0) and packs or nil, units = (not trig) and p.research_unit_count or nil,
    earned_by = trigger_text(trig), unlocks_recipes = (#unlocks > 0) and unlocks or nil, design_note = NOTES[t.name] or NOTES[base],
  }
end

-- A technology that can be started now: not done, not hidden, every prerequisite done.
local function open(t)
  if t.researched or t.enabled == false then return false end
  for _, pre in pairs(t.prerequisites or {}) do
    if not pre.researched then return false end
  end
  return true
end

local function queue_names(force)
  local out = {}
  for _, t in pairs(force.research_queue or {}) do out[#out + 1] = t.name end
  return out
end

R.register {
  name = "research_available",
  description = "For the bridge: what is being researched, what is queued, and every technology that could be started now (all its prerequisites are done), with its packs, cost, what it unlocks and its design note.",
  params = {},
  run = function()
    local force = game.forces.player
    local list = {}
    for _, t in pairs(force.technologies) do
      if open(t) then list[#list + 1] = describe(t) end
    end
    table.sort(list, function(a, b)
      if (a.units or 0) ~= (b.units or 0) then return (a.units or 0) < (b.units or 0) end
      return a.technology < b.technology
    end)
    local cur = force.current_research
    return {
      researching = cur and cur.name or nil, progress = cur and (math.floor(force.research_progress * 100) / 100) or nil,
      queued = queue_names(force), available = list, labs = game.surfaces.nauvis and game.surfaces.nauvis.count_entities_filtered { type = "lab", force = force } or 0,
    }
  end,
}

R.register {
  name = "queue_research",
  description = "Add a technology to the research queue. The labs and science packs do the research; this only queues it. Ask the player before queueing, unless they have told you to choose research yourself.",
  params = {
    technology = { type = "string", required = true, description = "internal technology name" },
  },
  run = function(a)
    local force = game.forces.player
    local t = force.technologies[a.technology]
    if not t then return { error = "there is no technology named '" .. a.technology .. "'", hint = "use research_options, or 'search' with kind 'technology'" } end
    if t.researched then return { error = a.technology .. " is already researched" } end
    for _, name in pairs(queue_names(force)) do
      if name == a.technology then return { error = a.technology .. " is already in the queue" } end
    end
    local trig = t.prototype.research_trigger
    if trig then
      return { error = a.technology .. " cannot be queued: it is earned in the game, not in labs", hint = "to earn it: " .. (trigger_text(trig) or "see lookup") }
    end
    local missing = {}
    for name, pre in pairs(t.prerequisites or {}) do
      if not pre.researched then missing[#missing + 1] = name end
    end
    table.sort(missing)
    local ok = force.add_research(a.technology)
    if not ok then
      return { error = "the game would not queue " .. a.technology, hint = (#missing > 0) and ("it needs first: " .. table.concat(missing, ", ")) or "the queue may be full" }
    end
    storage.research_idle_told = nil
    return { queued = a.technology, queue = queue_names(force), needs_first = (#missing > 0) and missing or nil }
  end,
}

-- Is research standing still for want of a choice? Nothing being researched, nothing queued, and at least one lab.
function Q.idle()
  local force = game.forces.player
  if force.current_research or #queue_names(force) > 0 then return false end
  for _, s in pairs(game.surfaces) do
    if s.count_entities_filtered { type = "lab", force = force, limit = 1 } > 0 then return true end
  end
  return false
end

return Q
