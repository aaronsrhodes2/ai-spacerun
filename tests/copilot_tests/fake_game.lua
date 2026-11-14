-- A stand-in for the parts of the Factorio API the Skippy Copilot mod uses, so the mod's Lua runs under plain Lua 5.2
-- in unit tests. It is deliberately small and literal: it models what the mod calls, not the game. Where the real
-- game behaves differently from this file the unit tests will not notice, which is why scripts/modcheck.py also runs
-- the mod against a real server.
--
-- `helpers.table_to_json` and `helpers.json_to_table` are supplied by the Python harness (luamod.py).

defines = {
  entity_status = { working = 1, normal = 2, no_power = 3, low_power = 4, no_fuel = 5, item_ingredient_shortage = 6,
                    fluid_ingredient_shortage = 7, full_output = 8, no_recipe = 9, frozen = 10 },
  inventory = { chest = 1, crafter_input = 2, crafter_output = 3 },
  alert_type = { entity_destroyed = 0, no_material_for_construction = 3, turret_out_of_ammo = 7, train_out_of_fuel = 9 },
  events = { on_player_created = 1, on_player_joined_game = 2, on_console_chat = 3, on_research_finished = 4 },
  build_check_type = { manual = 1, script = 2 },
  direction = { north = 0, east = 4, south = 8, west = 12 },
}

storage = {}
fake = { handlers = {}, commands = {}, printed = {}, rcon = {}, charted = {} }

script = {
  on_init = function(f) fake.on_init = f end,
  on_configuration_changed = function(f) fake.on_configuration_changed = f end,
  on_event = function(id, f) fake.handlers[id] = f end,
}
commands = { add_command = function(name, help, f) fake.commands[name] = f end }
rcon = { print = function(text) fake.rcon[#fake.rcon + 1] = text end }

-- ---------------------------------------------------------------- prototypes
local function item_part(name, amount, probability)
  return { type = "item", name = name, amount = amount, probability = probability }
end

local RECIPES = {
  ["iron-gear-wheel"] = { energy = 0.5, categories = { crafting = true }, ingredients = { item_part("iron-plate", 2) }, products = { item_part("iron-gear-wheel", 1) } },
  ["copper-cable"] = { energy = 0.5, categories = { crafting = true }, ingredients = { item_part("copper-plate", 1) }, products = { item_part("copper-cable", 2) } },
  ["electronic-circuit"] = { energy = 0.5, categories = { crafting = true, electromagnetics = true },
                             ingredients = { item_part("iron-plate", 1), item_part("copper-cable", 3) }, products = { item_part("electronic-circuit", 1) } },
  ["iron-plate"] = { energy = 3.2, categories = { smelting = true }, ingredients = { item_part("iron-ore", 1) }, products = { item_part("iron-plate", 1) } },
  ["iron-gear-wheel-recycling"] = { energy = 0.1, categories = { recycling = true }, ingredients = { item_part("iron-gear-wheel", 1) }, products = { item_part("iron-plate", 1, 0.25) } },
  ["assembling-machine-2"] = { energy = 0.5, categories = { crafting = true }, ingredients = { item_part("iron-plate", 20) }, products = { item_part("assembling-machine-2", 1) } },
  ["transport-belt"] = { energy = 0.5, categories = { crafting = true }, ingredients = { item_part("iron-plate", 1) }, products = { item_part("transport-belt", 2) } },
  ["underground-belt"] = { energy = 1, categories = { crafting = true }, ingredients = { item_part("iron-plate", 10) }, products = { item_part("underground-belt", 2) } },
  ["inserter"] = { energy = 0.5, categories = { crafting = true }, ingredients = { item_part("iron-plate", 1) }, products = { item_part("inserter", 1) } },
  ["pipe"] = { energy = 0.5, categories = { crafting = true }, ingredients = { item_part("iron-plate", 1) }, products = { item_part("pipe", 1) } },
  ["lab"] = { energy = 2, categories = { crafting = true }, ingredients = { item_part("electronic-circuit", 10) }, products = { item_part("lab", 1) } },
  ["cryogenic-science-pack"] = { energy = 20, categories = { cryogenics = true }, ingredients = { item_part("ice", 3) }, products = { item_part("cryogenic-science-pack", 1) },
                                 surface_conditions = { { property = "pressure", min = 300, max = 300 } } },
}
for name, r in pairs(RECIPES) do r.name = name end

local function item(name, stack, weight, place, extra)
  local p = { name = name, stack_size = stack, weight = weight, place_result = place and { name = place } or nil,
              fuel_value = 0, get_spoil_ticks = function() return 0 end }
  for k, v in pairs(extra or {}) do p[k] = v end
  return p
end

local ITEMS = {
  ["iron-plate"] = item("iron-plate", 100, 1000),
  ["iron-ore"] = item("iron-ore", 50, 2000),
  ["copper-plate"] = item("copper-plate", 100, 1000),
  ["copper-cable"] = item("copper-cable", 200, 250),
  ["iron-gear-wheel"] = item("iron-gear-wheel", 100, 1000),
  ["electronic-circuit"] = item("electronic-circuit", 200, 500),
  ["assembling-machine-2"] = item("assembling-machine-2", 50, 20000, "assembling-machine-2"),
  ["transport-belt"] = item("transport-belt", 100, 10000, "transport-belt"),
  ["coal"] = item("coal", 50, 2000, nil, { fuel_value = 4000000 }),
  ["nutrients"] = item("nutrients", 100, 500, nil, { get_spoil_ticks = function() return 18000 end, spoil_result = { name = "spoilage" } }),
}

local function ent(name, etype, w, h, extra)
  local p = { name = name, type = etype, tile_width = w, tile_height = h, items_to_place_this = { { name = name, count = 1 } },
              get_crafting_speed = function() return nil end, get_max_energy_usage = function() return 0 end,
              get_supply_area_distance = function() return 0 end, get_max_wire_distance = function() return 0 end }
  for k, v in pairs(extra or {}) do p[k] = v end
  return p
end

local ENTITIES = {
  ["assembling-machine-2"] = ent("assembling-machine-2", "assembling-machine", 3, 3, {
    crafting_categories = { crafting = true, ["advanced-crafting"] = true }, module_inventory_size = 2,
    get_crafting_speed = function() return 0.75 end, get_max_energy_usage = function() return 2500 end }),
  ["electromagnetic-plant"] = ent("electromagnetic-plant", "assembling-machine", 4, 4, {
    crafting_categories = { electromagnetics = true }, get_crafting_speed = function() return 2 end }),
  ["stone-furnace"] = ent("stone-furnace", "furnace", 2, 2, { crafting_categories = { smelting = true }, get_crafting_speed = function() return 1 end }),
  ["transport-belt"] = ent("transport-belt", "transport-belt", 1, 1, { belt_speed = 0.03125 }),
  ["underground-belt"] = ent("underground-belt", "underground-belt", 1, 1),
  ["inserter"] = ent("inserter", "inserter", 1, 1),
  ["pipe"] = ent("pipe", "pipe", 1, 1),
  ["pipe-to-ground"] = ent("pipe-to-ground", "pipe-to-ground", 1, 1),
  ["electric-mining-drill"] = ent("electric-mining-drill", "mining-drill", 3, 3, { mining_speed = 0.5 }),
  ["medium-electric-pole"] = ent("medium-electric-pole", "electric-pole", 1, 1, {
    get_supply_area_distance = function() return 3.5 end, get_max_wire_distance = function() return 9 end }),
  ["lab"] = ent("lab", "lab", 3, 3),
  ["heating-tower"] = ent("heating-tower", "reactor", 3, 3, {
    heat_buffer_prototype = { max_temperature = 1000, connections = { { position = { 0, -1 } }, { position = { 1, 0 } }, { position = { 0, 1 } }, { position = { -1, 0 } } } },
    surface_conditions = { { property = "pressure", min = 10, max = 1.7976931348623157e308 } } }),
  ["iron-ore"] = ent("iron-ore", "resource", 1, 1, { items_to_place_this = {} }),
  ["tree-01"] = ent("tree-01", "tree", 1, 1, { items_to_place_this = {} }),
  ["character"] = ent("character", "character", 1, 1, { items_to_place_this = {} }),
}

local TECHS = {
  ["automation-2"] = { research_unit_count = 40, research_unit_ingredients = { { name = "automation-science-pack" }, { name = "logistic-science-pack" } },
                       effects = { { type = "unlock-recipe", recipe = "assembling-machine-2" } } },
  ["electronics"] = { research_unit_count = 30, research_unit_ingredients = { { name = "automation-science-pack" } },
                      effects = { { type = "unlock-recipe", recipe = "electronic-circuit" }, { type = "unlock-recipe", recipe = "lab" } } },
  ["speed-module-2"] = { research_unit_count = 75, research_unit_ingredients = {}, effects = { { type = "nothing" } } },
  ["cryogenic-science-pack"] = { research_unit_ingredients = {}, research_trigger = { type = "craft-item", item = "cryogenic-plant", count = 1 },
                                 effects = { { type = "unlock-recipe", recipe = "cryogenic-science-pack" } } },
  ["worker-robots-speed-1"] = { research_unit_count = 50, research_unit_ingredients = {}, effects = { { type = "worker-robot-speed" } } },
}
for name, t in pairs(TECHS) do t.name = name end

prototypes = {
  recipe = RECIPES, item = ITEMS, entity = ENTITIES, technology = TECHS,
  fluid = { water = { name = "water", default_temperature = 15 } },
  tile = { ["out-of-map"] = {}, ["empty-space"] = {}, water = {}, ["grass-1"] = {} },
  get_entity_filtered = function(filters)
    local out = {}
    for name, e in pairs(ENTITIES) do
      if e.crafting_categories then out[name] = e end
    end
    return out
  end,
}

-- ---------------------------------------------------------------- force
local force = { name = "player", recipes = {}, technologies = {}, current_research = nil, research_progress = 0 }
for name, r in pairs(RECIPES) do
  force.recipes[name] = { name = name, enabled = true, ingredients = r.ingredients, products = r.products }
end
for name, t in pairs(TECHS) do
  force.technologies[name] = { name = name, researched = false, prerequisites = {}, prototype = t, force = force }
end
force.technologies["automation-2"].prerequisites = { electronics = force.technologies["electronics"] }
force.chart = function(surface, area) fake.charted[#fake.charted + 1] = { surface = surface.name, area = area } end
force.is_chunk_charted = function(surface, chunk) return surface.charted[chunk.x .. "," .. chunk.y] == true end

-- ---------------------------------------------------------------- surfaces and entities
local WATER = { water = true, deepwater = true }

local function make_tile(name)
  return { valid = true, name = name, collides_with = function(mask) return mask == "water_tile" and WATER[name] == true end }
end

local function overlap(box, area)
  return box.left_top.x < area[2][1] and box.right_bottom.x > area[1][1] and box.left_top.y < area[2][2] and box.right_bottom.y > area[1][2]
end

local function one_of(value, want)
  if want == nil then return true end
  if type(want) == "table" then
    for _, w in pairs(want) do
      if w == value then return true end
    end
    return false
  end
  return want == value
end

local function new_surface(name, index)
  local s = { name = name, index = index, entities = {}, tiles = {}, charted = {}, valid = true }

  function s.get_tile(x, y)
    return make_tile(s.tiles[math.floor(x) .. "," .. math.floor(y)] or "grass-1")
  end

  function s.set(x, y, tile) s.tiles[x .. "," .. y] = tile end

  function s.find_entities_filtered(f)
    local out = {}
    for _, e in ipairs(s.entities) do
      if e.valid and one_of(e.type, f.type) and one_of(e.name, f.name)
        and (f.force == nil or e.force == nil or e.force.name == (type(f.force) == "table" and f.force.name or f.force))
        and (f.area == nil or overlap(e.bounding_box, f.area)) then
        out[#out + 1] = e
        if f.limit and #out >= f.limit then break end
      end
    end
    return out
  end

  function s.count_entities_filtered(f) return #s.find_entities_filtered(f) end

  function s.count_tiles_filtered(f)
    local n = 0
    for x = math.floor(f.area[1][1]), math.ceil(f.area[2][1]) - 1 do
      for y = math.floor(f.area[1][2]), math.ceil(f.area[2][2]) - 1 do
        local t = s.get_tile(x, y)
        if (f.collision_mask == "water_tile" and t.collides_with("water_tile")) or (f.name and t.name == f.name) then n = n + 1 end
      end
    end
    return n
  end

  local function footprint(name, position)
    local p = ENTITIES[name]
    local x, y = position[1] or position.x, position[2] or position.y
    return { left_top = { x = x - p.tile_width / 2, y = y - p.tile_height / 2 }, right_bottom = { x = x + p.tile_width / 2, y = y + p.tile_height / 2 } }
  end

  function s.can_place_entity(a)
    local box = footprint(a.name, a.position)
    local area = { { box.left_top.x, box.left_top.y }, { box.right_bottom.x, box.right_bottom.y } }
    for _, e in ipairs(s.entities) do
      if e.valid and e.type ~= "resource" and overlap(e.bounding_box, area) then return false end
    end
    for x = math.floor(area[1][1] + 0.01), math.ceil(area[2][1] - 0.01) - 1 do
      for y = math.floor(area[1][2] + 0.01), math.ceil(area[2][2] - 0.01) - 1 do
        local t = s.get_tile(x, y)
        if t.collides_with("water_tile") or t.name == "out-of-map" or t.name == "empty-space" then return false end
      end
    end
    return true
  end

  -- status is a name from defines.entity_status; items and fluids are what the machine holds
  function s.create_entity(a)
    local p = ENTITIES[a.ghost and "lab" or a.name]
    if not p and a.name ~= "entity-ghost" then return nil end
    local x, y = a.position[1] or a.position.x, a.position[2] or a.position.y
    local e = { name = a.name, type = p and p.type or "entity-ghost", position = { x = x, y = y }, direction = a.direction or 0,
                force = (a.force ~= false) and force or nil, valid = true, recipe = a.recipe, items = a.items or {}, fluids = a.fluids or {},
                belt_to_ground_type = a.type, amount = a.amount, surface = s }
    if a.name == "entity-ghost" then
      e.ghost_name = a.inner_name
      p = ENTITIES[a.inner_name]
    end
    e.bounding_box = { left_top = { x = x - p.tile_width / 2 + 0.1, y = y - p.tile_height / 2 + 0.1 },
                       right_bottom = { x = x + p.tile_width / 2 - 0.1, y = y + p.tile_height / 2 - 0.1 } }
    if a.status then e.status = defines.entity_status[a.status] end
    function e.get_recipe()
      if not e.recipe then return nil end
      local r = RECIPES[e.recipe]
      return { name = e.recipe, ingredients = r.ingredients, products = r.products }
    end
    function e.set_recipe(name) e.recipe = name end
    function e.get_inventory(id)
      if id ~= defines.inventory.crafter_input then return nil end
      return { get_item_count = function(n) return e.items[n] or 0 end }
    end
    function e.get_fluid_contents() return e.fluids end
    function e.destroy() e.valid = false end
    s.entities[#s.entities + 1] = e
    return e
  end

  function s.get_chunks()
    local list, i = {}, 0
    for key in pairs(s.charted) do
      local cx, cy = string.match(key, "(-?%d+),(-?%d+)")
      list[#list + 1] = { x = tonumber(cx), y = tonumber(cy) }
    end
    return function()
      i = i + 1
      return list[i]
    end
  end

  return s
end

local nauvis = new_surface("nauvis", 1)

-- ---------------------------------------------------------------- players and gui
local function element(spec)
  local el = { type = spec.type, name = spec.name, caption = spec.caption, style = {}, children = {} }
  function el.add(child_spec)
    local c = element(child_spec)
    el.children[#el.children + 1] = c
    if c.name then el[c.name] = c end
    return c
  end
  return el
end

function fake.add_player(name, x, y, admin)
  local p = { name = name, index = #game.players + 1, position = { x = x, y = y }, surface = nauvis, admin = admin ~= false, valid = true,
              zoom = 1, display_resolution = { width = 1920, height = 1080 }, selected = nil, printed = {}, alerts = {},
              gui = { top = element { type = "flow" } } }
  function p.print(text) p.printed[#p.printed + 1] = text end
  function p.get_alerts() return p.alerts end
  game.players[#game.players + 1] = p
  game.connected_players[#game.connected_players + 1] = p
  if fake.handlers[defines.events.on_player_created] then fake.handlers[defines.events.on_player_created] { player_index = p.index } end
  return p
end

game = {
  tick = 100,
  surfaces = { nauvis = nauvis, [1] = nauvis },
  forces = { player = force },
  players = {}, connected_players = {},
  get_player = function(key)
    for _, p in ipairs(game.players) do
      if p.index == key or p.name == key then return p end
    end
  end,
  get_surface = function(index)
    for _, s in pairs(game.surfaces) do
      if s.index == index then return s end
    end
  end,
  print = function(text) fake.printed[#fake.printed + 1] = text end,
}

-- ---------------------------------------------------------------- what the harness calls
function fake.command(text, player_index)
  fake.rcon = {}
  fake.commands["skippy"] { parameter = text, player_index = player_index }
  return fake.rcon[#fake.rcon]
end

function fake.research(name)
  local t = force.technologies[name]
  t.researched = true
  fake.handlers[defines.events.on_research_finished] { research = t }
end

function fake.chat(player_index, message)
  fake.handlers[defines.events.on_console_chat] { player_index = player_index, message = message, tick = game.tick }
end
