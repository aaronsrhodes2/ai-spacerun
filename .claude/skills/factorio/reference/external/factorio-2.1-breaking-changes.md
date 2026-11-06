# Factorio 2.0+ Breaking Changes — Reference

Audit date: 2026-08-28
Versions: 2.0.x (runtime), 2.1.0 through 2.1.17
Last breaking changes: 2.1.15 (circuit connector layer migration, `LuaGroup` rename, `LuaSimulation::get_widget_position` reworked). See the "2.1.15" sections below.

## Where to get the changelog
```bash
curl -sL "https://raw.githubusercontent.com/wube/factorio-data/master/changelog.txt"
```
The **Modding** section of each version entry lists all API additions, removals, renames, and moves.

## Prototype changes (data stage)

### RecipePrototype
```diff
- category = "crafting"
+ categories = { "crafting" }
```
- `category` (single string) **removed**
- `additional_categories` **removed**
- Use `categories` (array of strings) instead
- Affects: `data.lua`, `data-updates.lua`, `data-final-fixes.lua`

### Removed recipe categories
The following compound/or-inherited categories were **removed** (use explicit multiple categories on the recipe instead):
- `basic-crafting`
- `recycling-or-hand-crafting`
- `chemistry-or-cryogenics`
- `pressing`
- `crafting-with-fluid-or-metallurgy`
- `metallurgy-or-assembling`
- `organic-or-hand-crafting`
- `organic-or-assembling`
- `organic-or-chemistry`
- `electronics-or-assembling`
- `electronics`
- `electronics-with-fluid`
- `cryogenics-or-assembling`

### Added categories
- `hand-crafting`

### Recycling moved
The `recycling` recipe category was moved from the base mod to a **separate recycler mod**. If your mod filters `recipe.category == "recycling"`, the logic must be updated for 2.1 since:
- `category` no longer exists on the prototype (use `categories`)
- If the recycler mod is not loaded, no recipes will have `"recycling"` in their categories
- **Data-stage iteration pattern**: `for name, recipe in pairs(data.raw.recipe) do if recipe.category == "recycling" then ... end end` → this pattern breaks because `recipe.category` is nil in 2.1. Change to iterating `recipe.categories` (array): `if recipe.categories then for _, cat in ipairs(recipe.categories) do if cat == "recycling" then ... end end end`

### Molten recipes renamed (Space Age)
- `molten-iron` → `iron-ore-melting`
- `molten-copper` → `copper-ore-melting`

### Science packs → plain items
- `TechnologyPrototype` and `LabPrototype` now accept **any item type** as research ingredients
- Science packs are now plain items (no longer `type = "tool"`)
- If your mod checks `type == "tool"` or similar, update it

### Quality changes
- Quality effect values in prototype definitions were **divided by 10**
- `next_probability` values were **multiplied by 10** (1.0 = 100% guarantee)
- Module effects now have **0.01% resolution**
- GUI quality percentages no longer multiplied by `next_probability`

### Vehicle changes
```diff
- braking_power, friction
+ braking_force, friction_force
```

### Entity flags
- `AssemblingMachinePrototype::enable_logistic_control_behavior` → use `"no-logistic-connection"` EntityPrototypeFlag instead

### Other prototype removals
- `DeconstructionItemPrototype::tile_filter_count`, `entity_filter_count` → dynamic filter counts
- `EntityPrototype::build_base_evolution_requirement` removed
- `AsteroidPrototype::mass` → use `damage_per_hp`
- `CraftingMachinePrototype::forced_symmetry` → `use_mirroring`
- `RecipePrototype::always_show_products`, `show_amount_in_title` removed
- `RecipePrototype::result_is_always_fresh` → `ItemProductPrototype::always_fresh`
- `RecipePrototype::reset_freshness_on_craft` → `ItemProductPrototype::reset_freshness_on_craft`

### Recipe PRODUCT probabilities — `probability` → `independent_probability` (2.1)
**Error** (data stage): `'probability' property on a product prototype was renamed
into 'independent_probability'. Please update. in property tree at
ROOT.recipe.<name>.results[0]`
**Fix**: for independent per-result probabilities (pumpjack-style multi-result
recipes — e.g. the DMR Quality Refiner returns BOTH the retry item and the
upgraded item with separate chances), use `independent_probability` on the
product. The old `probability` now means CUMULATIVE/summed probability and
errors at load when used as a standalone per-result chance. DMR hit this twice:
write the generator AND the test assert with the new key — the local unit test
(`independent_probability`) catches it only if you update it too.

### Recipes with `quality` fields REQUIRE an explicit `icon` (2.1)
**Error** (data stage): `Key "icon" not found in property tree at
ROOT.recipe.<name>`
**Root cause**: a recipe whose ingredients/results carry a `quality` field — and
is `hidden = true` — can't auto-detect its icon from a quality result, so 2.1
requires an explicit `icon`. (A plain single-result item/fluid recipe like DMR's
replication recipes loads fine with NO icon at all.)
**Fix**: copy the source item's `icon`(+`icon_size`), or its `icons` layer array
(`helpers.deep_copy` each layer + strip `icon_mipmaps`) when present. `icon` and
`icons` are mutually exclusive in a prototype — strip `icon` when the layered
array is present. Fallback to a known mod icon when the item has neither.
**Generalizable**: any recipe feature diverging from a plain single-result
item/fluid recipe (quality fields, probabilities, multiple results) tends to
trip NEW 2.1 validation rules the dynamic replication recipes never exercised.
Build a unit test asserting every field the game now requires, and expect 1-2
load-error round-trips on the user's PC even with tests green.

### Technologies REQUIRE an explicit `icon`/`icons` (2.1)
**Error** (data stage): `Key "icon" not found in property tree at
ROOT.technology.<name>`
**Root cause**: in 2.1 a technology prototype must define `icon`/`icons`
explicitly — there is no auto-detection from effects. DMR's dynamically
generated mirror techs already set `icons` via `get_tech_icons(...)`, so they
load fine; a STANDALONE tech that omits the field (e.g. the Quality Refiner
research) errors at load.
**Fix**: add `icon = "...", icon_size = 64` (or a bordered `icons` layer array)
to every technology you extend, including one-off standalone techs. Grep your
prototypes for `type = "technology"` and confirm each has an icon before
building the zip — this is a cheap pre-flight check that avoids a load-error
round-trip.

### Static shadow layers need `repeat_count`, not `frame_count` (2.1)
**Error** (data stage): `Different frame counts (expected 32, but has 1) in
animation layers of <shadow.png>`
**Root cause**: when an assembling-machine `graphics_set.animation` uses a
`layers` array, every layer must reach the main layer's `frame_count` — but a
STATIC shadow sprite is a single frame (`frame_count` effectively 1). naively
leaving the shadow's `frame_count` unset (defaults to 1) while the main layer
has 32 produces "different frame counts".
**Fix** (verified against the real 2.1 `assembling-machine-1` in the dump): a
static shadow layer that must span the whole animation uses `repeat_count`
(how many times to repeat the single frame) EQUAL to the main frame_count —
NOT `frame_count`. The real assembler-1 shadow is:
```lua
{ filename = ".../<name>-shadow.png", width = 190, height = 165,
  line_length = 1, repeat_count = 32, draw_as_shadow = true,
  shift = {0.265625, 0.15625}, scale = 0.58 }
```
pattern in the dump, NOT `frame_count`.) To reproduce the exact vanilla look,
pull these values from `dump['assembling-machine']['assembling-machine-1']`'s
`graphics_set.animation.layers` rather than memory — the 2.x dimensions
(214x226, frame_count 32, line_length 8) differ from the old 1.x sheets, and
the shadow shift/scale are entity-specific.

**Don't reproduce vanilla sprites with hardcoded rects — they fragment under
overhaul mods (v4.1.0 gate test).** Reproducing the `assembling-machine-1`
sprite as a placeholder produced a cascade of load errors on the user's
real Bob's+Angel's+SA modlist:
  1. `Different frame counts (expected 32, but has 1) in animation layers of
     <...>-shadow.png` → fixed with `repeat_count` (above).
  2. `The given sprite rectangle (left_top=0x0, right_bottom=190x165) is
     outside the actual sprite size (left_top=0x0, right_bottom=50x166)` —
     the REAL shadow sheet in the modlist is not 190x165; Bob's
     replaces/resizes the vanilla assembler-1 shadow, so any rectangle you
     pull from a clean dump is wrong on THAT load. The game log tells you the
     real size, but don't chase it — see the robust fix below.
  3. `File __base__/graphics/entity/assembling-machine-1/assembling-machine-1.png
     not found` — with Bob's active the whole vanilla sheet path can VANISH
     (overhaul mods replace the assembler entity + its graphics), so even the
     main sprite reference breaks.
**Robust pattern for placeholder graphics**: reference the mod's OWN proven
sprite (DMR used its `replicator-5.png`, whose dims are known-good because
they already load in 2.1), with a `tint` for the placeholder color — never a
vanilla entity sheet that an overhaul mod is free to replace/resize. A mod's
own sprite can't disappear. If you MUST reuse a vanilla machine's look, ship a
copy of the PNG inside your mod's graphics/ dir rather than `__base__/...`
pathing, so its dimensions/widths are yours to control. Hardcoding a vanilla
sprite's rect from a clean dump is a false economy: it only loads on a
pristine base install.
- `UtilityConstants::max_fluid_flow` removed (derived from FluidBox volume now)
- `MapSettings::steering` removed → `UnitPrototype::steering`, `SpiderUnitPrototype::steering`

## 2.1.15 — Circuit connector layer migration (2026-08-24)

The biggest 2.1.x breaking change since 2.1.7. Circuit connector visual layering
was unified into a single `CircuitConnectorSprites` prototype type, and the
per-machine `circuit_connector_layer` / `circuit_connector_render_layer` fields
were **removed**.

### Additions
- `EntityPrototype::ghost_build_sound` — sound played when a ghost entity is
  built (replaces the silent ghost-then-build sequence).
- `RocketSiloPrototype::rocket_parts_storage_cap` — now accepts `0` to disable
  crafting of a second rocket (previously had a minimum of `1`).
- `CircuitConnectorSprites::render_layer` (string) — explicit render layer for
  the circuit connector sprites.
- `CircuitConnectorSprites::secondary_draw_order` (number) — secondary draw
  order within the render layer.
- **Default render layer changes (silent breakage risk)**:
  - Inserter circuit connector no longer defaults to `"floor"` render layer.
  - Train stop circuit connector no longer defaults to `"train-stop-top"` render
    layer.
  - Asteroid collector circuit connector no longer defaults to
    `"higher-object-under"` render layer.
  - Rocket silo circuit connector no longer defaults to secondary draw order
    of `70`.
  - If your mod relied on any of these defaults, the connector may render
    BEHIND or ABOVE entities it previously didn't. Verify visually with a
    gate test.

### Removals (use `CircuitConnectorSprites::render_layer` instead)
```diff
- LoaderPrototype::circuit_connector_layer
- RailSignalPictureSet::circuit_connector_render_layer
- CraftingMachineGraphicsSet::circuit_connector_layer
- CraftingMachineGraphicsSet::circuit_connector_secondary_draw_order
- MiningDrillGraphicsSet::circuit_connector_layer
- MiningDrillGraphicsSet::circuit_connector_secondary_draw_order
```
**Migration pattern**: if you set these fields anywhere in your mod, move the
value onto the corresponding `CircuitConnectorSprites` prototype (the
connector definition that the entity references). If you don't set them at
all, the defaults above change silently — render visually to confirm.

**Audit command**:
`grep -rn "circuit_connector_layer\|circuit_connector_render_layer\|circuit_connector_secondary_draw_order" . --include="*.lua"`

**DMR impact**: DMR v4.x replicators inherit from `assembling-machine`
prototype and don't override circuit connectors, so the removal is a **no-op**
for DMR. Verify with a static grep before declaring safety.

## 2.1.15 — Scripting API changes (2026-08-24)

### Additions
- `LuaEntity::potential_effects` (read) — list of effect IDs the entity could
  apply if its `effect_receiver` is connected to the network.
- `LuaSpacePlatform::completed_trips` (read/write) — total trip count for the
  platform.
- `on_next_day_started` event — fires when the in-game day rolls over.
- `SimulationWidgetType` gained `"simple-item-with-quality-slot"`.

### Breaking rename
**`LuaGroup` → `LuaItemGroup` + `LuaItemSubGroup`** (REPLACED, not aliased).
The old `LuaGroup` API is gone; `data.raw["item-group"]` and
`data.raw["item-subgroup"]` are now accessed via distinct prototype types.
Any code that does `local g = prototypes.group[name]` or iterates
`for _, g in pairs(prototypes.group) do` will break at runtime — switch to
`prototypes.item_group` / `prototypes.item_sub_group` (note the underscored
snake-case at the script layer).
**Audit command**:
`grep -rn "prototypes\.group\|LuaGroup\b" . --include="*.lua"`
**DMR impact**: DMR's runtime scripts (`control.lua`) are minimal and don't
iterate item groups, but any player-log / debug / GUI code that touches groups
needs updating.

### Reworked APIs (breaking signature changes)
- `LuaSimulation::get_widget_position()` — **no longer accepts data/data2
  strings** (those args were removed) and now uses **1-based indexing** for
  position coordinates. Code that passed `"[gps=...]"` strings or relied on
  0-based positions silently gets wrong widget positions.
- `LuaControl::opened` — now supports:
  - Reading/writing the opened tile when in the map editor.
  - Opening the permissions GUI, server config GUI, and player management GUI
    (when allowed).
  - Opening the alerts GUI.
  Any switch on `LuaControl::opened`'s return type needs new branches.

### `LuaControl::opened` change summary
- Added support for: opened tile (map editor), permissions GUI, server config
  GUI, player management GUI, alerts GUI.

## 2.1.15 — Space Age tech graph change
- "Transport belt capacity 2" now requires "Inserter capacity bonus 7" as a
  prerequisite.
**Impact on DMR v4.x**: DMR's cost-solver reads tech prereqs to derive mirror
tiers. If any of DMR's mirror techs pull "Transport belt capacity 2" as a
prereq (likely for belt/inserter category items), the dependency chain is now
longer — verify in a dump that no mirror tier dropped due to the new prereq.
Re-run the `dmr-tests` suite against a fresh `--dump-data` if the user runs
2.1.15+.

## 2.1.16 — Pure bugfix (2026-08-24)
- Crash when opening production statistics GUI on the "all" tab.
- macOS trackpad scrolling issue.
No API changes.

## 2.1.17 — Pure bugfix (2026-08-26)
- Labs "set research" wouldn't mark active research as set-by-lab-behavior.
- Tooltips too hard to show in graph widgets.
- Cannot build sound playing twice for underground belts/pipes.
- Steam achievements not unlocking (Steamworks SDK update).
- Blueprint autofill artifacts with shared-tile entities.
- Disabled-achievements-confirmation message not showing with peaceful/no-enemies.
- Unreliable control behavior update performance.
- Elevated rail end rendering.
- Non-neutral robots attempting to build neutral ghosts.
No API changes.

### Pipe pictures — `assembler2pipepictures` is now a TABLE, not a function (2.1)
**Error**: `attempt to call global 'assembler2pipepictures' (a nil value)` at data stage
**Root cause**: In Factorio 2.1, `assembler2pipepictures()` and `assembler3pipepictures()`
were removed as global helper FUNCTIONS. They now live as data TABLES in
`base/prototypes/entity/assembler-pictures.lua`.
**Fix** (verified against wube/factorio-data master + Bob's 3.0.1, 2026-08-13):
```lua
-- OLD (2.0): global function call
pipe_picture = assembler2pipepictures(),

-- NEW (2.1): require the base module, reference the table WITHOUT parentheses.
-- CRITICAL: from another mod you MUST use the __base__/ prefix — plain
-- require("prototypes.entity.assembler-pictures") does NOT resolve from an
-- external mod (this exact mistake broke DMR 4.0.0's first fix attempt).
pipe_picture = require("__base__/prototypes/entity/assembler-pictures").assembler2pipepictures,
```
- `pipecoverspictures()` **still exists** as a global function in 2.1 (used in
  base entities.lua) — only assembler2/3pipepictures changed.
- Note the contrast: `require("resource-autoplace")` (NO `__base__/` prefix)
  still works from external mods (Paracelsin 1.9.11 does exactly this) — it's
  a lualib module on the global package.path. The assembler-pictures file is a
  base PROTOTYPE file, which is why it needs the `__base__/` path. When in
  doubt, grep a 2.1-updated mod (Bob's 3.0.1 etc.) for the exact require form.
- **Symptom to watch**: the mod's data.lua uses `safe_require`/pcall, so the
  entity file fails SILENTLY. The item prototype inside it never registers, and
  the crash appears LATER as a confusing `Error in assignID: item with name
  'X' does not exist` on the recipe that references that item. When you see an
  assignID "item does not exist" for a prototype that clearly exists in source,
  check factorio-current.log for the swallowed `ERROR loading ...` line from
  safe_require — the real error is there.
- **Audit command**: `grep -rn "assembler2pipepictures()\|assembler3pipepictures()" . --include="*.lua"`

## Scripting changes (control.lua / runtime)

### LuaRecipe changes
```diff
- local cat = recipe.category
+ local cats = recipe.categories  -- array of strings
```
- `LuaRecipe::category` → `LuaRecipe::categories` (READ: array, not single string)
- `LuaRecipe::additional_categories` removed
- `LuaRecipe::always_show_products`, `show_amount_in_title` removed
- `LuaRecipe::is_parameter` → `LuaPrototypeBase::parameter`
- `LuaRecipe::result_is_always_fresh` → product-level field

### Fluid system rework
- `LuaFluidBox` **removed entirely**
- All fluid interaction now through `LuaEntity`:
  - `LuaEntity::fluidbox` removed
  - `LuaEntity::remove_fluid()` → `extract_fluid()`
  - New: `clear_fluids()`, `add_fluid()`, `remove_fluid()`, `clear_fluid()`
  - New: fluid segment API (`has_fluid_segment()`, `get_fluid_segment_fluid()`, etc.)
  - New: `get_fluid_filter()`, `set_fluid_filter()`
  - New: `input_flow_limit`, `output_flow_limit`

### LuaEntity changes
- `LuaEntity::active` write → `disabled_by_script`
- `LuaEntity::minable` write → `minable_flag`
- `LuaEntity::neighbors` removed → use `fluidbox_neighbours`, `underground_belt_neighbour`, `wall_neighbours`, `cliff_neighbours`, `neighbour_connectable_connections`
- `LuaEntity::pump_rail_target` → `pump_input_rail_targets`, `pump_output_rail_targets`

### LuaEntityPrototype changes (runtime — affects control.lua)

⚠️ These are **runtime wrapper** changes. The raw prototype tables in `data.raw` still have the old fields; only `prototypes.entity[name]` (which returns `LuaEntityPrototype`) is affected.

```diff
- proto.category                          -- removed in 2.0
+ proto.resource_category                 -- use this instead
```

- `LuaEntityPrototype::category` → **removed in 2.0** (not just 2.1!). Use `resource_category` instead.
  - For resource entities, the old `category == "basic-fluid"` check becomes `resource_category == "basic-fluid"`
- `LuaEntityPrototype::normal` → **removed in 2.0** (was a raw data field, never exposed at runtime)
  - **Safe access pattern** — use `pcall` to avoid crashes if the field doesn't exist:
    ```lua
    local proto = prototypes.entity[name]
    local fluid_normal = 60000  -- default fallback
    if proto then
      local ok, val = pcall(function() return proto.normal end)
      if ok and val then fluid_normal = val end
    end
    ```
- `LuaEntityPrototype::minable` → still exists but structure may differ in 2.0+
- `LuaEntityPrototype::infinite` → still valid on resource prototypes (2.0)

**General rule for runtime prototype access**:
If you're accessing `prototypes.entity[name].some_field` and get `LuaEntityPrototype doesn't contain key X`, that field was removed from the runtime wrapper. Check the Factorio API docs for the 2.0 equivalent, or use `pcall` as a safe fallback.

### Inventory constants renamed
```diff
- defines.inventory.assembling_machine_input
- defines.inventory.furnace_source
- defines.inventory.rocket_silo_input
+ defines.inventory.crafter_input  (unified)

- defines.inventory.assembling_machine_output
- defines.inventory.furnace_result
- defines.inventory.rocket_silo_output
+ defines.inventory.crafter_output

- defines.inventory.assembling_machine_modules
- defines.inventory.furnace_modules
- defines.inventory.rocket_silo_modules
+ defines.inventory.crafter_modules

- defines.inventory.assembling_machine_trash
- defines.inventory.furnace_trash
+ defines.inventory.crafter_trash
```

### LuaPlayer changes
- `LuaPlayer::pipette_entity()` → `pipette()`

### Other scripting changes
- `LuaGameScript::create_profiler()` → `LuaHelpers::create_profiler()`
- `LuaFluidBoxPrototype::volume` → `get_volume()`
- `LuaEntityPrototype::fluid_usage_per_tick` → `get_fluid_usage_per_tick()`
- `LuaEntityPrototype::max_power_output` → `get_max_power_output()`
- `LuaEntityPrototype::pumping_speed` → `get_pumping_speed()`
- `LuaItemPrototype::inventory_size` → `get_inventory_size()`
- `LuaLogisticContainerControlBehavior::circuit_exclusive_mode_of_operation` → use `set_requests` and `read_contents`
- `LuaRecord::is_blueprint_preview` → `is_preview`
- `LuaEntity::mining_progress` moved to `LuaControl::mining_progress` (read/write)

## Settings changes
- Quality values in quality prototype definitions scaled differently
- `UtilityConstants` values added/removed (tall_entity_tint, etc.)

## New features for mods to leverage
- **Multiple recipe categories per recipe**: `categories = { "crafting", "chemistry" }` instead of single category
- **Dynamic filter counts** for deconstruction planners
- **Module effect quality multipliers**: per-effect multipliers for consumption, speed, productivity, pollution, quality
- **LuaDebugAdapter**: Debug Adapter Protocol support for mod debugging
- **`"expansion"` feature flag**: for Space Age expansion features
- **`"+"` mod dependency modifier**: optional but recommended (enabled by default)
- **`categories` as array** in recipe prototypes (the main migration target)

## Common mod compatibility issues

These patterns appear repeatedly across mod portal discussions and forum posts:

### 1. Duplicated technology prerequisite
**Error**: `Technology prerequisite "angels-basic-chemistry" is registered more than once.`
**Root cause**: Two mods (e.g. Angel's Smelting + Angel's Petrochem) both register the same technology. When your mod uses it as a prerequisite, Factorio's tech validation rejects it.
**Fix strategies**:
- Deduplicate the prerequisite list before building the tech prototype — but don't rely on `add_prereq()` alone. Add a **belt-and-suspenders final pass** that converts the array to a set and back:
  ```lua
  local seen = {}
  local clean = {}
  for _, p in ipairs(prerequisites) do
    if not seen[p] then seen[p] = true; table.insert(clean, p) end
  end
  prerequisites = clean
  ```
- Wrap `data:extend()` in `pcall` so a single failing tech doesn't cascade
- Check `data.raw.technology[name]` already exists before adding as prereq

### 2. Missing technology prerequisite
**Error**: `Error in assignID: technology with name 'spidertron-unit' does not exist. It was removed by moon-eneas.`
**Root cause**: A mod removes vanilla technology. Your dynamically-generated tech has a hardcoded prereq that no longer exists.
**Loading-phase trap**: The check `data.raw.technology[prereq_name]` done in `data-updates.lua` may pass because the other mod (moon-eneas) hasn't run its removal yet. Mods that remove prototypes often do so in `data-final-fixes.lua`, which runs AFTER `data-updates.lua`. So the prereq exists when you validate, but vanishes later during Factorio's ID assignment phase.
**Fix strategies**:
- Always validate `data.raw.technology[prereq_name]` before inserting into the prereq list (`data-updates.lua` catches static removals)
- **Additionally**, create a `data-final-fixes.lua` in your mod that re-iterates ALL your technologies and strips any prereqs that no longer exist. This catches removals by mods running in the final phase:
  ```lua
  -- data-final-fixes.lua: strip prereqs that other mods removed
  local gprefix = "mymod-"
  for tech_name, tech in pairs(data.raw.technology) do
    if string.sub(tech_name, 1, #gprefix) == gprefix and tech.prerequisites then
      local valid = {}
      for _, p in ipairs(tech.prerequisites) do
        if data.raw.technology[p] then table.insert(valid, p) end
      end
      tech.prerequisites = valid
    end
  end
  ```
- Provide fallback prereqs when the original doesn't exist

### 3. Non-contiguous technology levels
**Error**: `Technology dmrsa-replication: Non-contiguous levels: 2, followed by 4`
**Root cause**: Tier 3 technology was made hidden or removed, creating a gap in the tier progression that Factorio's level-based ordering rejects.
**Fix**: Register a hidden technology prototype to bridge missing tiers. E.g. if tier 3 is hidden behind planetary unlocks but referenced in the progression chain, an explicit `hidden = true` tech at tier 3 is needed.

**NEW (v4.0 mirror tree, 2026-08-13): a tech can also be non-contiguous when a DIRECT prereq is deeper in the tree than the tech's own tier.** The DMR mirror tech takes the ORIGINAL game tech as a direct prerequisite (when `dmrsa-require-original-tech` is ON). The original tech's science-pack level (which DMR uses for its tier) can be SHALLOWER than the tech's real depth in the research tree — e.g. angel's `chlorine-processing` maps to tier 2-3 by packs but sits at depth 4 (prereqs chain automation → simple-chemistry → chlorine-1 → chlorine-processing). Factorio computes tech levels from the prereq graph, so the mirror tech (level 2) having a level-4 prereq = "Non-contiguous levels: 2, followed by 4".
**Fix**: clamp the mirror tier to `max(science_level, tree_depth(original_tech))` with a memoized, cycle-safe recursive depth function (`get_tech_tree_depth`). This also has the nice property that deeply-nested original techs (Angel's/Bob's chains) push their replication to later tiers — matching the "you must know the materials" philosophy.
**CRITICAL — the depth fix silently depends on load order**: if the mod's
info.json does NOT declare optional deps for the overhaul family that owns the
tech (e.g. `? angelspetrochem`), DMR's data-final-fixes can run BEFORE Angel's,
so `get_tech_tree_depth("angels-chlorine-processing")` sees incomplete prereqs
and returns 1-2 instead of 4 → the tier clamp never fires → the SAME
"Non-contiguous levels: 2, followed by 4" error persists even with the fix in
place. This bit DMR 4.0.0: the first zip had the depth fix but not the Angel's
deps, and the identical error came back. Fix: add `? angelssmelting /
? angelsrefining / ? angelsindustries / ? angelspetrochem /
? angelsbioprocessing / ? angelsaddons-*` to info.json (same A5 pattern as
Bob's). Rule: any dynamic-generation fix that reads OTHER mods' tech graphs
(recipe_tech_map, tree depth, prereqs) requires optional deps for EVERY
overhaul family in the player's modlist — re-audit info.json when a new
family is added, and verify the fix against a FRESH dump/log, not just static
syntax.
**Audit**: any dynamically-generated tech whose prereq list mixes your tier techs with OTHER mods' techs needs this depth check; vanilla-style static techs rarely hit it because their packs and depth correlate.

**NEW (v4.0, 2026-08-13): leveled-tech chains (`name-N`) must generate ONE tech, not one per level.** Factorio treats technologies ending in `-N` (e.g. `angels-chlorine-processing-1..4`, many Angel's/Bob's chains) as LEVELS of a single base technology. If your generator emits one mirror tech per level (`dmrsa-mirror-angels-chlorine-processing-1`, `-2`, `-3`, `-4`), Factorio groups them into one composite tech whose levels must be CONTIGUOUS. When a middle level unlocks no qualifying recipes (its mirror is skipped), the chain breaks: `Non-contiguous levels: 2, followed by 4`. The error message shows the BASE name (no suffix) because Factorio reports the composite. Fix: normalize `-<digits>$` suffixes to the base name and group the whole chain into ONE mirror tech, using the deepest existing level as the original-tech prereq. Lua pitfall: `string.find(name, "%-%d+$")` does NOT capture the number — you need `string.find(name, "%-(" .. "%d+" .. ")$")` for the capture to work.

### 4. Missing crafting category
**Error**: `Skipping '<item>': crafting category '<name>' not found.`
**Root cause**: A recipe references a recipe-category that hasn't been defined yet, or the category was removed in a game version update.
**Fix**: Check `data.raw["recipe-category"][category_name]` before extending the recipe, and skip gracefully if missing.

### 5. Lab doesn't accept all science packs
**Error**: `"no lab will accept all science packs"`
**Root cause**: The Replication Lab's `inputs` list includes custom science packs that aren't registered as valid research ingredients for the lab entity.
**Fix**: Dynamically populate `inputs` from all generated technologies' research unit ingredients in `data-final-fixes.lua`.

---

## Localised string parameter syntax (Factorio 2.x)
The parameter list in Factorio 2.x is a **flat positional array** — each element is a
single parameter, numbered `__1__`, `__2__`, etc. There is NO "fallback chain" syntax
in 2.x; the `"?"` first-element trick that worked in old Factorio (pre-1.0) is gone.

### The bug: `parameter-N` instead of a name

This pattern looks like it should work but doesn't in Factorio 2.x:

```lua
localised_name = {
    "technology-name.dmrsa-repl-tech",
    {
        "?",
        { "item-name." .. name },
        { "entity-name." .. name },
        { "fluid-name." .. name },
        name  -- literal fallback string
    }
}
```

In Factorio 2.x, the inner array is treated as **5 separate positional parameters**:
- `__1__` = `"?"` (literal — not a fallback marker, just a string)
- `__2__` = `{ "item-name.<name>" }` (resolved to item name OR `parameter-1`)
- `__3__` = `{ "entity-name.<name>" }` (same — `parameter-2`)
- `__4__` = `{ "fluid-name.<name>" }` (same — `parameter-3`)
- `__5__` = `name` literal (also unresolved → `parameter-4`)

The locale string `__1__ replication: __2__` renders as
`? replication: <actual-item-name>` if `item-name.<name>` exists, else
`parameter-0 replication: parameter-1` when nothing resolves. The `parameter-N` text
is Factorio's debug placeholder for "I tried to localise this and couldn't".

### Correct pattern for 2.x: pick the right type at build time

You need to **decide at data-stage time** which type the prototype is, not let the
localisation system pick:

```lua
-- Resolve the localisable key once at build time
local type_key
if data.raw.item[name] then
    type_key = "item-name." .. name
elseif data.raw.entity[name] then
    type_key = "entity-name." .. name
elseif data.raw.fluid[name] then
    type_key = "fluid-name." .. name
else
    type_key = nil  -- not localisable; will display the literal string below
end

localised_name = {
    "recipe-name.dmrsa-replication-recipe",
    type_key and { type_key } or name  -- pass the resolved key OR the raw name as a literal
}
```

This way:
- If `name` is an item, `__1__` resolves to the item's display name
- If `name` is a fluid/entity, same idea with the right prefix
- If `name` doesn't exist in any registry, `__1__` is the raw string (acceptable
  fallback rather than `parameter-N`)

### Verification

Test by loading the mod in Factorio and inspecting the tech tree / crafting menu. Any
`parameter-N` text is the smoking gun for this bug. Search the codebase for any line
matching `"\?"` or `"'" .. name` in `localised_name` / `localised_description` blocks
to find instances of the legacy pattern.

### Where this came from

DMR v3.5.3 carried this bug from upstream (it had been latent since the 0.x → 1.0 →
2.x migration). Players saw `Replication: parameter-0`, `parameter-1`, etc. across
all dynamically-generated techs and recipes — every `dmrsa-tech-repl-<item>-tech`
showed it. The fix lands in v3.5.4 by rewriting the `localised_name` /
`localised_description` blocks in `prototypes/recipes/dynamic-generator.lua` to resolve
the type key at build time.

---

## What does NOT change in 2.1

Knowing what stays the same is as valuable as knowing what changes. These prototype fields and concepts are **unaffected** by the recipe `category` -> `categories` migration:

### Still works in 2.1 (no migration needed)

| Concept | Example | Why unchanged |
|---------|---------|--------------|
| Recipe-category definitions | `{ type = "recipe-category", name = "my-cat" }` | Defines a category registry entry, not a recipe field |
| Category registry validation | `data.raw["recipe-category"][name]` | The registry of available categories still exists |
| Assembling-machine `crafting_categories` | `crafting_categories = { "my-cat" }` | Entity field on assembling-machine, not recipe field |
| Lab `research_category` | `research_category = nil` or `= "crafting"` | Lab entity field, not recipe field |
| Technology `category` | `tech.category = "crafting"` | Technology category field, not recipe field |
| Autoplace-control `category` | `{ type = "autoplace-control", category = "resource" }` | Autoplace-control prototype, not recipe |
| Item/fluid type in `data.raw` | `data.raw["item"]`, `data.raw["fluid"]` | These are registry keys, not recipe fields |
| Resource `category` in data stage | `data.raw.resource[name].category` | Raw resource table still has this field (removed only from runtime `LuaEntityPrototype` wrapper) |

### What already worked in 2.0 and still works in 2.1

| Pattern | Status |
|---------|--------|
| `proto.resource_category == "basic-fluid"` in control.lua | Correct since 2.0 |
| `(proto.category or proto.resource_category) == "basic-fluid"` in data-final-fixes.lua | Forward-compat pattern |
| `pcall` for `LuaEntityPrototype` fields that may not exist | Safe pattern since 2.0 |
| `data.raw.technology[name]` existence check for tech prereqs | Still valid |

### Common false positives during audit

When grepping for `category` during a 2.1 migration audit, these will show up but require **no change**:

```lua
-- FALSE POSITIVE: defining a new recipe category (bucket E)
{ type = "recipe-category", name = "my-custom-category" }

-- FALSE POSITIVE: assembling-machine entity field (bucket G)
{ type = "assembling-machine", crafting_categories = { "my-cat" } }

-- FALSE POSITIVE: resource prototype in data stage (bucket I)
local proto = data.raw.resource[name]
if proto.category == "basic-fluid" then ... end  -- still works in data stage

-- FALSE POSITIVE: local string variable (bucket M)
local category = "dmrsa-replication-1"

-- FALSE POSITIVE: internal classification key (bucket N)
group.category = "ore"  -- mod-internal concept

-- FALSE POSITIVE: item type iteration (bucket L)
for _, category in ipairs({ "item", "fluid", "tool" }) do
    local registry = data.raw[category]
end
```