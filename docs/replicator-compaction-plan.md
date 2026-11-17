# Replicator compaction plan (2026-11-14, the Captain: "squish the replicator into the smallest stone wall box you can ... lossless compression for factories")

## What stands now (measured, read-only)

Wall (epic stone-wall, partial: west half only): x -366.5..-287.5, y -243.5..-162.5, 80 x 82 tiles = 6,560 tiles. Of it, the working Replicator parts cover very little:

| Part | Where now | Size now | Notes |
|---|---|---|---|
| 3 compact cells (replicator_cell.py, 3 machines each) | y -218..-203, x -358..-289 | 3 x (21 x 11) set 24 apart | the big block was already retired (commit 2703b40); 9 maker machines |
| Hub: demand roboport + stock stage + silo wiring | (-352,-229) | about 8 x 4 | the cells, furnace, fluid and fluid-assembler units all read it |
| Furnace unit + its table | furnace (-329,-222); table of 170 deciders x -323..-306, y -231..-222 | 17 x 10 table | one decider per smeltable item |
| Fluid unit (chemical plant + barrel machines) | x -306..-292, y -230..-218 | about 14 x 13 | |
| Fluid-assembler unit (2 machines) + its table | machines (-331,-181); table 96 deciders x -336..-289, y -174..-173 | 48 x 2 table + 12 x 8 | this is what spilled south of the old wall |
| Buffer chest field | x -340..-336, y -228..-226 | 5 x 3 | |
| Console (44 display panels + 44 lamps, replicator_viz.py, claimed by another session) | rows y -234 and -192, x -366..-293 | 2 rows, 74 wide | sets the box WIDTH and HEIGHT today |
| North spill | combinators y -240/-242 and chests near (-341,-241) | small | barrel/chem yard may own some of it |

## Target

Same logic, same wiring (script wires over-reach, so distance never matters), tight packing:

1. Cells abutted: 3 x 21 = 63 wide x 11 tall (not 72 wide with 3-tile gaps).
2. Hub, furnace unit, fluid unit, fluid-assembler unit, buffer field in ONE row under the cells, tables folded (decider blocks are 1x2 tiles, so a 170-decider table is a 17 x 10 block or a 34 x 5 block: fold to fit the row).
3. Console rows moved to the new top and bottom edge (replicator_viz.py re-run with the new footprint; ask the session that owns it).
4. Wall = the bounding box plus one tile. Rough result: about 65 x 34 = 2,200 tiles, about a third of the current 6,560.

## Second pass (logic compression, only on go-ahead)

The two big tables are the biggest ground users left: the furnace table (170 deciders) and the fluid-assembler table (96 deciders). The cell trick (a machine set by circuit to the chosen item reads its own ingredients) replaces a table with one bench machine; the cells already use it. Doing the same for the two units removes about 266 deciders and the 17 x 10 and 48 x 2 blocks. Needs the same live verify as the cell swap (replicator_compress.py verify).

## Procedure (each step: save, dry run, apply, verify, rollback ready)

1. `save_game pre-compaction`. Dry-run every placement (place_entities dry_run).
2. Build the new block at the tight site next to the old one (never touch the old until the new passes `verify`): cells via `replicator_cell.py plan/build/config` at new coordinates, then the unit scripts with their site constants moved.
3. Re-run `config` so the silo/orbital wires and the hub move over; run audit_replicator.py and replicator_hotspots.py; confirm a test order (e.g. 10 transport belts) completes.
4. Retire the old parts with deconstruction orders (robots; contents return to the network), then shrink the wall.
5. Rollback = the save, or rebuild the old site from the same scripts.

## Risks

- Another session owns replicator_viz (console) and has worked the cells; coordinate before moving either.
- The hub's silo wires are shared by four units: moving the hub last, once.
- Lattice substations and roboports in the old box are base infrastructure: keep them, wall only the Replicator.

## Progress (2026-11-14, evening)

Done (box 80 x 82 = 6,560 tiles -> 80 x 50 = 4,000 tiles; walls at x -366.5..-287.5, y -234.5..-185.5):
- Fluid-assembler unit moved from the south spill (-330,-178) to (-352,-192) inside the box (`scripts/repack_fasm.py`: retire by deconstruction, build with omni_fluid_asm, config re-wired; all 12 recipes wired, unit answers demand).
- Leftover compress test bench in the north strip deconstructed; console south row moved from y -192 to y -199 (`ROW_S` in replicator_viz.py).
- Wall: the two extension lines and the old internal south line removed, new south line at y -185.5 (`scripts/wall_extend.py`).
Not done: abut the 3 cells (x -358/-334/-310 -> -358/-337/-316; cell re-config follows the registry), pack hub/furnace/fluid unit/buffer into one row (replicator_viz.py hard-codes their positions: update it with them), narrow the console (it sets the box width), drop the lattice rows inside the box from the wall. Note: audit_replicator.py still reports MAKER 1-3 / ITEM LIST missing; that is the retired big block, not this repack.

## Correction (2026-11-14, after reading omni_fluid.py before building)

The second pass (replace the fluid unit's 112-decider table by a lookup bench) was oversold. It frees about 170 tiles (4% of the 4,000-tile box) and does NOT shorten the module row: that row is 13 tall because the fluid unit itself is 14 x 13, and the table is only 10 tall. Also, only the plant's solid requests (1 of the 8 outputs per recipe) can come from "read ingredients"; the barrel recipes and barrel counts of machines A/B/C/D are functions of fluid names, so they need a small per-fluid table and a rule for which fluid goes to A or B (the circuit cannot tell inputs apart). Real gain needs the fluid unit moved too: it would fit the free south-east corner (x -310..-289, y -198..-187, 22 x 12) only if it were one row shorter. Net: at most about 6 rows (300 tiles, 7%) for a live redesign of the fluid logic. Not done.

## Result of the hand-made layout (2026-11-14, with scripts/compact.py)
Walls now x -355.5..-288.5, y -235.5..-185.5 (inner 65 x 48 = 3,120 tiles; 6,560 at the start, 4,000 after phase 1: -52% overall), nearly square.
Moves made with compact.py (every one saved first, each verified): cells to x -352/-331/-310 (two hops each through the south-east scratch corner), a base-lattice substation that sat in the cell row moved to (-304,-200), the fluid-assembler unit split into fasm_core + fasm_table and shifted 6 east (site (-346,-192), config re-run: 12 of 12 recipes wired), console re-laid at pitch 2 (52 wide), walls rebuilt tight (`compact.py wall ... --clear-old`). Power: 0 `no_power` in the box before and after; all three cells verified, fluid unit status read.
Left over: a 33 x 9 free pocket at the bottom right (x -337..-289, y -198..-189) beside the fluid-assembler core; a further fold of the fluid-assembler table (48 wide) into two rows would let the box lose 6 columns. The 112-decider fluid table is still there (see the correction above).

## Third pass (2026-11-16, the Captain: "it still has lots of whitespace")
Walls now x -355.5..-288.5, y -235.5..-195.5 (inner 65 x 38 = 2,470 tiles; 3,120 before this pass, 6,560 at the start: -62% overall).
- The south band (12 rows holding only the fluid-assembler unit and its 48-wide table) is gone. Moved with compact.py (modules fa_core, fa_t1, fa_t2, fa_t3; save `pre-replicator-compaction-2`): core 27 north into the upper-left pocket (site (-346,-192) -> (-346,-219)); the table cut into strips of 12 + 12 + 24 slots at (-342,-225), (-342,-223), (-328,-220).
- `omni_fluid_asm.py` has `TABLE_FOLD` (site -> strips) so `config --at -346 -219` wires the folded table; `repack_fasm.py NEW` updated. Config re-run: 12 of 12 recipes wired, the unit chose tungsten carbide straight away (before the config it chose nothing: the last quality upgrade had dropped table wires).
- South wall moved from y -185.5 to y -195.5 (`compact.py wall`; note its box is the INNER box: the first try used the wall's own coordinates and laid a second ring west and north, removed again).
Left over: rows y -198/-197 hold only the unit's old substation (-341,-198): removing it would let the wall come up two more rows. Free pockets: x -354..-341 y -227..-226, the strip y -221..-218 west of the furnace, and the right third of the console rows.

## Fewer combinators for the same job: research notes (2026-11-16, the Captain's question; nothing built or tested)
Sources were thin: the Factorio forum threads (Sushi Mall, "programmable, scalable, bot auto mall, updated for 2.1", "Factory of the Future: a dynamic mall") sit behind a bot check and could not be read; only search summaries were available. So the list below is mostly our own analysis of the 2.x circuit features, to be proven on a bench.
Where the combinators are today: fluid unit table 112 deciders (8 a recipe x 14), fluid-assembler table 48 (4 a recipe x 12), each cell machine about 10, furnace table 5 (the "170" earlier in this file is stale).
1. **Per-fluid instead of per-recipe tables.** The maker machine can read its own ingredients (as the cells do), and that reading includes the fluid. So the table only has to turn a FLUID into its barrel recipe and barrel request: 2 deciders a fluid (about 5 fluids) instead of 4 a recipe. Fluid-assembler unit: 48 -> about 10. Chemical unit: inputs the same way; the two filling machines still need the product fluid, which "read ingredients" does not give, so about 112 -> 40.
2. **No combinator between machine and chest.** A machine's "read ingredients" wire can go straight to a requester chest set to "set requests" + "trash unrequested"; a combinator is only needed to scale the amount (one arithmetic, x BATCH). The read signals do not count for "set recipe", so one machine can do both on two wires. Check the cells: D1/A1/D2 and the ring exist to turn the chosen item into a recipe signal; if an item signal alone sets the recipe unambiguously for our menu, they go.
3. **Quality as a channel.** A signal carries a quality. One decider per recipe could put every target's signals on one wire, each target's set tagged with its own quality; each target then needs one selector (quality filter) and one selector (quality transfer back to normal). N + 2 x targets instead of 4N or 8N deciders. Unproven; a recipe signal's quality also sets the crafted quality, so the transfer back is mandatory.
4. **Packed table (bit fields).** One constant combinator holds, for every ingredient signal, the amounts of several recipes as digits of one number; two or three arithmetic combinators pick the chosen recipe's digit (divide by base^k, modulo base). A whole table becomes about 5 combinators a bank, but 32-bit numbers hold only 5-6 recipes a bank at our amounts. Most compact, most fragile: last resort.
5. **Share the demand filter in a cell.** The three machines of a cell each have their own demand decider and negator; one shared pair could serve all three (about 2 fewer a machine). Needs a look at the first-call logic first.
Order to try: 1 on the fluid-assembler unit (smallest, self-contained, a bench test proves it), then 2 on one cell, then 1 on the chemical unit. 3 and 4 only if those are not enough.

## Bench result: the per-fluid table works (2026-11-16, scripts/bench_per_fluid.py; the live unit is untouched)
Bench at Nauvis site (-192,-250) (map tag "BENCH per-fluid table"), north of the landing pad, same geometry as the fluid-assembler unit, demand faked by a constant combinator.
Proven with two recipes on different fluids: electric-engine-unit (lubricant) and processing-unit (sulfuric acid). In both, P took the recipe, its blue chest asked ingredients x BATCH
(20 circuits + 10 engines; 200 circuits + 20 red circuits), E took empty-<fluid>-barrel, E's blue chest asked the right barrels (3 lubricant, 1 sulfuric acid), and products came out
(22 electric engines, then processing units). Switching the demand switched everything with no rewiring.
- **Count for this unit:** old = 4 deciders a recipe (52 for today's 13 items; 48 on the live 12) + dec + sel = 54 combinators, 1 constant. New = dec, sel, D1, A1, D2 (item -> recipe signal), A (x BATCH), 2 a fluid x 5 fluids = **16 combinators, 2 constants**. The table no longer grows with recipes, only with fluids.
- **Wiring:** selector (chosen item) -> D1 (chosen AND rank list -> rank) -> A1 (sum to signal-R) -> D2 (ring of RECIPE signals == R -> that recipe, 1) -> P red (set recipe). P green (read ingredients) -> A (each x 10) -> P's blue chest; and -> per fluid a decider (fluid > 0 -> recipe empty-<fluid>-barrel -> E red) and an arithmetic (fluid / 5 -> <fluid>-barrel -> E's blue chest green). The makeable-item list doubles as the rank list (value = index).
- **Trap 1 (the one the plan warned of):** P puts its ingredient reading on BOTH wires, its set-recipe wire included, and it obeys those ITEM signals: fed the chosen item as an item signal, P set itself to electronic-circuit (an ingredient earlier in the item order) and asked for copper plate. A RECIPE-type signal on the wire wins over the item signals, so the item -> recipe lookup (3 combinators + the ring constant, as in the cells) is required. The search summary that "read signals do not count for set recipe" is wrong for item signals.
- **Trap 2:** `disconnect_all()` leaves wires made with `wire_origin.script`. A stale selector -> P wire fed the selector's output back into the demand decider and the count ran away (20 -> 6,400). Clear with `disconnect_all(defines.wire_origin.script)` as well.
- **Limit:** barrels asked = fluid x BATCH / 50, rounded down. Every fluid amount on today's list is a multiple of 5, so it is exact; a recipe with another amount would be short a barrel.
- **Not done:** the live unit at (-346,-219) still has its 48-decider table. Converting it means replacing `CONFIG` and `table_slots` in omni_fluid_asm.py with the bench wiring and removing the table strips. The bench stands idle (demand cleared); remove it with `bench_per_fluid.py remove --apply`.

## Live conversion: the fluid-assembler unit runs on the per-fluid table (2026-11-16; save `pre-fasm-per-fluid-live`)
The unit at site (-346,-219) was switched with `omni_fluid_asm.py config --at -346 -219`, which now places and wires the per-fluid design for every site in `PER_FLUID`.
- **Combinators:** 50 (48 table deciders + dec + sel) and 1 constant before; **17 combinators and 2 constants** now: dec, sel, D1, A1, D2, A (x BATCH), H (round-up helper), 5 fluid deciders, 5 fluid arithmetics; item list (also the rank list) and the ring.
- **Where:** the new row of 14 stands on tiles x -354..-341, y -227..-226 (free pocket under the hub); H at (-354,-225), the ring at (-353,-225). The three table strips are gone (`retire-table --apply`: 48 deciders, none still wired): 96 tiles freed at x -342..-331, y -225..-222 and x -328..-305, y -220..-219; the new parts take 31 tiles of ground that was empty. `TABLE_FOLD` is kept only for `retire-table` and `--old-design`.
- **Proven live** with an injected demand (nothing on the unit's list was in demand on the hub at the time; the injection was a temporary constant combinator on the demand decider, removed afterwards): electric-engine-unit (lubricant), processing-unit (sulfuric acid), express-transport-belt (lubricant again). Each time P took the recipe, its chest asked ingredients x 10, E took the matching empty-barrel recipe, its chest asked the right barrels (3, 1, 4) and products reached the red chest. The demand decider is back on the hub roboport's red wire.
- **Deadlock found and fixed:** an emptier that is blocked with a FULL fluid box (`full_output`, 1,000 lubricant left from before) does not change recipe, so the first switch to sulfuric acid hung. This was already true of the old design. E was flushed once by hand (`clear_fluid_inside`, 1,000 lubricant lost), and the new wiring caps it: E reads its contents on green and its feed inserter runs only while everything < 400, so the box never fills. Seen working (420 lubricant, inserter disabled).
- **Barrels round up:** barrels = (fluid + 4) / 5 for BATCH 10 (the helper adds 50/BATCH - 1 before the divide), so an odd fluid amount is never a barrel short.
- **`config` now:** per-fluid design at PER_FLUID sites (places missing parts, clears player and script wires, re-wires everything, re-writes the item list and the ring from the game's recipes: a new recipe needs only a re-run, no new combinator unless it brings a sixth fluid; the row holds 5). `--old-design` runs the old table wiring, which no longer fits here (13 recipes, 48 slots) and has no table left to wire: it is the code path for other sites (Fulgora's superconductor unit), not a rollback for this one. Rollback here = the save.
- **Not verified:** a run against real hub demand (none of the 13 items was demanded); behaviour after a quality upgrade (wires are player-origin `connect_to` without reach check, as before); a burner maker (`--fuel`) is refused by the new design. compact.py modules fa_t1, fa_t2, fa_t3 now describe empty ground. The bench at (-192,-250) still stands.

## Chemical fluid unit on the per-fluid table: bench, then live (2026-11-16; saves `pre-bench-chem-per-fluid`, `pre-chem-per-fluid-live`)
`omni_fluid.py config --site replicator` now builds and wires the per-fluid design (sites in `PER_FLUID`); `--old-design` keeps the 8-a-recipe table path.
- **Combinators:** 114 (112 table deciders + dec + sel) and 1 constant before; **28 combinators and 3 constants** now. The saving is 75%; the earlier estimate was 112 -> about 40.
- **Tiles:** the two table blocks are gone (`retire-table --apply`, 112 deciders, none still wired): 224 tiles freed at x -323..-307, y -231..-222 and in the row y -215..-214. The 26 new combinators and 2 ring constants take 54 tiles on ground the fluid-assembler conversion had freed (x -328..-305, y -220..-219; x -342..-339, y -225..-224; rings at (-338,-225), (-337,-225)). Net 170.
- **How it works:** plant = recipe-type signal from the item -> recipe lookup (D1, A1, D2, ring) and its own ingredient reading x 10 -> its blue chest. Inputs: three deciders split the plant's fluid reading into a first-input bus and a second-input bus (rule read from the recipe list: every two-fluid recipe starts with the same primary fluid, water; a single fluid is the first input), each bus gets a round-up helper, then per fluid one decider (empty-barrel recipe) and one arithmetic (barrels): 5 first-input fluids, 3 second-input fluids.
- **How the product fluid is found:** not from the plant. "Read contents" shares its wires with "read ingredients" (the two readings add up on both wires, so they cannot be told apart), and a pipe cannot be read. So a second ring constant holds, per recipe with a fluid product, the FILL recipe (named like the barrel) at that recipe's rank, and one decider compares it with the rank signal the lookup already makes: 1 decider + 1 constant for all recipes. A recipe-type signal is needed there too, because the filler C reads its own contents (barrels) on its set-recipe wire. D is unwired: no recipe today has two fluid products, and `config` refuses a list that has one.
- **Caps:** A, B and C read their contents; the feed inserters of A and B run only while everything in their own machine and in C is under 400. Seen working on B (480 light oil, feed disabled).
- **Bench** (site `bench`, plant (-246,-309), map tag "BENCH per-fluid chemical unit", left standing, demand cleared): sulfur (water + petroleum gas, solid product: 46 made), light-oil cracking (water + light oil -> petroleum gas barrels: filled), plastic bar (one non-primary fluid: routed to A, chest asked coal; product not waited for), sulfuric acid (water + solids -> acid barrels: 4 filled).
- **Live** (injected demand, removed afterwards): sulfur (44 made), petroleum-gas barrels by light-oil cracking (3), sulfuric-acid barrels (3). Then, back on the hub roboport's red wire, REAL demand chose carbon (850 missing) and 10 carbon came out.
- **Found on the way, both older than this change:**
  1. *Stale pipe fluid.* The one pipe tile between B and the plant's second input keeps its fluid when the recipe changes; the next second fluid cannot enter (petroleum gas left from sulfur blocked light oil). No circuit can empty a pipe. `omni_fluid.py flush --site replicator` (function `cycle()`) clears it when it holds the wrong fluid, and it is NOT yet called by the autopilot: until it is, a change of second-input fluid (heavy oil / light oil / petroleum gas) hangs the unit. The D-side pipe is flushed only when it holds something other than the plant's current product.
  2. *B faced north on the bench.* place_entities ignores an assembler's facing, so B's fluid never reached the pipe; `config` and `flush` now turn B east and D west. The live B already worked.
  3. *A was deadlocked* with 1,000 petroleum gas (full box, cannot change recipe): flushed once by hand; the cap prevents a repeat.
- **Not verified:** heavy-oil recipes (no heavy-oil barrels in stock: cracking, lubricant, solid fuel), crude oil (flamethrower ammo), fish breeding; a plant blocked with a full PRODUCT box when the filler has no empty barrels or a full red chest (the cap watches C's contents, but a plant that is itself blocked was not provoked); behaviour after a quality upgrade. Rollback = the save (the old table is gone).

## Parity test and baseline (2026-11-16, scripts/replicator_parity.py; baseline in snapshots/replicator_parity.json)
The loop is analyze, simplify, edit, compact, TEST FOR PARITY, repeat. `replicator_parity.py run` stores a baseline, `compare` runs the same orders and prints a table against it
(same unit, same recipe, as many crafts, done within 1.5x and 900 ticks, no more machines on one item than before). Orders arrive as a temporary constant combinator on the hub's
red wire, removed after each order. Target 3 crafts, timeout 18,000 ticks. The chemical unit's pipe flush runs before each order, as the autopilot now does every second cycle.
Baseline (ticks to first product / to 3 crafts): cell1 arithmetic-combinator 842/842; cell2 assembling-machine-1 387/1,587; cell3 constant-combinator 777/777;
fasm electric-engine-unit 897/897; fasm processing-unit 1,222/1,222; chem sulfur 292/292; chem sulfuric-acid-barrel 742/2,837; chem plastic-bar 1,737/1,737;
batch of three: 741, 831, 1,566. Box: 17 machines, 141 combinators, 12 constants, 365 entities, 708 built-on tiles of 2,442.
Findings on the CURRENT build (not fixed in this job):
1. **Furnace unit does not see demand:** stone-brick was never taken. Its demand decider at (-325.5,-223) has no wire on its red input (the hub demand).
2. **Nested order stalls:** piercing-shotgun-shell was taken by cell1 (chest asked 10 shotgun shells, 0 in stock), but only 2 shells existed after 5 minutes and nothing was made.
3. **A cell puts all three machines on one order:** every cell order showed 3 machines holding the same recipe at once (13, 11 and 4 crafts made for an order of 1).

## Parity faults fixed, new baseline (2026-11-16, save `pre-parity-fixes`)
1. **Furnace unit deaf:** its demand decider had lost the wire to the hub roboport (a long wire, dropped when a quality upgrade replaced the combinator). Fixed the scripted way: `omni_maker.py furnace replicator --config` (5 table entries re-wired). Stone brick is smelted again.
2. **Nested order stalled:** the chest's request did reach the hub wire (shotgun-shell 30) and cell2's rank list holds shotgun-shell. The cause was fault 3: all three machines of cell2 sat on one order, efficiency module 3, which cannot be made on Nauvis (its chests wait for spoilage), and the +10 hold kept them there, so the partition made nothing else.
3. **Three machines on one order** is a design gap, not a setting: nothing kept machine 2 and 3 off machine 1's choice. Fix in `replicator_cell.py` (SPREAD): machines 2 and 3 have one more decider each that subtracts 500,000 from the score of what the earlier machines chose (m2 sees m1; m3 sees m1 and m2). Another demanded item always wins; with nothing else demanded they still join the big order, so a large single order keeps its three machines. `config` places the two deciders if missing. An order of 1 with no other demand is still made by more than one machine (2 at once in the test, 3 before): the overshoot comes from BATCH and from machines not reserving an order; a real fix needs a claim signal and is left.
4. **Found by the first compare:** the autopilot's quality upgrade had turned the new epic control combinators of both fluid units legendary and dropped their long wires (every chemical order and the acid order failed). `omni_fluid.cycle()` (the autopilot hook) now also checks the control of the chemical unit and of the fluid-assembler unit and re-runs their config when a combinator has lost all inputs or all outputs. The cells and the furnace unit have no such check yet.
Compare after the fixes: 13 of 13 orders pass. Differences against the old baseline: furnace (now works), cell2 slower (2,530 vs 1,587 ticks: two machines on the order instead of three, and robot flights).
New baseline stored from that run (snapshots/replicator_parity.json; the old one is kept as replicator_parity_baseline_old_2026-11-16.json): 147 combinators, 368 entities, 708 built-on tiles.
