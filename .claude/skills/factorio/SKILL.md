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

- Names (docs/naming-sop.md is the rule): `LuaLogisticNetwork.custom_name`, `force.platforms[i].name`, `train.group` and `stop.backer_name` are writable. Renaming a stop does not rewrite schedules. Writing `train.schedule` drops the train's group; set the group after.
- Chest requests: `e.get_logistic_point(defines.logistic_member_index.logistic_container).sections`; `sec.group = 'name'` (a new name keeps the filters, an existing name takes the group's), `sec.set_slot(i,{value={type='item',name=..,quality='normal'},min=N})`. A circuit-driven section throws; check `sec.is_manual`.
- Circuit wires: `a.get_wire_connector(defines.wire_connector_id.circuit_red,true).connect_to(b.get_wire_connector(defines.wire_connector_id.circuit_red,true))`; condition through `get_or_create_control_behavior()` (`circuit_enable_disable`, `circuit_condition`).
- No `LuaEntity.fluidbox` in 2.1: use `get_fluid_contents()`. Storage tank ports: direction 4 tank at (cx,cy) connects at (cx+1,cy-2), (cx+2,cy-1), (cx-1,cy+2), (cx-2,cy+1); direction 0 at (cx-1,cy-2), (cx-2,cy-1), (cx+1,cy+2), (cx+2,cy+1).
- Items on a belt: `e.get_transport_line(i).get_contents()` and `.remove_item{}`; `network.insert{}` puts items into network storage, `network.remove_item{}` takes them out (the allowed way to move factory-made fuel).
- A locomotive with all three fuel slots holding another fuel never accepts the feeder's fuel. Empty the slots when changing the fuel standard.

- 2.1 has no `LuaEntity.fluidbox`. Read fluids with `e.get_fluid_contents()`.
- Storage tank ports: a tank at (cx,cy) facing north connects at (cx-1,cy-2), (cx-2,cy-1), (cx+1,cy+2), (cx+2,cy+1); facing east at (cx+1,cy-2), (cx+2,cy-1), (cx-1,cy+2), (cx-2,cy+1). The tile straight west of the centre is not a port.
- A pipeline longer than 320 tiles needs a pump. A horizontal pump at (X, y+0.5), X an integer, covers tiles X-1 and X; direction 12 pumps west. A pipe-to-ground pair can sit 10 tiles apart; `direction` is the side of the open end.
- An assembling machine 3 with a fluid recipe placed by `place_entities` keeps direction 0; set `e.direction` afterwards so the fluid port faces the pipe.
- Status numbers seen: 1 working, 18 no ingredients, 30 fluid shortage, 31 item shortage, 32 full output, 38 waiting for space, 60 no power, 61 disabled by circuit. Compare against `defines.entity_status`, do not hard-code.
- Unloading a wagon: the inserter must stand on the tile next to the rail (rail centre y, inserter y+1.5). One tile further and it never finds the wagon; `inserter.pickup_target` is nil with a train at the stop. Wagon centres for a loco-4 wagons-loco train whose front loco stands 3 tiles past the stop are stop x +10, +17, +24, +31; six inserters per wagon at centre -2.5..+2.5.
- A build is not verified until the cargo moved: read the chest or belt after a train has called.

- A `place_entities` dry run reports trees as "blocked at this position". `build_cells.py --apply` clears natural pieces first, so a dry-run failure on a machine tile may only be a tree: look at the tile before skipping the site.
- More power: `scripts/build_solar_field.py --panels X0 Y0 X1 Y1 --accus X0 Y0 X1 Y1 [--apply]` fills two boxes with panels and accumulators around the substation lattice. Afterwards check that every piece is on the turbines' `electric_network_id`: a strip without substations (x 288..320 at the south field) left 480 accumulators unconnected until substations were added.
- `invert=true` in `find_entities_filtered`/`count_entities_filtered` inverts the whole filter, force included, so "our entities not named X" must be filtered in Lua.
- Nuclear: `scripts/build_nuclear_unit.py` builds a 480 MW unit (2x2 reactors, 48 exchangers, 96 turbines); stack at pitch 28, side by side at X+88 with `--gap-east`. A reactor's `neighbour_bonus` needs the next reactor touching and exactly in line (centres 5 apart); it reads 0 until the reactor burns. Heat exchanger (3x2, direction 0): water passes through the short ends, steam leaves north, heat pipe goes directly south; turbines chain end to end. Turbines only deliver when a pole's supply area touches them. Offshore pumps cannot stand side by side (leave a tile between). `LuaEntity.fluidbox` does not exist on an offshore pump; use `get_fluid_contents()`. Status 34 on a reactor is a full spent-cell slot.
- Drone-fed cells far from their supply cost power: roboports drew 236 MW of a 265 MW grid (2026-11-09). Read the roboport line of the electric statistics before adding drone-fed load, and put cells next to their yard.
- A requester chest pulls from every red provider in the network, including the lab-side and station chests, so a requester feeding a belt that ends in a provider chest makes a loop. Feed the last belt directly.
- Underground belt pairing has no `neighbours` key in 2.1; walk upstream along the direction to find the input end.
- **Belt lanes (2026-11-10).** An inserter drops on the far lane of the belt in front of it; a belt that side-loads onto another fills only the lane on the side it comes from. One express lane is 22.5 per second.
  `fx.py mine` side-loads every drill column onto the collector from the same side, so the collector carries one lane (22.5/s, not 45/s). Fix on an existing outpost: every second feeder goes under the collector by underground belt
  and side-loads from the other side (done at Iron A and the west iron outpost; furnace rows went from about half to all working). Not yet fixed in `fx.py mine` itself, at Coal A or at the copper outposts.
- The y axis points south: smaller y is north, and a belt with direction 0 flows toward smaller y.
- `get_transport_line` only exists on belt-type entities; on a lab it raises "Entity is not transport-belt-connectable". Check `e.type` first.
- Requests of a chest can also be read as `c.get_logistic_point(defines.logistic_member_index.logistic_container).filters` (name, count).
- **Raw ore by drone:** `scripts/build_drone_mine.py --area X1 Y1 X2 Y2 --resource coal --out E --name "Coal A" [--chests 16] [--apply]` lays the `fx.py mine` pattern and ends the collector in a spur with a bulk inserter and a red chest
  on each side of every tile. The whole map is one robot network ("Nauvis Main"), so a requester chest anywhere can ask for the ore. Meant for cargo used raw (coal, stone). First use: Coal A at (-639,-340).
- **Labs fed lab to lab starve at the far end** when two packs share one entry inserter (automation and military through one fast inserter at (7.5,33.5)). A requester chest and bulk inserter straight into a lab at the far end
  of the chain fixes it without touching the chain (map tag "Lab Feed", group "Lab Feed: Science Packs": chests at y 53.5 and at (8.5,46.5) ask for six packs). The tile south of the first lab column is water.
  Result: 45 of 50 labs working, up from 6 to 14. An inserter feeding a lab that needs nothing shows status 36, which is not a fault.
- **Size a drone request for the flight time.** A request of 100 iron plates starved the circuit cells because the iron chests are about 500 tiles away; 600 fixed it. A slot changed in one chest of a group changes the whole group.
- **A mixed belt blocks when one cargo has no taker.** The chemical belt (y -62.5 and -63.5 at x -345) filled with plastic and engines, so advanced circuits could not get on. A filtered bulk inserter into a red chest at the end
  of each lane (map tag "Chemical Belt Plastic Overflow") lets the surplus leave by drone. It blocks again if those chests fill.
- **Space platforms** (first worked on 2026-11-10, platform 4 "Inner Planets Shuttle", surface `platform-3`, `scripts/build_shuttle.py`, watch a flight with `scripts/shuttle_watch.py`):
  - `game.forces.player.platforms[i]` gives name, `surface`, `hub`, `state`, `paused`, `speed`, `distance` (0 to 1 along `space_connection`), `space_location`, `schedule`, `weight`. A schedule is
    `{current=1, records={{station='fulgora', wait_conditions={{type='time', ticks=1800, compare_type='and'}}}, ...}}`; set it and `paused=false` to fly.
  - `place_entities` works with `surface="platform-3"`. `params` go to `create_entity`, so `{"quality":"legendary"}` places legendary. For a dry run that really checks tiles and collisions pass `clear_trees=False`.
    Placing over a ghost replaces the ghost.
  - **A platform has one global electric network** (`surface.has_global_electric_network`). Poles are not needed and nothing can be kept unpowered by leaving it outside a supply area.
    Adding solar panels powered the fuel inserters of the Captain's cold reactor and started it.
  - The four inner routes (Nauvis to Vulcanus, Gleba, Fulgora; Gleba to Fulgora) are 15000 long and carry only medium asteroids (400 hp, 89% laser resistance, 10% physical), so gun turrets, not lasers.
  - Chunks are scarce in orbit: the ammunition line made about 60 magazines while parked, and only fills up in flight.
  - **First test flight, Nauvis to Fulgora, 2026-11-10: arrived, but not flight-worthy.** With 6 of 13 turrets armed at departure and one ammunition line (two legendary furnaces, 0.78 magazines a second,
    the furnaces are the limit: a legendary crusher makes 25 ore a second, a furnace smelts 1.56) the turrets ran dry at 60% of the route; asteroids destroyed about 570 foundation tiles and 66 entities
    (all four collectors at one point), and the thrusters ran out of oxidizer so it crawled the last 40% at 10 km/s. `scripts/shuttle_repair.py` rebuilt the ghosts as they appeared (`ghost.revive()`,
    tile ghosts first, several passes). Fixes made after: the four underground belts on the fuel block's return line (x 36.5, y 1.5 to 7.5) pointed north into the belts feeding them, so returned chunks
    jammed the fuel crushers; rotated, they now run south to the overboard inserter at (36.5,8.5), and fuel and oxidizer refilled to about 10,000 each. Second ammunition line (`scripts/build_shuttle_ammo2.py`)
    north-west of the north collector belt. Two circuit-wired overboard inserters at (51.5,-6.5) and (51.5,-5.5) throw chunks into space only when their belt tile holds more than two of one kind.
  - **Return flight, Fulgora to Nauvis, same day: about 90 seconds at 210 km/s** with full tanks (135,000 each), 13 of 13 turrets armed and 507 magazines on the belts. Much better, still not clean:
    355 tiles and 23 entities destroyed and rebuilt by the repair loop, and it arrived with 6 of 13 turrets armed while 186 magazines sat on the belts, so the fault is now distribution
    (some turrets are not reached fast enough), not production. Next: find which turrets ran dry and feed them directly, and consider capping speed, since asteroids arrive faster at 210 km/s.
  - **Reactor water loop (the Captain, 2026-11-10: the shuttle melts ice and stores water for nuclear power; no solar conversion, no barrels).** A water line runs along row y=4 as three underground
    pipe pairs (x -5 to 5, 6 to 16, 17 to 21, under the oxidizer and fuel tanks and the belt at x=20) from the four water tanks (62,500 each) at (22.5,1.5..4.5) to the Captain's inlet stub at (-5.5,3.5)
    and the heat exchanger. Do NOT put a pipe on (23,4) or (24,4): that one carries thruster fuel. The thruster-oxidizer and thruster-fuel plants are red-wired to the water tank at (27.5,2.5) and run only
    while it reads more than 5,000 water, so the reactor's reserve fills first. Checked: the exchanger made steam and all five turbines ran on it. Not checked: a full reserve, since oxide chunks are
    rare in Nauvis orbit and the tanks were at zero. `entity.fluidbox` is gone in 2.1; use `get_fluid_contents()`, `fluids_count` and `get_fluid_segment_id(i)` (same id = same pipe network).
  - **Two measured legs, 2026-11-10 (`scripts/shuttle_trial.py --to <planet>` flies one leg, rebuilds damage and prints a row every 5 s plus a summary).** Nauvis to Fulgora: 71 s at 210 to 227 km/s,
    87 tiles and 6 entities rebuilt, 160 magazines made, water +1,780, fuel 40,974 and oxidizer 40,961 burned. Fulgora to Nauvis: 81 s, 698 tiles and 69 entities rebuilt, water +1,761, fuel 32,079
    and oxidizer 32,069 burned. Asteroids are heavy only in the half of the route near Fulgora; there the front row empties in about 20 s (about 10 magazines a second needed, 1.56 made).
    A leg burns the propellant of 8,500 to 11,000 water and collects under 2,000, so at full throttle the shuttle is neither safe nor self-sufficient on ice. Read in game: thruster effectivity is
    0.51 at full flow and 1.0 at minimum flow, so the fix is a speed cap: a circuit-controlled pump on each thruster feed line (the platform has no pumps; the feed pipes are the Captain's, ask first).
    Mistake to avoid: cutting ammo belt 1 at (8.5,-21.5) to hold stock at the front starved the three west turrets and caused the 698-tile leg. The stock sits downstream of the front row, so the west
    flank only refills after the front row is full. A belt at (4.5,-22.5) makes the turn at (4.5,-21.5) a side-load. Parked 20 minutes at Fulgora, water rose from 2,274 to 14,443.
    `entity.neighbours` is gone in 2.1: use `belt_neighbours` and `underground_belt_neighbour`. `entity.active` reads false on belts, pipes and poles; it means nothing there.
  - Before the next flight: every turret armed and the ammo belts full (they hold several hundred magazines); depart only then. Still open: more furnaces per assembler, physical damage research, the reactor loop.
  - An inserter whose drop tile is empty space throws the item overboard. `entity.rotate()` on one underground belt flips the pair. Wires: `a.get_wire_connector(defines.wire_connector_id.circuit_red, true).connect_to(b...)`.
  - An inserter's `direction` is the side it picks up from. `find_entity('inserter', pos)` missed a legendary inserter; use `find_entities_filtered{position=, type=}`. `get_recipe()` on a ghost only for `ghost_type=='assembling-machine'`.
  - `e.status` names: 29 no_input_fluid, 30 fluid_ingredient_shortage, 31 item_ingredient_shortage, 32 full_output, 36 waiting_for_source_items, 43 thrust_not_required, 57 no_ammo.

## Not built yet
When one of these gets built, move it to the tools table and note what was tested.
- **More train lines**: only coal line 1 exists. Next: iron, copper and stone outposts and the `10 patches each` target (the generated map has fewer; chunks must be generated outward first). Needs: a generic outpost generator, signals once two trains share track, a real hub (belts into the existing smelters, or new smelters), and a second coal source before patch 1 runs dry.
- Chemical science (the tech is done; the packs need sulfur, so water for the refinery site) and everything planet-side.
- Sulfur and anything needing water: no water near the refinery; pipe from the south lake or move the complex.
- General outpost layouts. The first mines use one-off rows, so power poles and electric drills are still to come.
- Connecting to existing base lines, plus defense. Pollution from these drills will reach biters eventually.
- Blueprint-string import.
- Research driver: what's blocking the next tech, then build it.
- Other planets: nothing built on Fulgora, Vulcanus or Gleba. Surfaces need a real arrival first (not yet tested). The shuttle carries no cargo yet and its reactor loop has no water.
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
