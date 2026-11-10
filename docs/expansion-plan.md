# Outposts, trains and the new main bus (plan, 2026-11-09)

Order from the Captain: cover all copper and iron outposts, maximum smelt, trains carrying the plates to the main base, pave the outposts too, bring in stone, coal and oil (raw, refined later),
and collect everything into one great main bus where future production grows.

## What exists
- Rails: about 1,050 pieces, 12 stops, 6 trains. Iron depot (load (-171,-411), unload (19,-159)), copper depot (load (165,-295), unload (87,-151)), Coal2 (73,-43)/(143,69), science and pack routes. No rail routing tool yet.
- Plate outposts built by drone: iron south-west (-464,284) 137 drills / 72 furnaces; copper north (-41,-525) 71 drills / 54 furnaces. Their plates sit in provider chests (no belt, no train).
- Patches (unused): iron (-723,-317) 1,420 tiles, (693,488) 1,410, (-1155,256) 1,366, (788,595); copper (317,233) 596, (732,97) 1,039, (-902,-345) 1,115, (469,552) 558, (-1136,618) 1,174.
  Stone: (95,-424) used, (-250,522), (-267,380), (94,-573) unused. Coal: (507,341), (685,342), (775,158), (134,654), (-639,-340) unused. Oil: seven fields, only (-314,-293) used.
- Free ground for a bus: x 160..288, y -128..64 (4 by 6 chunks) east of the base, all land, no entities.

## The numbers that decide the size
- One full outpost (137 drills, 72 electric furnaces) is about 28 MW (drills 12 MW, furnaces 13 MW, inserters and poles the rest) and gives up to 45 plates/s, which is exactly one full express belt (45 items/s, 22.5 per lane).
- Ten outposts would add about 280 MW. The grid today: about 64 MW of turbines, 180 MW of solar at noon and nothing at night; demand was 130 MW at dusk with the silos on. Nuclear (the Captain is building it) is what allows "maximum smelt everywhere".
- A cargo wagon holds 4,000 plates (40 slots x 100), so a train with 6 wagons carries 24,000; one outpost's 45 plates/s fills it in about 9 minutes.

## Plan, in order
0. **Power gate.** Build the outposts to full size but let the autopilot enable them in stages by power headroom (accumulator level, fraction of low-power machines), the same way it guards the silos. Nothing is wasted if nuclear arrives later.
1. **Paving.** `scripts/pave.py` already handles chunks; add `--around X Y R` so each outpost and its rail line gets refined concrete.
2. **Rail tool (the missing piece).** `fx.py rail route A B` that lays straight and curved rail between two points with signals and a chain at junctions, avoiding trees, cliffs, water, entities. Test it on one pair of stops first.
3. **Pilot, one iron outpost by train.** Smelter output goes onto an express belt instead of chests (or both), a load station of 6 wagons with bulk inserters, a train, and an unload station at the bus head. Measure plates/s delivered for an hour of game time.
4. **Roll out:** iron (-464,284) full and second smelter line, (-723,-317); copper north (-41,-525) completed, (317,233), (732,97), (-902,-345). Then stone (-250,522), coal (507,341), crude oil to storage tanks by train (fluid wagons).
5. **The main bus** (east block): 16 lanes of express belt (8 belts): iron plate, copper plate, steel, stone brick, coal, plastic, sulfur, circuits, with room to grow, splitter tap points every 12 tiles, stations feeding the head and the belts running south to north, producers before consumers. Unloading stations at the head deliver raw plates; raw stone, coal and oil arrive at the head and are refined in sections along the bus, later.
6. **Retire** the drone-only plate hubs and long belts once the bus is steady; `fx.py compact` the gaps.

## Decisions needed (asked in chat)
- Power: build everything and let the autopilot stage it by headroom, or build only what current power supports.
- Bus site: the east block above, or somewhere else.
- Pilot first (iron, one train), or build all outposts and rails in one sweep.

## Progress log
### 2026-11-09: pilot copper outpost "Copper A" built end to end (the Captain chose power staging, east bus block, everything in one sweep)
- Tools: `scripts/rail_plan.py` (A* over the 2-tile rail grid with a minimum straight run, grid substations/roboports/solar treated as removable at a cost, then `bridge/factorio/rails.route` for the pieces),
  `scripts/build_train_outpost.py` (drills + electric furnaces, output belts merged lane by lane onto one express belt, 24-inserter load station), `scripts/build_yard.py` (bus-head unload yard and rail stubs),
  `scripts/pave.py --box`. Saves: before-copper-a, before-yard, before-stub, before-rail-line.
- Copper A: 60 drills, 62 electric furnaces on the (317,233) patch, about 39 plates/s, loading a 4-wagon train (16,000 plates) at "Copper A Load" (327,111). A 108-piece track runs north and west to
  "Bus Copper Unload" (203,-123) at the head of the east bus, where 24 inserters put plates on an express belt that runs west and then south as the first bus lane (x=198.5, 60 tiles). One train with a
  coal-fuelled locomotive at each end shuttles; it was loading plates when last checked. Outpost and yard are paved.
- Power staging: the autopilot's guard (SILO_GUARD) now also switches off Copper A's furnaces and drills when the accumulators fall below 20 percent and back on above 50 percent, besides pausing the 3 new silos
  below 30 percent. At night the accumulators were already at 4 percent, so both are paused until the sun is up: nuclear is what lets this run through the night.
- Known gaps: no signals on the line (one train only), no fuel feeder at the new stops (150 coal in each locomotive), grid substations and roboports were removed along the track and yard, restore with
  `build_substation_grid.py --restore-near` and a roboport pass; the bus has one lane (copper) and no consumers yet.
- Next, by the plan above: second smelter lines and chest-to-belt/train versions of the two drone outposts, iron outposts (-464,284) shipped by train, new patches (732,97), (-723,-317), (693,488), then stone, coal and oil,
  signals and fuel feeders, and the rest of the bus lanes.

### Correction (2026-11-09, found while building science cell 1): the bus yards never unloaded
The yards described below had their inserters two tiles from the rail, one tile short of the wagons, so no plate ever left a train there; "loading plates when last checked" was the only check made.
All four rows (y -121, -133, -145, -157) now have 24 bulk inserters on the tile next to the rail and 24 red provider chests behind them, plus a roboport at (222,-112). Verified by chest contents after train visits.
The express belts beside the rows and the bus lanes south of them are still there and carry nothing.

### 2026-11-09 (later): Iron A and Copper B added, each with its own yard track and bus lane
- Iron A: iron patch (693,488), 138 drills, 72 furnaces (about 45 plates/s, half the ore capacity: a second smelter line would use the rest), load stop "Iron A Load" (717,339), 423-piece track north and west
  to the yard track y=-133, stop "Bus Iron Unload" (203,-135), belt lane x=196.5. Copper B: copper patch (732,97), 102 drills, 72 furnaces, stop "Copper B Load" (749,-45), 271-piece track to the yard track y=-145,
  "Bus Copper B Unload", lane x=194.5. One train each (2 locomotives, 4 wagons, 150 coal each). Everything paved (outposts and yards). Saves before-iron-a, before-copper-b, before-yard, before-stub.
- Each outpost has its own unload track so no two trains share a track (no signals yet). Lanes are separate for now; they get merged with splitters when the bus is built out.
- Station fix: when the belt column lands the rail on an even line, the build adds a one-tile jog in the belt before the station (build_train_outpost.py picks it). Poles beside the output belts sit at du=7.
- Biter nests: both new outposts had nests within 30 tiles (about 150 enemies at Copper B, 49+63 at Iron A); I destroyed the enemy pieces in the outpost boxes and along the track. More nests stand east of (850,240).
  No turrets are built; expect expansion attacks later (pollution reaches them), so defences or periodic clearing are open items.
- The autopilot's SILO_GUARD now guards all three outposts' furnaces and drills (off below 20 percent accumulators, on above 50 percent). At the last check the accumulators were at 3 percent, so all three
  outposts and the new silos stand paused: Copper A's train had already loaded 9,816 plates, Iron A 2,636, Copper B 88.
