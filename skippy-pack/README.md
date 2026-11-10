# skippy-pack: scripts and skills for an agent that solves Nauvis and white science

Status: framework only (2026-11-09). Nothing here was run as a package; every command wraps a script that already ran in the Captain's game, except the ones marked `gap`.

## How a local model uses it
1. `python skippy-pack/nauvis.py next` prints the next step, its exact command, how to verify it, and whether it exists.
2. Run the command as a dry run (no `--apply`). Read the JSON. If it is clean, run it with `--apply` (the script saves the game first and says the save name).
3. Run the verify check. If it passes: `nauvis.py done STEP`. If not: roll back to the named save and report to the Captain. Never improvise a build the pack does not list.
The model never writes Lua or coordinates. Geometry lives in the scripts; the model chooses which script, which patch from `state.json`, and reads a verdict. That keeps each prompt small enough for a local model.

## Files
- `manifest.json` every command: what it does, status, caveats, verify, rollback
- `milestones.json` tech -> actions ("after you research X, run Y")
- `nauvis.py` the dispatcher described above (read only, never touches the game)
- `skills/` one short page per job, the rules an agent must follow for it
- `state.json` created on first use: steps done and the registry (patch coordinates, yard rows and bus lanes in use, station names)

## Guard rails (apply to every step)
- Dry run first. `--apply` saves the game. One build at a time, verify before the next.
- A permission or classifier denial is reported, never worked around. No scheduled tasks or services on the Captain's machines.
- Placed entities and tiles are free but only once researched; machine inputs must be produced by the factory; never write research state (queueing is fine).
- Chest rules: yellow storage only in trash yards, red at the end of a line, blue at the start, steel inert.
- Never touch the crash site (about (-5,-6)). Never remove what you did not build without asking.
- Power first: a build that adds load runs behind the power guard (autopilot) and is paused when accumulators run low.

## Known gaps (the honest list)
science-rates command, a one-call `discover`, crash-site exclusion in `clear`, signals and junctions for rails, fluid unload script, uranium with acid, nuclear plant and breeder builders, the space platform, a first-planet pack.
See `docs/purple-skippy-plan.md` for the plan to close them in order.
