# Compaction routine (scripts/compact.py) — lossless squeeze of any block of machines

Captain's order 2026-11-14: "script an easy routine that does this so that we'll be able to use it in the future." The routine moves whole modules (a cell, a unit, a chest field) to new positions without rebuilding them from their own scripts.

## How a move works
`surface.clone_entities` copies every entity of the module with its recipe, modules, chest requests, inventories and all wires BETWEEN the copied entities (tested live 2026-11-14 on test entities and on a real Replicator cell, round trip: moved 49 entities, re-attached 17 external wires, the cell kept making items and its counters, undone cleanly). Before cloning, the script records every wire that goes from the module to something OUTSIDE it (hub roboport, silos, lattice substations); after cloning it re-attaches each of them to the copy. Only when all copies exist and all wires re-attached does it destroy the original. Aborts leave the original untouched. `move --apply` saves the game first (`pre-compact-NAME`).

## Use (bash, PYTHONPATH=scripts)
```bash
python scripts/compact.py survey X1 Y1 X2 Y2          # ASCII map + how much of the box is built on
python scripts/compact.py list                         # registered modules (snapshots/compact_modules.json)
python scripts/compact.py define NAME X1 Y1 X2 Y2 [--exclude substation,roboport] [--part x1,y1,x2,y2 ...] [--skip x1,y1,x2,y2] [--post "note"]
python scripts/compact.py check NAME                   # names/counts inside + which wires leave (review before moving)
python scripts/compact.py move NAME DX DY [--apply]    # dry run first: checks the destination for foreign entities
python scripts/compact.py plan --at X Y [--width W] [--gap G] [--order a,b,c]   # naive shelf packing of the registered modules (a starting point, edit offsets by hand)
python scripts/compact.py run [--apply]                # the plan's moves, deferring any whose destination is still occupied
python scripts/compact.py undo NAME                    # reverse the last recorded move
python scripts/compact.py wall X1 Y1 X2 Y2 [--clear-old] [--apply]   # epic stone-wall ring just outside the box
```
A module whose parts interleave with other things (the fluid unit's two table blocks) is several `--part` rectangles moved rigidly together. `exclude` keeps base lattice (substations, roboports) out. A move whose destination overlaps the module's own source is refused: use two steps.

## Registered for the Replicator (snapshots/compact_modules.json)
cell1, cell2, cell3 (verified live), fasm (fluid-assembler unit), buffer, furnace_unit, fluid_unit (two parts, 142 entities, 2 wires out), all but the cells marked UNVERIFIED until a `check` + a move has been seen working. The hub roboport (-352,-229) is not registered: its wires are the external ones every module re-attaches to, so it can be moved last as a module of its own.

## What a clone cannot carry (the `post` notes print after a move)
Constants in other scripts: replicator_viz.py hard-codes the cells, the fluid unit (C,CY) and the furnace unit; omni_fluid.py `SITES`, omni_maker.py `SITES`, repack_fasm.py; the cell registry is edited by the `cellreg:` hook. After moving a module: update those, run the unit's `config`/`verify` (replicator_cell.py verify NAME, omni_fluid.py status, audit_replicator.py).

## Known limits
- `plan` packs bounding rectangles in shelves; it does not know about base lattice in the target area or about the console rows. Treat it as a draft; the Replicator target (docs/replicator-compaction-plan.md) still needs a hand-made layout.
- Pipes, belts and fluid-connected machines clone fine but their fluid contents reset; check connections after moving anything piped (the fluid unit has only 2 pipe pieces, barrel-fed).
- Poles: copper wires to neighbouring poles are re-attached like circuit wires; check `no_power` after a move (factory_problems).
