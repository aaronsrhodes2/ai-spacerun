# Factorio Lua/RCON API notes — confirmed firsthand

Durable technical facts about how this specific setup (ai-player-v3 mod +
RCON + `run_lua`) actually behaves, independent of any one game session.
Update this when a new API quirk is confirmed; don't bury it only in
`docs/progress.md`.

## RCON / connection

- **RCON only binds when the save is hosted as (solo) Multiplayer.** Plain
  Singleplayer never opens the port, regardless of launch flags. Set via
  `config.ini`'s `[other]` → `local-rcon-socket` / `local-rcon-password`,
  then launch via **Multiplayer → Host saved game**, not Singleplayer →
  Load Game.
- **The first RCON call after any fresh connection reliably comes back as an
  empty string**, not an error, not real data. A second identical call then
  succeeds. Treat empty-on-first-call as "retry once," not a real failure.

## `run_lua` / `/sc` execution context

- **`run_lua` executes in a separate "console" Lua context that cannot see
  the mod's own `storage` table.** `storage.ai_player.character` etc. is
  only reachable from Lua that the mod itself owns (i.e. through
  `remote.call('ai_player', 'run_skill'/'get_state'/etc, ...)`). Direct
  access from `run_lua` raises `attempt to index field 'ai_player' (a nil
  value)`.
- **Workaround to get the AI character from `run_lua`**: scan
  `surface.find_entities_filtered{type='character'}` and exclude any entity
  that matches a real player's `.character` (build a set from
  `game.players`). The one left over is the AI's.
  ```lua
  local player_chars = {}
  for _, p in pairs(game.players) do
    if p.character then player_chars[p.character.unit_number] = true end
  end
  local ai_char = nil
  for _, e in ipairs(surface.find_entities_filtered{type='character'}) do
    if e.valid and not player_chars[e.unit_number] then ai_char = e break end
  end
  ```

## Skill-layer behavior (upstream `mod/scripts/skills.lua`)

- **`build_miner` (and similar placement skills) place entities directly via
  RCON without moving the character first** — an intentional workaround for
  a placement-collision bug in the upstream code. The character does not
  visibly walk/act at its own location; only the new entity appears,
  wherever the resource patch was.
- **`build_miner` picks the single nearest resource *tile*, not the richest
  patch.** A large overall deposit can still have small/edge tiles nearest
  to the character, which deplete almost immediately. Better: find the
  patch's dense center via `find_entities_filtered{name=..., type='resource'}`
  sorted by `amount`, teleport the character there first, *then* call the
  skill.
- **`build_miner`'s furnace-at-drop-position placement fails/collides
  often** (`"couldn't place stone-furnace at drop {x,y}"`). Placing nearby
  instead via `find_non_colliding_position(name, drop_position, ~6, 0.5)`
  works, but the drill's automatic output-to-adjacent-container link is
  **only guaranteed at the exact drop tile** — a furnace placed a few tiles
  off will not reliably auto-receive drill output, and needs manual
  transfer (`drill.get_output_inventory()` → `furnace.get_inventory(
  defines.inventory.furnace_source)`) until a real inserter connects them.
  Same issue applies to furnace-output → chest.
- **Burner-mining-drills have small effective coverage** — even within a
  large overall ore patch, an individual drill can deplete (`status:
  depleted`) surprisingly fast. Don't judge patch richness from one drill's
  status; check the underlying resource tile `amount` before placing.
- **`fuel_all()` only checks near the character's *current* position**
  (mod-defined radius). If the character has been teleported around a lot
  (common when chasing resource patches), distant machines get missed. A
  global sweep over `surface.find_entities_filtered{force=...}` checking
  `get_fuel_inventory()` on everything is more reliable when the character
  isn't anchored to one spot.
- **The `research()` skill's "unlocked by CRAFTING" error message is
  hardcoded** to always say *"hand-craft automation-science-pack (1
  copper-plate + 1 iron-gear-wheel)"*, regardless of which tech/trigger is
  actually next. **Don't trust it — verify the real trigger directly**:
  ```lua
  local trig = force.technologies[name].prototype.research_trigger
  -- trig.type, trig.item.name, trig.count
  ```
  Confirmed wrong at least twice in one session (real triggers were "smelt
  50 iron-plate" and "craft 1 lab", not automation-science-pack either time).

## Research triggers (`research_trigger`, Factorio 2.0 / Space Age)

- Space Age's early techs mostly use `research_trigger` (types seen:
  `craft-item`, `mine-entity`, `capture-spawner`, `create-space-platform`,
  `build-entity`) instead of queued science-pack research. Must inspect
  `technology.prototype.research_trigger` per-tech; there's no shortcut.
- **`craft-item` triggers driven by automated/machine production DO count**:
  `steam-power`'s trigger (craft 50 `iron-plate`) was satisfied purely by
  furnace-smelted iron-plate reaching a cumulative total of 50 — no hand
  crafting involved.
- **`craft-item` triggers tied to hand-crafting appear NOT to count when the
  crafting character isn't a connected `LuaPlayer`**: the AI character
  hand-crafted a `lab` via `character.begin_crafting{recipe='lab', count=1}`
  (mechanically succeeded — item count went from 1→2), but
  `force.get_item_production_statistics(surface):get_input_count('lab')`
  stayed at `0` and the `automation-science-pack` tech's `research_trigger`
  never fired. **Researched via deep-research (2026-07-24), still open**:
  the official Lua API docs for `ResearchTrigger` (craft-item type) only
  document `item`/`item_quality`/`count` fields and say nothing about
  player-vs-character semantics; FFF-376 (the devblog introducing trigger
  technologies) likewise doesn't address it at the API level. So there is
  **no documented confirmation that a LuaPlayer is required, and no
  documented workaround** — our in-game test result is suggestive but not
  proven by any primary source found. Until this is resolved (candidates:
  ask on the Factorio Discord/forums, or read the base game's control
  scripts directly), the practical working assumption is: have the human
  player hand-craft the specific trigger item when one comes up. Do **not**
  work around it via `technology.researched = true` — that crosses into
  faking earned progress, same spirit as never editing the save file
  directly.
- Distinction worth remembering: **automated production trigger-checks
  appear to work fine for the AI character's builds** (furnaces, drills,
  anything the AI's *machines* produce) — it's specifically **hand-crafting
  by the AI character** that may not register for trigger purposes.

## Legitimate vs. not (house rule, not an API fact, but relevant here)

- Unlimited reach / direct API manipulation through `run_lua` while the game
  is live (mining without walking there, moving items between inventories,
  placing entities) **is legitimate play** — the AI character has no body to
  simulate walking with.
- Directly writing state that represents *earned progress* rather than
  mechanical position (e.g. `technology.researched = true`) is **not**
  legitimate — same spirit as the hard rule against editing the save file
  directly to shortcut a goal.
