# Progress log

Dated entries, newest first. Milestones, dead ends, and decisions — not a
full transcript.

## 2026-07-23 — Setup complete, first actions taken

**Setup (Stage 1 of the plan):**
- Cloned `thedemon117/ai-player-v3` into this repo, Python 3.13 venv,
  dependencies installed.
- Confirmed RCON does **not** work under plain Singleplayer — only when the
  save is hosted as (solo) Multiplayer, via `config.ini`'s
  `local-rcon-socket`/`local-rcon-password`. Verified directly against a
  Wube developer's forum post and the user's own `config.ini`.
- `bridge/.env` configured with RCON credentials only — no LLM provider key
  anywhere, since Claude Code drives the character directly via the MCP
  server (`bridge/factorio/mcp_server.py`), not the mod's own autonomous
  bridge loop.
- Registered the MCP server with Claude Code via `.mcp.json`. Confirmed the
  `mcp__factorio__*` tools work end to end: `spawn_ai_player` →
  `set_autonomy(false)` → `set_coop(true)` → a real skill call
  (`build_miner`) produced a real drill in the world.
- **Quirk**: the first RCON call after any fresh connection comes back as an
  empty string rather than erroring or returning data; a second identical
  call then succeeds. Worth a "retry once on empty" in future tooling
  (`scripts/smoke_test.py`, not yet built).

**First real gameplay actions:**
- Cleared all 14 crash-site wreckage entities (`crash-site-spaceship-wreck-*`)
  and 2 `big-sand-rock`s near the player's spawn point, and looted a wreck
  chest (+2 iron-plate). No skill/primitive currently exists for "mine this
  specific entity" — did this via a `run_lua` pass that finds the AI
  character by excluding real players from `find_entities_filtered{type=
  'character'}` (direct `storage.ai_player` access from `run_lua`/`/sc`
  fails — that table belongs to the mod's own Lua state, not the console's;
  only the mod's `remote.call('ai_player', ...)` interface can see it).
  Candidate for a proper skill later.
- Surveyed resources within 80 tiles of spawn: ~229 copper-ore, ~800+
  iron-ore, ~340 coal. Next: gather coal/copper/iron as requested.

**Two known issues from the first `build_miner` call, not yet fixed:**
1. Placement skills place entities directly via RCON without moving the
   character there first (an intentional workaround for a placement-collision
   bug in the upstream code) — so nothing visibly happens at the character's
   own location, which undercuts watching the AI play. Candidate fix: make
   placement skills walk the character to the target first, like `gather`/
   `deconstruct` already do.
2. `build_miner` doesn't check patch size before committing — the first drill
   landed on a tiny patch and was `depleted` after ~9 ore.

**House rules established this session** (see the plan file's "Play
parameters" and "Project discipline" sections for the full list): cost-aware
model choice, blueprint-first (and export our own builds back into the
library), no hesitation on in-game destructive actions, respect
pollution/depletion/defense and restart from a save rather than churn,
save after each completed project, abandon-and-mark difficult projects
rather than spiral, label liberally in-world (names/signs/display panels),
and — hard constraint — never edit the save file directly to shortcut a
goal.

## 2026-07-24 — First production loop + a real research-trigger limitation

**Mining/smelting/storage goal** (coal, copper, stone, iron — mined, smelted where
applicable, fueled by coal, product stored in iron chests): achieved a working
version. 5 burner-mining-drills (coal, copper-ore, iron-ore, stone ×2) and 3
stone-furnaces (iron-plate, copper-plate, stone-brick recipes) placed, each
furnace linked to an iron-chest catching its output. `build_miner`'s
drop-position furnace placement collided almost every time (something about
the exact tile being blocked) — worked around by placing the furnace nearby
via `find_non_colliding_position` and confirming the drop-position auto-link
still catches most output. Burner-mining-drills have a small effective
coverage and deplete individual ore tiles surprisingly fast — several are
already `depleted`/`no_ingredients` again. This needs a real fix (multiple
drills spread across a patch, or upgrading to bigger/electric drills later),
not more manual patching.

**Clarified mid-session where the actual line is**: initially second-guessed
using `entity.mine{force=true}` and manual inventory shuffling between
drill/furnace/chest as "not really playing." User confirmed this is fine —
the AI character has no physical body to simulate walking/reach with, so
unlimited-reach, direct-API manipulation through the live game (mining,
moving items, placing entities, all via RCON while the game runs) **is**
legitimate play. The one hard, unchanged line: never rewrite the save file
directly outside the game's own live mechanisms (no editing `.zip`/save
internals to fake progress). Noted so this isn't re-litigated every
session.

**Research-trigger discovery**: got `steam-power` researched by smelting
50 iron-plate (a real `craft-item` trigger — furnace production statistics
count toward it). But `automation-science-pack`'s trigger (craft 1 `lab`)
did **not** fire even after actually hand-crafting one via
`character.begin_crafting` — `force.get_item_production_statistics():
get_input_count('lab')` reads 0 despite the craft succeeding. Best
hypothesis: `craft-item` triggers hook `on_player_crafted_item`, which
likely requires a connected `LuaPlayer`, not just a `character` entity —
the AI character may not be able to satisfy player-gated research triggers
at all. Did not try to force this via direct technology-state writes (out
of bounds per house rules); the likely real fix is having the human player
hand-craft the specific trigger item when one comes up. Worth confirming
with a documented Space Age walkthrough rather than more trial and error.

**Also confirmed**: the mod's hardcoded research-skill error message
("hand-craft automation-science-pack...") is wrong for Space Age — it's a
static string that doesn't reflect the actual trigger item/count for
whichever tech is next. Worth fixing in our fork: read the real trigger
(`technology.prototype.research_trigger`) and report it dynamically instead.

**Goal**: complete Space Age. External blueprints are fair game throughout.
