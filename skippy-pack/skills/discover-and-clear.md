# Skill: find patches, clear them, floor them

Goal: every resource patch has a cleared, floored area around it and a cleared strip to the next patch or the bus, ready for rails.

1. `discover`: list patches (resource, tiles, amount, centre, distance to the bus, nests within 100 tiles). Record them in `state.json` registry as `patches[]`. Skip stone unless a shortage is reported (the Captain's rule).
2. For each patch, the clearing box is the patch bounding box plus 30 tiles (furnace block and station need room on the output side; for iron and copper a second box of 60 by 100 beside it).
3. `clear --area BOX --all`: trees, rocks, cliffs, decoratives, enemies. Enemies are removed directly (god mode); the Captain said "take care of biters with mines", so if land mines are researched and wanted, ask before using them instead.
4. **Never remove the crash site** (`crash-site-spaceship*`, about (-5,-6)). It is not near any patch, but never use `--all` within 100 tiles of (-20,0) without the exclusion in place (gap: add `name:find('crash-site')` skip to `fx.py clear`).
5. `pave --box BOX`: refined concrete. Skips ore tiles and water.
6. Strip to the next patch: clear a 12 tile wide corridor along the planned rail; `rail-line` clears natural pieces itself, so only do this by hand if you want it paved.
Verify: natural entity count in the box is 0 (`count_entities_filtered` for tree, simple-entity, cliff, enemy), sample tiles are concrete.
Rollback: the save named `before-clear` / `before-paving`.
