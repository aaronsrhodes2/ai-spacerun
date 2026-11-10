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

## Order
1. Make the existing base a true 1 per second cell: utility 1 to 4 machines, production 2 to 6, iron supply from 46 to 112 per second (two more iron outposts), then measure all seven at 1.0.
2. Write the cell as one script (inputs: a cleared box, a rail stop for iron, copper, stone, a pipe or train for plastic or gas) and build cell 2 with it next to its own ore.
3. Repeat across the map; add labs and platform capacity in step with the cells.
