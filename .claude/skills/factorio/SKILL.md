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
  - **Platform 4 was lost on 2026-11-10** (flown with unarmed turrets after a foundation trim; ship and cargo gone, no restore). Rules since: `shuttle_trial.py` refuses to launch unless every turret
    holds 8+ magazines, the hub stock, water, propellant and reactor temperature pass, and it saves `before-flight-p<N>` first. Never fly an untested change; test parked.
  - **Second design, three ships (2026-11-10): platform 5 "Fulgora Shuttle" (`platform-3`), 6 "Gleba Shuttle" (`platform-4`), 7 "Vulcanus Shuttle" (`platform-5`).** Create with
    `force.create_space_platform{name=,planet='nauvis',starter_pack='space-platform-starter-pack'}` then `p.apply_starter_pack()`; build with `scripts/build_shuttle2.py --surface <s> --apply`
    (281 entities, 1040 tiles), then `scripts/configure_shuttle2.py --surface <s> --platform <i>` BEFORE stocking the hub, `scripts/shuttle2_status.py` for a readout,
    `scripts/shuttle2_wait.py` to log refill rates. Layout and coordinates are in the build script's comments. Everything hangs off the hub's 32 perimeter tiles; no shared belt loop.
    Rare quality: `force.is_quality_unlocked` says epic and legendary are NOT researched (the old shuttle's legendary machines slipped past the gate; `place_entities` does not check quality).
  - Facts found building it: inserters cannot use cargo bays (only the hub). The hub has 59 slots and an asteroid chunk does not stack, so hub limits are tiny (3 chunks a kind).
    A collector needs foundation under its back two rows and empty space on its front row and three rows ahead. Thrusters cannot touch each other; a two-tile gap carries one fluid to both neighbours.
    Thruster ports: fuel west-top and east-middle, oxidizer east-top and west-middle. Chemical plant: inputs on the side it faces, outputs opposite. Hub: `get_or_create_control_behavior().read_contents=true`.
    Reactor: `read_temperature=true`, `temperature_signal`; the fuel inserter runs below 600 C. A furnace input from the hub must be filtered to ore or it smelts the hub's plates into steel.
    **`place_entities` stacks a second copy on an identical entity on a platform** (not belts), and the stacked pipes then stop connecting even after the copies are destroyed: the build script now
    skips what stands; if it happens, destroy everything but the hub and rebuild. Reactor needs water and water needs power: four solar panels start the ship cold.
  - Start-up stock moved from the Nauvis logistic network (factory-made): 200 uranium fuel cells and iron plates for the first magazines per ship. Ice cannot enter (the melter is fed by the crusher only).
  - **Refill parked at Nauvis (measured 2026-11-10):** three collectors on the north-west corner gave about 200 water a minute per ship (2 oxide chunks a minute; Nauvis spawns metallic 0.0125,
    carbonic 0.0083, oxide 0.0042). Three more on the north-east corner (belt west along y=-12, under the ammunition belt and the heat exchanger, into the head of the chunk belt; 281 entities,
    1040 tiles) doubled it to about 400 a minute. The reserve wire reads one of the two water tanks, so the plants start at 10,000 water in all, then take every drop: about 1,400 fuel and
    1,400 oxidizer a minute while water sits at 10,000, and water only climbs again once the propellant tanks are full. So the launch guard asks for 15,000 water, not 40,000.
    Magazines from the ship's own ore: about 29 a minute. Oxide is scarcer at the other planets (0.0004 to 0.0006 chunks, plus medium asteroids the turrets break up).
  - **Round trips flown 2026-11-10, all three ships, full thrust:** Nauvis to Fulgora, Gleba and Vulcanus and back, each leg about 60 s at 250 to 300 km/s. Outbound burns about 30,500 fuel
    and 31,100 oxidizer, the return about 19,500 each, so one fill (80,000 each, about 1 h parked at Nauvis) covers a round trip with 30,000 left. Water rose in flight (22,500 to 24,000),
    a round trip costs about 500 magazines net (hub 2,000 to about 1,480; refill about 29 a minute parked). Damage over six legs: 29 tiles and 4 entities on ship 1 (one turret lost and rebuilt on its return), 1 tile on ship 2,
    none on ship 3; `shuttle_trial.py` revives the ghosts (free rebuild, friendly build mode). The thresholds in the guard (15,000 water, 40,000 propellant, 1,500 magazines) cover one leg.
  - **Standing schedules since 2026-11-10 (`configure_shuttle2.py --surface S --platform N --route <planet> --go`):** ship 5 Nauvis and Fulgora, 6 Gleba, 7 Vulcanus, looping unattended, no cargo.
    The hub's green wire also reaches one water, one fuel and one oxidizer tank, so schedule conditions (type `circuit`, read on the hub) see HALF the ship's totals. Nauvis is where the fill
    happens (oxide chunks are 7 to 10 times more common there): the ship waits for fuel and oxidizer 35,000 each (70,000 total, a round trip burns about 50,000), water 7,500, magazines 1,500.
    The far stop is only a floor for the flight home (15,000, 5,000, 800); with a Nauvis fill it is already met, so the ship turns round at once. Verified: all three flew out and back and
    now wait at Nauvis. Flight damage is rebuilt by the autopilot's `SHIPS` step each cycle (every platform named `...Shuttle`); `shuttle2_watch.py` does the same and prints a row per ship.
    Without the autopilot running nothing rebuilds a lost turret. Not changed: hull and thrust (a thruster throttle would save fuel but slow the legs; untested).
  - **Solar since 2026-11-10 (the Captain's order, reversing the nuclear rule above).** `scripts/shuttle2_denuclear.py` (ship parked and paused) took off reactor, exchanger, turbine, the two
    cell inserters and the water riser; `build_shuttle2.py --apply` then added the rest: 15 rare panels (one in the nose, 14 in two columns per flank, no extra width), 6 rare accumulators
    (15 MJ each, 90 MJ), and four more nose turrets (11 in all; the two nose turrets had twice the kills of any other). 278 entities, 1136 tiles. Sunlight in orbit: Vulcanus 600%,
    Nauvis 300, Gleba 200, Fulgora 120, Aquilo 60; a rare panel is 96 kW at 100%. Measured: at Nauvis 40 MJ of charge in 30 s while refilling; held three minutes at Fulgora making
    propellant the accumulators stayed between 85 and 90 MJ, no machine short of power; Gleba and Vulcanus round trips flown on solar with no damage. The water reserve gate is now 500 and
    the schedule has no water condition. Legendary panels were asked for but `epic-quality` (needs agricultural science) and `legendary-quality` (needs cryogenic) are not researched: rare
    is the best allowed; upgrade when they are. About 193 uranium fuel cells sit unused in each hub.
  - **Mistake to avoid:** a test schedule with only time waits loops. Ship 5 left Nauvis a second time with 22,000 fuel; turned back in time by setting the real schedule. For a one-off
    hold use a single far record or pause on arrival.
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
- Other planets: nothing built on Fulgora, Vulcanus or Gleba. Surfaces need a real arrival first (not yet tested). The three shuttles carry no cargo yet (no cargo bays; the hub is full of the ship's own stock) and have no speed cap on the thrusters (effectivity 0.51 at full flow).
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

## Quality: upgrade everything when a level is researched (the Captain, 2026-11-10)
- Standing order: no grinding for quality. When a quality level is researched, run `scripts/upgrade_quality.py --items --apply` (dry run without `--apply`): every entity of ours on every
  surface goes to the best researched quality in place (`order_upgrade` + `apply_upgrade` keeps recipe, contents, wires, heat, schedules), modules and robots resting in roboports are swapped.
- Not upgraded: robots in flight (run again later), platform hubs, the crash-landed ship; rails sometimes refuse on the first pass (run again). An upgraded accumulator starts empty unless its
  energy is carried over (the script does). Use the entity after `apply_upgrade` returns, the old reference is invalid.
- Substations have no power drain (looked up: `prototypes.entity.substation` has none). Rare substation: 22x22 supply, 22 wire reach, so a lattice of pitch 20 covers everything.

## Planets: landing and base preparation (first done 2026-11-10 on Fulgora, Gleba, Vulcanus)
- Landing: `scripts/planet_landing.py` drops one cargo pod (50 of the ship's own iron ore) from a shuttle's hub when it is in orbit: `hub.create_cargo_pod()`, fill
  `pod.get_inventory(defines.inventory.cargo_unit)`, set `pod.cargo_pod_destination={type=defines.cargo_destination.surface,surface=...}`. The surface is generated by that arrival.
- A shuttle whose "away" wait conditions are already true leaves the planet in the same second, too fast for a 10 s poll. The planet records now also carry a 60 s time condition.
  Pipe the watcher through `grep --line-buffered` or its output only appears when it exits.
- `scripts/planet_base.py STEP --surface NAME [--centre X Y] [--radius 128] [--apply]`, steps in this order: `generate` (chunks, chart, peaceful), `survey`, `clear` (keeps resources, plants such as
  yumako trees and jellystems, stromatolites, lightning attractors, the Fulgoran vault), `power` (rare substations, pitch 20), `drones` (rare roboports, pitch 48), `sites` (refined concrete pads at
  resource patches plus 6-wide paths from the centre; liquids, ore and Gleba's farm soils are left), then `solar --cells N` (24 panels + 27 accumulators inside a free lattice cell) or `rods`
  (Fulgora: a lightning rod and four accumulators at every substation). Every step is a dry run without `--apply` and safe to repeat.
- Land test for tiles: `not tile.collides_with('water_tile')` (oil ocean, lava and wetlands all carry `water_tile`; the `player` layer does not catch shallow oil ocean).
- Solar by surface (looked up): Fulgora 20%, Gleba 50%, Vulcanus 400%. Foundation (Aquilo research) is not available, so liquid tiles stay liquid; Fulgora's islands are separate electric networks.
- The planet roboports each got 10 construction robots moved out of Nauvis roboports (factory-made items, moved not spawned).
- Planet trigger techs (looked up 2026-11-10, `technology.prototype.research_trigger`): agriculture = mine an iron stromatolite, heating-tower = a copper stromatolite, recycling = the Fulgoran vault,
  tungsten-carbide = a big/huge volcanic rock, calcite-processing = calcite, yumako = a yumako tree, jellynut = a jellystem. Mining by construction robot counts: `entity.order_deconstruction(force)`
  inside a roboport's construction range (a yellow storage chest as trash yard must exist for the spoils), calcite by an electric mining drill. All but jellynut are earned (no jellystem charted yet).
  Next triggers: foundry = craft tungsten carbide, holmium-processing = craft holmium ore (recycle scrap).
- `queue_research` once reported "queued" while the queue stayed empty; check `force.research_queue` afterwards and use `force.add_research(name)` if so.

## First production on the planets (2026-11-10)
- `foundry` and `holmium-processing` are earned. Only `jellynut` is left of the planet trigger techs (no jellystem charted on Gleba yet).
- Fulgora: drill (17.5,-106.5) drops scrap straight into the recycler (18,-110), which drops into a red chest (17.5,-112.5).
- Vulcanus, at (0,109): pumpjack on the acid geyser, chemical plant (carbon), assembling machine 3 (tungsten carbide), blue chests for coal and tungsten ore, red chest for the carbide. Coal comes by robot from a drill and red chest at (-66.5,-100.5). 20 logistic robots moved from Nauvis. Tungsten ore has no source yet (big mining drill not researched); the 5 ore found in the trash yard made 2 carbide.
- An inserter's `direction` is the side it picks up from, not the side it drops to. Read `drop_target` back after placing (it is nil until the next tick).
- Pipe connection positions from the prototype are for direction north; rotate them with the entity. The pipe goes one tile beyond the connection position.
- Requests on a requester chest: `chest.get_logistic_sections().add_section().set_slot(1,{value={name=..,quality='normal'},min=n})`.

## Labs idle with an empty queue (2026-11-10)
- Cause was the autopilot's own TOPUP step, not the labs: it counted trigger techs (big-mining-drill, electromagnetic-plant) as queueable, and writing them to `research_queue` emptied the queue every cycle. TOPUP now skips techs with `prototype.research_trigger` and leaves the queue alone when it has nothing finite to add, so hand-queued infinite techs stay.
- The four lab requester chests had no production science request; added 100 each. The belt-fed lab group (belts near (5,31)..(8,34)) still carries no production packs: 19 of 50 labs miss them.
- Production science is not being made: four assemblers at (-51.5,-181..-172) sit on full output, two at (99.5,-60.5) lack electric furnaces. Research runs on a stock of about 12,000.

## Fulgora science, stage 1 (2026-11-10)
- Goal (the Captain): electromagnetic science at Nauvis' rate, delivered to the Nauvis science centre; first cell 2 packs/s. Stages: 1 triggers (done), 2 scrap block, 3 science cell, 4 silo and shipping, 5 power.
- `electromagnetic-plant` and `electromagnetic-science-pack` are earned. Ten techs now wait on electromagnetic packs (scrap-recycling-productivity, lightning-collector, ...).
- Plate line at (9,-103): ice melter, holmium solution, assembler 3 for plates, machines touching so fluids pass without pipes. Its ore request is cleared.
- Supercapacitor line at (24..42,-124..-99): offshore pump (30.5,-123.5) gives heavy oil from the ocean (deep ocean works too), cracker, second recycler (40,-114) turning advanced circuits and low density structures into circuits, plastic and copper plate, three electromagnetic plants. All fed by robots; 20 logistic robots moved from Nauvis. The superconductor request is cleared (128 in the red chest at (27.5,-113.5)).
- Sizing for 2 packs/s without modules: 22 electromagnetic plants, 1 foundry, 10 chemical plants for solution, 125-185 scrap/s (50-75 recyclers, 90-135 electric drills), about 75 MW. Charted scrap (1,143 tiles, 30.8M) fits about 127 drills: chart more islands.
- Roboport logistic reach is 25 tiles; a chest at 25.5 gets nothing though robots still build there. Added a roboport at (40,-106).
- Electromagnetic plant pipe spots (facing north, plant centre on a whole number): input 1 west (-2.5,+0.5), input 2 east (+2.5,-0.5), output 1 south (+0.5,+2.5), output 2 north (-0.5,-2.5). Fluid ingredients take the inputs in recipe order.
- `pipe-to-ground` direction is the side of its above-ground opening. Use a pair to pass a machine's unused fluid connection.
- Recycling results list `amount` 0 with `extra_count_fraction`; scrap-recycling odds are not readable from the prototype, measure them from the chest.
- The Claude session restarts drop the background autopilot and watchdog; restart both.

## Nauvis science centre: compact lab block (2026-11-10)
- `scripts/lab_block.py` (teardown, place, fill) replaced the two sparse 50-lab fields with 48 rare labs at x -73..-6, y 32..52: beacon row, lab row, repeated; 16 labs per row, a blue chest and bulk inserter at each end, bulk inserters between labs passing packs toward the middle. 67 beacons with 2 speed module 2, labs with 2 productivity modules (taken from network stock, then raised to rare by upgrade_quality.py). Pack use went from 168 to 492 a minute on the same research; lab speed bonus 11-20, productivity +12.8%.
- The bottom beacon row is half empty: an underground pipe run and a row of substations along y 52-53 (not mine, left alone).
- The four belts that ended in a lab at (5.5,34.5) now end in red chests at (4.5..6.5,33.5) and (6.5,34.5); robots carry from there.
- Blue chests request 100 of each of the 12 lab inputs, so planet packs flow in as soon as they exist.
- A new requester chest already has one empty section: use `sections[1] or add_section()`; testing `#sections==0` sets nothing.
- place_entities dry runs fail at random spots while robots fly over; rerun or just place.
- Production science: the four assemblers at (-51.5,-181..-172) stop on purpose when their red chests hit the 8-slot limit (1,600 each). Not a fault.
- South edge moved with the Captain's leave (2026-11-10): the water main that ran underground along y 52.5 now runs along y 56.5 from a new shore pump at (-13.5,56.5), rejoining the old main at (-76.5,52.5); the nine substations that sat at y 53 are at y 54 (the east four at x -4,-2,0,2). The bottom beacon row has 21 of 22 beacons: the west slot carries the pipe up to the main. 77 beacons in all.
- BUG in `place_entities`: placing an entity where the same entity already stands reports "placed" and stacks a second one on top (10 beacons doubled). Never re-send a list that includes things already built; check for duplicates by position afterwards.
- Fixed 2026-11-10: `place_entities` now fails with "already occupied by <name>" when the same entity, or one it could fast-replace, already stands there (dry run and real). Dry runs also ignore flying robots. The Lua inside god_tools.py is sent as one line: no `--` comments in it. The running MCP server keeps the old code until Claude restarts; scripts through `_game.tools` use the fix at once.

## Fulgora stage 2: scrap block and island survey (2026-11-10)
- Fulgora charted to x -384..575, y -384..575. Two kinds of scrap: big islands hold wide but nearly empty patches (0.2-1.1M); small islands hold the rich ones. Rich: home (22,-95) 29.8M; (-195,327) 34.5M; (-200,-367) 24.8M; (534,316) 21.5M; (513,498) 18.0M; (-199,196) 17.7M; (197,363) 16.8M; (499,-351) 10.8M; (391,-376) 10.3M. Poor: (148,515) 1.1M, (169,-5) 0.4M, (158,66) 0.3M, (32,92) 0.2M.
- The home island is only about 3,000 tiles. Nothing but rails crosses the oil ocean: elevated rails ARE researched (rail-ramp, rail-support); supports stand on shallow ocean (tiles oil-ocean-shallow and oil-ocean-shallow-2), not on oil-ocean-deep. Roboports link only within 50 tiles. Test land with `collides_with('water_tile')`, never by tile name.
- `scripts/fulgora_scrap.py`: drill drops scrap straight into a recycler, recycler drops onto a belt; no inserters. 14 units at x 12..45, drills back to back on rows -93..-88, belts on y -97.5 and -82.5 flowing west and ending at x 12.5 (nothing takes the items yet, so the belts back up and the drills idle until stage 3). 3 speed module 2 per drill, moved from Nauvis stock.
- Measured while the belts filled: 3,163 scrap/min (52.7/s) and 50 holmium ore/min (0.83/s), about 1.6% of scrap. 2 packs/s needs about 1.9 ore/s without productivity modules, about 1.1 with them.
- Recycler facing north takes input at its south end and drops at (x-0.35, y-2.3); facing south is the mirror. Drill centre is half a tile west of a north-facing recycler's centre.
- Scrap under the recyclers and belts (rows -97..-94 and -87..-83) and items left on the ground at x 19 are not mined; two units were skipped there.

## Infinite scrap (the Captain's order, 2026-11-11)
- All 4,387 charted scrap tiles on Fulgora are set to 4,294,967,295 (`e.amount`, the largest value). This is the Captain's explicit exception to "inputs are never spawned", for scrap only.
- The prototype is not infinite: scrap in chunks generated later has its natural amount. Set it the same way when it is to be mined, and tell the Captain.
- Consequence for planning: patch richness no longer matters, only tile count and island size. The wide patches on the big islands ((148,515) 829 tiles, (169,-5) 459 tiles, (158,66) 214 tiles) are now the best mining sites, with room to build beside them.

## Fulgora main base plan and elevated rail (the Captain's order, 2026-11-11)
- Order: main base in an open area with no scrap; scrap is brought there by elevated rail, recycled and sorted by robots; all other manufacturing at the base.
- Base site chosen: north-west lobe of the big island, about x 118..150, y -106..-36 (clean land, no scrap), with more open land east at x 196..256. Scrap lumps on the same island: (152..184,-56..-24), (164..188,-4..24), (124..140,-12..8), (144..168,48..76).
- Built and tested: one straight line along y -105. Ground rails x 7..43 on the home island (stop `Scrap Home Load` at (7,-107)), ramp at (52,-105), elevated rails x 61..115 over shallow ocean on supports at x 64,76,84,96,104, ramp at (124,-105), ground rails x 133..171 on the big island (stop `Scrap Base Unload` at (171,-103)). Train group `Scrap Home`: locomotive, 3 cargo wagons, locomotive, solid fuel from scrap. A round trip takes about 15 s of travel. The train is parked in manual mode until the stations can load and unload.
- Rail facts learned: rails sit on odd coordinates; `straight-rail` and `elevated-straight-rail` direction 4 = east-west. `rail-ramp` is 16 long, centre 9 from the last rail on either side; direction 4 = low end west, direction 12 = low end east. A `rail-support` (direction 4) carries elevated rails from about 3 tiles west to 9 tiles east of itself, so space supports 8-12 apart; ramps carry the first rail beside them. Supports stand on shallow ocean, not deep. `can_place_entity` says false for an elevated rail with no support in reach. Check a line with `get_connected_rail{rail_direction=, rail_connection_direction=straight}`.
- A single straight track with one double-headed train needs no curves and no signals. Stop goes on the right of the arriving train: north side for a train heading west, south side heading east.
- Stage-1 lines on the home island were removed; their contents are in two steel chests at (8.5,-118.5) and (9.5,-118.5) (108 items did not fit and were lost). The 14-unit drill and recycler block still stands and still recycles on site; it is to be converted to send raw scrap by train.

## Fulgora solved, part 1: mine, train, robot base, science cell (2026-11-11, order "Proceed to solve Fulgora")
- Scripts: `scripts/fulgora_home.py` (teardown, build, modules, train) and `scripts/fulgora_base.py` (unload, recyclers, yard, ports, robots N, cell, modules). Saves: before-fulgora-home-rebuild, fulgora-base-sorting, fulgora-science-first-packs.
- Home island (22,-95): 37 electric drills (3 speed module 2 each) in four belt columns at x 13, 20, 27, 34 (rows -100..-84, substation and rods in the gap rows -94/-93). Each belt turns west along row -101 under one wagon: belt -> bulk inserter -> steel chest -> bulk inserter -> wagon. Stop `Scrap Home Load` (1,-107). Medium poles in the gaps at x 7,14,21,28,35 (the substations do not reach the wagon inserters).
- Train `Scrap Home`: locomotive, 4 wagons, locomotive; waits full or 10 s idle at Load, empty or 10 s idle at Unload. Carriages stop on whole x: front locomotive centre = stop x + 3 (west stop) or stop x - 3 (east stop), 7 apart; a wagon centred on c is reached from tiles c-3..c+2.
- Base on the big island, open land x 116..200, y -164..-88. Stop `Scrap Base Unload` (179,-103); wagons at x 148,155,162,169. North of the track: bulk inserters row -107 into red chests row -108.
- Recycler row: 34 recyclers centred y -113, x 126..192 step 2; blue chest (scrap 100) row -110, inserter row -111, purple chest row -116. Trash yard: 19 recyclers centred y -99 between the lattice clusters, yellow chest row -96, purple chest row -102. 600 logistic robots moved from Nauvis; 15 roboports.
- Science cell, x 105..200, y -162..-129, all items by robot, fluids by pipe. Heavy oil pump (105.5,-151.5) facing west; trunk along y -155.5. Light unit at x 108..114: ice melter (112.5,-160.5), water under the trunk by underground pipe, cracker (112.5,-150.5), superconductor plant (112,-146). Row A y -153: 4 electrolyte plants at x 122+6k. Row B y -146: 5 science pack plants then 3 supercapacitor plants at x 122+6k. Mains: solution y -150.5 and y -143.5 (joined at x 117.5), electrolyte y -148.5, solution from the chem row y -130.5 (joined at x 116.5), water y -134.5. Chem row y -132.5: 5 solution plants at x 124.5+5k, ice melter (134.5,-136.5), 2 plate assemblers (149.5 and 154.5, facing south), then 5 accumulator assemblers and 1 circuit assembler at x 160.5+7k.
- Electromagnetic plant facing east (direction 4): input 1 north at (x-0.5,y-2.5), input 2 south at (x+0.5,y+2.5), output 1 west at (x-2.5,y+0.5). A row of east-facing plants 6 apart taps a straight main on each side; the west output goes plain pipe, then an underground pair under the south main.
- LESSON: `place_entities` (create_entity) drops the direction of a crafting machine that has no fluid recipe yet, so every plant came out facing north and the mains touched the wrong ports: nothing flowed and nothing warned. After placing, set `e.direction` again once the recipe is set, read it back, and flush pipes with `clear_fluid_inside()`.
- Lattice clusters (substation + rod + 4 accumulators every 20 tiles) leave free bands 13 rows high between them; lay machine rows in those bands. `planet_base.py drones` can drop a roboport inside a planned row (one at (144,-144) was removed).

## Fulgora solved, part 2: silo, delivery, power, tuning (2026-11-11)
- DELIVERED: the first 1,000 electromagnetic science packs went Fulgora silo -> Fulgora Shuttle (platform 5) -> Nauvis landing pad -> lab chests -> labs. Autopilot TOPUP now counts the electromagnetic pack, so it queues those techs (lightning-collector first). Save: fulgora-science-delivered.
- Silo at (150.5,-170.5), 4 productivity modules, `use_transitional_requests=true` (answers platform requests; robots load the cargo). Three blue chests north of it ask for 50 processing units, 50 low density structures, 50 rocket fuel. Rocket fuel unit on the west shore at x 108..114, y -144..-132: own pump (108.5,-139.5), ice melter, cracker, assembler.
- Platform 5 hub section: electromagnetic-science-pack min 4400 `import_from='fulgora'`; its Fulgora schedule record has an extra circuit condition on the pack count (the first trip left with 1,000 when the constant was 2,000, so the hub signal seems to count double). Nauvis landing pad (-216,-228) requests 20,000 packs; platforms in orbit drop to it.
- Power, measured: lightning falls from about 0.27 to 0.73 of the day (81 s of 180 s); nothing for 99 s. Base load about 72 MW (electromagnetic plants 33, roboports 23 for robot charging, recyclers 8.5). With 152 accumulators the base blacked out 65 s every day. Now: about 700 rare accumulators on the base network (10,290+ MJ; fields in the north band y -175..-165 and the east land x 205..255, y -35..-5) and 87 on the home island (1,305 MJ); rods extended over the east and south of the island (63 rods). Lowest charge over two days: base 2,872 MJ, home 157 MJ.
- A productivity module adds 40% power draw to a 2 MW plant. They are kept only in the 5 science pack plants, the chemistry and the silo; the other 8 plants gave theirs back to Nauvis.
- Read electric use by entity by sampling `electric_network_statistics.input_counts` twice and dividing by the time; `get_flow_count` returned 0 for it.
- Train: full OR 15 s at Load, empty OR 15 s at Unload (some belts deliver far less than others; waiting for a full train starved the base). Rare wagons hold 3,000 scrap. Solid fuel feeders (blue chest + inserter) at the base stop under both locomotives, x 140.5 and 175.5.
- Trash yard: a recycler takes 1 s per steel plate, 0.94 s per low density structure, 0.63 s per processing unit, 0.38 s per advanced circuit; these slow items set its size. 34 yard recyclers now (19 south of the track, 15 at y -153, x 170..198). Robots fill storage chests one at a time, so some yard recyclers idle while others are full.
- Red stock chests for supercapacitors, plates, superconductors and accumulators are capped at 3-4 slots (`set_bar`), otherwise intermediates hoard the holmium and the pack plants starve for solution.
- Measured rates: 136 scrap/s through 34 recyclers; holmium ore is 1.0% of scrap (81/min), batteries 4% (329/min). Batteries cap output near 1.8 packs/s; holmium allows about 2.2.
- State at hand-over (save fulgora-solved-v1): 116 packs/min made over the last 10 minutes while accumulator stock ran down; batteries (326/min) support about 89 packs/min (1.5/s) sustained. To reach 2/s: a third more scrap (drills, train, recyclers) or batteries made from oil. 1,068 logistic robots on the base (568 were all busy). Yard storage 828 of 1,444 slots before the 15 extra recyclers took effect: watch it. The shuttle was refuelling at Nauvis (53k of 70k fuel) with 1,650 packs and a ready rocket waiting on Fulgora; the second delivery is not yet verified.

## Fulgora: stable trash yard and ice for the shuttle (the Captain, 2026-11-11)
- The Captain's rule: getting rid of what is not needed is part of each planet's puzzle; recyclers are the tool. A yard is only "done" when its stock falls or holds over time: measure it twice, minutes apart.
- Dedicated void units (the 15 recyclers at y -153, x 170..198): blue chest requesting 400 of one item, and the inserter joined to the logistic network (`get_or_create_control_behavior()`, `connect_to_logistic_network=true`, `logistic_condition` item > level) so it only runs above a stock level and never starves the science machines. Steel plate x7 (>300), advanced circuit x3 (>300), copper plate x2 (>1000), iron plate x2 (>2000), electronic circuit x1 (>3000). The 19 generic yellow-chest recyclers south of the track take everything else. After the change yard stock fell from 888 to 674 slots in 8 minutes.
- Fulgora Shuttle (platform 5, surface `platform-3`): its fuel makers only run when a water tank reads over 500, and water was the limit. Added a second ice melter at (6.5,6.5) fed from the hub: filtered bulk inserter (3.5,4.5) -> one belt tile (3.5,5.5) -> bulk inserter (4.5,5.5) -> melter, whose output touches the water tank's north-west port. Chests cannot be placed on a platform; a single belt tile is the relay. Hub request: ice 300 from Fulgora with `minimum_delivery_count=300`; packs 4000.
- An inserter placed without its filter grabs whatever the hub holds first (it jammed on magazines): set the filter in the same call that places it.
- The Nauvis landing pad also requests 50 ice and 50 carbon, so a platform in Nauvis orbit drops those to the ground. Not mine; left alone.
- Verified second delivery: the shuttle left Fulgora with 2,400 packs (the pack condition counts double, so a constant of 4000 means 2,000 real) and Nauvis used them in about 4 minutes: the lab block can burn about 600 packs a minute, Fulgora makes about 126.

## Nauvis landing pad: ice and carbon requests are the Captain's (2026-11-11)
The pad's request for 50 carbon is deliberate: it takes the White Science platform's surplus down to the surface instead of trashing it. Leave it. The ice request was removed on the Captain's order (White Science has no spare ice, so it only drained the Fulgora Shuttle).
The Captain wants shuttles never to export carbon. 2.1.24 has no per-item export switch: the only control is `LuaSchedule.set_allow_unloading` for a whole stop, which would also stop the packs. On 2026-11-11 the three shuttles held no carbon in hub or belts, so none can leave. If a shuttle ever stocks carbon in its hub, raise it again.
Hub and pad slots also take `request_from` = 'planet' (default), 'platforms' or 'all'.
Platform-to-platform test, 2026-11-11: Fulgora Shuttle hub slot carbon 200 with `request_from='platforms'`, parked at Nauvis beside White Science (7,257 carbon in hub) for about 2.5 minutes: nothing moved, no carbon pod, and the shuttle left on schedule. The setting exists but one request alone does not move items; what else it needs (a setting on the giving side, a research, a hub upgrade) is unknown. Test request removed.

## Research queue holds 7 (2026-11-11)
Writing more than 7 techs to `force.research_queue` fails, and the autopilot's pcall hid it: research sat idle for over an hour with 12,484 electromagnetic packs on the Nauvis pad. TOPUP now caps the list at 7. When asked "is it working", check `current_research` and lab status first.
Fulgora check the same day: 103 packs/min over an hour (1.7/s, target 2), limited by batteries (network short); ice stock down to 57 with the shuttle's 300-ice request competing with the cell's melters.

## Fulgora at 2 packs/s (2026-11-11, save fulgora-two-per-second)
- The limit was accumulator assemblers (5 at 60/min exactly), then batteries. Now 8 assemblers (new at (202.5,-132.5), (160.5,-125.5), (195.5,-125.5)); 5 rare productivity modules in each of the 3 supercapacitor plants. The accumulator recipe takes no productivity modules: `inv.insert` returns 0, so count what insert returns, never assume.
- Batteries (4% of scrap) are the hard cap: about 3.05 per pack, so packs/min = batteries/min / 3.05. Each level of scrap-recycling-productivity adds 10% of everything from scrap; it is queued first.
- Ice: the yard was voiding it (about 380/min; melters need under 30). Generic yard inserters now blacklist ice (`use_filters`, `inserter_filter_mode='blacklist'`); an ice void unit at (200,-153) runs only above 3,000 in the network, so 3,000 is the standing reserve.
- The yard was filling by about 300 slots an hour. Second row of 18 generic recyclers at top y -93 (x 136..144, 156, 162, 164, 174..186, 194..198), 800 more robots (1,868). Measured falling afterwards. Check the yard over hours, not minutes.
- Power: the added load caused a 10 s blackout at the end of each dry spell. 220 more rare accumulators at x 203..237, y -71..-45 (substations (211,-51), (229,-51), (211,-65), (225,-63)); base now 13,035 MJ, daily minimum about 1,770. Thin: add storage before adding load.
- Autopilot: now queues repeatable research after finite research (it used to skip it, which left the labs idle once finite research ran out). After editing TOPUP, run it once and read the queue it prints.

## Fulgora storage: intake gate and useful sinks (2026-11-11, save fulgora-intake-gate-foundations)
- The Captain's idea: turn the miners off when nothing is needed. Done by backpressure, no script: the 24 unload inserters at `Scrap Base Unload` (y -106.5) are wired to the logistic network and run only while electromagnetic packs < 6,000; the train's wait at the base is now "empty" only (no 15 s timeout), so it parks full; home chests and belts fill and the drills stop. Verified: 30 of 37 drills stopped, main recyclers idle, yard fell 1,477 to 1,059 slots in 9 minutes.
- With intake running the yard was level (1,552 to 1,566 slots over 1.5 game hours) with 16 of 37 generic recyclers idle.
- Captain's order: turn what is voided into things we consume before voiding it. First sink: two assemblers at (181.5,-125.5) and (202.5,-125.5) make space platform foundation from surplus steel and copper cable (request 200 each, output chest barred at 10 stacks = 1,000 each). Nothing ships them yet.
- Not done: advanced circuits, processing units and low density structures are also voided and could go to Nauvis, whose chemical science has stopped.
- The Captain does not want the quality game: quality comes only from upgrading everything when a level is researched.

## Nauvis chemical science fed from the network (2026-11-11, save chem-science-fed)
- The 8 chemical science assemblers (y -66.5, x -344.5..-316.5) take sulfur, engines and advanced circuits from belts y -63.5 and -62.5. The advanced circuit lane was empty because the local circuit makers at y -59.5 are short of copper cable and iron, while the network held 451,000 advanced circuits. Added a requester chest (-312.5,-65.5, 400 advanced circuits) and a bulk inserter (-312.5,-64.5) onto the south lane. All 8 working again. The starved local circuit makers are the Captain's and were left alone.
- Nauvis stock on that day: advanced circuits 451k, processing units 91k, low density structure 62k, steel 126k, platform foundation 84k, copper and iron plate 450k+ each, holmium plate 0, batteries 1,800. So Fulgora's surplus has no use on Nauvis except holmium and batteries, which Fulgora itself is short of. Nothing is shipped.
- Rocket capacity: advanced circuit 1000, plates 1000, plastic 2000, steel 400, battery 400, processing unit 300, low density structure 200, platform foundation 50.

## Vulcanus survey (2026-11-11), before building the science base
- Charted to +-640. Base lattice (substations, roboports, solar, accumulators) covers x -125..121, y -120..120; only the small tungsten carbide trigger unit works there (pumpjack (-3.5,103.5), carbon plant, carbide assembler (0.5,109.5)).
- Research chain still to earn, all craft triggers: big-mining-drill (craft a foundry: 50 steel, 30 electronic circuit, 50 tungsten carbide, 20 refined concrete, 20 lubricant) -> tungsten-steel (craft a big mining drill) -> tungsten plate recipe -> metallurgic-science-pack (craft a tungsten plate). Pack: 3 tungsten carbide, 2 tungsten plate, 200 molten copper, 10 s.
- Resources: lava nearest at (53,0); calcite 757k at (-144,112); coal 464k at (-49,-80) and neighbours; sulfuric acid geysers around (-11,111); tungsten ore 10.4M in the charted map, nearest patch 364k at x 203..250, y 26..76.
- Every bit of that near tungsten patch is inside demolisher territory 4 (a small demolisher; territory starts at about x 200 on y 50). `surface.get_territories()`, `territory.get_chunks()`, `territory.get_segmented_units()`. Peaceful mode is on but that is not known to stop a demolisher attacking buildings in its territory. Waiting for the Captain's decision before building there.

## Read the game's alerts first (Captain's order, 2026-11-11)
When scanning any planet for problems or bottlenecks, always read the alert overview the player sees. `factory_problems` now returns `alerts` (type, count, what, sample positions), `damaged_entities` and `ghosts` for the surface; the running MCP server only picks this up after an app restart, so until then call it through `_game.tools["factory_problems"]` or `player.get_alerts{surface=s}` (`defines.alert_type` gives the names).
Fulgora that day (save fulgora-alerts-clear), all cleared:
- not_enough_repair_packs / not_enough_construction_robots: 11 damaged substations and a roboport, 3 destroyed entities as ghosts. No repair pack exists anywhere, Nauvis included. Repaired by setting health and reviving ghosts (free build: same as placing a new one). 60 construction robots moved from Nauvis to the base network, which had none.
- Lightning: most damage was old, but one substation at (-125,-125) was hit while I watched. 106 of my entities had no rod within 14 tiles (mostly the accumulator fields I added). 25 rods placed so every pole, accumulator, roboport and panel has one within 12. A full storm afterwards: no damage. After adding anything on Fulgora, re-run the rod check.
- no_storage: construction robots on the home island held scrap with no storage chest in that network; moved it into the wagons. It will recur whenever robots there pick something up.
- unclaimed_cargo: drop pod containers with 50 iron ore on Fulgora and Gleba; emptied into network storage and removed.
- A stray train-stop ghost of mine at (171,-103) removed.
Vulcanus demolishers (Captain): never kill them. They keep to a regular path unless bothered; lay a block of walls or foundation in front of one and the path it carves shows the safe build area. Cross its path with underground belts or with robots.

## Vulcanus demolishers: exact paths from the API (2026-11-11)
- `surface.get_territories()[i].get_patrol_path()` returns the waypoints the demolisher follows (closed loop); `get_segmented_units()[1]` has `.segments[1].position` (head), `.get_ai_state()` (waypoint, destination), `.activity_mode` (T4's was asleep and did not move for minutes; T2 and T3 were patrolling). Small demolisher head box is 3x3. Never script the unit itself.
- All tungsten ore is inside territories. Ore clear of its own demolisher's path: T5 patch at (-371,-183) 4.2M total, 3.1M at >=25 tiles, 1.5M at >=40 (safe ore box x -405..-359, y -217..-154); T4 near patch 364k total, only 102k at >=15; T8 (-524,-570) 816k all >=40 but a medium demolisher; T16/T17 around (450,605).
- T5's path is a huge loop (x -781..-241, y -394..211) and the ore is inside it, so any route crosses it once. T1's loop sits between the base and the ore north of y -90 (its southern edge runs (-205,-104),(-214,-96)); stay south of y -90 to avoid it. Chosen crossing: T5 path segment (-248,-82) to (-241,-55), i.e. cross at about (-245,-70) going west, then north-west inside the loop to the ore.
- Plan: tungsten mine in the safe box, elevated rail over the crossing (supports 12 apart, path midway), train to the base as on Fulgora; foundries on the lava at (53,0); carbide from coal and acid near the base.

## Vulcanus triggers earned (2026-11-11, save vulcanus-triggers-earned)
- Tungsten ore is `hard-solid`: only the big mining drill mines it. First ore comes from rocks, as in a normal game: `order_deconstruction` on free big/huge volcanic rocks inside robot construction range (98 rocks gave about 400 ore; `cell.is_in_construction_range(pos)`).
- `scripts/vulcanus_triggers.py lube|lava`: acid well (-11.5,89.5) -> refinery (-9.5,84.5, simple coal liquefaction) -> chemical plant (-12.5,79.5, dir 8, lubricant) -> assembler (-11.5,75.5, dir 8); lava pump (54.5,-12.5, dir 4) -> foundry A (48.5,-16.5, molten iron from lava, needs calcite) -> foundry B (48.5,-22.5).
- Crafted in order: foundry (assembler; steel, circuits, refined concrete moved from Nauvis) -> big-mining-drill researched; electric mining drill then big mining drill (foundry B) -> tungsten-steel; tungsten plate (foundry B) -> metallurgic-science-pack researched. Foundry B is left on tungsten plate.
- Port geometry (north-facing): foundry and refinery take fluids on the south side (x-1,y+2),(x+1,y+2) and give them on the north (foundry (x-1,y-2),(x+1,y-2); refinery (x-2),(x),(x+2)); stacking a foundry 6 tiles north of another joins output 1 to input 1 with one pipe at (x-1, y-3). Big mining drill is 5x5, radius 6.49. `prototypes.entity[n].fluidbox_prototypes[i].pipe_connections` gives these.
- Land route for tungsten: a breadth-first search on a 2-tile grid (no lava, no rocks or cliffs, 10 tiles from both patrol paths) connects the ore to the inside of the crossing at (-258,-70), about 940 tiles of belt winding west around the lava (x down to about -540). The base side reaches (-232,-70). The 26-tile gap over the path is for robots. Script: scratchpad bfs.lua (rebuild it; not in the repo).
- 220 logistic robots and 250 construction robots are on Vulcanus (moved from Nauvis).

## Vulcanus tungsten mine and crossing (2026-11-11, save vulcanus-tungsten-mine)
- `scripts/vulcanus_route.py OUT.json CLEAR EXPAND` (env ROUTE_START, ROUTE_GOAL): breadth-first belt route; ore tiles are NOT obstacles (belts run over ore), rocks and cliffs are (EXPAND tiles of margin). Routes saved in docs/vulcanus_tungsten_belt.json (1,090 tiles, mine (-376,-150) -> (-257.5,-68.5)) and docs/vulcanus_tungsten_belt_east.json ((-229.5,-69.5) -> (-117.5,-70.5), 120 tiles).
- `scripts/vulcanus_mine.py drills|poles|cross|east`: 15 big mining drills (west column x -374.5 and east column x -368.5 at y -186.5..-158.5 step 7, facing the belt column x -371.5; five more on the belt row y -203.5); substations in the 2-tile gaps (centre y = drill y + 3.5); 56 big poles beside the belts carry base power to the mine.
- Crossing of T5's path at y -70 (path x about -245): 3 red chests at the west belt's end, 6 blue chests (400 ore each) at the east belt's start, roboports at (-262,-64) and (-226,-64) in one network with 200 robots, one big-pole span (-254,-58) to (-227,-60). Nothing stands within 12 tiles of the path.
- Measured: 12.7 ore/s from 15 drills; first ore crossed within 4 minutes. The T5 demolisher was patrolling ("minimal" activity) and had not yet passed the crossing when this was written: watch a pass.
- LESSON: place_entities dry runs check each entity against the world only, not against the others in the same batch (a substation and a drill overlapped; a pole was planned on a chest).
- Science cell plan: free band y -36.5..-23.5 between the lattice rows; columns 9 wide, each a lava foundry (y -27.5) over a pack or plate foundry (y -33.5), one link pipe at (x-1,-30.5), lava main along y -24.5.

## Vulcanus science cell (2026-11-11, save vulcanus-science-running)
`scripts/vulcanus_cell.py foundries|unload|coal|carbide|calcite|dump|silo|space`
- Band y -58.5..-41.5 (the band south of it, y -38.5..-21.5, is the base's first solar field): lava pump (46.5,-43.5) -> lava main along y -43.5 (x -17.5..45.5) -> six columns: packs at x 36.5, 27.5, 18.5 (molten copper foundry at y -46.5 over a pack foundry at y -52.5), plates at x 9.5, -7.5, -16.5 (molten iron over tungsten plate). Link pipe at (x-1,-49.5). West chest of each foundry is blue (calcite 20; packs: carbide 60 + plate 40; plates: ore 100), east chest red. Extra substations at x -10, 10, 30 on y -57 and -42.
- Tungsten belt ends at (-117.5,-70.5) in three red chests; robots do all item moves at the base (1,020 logistic robots).
- Coal: three big drills at y -68.5 (x -72.5, -66.5, -52.5) dropping into red chests at y -71.5. Calcite: one big drill (-140.5,108.5) into a red chest, roboport (-130,110) and substation (-132,104) extend the network.
- Acid block: wells at (2.5,91.5), (-0.5,89.5), (-3.5,89.5), (7.5,94.5) -> acid main y 90.5 (x 4.5..19.5); carbon plants (dir 8) at y 88.5 and carbide assemblers at y 92.5, x 10.5, 14.5, 18.5; blue chests y 85.5 (coal 100) and y 95.5 (carbon 50, ore 100), red chests beside them.
- Stone is the surplus (about 21/s): two blue chests at (43.5,-50.5/-51.5) with inserters that drop it into lava, on only above 2,000 stone in the network. Verified: nothing lands on the ground.
- Silo (-30.5,-50.5), blue chests at (-31.5..-29.5,-56.5). Rocket part ingredients are NOT made on Vulcanus yet: 2,500 each of processing units, low density structure and rocket fuel were moved from Nauvis stock (enough for 50 rockets). Shuttle 7 requests 4,000 packs from Vulcanus and waits there for them; Nauvis pad requests 8,000 metallurgic (and electromagnetic lowered to 8,000); autopilot pack set includes metallurgic.
- Measured: 144 packs/min over 10 minutes (2.4/s) while a stock of ore lasted; ore mined 12/s against 18/s used, so 28 speed module 2 went into the tungsten drills (not yet re-measured). 7.5 ore per pack.
- Power: load about 44 MW drained the first 3,240 MJ in one night; `planet_base.py solar --cells 9` added 216 panels and 243 accumulators (6,885 MJ). Vulcanus day is 5,400 ticks.
- Not yet seen: a rocket launch, a delivery to Nauvis, and the T5 demolisher passing the crossing.

## Vulcanus solved, first version (2026-11-11, save vulcanus-solved-v1)
- End to end: tungsten mine in territory 5 -> 1,100-tile belt -> robot crossing -> base cell -> silo -> Vulcanus Shuttle -> Nauvis pad -> labs. First delivery of 2,000 metallurgic packs seen on Nauvis (shuttle trips 144 -> 146), labs researching cliff explosives.
- Measured over 10 minutes: 160 packs/min (2.7/s); ore mined 1,354/min against 1,200 used after 28 speed module 2 went into the tungsten drills; no alerts, no ghosts; accumulators full at dusk (6,885 MJ).
- Demolisher pass watched live: T5's demolisher went by the mine at 31 tiles and through the crossing (nearest building 12 tiles from the path, robots flying 4 tiles over its head), woke to "full" activity near the buildings, stayed on patrol (ai type 0) and damaged nothing. Keep everything 12+ tiles from a patrol path.
- Intake gate: the three unload inserters at the tungsten belt's end run only while fewer than 6,000 packs are in the network.
- Autopilot TOPUP now counts a pack as available if Nauvis labs plus network hold 30 or Nauvis made some in the last 10 minutes; otherwise techs needing it rank last (it had queued metallurgic research before any pack arrived and stalled the labs).
- Open: rocket part ingredients on Vulcanus came from Nauvis stock (2,500 each, about 50 rockets); no local production yet. The tungsten patch is finite (4.2M ore, 7.5 ore per pack). Chemical science on Nauvis (130/min) limits the labs.

## Vulcanus rocket parts made locally (2026-11-11, save vulcanus-rocket-parts-local)
`scripts/vulcanus_parts.py oil|metal`
- Oil field x 26..73, y 97..117 (lattice cluster at (60,100) removed), anchored on refinery R3 (54.5,111.5); refineries at x 30.5, 38.5, 46.5, 54.5 (simple coal liquefaction, blue chest on the west: coal 300, calcite 60). Acid main y 114.5 from x 8.5, three new wells (13.5,109.5), (9.5,108.5), (21.5,90.5).
  R1 and R2 each feed a solid-fuel-from-heavy-oil plant above them. R3 and R4 share a heavy oil row (y 108.5) into the heavy cracker (53.5,106.5); light oil row y 104.5 runs west to two rocket fuel assemblers (48.5 and 41.5, 106.5) and up into the light cracker (55.5,102.5); gas into the plastic plant (55.5,98.5).
  Water: acid neutralisation (62.5,112.5) under steam condensation (62.5,108.5), outlet pipe (63.5,106.5) feeding water rows y 108.5 and y 104.5. Processing unit assembler (67.5,112.5) on the acid main; circuits above it at y 107.5, 103.5 (electronic) and 99.5 (advanced).
- All chemical plants face south (dir 8): inputs on the south side, fb1 at (x+1,y+2), fb2 at (x-1,y+2); outputs north, fb3 at (x+1,y-2). Cracking recipes list water first, so water is fb1 and oil fb2. Refinery (dir 0): acid in at (x-1,y+3), heavy oil out at (x-2,y-3); its unused outlets at (x,y-3) and (x+2,y-3) did not leak into the water row.
- Metal row beside the northern lava pool: pump (80.5,53.5), lava main y 75.5; molten iron foundry (72.5,72.5), molten copper foundry (82.5,72.5); casting iron (64.5,66.5), low density structure (73.5,66.5), copper cable (82.5,66.5); iron pipe y 69.5 x 63.5..72.5, copper pipe x 74.5..81.5.
- LESSON: a lava foundry pushes its molten metal out of BOTH north outlets. The iron foundry stood directly under the LDS foundry and filled the copper pipe with iron through its second outlet. Never put a pipe on a foundry's second outlet tile unless it should carry that fluid; flush with `clear_fluid_inside()`.
- Measured: processing unit 8/min, low density structure 7/min, rocket fuel 5/min (need about 8 each for 160 packs/min); solid fuel was the limit and coal buffers were raised afterwards (not re-measured). Coal use rose from about 630 to 1,090 a minute; three more coal drills (six in all) mine 1,490.
- Coal outside demolisher territories is only about 1.0M on the whole charted map (58M inside territories). Calcite outside: 1.0M.

## Nauvis belt survey (2026-11-11, read only)
13,267 belt pieces in 287 connected networks. 153 networks (3,300 pieces) have no inserter or mining drill touching them, 27 of those (1,266 pieces) hold no items at all; the survey may split networks at underground belts, so re-check before removing. Entities: 860 mining drills, 528 furnaces, 388 assemblers, 8,697 poles, 932 roboports. The Captain wants the main base cleaned up, organised and compressed, with big mining drills and foundries; no plan agreed yet.

## Nauvis clean-up stage 1: dead belts (2026-11-11, saves before-nauvis-dead-belts, nauvis-dead-belts-removed)
`scripts/nauvis_dead_belts.py [--apply]` groups belts, splitters and underground belts (`underground_belt_neighbour`, not in `belt_neighbours`) into networks and removes those no inserter or drill touches, plus empty ones nothing can ever drop onto. Removed 757 pieces (736 + 21), none held items; 12,510 remain in 70 networks. Machine statuses and alerts unchanged afterwards.
- The first survey without underground pairing said 3,300 dead pieces; the true figure was 757. Always pair undergrounds.
- Left alone, for the Captain to decide: one empty, idle network of 826 pieces across x -333..131, y -126..-25 (6 feeders, none working; 12 takers); three networks (108 pieces) that nothing takes from (removing them would make their feeding inserters spill onto the ground).
- The "idle 826-piece network" was the science belt from four military and two production science assemblers ((117.5..126.5,-124.5) and (99.5,102.5,-62.5)) to twelve red chests at (-333..-316,-42.5); idle only because those assemblers were starved. On the Captain's go-ahead it was removed and a red chest placed under each of the six output inserters instead (save nauvis-science-belt-to-chests). The twelve old unloading inserters and their chests are still there, now idle. LESSON: before calling a belt dead, look at what its feeders take from.

## Nauvis clean-up stage 2 (2026-11-11, saves before-nauvis-nowhere-belts, before-nauvis-big-drills, nauvis-big-drills)
- Belts to nowhere (nothing takes from them; the Captain pointed at the stone mine): three networks, 108 pieces, removed with the 3 drills and 1 inserter that only fed them; 315 items went to storage. Inserters whose drop target is "nothing" at a belt's end are usually train loaders with no train present: not dead.
- `scripts/nauvis_big_drills.py X0 Y0 X1 Y1 [--apply]`: 782 electric drills -> 211 big mining drills dropping on the same belt tiles (the usual layout is two electric rows back to back between belts; one big row replaces both). 59 electric drills kept where a big one does not fit, 54 uranium drills untouched (acid piping). 114 poles in the way removed, 33 substations and 5 medium poles added; every big drill is on the main grid; no alerts. Upgraded to rare.
- Products made on Nauvis but not consumed (50 h): space platform foundation (5 machines, 4 working, 34/min, 97k stock, none used), nuclear fuel (7 machines full), rocket fuel (19 machines full, 2/min used), military items (military science not running). Reported to the Captain, nothing changed.

## Nauvis foundries: on hold (the Captain, 2026-11-11)
Skip foundries on Nauvis until advanced asteroid processing is researched (it needs agricultural science from Gleba); then a platform (the Captain named Mobile Space Factory) can make calcite in orbit and drop it. Until then the only calcite is Vulcanus rockets: a full conversion needs about 70 calcite/min (iron 5,400, copper 4,300, steel 880 plates/min), i.e. a 500-calcite rocket every 7 minutes.
A pilot (`scripts/nauvis_foundry_pilot.py`: melting foundry over a casting foundry on the ore belt at (-377.5,-355.5)) was built and then undone on that order: the eight furnaces, their inserters and the ore belt are back, calcite requests removed from shuttle 7 and the Nauvis pad. 400 calcite moved from Vulcanus stock stays in Nauvis storage. The pilot was never seen running.

## Nauvis trains on nuclear fuel only (2026-11-11, saves before-nauvis-train-fuel, nauvis-trains-nuclear)
Why trains still burned coal and rocket fuel: (1) old refuelling inserters fed locomotives straight from coal and rocket fuel belts at stations; (2) the 21 blue refuelling chests (request nuclear fuel 10) still held thousands of leftover coal and some rocket fuel; (3) locomotive fuel slots were full of the old fuels (nuclear fuel stacks to 1, so little fitted); (4) trains 290 (Hub Chem Yard / Refinery Yard) and 320 (Science Packs Load / Unload) had no nuclear chest at either station.
Done with `scripts/nauvis_train_fuel.py` plus two scratch scripts: old fuel moved out of chests and locomotives into storage (coal about 7,300, rocket fuel 310, wood 200), each locomotive topped up to at least 2 nuclear fuel, five belt-fed fuel inserters removed, and four new inserter + blue chest pairs at the front and rear locomotive positions of Refinery Yard and Science Packs Unload. The three rocket fuel inserters at (-204.5,-262.5..-260.5) load cargo wagon 4 of train 290 and were left.
To tell a fuel inserter from a cargo loader: carriages sit every 7 tiles from the stop (first centre 3 tiles behind it); compare with `train.carriages`.

## Nauvis chemical science (2026-11-12)
- Eight assemblers at y -66.5 (x -344.5..-316.5), fed by the belt y -63.5 (advanced circuits south lane, engines north lane) and y -62.5 (sulfur).
- They were starved of engines (48/min from four belt-side assemblers; about 130/min needed). Fix in `scripts/nauvis_chem_science.py`:
  blue chest (-304.5,-59.5) + long-handed inserter (-304.5,-61.5) puts network engines on the north lane; seven robot-fed engine
  assemblers at x -320.5, y -118.5..-100.5. Measured after: 130 packs/min (was 48), engines 135 made / 134 used.
- Labs can use far more (48 labs, all packs but chemical plentiful), so chemical science is still the limit; next step is more science assemblers.

## Vulcanus science rate (2026-11-12)
- Production statistics flows on Vulcanus read low and jumpy; measure with `products_finished` deltas over a few minutes instead.
- Three plate foundries (57.6 plates/min each) capped science at about 127 packs/min. The trigger workshop pair (lava foundry 48.5,-16.5 and
  plate foundry 48.5,-22.5) is now the fourth: its chest (44.5,-16.5) requests calcite 20, chest (44.5,-22.5) tungsten ore 100.
  Measured after: 230 plates/min, 170 packs/min (three pack foundries, capacity 173). Nauvis science machines are 96..144 packs/min per kind.
- At that rate the network's coal fell about 180/min; the 6,000-pack intake gate pauses the cell often, which lets coal recover.

## Vulcanus coal from territory 5 (2026-11-12) - `scripts/vulcanus_coal.py`
- Coal outside all territories is under 1 million; territory 5 holds 17 million, and the tungsten belt passes 20 tiles east of that field.
- Seven big drills on a collector belt along y -209.5 (x -640..-588.5). It meets the tungsten belt's corner (-587.5,-209.5) from the west while the
  ore arrives from the east: a belt fed from both sides and not from behind stays straight and both side-load, so ore keeps lane 1 and coal lane 2.
- Mixed belts with separately gated unloaders jam (head-of-line blocking). Keeping one item per lane, with filtered unloaders, avoids it.
- Crossing: west red chests (-259.5,..),(-257.5,-70.5) ore only; (-255.5,-68.5/-67.5) coal only. East blue chests: north row ore 800, south row
  coal 800 (their inserters load opposite lanes). 400 robots. Base end: (-118.5/-116.5,-70.5) ore gated packs<6000; (-117.5,-69.5) coal gated coal<12000.
- place_entities removes trees and rocks under what it places.
- Vulcanus Shuttle: its hub has 59 slots and is full at 4,000 packs (the rest is ammunition, fuel cells, calcite), so 4,000 a trip is the
  ceiling; a request of 8,000 just left it waiting. The schedule's circuit condition DOES see the pack signal doubled (it left with 2,000 when the constant was 4000), so the constant is 8000 for 4,000 packs. It waits at Nauvis for
  thruster fuel 35000. A round trip burns about 21,000 fuel per tank (13,600 out, 7,800 back) and the platform makes 700..1,400 a minute, so the cycle is fuel-bound at 15..30 minutes whatever the threshold: about 130..260 packs a minute.

## Gleba: spoilage-first core (started 2026-11-12, scripts `gleba.py`, `gleba_core.py`, routes in `docs/gleba_routes.json`)
The Captain's warning: spoilage is what makes Gleba unstable. The layout answers that first; rate comes second.
- **Where:** core at x 61..132, y 1..20 (free band between the substation rows). Yumako farm: tower (-150.5,-115.5) on the natural soil north-west.
  Jellynut farm: tower (195.5,100.5) east. Two turbo trunks (392 and 176 tiles, wetland landfilled) meet at (126,-4), one lane each.
  Water: pump (156.5,26.5) -> pipe -> main along y 12 over the egg chambers.
- **Rules built in** (details in the `gleba_core.py` header): mash and jelly never ride a belt (direct insertion); every belt is a dead end whose
  last inserter takes spoilage only into a heating tower (egg belt and junk belt: takes everything); every machine has a spoilage-out inserter;
  two electric assemblers restart the nutrient belt from fruit alone; priority is by position on the belt (fuel for the fruit line, then eggs,
  then science; bioflux passes the nutrient chamber before science).
- **Eggs:** keeper pair (117.5/121.5, y 14.5) hands eggs to each other and always runs. The other six chambers take eggs off the egg belt one at
  a time and only while no egg reaches the ten sensor tiles before the burner (red wire, condition egg = 0), so surplus is not made.
  Egg chambers must face east (water inlet); a biochamber placed before its recipe has a fluid ignores `direction`, set it after `set_recipe`.
- **Trigger chain as earned:** jellynut (robot-mined jellystem) -> 10 nutrients from spoilage in an assembler (biochamber) -> 500 nutrients
  (artificial soil) -> one biochamber crafted in an assembler (bioflux; needs 1 pentapod egg) -> bioflux 1/25/100 (bacteria, bioflux processing,
  agricultural science). The egg came from the lone small raft at (-134,199): two laser turrets on a four-panel solar outpost shot it; it
  dropped 3 eggs (script moved one to the crafter with 5 nutrients, two into egg chambers; `gleba.py seed` spreads belt eggs to empty chambers).
  If the egg line ever dies (15 minutes without nutrients), another raft has to be shot: 28 left, nearest small ones at (127,221), (99,-242).
- **Agricultural towers harvest every wild tree in reach too** (wood, stone, spoilage): the trunk inserter is whitelisted fruit + spoilage, a
  second inserter (blacklist) puts the rest in a red chest. Stone cannot burn, so it must never reach a belt end.
- **Seeds are the slow part.** A tower only replants with seeds; 50 fruit give 1.5 seeds in a biochamber (1 in an assembler). The wild plants in
  reach (7 yumako, 13 jellystems) were harvested in minutes, then the field regrows from seeds at about x1.5 per 5-minute generation. Seeds go
  junk belt -> red chest (72.5,0.5) -> robots -> blue chest at each tower.
- **Science chambers are off** (`gleba_core.py recipes --science` turns them on): there is no rocket silo on Gleba yet, packs would only spoil.
- API: `defines.inventory.crafter_input`; belt control behaviour uses `circuit_enable_disable`, `read_contents`, `read_contents_mode`;
  `connector.connect_to(other,false)`; `inserter_stack_size_override`; `place_entities` takes `"params":{"quality":"rare"}`;
  `surface.set_tiles` with landfill for wetland; plants are type `plant` (`tick_grown`), not removed by `place_entities`.
- Not done: rocket silo and shipping, a long stability run, more soil (artificial soil is researched), rocket part ingredients on Gleba.

## Gleba: shipping and first rates (2026-11-12, `gleba_ship.py`, `_glebawatch.py`)
- Silo (143.5,3.5), blue chests (142.5..144.5,-2.5) holding 2,500 processing units, 2,400 low density structure, 950 rocket fuel moved from
  Nauvis stock (19 rockets; nothing for rockets is made on Gleba yet). Science belt end -> red chest (128.5,20.5) -> robots -> silo
  (`use_transitional_requests`). Spoilage in that chest goes to a heating tower (125.5,20.5).
- **Science rots (the Captain, 2026-11-12):** the science chambers' egg inserters work only while the red chest holds under 1,000 packs
  (green wire), so packs are made close to pickup. Shuttle 6 asks for 2,000, leaves Gleba with 2,000 aboard or after 10 minutes. Nauvis pad asks 8,000.
- Measured with science on (production statistics, per minute): science 102, eggs 68, bioflux 168, nutrients 1,440 to 1,640, yumako 240, jellynut 60.
  The limit is nutrients: every nutrient inserter drops on the same belt lane (about 1,440 a minute) and eggs take 30 each. A second nutrient
  chamber (89.5,14.5) sits just before the science chambers because they got no fuel at the end of that lane. More rate needs a second lane.
- The block ran about 2.5 hours of game time unattended during the seed shortage with no jam and the egg line alive.
- `products_finished` on biochambers does not count plain crafts; use `force.get_item_production_statistics('gleba')` here.
- The Captain wants the rot burnt for steam power (boilers) rather than only destroyed: not built yet. A boiler stops burning when its steam
  is full, so a belt end must keep a heating tower as overflow, or the towers get heat exchangers and turbines instead.
- Not seen yet: a rocket launch from Gleba, a delivery to Nauvis. The autopilot pack list has the agricultural pack added but the running
  autopilot was not restarted.

## Gleba long run, egg life support, stalled shuttles (2026-11-12 evening)
- **Game speed for tests (the Captain's order):** `game.speed=8` gives about 6.8x on the server; set it back to 1 afterwards. `scripts/_glebalong.py`
  appends one line a minute to `docs/gleba_longrun.log` (rates from the ten-minute production statistics, keeper eggs, belts, rot, enemies, deliveries).
- **Long run:** about 5 game hours at speed, 46 lines. Keeper pair never lost its eggs, no rot in the pack chest, no hatchlings, packs delivered
  to Nauvis and used by the labs. Science averaged 50 a minute over the run (100 while the chambers run; they pause when 1,200 packs wait for the shuttle).
- **Fruit-cut tests** (remove the belt tile at (126.5,0.5), put it back later; `LuaEntity.active` is read only on belts): 10 minutes without fruit: the
  nutrient belt was empty in 3 minutes and every chamber stopped, eggs survived, restart by itself in under 2 minutes. That margin was too thin
  (eggs hatch at 15), so `scripts/gleba_reserve.py` built a life support from rot: spoilage caught at the junk belt and the egg belt tail ->
  robots -> blue chest (130.5,10.5, asks 9,600) -> electric assembler (127.5,10.5) -> nutrients onto the belt just before the keeper pair, fed only
  while the nutrient belt is empty. 25 minutes without fruit: keeper kept 2 eggs alive throughout, 5,200 spoilage used, restart by itself, nothing hatched.
  So about 40 minutes of cover per 9,600 spoilage.
- Yumako was the short fruit (16 trees on natural soil): `gleba.py soil` put artificial soil on the wetland in each tower's reach; 40 plants each now.
- A rocket only flies full (1,000 packs) unless the request carries `minimum_delivery_count`; the Gleba request has 500. The pack buffer gate is 1,200.
- **Vulcanus Shuttle was stuck:** hub full at 3,000 packs (other cargo grew), waiting for 4,000. Now asks 3,000, leaves at 3,000 (constant 6000).
- **Fulgora silo was starved:** no processing units or low density structure in the Fulgora network (cause not found; scrap normally yields both).
  2,500 and 2,400 moved from Nauvis stock into its blue chests; electromagnetic packs reached Nauvis again.
- Vulcanus rocket parts under load: 4.4 rockets' worth of parts an hour used at today's lab demand; capacity measured earlier 8 PU, 7 LDS, about 9.6
  rocket fuel a minute (solid fuel bound). Four productivity modules moved into the Vulcanus and Gleba silos (16%), so a full 170 packs/min needs 7.3 each.
- Research on the road to Aquilo: carbon fibre done; rocket turret, advanced asteroid processing, Aquilo discovery queued (6,000 agricultural packs).
- Relay shuttles (the Captain's order): outer ships go only between an outer planet and an inner hub planet; cargo changes ship on the hub's
  surface (landing pad -> silo -> inner shuttle), since platforms cannot hand cargo to each other. Not built: needs rocket turrets and Aquilo discovery.

## Six shuttles, named by route (2026-11-12, `scripts/more_shuttles.py`)
- The Captain: several fast shuttles per planet (Gleba first, its packs rot), names that say source and destination, Fulgora as the hand-off
  hub for the outer relay ships. Platforms: 5 `Nauvis-Fulgora 1 Shuttle`, 6 `Nauvis-Gleba 1 Shuttle`, 7 `Nauvis-Vulcanus 1 Shuttle`,
  8 `Nauvis-Gleba 2 Shuttle` (platform-6), 9 `Nauvis-Vulcanus 2 Shuttle` (platform-7), 10 `Nauvis-Fulgora 2 Shuttle` (platform-8).
  Names still end in `Shuttle` because the autopilot repairs platforms matching `Shuttle$`.
- New ship: `more_shuttles.py create` -> `build_shuttle2.py --surface S --apply` -> `configure_shuttle2.py --surface S --platform N` ->
  `more_shuttles.py twin` (200 iron plates from Nauvis, sibling's schedule and science requests). It fills from zero in about an hour.
- **Trap:** the starter pack leaves foundation items in the hub, and the rear ammunition belt took 10 of them before the filters were set, so
  the rear turret (-3,14) got no magazines on all three new ships. Cleared by moving every non-magazine, non-chunk item off the belts back into
  the hub. Check `turrets armed 11/11` before the first flight of any new ship.
- Autopilot PRIORITY now starts with advanced-asteroid-processing (58% done), rocket-turret, planet-discovery-aquilo; they wait on agricultural packs.
- Asked for, not started: a platform above Gleba making all the sciences in space (needs advanced asteroid processing, not researched yet).

## Server freeze, 2026-11-12 night (my mistake)
- `gleba_labs.py ships` ran `while #secs.sections>0 do secs.remove_section(1) end` over RCON. It never ended: RCON stopped answering and SSH to the
  VM timed out at the banner (ping still fine). **Never send an unbounded loop over RCON**: a Lua command that does not return freezes the game
  for everyone and nothing but a restart ends it. Use `for` over a fixed list, or a counter with a hard cap.
- `gcloud` had no active account in my shell, so I could not restart the VM or container; reported to the Captain.
- State at the freeze: last named save `six-shuttles`. Built after it and possibly lost: Gleba labs, pack belt, landing pad (`gleba_labs.py build`
  and `config` rebuild them in a minute). Not yet run: `gleba_labs.py ships` (fixed, untested) and the autopilot change to count Gleba's packs.
- Decision recorded: Gleba is science central (labs on Gleba, other packs shipped in); the Nauvis-Gleba shuttles carry packs outward.
- Freeze follow-up: the VM is operated from skippy-core, not with gcloud here: `ssh -o BatchMode=yes skippy-core "sudo -n python3 /opt/skippy-core/cd/cd.py ops status|logs factorio|restart|restart-game factorio"`.
  `ops logs factorio` showed no crash: autosave `_autosave4` finished about 75 s before my command, then only health-check connections and the
  container `unhealthy`: the game thread is stuck in the loop. `restart-game` got no reply (the VM's agent is starved); `ops restart` was denied
  by the auto mode classifier, so the restart is the Captain's to run or allow.
- **A restart loads `skippy.zip` and nothing else** (`SAVE_NAME=skippy`, `LOAD_LATEST_SAVE=false` in SkippyTel `games/docker-compose.yml`). `save_game <name>`
  and the rotating `_autosaveN.zip` are never loaded by themselves. After the 2026-11-13 restart the server came up on a `skippy.zip` from game hour 171.6
  (before Gleba), at speed 20, paused with nobody on. The state to bring back is `_autosave4.zip` (01:10 UTC, about 75 s before the freeze; game hour ~187)
  or `six-shuttles.zip` (00:56). Fix: stop the container, keep the old file under another name, copy the wanted save to `skippy.zip`, start.
  My SSH attempt to do that was denied by the auto mode classifier; left for the Captain. Autopilot stopped meanwhile so it does not act on the old state.
- Before any planned restart: copy the newest save over `skippy.zip` first, or the restart goes back in time.

## Recovery and Gleba science central (2026-11-13)
- Recovery from the freeze: `ops restart` (allowed by the Captain) brought the server up on the old `skippy.zip`. Fix that worked, over SSH to the VM:
  copy `_autosave4.zip` aside, `docker stop factorio`, rename `skippy.zip` to `skippy-old-171h.zip`, copy the autosave to `skippy.zip`, `docker start factorio`.
  Came back at game hour 188.2 with six shuttles and Gleba intact. **`save_game skippy` now and then keeps the file a restart loads current.**
- Hub logistic sections: some are not manual and raise "trying to change logistic section that is not manual"; touch only `sec.is_manual` ones.
- `scripts/gleba_labs.py build|config|ships` all applied: nine labs beside a pack belt from the science chest, blue chests asking 200 of each
  non-rotting pack, landing pad (142,23) asking 4,000 of each. Both Nauvis-Gleba shuttles ask Nauvis for 400 each of eight packs (not military:
  Nauvis has none), leave Nauvis fuelled, armed and loaded (`all_requests_satisfied`), leave Gleba after 10 quiet seconds. Nauvis pad no longer asks
  for agricultural packs. Autopilot counts packs in Gleba's labs and network too.
- Not seen yet: a pack delivery to Gleba, research progress in the Gleba labs. Military packs: none made on Nauvis, rocket turret research needs them.
- 2026-11-13: the VM switched itself off after 30 idle minutes (status TERMINATED via `ops status`), so `scripts/gleba_eggs.py` (second keeper
  pair fed slowly, reserve tripled) is written but NOT applied. The game also pauses with nobody connected, so outage tests need a player on
  (or auto-pause off). Asked the Captain before starting the VM (it costs money and pings Discord).
- White science above Gleba (asked 2026-11-13): not useful now. Oxide chunks there are 0.0006 against 0.0042 at Nauvis (ice is the limit), while
  Nauvis holds about 106,000 space packs and the White Science platform another 26,000 and makes 472 a minute; ship them.
- 2026-11-13 later: VM started with `ops start factorio` (the Captain's yes); it came up on the current state. `gleba_eggs.py --apply` done: second
  keeper pair (93.5/97.5) with pair inserters at x 95.5 and slow one-at-a-time nutrient inserters; reserve is three chests in a row. NOT tested:
  the game only ticks with a player connected (auto-pause is a server setting; `/config` has no runtime switch for it), and nobody was on.
  To do when the Captain is on: 60-minute fruit cut at speed 8 (remove the belt tile at (126.5,0.5), `/tmp`-style watch as in the 25-minute test).
- The Captain: the server must not sleep until Factorio is solved. A separate session ("Games VM: stay-on mode for Factorio") is changing SkippyTel
  so `ops` can set idle-minutes 0 and max-hours 0. Until it lands the VM still sleeps after 30 idle minutes.
- Raw server commands: `mcp_server._GW._send('/command')`.

## Gleba science central running; egg tests; military cell (2026-11-13)
- First deliveries to Gleba worked once the Gleba stop waits 60 quiet seconds (10 left packs aboard). All nine labs ran; advanced asteroid
  processing finished there; rocket turret reached 91%. Both Nauvis-Gleba ships now ask for all nine packs x400 and wait at Nauvis for them.
- **Logistic packs are the short one:** Nauvis network 0. Its 48 labs were using them on research that needs no agricultural pack. The
  autopilot now queues only techs that need the agricultural pack while any is open, so the Nauvis labs idle once their leftover packs are gone.
- **Military science:** the belt plant at (99..127,-122) made none (grenade assemblers get no iron: iron lane of belt y -125.5 empty). New
  robot-fed cell `scripts/nauvis_military.py`: eleven 9x3 slots at x -360 and -350 (blue chest, inserter, assembler, inserter, red chest),
  about 77 packs a minute; 2,000 in stock within minutes. The old plant is untouched.
- **60-minute fruit cut (`scripts/_glebacut.py 60`):** keeper pair A held 2 eggs for the whole hour on the rot reserve (31,000 spoilage, gone at
  minute 57: the assembler eats about 550 a minute); full restart about 6 minutes after fruit came back. But 161 premature pentapods were killed
  by the turrets, 15 entities scratched, one lost: starved chambers kept taking eggs off the belt and those hatched.
- Fix, `scripts/gleba_egg_gate.py`: a decider (95.5,20) puts out signal A only while eggs at the tail = 0 AND nutrients on tail tiles
  x 100..105 > 10; the six belt egg inserters need A > 0 (green). Not yet re-tested with a fruit cut.
- Defence (the Captain's warning: whatever breeds eggs gets attacked): four tesla turrets (104,-2), (112,-2), (131,4), (54,10) and lasers at the
  labs and both farms, besides the four lasers at the core (`scripts/gleba_defence.py`). No repair packs on Gleba or Nauvis (stock 0); ghosts are
  revived by script.
- Second keeper pair B is not kept alive by the reserve (pair A takes all of it); it and the production chambers reseed from the belt afterwards.

## Nauvis logistic science (2026-11-13, `scripts/nauvis_logistic_science.py`)
- It made none: the seven inserter assemblers (x -198.5..-78.5 step 20, y -59.5) had iron and gears but no electronic circuits on their belt.
  Six now have a blue chest (circuits 200) on the north side with an inserter into the assembler (west of centre where a substation stands
  east: -198.5 and -158.5). A roboport at (-162,-66) closes a hole in robot coverage at the -158.5 chest. The unit at -78.5 has a belt north of
  it and is left belt-fed (still starved). Six units at 20 a minute each: about 120 a minute; measured 52 a minute and rising two minutes in.
- Do not apply a build whose dry run reported failures: I did, and left a stray inserter at (-77.5,-61.5), since removed.

## 2026-11-13 evening: five Gleba ships, egg gate re-test, space factory idea
- Rocket turret researched; Aquilo discovery reached 70% in the Gleba labs. Labs use 400 of each pack in about 4 minutes (9 labs, about 100
  units a minute), so delivery is the limit: `Nauvis-Gleba 3/4/5 Shuttle` built (platforms 11, 12, 13 on platform-9/10/11). `more_shuttles.py twin`
  now clears starter-pack junk off the belts itself and skips ships that already have a schedule.
- Egg gate re-test, 30 minutes without fruit: production chambers held no eggs, keeper A kept 2, restart by itself. Hatchlings killed went
  161 -> 23 more (eggs already inside chambers when the fruit stops still hatch, and keeper B's own). One more building scratched.
- Fulgora hand-off landing pad: no dry spot with power found next to the silo (150,-170) in a quick search; not placed.
- The Captain's idea: a gigantic stationary factory platform above Gleba, most materials from asteroids, dropping packs straight to the Gleba
  labs (drops need no rocket). Game data: chunk spawn at Gleba is metallic 0.0012, carbonic 0.0030, oxide 0.0006 plus medium asteroids
  (0.0010, 0.0025, 0.0005); Nauvis is 0.0125, 0.0083, 0.0042 chunks only. Advanced asteroid processing (researched) gives copper, sulfur,
  calcite; reprocessing turns the plentiful carbonic chunks into the other kinds. My rough estimate, not measured: 0.4 to 0.7 chunks a minute per
  collector at Gleba, so hundreds of collectors for 10 full pack sets a minute. Proposed a small pilot first to measure the real income.
- 2026-11-13: the Captain expected everything at epic (purple) already. It is NOT researched: `is_quality_unlocked('epic')` false, `epic-quality`
  0% of 5,000 units (automation, logistic, chemical, utility, space, agricultural). Put first in the queue and in the autopilot PRIORITY.
  When it completes: `scripts/upgrade_quality.py --items --apply` (all surfaces), and change the `"quality": "rare"` constants in the Gleba,
  shuttle and Nauvis scripts. Everything else is already at rare except things the game refuses (rails, Fulgoran ruin attractors, hubs).
- Aquilo discovery is researched (2026-11-13).

## Gleba Wheel, stage 1 (2026-11-13, `scripts/wheel.py`, platform 15 on `platform-12`)
- The Captain: a zero-waste wagon wheel above Gleba for space science and every Nauvis pack, most material from asteroids, stone by rocket.
  All fluids those packs need can be made in space (coal synthesis, simple coal liquefaction, cracking, sulfuric acid, lubricant are unlocked).
- Built: square ring, collector row 34 tiles out, 60 collectors, rim belts, four spokes, inner belt loop at 10 tiles, 8 crushers handing
  products straight into the hub, ammunition loop with 24 gun turrets, 60 solar panels, 20 substations. Layout in the script header.
- **Measured income (first 40 game minutes): about 5 chunks a minute in all** (metallic 1.0 to 1.6, carbonic 2.9 to 4.5, oxide 0.5 to 1.0),
  i.e. 32 iron ore, 38 carbon, 7 ice a minute; about 0.08 chunks per collector-minute, about 0.02 per tile of rim. Belts ran empty, so this is
  what arrives, not what the crushers can take. Ice limits space science to about 35 packs a minute; the Nauvis packs need 50 to 100 times this.
- Lessons: (1) collectors near the corners were refused until the ring foundation in front of them was removed; (2) an underground belt's
  `type` must go in `params`, a top-level `type` is ignored and both ends become inputs; (3) the ammunition feed stopped one tile short of the
  loop and the starter-pack foundation items jammed it, so the turrets stayed empty and asteroids destroyed 21 collectors and about 200 tiles
  in half an hour at speed 8: arm turrets from the hub by script BEFORE running at speed; (4) the hub (59 slots) fills in under an hour and then
  everything backs up, which is safe but stops the count; (5) the Gleba pad has 80 slots: nine packs at 4,000 filled it, now 1,200 each.
- State left: 60 collectors, 24 turrets armed, loop full, hub 2,500 magazines (moved from Nauvis; nothing on board makes them yet), hub full
  of ore so crushing has stopped. The autopilot repairs platforms named `...Wheel` as well as `...Shuttle`.
- Not built: furnace, magazine and space science machines on the wheel (no hub-adjacent room between the crushers: needs a belt-fed block).
