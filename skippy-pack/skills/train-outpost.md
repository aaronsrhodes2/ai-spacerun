# Skill: one patch to the bus by train (iron, copper, stone, coal)

Needs: a cleared patch (discover-and-clear), the registry entry for the next free yard row and bus lane.
1. Pick the output direction that faces the bus (`--out N|S|E|W`). Iron and copper: `--furnaces N` with N = ore per second / 0.625 (one outpost with one express belt caps at 72 furnaces, 45 plates/s); stone, coal, uranium ore: `--furnaces 0`.
2. `train-outpost ... --stage plan` (dry run: counts, station position, parity). Then `--stage outpost --apply`.
3. Yard row: rows are y=-121, -133, -145, -157, -169, ... `yard-lane yard --y Y --name "Bus <Resource> Unload"`. The yard unloads into red provider chests (drones carry the cargo on), so the row needs roboport cover and the outpost needs to be on the main electric network.
4. `yard-lane stub` at the outpost (dead end three tiles behind the stop, run 41 tiles), then name the stop `<Name> Load` with `find_stop`.
5. `rail-line --start <stub end> --goal 250 Y W --min-run 16`. If it stops half way, finish with `rails.route` and the printed legs.
6. Train: 2 locomotives and 4 cargo wagons at the stop, 150 coal each, schedule load (full or 3600 ticks) then unload (empty or 600 ticks).
7. Power: the autopilot guard lists outposts; add the outpost box to `OUTPOSTS` in `scripts/autopilot_server.py` and restart the autopilot.
Verify: plates (or ore) on the station belt, train loading, and after the first visit the yard's provider chests hold cargo. Not verified until the cargo moved. `audit` quiet.
Rules learned the hard way: one train per track (no signals); rail line parity must be odd; the belt jogs a tile if needed (the script does it); nests near the track must be destroyed before laying; an unloading inserter stands on the tile next to the rail (rail centre y, inserter y+1.5), one tile further and it reaches nothing.
