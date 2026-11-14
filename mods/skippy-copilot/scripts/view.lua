-- Frames for pointing with words (the Captain, 2026-11-13). A player with no mouse says "the middle of the screen",
-- "the east of the base", "the upper right of my view". The bridge turns such words into a rectangle; it needs the
-- frames those words refer to, which only the game knows: what is on screen, where the base lies, how far the map goes.
local R = require("scripts.registry")
local A = require("scripts.alerts")
local V = require("scripts.avatar")

local function rect(left, top, right, bottom)
  return { math.floor(left), math.floor(top), math.floor(right), math.floor(bottom) }
end

-- What the player can see. A tile is 32 pixels at zoom 1; this ignores the interface panels at the screen edges,
-- so the true view is a little smaller.
local function view_of(p)
  local res, zoom = p.display_resolution, p.zoom
  if not res or not zoom or zoom <= 0 then return nil end
  local scale = 32 * zoom
  local w, h = res.width / scale, res.height / scale
  return rect(p.position.x - w / 2, p.position.y - h / 2, p.position.x + w / 2, p.position.y + h / 2)
end

-- Where our buildings stand: the rectangle round every electric pole. Poles are everywhere a base is, and far fewer
-- than buildings, so this stays cheap on a large map.
local function base_of(surface)
  local l, t, r, b
  for _, e in pairs(surface.find_entities_filtered { type = "electric-pole", force = "player" }) do
    local x, y = e.position.x, e.position.y
    l, t, r, b = math.min(l or x, x), math.min(t or y, y), math.max(r or x, x), math.max(b or y, y)
  end
  if not l then return nil end
  return rect(l, t, r, b)
end

-- How far the revealed map goes.
local function map_of(surface)
  local force = game.forces.player
  local l, t, r, b
  for chunk in surface.get_chunks() do
    if force.is_chunk_charted(surface, chunk) then
      l, t = math.min(l or chunk.x, chunk.x), math.min(t or chunk.y, chunk.y)
      r, b = math.max(r or chunk.x, chunk.x), math.max(b or chunk.y, chunk.y)
    end
  end
  if not l then return nil end
  return rect(l * 32, t * 32, r * 32 + 31, b * 32 + 31)
end

R.register {
  name = "frames",
  description = "For the 'locate' tool: the rectangles that spoken places refer to. view = what the player sees on screen, base = where our buildings stand, map = how far the revealed map goes, player = the tiles around the player. Each is [left, top, right, bottom].",
  params = {
    name = { type = "string", description = "player name; leave out for the first player in the game" },
  },
  run = function(a)
    local p
    if a.name then p = game.get_player(a.name) else p = A.any_player() end          -- a name that is not in the game is an error, not somebody else
    if not p then
      return { error = a.name and ("no player named '" .. a.name .. "' is in the game") or "no player is in the game, so there is no view to point in" }
    end
    local s = p.surface
    return {
      surface = s.name, view = view_of(p), base = base_of(s), map = map_of(s),
      player = rect(p.position.x - 15, p.position.y - 15, p.position.x + 15, p.position.y + 15),
    }
  end,
}

R.register {
  name = "reveal_map",
  description = "Reveal more of the map round the edge of what is known, as if someone walked the perimeter. depth is how many tiles outward to reveal. Use it for 'explore' or 'show me more of the map'; then use 'map' or a resource search on the new ground.",
  params = {
    depth = { type = "number", default = 64, description = "tiles to reveal beyond the known edge, at most 320" },
    surface = { type = "string", description = "surface name; leave out for where the player is" },
  },
  run = function(a)
    if V.executor() ~= "god" then
      return { error = "exploring on foot is not built yet", hint = "walk the avatar toward the edge with walk_to, or ask the player to switch to free-hand mode" }
    end
    local p = A.any_player()
    local s = a.surface and game.surfaces[a.surface] or (p and p.surface) or game.surfaces.nauvis
    if not s then return { error = "there is no surface named '" .. tostring(a.surface) .. "'" } end
    local m = map_of(s) or rect(-32, -32, 31, 31)
    local d = math.max(32, math.min(math.floor(a.depth), 320))
    local area = { { m[1] - d, m[2] - d }, { m[3] + d, m[4] + d } }
    game.forces.player.chart(s, area)
    return { surface = s.name, was = m, now = { m[1] - d, m[2] - d, m[3] + d, m[4] + d }, note = "new ground appears on the map over the next few seconds" }
  end,
}
