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
  events = { on_player_created = 1, on_player_joined_game = 2, on_console_chat = 3, on_research_finished = 4, on_tick = 5,
             on_script_path_request_finished = 6, on_runtime_mod_setting_changed = 7, on_gui_click = 8 },
  build_check_type = { manual = 1, script = 2 },
  flow_precision_index = { one_minute = 1, ten_minutes = 2, one_hour = 3 },
  rocket_silo_status = { building_rocket = 1, rocket_ready = 2, launch_started = 3 },
  cargo_destination = { invalid = 0, orbit = 1, station = 2, surface = 3 },
  direction = { north = 0, northeast = 2, east = 4, southeast = 6, south = 8, southwest = 10, west = 12, northwest = 14 },
}

storage = {}
settings = { global = { ["skippy-copilot-mode"] = { value = "free-hand" } } }
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
  ["automation-science-pack"] = { energy = 5, categories = { crafting = true }, ingredients = { item_part("copper-plate", 1), item_part("iron-gear-wheel", 1) }, products = { item_part("automation-science-pack", 1) } },
  ["logistic-science-pack"] = { energy = 6, categories = { crafting = true }, ingredients = { item_part("inserter", 1), item_part("transport-belt", 1) }, products = { item_part("logistic-science-pack", 1) } },
  ["chemical-science-pack"] = { energy = 24, categories = { crafting = true }, ingredients = { item_part("iron-plate", 2) }, products = { item_part("chemical-science-pack", 2) } },
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
  ["automation-science-pack"] = item("automation-science-pack", 200, 1000),
  ["logistic-science-pack"] = item("logistic-science-pack", 200, 1000),
  ["chemical-science-pack"] = item("chemical-science-pack", 200, 1000),
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
  ["lab"] = ent("lab", "lab", 3, 3, { lab_inputs = { "automation-science-pack", "logistic-science-pack", "chemical-science-pack" } }),
  ["heating-tower"] = ent("heating-tower", "reactor", 3, 3, {
    heat_buffer_prototype = { max_temperature = 1000, connections = { { position = { 0, -1 } }, { position = { 1, 0 } }, { position = { 0, 1 } }, { position = { -1, 0 } } } },
    surface_conditions = { { property = "pressure", min = 10, max = 1.7976931348623157e308 } } }),
  ["iron-ore"] = ent("iron-ore", "resource", 1, 1, { items_to_place_this = {}, mineable_properties = { products = { { name = "iron-ore" } } } }),
  ["tree-01"] = ent("tree-01", "tree", 1, 1, { items_to_place_this = {}, mineable_properties = { products = { { name = "wood" } } } }),
  ["cliff"] = ent("cliff", "cliff", 1, 1, { items_to_place_this = {}, mineable_properties = {} }),
  ["wooden-chest"] = ent("wooden-chest", "container", 1, 1),
  ["rocket-silo"] = ent("rocket-silo", "rocket-silo", 9, 9),
  ["space-platform-hub"] = ent("space-platform-hub", "space-platform-hub", 8, 8, { items_to_place_this = {} }),
  ["character"] = ent("character", "character", 1, 1, { items_to_place_this = {},
    collision_box = { left_top = { x = -0.2, y = -0.2 }, right_bottom = { x = 0.2, y = 0.2 } }, collision_mask = { layers = { player = true } } }),
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
    local f = filters[1]
    for name, e in pairs(ENTITIES) do
      if (f.filter == "crafting-machine" and e.crafting_categories) or (f.filter == "type" and e.type == f.type) then out[name] = e end
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
        and (f.area == nil or overlap(e.bounding_box, f.area))
        and (f.position == nil or math.sqrt(((f.position.x or f.position[1]) - e.position.x) ^ 2 + ((f.position.y or f.position[2]) - e.position.y) ^ 2) <= (f.radius or 0.5)) then
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
    e.prototype = p
    function e.remove_item(a2)
      local have = e.items[a2.name] or 0
      local n = math.min(have, a2.count)
      e.items[a2.name] = have - n
      return n
    end
    function e.insert(a2)
      local room = e.capacity and math.max(0, e.capacity - (e.items[a2.name] or 0)) or a2.count
      local n = math.min(room, a2.count)
      e.items[a2.name] = (e.items[a2.name] or 0) + n
      return n
    end
    if a.name == "character" then fake.make_character(e) end
    if a.name == "rocket-silo" then fake.make_silo(e, a.rocket_ready) end
    if a.name == "space-platform-hub" then fake.make_hub(e) end
    s.entities[#s.entities + 1] = e
    return e
  end

  function s.find_non_colliding_position(name, centre, radius, precision)
    local cx, cy = centre[1] or centre.x, centre[2] or centre.y
    for r = 0, radius do
      for dx = -r, r do
        for dy = -r, r do
          local pos = { cx + dx + 0.5, cy + dy + 0.5 }
          if s.can_place_entity { name = name, position = pos } then return { x = pos[1], y = pos[2] } end
        end
      end
    end
    return nil
  end

  function s.request_path(a2)
    fake.next_path = (fake.next_path or 0) + 1
    fake.path_requests[#fake.path_requests + 1] = { id = fake.next_path, start = { x = a2.start.x, y = a2.start.y }, goal = { x = a2.goal.x, y = a2.goal.y }, args = a2 }
    return fake.next_path
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
fake.new_surface = new_surface

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
  if fake.players_have_bodies then                      -- the player's character; the player's position is the character's
    p.character = nauvis.create_entity { name = "character", position = { x, y } }
    p.position = p.character.position
    function p.land_on_planet()                         -- leave the platform for the planet below
      local platform = p.character.surface.platform
      if not platform or not platform.space_location then return false end
      local ground = game.planets[platform.space_location.name].surface
      if not ground then return false end
      p.character.in_flight = true
      fake.flights[#fake.flights + 1] = { who = p.character, to = ground, x = 0.5, y = 0.5, left = fake.rocket_ticks }
      return true
    end
  end
  setmetatable(p, { __index = function(t, k)             -- where the player really is, character or not
    if k == "physical_surface" then return t.character and t.character.surface or t.surface end
  end })
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
  planets = {},
  finished = false, finished_but_continuing = false,
  get_surface = function(index)
    for _, s in pairs(game.surfaces) do
      if s.index == index then return s end
    end
  end,
  print = function(text) fake.printed[#fake.printed + 1] = text end,
}

-- ---------------------------------------------------------------- the character: walking, mining, crafting, carrying
fake.path_requests = {}
fake.walk_speed = 0.15                                   -- tiles a tick
fake.mine_ticks = 30                                     -- ticks to mine one item by hand
fake.craft_ticks = 30

function fake.make_character(e)
  e.walking_state = { walking = false, direction = 0 }
  e.mining_state = { mining = false }
  e.build_distance, e.reach_distance, e.resource_reach_distance = 10, 10, 2.7
  e.crafting = {}
  e.crafting_queue_size = 0
  e.mined = 0
  local inv = {
    get_item_count = function(name) return e.items[name] or 0 end,
    get_contents = function()
      local out = {}
      for name, n in pairs(e.items) do
        if n > 0 then out[#out + 1] = { name = name, count = n, quality = "normal" } end
      end
      return out
    end,
    insert = function(a) e.items[a.name] = (e.items[a.name] or 0) + a.count return a.count end,
    remove = function(a)
      local n = math.min(e.items[a.name] or 0, a.count)
      e.items[a.name] = (e.items[a.name] or 0) - n
      return n
    end,
  }
  function e.get_main_inventory() return inv end
  function e.get_craftable_count(recipe)
    local r = RECIPES[recipe]
    local best
    for _, ing in pairs(r.ingredients) do
      local n = math.floor((e.items[ing.name] or 0) / ing.amount)
      if not best or n < best then best = n end
    end
    return best or 0
  end
  function e.begin_crafting(a)
    local r = RECIPES[a.recipe]
    local n = math.min(a.count, e.get_craftable_count(a.recipe))
    for _, ing in pairs(r.ingredients) do e.items[ing.name] = e.items[ing.name] - ing.amount * n end
    for _ = 1, n do e.crafting[#e.crafting + 1] = { recipe = a.recipe, left = fake.craft_ticks } end
    e.crafting_queue_size = #e.crafting
    return n
  end
end

local VECTOR = { [0] = { 0, -1 }, [2] = { 1, -1 }, [4] = { 1, 0 }, [6] = { 1, 1 }, [8] = { 0, 1 }, [10] = { -1, 1 }, [12] = { -1, 0 }, [14] = { -1, -1 } }

-- Can a character stand at x,y? Not on water, not inside anything but ore.
local function standable(s, x, y, self)
  local t = s.get_tile(x, y)
  if t.collides_with("water_tile") or t.name == "out-of-map" then return false end
  for _, o in ipairs(s.entities) do
    if o.valid and o ~= self and o.type ~= "resource" and o.type ~= "character" and o.type ~= "entity-ghost"
      and x > o.bounding_box.left_top.x - 0.2 and x < o.bounding_box.right_bottom.x + 0.2
      and y > o.bounding_box.left_top.y - 0.2 and y < o.bounding_box.right_bottom.y + 0.2 then
      return false
    end
  end
  return true
end

-- The stand-in pathfinder: a breadth-first search over whole tiles, eight ways, within 60 tiles of the start.
-- fake.no_path makes it answer that there is no way; fake.path_delay holds answers back that many ticks.
local function find_path(s, req)
  if fake.no_path then return nil end
  local sx, sy = math.floor(req.start.x), math.floor(req.start.y)
  local gx, gy = math.floor(req.goal.x), math.floor(req.goal.y)
  local radius = req.args.radius or 0.5
  local queue, head, came = { { sx, sy } }, 1, { [sx .. "," .. sy] = false }
  local found
  while queue[head] do
    local x, y = queue[head][1], queue[head][2]
    head = head + 1
    if math.sqrt((x + 0.5 - req.goal.x) ^ 2 + (y + 0.5 - req.goal.y) ^ 2) <= radius + 0.01 or (x == gx and y == gy) then
      found = { x, y }
      break
    end
    for _, v in pairs(VECTOR) do
      local nx, ny = x + v[1], y + v[2]
      local key = nx .. "," .. ny
      if came[key] == nil and math.abs(nx - sx) <= 60 and math.abs(ny - sy) <= 60
        and standable(s, nx + 0.5, ny + 0.5, req.args.entity_to_ignore)
        and (v[1] == 0 or v[2] == 0 or (standable(s, x + v[1] + 0.5, y + 0.5, req.args.entity_to_ignore) and standable(s, x + 0.5, y + v[2] + 0.5, req.args.entity_to_ignore))) then
        came[key] = { x, y }
        queue[#queue + 1] = { nx, ny }
      end
    end
  end
  if not found then return nil end
  local rev = {}
  local at = found
  while at do
    rev[#rev + 1] = { position = { x = at[1] + 0.5, y = at[2] + 0.5 }, needs_destroy_to_reach = false }
    at = came[at[1] .. "," .. at[2]]
  end
  local path = {}
  for i = #rev, 1, -1 do path[#path + 1] = rev[i] end
  return path
end

local function physics(s)
  for _, e in ipairs(s.entities) do
    if e.valid and e.type == "character" then
      if e.walking_state.walking then
        local v = VECTOR[e.walking_state.direction]
        local len = math.sqrt(v[1] * v[1] + v[2] * v[2])
        local nx, ny = e.position.x + v[1] / len * fake.walk_speed, e.position.y + v[2] / len * fake.walk_speed
        if standable(s, nx, ny, e) then
          e.position.x, e.position.y = nx, ny
          e.bounding_box = { left_top = { x = nx - 0.2, y = ny - 0.2 }, right_bottom = { x = nx + 0.2, y = ny + 0.2 } }
        end
      end
      if e.mining_state.mining then
        local pos = e.mining_state.position
        local target
        for _, o in ipairs(s.entities) do
          if o.valid and o.prototype and o.prototype.mineable_properties and o.prototype.mineable_properties.products
            and math.abs(o.position.x - pos.x) < 0.6 and math.abs(o.position.y - pos.y) < 0.6 then
            target = o
            break
          end
        end
        if target and math.sqrt((target.position.x - e.position.x) ^ 2 + (target.position.y - e.position.y) ^ 2) <= e.resource_reach_distance + 0.01 then
          e.mined = e.mined + 1
          if e.mined >= fake.mine_ticks then
            e.mined = 0
            local item = target.prototype.mineable_properties.products[1].name
            e.items[item] = (e.items[item] or 0) + 1
            if target.type == "resource" then
              target.amount = target.amount - 1
              if target.amount <= 0 then target.valid = false end
            else
              target.valid = false
            end
          end
        end
      end
      if e.crafting[1] then
        e.crafting[1].left = e.crafting[1].left - 1
        if e.crafting[1].left <= 0 then
          local r = RECIPES[table.remove(e.crafting, 1).recipe]
          for _, prod in pairs(r.products) do e.items[prod.name] = (e.items[prod.name] or 0) + prod.amount end
        end
        e.crafting_queue_size = #e.crafting
      end
    end
  end
end

-- Advance the stand-in world: answer path requests, run the mod's tick handler, move what moves.
function fake.tick(n)
  for _ = 1, n or 1 do
    game.tick = game.tick + 1
    local waiting = {}
    for _, req in ipairs(fake.path_requests) do
      req.age = (req.age or 0) + 1
      if req.age > (fake.path_delay or 0) then
        fake.handlers[defines.events.on_script_path_request_finished] { id = req.id, path = find_path(nauvis, req), try_again_later = false }
      else
        waiting[#waiting + 1] = req
      end
    end
    fake.path_requests = waiting
    if fake.handlers[defines.events.on_tick] then fake.handlers[defines.events.on_tick] { tick = game.tick } end
    physics(nauvis)
    fake.fly()
  end
end

-- ---------------------------------------------------------------- what the harness calls
function fake.command(text, player_index)
  fake.rcon = {}
  fake.commands["skippy"] { parameter = text, player_index = player_index }
  return fake.rcon[#fake.rcon]
end

-- ---------------------------------------------------------------- space: planets, platforms, rockets, pods
fake.rocket_ticks = 120                                  -- how long a rocket or a pod takes
fake.flights = {}
force.platforms = {}
force.rockets_launched = 0
force.unlocked = {}
force.is_space_location_unlocked = function(name) return force.unlocked[name] ~= false end
force.made = {}                                          -- item -> total ever produced, for the progress tool
force.rate = {}                                          -- item -> { made a minute, used a minute }, on nauvis
force.rate_elsewhere = {}                                -- the same, on every other surface that is a planet
force.get_item_production_statistics = function(surface)
  return {
    get_input_count = function(item) return (surface == nauvis) and (force.made[item] or 0) or 0 end,
    get_flow_count = function(a)
      local book = (surface == nauvis) and force.rate or (surface.planet and force.rate_elsewhere or {})
      local r = book[a.name]
      if not r or a.precision_index ~= defines.flow_precision_index.ten_minutes then return 0 end
      return (a.category == "input") and r[1] or r[2]
    end,
  }
end

local function move_to(e, surface, x, y)
  for i, o in ipairs(e.surface.entities) do
    if o == e then table.remove(e.surface.entities, i) break end
  end
  e.surface = surface
  e.position.x, e.position.y = x, y
  e.bounding_box = { left_top = { x = x - 0.2, y = y - 0.2 }, right_bottom = { x = x + 0.2, y = y + 0.2 } }
  surface.entities[#surface.entities + 1] = e
end

-- A planet, with or without a surface yet. nauvis exists from the start.
function fake.add_planet(name, with_surface)
  local planet = { name = name }
  function planet.create_surface()
    local index = 1
    for _, s in pairs(game.surfaces) do index = math.max(index, s.index + 1) end
    local s = new_surface(name, index)
    s.planet = planet
    game.surfaces[name] = s
    planet.surface = s
    return s
  end
  if name == "nauvis" then
    planet.surface = nauvis
    nauvis.planet = planet
  elseif with_surface then
    planet.create_surface()
  end
  game.planets[name] = planet
  return planet
end
fake.add_planet("nauvis")

-- A platform in orbit over `at`, with a schedule of stations. fake.tick flies it: it leaves after `wait` ticks at a
-- station and takes `flight` ticks to the next one.
function fake.add_platform(name, at, stations, wait, flight)
  local index = 1
  for _, s in pairs(game.surfaces) do index = math.max(index, s.index + 1) end
  local surface = new_surface("platform-" .. (#force.platforms + 1), index)
  game.surfaces[surface.name] = surface
  local records, current = {}, 1
  for i, station in ipairs(stations or {}) do
    records[i] = { station = station }
    if station == at then current = i end
  end
  local p = { name = name, valid = true, surface = surface, paused = false, space_location = { name = at },
              schedule = (#records > 0) and { current = current, records = records } or nil,
              wait = wait or 300, flight = flight or 600, clock = 0 }
  surface.platform = p
  p.hub = surface.create_entity { name = "space-platform-hub", position = { 0, 0 } }
  force.platforms[#force.platforms + 1] = p
  return p
end

function fake.make_silo(e, ready)
  e.rocket_silo_status = ready and defines.rocket_silo_status.rocket_ready or defines.rocket_silo_status.building_rocket
  function e.launch_rocket(destination, character)
    if e.rocket_silo_status ~= defines.rocket_silo_status.rocket_ready then return false end
    if fake.silo_refuses then return false end
    e.rocket_silo_status = defines.rocket_silo_status.building_rocket
    force.rockets_launched = force.rockets_launched + 1
    if character then
      character.in_flight = true
      fake.flights[#fake.flights + 1] = { who = character, to = destination.station.surface, x = 0.5, y = 6.5, left = fake.rocket_ticks }
    end
    return true
  end
end

function fake.make_hub(e)
  function e.create_cargo_pod()
    if fake.no_pods then return nil end
    local pod = { passenger = nil }
    function pod.set_passenger(who) pod.passenger = who end
    return setmetatable(pod, { __newindex = function(t, k, v)
      rawset(t, k, v)
      if k == "cargo_pod_destination" and pod.passenger then
        pod.passenger.in_flight = true
        fake.flights[#fake.flights + 1] = { who = pod.passenger, to = v.surface, x = 0.5, y = 0.5, left = fake.rocket_ticks }
      end
    end })
  end
end

local function fly(n)
  for i = #fake.flights, 1, -1 do
    local f = fake.flights[i]
    f.left = f.left - 1
    if f.left <= 0 then
      f.who.in_flight = nil
      move_to(f.who, f.to, f.x, f.y)
      table.remove(fake.flights, i)
    end
  end
  for _, p in ipairs(force.platforms) do
    if p.schedule and not p.paused and not p.stuck then
      p.clock = p.clock + 1
      if p.space_location and p.clock >= p.wait and #p.schedule.records > 1 then
        p.space_location, p.clock = nil, 0
      elseif not p.space_location and p.clock >= p.flight then
        p.schedule.current = p.schedule.current % #p.schedule.records + 1
        p.space_location, p.clock = { name = p.schedule.records[p.schedule.current].station }, 0
      end
    end
  end
end
fake.fly = fly

-- The player changes the mod setting in the game's settings window.
function fake.change_setting(name, value)
  settings.global[name] = { value = value }
  fake.handlers[defines.events.on_runtime_mod_setting_changed] { setting = name, setting_type = "runtime-global" }
end

-- The player clicks an element of the interface.
function fake.click(player_index, element)
  element.valid = true
  fake.handlers[defines.events.on_gui_click] { player_index = player_index, element = element }
end

function fake.research(name)
  local t = force.technologies[name]
  t.researched = true
  fake.handlers[defines.events.on_research_finished] { research = t }
end

function fake.chat(player_index, message)
  fake.handlers[defines.events.on_console_chat] { player_index = player_index, message = message, tick = game.tick }
end
