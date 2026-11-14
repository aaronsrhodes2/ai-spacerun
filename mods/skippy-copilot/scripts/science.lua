-- Science per minute, the community's usual measure of a factory (the Captain, 2026-11-13: "I want to produce 1,000
-- science per minute of each science"). For every science pack the labs take: how many are made a minute and how many
-- the labs use, over the last ten minutes, on all surfaces together. A factory's science per minute is its slowest pack.
--
-- Also the run's own counters, for the other thing players will try: finishing the game in the fewest prompts.
local R = require("scripts.registry")

local function packs()
  local seen, out = {}, {}
  for _, lab in pairs(prototypes.get_entity_filtered { { filter = "type", type = "lab" } }) do
    for _, name in pairs(lab.lab_inputs or {}) do
      if not seen[name] then
        seen[name] = true
        out[#out + 1] = name
      end
    end
  end
  return out
end

local function surfaces()
  local out = {}
  for _, s in pairs(game.surfaces) do out[s.index] = s end
  return out
end

-- Items a minute over the last ten minutes, summed over every surface. category is "input" (made) or "output" (used).
local function per_minute(force, item, category)
  local total = 0
  for _, s in pairs(surfaces()) do
    local ok, n = pcall(function()
      return force.get_item_production_statistics(s).get_flow_count { name = item, category = category, precision_index = defines.flow_precision_index.ten_minutes }
    end)
    if ok and n then total = total + n end
  end
  return total
end

-- The recipe that makes a pack is unlocked.
local function available(force, pack)
  for _, recipe in pairs(force.recipes) do
    if recipe.enabled then
      for _, p in pairs(recipe.products) do
        if p.name == pack then return true end
      end
    end
  end
  return false
end

R.register {
  name = "science",
  description = "Science per minute: for each science pack, how many are made and how many the labs use a minute (over the last ten minutes, all surfaces together), and the factory's science per minute, which is its slowest pack. With a target it says which packs fall short and by how much. Use it for goals such as '1,000 science a minute of each science'.",
  params = {
    target = { type = "number", description = "packs a minute wanted of each science; leave out to only measure" },
  },
  run = function(a)
    local force = game.forces.player
    local list, lowest, lowest_name = {}, nil, nil
    local short = {}
    for _, pack in ipairs(packs()) do
      local can = available(force, pack)
      local made = math.floor(per_minute(force, pack, "input") * 10 + 0.5) / 10
      local used = math.floor(per_minute(force, pack, "output") * 10 + 0.5) / 10
      list[#list + 1] = { pack = pack, made_per_minute = made, used_per_minute = used, researched = can }
      if can then
        if not lowest or made < lowest then lowest, lowest_name = made, pack end
        if a.target and made < a.target then short[#short + 1] = { pack = pack, short_by = math.floor((a.target - made) * 10 + 0.5) / 10 } end
      end
    end
    table.sort(list, function(p, q) return p.made_per_minute < q.made_per_minute end)
    table.sort(short, function(p, q) return p.short_by > q.short_by end)
    local reached = nil                                  -- only said when a target was given; false must stay false
    if a.target then reached = (#short == 0 and lowest ~= nil) end
    return {
      science_per_minute = lowest or 0, slowest_pack = lowest_name, packs = list,
      target = a.target, reached = reached, short = a.target and short or nil,
      note = "a factory's science per minute is its slowest researched pack; packs not yet researched are listed but not counted",
    }
  end,
}

-- ---------------------------------------------------------------- the run's counters
local S = {}

function S.init()
  storage.run = storage.run or { prompts = 0 }
end

-- A line a player typed in chat is a prompt.
function S.on_chat(event)
  if event.player_index and event.message and event.message ~= "" then
    storage.run.prompts = storage.run.prompts + 1
  end
end

-- Note the moment of the win, once.
function S.on_tick(event)
  if event.tick % 300 ~= 0 then return end
  local run = storage.run
  if run and not run.won_tick and (game.finished or game.finished_but_continuing) then
    run.won_tick = event.tick
    run.prompts_at_win = run.prompts
  end
end

R.register {
  name = "run_stats",
  description = "The run so far: how many prompts the player has typed, hours played, and if the game is won, how many prompts and hours it took. For players who try to finish in as few prompts as they can.",
  params = {},
  run = function()
    local run = storage.run
    return {
      prompts = run.prompts, hours_played = math.floor(game.tick / 216000 * 10) / 10,
      won = run.won_tick ~= nil,
      prompts_to_win = run.prompts_at_win, hours_to_win = run.won_tick and math.floor(run.won_tick / 216000 * 10) / 10 or nil,
    }
  end,
}

return S
