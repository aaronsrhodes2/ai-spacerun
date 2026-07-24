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

**Goal**: complete Space Age. External blueprints are fair game throughout.
