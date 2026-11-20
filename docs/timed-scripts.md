# Timed scripts

Every script that runs on a timer, why it exists, and when it can be retired. A timed script is a patch over something the factory's
own logistics do not do yet; the goal is an empty list. Keep this file current: a new timed step gets a row in the same change.
Rule approved by the Captain, 2026-11-20 (see the skill's working rules).

## The autopilot (`scripts/autopilot_local.py`, one cycle about a minute, on skippy-pc)

| Step | Every | Purpose | Retire when |
|---|---|---|---|
| research top-up (`ap.TOPUP`) | cycle | keeps the research queue filled | the Captain queues research by hand, or the mod's queue does it |
| snapshot (`ap.SNAP`) | cycle | one status line for the log | never (read-only) |
| repair (`ap.REPAIR`) | cycle | revives destroyed entities' ghosts | every surface has repair robots and stock |
| silo guard (`ap.SILO_GUARD`) | cycle | keeps silos from wedging on a half load | silos are driven by requests only |
| ship guard (`ap.SHIPS`, `SHIP_GUARD`) | cycle | unsticks shuttles whose leave rules can never come true | each shuttle has a timed fallback on every stop (fleet rework) |
| oxidizer wire (`OX_WIRE`) | cycle | rewires hub tank readings lost in quality upgrades | upgrades keep wires, or the fleet is rebuilt from one blueprint |
| robots (`ROBOTS`) | cycle | swaps robots below the best quality | all robots legendary |
| reactor (`REACTOR`) | cycle | hand-feeds a fuel cell | every reactor has a fed inserter |
| chart (`CHART`) | 3 cycles | charts every area we build on, so the Captain can see it | a radar or roboport covers every built area |
| factory wall (`factory_wall.py`) | WALL_EVERY | status panels near the silos | never (display) |
| Replicator console (`replicator_viz.py`) | VIZ_EVERY | display of the Replicator's state | never (display) |
| fluid unit flush (`omni_fluid.cycle`) | 2 cycles | empties the one pipe tile that keeps the last recipe's fluid | the fluid unit is rebuilt port to port, with no pipe tile |
| Replicator list refresh (`replicator_cell.refresh_all`) | REFRESH_EVERY | new research changes what the cells may make | research is complete |
| ghost demand (`ghost_demand.update`) | 3 cycles | Nauvis ghosts become a requester chest's requests | the mod's ghost-to-request logic (0.19.0) runs in the live game |
| drone supply (`robot_network.cycle`) | 3 cycles | orders and feeds robots to roboports | roboports request robots themselves on every surface |
| Aquilo build logistics (`aquilo_build_logistics.cycle`) | 5 cycles | ghost needs to ship kit sections, ammunition top-up | Aquilo's pad and one stable shuttle carry it by request |
| island trim (`island_legendary.cycle`) | 2 cycles | voids junk in the Fulgora island's provider chests | the island voids by recycler loop on belts |
| ghost requests (`ghost_requests.cycle`) | 5 cycles | ghost shortfalls become landing-pad requests on every planet | the mod's ghost-to-request logic runs in the live game |
| Aquilo floor requests (`request_tidy.tiles`) | 5 cycles | pad and shuttle requests follow the floor-tile ghost count | Aquilo's floor ghosts are all built (retires itself at 0) |
| Replicator demand watch (`replicator_demand_watch.sample`) | cycle | flags steady consumers that need a dedicated line | never (read-only) |
| Gleba cell (`gleba_cell.watch`, `gleba_restart.cycle`) | 2 cycles | balances fruit caps, restarts a stalled cell | the cell runs a long test without a restart |
| Gleba stability watch (`gleba_stability.sample`) | 3 cycles | samples, alarms, heals | same as above |
| depleted return (`depleted_return.cycle`) | 2 cycles | spent fuel cells home to Nauvis | a ship request does it |
| module mall (`module_mall.LABS`, `INSTALL`) | cycle | modules into labs and wheels | modules are placed by request proxies and robots |

## Hand-kept tables (not timed, but they go stale)

| Script | Purpose | Retire when |
|---|---|---|
| `ghost_carriers.py` | ship and pad requests for ghost materials and the foundation line | ships carry menus (order carrier) on every route, or the mod writes route requests |

## Windows tasks on skippy-pc

| Task | Purpose | Retire when |
|---|---|---|
| Release stuck Ctrl at login | frees a stuck Ctrl key left by input automation | input automation is gone |
| night run (Claude scheduled task, one-off, 2026-11-21 03:00) | mod test with the local model | after it runs |
