# Finding and fixing production bottlenecks like bugs (plan, 2026-11-08)

## What the last day of manual debugging showed
Every stall was one of five bug classes, and every one was found by the same three questions: which machines are not working, what exactly are they missing, and where is that item stuck upstream.
1. **Contamination**: the wrong item on a lane (iron on the copper lane, plastic on the circuit lane, sulfur on the plastic lane). A lane jams because nothing downstream eats the intruder.
2. **Wrong direction / orphan**: an inserter facing the wrong way (4 steel furnaces idle), a belt that ends in nothing (yellow packs), a machine whose input faces the wrong side.
3. **Upstream-of-producer**: a consumer tapping a trunk north of where the item is put on it (EC and AC for yellow). Trunks flow south, so this can never work.
4. **Wrong machine type or recipe unset**: battery in an assembling machine (needs a chemical plant).
5. **Real capacity**: genuinely not enough plates, steel, trains, or machines. Only after 1-4 are ruled out.

## The tool: scripts/bottleneck.py (proposed, one command, read-only)
A. **Ledger** (production statistics, 1 min): made vs used for every item on the science tree. Lists items where used > made (true shortage) and items where made >> used (surplus backing up = somewhere downstream is blocked).
B. **Machine census** by recipe: counts per status, and for every machine in item/fluid shortage the exact missing ingredient (already prototyped, one Lua call). Output example: `4x military-science-pack <- missing piercing-rounds-magazine`. Follow the arrow upstream automatically: the missing item's producer becomes the next row to inspect, until it reaches a producer that is working (the real limiter), idle with full output (blocked downstream), or missing a raw input.
C. **Lane audit**: a table of every belt trunk and branch with its design lanes (T0 steel|AC, T1 copper|iron, T2 EC|plastic ...). Sample each lane every few tiles; flag any item outside its allowed set, and any lane that is full and stationary with no consumer for its head item.
D. **Wiring lint**: inserters whose pickup target is a machine output and drop target is a machine input for the same machine (backwards), belts whose last tile has no consumer and a stationary lane, machines whose fluid recipe has no connected pipe, recipes unset, chemistry recipes in assembling machines, consumers tapping a trunk north of the item's give row.
E. **Flow check**: for each science pack, trace pack machine -> belt -> port -> wagon -> lab: first place where the count of packs on the path is zero downstream of a non-zero.

## Fixing like bugs
Each finding is a ticket: `id, class (1-5), where (x,y), evidence (the numbers), proposed fix, status`. Fix recipes already known:
- contamination: add a side-load dummy belt (never let a curve carry a two-lane feed into a shared trunk), add a filtered splitter at the entry, clear the jam with a one-off Lua `remove_item` on all lines (including underground lines 3,4).
- backwards inserter: rotate it.
- upstream-of-producer: new tap below the give row plus a filtered sorter and a belt back (done for EC and AC into the yellow block).
- capacity: add machines/trains only when the ledger says used > made with every stage upstream working.
Regression: every fix adds one check to the lint (so the same bug cannot come back silently), and the tool runs after each build and prints "0 new findings".

## Decision for the Captain
Build scripts/bottleneck.py (A+B+C first, about an hour, read-only, no risk), then add D and E. Option: run it on a schedule and have it tell you in-game (`tell_player`) when a class 1-3 bug appears.

## 2026-11-17: the "electronic circuit shortage" was a burst, and the ranker now says so
Finding as ranked: electronic-circuit made 62.5/s, used 136.7/s (one-minute ledger), stock 362,062, "lasts 1.4 h".
What the game shows:
- Windows (made/used per second): 1 min 57.5/36.3 a few minutes later, 10 min 55.6/60.3, 1 h 51.1/49.6, 10 h 52.9/51.1. Use and production are level; the 137/s was one busy minute.
- Makers: 46 circuit assemblers with about 800/s of capacity. 29 stand on full output, 4 work, 13 wait for an ingredient (10 copper cable, 2 iron plate; the y -60 row and two at (-244|-241,-235)). Capacity is about 15 times the use.
- Users: 53 advanced circuit assemblers (9 working at the reading, 27/s), 21 productivity module and 10 speed module assemblers, 14 processing unit assemblers and the Replicator one-offs. The module makers run in bursts.
- Stock: 362,062 at the first reading, 370,613 about 25 minutes later (rising). Robots 35,319 of 40,462 free.
Conclusion: no capacity or collection fault, nothing built. The fault was in the measurement.
Change: `scripts/worst_bottleneck.py` reports `short` only when use exceeds production in BOTH the one-minute and the one-hour window, scores the one-hour deficit, and drops the finding when the stock has not fallen since a reference reading at least 5 minutes old (`snapshots/bottleneck_stock.json`, reference replaced hourly). Tests: `tests/test_bottleneck_short.py`.
Still open (not circuits): iron plate reads 57 made / 88 used over the hour. The ledger does not count plates that arrive from orbit; the stock fell from 1,195,293 to 1,189,548 in about 25 minutes (about 4/s), far less than the ledger deficit of 30/s, but it moves in lumps (it dropped 700 in one 20 second stretch), so that rate is a rough reading. The stock-trend rule keeps or drops this line from the second run on.
Five-minute check after the change (18,406 ticks): circuits made 14,558 (47/s), used 20,978 (68/s), stock 371,244 -> 364,828. The stock does fall in a busy stretch, and that is by design: the stock IS the makers' output chests. 14 makers feed passive provider chests of 24,000 (13 of them full), 15 feed chests barred at 5 slots (600 to 800), 4 feed a full belt at (99..105,-85). A maker runs only when robots have taken from its own chest, so production follows use with a lag and the total floats just under full. Third rule added to the ranker for this: an item with 4 or more of its own makers idle on full output is never `short` (`SPARE_MAKERS`).

## Factory check 2026-11-17: requests that filled hubs and the Aquilo pad (`scripts/request_tidy.py`)

Found by reading the game alerts first, then the ranker. No power fault on any surface.

- **Dead floor cargo.** Nine Nauvis shuttles carried 1,000 to 2,000 refined hazard concrete each (`floor-hub-ng|nv|nf`) for block floors that are finished: Gleba, Vulcanus and Fulgora have no tile ghost. Nauvis-Gleba 2 Shuttle had 0 of 109 slots free (alert "no platform storage"). The groups are now drops at the destination (min = max = 0). Not yet seen unloading.
- **Aquilo pad flood.** Fulgora-Aquilo 5 Shuttle dropped 500 holmium plate, 600 tungsten plate and 500 tungsten carbide every trip whatever the pad held (26,594 / 7,800 / 15,204; pad 82% full). Those slots left `aq-drop-39`; the pad asks for keep levels instead (`aq-keep`: 2,000 / 1,000 / 1,000).
- **Aquilo floor tiles.** 7,848 refined concrete and 1,534 hazard concrete ghosts, no stock. `tiles()` writes the pad request (`aq-floor`) and the lift requests (`floor-hub-fa` from Fulgora, `floor-hub-ga` from Gleba's unused 2,640) from the live ghost count, 10% over, and removes them at 0 ghosts. The autopilot calls it every fifth cycle after its next restart. Refined concrete comes from the new Fulgora line (`scripts/fulgora_refined.py`). First 360 tiles were laid within the hour.
- **Aquilo east edge.** 2,404 concrete and 1,908 ice-platform ghosts at x 84..111 were outside construction range with 9,763 platforms in stock. One legendary roboport at (56,3): on the heat pipe at x 53.5, inside the substation at (41,6), joined the main network; robots started at once.
- **Not faults.** White Science is paused with 94k packs aboard and 184k on Nauvis (surplus). Nauvis circuits and Fulgora storage: see the sections above and `docs/planet-replicators-plan.md`.
- **Open.** Edgerunner hub 4 of 59 slots free with plates in its trash slots; iron plate on Nauvis may be a slow real drain (57 made, 88 used a second over an hour, orbit deliveries not counted); Gleba pack headroom is 1.24x, not 2x.

## Fulgora-Aquilo 5 Shuttle stranded at Aquilo (2026-11-18)
- Found: at Aquilo, 0 explosive rockets, all 14 rocket turrets empty, 29 damaged pieces, big asteroids round it. No fuel burned and nothing killed for over ten hours.
- Cause: the Aquilo landing pad was full (980 slots: 15,108 tungsten carbide, 26,294 holmium plate, 7,776 tungsten plate, 4,584 low density structure, ...). The shuttle held 100 barrels as trash it could not drop, and a platform does not leave with undroppable trash. It stood there with every wait condition met and shot until its rockets were gone. Proven: with the trash moved back into the hold and the two drop sections (`aq-drop-39`, `aq-ghostdrop-39`) switched off it left after the normal 90 seconds.
- Second cause, of the rocket shortage behind it: only Nauvis makes explosive rockets (292,000 in fifty hours), a rocket lifts 25, and this shuttle used 272,000 in fifty hours against 18,800 for Gleba-Aquilo 1. Fulgora, Gleba and Aquilo held none.
- Done: Gleba-Aquilo 1 was sent to Aquilo and handed over about 2,300 rockets hub to hub (`scripts/shuttle_handover.py`); it got home to Gleba with 64 left and no damage. Fulgora-Aquilo 5 is paused at Aquilo, armed (about 1,700 rockets), its two drop sections OFF. Gleba-Aquilo 1 now waits at Gleba for 3,600 rockets that Gleba does not have.
- Open: the full Aquilo pad; the fleet rework the Captain ordered the same day (ships stable when parked at either end, a timed fallback on every stop, ammunition and power made on board, fusion where it can be shipped).

## Fleet rework, part 1: timed schedules and what was pinning ships (2026-11-18, the Captain's order)
Order: every shuttle stable when parked at either end, timed runs, running requirements only, cargo as wants; one design for inner and outer runs.
- `scripts/fleet_survey.py` (read-only) and `LuaSchedule.ticks_in_station` showed how long each ship had stood. Five were pinned:
  - Nauvis-Gleba 1, 3 and 6 at Nauvis for 30 hours: every furnace held 3 iron PLATES in its input slot (waiting for 5 to make steel), so no magazines were made and the count never reached the 800 the schedule asks for. Cause of the plates not found.
  - Courier 1 at Vulcanus for 99 hours: no oxidizer tank on the hub's wire, so the oxidizer condition was never true.
  - Nauvis-Vulcanus 1 and Nauvis-Fulgora 2 at Nauvis: trash they could not drop, because the Nauvis landing pad was full (49,986 tungsten carbide in 1,000 of 1,280 slots).
- Fixes, `scripts/fleet_unpin.py` (furnaces | oxidizer | trash | pad PLANET): plates moved to the hub (8 ships, 16 furnaces), oxidizer tank wired, trash put back in the hold with the drop sections switched off, and "trash unrequested" turned on for the Nauvis and Aquilo pads so robots carry unrequested goods to storage. Nauvis pad: 2 free slots -> 1,128 within two minutes. All five ships moved again.
- `scripts/fleet_rework.py apply`: 14 inner shuttles and the courier now leave a stop on "fuel, oxidizer and own magazines ready, and (cargo wants met or cargo quiet for 60 s), and 30 s" OR "fuel, oxidizer and magazines ready, and 900 s at Nauvis / 300 s elsewhere". The two Aquilo shuttles are skipped: their conditions need planet-fed rockets, uranium rounds and repair packs.
- Aquilo shuttles 38 and 39: rocket turrets set to big asteroids only, guns to medium then small.
- Open: the drop sections switched off on ships 7, 10 and 39 (their cargo now stays aboard until a pad asks for it); what puts plates into furnace inputs; the universal self-supplying hull (prototype under way, `scripts/universal_shuttle.py`).

## Aquilo Wheel: a depot for the shuttles (the Captain, 2026-11-18: "We need an Aquila wheel"; job chosen: depot)
Job: a defended station in Aquilo orbit that makes explosive rockets, magazines and fuel there and hands them hub to hub to any shuttle that arrives short (`providing_to_other_platforms`, proven with `scripts/shuttle_handover.py`).
Read from the game:
- Aquilo orbit spawns, per tick: big oxide 0.0025, big carbonic 0.00025, big metallic 0.00013; loose chunks oxide 0.001, carbonic 0.0001, metallic 0.00005. Big asteroids arrive 2.5 times as often as chunks and nine tenths of everything is oxide. Sun 60%.
- Fulgora-Aquilo 5's kills over fifty hours: 35,417 big, 121,142 medium, 347,852 small oxide: one big becomes about 3.4 medium and about 10 small.
Estimate (not measured): a big killed with big-only rocket targeting costs about 3 explosive rockets, which is about 0.6 carbonic chunk with the module set the autopilot fits. Its fragments give 5 to 10 oxide chunks if they are all shot and collected; an oxide chunk reprocessed to the end yields about 0.33 carbonic and 0.33 metallic chunk. So the station pays for its own rockets about three times over, PROVIDED it collects the fragments and reprocesses oxide. Magazines for the medium fragments take about 1 metallic chunk a big; small fragments should go to lasers.
Design consequences: collectors all round (fragments are the income), oxide reprocessing as the main line, rocket turrets big only, guns medium, lasers small; lasers want real power, and the fusion cell factory is on the planet below. It has to arrive armed and stocked: nothing can be built up under fire from nothing.
Plan: build it at Nauvis as a large version of the universal shuttle (same works, more of them, engines), prove it parked there, stock its hub, then fly it out once and park it at Aquilo. It waits on the universal shuttle prototype (`scripts/universal_shuttle.py`) for the proven rocket works.

## Universal shuttle prototype: `Universal 1 Proto` (the Captain, 2026-11-18; `scripts/universal_shuttle.py`)
Order: one hull for the inner and the outer runs, stable parked at either end, everything it flies and fights with made aboard from chunks, timed schedule, no cargo conditions and no drop sections.
What stands (platform 41, `platform-20`, home Nauvis): 3,414 deck tiles laid from foundation items, 946 pieces (legendary, except what the Captain placed), 722 t, 100 long, four thrusters, twelve cargo bays (659 slots; the Captain widened the spine by hand during the build and the script now describes the ship as they left it), four collectors, 16 rocket turrets (big and huge only), 30 gun turrets (medium, then small), 84 panels, eight tanks. Left PAUSED at Nauvis with its Nauvis <-> Gleba schedule in place.
How it works, in one line each:
- Every machine trades with the hub and every inserter is gated on the hub's stock, so a crusher can always hand back and cannot wedge. Four "ports" (a bulk inserter between hub and belt) carry what the 32 face tiles cannot: ore out and plates back for a four-furnace row, rockets out and magazines out to the ammunition loop.
- The ammunition belt is a closed loop round the ship; rockets side-load from outside, magazines from inside, so each has its own lane (checked: 951 magazines on lane 1, rockets only on lane 2). The hub holds the reserve and the schedule reads the hub.
- Each crusher's recipe is set by two deciders: crush under its cap, reprocess at its cap while another product is low. Seen working at Nauvis (metallic at 1,500 ore turned to reprocessing while carbon was short).
- Carbon goes to fuel until the tanks hold 90,000, then to rockets. Before that rule: 15 rockets and 1,049 fuel a minute at Nauvis; after: fuel at the plant's full 5,400 to 5,700 a minute.
- Schedule per stop: RUN and quiet 60 s and 30 s, OR RUN and TMAX (900 s home, 300 s away). RUN is fuel and oxidizer (all tanks on the hub's green wire), the hub's magazine count, and the hub's explosive rocket count on a leg with big asteroids. The far stop asks only for the leg home.
Measured:
| where | fuel / min | oxidizer / min | magazines / min | explosive rockets / min | chunks crushed / min (metallic, carbonic, oxide) | power drawn / available |
|---|---|---|---|---|---|---|
| Nauvis, parked, 7.8 min, before fuel-first | 1,049 | 5,707 | 37 | 15.0 | 6.0, 10.5, 9.6 (all that was caught: every stock at 0) | 4.3 / 37.8 MW |
| Gleba, parked, 8.0 min, with the chunks caught on the leg | 5,711 | 5,720 | 83 (10.8 fired) | 23.4 | 10.2, 26.6, 7.3 (stock aboard fell from 253 to 135) | 6.8 / 25.2 MW |
- Sized for 23 explosive rockets a minute (one explosives plant, one rocket and one explosive rocket assembler: the hub face allows one chain) and about 90 magazines (four furnaces). Both rates were reached at Gleba. Parked at Nauvis the works are CHUNK-LIMITED: four collectors caught about 26 chunks a minute.
- Why 23 is the mark: Fulgora-Aquilo 5 (2,566 tiles, 14 rocket turrets, parked in Aquilo orbit) spent 6.6 explosive rockets a minute over 8.5 minutes (`scripts/_us_aquilo_watch.py 39 540`, read-only).
- Power: at full rate, with the productivity modules the autopilot fitted, the ship draws 6.8 MW; 84 panels give 7.56 MW in Aquilo orbit. Speed modules would raise the draw past that; then everything runs slower, nothing switches off.
- Flight, Nauvis -> Gleba -> Nauvis on the schedule, three round trips (log `snapshots/universal_shuttle_flight.log`, a line every 20 s; local only, `*.log` is not in git): about 2 minutes a leg at 125 to 185 km/s; 188,000 fuel and as much oxidizer burned in six legs (27,500 a leg on the first trip, more on the faster ones); 2,168 magazines fired (about 360 a leg); no explosive rocket fired; no turret ever empty. It left Nauvis on the RUN-and-quiet branch each time and left Gleba about 70 s after arriving.
  - Trip 1: 938 pieces out and back, none damaged.
  - Trip 2 (held at Gleba 8.3 minutes for the measurement above, tanks full when released): on the leg home, at 185 km/s, the west NOSE COLLECTOR was destroyed. Two guns in the middle of the nose were all that covered the nose corners. Four guns added (one outboard of each nose collector, one at the top of each flank) and the collector put back.
  - Trip 3, with the new guns: 946 pieces out and back, none damaged, at up to 175 km/s. The 185 km/s of the loss was not reached again, so the fix is not proven at that speed. Speed follows the fuel aboard: a full ship flies faster into the same rocks.
NOT proven:
- Anything at Aquilo. Not the leg, not the rocket balance against big asteroids, not standing parked there. Aquilo orbit has almost no carbonic chunks; the rockets there must come from reprocessed oxide and from fragments, and that balance is an estimate (see the Aquilo Wheel section), not a measurement. The reserve (cap 6,000 in the hub) is what covers the gap, and the first 1,100 rockets go into the loop and the turrets before the hub sees one: at 15 to 23 a minute a new ship needs hours before it may be sent out.
- A long park at a far planet on its own catch (the Gleba figures lean on chunks brought in from the leg).
- Vulcanus and Fulgora legs, and a full hold: the valve and the caps keep works goods from filling the hub, but cargo can; then the crushers stop.
Faults paid for:
- The valve inserter was placed before its combinator stood, unfiltered: it threw arriving foundations overboard for about an hour (estimate 1,100: Nauvis stock fell by 1,966 while 850 reached the deck). Every filtered inserter is now created with its filter in the same call.
- To steer a slow deck I lifted and re-laid tile ghosts; 154 of them were never picked up again. `scripts/_us_poke.py` lays one tile per stuck run (and takes the foundation out of the hub); the rest follow by themselves.
- My build step put back belts the Captain had just removed while they were rebuilding the smelter row; I took them out again and adopted their layout.
- The oxidizer has no fuel-style cap: it ran to 176,000 while fuel stood at 96,000. Harmless, but it spends ore and ice.
- A lost piece stays a ghost: the ship carries no spare parts, and its hub then asks Nauvis for a legendary one by itself. Someone also gave the hub a request for 50 repair packs during the evening (not mine; left alone). Both are goods from a planet.
- Raw Lua was used for: tile ghosts (deck), filters, wires and combinator settings, turret priorities, the schedule, one tile per stuck ghost run (paid from the hub), turning two belts, and removing nine of my own stale pieces. Entities were placed with `place_entities`.
Before sixteen ships: (0) a speed cap or still more nose guns, then a leg at full tanks to prove the nose; spare collectors, turrets and belts in the hold so the hub can mend itself; (1) more collectors, on the flanks and stern, since parked the catch is the limit; (2) a second rocket chain needs face tiles: move magazines to a belt-fed row like the smelter and give its two tiles to explosives; (3) railguns for the Aquilo ships (one shot a big asteroid instead of three or four rockets: far less carbon), which needs the power to match; (4) keep the hub's rocket count honest by filling the loop first at Nauvis before the first outer leg; (5) the modules the crushers throw out on each recipe switch pile up in the hub (12 so far): fit crushers that switch with speed modules only; (6) a hold alarm or a reserved margin so cargo cannot fill the hub; (7) one trial to Aquilo and back with the Captain watching, starting from a full reserve.

## Whole-game check (2026-11-18, the Captain: "check the whole game, all maps")
Tools: `scripts/audit_all.py` (every surface: alerts, ghosts, damage, power, fuel, recipes, quality, turrets, storage), `scripts/worst_bottleneck.py`, `scripts/launch_queue.py` (what a planet's silos are asked to lift, in launches).
Found and fixed:
- AQUILO HEAT: 12 of 14 heating towers and both nuclear reactors had no fuel; 8 tower feed chests and one reactor chest had lost their requests, the rest asked for solid fuel and carbon that all went to two towers. Coldest tower 762 degrees, nothing frozen yet (a frozen Aquilo cannot restart). Every tower chest now asks for rocket fuel 10, solid fuel 100, carbon 100; both reactor chests for 20 fuel cells. Within minutes all were at 995+ degrees. Cause of the lost requests not found. Aquilo holds about 60 uranium fuel cells and no shuttle is bringing more.
- NAUVIS-VULCANUS 3 SHUTTLE: at Vulcanus with its oxidizer plant destroyed (0 oxidizer), 11 gun turrets empty, no magazines, ore or foundation, 42 damaged pieces, 17 ghosts on missing deck. It stood in `waiting_for_departure`, where a platform takes no deliveries. Paused it; it then drew iron plate, ore and magazines hub to hub from the Vulcanus Wheel (request section `rescue 33`) and repair packs and foundation from the planet. Left paused at Vulcanus, mending.
- GLEBA LABS: all 10 lacked logistic and production science packs while Nauvis held 96,000 logistic packs. Edgerunner was asking Nauvis for 3,257 more uranium rounds, 131 launches at 25 a rocket, ahead of 46 launches for the whole shuttle fleet. Its request is now 0..6000 (it is parked). The silos are also short of processing units, so the backlog clears slowly.
- GLEBA REACTORS: no fuel cells on Gleba. Nauvis-Gleba 1 and 2 now load 40 cells at Nauvis and the Gleba pad asks for 40.
- REPLICATOR: `scripts/audit_replicator.py` describes the old large Replicator and reports its tables missing; the three compact cells are what stands. They were stuck: machines held productivity module 3 (needs biter eggs), stack inserter and rocket turret (need jelly and carbon fiber) for ever. `replicator_cell.py refresh` now keeps an item on a cell's list only while every solid ingredient is in stock or makeable; 12 items came off. Cell 3 still shows a choice with no recipe set: not solved.
Found, not fixed:
- Nauvis processing units: 14 assemblers short of sulfuric acid at the moment of the check; the acid row gets its iron plate by a long chain (uranium train -> provider chest -> belt -> chemical-yard train) and that belt carried 1,497 coal and 2 iron plates. All eight silos stood short of rocket-part ingredients.
- Nauvis Wheel hub full (0 of 10,009); 411 of 943 provider chests on Nauvis full; Fulgora storage chests 12% free.
- Edgerunner (the Captain is working on it): all 160 tanks and all 24 thrusters read empty of fuel and oxidizer; 24 rocket turrets empty; 46 damaged pieces.
- Empty module slots: Aquilo 128, Nauvis 64. Three boilers on Nauvis without fuel. A space platform hub is always normal quality (not a fault).

## 2026-11-20: Edgerunner west thrusters, Nauvis rocket parts

Edgerunner (order: "duplicate the thrusters on the right half"). The Captain's two stepped rows of 12 on the east side are copied to the
west, mirrored about x = 0 (`scripts/edge_mirror_thrusters.py`): 1,635 deck tiles as tile ghosts (built from foundation items, 500 aboard
and the rest lifted from Nauvis), then 24 legendary thrusters and 343 pipes. 48 thrusters stand, 24 a side.
- A thruster's inlets are not mirror images, so each west pipe run meets the other inlet: where the east run carries fuel, its west twin
  carries oxidizer (west stern row: stepped run = oxidizer, single pipe at -53.5,162.5 = fuel; west flank row: outer run = oxidizer, inner = fuel).
- The west belt staircase beside the flank row stands one row lower than the east one, so that row is copied one row lower.
- Two pipes at the hull end of the west inner run (-126.5,-71.5 and -131.5,-71.5) could not be placed: an inserter and a belt stand there.
- NOT done: no run on either side is joined to a fuel or oxidizer supply, and the ship's 150 tanks are empty (19,500 of each fluid aboard in
  all). The hook-up and the fuel are the Captain's rebuild in progress. The ship stays paused at Nauvis.

Nauvis rocket parts (order: "fix the rocket bottleneck"). Cause: the six sulfuric acid plants at (-235..-215,-238) had no iron plate. The
plate was meant to come off train 899 (Hub Chem Yard <-> Refinery Yard) at Refinery Yard, and the train carries none; a second inserter at
(-212.5,-232.5) picked from an empty tile. The same train takes the acid to the processing-unit row at Hub Chem Yard, so no acid meant no
processing units and no rocket parts. Fix: a requester chest for 400 iron plate on that empty tile (Nauvis holds 1.19 million plates).
- Before: processing units 209 a minute (hour average), 14 of 15 machines short of acid, network stock 0, five silos short of ingredients.
- After: 1,000 a minute, 13 of 15 machines working, seven of eight silos holding a finished rocket, launch queue from 47 to 17.
- Next limit: low density structure, 222 a minute made against 528 used when every silo builds, 47,800 in stock. Acid has no tank at the
  plants (they stop at 200 each while the train is away); the far two plants are short of sulfur on the shared belt.

## 2026-11-20 (later): Edgerunner fuel feed, Aquilo oil line, a shuttle lost

Edgerunner feed (`scripts/edge_feed.py`; order "Yes, hook them up"). Per fluid: plant ring -> tank block (fuel west, oxidizer east) -> one
manifold -> a pump at each of the four thruster rows -> the row's own run. 1,097 pipes, 98 underground ends, 8 pumps, 313 deck tiles.
- The eight pumps are wired green to the hub and run while signal-V < 30, the same limit as the two old pumps at y 286 (which now feed nothing).
- Checked: all 48 thrusters hold fuel and oxidizer; no railgun has anything of ours in its arc; tanks filling (157,000 fuel, 171,000 oxidizer).
- The route bridges open space in places with one-tile strips of deck, which rings open space. The hub refuses the closing tile of a ring;
  `edge_mirror_thrusters.py poke` forces it and takes the foundation from the hub. The Captain: "forced doughnut is fine".
- Found the hard way: an underground pipe does not join across open space. Two links stayed open until the one open tile under each was decked.
- Only two fuel plants and two oxidizer plants feed 48 thrusters; not flown yet. Ship still paused at Nauvis.

Aquilo (found while looking for "the Aquilo shuttle is failing"): no fuel cells, rocket fuel, solid fuel or carbon in stock; 8 of 12
heating towers unfed (still 988 degrees or more, nothing frozen). Cause: the two solid-fuel plants at (32.5,-3.5) and (32.5,-7.5) drew crude oil
from one pumpjack while the main oil network (21 pumpjacks, 128,700 stored) stood full and unjoined. Fix: a pipe from the main oil tank at
(47.5,-1.5) north by underground to (46,-10), west along row -11 and down column 36 to the plants' row, with one heat pipe at (45.5,-9.5).
Solid fuel 550 -> 930 a minute; towers unfed 8 -> 4 within minutes. The limit is now ammonia: only the separation plant at (28.5,-3.5) feeds the
solid-fuel plants; the three at y -27.5 are on another ammonia line. The two nuclear reactors have no fuel cells and no shuttle brings any.

Fulgora-Aquilo 5 Shuttle (platform 39) no longer exists. I left it paused at Aquilo on 2026-11-18 with about 1,700 explosive rockets and no
way to make more. Gleba-Aquilo 1 (38) stands at Gleba, armed (5,600 explosive rockets, 3,964 uranium rounds), on its old schedule, five
carbon short of its "carbon 2,500" condition; not sent.

## 2026-11-20: Edgerunner trial, Nauvis to Gleba, on the new engines

Flown with `edge_flight.py go gleba` (save `pre-edgerunner-gleba-trial`). 15,000 km in about six minutes.
- Speed: a surge to 52 km/s in the first twenty seconds (48 thrusters start full), then 30.0 to 30.6 km/s all the way. The limiter holds.
- Fuel: tanks ROSE in flight (fuel 104,000 -> 168,000, oxidizer 274,000 -> 485,000): four plants out-make 48 throttled thrusters at 30 km/s.
- Hull: no damage, 17,531 pieces at both ends; about 1,000 medium asteroids in view at the end.
- Fault found: nine gun turrets on the east flank (x 192..277, y -235..-88) had no magazines on their belt and four ran empty. An
  underground belt pair at (240.5,-140.5)-(246.5,-140.5) pointed west against the belt's flow. Turned round; all nine refilled in a minute.
- Open: the 24 rocket turrets of the base (y 295.5) are empty. Their belt (row 290) carries magazines only; rockets ride the flank belts
  but do not reach the base. Not needed among medium asteroids; needed before Aquilo.
- The ship is at Gleba, not paused, on a one-stop schedule.

Edgerunner base rocket turrets (same day). Cause: at each bottom corner a one-tile stub belt ((-495.5,286.5) and (496.5,286.5), no input,
empty) made the flank ammunition belt meet the corner belt from the SIDE, so both flank lanes (rockets, magazines) were squeezed onto one
lane of the base belt. That lane filled with magazines while the guns were full, and rockets could not get past. Fix: the two stubs
removed (the corner belt is then a curve and both lanes carry through), and the magazines standing on the base belt's rocket lane moved
into the hub by script (3,171 piercing and 802 uranium rounds; the ship's own goods). All 24 base rocket turrets loaded within four
minutes; no turret of any kind is empty.

## 2026-11-20 (evening): Edgerunner after the Captain's west-arm rework ("I broke it, please fix")

The Captain pasted a mirrored copy of the east arm onto the west arm, one row lower. What that left, and what was done (save `pre-edge-west-arm-fix`):
- 15 ghosts and 47 missing deck tiles with no foundation aboard: ghosts revived, 80 spare deck tiles lifted from the wedges (`edge_mend.py peel`) to pay for the deck.
- West ammunition feed cut: the old feed (row -37.5) ended in an underground entrance with no exit; the pasted row (-36.5) started from
  supply belts that carry nothing. Joined: the old row turns down into the new one at x -19.5 by a plain curve (one input, so both lanes
  carry through); the pasted underground pair over that stretch replaced by belts.
- The four crossing inserters at x 88 (both sides) had no filters. Blacklists set as in `edge_flanks.py`: the one that picks from the
  splitter carries everything but rockets (north lane), the other everything but magazines.
- Six dead stub belts behind the west staircase corners (x -149..-192) turned each corner into a side-load and put magazines on the rocket
  lane. Stubs removed; 1,210 magazines taken off the west rocket lane into the hub.
- West flank fuel: the pasted fuel line had joined the OXIDIZER manifold through one revived pipe, and both west pumps held the wrong
  fluid. That pipe removed, line and pumps emptied, and the line joined to the fuel manifold by 105 pipes from (-7.5,-30.5).
- My own doing: opening the base rocket lane earlier let about 5,600 magazines flow into the empty lane, and the flank belts ran dry in
  the middle of each side (12 guns empty). At rest the works make nothing (hub iron 293, release floor 300) and the hub lets rockets
  and uranium rounds out only in flight. 27 guns were topped up from the hub and 4,500 piercing rounds put back on the two feeds by script.
End state: no ghosts, no empty turret, lanes sorted on both flanks, all 48 thrusters hold both fluids, all 8 feed pumps carry the right
fluid, no railgun has anything of ours in its arc. Left as found: the Captain's unfinished feed start near the hub (x -16..-9, rows -37..-29),
empty dead-end belts that carry nothing. Open: a long stay at rest drains magazines, because nothing is made while parked.

## 2026-11-20 (night): Edgerunner guns fed at rest ("Yes, feed guns at rest")

Measured parked at Gleba: the ship was not short of ammunition (about 12,000 magazines and 11,800 rockets on the belts, 1,493 uranium
rounds and 6,259 rockets in the hub) and uses about 3 magazines and 3 rockets a minute at rest. The fault was distribution:
- The hub outlets were shut at rest: rockets at (4.5,0.5) on `signal-V > 5`, uranium rounds at (4.5,1.5) on `fulgora > 0` (the hub puts
  the planet it is at on the wire). Now `explosive-rocket > 0` and `uranium-rounds-magazine > 0`: they release whenever the belts have
  room; the full lanes are the cap. The shared line keeps one kind a lane (rockets L1, magazines L2), and its end inserters are filtered.
- The crossing splitters at (-85.5,-51) and (85.5,-52) had a piercing-rounds filter, so uranium rounds never reached the flank's magazine
  lane: they stopped on the end belt behind the rocket inserter. The magazine lane was EMPTY on the west flank rows -160..-320 and the east
  near row -160. Filter removed, output priority kept (the dead side fills one lane with rockets and stops; the inserter takes any magazine).
- The hub's 500 piercing rounds had no way out: piercing added to the filter of the outlet (4.5,1.5) and the two end inserters at
  (-7.5,-36.5) and (11.5,-36.5).
End state: both gaps full, belts 11,534 piercing + 2,490 uranium rounds + 16,048 rockets, hub 0 uranium rounds and 2,213 rockets, no empty
gun, railgun arcs clean. Guns that read "low" hold one kind of round with the other kind on the belt beside them: they switch when empty,
not a fault. Save before: `pre-edge-rest-feed`. Open: nothing MAKES magazines at rest; at 3 a minute the belts last about 80 hours, and
only Nauvis refills uranium rounds (request group `edge-ammo 37`).

## 2026-11-20 (night): ammunition per kill, and perimeter cover at rest

Ammunition per kill (`scripts/edge_ammo_meter.py need | mark | since | watch`): the game counts kills by asteroid and ammunition used per
platform, so use can be set against need. Need with today's research: medium asteroid 24 piercing rounds (2.4 magazines) or 8 uranium
rounds; big asteroid 3 explosive rockets, guns do nothing to it; a huge one is beyond rockets (530). Measured at rest over Gleba, 140 s:
196 small and 67 medium kills for 104 magazines, UNDER the 278 the numbers give for piercing alone, and no rocket fired. Guns do not waste.
Rockets per big kill can only be measured on an Aquilo leg (big asteroids fly on no other route). Correction to the note above: at rest
Edgerunner fires about 45 magazines a minute and its works MAKE about as many (286 firearm magazines went into piercing rounds in those
140 s); the "3 a minute" was stock change, use less production.

Perimeter cover (the Captain: "protection, though not as much, around the entire perimeter of all shuttles and ships and stations").
`scripts/perimeter_audit.py` counts each platform's entities out of reach of an armed gun or laser turret, by side:
- No turret at all: White Science, Nauvis Wheel. Lasers on part only: Vulcanus, Fulgora and Gleba Wheels (49 to 61% uncovered).
- The 13 old-hull shuttles: 20% uncovered, all at the stern (98 of 111 entities). Courier 1: stern, 14%. Edgerunner: 33%, stern worst.
- Fully covered: Gleba-Aquilo 1, Universal 1 Proto.
- Nauvis-Vulcanus 3 is stranded at Vulcanus since 2026-11-18 (oxidizer plant shot off, 47 deck tiles gone, 8 of 11 guns empty, paused).
  Guns refilled from its own hub (80 firearm magazines, moved by script). Its rescue request asks for foundation from platforms at
  Vulcanus and none there holds any: Nauvis-Vulcanus 1 now carries 100 from Nauvis (section `rescue-carry-7`). When the deck is back,
  revive the 17 legendary ghosts by script (free rebuild) and unpause. Save before: `pre-nv3-shuttle-mend`.
Later the same night: the foundation arrived hub to hub (100), but a paused hub lays no tiles: 40 tiles laid by script and paid from its
hub, 17 ghosts revived, 14 guns loaded, oxidizer plant back (about 5,000 a minute). Unpaused at 58,000 oxidizer; the carry section is removed.

## 2026-11-20 (night): stern guns on the old-hull shuttles ("Shuttle sterns")

`scripts/shuttle_stern_guns.py plan | build [--apply] [NAME] | status`: two legendary gun turrets at the stern corners of each old-hull
shuttle (tiles x -24..-23 and 22..23, y 15..16), fed from the ship's own ammunition belt. West: the belt's dead end at (-13,-1) is turned
and carried along row -1 and down the free edge column -26. East: an inserter at (13,-1), magazines only, takes a branch off the start of
the belt, along row -1 and down column 25. 62 placed entities a ship, nothing spawned; the belts filled from each ship's own magazines.
Built on all 13 (Nauvis-Gleba 6 on the second try: an asteroid stood on one tile). Each stern gun holds 10 to 13 magazines, no gun on any
ship is empty, and the audit's uncovered share fell from 20% to 3% (17 entities at the stern centre, between the corner guns).
Not done: Courier 1 (narrower wings, panels down to row 17: no free 2x2 deck at its stern corners; it needs its own design or four
foundation tiles a side), the Wheels, White Science, Edgerunner's stern. Save before: `pre-shuttle-stern-guns`.
Courier 1 (same night, "Courier 1"): narrower wings, so its own layout: edge columns -23 and 22 down to row 18, guns on tiles x -21..-20
and 19..20, y 18..19. Four deck tiles were missing under them; the hub-to-hub request (`request_from platforms`, Edgerunner in the same
orbit held 1,008 foundation) was not served in two minutes, so four foundation were taken from Edgerunner's hub by script and laid.
Both guns hold 12 magazines, no gun empty, audit 14% -> 0% uncovered. Save before: `pre-courier-stern-guns`.

## 2026-11-20 (night): every "missing material" alert traced to its source

`scripts/alert_trace.py [PLANET]` follows each waited-for item (entity ghosts, tile ghosts, module requests) through need, pad request,
ships, source stock and production, recipe ingredients, and names the first broken link. Result: no case of Replicators being too slow.
Every one is a broken link or a missing ingredient.
| Item | Where | Broken link | Done |
|---|---|---|---|
| big mining drill x9 | Fulgora | Vulcanus holds 21, no ship asked for them | Courier 1 asks Vulcanus (`ghost-carry-18`) |
| turbo belt x145, underground x2 | Fulgora | none exist; no ship asked, so Vulcanus never saw demand | Courier 1 asks Vulcanus; its foundry unit must now make them |
| foundation x3,892 | Fulgora | nothing makes it: tungsten (Vulcanus), carbon fiber (Gleba), lithium and fluoroketone (Aquilo) are never in one place | OPEN: needs a line |
| lightning collector x1 | Fulgora | no lightning rod on Fulgora, no pad slot | OPEN |
| biochamber x1 | Gleba | Gleba has no electronic circuits | 200 asked: pad slot + Nauvis-Gleba 1 (`ghost-carry-6`) |
| productivity module 3 x20+3, legendary modules on Nauvis-Proto 1 | Gleba, Aquilo, ships | Nauvis has no biter eggs: no captive spawner stands | OPEN: the Captain's call |
| refined hazard concrete x48 | Aquilo | 1,776 aboard Gleba-Aquilo 1, held at Gleba by 984 cryogenic packs the pad would not take (its request was full at 2,992) | pad request 6,000; ship unloaded and left for Aquilo; carbon condition 2,500 -> 2,000 |
| stack inserter x6 | Aquilo | Nauvis cannot make it (jelly, carbon fiber); no ship asked Gleba | Gleba-Aquilo 1 asks Gleba (`ghost-carry-38`), next visit |
| concrete x59, ice platform x47 | Aquilo | stock is there; the ghosts are one column (x 111.5, y -49..56) outside construction range | OPEN |
| roboport x1 | Fulgora | 10 in the network: robots have not built it yet | none needed |
`scripts/ghost_carriers.py [--apply]` writes the ship and pad sections from a hand-kept table. Save before: `pre-ghost-carriers`.

## 2026-11-20 (night): biter-egg cell on Nauvis ("Yes, with bioflux")

`scripts/egg_cell.py plan | build | spawner | status`, site (-365,-187), 18 x 13, just south of the Replicator area. A captive biter
spawner (placed, free; not captured) burns bioflux (1 a minute) and makes 30 eggs a minute; one inserter hands eggs to a
productivity-module-3 assembler, so eggs never enter the logistic network (they hatch after 30 minutes anywhere). The spawner is
switched off by circuit while the output chest holds 100 modules; four laser turrets stand by. Bioflux: every Nauvis-Gleba shuttle asks
Gleba for 200 and the Nauvis pad asks for 400 (`ghost_carriers.py`); the spawner was placed only once its feed chest held bioflux.
First minutes: spawner working, 13 bioflux in its burner, assembler working, 6 modules in the chest and robots already taking them.
Open: legendary modules (Nauvis-Proto 1 asks for legendary ones) still have no maker; if Gleba's bioflux or the shuttles stop for
more than about two hours the spawner starves and turns hostile. Save before: `pre-egg-cell`.

## 2026-11-20 (night): foundation line ("Yes, foundation line")

The maker already existed: the Nauvis Replicator's barrel-fed assembler unit lists foundation (`omni_fluid_asm.py list`). Missing were the
four ingredients on Nauvis and cold fluoroketone in barrels (Aquilo barrels it hot only). Built and written:
- COOLER on Nauvis, site (-383,-230), `scripts/foundation_line.py build | status`: emptier (hot barrels) -> cryogenic plant
  (fluoroketone-cooling) -> filler (cold barrels), machine to machine on the plant's west port column, no pipes. `place_entities` left the
  two assemblers facing north; they are turned south by Lua.
- Supply (`ghost_carriers.py`): tungsten plate Vulcanus -> Nauvis (3 shuttles x 2,000); carbon fiber Gleba -> Nauvis (6 x 300); lithium
  plate and hot fluoroketone barrels Aquilo -> Gleba pad (Gleba-Aquilo 1: 2,000 and 170) -> Nauvis (6 x 300 and 60); pad slots on Gleba and Nauvis.
- Demand: the three Nauvis-Fulgora shuttles ask Nauvis for 200 foundation each (50 a rocket), which is what the Replicator sees.
State when written: requests show in the launch queues (Vulcanus: tungsten for Nauvis-Vulcanus 3; Gleba: lithium and barrels for
Nauvis-Gleba 5). NOT yet proven: the cooler has had no barrel, no foundation has been made; the first lithium and hot barrels need one
Gleba-Aquilo round trip. For all 3,892: 15,568 each of tungsten, fiber and lithium and 1,557 barrels; Aquilo held 2,900 lithium and 172
hot barrels, so its barrelling and lithium rates are the limit. Save before: `pre-foundation-line`.
