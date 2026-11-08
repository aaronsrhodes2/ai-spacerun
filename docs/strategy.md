# Factory strategy (the Captain, 2026-11-07)

Goal: an organised, compact factory. Each raw resource is mined at its own patch, smelted at
a **depot** at that patch, and shipped to the central base by train. Anything consumed where it
is made (sulfur at the refinery, plastic at the refinery) stays local.

## Principles
- **Smelt at the depot.** Plates travel, ore does not. A depot is a patch with miners, a furnace
  row (steel furnaces, electric inserters), a coal supply and a loading stop.
- **Trains for long distance**, belts for anything inside a depot or the central base.
- **Fuel where the train is.** Locomotives refuel at the depot they load from (coal from the
  coal depot, or any fuel the depot makes).
- **Clear-cut is allowed** in the central base and at depots. Rebuilding a whole area to
  re-optimise is fine; keep the save before each clearance.
- **Water** is pumped where it is needed (sulfur); a train can carry it only as a fluid wagon
  (fluid-wagon is researched).

## Depots (targets from the Captain's map survey)
| Depot | Product | Patch(es) |
|---|---|---|
| Coal | coal, to fuel the central base and locomotives | (145,62) line 1 (in service), plus others |
| Copper | copper plate | copper patches: (128,-329), (317,233), (-81,422), (-41,-525) and near base (-64,-88) |
| Iron | iron plate | iron: (-27,-103) near base, (-219,-433), (-361,-358), (-464,284) |
| Stone | stone brick | stone: (18,-50) near base, (95,-424), (-267,380) |
| Oil | crude, to refinery | field (-314,-293), already piped |
| Uranium | uranium ore (later) | uranium patches (see survey) |

## Central base
Clear-cut the area between the mines and the lake. Layout bands, north to south: science
assemblers and labs; intermediate products (gears, circuits, cable); the sulfur and plastic
plants stay at the refinery (-150,-115) with a train or belt link.

## Status (2026-11-07)
- Done: coal line 1 (train, 343k patch). Electric iron, copper, coal fields near base. Red and
  green science in service; oil refining; plastic.
- Blue science: engine sets, advanced-circuit chains and pack assemblers built. Engine sets
  make steel in their own furnaces; engine units reach N2.
- **Blocked:** sulfur plant gets no petroleum gas. Water reaches its input pipe; the gas
  underground run ends at the input tile but the plant still reports a fluid shortage. Next
  step is to check which plant input faces which fluid in game. The plastic plant was paused
  for this test and is running again.
- Not started: copper, iron and stone depots with trains; the central clear-cut.

## Decision needed
Clear-cut scope for the central base, and whether to start with the copper depot (train copper
plates in) or the iron depot (more plates; the base's current iron is the constraint).

---
## Update 2026-11-07 (evening): the train circuit

The Captain's order of loading is **water, coal, iron, copper, oil, stone, uranium**, on a circuit of
trains whose cars are mobile storage and balancing. Everything visible is to be mined.

### What "everything visible" costs (from scripts/survey.py, snapshots/survey.json)
29,045 ore tiles in 41 patches (iron 8,855, copper 7,580, coal 6,043, stone 5,657, uranium 910),
7 oil fields (70 wells) and 25 lakes, with 431 enemy spawners scattered between them.
Covering every tile means about 2,400 electric drills: 218 MW, about 120 boilers, 1,200 ore/s.
That is far more than the base could use, so coverage is sized to a **target rate per resource**,
and the cap on drills is the power plant.

### Two layers
1. **Long haul**: one shuttle train per patch group (the coal line 1 pattern, already proven),
   loading drill-to-wagon at the patch, unloading at the depot district.
2. **The circuit**: a short, compact loop round a cleared depot district next to the base. Mixed
   trains (fluid wagons for water and oil, cargo wagons for the rest, in the Captain's order)
   pass the seven loading stops in order, then the base's unloading stops. Adding a train adds
   capacity; cars buffer between supply and demand.

### Power is the real limit
Steam is 9 MW now. Remote drills need power too: local solar (solar-energy is researched) or the
coal cars fuelling burner drills. Nuclear waits on uranium, which is 580+ tiles away.

### Build order proposed
1. Re-clear and lay out the depot district and its circuit.
2. Water (pumps on the south lake, fluid wagons). 3. Coal: line 1 delivers to the depot.
4. Iron (near patch first, then remote). 5. Copper. 6. Oil (crude by fluid wagon from the NW field).
7. Stone. 8. Uranium. Nests near a patch are destroyed before building there.

### Revision (the Captain, same evening): ONE loop, extended outward
Supersedes the "two layers" idea above. There is a single closed, one-way railway. Trains with
mixed cars (fluid wagons for water and oil, cargo wagons for the rest, in loading order) circle
it and each stop loads only its own cars. To add a patch, the loop is extended outward so it
runs through the new patch: one segment is replaced by a longer path that passes the patch and
rejoins. No spur lines and no separate shuttles.

What that implies:
- **One-way track, so one locomotive per train** is enough (no reversing) and signals keep trains apart.
  Needs rail signals/chain signals (both researched) at every stop and junction.
- **Refuelling** happens at one stop on the loop (coal from the coal wagon into the locomotive).
- **A stop per resource, in order**: water, coal, iron, copper, oil, stone, uranium; several stops of the
  same resource can sit side by side when a resource has more than one patch on the loop.
- **Extending the loop is a router job**: pick the segment to replace, route out to the patch
  (corners are the four-curve turn), run through it so drills load straight into the wagons, route back.
- **Loop v1** covers the patches near the base (water, coal, iron, copper, stone are all within about
  200 tiles); oil and uranium are 370-580+ tiles out and come later, by extension.

## Loop v1 status (2026-11-07)
- Track skeleton built by scripts/build_loop.py rails: 124 pieces, closed (0 open ends), in free
  ground: side B y=-117 (x -70..51, over the free iron strip), side A y=-143, west turn x=-83.
- Finding: the central base and every near patch are covered by running mines, belts and the blue
  science block (belts run west at y=-90, -78, -56 across any west-side route), so a loop through the
  patches means rebuilding those mines. Free ore only: copper x -73..-52 y -100..-91, iron
  x -39..-23 y -106..-93 plus a strip at y -120..-115, coal x 17..37 y -66..-47, stone x 10..20 y -48..-44.
- Rail rules found: east/west-heading ends sit on odd y, north/south on odd x for these turns;
  a 90-degree four-curve turn is about 13 tiles each way, so the oval is at least ~26 tiles tall.
- Next: signals, iron stop with drills into wagons, locomotive+wagons, schedule, then the verifier
  (every inserter/belt/pole link checked after each build) and standard block interfaces.

## East base (2026-11-07, the Captain: "clear a new larger area ... standardized blueprints")
- Area x 80..180, y -140..-60 (150x80 tiles at survey, ore/water free), cleared of 349 trees and 5 rocks;
  save `before-east-base` taken first.
- Standard blocks: bridge/factorio/blocks.py. A block = entities + declared ports. Every belt flows east, so
  blocks chain by abutting (west-face ports = previous block's east-face ports). `assembler_row` is the first
  block (n assemblers of one recipe: belts A and B in, belt O out, inserters, poles). `check_ports` reads the
  game and confirms each port tile holds an east-flowing belt; scripts/verify.py checks links and power.
- Tested in game with a 3-machine firearm-magazine row: 45 entities placed, ports OK, no missing inserter
  links; verifier flagged the unpowered machines until a grid link exists (so a power port is next).
- Next: power port (pole line from the grid), bus lanes entering from the loop, then rows for military,
  production (purple) and utility (yellow) science feeding the Captain's research train near the crash site.

## East base power and bus (2026-11-07)
- Power: big poles (70.5,-58.9) and (94,-60) from the grid pole at (62,-59), then a medium-pole spine at
  x=97.5, y=-132.5 to -60.5 every 8. All on network 1.
- Bus: bridge/factorio/bus.py. Eight north-flowing trunks at x=72,75,...,93 (y -62 to -139), meant as
  iron, copper, steel, plastic, coal, stone brick, sulfur, spare (TRUNK_ITEMS). Rows start at x=98.
  `tap(k, y, 98)` splits trunk k and runs a branch east under the other trunks to the row's belt;
  a row's belt A uses a lower-numbered trunk than its belt B.
- Tested in game: a 2-machine row with taps on trunks 0 and 1; a plate put on each trunk arrived at the
  row (copper on belt B, iron inside the machine). Test row removed; plain trunks laid, empty.
- Nothing supplies the trunks yet: plates must come in from the south end (y=-62) from the loop or from
  the existing smelters.

## Bus supply (2026-11-07)
- Coal: scripts/build_bus_supply.py coal. A west-facing splitter at (66,-63) on the coal belt sends half
  down x=65 to y=-56, east under the x=68 coal belt, then north up x=84 into the head of trunk 4. Tested with
  32 coal put on the x=68 belt: some went west as before, 6 reached trunk 4. When trunk 4 fills, the splitter
  sends everything west again. Real coal arrives with the coal train (it was still loading at the patch).
- Iron, copper, steel, plastic, stone brick, sulfur: not supplied. Trunks 0-3 and 5-7 are empty. Feeds come
  from the south at each trunk's x; they must cross the coal feed on y=-56 with an underground.
- Free ore near the base is small (iron strip, copper block, coal/stone edges); full supply needs the loop's
  depots (smelt at the patch, plates by train to a stop at the trunks' south end).

## Military science plant (2026-11-07)
Built in the east base: bridge/factorio/military.py, scripts/build_military.py, 281 entities, all powered, no
missing inserter links. Layout around the shared belt Y_S=-120 (see the module docstring):
- sets row (2 sets of firearm magazine -> piercing rounds, direct inserter), grenade row (3, flipped so it
  shares the O belt on the opposite lane), wall row (1), science row (4 machines, about 36 packs/min at full feed).
- Bus inputs (taps): trunk 0 = iron|copper lanes, trunk 1 = steel|brick lanes, trunk 4 = coal, trunk 5 = stone brick.
  Lanes are filled at the supply end (side-load each item onto its own lane); inserters take what they need.
- Status: every machine is idle with item_ingredient_shortage because the trunks are empty (coal on trunk 4
  waits for the coal train). Packs leave on the belt at y=-126 flowing east from x=116; nothing carries them
  to the Captain's research line yet.
- Needed to run: plates, steel and stone brick on trunks 0, 1 and 5 (loop depots), coal flowing, and a pack belt or
  train stop for the output.

## Bus flipped south (2026-11-07)
Every remaining patch is north of the base, so the bus now flows SOUTH and is supplied at its north end (y=-139).
- Trunks (x=72+3k): 0 steel, 1 iron|copper (one per lane), 5 stone brick, 7 coal; 2-4 and 6 spare.
- Coal riser at x=96 runs north from the coal feed (y=-56), turns west at y=-141 and drops into trunk 7. Taps cross it
  by underground like a trunk. Order rule: normal rows take B from a lower trunk than A; flipped rows take A lower.
- scripts/build_bus2.py rebuilt it with the military taps. Tested: coal put on the feed (plus real train coal) reached
  all three grenade machines (20 coal each) through the riser, trunk 7 and the tap.
- Still empty: trunks 0, 1, 5. Next: depots feed their north heads (x=72, 75, 87 at y=-139).

## Iron depot (2026-11-07) - built and running
scripts/build_iron_depot.py (stages rails, extend, mine, furnaces, stops, unload, train).
- Patch (-219,-433): 16 electric drills in two belts, collector x=-207, 12 electric furnaces (about 7.5 plates/s,
  measured), plate belt y=-412 (hops under the load stop by underground), 12 fast inserters load two wagons.
- One shuttle train (locomotive, 2 cargo wagons, locomotive; each loco hand-fuelled with 150 coal): stop
  "Iron Depot Load" at (-171,-411), "Iron Depot Unload" at (19,-159). Track is one line, 265 pieces, dead end
  at each end (cliffs on the way were removed). Wait conditions: full or 60 s idle at load; empty or 10 s idle at unload.
- Unload: 12 fast inserters on the south side onto a belt at y=-155 that runs east to x=75 and south into the head of
  trunk 1 (iron on one lane). Tested end to end: train loaded 1136 plates, travelled, unloaded; 300+ plates reached
  trunk 1 and the three grenade machines hold iron and are working.
- Power: big poles (-242,-333) to the depot (4), medium poles (91.5,-137.5) west to the unload station (8). A second
  solar field (X0=-196, 288 panels total) was added because the depot pushed the grid into low power.
- Locomotive fuel is not automatic: refuel the two locomotives by hand (about 3 coal per round trip).
- Missing for military science: copper on trunk 1's other lane, steel on trunk 0, stone brick on trunk 5.

## Copper depot (2026-11-07) - built and running
scripts/build_copper_depot.py (stages rails, mine, furnaces, stops, unload, power, train). Same pattern as iron, at the
(128,-329) patch: 16 drills (x 112..127), collector x=129, 12 electric furnaces (about 7 plates/s), plate belt hopping
under the load stop (Copper Depot Load, (165,-295)). Track 126 pieces: dead end (162,-293) east to x=195, south to
y=-149, west to a dead end at x=84; stop Copper Depot Unload at (87,-151). Unload: 12 fast inserters at y=-148 onto a
belt at y=-147 flowing west; its last tile side-loads the x=75 feeder from the east, so copper takes the lane
opposite the iron (iron west, copper east). Power: 7 big poles from (93,-143) plus 3 mediums linking mine to furnaces.
Tested: train loaded 985 plates, ran, unloaded; trunk 1 now holds a full lane of each metal.
Military state: grenades running (full output), magazines full, piercing rounds hold copper and magazines and wait for
steel; walls wait for stone brick. Locomotives (iron and copper trains) are hand-fuelled.

## Steel and stone brick (2026-11-07) - built, military science pack is producing
scripts/build_stone_depot.py (stages steel, mine, furnaces, belt, power).
- Steel: 3 electric furnaces west of the iron feeder belt (x=75, y -154..-140); inserters take iron plates off the feeder
  and steel goes down a belt at x=69 into the head of trunk 0 (about 0.375 steel/s). A chain pole was moved to
  (70.5,-143.5) to make room.
- Stone: 12 electric drills at the (95,-424) patch, 6 electric furnaces (brick), plain belt (265 tiles) down x=79 to
  trunk 5's head, hopping under the copper unload belt. Power: 4 big poles from the copper depot. No train, no fuel.
- Result (measured): all five military machine types run; 23 military science packs made in about 3 minutes from the
  first brick (about 11/min, walls and steel limit it). Packs pile up on the output belt at y=-126 (x 116..); nothing
  carries them away yet.

## Electronics rows and science ports (2026-11-08)
- scripts/build_electronics.py: rows at y0=-96 (copper cable, 2 machines), -88 (electronic circuit, 2), -80 (advanced circuit, 3). Output belts
  flow WEST and bus.give puts each product on a trunk's east lane: cable -> trunk 3, EC -> trunk 2 (plastic is on the west lane), AC -> trunk 0
  (steel on the west lane). Lane facts measured: steel T0 west, plastic T2 west, copper T1 east/iron west, brick T5 east, coal T7 east.
- Plastic reaches trunk 2 by a 230-tile belt from the refinery chest (scripts/build_plastic_belt.py).
- Requester/buffer/active-provider chests are NOT researched (logistic-system), so no bot mall yet.
- The Captain built three input ports at the Sandro station (feeder belts at x=-333, -326, -319, heads at y=-39, bulk-inserter chests onto the
  wagons). Assigned: port 1 military (belt built: scripts/build_pack_to_ports.py, along y=-37), port 2 yellow, port 3 purple.
- Still to build: purple (production) rows (productivity module, electric furnace, rails, science) and yellow (utility) rows
  (batteries and acid, electric engines and lubricant, flying robot frame, processing units, LDS).

## Blue circuits (2026-11-08)
Advanced circuit row now 6 machines (about 45/min at full feed, plastic permitting) at y0=-80 putting AC on trunk 0's east lane.
Pickup: a fast inserter filtered to advanced-circuit takes them off trunk 0's last tile (72,-46) into a steel chest at (74.5,-45.5).
The oval loop (my unused rails) was removed to free the west side of the bus for mirrored rows.

## Row-ordering constraint found while planning purple (2026-11-08)
Trunks flow south, so a row can only use items given by rows NORTH of it. Rows also share the bus gap tiles by row: an east tap from trunk k and a
west (mirrored) tap from trunk m can share a row only if m < k (their lines then diverge); same for gives. bridge/factorio/westbus.py mirrors east-side
designs onto the west side (virtual trunk kv = real 7 - kv; west gives land on the west lane). scripts/build_purple.py is a WIP plan that fails its dry run
(rows -114/-113/-105 are taken by the military taps on the east side, and PM needs EC/AC from rows at -88/-80 so it must sit south of them).
Free bands: east -72, -64; west: -136, -128, -104 and, using the m<k rule, shared bands -72/-64. Needed: IS (east, give T4), PM (east, give T6 east),
RAIL (west, give T6 west), EF (west, give T3 west), PUR (taps T3|EF and T6|PM+rails). Stone is arriving on trunk 4's west lane (scripts/build_stone_belt.py).

## Purple science running (2026-11-08) - solved on the same bus, no second bus needed
scripts/solve_rows.py is an offline solver that tries every (side, band) placement against the built entities; its answer was applied by
scripts/build_purple.py: iron stick (east y0=-136, give T4 east), rail (west y0=-135, give T6 west lane), productivity module (east -72, give T6 east),
electric furnace (west, y0=-84 after scripts/fix_ef_row.py: the first choice -85 put a tap splitter on the AC give target at (72,-80)),
purple pack (east y0=-64, taps T6 + T5, output flows east and joins the pack belt at (130,-64)). Cable row grew to 5 machines (EC was starved of cable).
Pack sorting at the ports: filtered splitters on the y=-37 line at x=-318 (production-science-pack -> feeder (-319,-38), port 3) and x=-325
(utility-science-pack -> feeder (-326,-38), port 2); everything else (military) continues to port 1.
Measured: purple pack machine working, 2 packs made in the first minutes; rails, modules, circuits flowing; steel is the likely limiter.
The AC pickup inserter at trunk 0's end was removed (it starved the furnace and module rows); the chest keeps 612 AC.
Yellow (utility): not built (needs acid, lubricant, batteries, electric engines, flying robot frames, processing units, LDS).

## Steel x2 and the oil rebuild (2026-11-08)
scripts/build_steel2.py: four more electric steel furnaces on the iron unload belt (x 53..67, y -153..-151), steel belt y=-149 into the x=69 steel belt;
total steel about 0.875/s. The Captain is rebuilding the oil site himself (old refineries, plastic/acid plants and the plastic chest were marked for
deconstruction), so yellow waits for his plastic, acid and lubricant outputs; the plastic belt to trunk 2 starts at the old chest (-146.5,-120.5).

## Automatic locomotive fuel (2026-11-08)
The Captain reported trains halting for lack of coal (hand-fuelled locomotives). scripts/build_train_fuel.py puts a burner inserter + steel chest of
coal (575 each, taken from coal already in storage chests) on the south side of the rail at the iron load stop (x=-168 and -147, y=-408) and the
copper load stop (x=168 and 185, y=-292), one per locomotive position; burner inserters fuel themselves, so no power. The trains swap ends at the dead
ends, so both locomotives are at the load stop every trip. About 3 coal per round trip: 575 coal lasts a very long time, but the chests need
topping up eventually (a coal belt would remove that). Not yet verified with a train in place; check inserter drop_target when a train is loading.
Research: the queue now holds only techs that use the packs that exist (purple/yellow techs stall the labs); labs went from 0 to about 34 working.
