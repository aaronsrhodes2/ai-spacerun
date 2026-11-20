-- Ghosts to requests. The game has no way to turn a ghost into a logistic request (vanilla robots only take from chests that
-- already hold the item; nothing asks for what is missing, and nothing asks orbit at all). This module closes that gap, gated by
-- the allowance 'ghost-requests': it totals the items the entity and tile ghosts of a logistic network need, subtracts what the
-- network already holds, and writes the shortfall as requests, either
--   into a cargo landing pad's request list, section group "ghost-auto-<surface>" (ours alone, rewritten each time), which is
--   the one link from a planet to the platforms in orbit, or
--   into one requester chest (chest_x, chest_y), whose unmet requests anything that makes goods for requesters can read.
-- A ghost asks for its own quality exactly. Ghosts outside roboport coverage are counted and not requested: no robot can build
-- them. Nothing is created and no ghost is touched; the requests only ask. Choosing what quality to build at is policy and
-- stays outside (scripts/ghost_requests.py).
local R = require("scripts.registry")
local AL = require("scripts.allowances")

local GROUP = "ghost-auto"
local DEFAULT_STACKS = 40

-- The network ghosts are counted against on a surface: the landing pad's, else the biggest roboport network.
local function main_network(s, f, pad)
  local net = pad and (pad.logistic_network or s.find_logistic_network_by_position(pad.position, f)) or nil
  local from = "the cargo landing pad's network"
  if not net then
    from = "the largest roboport network"
    for _, rp in pairs(s.find_entities_filtered { type = "roboport", force = f }) do
      local n = rp.logistic_network
      if n and (not net or #n.cells > #net.cells) then net = n end
    end
  end
  return net, from
end

-- What the ghosts inside `net` need: rows {name, quality, need, have, short, stack}, and how many ghosts are inside and outside.
local function needs(s, f, net)
  local by, inside, outside = {}, 0, 0
  local function add(g)
    local n = s.find_logistic_network_by_position(g.position, f)
    if not n or n.network_id ~= net.network_id then outside = outside + 1 return end
    inside = inside + 1
    local proto = g.ghost_prototype
    local quality = (g.quality and g.quality.name) or "normal"
    for _, it in pairs((proto and proto.items_to_place_this) or {}) do
      local key = it.name .. " " .. quality
      local row = by[key]
      if not row then
        local item = prototypes.item[it.name]
        row = { name = it.name, quality = quality, need = 0, stack = item and item.stack_size or 1 }
        by[key] = row
      end
      row.need = row.need + it.count
    end
  end
  for _, g in pairs(s.find_entities_filtered { type = "entity-ghost", force = f }) do add(g) end
  for _, g in pairs(s.find_entities_filtered { type = "tile-ghost", force = f }) do add(g) end
  local rows = {}
  for _, row in pairs(by) do
    row.have = net.get_item_count { name = row.name, quality = row.quality }
    row.short = math.max(0, row.need - row.have)
    rows[#rows + 1] = row
  end
  table.sort(rows, function(a, b)
    local sa, sb = a.short / a.stack, b.short / b.stack
    if sa ~= sb then return sa > sb end
    if a.name ~= b.name then return a.name < b.name end
    return a.quality < b.quality
  end)
  return rows, inside, outside
end

-- The biggest shortfalls first, as many as fit in `max_stacks` stacks.
local function pick(rows, max_stacks)
  local chosen, used = {}, 0
  for _, row in ipairs(rows) do
    if row.short > 0 then
      local stacks = math.ceil(row.short / row.stack)
      if used + stacks <= max_stacks then
        used = used + stacks
        chosen[#chosen + 1] = row
      end
    end
  end
  return chosen, used
end

local function surfaces_to_look_at(name)
  if name and name ~= "" then
    local s = game.surfaces[name]
    return s and { s } or nil, "there is no surface named '" .. name .. "'"
  end
  local list, seen = {}, {}
  for _, s in pairs(game.surfaces) do
    if s.valid and not seen[s.index] then seen[s.index] = true list[#list + 1] = s end
  end
  table.sort(list, function(a, b) return a.index < b.index end)
  return list
end

local function view_row(row)
  return { item = row.name, quality = row.quality, need = row.need, have = row.have, short = row.short }
end

R.register {
  name = "ghost_needs",
  description = "What the ghosts (unbuilt blueprint pieces) of a surface still need: per item and quality, how many the ghosts use, how many the logistic network holds and how many are short. Ghosts outside roboport coverage are counted apart: no robot can build them. Read only.",
  params = {
    surface = { type = "string", description = "surface name; leave out for every surface that has a logistic network of ours" },
  },
  run = function(a)
    local list, err = surfaces_to_look_at(a.surface)
    if not list then return { error = err } end
    local f = game.forces.player
    local out = {}
    for _, s in ipairs(list) do
      local pad = s.find_entities_filtered { type = "cargo-landing-pad", force = f }[1]
      local net, from = main_network(s, f, pad)
      if net then
        local rows, inside, outside = needs(s, f, net)
        local shown = {}
        for i, row in ipairs(rows) do
          if i > 40 then break end
          shown[#shown + 1] = view_row(row)
        end
        out[#out + 1] = { surface = s.name, network = from, ghosts_inside = inside, ghosts_outside_coverage = outside, kinds = #rows, items = shown }
      elseif a.surface then
        out[#out + 1] = { surface = s.name, error = "no logistic network of ours there" }
      end
    end
    return { surfaces = out }
  end,
}

-- Rewrite the pad's section for this surface. -> number of slots written, or nil and a reason.
local function write_pad(s, f, chosen)
  local pad = s.find_entities_filtered { type = "cargo-landing-pad", force = f }[1]
  if not pad then return nil, "no cargo landing pad" end
  local point
  for _, q in pairs(pad.get_logistic_point()) do
    if q.mode == defines.logistic_mode.requester then point = q end
  end
  if not point then return nil, "the pad has no requester point" end
  local group = GROUP .. "-" .. s.name
  for i = point.sections_count, 1, -1 do
    local g = point.sections[i].group
    if g == group or g == GROUP then point.remove_section(i) end
  end
  if #chosen > 0 then
    local sec = point.add_section(group)
    local inv = pad.get_inventory(defines.inventory.cargo_landing_pad_main)
    for i, row in ipairs(chosen) do
      local want = row.short + (inv and inv.get_item_count { name = row.name, quality = row.quality } or 0)
      sec.set_slot(i, { value = { type = "item", name = row.name, quality = row.quality }, min = want, max = want })
    end
  end
  return #chosen
end

-- Rewrite the first section of a requester chest. -> number of slots written, or nil and a reason.
local function write_chest(chest, chosen)
  local point = chest.get_logistic_point(defines.logistic_member_index.logistic_container)
  if not point then return nil, "that chest has no logistic point" end
  local sec = point.sections[1] or point.add_section()
  sec.filters = {}
  for i, row in ipairs(chosen) do
    sec.set_slot(i, { value = { type = "item", name = row.name, quality = row.quality }, min = row.short })
  end
  return #chosen
end

R.register {
  name = "ghost_requests",
  description = "Turn the ghosts' shortfall into requests, which the game never does by itself: into a surface's cargo landing pad (so platforms in orbit bring the goods), or, when chest_x and chest_y are given, into the requester chest there. Dry run unless apply is true. Rewrites only its own request section; creates nothing. Run it again after the ghosts change.",
  params = {
    surface = { type = "string", description = "surface name; leave out for every surface with a landing pad (not with a chest)" },
    apply = { type = "boolean", default = false, description = "true to write the requests; false counts them" },
    max_stacks = { type = "number", default = DEFAULT_STACKS, description = "most stacks one surface's requests may ask for in total" },
    chest_x = { type = "number", description = "x of a requester chest to write into instead of the landing pad" },
    chest_y = { type = "number", description = "y of that chest" },
  },
  run = function(a)
    local f = game.forces.player
    local apply = a.apply == true
    if apply and not AL.on("ghost-requests") then
      return { error = "writing requests from ghosts is switched off (the allowance 'ghost-requests')",
               hint = "the player can allow it again; a dry run (apply false) still works" }
    end
    local to_chest = a.chest_x ~= nil or a.chest_y ~= nil
    if to_chest and (a.chest_x == nil or a.chest_y == nil or not a.surface) then
      return { error = "a chest needs surface, chest_x and chest_y together" }
    end
    local list, err = surfaces_to_look_at(a.surface)
    if not list then return { error = err } end
    local max_stacks = math.max(1, math.floor(a.max_stacks or DEFAULT_STACKS))
    local out = {}
    for _, s in ipairs(list) do
      local entry = { surface = s.name }
      local chest
      if to_chest then
        chest = s.find_entities_filtered { name = "requester-chest", position = { a.chest_x, a.chest_y }, radius = 0.4 }[1]
        if not chest then entry.skipped = "no requester chest at " .. a.chest_x .. "," .. a.chest_y end
      end
      local pad = (not to_chest) and s.find_entities_filtered { type = "cargo-landing-pad", force = f }[1] or nil
      if not entry.skipped and not to_chest and not pad then entry.skipped = "no cargo landing pad" end
      local net, from
      if not entry.skipped then
        if chest then net, from = chest.logistic_network, "the chest's network" else net, from = main_network(s, f, pad) end
        if not net then entry.skipped = "no logistic network there" end
      end
      if not entry.skipped then
        local rows, inside, outside = needs(s, f, net)
        local chosen, used = pick(rows, max_stacks)
        entry.network, entry.ghosts_inside, entry.ghosts_outside_coverage = from, inside, outside
        entry.slots, entry.stacks = #chosen, used
        local shown = {}
        for i, row in ipairs(chosen) do
          if i > 12 then break end
          shown[#shown + 1] = view_row(row)
        end
        entry.items = shown
        if apply then
          local n, why
          if chest then n, why = write_chest(chest, chosen) else n, why = write_pad(s, f, chosen) end
          if n then entry.wrote = n else entry.skipped = why end
        end
      end
      out[#out + 1] = entry
    end
    return { surfaces = out, applied = apply, note = apply and "requests written" or "dry run: nothing was written" }
  end,
}

return { GROUP = GROUP }
