-- Place names: the map tags (chart tags) of our force, read as an address book. A model refers to "Copper outpost B" or
-- "free land east" instead of carrying coordinates in its head; the player sees the same names on the map and can add,
-- move or rename them. Every tag is read, the player's too. Only tags the mod made (remembered by their tag number) are
-- moved or removed by it: never what someone else wrote.
local R = require("scripts.registry")

local P = {}
local MAX_SHOWN = 60

local function ours()
  storage.places_ours = storage.places_ours or {}
  return storage.places_ours
end

local function icon_of(tag)
  local i = tag.icon
  return i and i.name and ((i.type or "item") .. ":" .. i.name) or nil
end

local function row(tag)
  return { name = tag.text, surface = tag.surface.name, x = math.floor(tag.position.x), y = math.floor(tag.position.y),
           icon = icon_of(tag), ours = ours()[tag.tag_number] == true }
end

local function surfaces(name)
  if name and name ~= "" then
    local s = game.surfaces[name]
    if not s then return nil, { error = "there is no surface named '" .. name .. "'" } end
    return { s }
  end
  local list, seen = {}, {}
  for _, s in pairs(game.surfaces) do
    if s.valid and not seen[s.index] then seen[s.index] = true list[#list + 1] = s end
  end
  table.sort(list, function(a, b) return a.index < b.index end)
  return list
end

-- Every tag on the given surfaces, in a stable order.
local function all_tags(list)
  local f = game.forces.player
  local out = {}
  for _, s in ipairs(list) do
    for _, t in pairs(f.find_chart_tags(s)) do
      if t.valid and t.text and t.text ~= "" then out[#out + 1] = t end
    end
  end
  table.sort(out, function(a, b)
    if a.surface.index ~= b.surface.index then return a.surface.index < b.surface.index end
    return a.text:lower() < b.text:lower()
  end)
  return out
end

-- The tag a name means: an exact name (case does not matter), else the only tag whose name contains it.
-- -> tag, or nil and an error table.
local function find(name, surface_name)
  local list, err = surfaces(surface_name)
  if not list then return nil, err end
  local want = tostring(name):lower()
  local exact, partial = {}, {}
  for _, t in ipairs(all_tags(list)) do
    local text = t.text:lower()
    if text == want then exact[#exact + 1] = t
    elseif text:find(want, 1, true) then partial[#partial + 1] = t end
  end
  local hits = (#exact > 0) and exact or partial
  if #hits == 1 then return hits[1] end
  if #hits == 0 then
    return nil, { error = "there is no place named '" .. tostring(name) .. "'", hint = "the 'places' tool lists the names on the map" }
  end
  local names = {}
  for i, t in ipairs(hits) do
    if i > 8 then break end
    names[#names + 1] = t.text .. " (" .. t.surface.name .. ")"
  end
  return nil, { error = "'" .. tostring(name) .. "' fits more than one place: " .. table.concat(names, ", "), hint = "give the whole name, or the surface" }
end

-- For other tools: a place name to a surface and a tile. -> { surface, x, y, name } or nil and an error table.
function P.resolve(name, surface_name)
  local t, err = find(name, surface_name)
  if not t then return nil, err end
  return { surface = t.surface, x = t.position.x, y = t.position.y, name = t.text }
end

local function icon_spec(text)
  if not text or text == "" then return { type = "virtual", name = "signal-info" } end
  local kind, name = string.match(text, "^(%a+):(.+)$")
  name = name or text
  if (kind == nil or kind == "item") and prototypes.item[name] then return { type = "item", name = name } end
  local virtual = prototypes.virtual_signal
  if (kind == nil or kind == "virtual") and (virtual == nil or virtual[name]) then return { type = "virtual", name = name } end
  return nil
end

R.register {
  name = "places",
  description = "The named places on the map (map tags, the player's and ours) with their tiles. Tools that take 'at' accept these names.",
  params = {
    surface = { type = "string", description = "surface name; leave out for every surface" },
    near = { type = "string", description = "names containing this" },
  },
  run = function(a)
    local list, err = surfaces(a.surface)
    if not list then return err end
    local out, total = {}, 0
    local want = a.near and a.near:lower() or nil
    for _, t in ipairs(all_tags(list)) do
      if not want or t.text:lower():find(want, 1, true) then
        total = total + 1
        if #out < MAX_SHOWN then out[#out + 1] = row(t) end
      end
    end
    return { places = out, count = total, more_not_shown = math.max(0, total - #out),
             hint = (total == 0) and "no named places yet: mark_place names one" or nil }
  end,
}

R.register {
  name = "mark_place",
  description = "Name a place worth coming back to (an outpost, a build site, free land) with a map tag the player sees too; an existing name of ours moves. The ground must be charted.",
  params = {
    name = { type = "string", required = true, description = "a few words" },
    x = { type = "number", required = true, description = "tile x" },
    y = { type = "number", required = true, description = "tile y" },
    surface = { type = "string", description = "surface name; leave out for where the player is" },
    icon = { type = "string", description = "an item or virtual signal name" },
  },
  run = function(a)
    local G = require("scripts.grid")
    local s, err = G.surface_of(a.surface)
    if not s then return err end
    local icon = icon_spec(a.icon)
    if not icon then return { error = "there is no item or signal named '" .. tostring(a.icon) .. "'" } end
    local name = string.match(a.name, "^%s*(.-)%s*$")
    if name == "" then return { error = "a place needs a name" } end
    local f = game.forces.player
    local moved = false
    for _, t in ipairs(all_tags(surfaces())) do
      if t.text:lower() == name:lower() then
        if not ours()[t.tag_number] then
          return { error = "the player's own tag is already called '" .. t.text .. "'", hint = "choose another name; the mod does not move the player's tags" }
        end
        ours()[t.tag_number] = nil
        t.destroy()
        moved = true
      end
    end
    local tag = f.add_chart_tag(s, { position = { a.x + 0.5, a.y + 0.5 }, text = name, icon = icon })
    if not tag then
      return { error = "the game did not take the tag", hint = "the ground there must be charted first (reveal_map, or a radar)" }
    end
    ours()[tag.tag_number] = true
    return { place = row(tag), moved = moved }
  end,
}

R.register {
  name = "forget_place",
  description = "Remove one of our named places (never the player's).",
  params = {
    name = { type = "string", required = true, description = "the place's name" },
    surface = { type = "string", description = "surface name, if needed" },
  },
  run = function(a)
    local t, err = find(a.name, a.surface)
    if not t then return err end
    if not ours()[t.tag_number] then
      return { error = "'" .. t.text .. "' is the player's tag, not ours", hint = "ask the player to remove it" }
    end
    local was = row(t)
    ours()[t.tag_number] = nil
    t.destroy()
    return { removed = was }
  end,
}

return P
