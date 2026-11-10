---
name: factorio
description: God-mode helper for the Captain's live Factorio Space Age game on skippy-games. Use for any request about the game - build something, find or mine a resource, fix a bottleneck, what's blocked, research, trains, planets, mods, saves, or the server. Read before the first game action in a session, and update it when something new is learned.
---

# Factorio god-mode helper

The Captain plays live while giving orders from this chat, such as "find more coal, mine it and bring it to the central base by train". Carry the order out on the map. The goal is to research everything and finish Space Age.

**Be more help than hindrance.** Never break what's running, block where the player is working, or leave a half-finished build without saying so.

## The rules
- **The only barriers are research progression and planet progression** (the Captain, 2026-11-06). Everything else is creative: placed entities are free once researched (`place_entities` enforces that; don't bypass it with `run_lua`), starter fuel is free, and the Captain's own player has `cheat_mode` (free crafting of anything researched), 50x hand speed, 200-tile reach and 200 extra inventory slots. Re-apply the force bonuses on a new force or surface if they don't carry.
- **Science packs are still made by the factory.** Research only counts as progression if the chains that make the packs exist, so never spawn packs or lab contents, and don't hand-craft them in cheat mode either. Planets are reached by real rockets and platforms.
- **Never write research state.** Queueing is fine. A trigger tech is earned by really making its item.
- Build in unused land next to the used area unless told otherwise.
- The Captain gave full write access to the game, mods and saves on 2026-11-06. Achievements on this save are given up.
- Starter fuel via `seed_starter_fuel` is fine any time, but a machine out of fuel is still a supply bug to fix, not a reason to seed again.
- Every coal-powered machine must be fed by belt, not by hand.
- **The fuel paradox** (the Captain, 2026-11-06): only an inserter can fuel an inserter, so the head of a burner-inserter chain gets its coal by hand (`seed_starter_fuel`). Once power is up, every new inserter is electric: that is what makes full automation possible. Keep the boiler's own coal inserter a burner one, so power can restart from nothing.
- **Biters and pollution are switched off** (the Captain, 2026-11-06, replacing an earlier wish for walls and a turret maze): `map_settings.pollution.enabled=false`, `enemy_evolution` and `enemy_expansion` off, every surface in `peaceful_mode`. Biters only fight back if attacked. Nests matter only when we go to clear them, which is when turrets, ammo and `restock_turrets` come in. Re-apply these settings if a new surface appears (planets, platforms).

## Connection
- Server: `skippy-games`, `35.233.145.176:34197`, GCP project `skippy-tel`, zone `us-west1-b`. Factorio 2.1.24 in Docker container `factorio`, data in `/srv/games/data/factorio`.
- SSH as `aaron_s_rhodes` with this PC's default key. It has sudo.
- RCON is not published on the VM. The MCP server keeps a tunnel from `127.0.0.1:27115` to the container, set by `FACTORIO_SSH_TARGET` in `bridge/.env`. The code is `bridge/factorio/tunnel.py`.
- SkippyTel owns the server: `SkippyTel/games/docker-compose.yml`, `SkippyTel/scripts/games.sh`, `SkippyTel/docs/games/README.md`. Change its setup there, not by hand on the VM.
- The VM sleeps after 30 idle minutes and after 8 hours (`scripts/games.sh up factorio --idle 0` disables both). The game pauses when nobody is online, so production and research stop too.

**If tools report that RCON failed:** first check whether the VM is awake with `scripts/games.sh status` in SkippyTel. Starting it costs money and pings Discord, so ask first unless the Captain has asked to play.

## Tools (MCP server `factorio`)
| Need | Tool |
|---|---|
| Orient yourself: players, research, base size, what they're hovering | `game_overview` |
| Find ore, nearest to the base, used or not | `find_resource_patches` |
| What's blocked and how much is made | `factory_problems` |
| Read terrain and ore tile by tile | `map_grid` |
| See it: check layouts by eye after every build | `screenshot`, then Read the path it returns. Needs the Captain's client online |
| Build | `place_entities`, use `dry_run` first on big builds |
| Start a fuel loop | `seed_starter_fuel` |
| Tear down | `remove_entities` |
| Research | `research_status`, `queue_research` |
| Talk to the player, tag a map spot | `tell_player` |
| Restore point | `save_game` |
| Is the factory healthy? Per-minute rates, power, stalled machines | `scripts/health.py` (60 s measurement) |
| Overflow of red packs for later | chest at (-79,-65) (labs' red belt end); green: chest at (-42,-77) |
| Anything else | `run_lua`, must call `rcon.print` |

The older character tools (`gather`, `build_miner`, `spawn_ai_player` and so on) need the `ai-player-v3` mod. It isn't on this server and isn't needed.

## Game knowledge: look it up, don't recall it
Your memory of Factorio can be wrong for this version. `reference/` is dumped from the live server by `scripts/dump_game_data.py`, so use it for any number or recipe, and re-run the script after a game or mod update.

| Question | File |
|---|---|
| How does a pack get made, from raw ore? What does all research cost? Which techs are triggers? | `reference/science-packs.md` |
| What machines exist and how fast are they? | `reference/machines.md` |
| What spoils, how fast, and into what? | `reference/items-that-spoil.md` |
| What can only be made on a certain planet? Planets and routes? | `reference/planet-only-recipes.md` |
| Any single recipe, item, machine, tech, fluid or resource in full | `reference/{recipes,items,entities,technologies,fluids,resources,planets,space_connections}.json`, search them with Grep |
| Strategy for Space Age | `docs/reference/space-age-strategy.md`, `docs/reference/buildings.md` |
| A Lua field has vanished in 2.1 | `reference/external/factorio-2.1-breaking-changes.md` (MIT, from Jaer985/factorio-modding-skill) |
| Writing an actual mod | Read https://github.com/Jaer985/factorio-modding-skill, its SKILL.md is 100 KB so take only what's needed |

**How progress works:** techs consume science packs in labs, one of each per unit, and some techs are triggers instead (make an item, build a thing). So every plan answers: what's the next tech, which packs does it need, and which step in that pack's chain is short? Twelve packs exist, and the later ones need other planets: metallurgic (Vulcanus), electromagnetic (Fulgora), agricultural (Gleba), cryogenic (Aquilo), plus space and promethium. Check this against `science-packs.md` before relying on it.

**Gleba is the failure mode the Captain most wants handled.** Yumako mash lasts 3 minutes and fruit 60 minutes, and a backed-up line becomes spoilage that blocks it. Plan it so belts keep moving and spoilage always has somewhere to go.

## Design rules learned the hard way
- **Never run a destructive step after an unchecked one.** 2026-11-06: a chest move failed (the target tile held a pole), the script carried on and removed the old chest, destroying 1,054 red packs of stockpile. Move items, read the new count back, and only then remove the source. Stop on the first error.
- **Swapping machines can strand inserters.** After replacing assemblers or furnaces, inserters that fed them may hold an item the new machine won't take (copper plates in the gear inserters starved four green chains). The upgrade scripts end with a pass that clears any inserter `waiting_for_space_in_destination` that is holding something.
- **Restoring can undo a deliberate change.** The mines plan re-laid a stone belt tile that the smelting build had trimmed, and stone ran into the iron furnaces (bricks on the plate belt, assemblers starved). When a later build removes part of an earlier plan, change the earlier plan too.
- **Every build is a script that can be re-laid.** `scripts/restore.py` re-places every plan; what stands reports "blocked", what's missing comes back. Plans that put drills on ore need the pre-build `map_grid` snapshot (the live grid shows the entity, not the ore under it): keep those in `snapshots/`. Always take and keep one before building on ore.
- **Peaceful mode doesn't recall attack groups already on their way.** When switching it on, destroy every enemy unit on the surface, not just those near the base: a group from a nest 305 tiles out wiped the iron row after a 300-tile clear (2026-11-06).
- `factory_problems` found that fault at once (furnaces `no_ingredients`, every assembler starved) while the research watcher still looked fine. Run it whenever numbers look off. Its production-rate section comes back empty on 2.1: `get_flow_count` needs fixing before those numbers mean anything.
- **Every consumer on a belt needs a producer upstream of it.** On 2026-11-06 a coal band's easternmost inserter sat upstream of all the drops. It starved, and the failure spread along the band once starter coal ran out. Self-fuelling loops must be rings: see `coal_band` in `scripts/build_first_mines.py`.
- **Starter fuel hides bugs for minutes.** 5 coal runs a burner drill for about 2 minutes, so watch for longer than that before saying a build works. `scripts/watch_first_mines.py` is the pattern.
- **Drills must sit on one ore only**, or they output a mix. `Plan.drill` refuses mixed tiles.
- With no undergrounds, plan the order of lines around the hub first so nothing has to cross.

## How to run an order
1. `game_overview`, then look at what the order touches. Read before you build.
2. Say the plan in a sentence or two if it's big or the choice is genuinely the Captain's. Otherwise go ahead.
3. `save_game` before anything risky or large. Check disk space first: it was 98% full on 2026-11-06.
4. `dry_run`, fix failures, place in batches of about 500.
5. Check the result by reading the map back, including that machines are actually working. A placed entity isn't a working one.
6. Tell the Captain what was built and where, using a map tag, and what's still unfinished.
7. Add anything new you learned to this file.

## One-command scripts: `scripts/fx.py` (use these before hand-writing Lua)
Run from the project root with `python scripts/fx.py ...`. Areas are `--area X1 Y1 X2 Y2` (tiles, inclusive) or `--around X Y R`; `--surface NAME` for platforms. Everything that changes the map is a dry run until you add `--apply`, and the dry run prints what it would do.
- **`clear AREA [--trees --rocks --cliffs --biters --decoratives --fish --items --corpses | --all]`** removes trees, rocks, cliffs, enemy units/spawners/worms, decoratives, fish, items on the ground. Do this before building on ground that is not yet clear (items on the ground and trees make `can_place_entity` fail).
- **`upgrade AREA [--belts --inserters --chests --machines --poles --furnaces --bulk | --all]`** replaces each entity with the best researched tier by fast-replace (belt -> fast -> express, inserter -> fast (-> bulk with `--bulk`), wooden -> iron -> steel chest, assembler 1 -> 2 -> 3, small -> medium pole, and with `--furnaces` stone -> steel -> electric). Splitter filters and priorities survive; underground types are kept. `--storage` turns wooden/iron/steel chests into logistic storage chests (contents kept). Add `--modules speed|productivity|efficiency --from-chest X Y` (or `--from-hub` for a space platform hub) to fill every empty module slot with the best tier that the source really holds. Modules come from a source; `--spawn` (only on the Captain's explicit order) makes them appear, `--module-name speed-module-2` fixes the tier, and `--budget-mw N` stops filling when the estimated extra power demand would pass N MW (labs first, then assemblers, furnaces, drills). The dry run prints that estimate: always read it before filling, because every module raises energy use (speed module 2: +60% each).
- **`bottlenecks [AREA] [--top N] [--json] [--ledger ITEM...]`** prints alerts (unpowered, unfueled, fluid-starved machines, recipe-less assemblers) and every starved machine group with the exact missing ingredient, what its feeder belts carry, who produces the ingredient and in what state, and a one-line fix plan (supply broken / producers starved / capacity / suspected lane jam). Start here for "why is X not being made". Run it before and after every fix.
- **`compact AREA [--keep N]`** shrinks a factory by deleting whole empty columns and rows (a straight belt running across a gap does not count as occupying it; that belt tile is dropped, which just shortens the line) and moving everything beyond. Nothing is rotated or re-routed. Refuses areas that contain rails, train stops, signals, vehicles, or entities crossing the border. `--apply` saves the game first, moves by clone so inventories, recipes, modules and settings travel, and verifies entity counts, pole networks, inserter links and belt links (it prints how to roll back if anything differs). Pick the area so each block is whole inside it. Poles are re-created, not cloned, so wire topology is re-derived.
- **`mine AREA --resource ORE [--out N|E|S|W] [--belt NAME] [--min-tiles N] [--allow-mixed]`** lays out a mining patch: belt columns with a drill row on each side, a medium pole in the gap between drill pairs, one collector belt, and an output belt leaving toward `--out`. It tries all 49 grid offsets and keeps the one with the most ore, never puts a drill where a second ore is in reach (unless `--allow-mixed`), drops spots that are blocked, and prints the drill count, expected ore/s and the output tile. Dry run by default. The pole chain is not joined to the grid: link it. It lays out the "simple" family (like the Mining Patch Planner mod, which has no remote interface and cannot be driven from RCON).
- **`--planner` on `clear` and `upgrade`** marks the work with the game's own deconstruction/upgrade planner for construction robots (real item cost, only where a roboport reaches; it prints the coverage). The direct modes are instant and free.
- **Robot coverage:** `scripts/build_roboport_grid.py` put a roboport with its own solar kit (3 panels, 2 accumulators, a pole) in every 48x48 cell that holds anything of ours, so the whole factory (belts, rails, depots, mines, oil site) is one logistic network. Re-run it after building somewhere new; it skips covered cells and bridges gaps.
Facts learned building these: `create_entity{fast_replace=true, spill=false}` upgrades in place and keeps belt items; `LuaEntity.clone{position,surface,force}` moves an entity with its contents; `LuaEntity.bounding_box` of a vehicle is NOT rotated (use orientation); `inserter.drop_target` reads nil for a moment right after create_entity; `entity.status` enum values differ per version, so always map names through `defines.entity_status`.

## Finding blockages
Work from `factory_problems`. Power first: `low_power` or `no_power` makes every other reading misleading. A machine with no ingredients is starved, so look upstream. One with full output is backed up, so look downstream. The bottleneck is usually where a backed-up section meets a starved one.

## What's known about the API
Verified on the live server unless marked otherwise.
- The first `/sc` on a new RCON connection returns empty. `_q` in `mcp_server.py` primes each connection, so real commands aren't sent twice.
- `build_check_type.script` ignores collisions, so `can_place_entity` said yes and stacked two chests. Use `manual`.
- `helpers.table_to_json` renders an empty table as `{}` even when it's a list.
- RCON commands are limited to 65535 characters. Long Lua must stay on one line with no `--` comments.
- Entities can only be placed in generated chunks. For new ground use `surface.request_to_generate_chunks` then `force_generate_chunk_requests` (not yet tested).
- Directions in 2.x: 0=N, 4=E, 8=S, 12=W.
- An inserter's `direction` is its pickup side. It drops on the opposite side.
- A burner drill facing north drops above its left column; facing south, below its right column; facing east, right of its upper row. Tile (x, y) as top-left puts its position at (x+1, y+1).
- Recipes use `categories`, a list. `recipe.category` is gone in 2.1.
- `LuaXPrototype` raises an error on a missing key instead of returning nil, and has no `.help()`. API methods are called with a dot and no self: `p.get_spoil_ticks()`.
- `get_entity_filtered` wants a list of filter tables: `{{filter='type', type='resource'}}`.
- Trigger techs can complete from furnace output (`steam-power` from 50 iron plates, July 2026 local save). A hand-craft by a character did not fire `automation-science-pack`'s trigger then, so a trigger may need the Captain to craft the item.
- First techs on this map: `electronics` (make 10 copper plates) and `steam-power` (make 50 iron plates). Both fired from furnace output alone.
- A real, connected player's `begin_crafting` fires `craft-item` triggers: `automation-science-pack` unlocked the moment the Captain's character finished a lab (2026-11-06). Use the Captain's crafting queue for the first lab and the first packs, and tell them first.
- The research queue holds 7. `add_research` returns false when it is full. `force.research_queue_enabled` is gone in 2.x.
- `transport_line.remove_item{count=0}` raises an error that aborts the whole command. Guard every count.
- Inventory names in 2.x: `defines.inventory.crafter_input` / `crafter_output` for assemblers and furnaces, `lab_input`, `chest`, `turret_ammo`. `assembling_machine_input` and `furnace_source` are gone.
- `find_entities_filtered{area=...}` matches anything whose collision box overlaps the area, so a box that touches a tile edge also catches the neighbour. To hit one tile, use its centre ±0.2. `remove_entities` once took the belt next door this way.
- Fluids in 2.1: `LuaEntity.fluidbox` is gone. Connection points come from `prototypes.entity[n].fluidbox_prototypes[i].pipe_connections[j].positions`, relative to the entity's position. Measured: boiler (3x2, facing N) takes water at (-2, +0.5) and (+2, +0.5), gives steam at (0, -1.5); steam engine (3x5, facing N) connects at (0, -3) and (0, +3). `entity.get_fluid_contents()` reads what is inside.
- `offshore-pump` facing S must sit on the shore tile with water to its south; `can_place_entity` with `build_check_type.manual` finds valid spots.
- Nearest nest is ~115 tiles east of the coal mines (around 150, -40). Before peaceful mode it took out drills twice.

## Built so far
- **Green science**: seven AM2 chains (`build_green.py chain..chain7`), ~52 packs/min. **27 labs** in three daisy-chained rows (`build_science.py labs/labs2/labswest`).
- **Mining**: electric iron field (12 drills, `build_iron3.py`) onto the ore spoke; electric copper field (6 drills, `build_copper2.py`, joins on the ore lane via underground); electric coal: boiler line field (`build_coal2.py`, 5 drills) and trunk source (`build_coal3.py`, 5 drills replacing the burner ring). **Burner drills still run on the iron row, copper row and stone row**; they're the first thing to swap for electric when the coal trunk runs short.
- **Smelting**: all furnaces are steel (`upgrade_furnaces.py`), spoke smelter 12 + hub 5 iron, 6 copper.
- **Power**: plant 1 (2 boilers, 4 engines) and plant 2 (3 boilers, 6 engines at x=37..47,y=8..19, `build_plant2.py`), 9 MW total. Boiler coal: two electric lifts plus the north coal field.
- **Oil**: 7 pumpjacks at the NW field (-314,-293), big-pole line (10 poles, `build_oil.py`), 129-piece crude pipeline (`build_crude_pipe.py`), one refinery at (-152,-114) on basic oil processing, one chemical plant making plastic (`build_plastic.py`) with coal on a belt extended from the copper row's fuel line. Plastic collects in the chest at (-147,-121).
- `bridge/factorio/planner.py`: belt router with no crossings, drill and inserter placement, tested in `tests/test_planner.py`.
- Smelting (`scripts/build_smelting.py`): 5 iron furnaces at the hub, 6 copper furnaces on the copper line, each fed ore and coal by one burner inserter from a two-lane belt. Electric inserters put plates on belts at y=-56 (iron) and y=-57 (copper) running west to x=-66.
- Power (`scripts/build_power.py`): offshore pump at (28.5, 51.5), one boiler and two steam engines north of the lake, coal from the ring by a 110-tile belt, 26 small poles to the base.
- Red science (`scripts/build_science.py`, stages `labs`, `labs2`, `assemblers`): 12 labs in two rows (the second fed lab-to-lab), 6 pack assemblers, a gear assembler feeding gears onto the copper belt's spare lane, an ammo assembler into a chest at (-37, -63).
- The first mines on Nauvis: `scripts/build_first_mines.py`. Hub at (-20, -62) with iron from the north, coal from the east, copper from the west, stone from the south. Fuel trunk runs along x=9 and y=-108 to iron then copper. Stone's fuel is lifted off the coal line at (9, -58).

## Rails and trains: what was learned (2026-11-06, first line working)
- **Geometry comes from the game, never from memory.** `scripts/rail_catalog.py` places every rail piece in all 16 directions on cleared ground and records both open ends via `get_rail_end(...).location`; `snapshots/rail-catalog.json` holds it. A piece continues a track when one of its ends sits on the open end facing the other way (dir+8). The test area must be truly clear (trees block some orientations and silently drop them from the catalog).
- **Router** (`bridge/factorio/rails.py`): `route(start, [(heading, line[, end_along])...])`. Straights are 2-tile pieces; a corner is the compact four-curve turn (curved-a, curved-b, curved-b, curved-a, ~14 tiles across); the straight run before it is sized so the turned track lands exactly on `line`. `line` must have the right parity (odd, for tracks on this grid) and lie ahead. Start from a virtual open end `(x, y, heading)`; for a N-S track at x=145 starting at y=72 heading north, that is `(145, 72, 0)` and the first piece is requested at (144, 70).
- **Rail entity positions**: you request (px, py) on even integers; the game reports the entity at (px+1, py+1), and a N-S track's centre line is x = px+1.
- **Train stops sit on the right-hand side of their direction of travel** (N-bound: east of the track; S-bound: west; E-bound: south; W-bound: north), at the rail centre where the train's FRONT stops; the wrong side is refused. `find_stop` in `scripts/build_coal_line.py` tries the expected tile first and checks `connected_rail`.
- **A dead-end line needs a locomotive at each end** (loco, wagon, loco); the game drives with whichever faces the way it's going. A stop inside the train's own length gives `no_path`.
- **Fuel each locomotive where it is at the front**: at the hub the north loco is the front, at the patch the south loco is. Hub: an inserter from the unloading belt into the loco. Patch: a drill whose output faces the loco feeds it coal directly. Drills output straight into an adjacent cargo wagon, no belts or inserters.
- A train stands about 20 tiles for loco+wagon+loco; stock is placed 7 tiles apart along the track. Pausing drills (`disabled_by_script = true`) before placing stock is cheap insurance against items in the way.
- Schedules: `train.schedule = {current=1, records={{station=..., wait_conditions={{type='full'|'empty'|'time'|'inactivity', compare_type='and'|'or', ticks=...}}}}}` then `manual_mode = false`. Station names are the stop's `backer_name`.
- **Line 1: coal** (`scripts/build_coal_line.py` stages `rails`, `patch`, `hub`, `train`): patch (145,62), 82 rails north to y=21, west, north up x=71 to the base's east side; the hub unloads onto a belt along x=68 that runs north and west under the boiler-feed belt into the trunk top belt. One loco+wagon+loco train, ~2 coal/s. It is the template for every further line.
- A biter nest sits at about (346-358,-50..-30), another near (150,-45)..(152,-34); they are peaceful but you cannot build on a spawner, so route around them.

## Pipes, oil and rails: what was learned
- **Underground pipe orientation** (tested): entry direction = opposite of the flow, exit direction = the flow direction. South flow: entry N(0) / exit S(8). East flow: entry W(12) / exit E(4). Max gap 10. `planner.underground_run` does this and `planner.pipe_route` routes manifolds.
- **Refinery** (5x5, facing N): crude in at the bottom corner tiles `(-1,+3)` and `(+1,+3)` from its centre, petroleum gas out of the third top tile `(+2,-3)` for basic oil processing (tested). Top-left (-152,-114) gives centre (-149.5,-111.5).
- **Chemical plant** (3x3): facing S puts its fluid inputs on the south side, which is why the plastic plant sits north of the refinery with a pipe row between.
- **Pumpjack** (3x3): output tile by facing is `(1,-2)` N, `(2,1)` E, `(-1,2)` S, `(-2,-1)` W from the centre. Jacks can rotate freely (`e.direction = ...`).
- **`oil-processing` is a trigger tech**: it fires when a powered pumpjack mines crude oil. Everything else in the red+green list is queueable.
- **Hard prerequisites can be red-only.** `modular-armor` needs `heavy-armor`, `weapon-shooting-speed-2` needs `weapon-shooting-speed-1`: both red-only, and six red+green techs stalled behind them. When a goal list stops advancing, check `missing_prereq` of what's pending.
- Big poles reach 32 tiles but a big-to-small link is limited to the small pole's 7.5; medium poles reach 9 (so 9.06 fails). Use `find_non_colliding_position` for poles in unknown terrain.

## Not built yet
When one of these gets built, move it to the tools table and note what was tested.
- **More train lines**: only coal line 1 exists. Next: iron, copper and stone outposts and the `10 patches each` target (the generated map has fewer; chunks must be generated outward first). Needs: a generic outpost generator, signals once two trains share track, a real hub (belts into the existing smelters, or new smelters), and a second coal source before patch 1 runs dry.
- Chemical science (the tech is done; the packs need sulfur, so water for the refinery site) and everything planet-side.
- Sulfur and anything needing water: no water near the refinery; pipe from the south lake or move the complex.
- General outpost layouts. The first mines use one-off rows, so power poles and electric drills are still to come.
- Connecting to existing base lines, plus defense. Pollution from these drills will reach biters eventually.
- Blueprint-string import.
- Research driver: what's blocking the next tech, then build it.
- Space platforms and other planets. Surfaces need a real arrival first (not yet tested).
- `factory_problems` has only run on an empty map, so check its output against a real factory.

## Verifier (run after every build)
`.venv/Scripts/python.exe scripts/verify.py x1 y1 x2 y2` (default: blue block) lists inserters with no pickup or
drop target, electric machines on no network or with no_power, and belt dead ends, plus a status count per machine
type. Exit code 1 on hard problems (belt dead ends are information: lane ends are normal). Tested: it flags a lone
inserter in empty ground. Burner furnaces are not counted as unpowered.
Next: standard blocks with declared input/output ports, checked by this verifier at their edges.

## Chest rules (the Captain, 2026-11-09)
- **Yellow storage chest:** only where no inserter draws from it. It is where robots drop trashed items, so trash yards only. Never convert working chests to it (it pulled in junk and polluted the network on 2026-11-09).
- **Steel chest:** no drone interaction; a plain local buffer. The Captain (2026-11-09) said steel chests can safely become red providers; all but the junk stash were converted. Anything with an inserter on it that must stay out of the network.
- **Red passive provider:** the end of a production line; offers its contents to requesters.
- **Blue requester:** the start of a line; set the request to what the consumer needs (about 60 s of work), never "stock it full".
- **Buffer chest:** both asks like a requester and offers like a provider (below passive providers in priority). Use only for a local stock of a scarce item that many requesters share; otherwise skip it.

## fx.py logistics (belt-fed to drone-fed; built 2026-11-09, scripts/logistics.py)
- `fx.py logistics survey --area X1 Y1 X2 Y2`: machines (solid/fluid), belt pieces, inserters from/to belts, what the belts carry.
- `fx.py logistics convert --area ... [--minutes 1] [--apply]`: every assembling machine and furnace with a solid recipe: belt tiles its inserters pick from become blue requester chests (the recipe's ingredients for about
  --minutes of work, at most 2 stacks), belt tiles its inserters drop on become red provider chests (a tile used both ways becomes a provider). Inserters stay; fluid recipes, undergrounds and splitters are skipped. Saves first.
- `fx.py logistics retire --area ...  [--apply]`: removes belt/underground/splitter groups wholly inside the area that no inserter, drill or loader uses; items on them are salvaged into red provider chests near the area. Groups crossing the
  border are never touched. Run convert on the WHOLE chain first, then retire.
- Lesson from the first trial (rail assemblers at (63..67,-131), 2026-11-09): converting a machine whose ingredients are not in the network starves it (stone, iron sticks and steel were not provided as chests, they came by belt), so
  convert producers and consumers of a chain together, and make sure every raw input has a provider chest somewhere. The two rail assemblers there now wait for stone and iron sticks.
