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
