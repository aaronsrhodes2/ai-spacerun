# Progress log

Dated entries, newest first. Milestones, dead ends, and decisions — not a
full transcript.

## 2026-11-06 — New direction: god-mode co-pilot on skippy-games

The Captain now plays live on the SkippyTel server `skippy-games` and gives orders
from the project chat. Claude acts directly on the map, with no AI character. Building
is free but gated by research, and anything consumed must be produced. This replaces
the July approach of a character on a locally hosted save, so the "no free items"
reading in the README's house rules no longer applies. The operating guide is
[.claude/skills/factorio/SKILL.md](../.claude/skills/factorio/SKILL.md), kept up to date as we learn.

**Built and tested on the live map (a new game with nothing built):** a self-healing SSH
tunnel to RCON (no server change needed: RCON was already on, just not published),
overview, resource patches, research status, research-gated placement and removal,
saves and chat. Testing caught `build_check_type.script` ignoring collisions, which stacked
two chests, so placement now uses `manual`.

**First order:** iron, copper, coal and stone by belt to a hub at (-20, -62), all burner machines
fed coal by belt, with no undergrounds available. Built by the new planner. Watching it caught a design bug: a
coal-band inserter upstream of every drop starved, and the failure spread along the band as the starter
coal ran out. The band is now a ring. The lesson is in the skill.

**Red science, same day:** smelting at the hub (11 stone furnaces, ore and coal on one two-lane belt
each), steam power at the lake with a 110-tile coal belt, then a science block west of the hub: 6 labs,
6 red-pack assemblers, a gear assembler sharing the copper belt's spare lane. The first lab and 10 packs
were hand-crafted through the Captain's own character (a real player's craft fires the trigger tech).
Automation researched 25 s after the packs went in; gun-turret, stone-wall, military, logistics and
electric-mining-drill followed within minutes. 15 red-only techs, 525 packs in all, queued to the end.

**Biters:** a nest 115 tiles east took out drills twice. The Captain first asked for walls and a turret maze,
then changed his mind: pollution, evolution and expansion are off and every surface is in peaceful mode.
A perimeter-and-kill-box script was written and discarded; `restock_turrets` stays for clearing nests later.

**Green science to ~10x, same day:** one chain made ~5 packs/min; seven AM2 chains now make ~52/min,
fed by an electric iron field (12 drills), an electric copper field (6 drills, joined on the ore lane),
steel furnaces everywhere, a second gear assembler with fast outputs, and a second 5.4 MW power plant
(10 engines total, 9 MW) with an electric coal field. 27 labs. A health report (`scripts/health.py`) measures
real per-minute rates; it found each limit in turn (gears, plates, labs). Two faults worth remembering:
inserters left holding copper plates after a machine swap starved four chains, and a chest move I ran
without checking the previous step destroyed 1,054 red packs of stockpile.
Oil: oil-gathering researched, big-pole line (10 poles) to the NW field at (-314,-293), seven pumpjacks
(~117 crude/s), and the oil-processing trigger fired. Refinery unlocked.

**All 46 red+green research goals complete** (plus the red-only prerequisites they needed). Oil refining is
running (7 pumpjacks, refinery, plastic). **First train line**: coal from the 343k patch at (145,62) to the
base, 82 rails built from a rail-geometry catalog taken from the game itself, with a loco-wagon-loco train
loading straight from drills and refuelling itself from the coal it hauls. A coal-trunk conversion
(five electric drills replacing the burner ring) fixed a coal shortage that had starved the plastic plant.
Tests: 26 planner/router tests pass.

**Game data:** every recipe, item, machine, tech, planet and route dumped from the live server into
`.claude/skills/factorio/reference/`, with each science pack traced to raw materials.

**Not built or not tested:** rail routing, general outposts, connecting to base lines, the research
driver, platforms and planets. `queue_research` has not been run at all.

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
