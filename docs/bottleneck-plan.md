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
