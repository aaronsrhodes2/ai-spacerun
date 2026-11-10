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

## Purple supply fix (2026-11-08)
Root cause of the starved circuit and purple rows: the iron depot (and its 4 big poles) was an isolated electric network. Its link to the main grid went through
poles at the old oil site that were deconstructed when the Captain rebuilt oil, so all 12 depot furnaces and the drills were no_power and the iron train
left with 0 plates. Fixed with two big poles at (-236,-317) and (-221,-299) joining (-242,-333) to the main grid pole at (-208,-283) (depot furnaces working again).
Also: iron and copper trains now leave the depot when full or after 2 minutes (was full or 60 s idle), for a steadier supply.

## Coal boilers retired (2026-11-08)
Measured at night: whole base about 13 MW (turbines 11-13 MW, old steam engines about 2 MW, solar 0, accumulators full); reactor 1 sits at 999 C with 6 fuel cells,
so it has headroom (reactor 40 MW max, turbines 64 MW). Removed the 5 coal boilers, 10 steam engines and 5 burner restart inserters of the two old plants
((30..47,19..49)); no low_power machines afterwards, turbines now carry about 12.9 MW. Left in place: the 4 boilers at x=-288, y -85..-76 (nuclear plant,
coal=0, full of steam; they sit in the water/steam plumbing so I did not touch them) and the belts/coal fields that fed the old plants (now idle).
Risk to remember: with the boilers gone the base depends on the reactor's fuel cells (uranium processing) plus 288 solar panels and 48 accumulators.
Remaining burners: 23 steel furnaces (old smelters), 23 burner mining drills, 36 burner inserters (old mines/smelters), 4 train-fuel burner inserters (intended), 12 locomotives.

## Burner mining drills replaced (2026-11-08)
scripts/upgrade_burner_drills.py: the three rows of burner drills (copper y=-87, iron y=-105, stone y=-51; 23 drills) are now electric drills at pitch 4 with a medium pole
in each gap (drop tiles unchanged), and the 23 burner inserters that fuelled them were removed. Notes: stone row has 2 drills (the third would have mined coal too and
contaminated the belt); items lying on the ground block can_place, so clear them first. All new drills are on the main grid and working; no low_power machines.
Remaining burners: 23 steel furnaces (old smelters), 13 burner inserters (4 train-fuel on purpose), 12 locomotives, 4 idle boilers in the nuclear plant.

## Old smelters now electric (2026-11-08)
scripts/build_smelter_iron.py: iron column (x -26..-19, y -100..-65) is 12 electric furnaces (plate belt moved west to x=-26, out inserters x=-25, in inserters x=-21 from the
existing ore belt x=-20; the idle coal belt x=-19 stays). All 12 working. scripts/build_smelter_copper.py: copper column (x -35..-29, y -84..-65) is 6 electric furnaces
(plate belt to x=-35, joins (-34,-64)); measured 1.78 copper plates/s, limited by ore on the y=-86 belt (not by furnaces, max 3.75/s). The 5-furnace burner row below
(y -59..-57) was removed (its 1,100-plate outputs showed it was surplus), the 2 coal-feeder burner inserters at x=-50 were removed and 350 coal purged from the ore belts so both lanes carry ore.
0 steel/stone furnaces and 0 burner mining drills left. Burners left: 4 train-refuel burner inserters (on purpose), 2 others, 12 locomotives, 4 idle boilers in the nuclear plant.
The 6 copper drills at y=-91.5 are blocked: they drop on the old coal belt y=-90 (flows west, full) - a candidate to redirect to the ore belt for more copper.

## Yellow fluids (2026-11-08)
- `scripts/build_yellow_fluids.py` pipes sulfuric acid and lubricant to the yellow block with two pipe-to-ground trunks: acid from the existing acid line at (-234.5,-127.5), lubricant from the existing line at (-242.5,-131.5). Acid runs on tile row -128, drops under the E-W rail at x=-216, runs row -122, jogs to row -123 at x=-150; lubricant on row -124. Branches go south into the machines' NORTH fluid inputs (the machines face north): PU (21,-115), battery plant (28,-119), electric engine unit (33,-115).
- Battery is a chemistry recipe: the "battery" machine at (29.5,-116.5) is a chemical plant, not an assembling-machine-2 (its inserter moved to x=29; fluid box 1 is the west input tile).
- Verified: acid and lubricant reach the machines; the battery plant works. PU / EEU / FRF / yellow pack starve for electronic circuits, because copper (7 plates/s made = used) caps the bus. Labs (50) all report missing packs: worker-robots-storage-2 needs yellow.

## Copper starvation root cause: iron on the copper lane (2026-11-08)
- Symptom: 50 labs missing packs, EC machines on the east bus starved, copper "made = used" at ~7/s although the copper depot idled (all furnaces full_output, trains waiting).
- Cause: the iron feeder turned into trunk 1 at (75,-155) as a CURVE, so iron filled BOTH lanes. Copper only side-loads (at y=-147) onto the east lane L1 in gaps, and L1 was a jammed column of iron from y=-154 to -94 that no consumer drained. Copper never reached the cable row taps.
- Fix: dummy south-flowing belt at (75,-156) so the iron feed side-loads onto the west lane only; removed the 242 jammed iron plates from L1 (y -154..-90). Rule: when two items share a trunk, each must enter by side-loading onto its own lane; never let a curve carry a two-lane feed into a shared trunk.
- Detection idea for the bottleneck tooling: for every trunk, sample each lane at ~8 points along it; a lane holding an item not in its design list (or a stationary compressed lane whose head item has no consumer downstream) is contamination.

## Train fuel: rocket fuel for all trains (2026-11-09)
- Cause of the copper train running dry: at the depot stop its rear locomotive sits on a curve at (188.5,-290.9), so the second burner-inserter feeder at (185.5,-291.5) never reached it; the front feeder's chest (168.5,-290.5) was also empty.
- Fix: feeders (steel chest + burner inserter, seeded with 1 rocket fuel) beside each locomotive at the stop where the train waits longest, stocked with 300 rocket fuel (moved from the idle 960-stacks at the oil site; the factory makes it):
  copper train at Copper Depot Unload: locos stop at (90,-149) and (111,-149); chests at (90.5,-151.5) and (111.5,-151.5), inserters on y=-150.5 facing north.
  Coal2 train at Coal2 Patch: locos (145,52) and (145,66); inserters (146.5,52.5)/(146.5,66.5) facing east, chests at x=147.5.
  Science train front loco at Travis Christian: loco (23,-5); inserter (21.5,-7.5) facing west, chest (20.5,-7.5). (Its back loco is fed from a belt by a fast inserter at (25,44).)
  Existing depot feeders (copper depot back loco at (168,-293), iron depot both) got 300 rocket fuel + coal each; Callie Arnadottir chest got 100 rocket fuel.
- Facts: inserters reach a locomotive only if their drop point (1.2 tiles from the inserter) lies inside its 1.2-wide collision box, so a loco must sit on a straight track; `LuaEntity.bounding_box` of a loco is NOT rotated (use orientation). `drop_target` reads nil for a moment right after create_entity. Rocket fuel only enters an empty fuel slot (locomotives have 3), so a loco full of coal burns it down first.
- Rocket fuel burn: 600 kW per moving loco = 1 rocket fuel per ~167 s moving; 300 per chest is many hours. Restock when a chest drops under ~50.

## Speed, power link, AM3 upgrades (2026-11-09)
- The server sustains game.speed 9 (540 UPS; 10 gives 563/600). Set with `game.speed=9` over RCON (mod skippy-speed has buttons). At 9x the one-minute production statistics are per game minute, so real-time rates are 9x what the log shows.
- Coal2 Patch drills had no power: their pole network (big poles at (75,45),(102,47),(130,50)) was cut off from the base grid. Added big poles at (68,-23), (69,4), (72,34); network merged. Zero entities report no_power now.
- Upgraded to assembling-machine-3 (fast_replace keeps recipe/modules) all science-chain machines: chemical, advanced/electronic circuit, processing unit, LDS, logistic/automation/military/production/utility packs, rail, engine units, grenade, etc. (73 machines). Power stayed fine (turbines were at 10 of ~60 MW).
- autopilot_local.py (60 s cycle via AUTOPILOT_CYCLE=60): priority queue = next-planet techs first, then cheapest techs whose packs exist; log in docs/autopilot.log.

## Fast belts on the east bus (2026-11-09)
- Cause of thin iron on the bus: trunk lanes were yellow belts (7.5 items/s per lane), and iron enters trunk 1 by side-loading onto ONE lane. Iron belt at the unload was full while trunk 1's iron lane was sparse downstream.
- Upgraded every transport-belt (2022), underground-belt (340) and splitter (33) in x 15..135, y -165..-40 to fast tier with fast_replace (items kept). Splitter filters and priorities (6 filtered ones: plastic, steel, plastic, iron, EC, AC sorters) were saved and restored.
- Remaining limits: depot output (iron and copper trains, no rail signals so no second train), and ore/furnace counts at the depots.

## Whole-factory robot coverage (2026-11-09)
- scripts/build_roboport_grid.py: 102 new roboports (each with 3 solar panels, 2 accumulators, a medium pole) on a 48-tile grid over every cell that holds a player entity, plus 1 bridge; 117 roboports, one logistic network (400 construction and 950 logistic robots from the old west and oil-site networks merged into it). New roboports show low_power until their 100 MJ buffer fills from the solar panels.
- Not done yet: more robots (the factory has no robot production line), and replacing the long belts (plastic, fuel, packs) by requester/passive provider chests with bots.
- fx.py mine: simple mining-patch layout; tested on the unused iron patch at (-464,284): 56 drills, every drill's drop point has a belt, one pole network, output belt end checked; the test build was removed.
- Revealed-map coverage: `build_roboport_grid.py --revealed --build` (2026-11-09) covered every charted 48x48 cell that is mostly land: 595 more roboports plus 3 bridges, 721 in total, one logistic network (400 construction and 950 logistic robots). The server kept 593 of 600 ticks/s. Roboports show low_power until their 100 MJ buffer fills from 3 solar panels; check `status` again after a few game hours, and add panels to any that stay low at night.
- Robots (2026-11-09): every roboport (721) now holds 50 construction and 50 logistic robots and carries the logistic group "Nauvis Land" (request: 50 of each robot type, the same group the original roboports had), so the robots refill themselves from the network. Network totals: 36,050 construction and 36,600 logistic robots.

## Quality mod (2026-11-09), staged, not live
- mods/skippy-quality (zip built, md5 dd7e8663...): data-final-fixes sets every quality module's quality effect to 1.0 (100%) and every quality prototype's next_probability to 1.0, so any machine holding a quality module outputs legendary products directly. (This game's prototypes already report next_probability 1 for normal..epic; the mod pins it.)
- Staged on the VM at /srv/games/data/factorio-staging/ on purpose: the server has auto_pause=true, and activating needs a restart plus the same mod in the client's mods folder, so activating while the Captain is away would pause the game (no client connected) and stall research. To go live: close Factorio on the PC, copy mods/skippy-quality_0.1.0.zip to %APPDATA%\Factorio\mods, enable it in that mod-list.json, copy the zip to /srv/games/data/factorio/mods on the VM (sudo), docker restart factorio, rejoin.
- Substation grid status: 7,957 substations placed; 14 machines still uncovered (dense spots without a free 2x2) and one stray substation network; poles NOT removed yet (scripts/build_substation_grid.py --remove would, with --restore as rollback).
- Pole removal done (2026-11-09): 1,412 small/medium/big poles removed, 71 medium + 1 big kept within 14 tiles of the 14 machines no substation could reach (dense spots with no free 2x2). Power check right after: 0 no_power, 0 low_power (a one-tick blip of 2,411 solar panels reading no_power was only the network rebuilding). Rollback: scripts/build_substation_grid.py --restore (all poles) or --restore-near (only near unpowered machines), from scripts/_poles_removed.json; save "before-pole-removal".
- fx note: substation connectivity in 2.1 uses entity.get_wire_connector(defines.wire_connector_id.pole_copper, true).connect_to(other, false, defines.wire_origin.player); LuaEntity.neighbours no longer exists.

## Whole-map tier upgrade (2026-11-09)
- Applied with `fx.py upgrade --belts --machines --storage` in x slices: 7,299 fast + 2,604 yellow belts, 516 + 22 undergrounds, 92 splitters now express (all 16 filtered splitters kept their filters); 65 assembler 2 -> 3; 81 steel + 1 iron chest -> storage chests (103 storage chests now, none of wood/iron/steel left). Save: before-express-upgrade.
- Speed module 2 fill NOT applied: 2,288 empty slots on 858 machines (1,242 in electric mining drills, 434 in furnaces, 260 in assembler 3, 117 chemical plant, 108 assembler 2, 100 labs, 27 refineries) would add about 207 MW of demand (module +60% energy each) against 11 turbines (about 64 MW) plus 3,033 solar panels (about 180 MW at noon, 0 at night) with demand already near 100 MW. Use `fx.py upgrade --modules speed --module-name speed-module-2 --spawn --budget-mw N --apply` once the nuclear plant can carry it.
- Inserters (2026-11-09): 154 basic and 13 burner inserters -> fast inserters (save before-inserter-upgrade). Now only fast (991), bulk (171, left as they were) and long-handed (158, left as they were) remain. 7 poles added at the far end of the iron outpost smelter where 4 inserters had no power.

## Storage chests reverted to steel (2026-11-09)
- Mistake: `fx.py upgrade --storage` turned 82 steel/iron chests into storage chests. A storage chest is part of the logistic network, so robots dumped
  deconstruction leftovers into it and every buffer chest looked like free network stock. The `--storage` option is removed from fx.py.
- Fix (`scripts/revert_storage_chests.py`, save `before-storage-revert`): all 103 storage chests are steel chests again (fast replace, inserters untouched).
  A chest with an inserter on it kept its main item (science pack buffers, plate stock, uranium ore and so on); everything else, about 18,400 items
  (old belts, inserters, machines, wood, plastic, sulfur), was moved into 10 plain steel chests near (-226, -264), outside the network. Nothing was destroyed.
- Why storage chests exist at all: items a player trashes are carried by robots to the nearest storage chest. A small trash yard of 4 empty storage chests,
  with no inserter or machine near them, is at (-273.5..-270.5, -105.5). Add more yards near wherever the player works, never beside a machine.
- Rule: never convert working chests to storage chests; only the trash yards are storage chests.
- Five more trash yards (4 empty storage chests each, row along +x): (44.5,-143.5) bus head, (2.5,15.5) science block, (-341.5,-33.5) old base west,
  (-241.5,-211.5) oil/pad area, (-33.5,-37.5) middle. Plus the first at (-273.5,-105.5).
- Steel chests to red (2026-11-09, the Captain): 77 steel chests became passive provider chests (fast replace, contents and inserters kept). Only the 10 stash chests near (-226,-264) stay steel.
  Provider chests attract no robot dumping (that was the storage chest problem), so their stock (science packs, plates, uranium) is now offered to any requester that asks.

## Rocket silos x4 and drone-fed parts cells (2026-11-09, the Captain: "increase rocket production and launch pads")
- Finding: silo 1 (-228.5,-227.5) had a finished rocket with empty cargo, waiting to launch; rocket parts were not its limit, cargo was. Part supply
  (processing unit 0.25/s, low density structure 0.27/s) is below what even one silo draws at full speed (0.33/s each).
- Built `scripts/build_silos.py`: 3 new silos at (-270.5,-195.5), (-251.5,-195.5), (-232.5,-195.5). Each has 3 fast inserters from 3 requester chests on the
  north (processing unit, LDS, rocket fuel, 40 each) and 3 bulk inserters from 3 requester chests on the south loading the rocket (first asks for 100 space
  platform foundations, the other two are empty for the Captain to set). All silos launch automatically (`send_to_orbit_automatically`). Substations at each corner;
  one roboport at (-223.5,-204.5) covers the third silo. Save: before-silos.
- Built `scripts/build_cells.py`: requester chest -> bulk inserter -> machine -> bulk inserter -> passive provider chest, stacked 3 tiles apart. 12 steel furnaces at
  x -238.. (iron plate in, steel out) and 9 LDS assemblers at x -248.. (copper, steel, plastic in), y -178..-142, substations at (-240,-175/-160/-146). Save: before-cells.
- Power: 4 silos draw about 30 MW each when crafting. The autopilot now pauses the 3 new silos (`disabled_by_script`) when accumulators fall below 30 percent and
  resumes above 60 percent (`SILO_GUARD`). Demand was 130 MW at dusk against about 64 MW of turbines, so nuclear matters.
- Still short: processing units (needs electronic circuit, advanced circuit and sulfuric acid; acid plants are the row at y=-238.5, x -235..-215). Utility science pack
  also competes for PU and LDS, and the labs have had no utility pack since about 16:11 (the pack train is waiting; utility assembler at (25,-113) is starved).
- Circuit cells (build_cells.py kinds cable, ec, ac) at x -202.. , y -160..-134: 8 copper cable, 5 electronic circuit and 5 advanced circuit assembler 3, each with a requester chest in and a red chest out;
  substations in the gaps. Processing unit block (`build_pu_block.py`): 4 assembler 3 at (-212.5..-200.5,-117.5), acid from the line's surface pipe at (-215.5,-121.5)
  through a new pipe at (-215.5,-120.5), requester chests for electronic and advanced circuits, red output chests; roboport re-added at (-206,-124) and a substation at (-207,-112).
  Saves: before-cells, before-pu-block. Target: +0.5 processing unit/s, +0.75 LDS/s. Check the real rates after an hour of game time.
- Result (game tick 25.71M): processing units 0.52/s (was 0.25), LDS 1.02/s (was 0.27), steel 3.1/s; all 4 silos hold a full rocket (50 platform foundations = 1,000,000 weight, the rocket limit)
  at status rocket_ready. They do not launch on their own: with `send_to_orbit_automatically` a rocket only goes when a platform in orbit asks for its contents, so the shuttle the Captain
  is building is now the limit, not rocket production. Cargo requests are the 100-foundation placeholders; change them on each silo's south requester chests. Gotchas: a cargo inserter's
  drop_target reads "rocket-silo" but the items do go to the rocket (`defines.inventory.rocket_silo_rocket`); `silo.active` is read only, use `disabled_by_script`.
