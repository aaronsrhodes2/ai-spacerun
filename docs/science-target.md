# Science target (the Captain, 2026-11-09)

**Target:** maximise science production, all seven packs in equal numbers, using the charted map area, plus orbiting platforms if iron is needed. 10 of each pack per second is the first mark. The point is a pattern that can be replicated across the map, not one hand-built block.
**Allowed:** science packs may be deleted from storage if storage becomes a problem.

## Where the base stands (measured 2026-11-09)
| pack | machines | most it can make per second |
|---|---|---|
| automation | 6 | 1.50 |
| logistic | 7 | 1.46 |
| military | 4 | 1.00 |
| chemical | 8 | 1.17 |
| production | 2 | 0.36 |
| utility | 1 | 0.32 |
| space (platform-1) | 12 | 4.20 |

Equal output today is therefore about 0.3 per second, set by utility and production. 50 labs, research speed bonus 2.5, were using about 1.2 packs per second of each kind. Plates: iron 46/s made against 68/s used (the stock is being run down), copper 43/s made.
Ore is not the limit: the charted map holds far more of every ore than this target can use. Smelting, belts and trains are the limit, so platforms are not needed for iron.

## What one of each pack costs (my arithmetic from the recipes, no productivity modules, not measured in game)
| pack | iron plate | copper plate | plastic | stone | coal |
|---|---|---|---|---|---|
| automation | 2 | 1 | | | |
| logistic | 5.5 | 1.5 | | | |
| military | 7 | 2.5 | | 10 | 5 |
| chemical | 12 | 7.5 | 3 | | |
| production | 52.5 | 19.2 | 6.7 | 11.7 | |
| utility | 33 | 49.8 | 7.7 | | |
| **one of each** | **112** | **82** | **17** | **22** | **5** |

Space science adds 0.4 iron plate, 0.2 carbon and 0.2 ice per pack, all from asteroids.

## The replicable unit: a 1 per second science cell
One cell makes one of each Nauvis pack per second and needs about 112 iron plate, 82 copper plate, 17 plastic and 22 stone per second: 3 express belts of iron, 2 of copper (45/s each), which is three iron outposts and two copper outposts at today's one-belt size.
Machines per cell at the rates measured above: 4 automation, 5 logistic, 4 military, 7 chemical, 6 production, 4 to 6 utility, plus the intermediates (circuits, steel, engines, rails, low density structures).
10 per second is ten cells: about 1,120 iron plate and 815 copper plate per second, roughly 24 times today's iron. Productivity modules in the pack machines and the intermediates would cut that by a large share and should be part of the cell design.
Labs: 50 labs took about 1.2 packs per second, so 10 per second needs about 400 labs at this speed, or fewer with speed beacons.
Space: platform-1 can make 4.2 per second; 10 per second needs about 29 machines and the asteroid collection to feed them (measure collectors first, docs/space-factory-plan.md).

## Cell 1 build log (2026-11-09): not at 1 per second yet
Built (drone-fed cells from `scripts/build_cells.py`, band y -198..-168 north of the base, map tags "Science Cell 1: ..."):
utility 1 to 5 machines, production 2 to 6, plus robot frames, engines, electric engines, low density structures, rails, sticks, electric furnaces, productivity modules,
16 steel furnaces, 6 brick furnaces, 2 gear machines, 7 electronic circuit and 11 copper cable machines. `scripts/build_crude_trunk.py`: an underground crude trunk from the Oil A tanks to the refinery (9 refineries now work).
Found and fixed on the way:
- The four bus-head yards had never unloaded a plate (inserters one tile short of the wagons). Now bulk inserters next to the rail into red provider chests; Stone A joined to the main electric network.
- The labs had no utility packs at all: the old utility machine's output chest sits directly on the start of its belt with nothing to move packs across, and no chest asked for them.
  Two requester chests of mine now feed the lab belt directly at (18.5,28.5) utility and (18.5,35.5) production (tag "Lab Belt Feed"). Research moved again (atomic-bomb 37% to 40% in a few minutes, 20 of 50 labs working).

Last measurement, per minute, taken at dawn with the grid short of power (so these are low readings, not capacity):
| pack | made | used |
|---|---|---|
| automation | 4 | 48 |
| logistic | 18 | 48 |
| military | 0 | 50 |
| chemical | 0 | 52 |
| production | 36 | 0 |
| utility | 30 | 53 |
| space | 0 | 53 |

The first four and space make little because their stores are full (37,000 to 65,000 each); utility is the pack that limits research (0.5/s made against 0.9/s wanted by 20 labs).

What still stands between this base and 1 per second of each:
1. **Power, first.** Demand is at the limit: six reactors with no neighbour bonus give about 240 MW, solar 0 to 180 MW, and the roboports alone drew 236 MW. 669 machines were on low power and the accumulators at 3% before dawn,
   so the power guard pauses the outposts and iron falls further. Drone-fed cells 300 tiles from the unload yard are what make the roboports this hungry. A cell must stand next to its own yard (lesson for the cell script).
2. Iron: 35 to 70 plates/s arriving against 112 needed; the two extra iron outposts are not built.
3. Steel about 13/s of furnace capacity now (16 cell furnaces plus the old ones) but starved of iron; bricks 6 furnaces; plastic 10 plants, 9 working, 406 to 650/min against about 1,000 needed.
4. The old belt-fed chemical line lacks advanced circuits and the military line lacks grenades; hidden today by their stores.

## Power (2026-11-09, later): no longer the limit
- **Solar Field South**: `scripts/build_solar_field.py` put 4,198 panels in (-128,128)-(96,320) and 3,336 accumulators in (96,128)-(320,192). Totals 7,875 panels (about 472 MW at noon) and about 8,030 accumulators.
  Just before dawn the accumulators stood at 100 percent with no machine on low power.
- **Why the Captain's nuclear plant gave so little:** its 9 reactors stand in threes, 6 tiles apart and one tile out of line, so not one has a neighbour bonus (40 MW each, 360 MW in all), and each trio has only 11 heat exchangers
  (33 in all, a 330 MW ceiling). Turbines (93) and water were never the limit. Two reactors also had their spent-cell slot full. That plant is left as it is.
- **Nuclear Units 1 to 8** (`scripts/build_nuclear_unit.py`, block (-694,-306)-(-522,-192) north-west of the lake, map tags "Nuclear Unit N", pumps at "Nuclear Water Intake"): each unit is 4 reactors in a square
  (bonus 2, 120 MW each), 48 exchangers, 96 turbines: 480 MW in 82 by 26 tiles. Eight units are 32 reactors, 3.84 GW. Fuel comes by drone (group "Feed: Uranium Fuel Cell", 10 cells per reactor), spent cells go to red chests.
- 2026-11-10, on the Captain's order "rebuild them to the new design": Nuclear Units 9 and 10 stand west of the block at (-782,-250)-(-694,-192), and the old plant's 9 reactors, 108 heat pipes, 33 exchangers, 87 turbines
  and 9 steam tanks are removed (58 fuel cells and 237 spent cells from the reactors went into Unit 9's red chest). Ten units, 40 reactors, 4.8 GW, five offshore pumps. Left at the old site: its water pipes and pumps,
  the fuel chests and inserters, the three fuel cell assemblers and the centrifuges.
- Uranium budget (one-hour averages): U-238 73.6 made and 52.9 used per minute, so about 20 per minute spare; 32 reactors burn 9.6 cells (18 U-238) per minute. The stock was 7,200 cells and 54,838 U-238. That is why the count stops at eight.
- Not proven: the far exchangers at full load. With demand near 0.5 GW the units idle; during warm-up the trunk lost about 150 degrees over its 35 tiles. If a far exchanger drops below 500 degrees under real load, shorten the wings.
- Reactors burn fuel whether or not power is wanted. A circuit rule (insert fuel only when steam is low) would save uranium; not built.

## Ramp-up (2026-11-10, order "continue to ramp up production")
Built or changed:
- Labs: the utility lane of the lab belt fixed, and four direct feeds (requester chest and bulk inserter into a lab; map tag "Lab Feed", group "Lab Feed: Science Packs", six packs). Labs working went from 6 to 14 of 50 up to 45 of 50.
- Iron: the collectors at Iron A and the west iron outpost filled one belt lane only; every second feeder now goes under the collector by underground belt and loads the other lane. Furnace rows went from about half to all working.
- "Science Cell 1: Pipe" at (-94,-177) for the engine cells (kind `pipe` in `scripts/build_cells.py`).
- Coal A, a drone outpost at (-639,-340): 106 drills, 16 red chests (`scripts/build_drone_mine.py`). "Plastic Coal Feed" requesters at (-207.5,-245.5 to -247.5), group "Belt Feed: Coal".
- Electronic circuit cells: iron request raised from 100 to 600 (the flight is about 500 tiles). Circuits made went from 1,058 to 3,436 per minute.
- "Chemical Belt Plastic Overflow" at (-345,-62): three filtered inserters lift surplus plastic and engines off the old chemical belt into red chests, so advanced circuits get on it again. Chemical packs went from 0 to 32 per minute.

Measured after (per minute, made / used): iron plate 6,660 / 6,689; copper plate 3,861 / 3,624; steel 518 / 522; coal 1,666 / 567; plastic 1,125 / 717; electronic circuit 3,436 / 1,692; advanced circuit 225 / 198; processing unit 50 / 35.
Packs made: automation 89, logistic 40, military 0, chemical 32, production 0, utility 50, space 0. The labs now use about 200 of each per minute, so research runs on the stores:
automation 47,976, logistic 47,980, military 35,390, chemical 42,350, production 12,376, space 61,329, and utility only 1,578 (about ten minutes of stock above what is made).

Still limiting:
1. Utility packs: 50 made against 200 wanted, and the store is nearly gone. Research will fall back to the utility rate (about a quarter) unless more utility cells are built. Next build.
2. Iron plate: everything made is used (6,660 per minute, 111 per second). The iron lane of the bus is empty at the grenade machines (99.5 to 105.5,-122.5), so military packs are not made. More iron outposts come first.
3. Advanced circuits: 225 per minute and the network is in deficit; 5 of 8 chemical machines still wait for them.
4. The pack machines themselves are sized for about 1.5 per second at best; the labs can now use 3.3 per second.
5. Five labs in the middle of the east block still lack automation packs (no free tile for a direct feed).
6. The overflow chests on the chemical belt can fill (1,403, 1,255 and 481 items so far); the belt blocks again if they do.
7. The one-lane collector fix is not in `fx.py mine`, at Coal A or at the copper outposts. Four lattice roboports were removed at Coal A and the grid script has not been re-run there.

## Order
1. Make the existing base a true 1 per second cell: utility 1 to 4 machines, production 2 to 6, iron supply from 46 to 112 per second (two more iron outposts), then measure all seven at 1.0.
2. Write the cell as one script (inputs: a cleared box, a rail stop for iron, copper, stone, a pipe or train for plastic or gas) and build cell 2 with it next to its own ore.
3. Repeat across the map; add labs and platform capacity in step with the cells.
