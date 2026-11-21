-- Quality that builds (the Captain, 2026-11-21), the runtime half; the data half is the mod skippy-quality, and nothing
-- here runs without it. There, one quality module makes a machine's output the highest quality researched, slowly.
-- Here:
--   * one quality module per machine: a second only slows the machine, so a sliced check takes extras out and spills
--     them beside the machine, marked for the robots to pick up, and says so in the news;
--   * the best quality: what the assistant's ghosts are placed at (designs.lua), so the requests ask for it and the
--     quality machines make it.
local E = require("scripts.events")

local Q = {}
local KINDS = { "assembling-machine", "furnace", "mining-drill", "rocket-silo" }
local PER_SECOND = 50                    -- machines checked a second

function Q.active()
  return script.active_mods["skippy-quality"] ~= nil
end

-- The highest quality the force has unlocked, by name.
function Q.best(force)
  local best, level = "normal", -1
  for name, q in pairs(prototypes.quality) do
    if name ~= "quality-unknown" and not q.hidden and q.level > level and force.is_quality_unlocked(name) then
      best, level = name, q.level
    end
  end
  return best
end

local function is_quality_module(name)
  local p = prototypes.item[name]
  return p ~= nil and p.type == "module" and p.category == "quality"
end

-- Take every quality module past the first out of a machine. -> how many were taken out.
function Q.trim(e)
  local inv = e.get_module_inventory and e.get_module_inventory()
  if not inv then return 0 end
  local mods, total = {}, 0
  for _, it in pairs(inv.get_contents()) do
    if is_quality_module(it.name) then
      mods[#mods + 1] = it
      total = total + it.count
    end
  end
  if total <= 1 then return 0 end
  local keep, taken = 1, 0                         -- the first one found stays
  for _, it in ipairs(mods) do
    local n = it.count
    if keep > 0 then
      local k = math.min(keep, n)
      n, keep = n - k, keep - k
    end
    if n > 0 then
      local got = inv.remove { name = it.name, quality = it.quality, count = n }
      if got > 0 then
        e.surface.spill_item_stack { position = e.position, stack = { name = it.name, quality = it.quality, count = got },
                                     enable_looted = true, force = e.force, allow_belts = false }
        taken = taken + got
      end
    end
  end
  if taken > 0 then
    E.push { kind = "quality_module", text = taken .. " extra quality module" .. ((taken == 1) and "" or "s") .. " taken out of the " .. e.name
             .. " at " .. math.floor(e.position.x) .. "," .. math.floor(e.position.y) .. " on " .. e.surface.name
             .. ": one is enough for the best quality, more only slow it. They lie beside it, marked for the robots." }
  end
  return taken
end

-- A slice of the machines each second; the list is rebuilt when it runs out.
function Q.on_tick(event)
  if event.tick % 60 ~= 30 or not Q.active() then return end
  local scan = storage.quality_scan
  if not scan or scan.i > #scan.list then
    local list = {}
    for _, s in pairs(game.surfaces) do
      for _, e in pairs(s.find_entities_filtered { type = KINDS, force = "player" }) do list[#list + 1] = e end
    end
    scan = { list = list, i = 1 }
    storage.quality_scan = scan
  end
  local stop = math.min(#scan.list, scan.i + PER_SECOND - 1)
  for i = scan.i, stop do
    local e = scan.list[i]
    if e and e.valid then Q.trim(e) end
  end
  scan.i = stop + 1
end

return Q
