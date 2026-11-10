# Newly found patches and the build queue (2026-11-09)

## What "revealed" means here
The map is generated far past what is charted: 17,228 chunks exist (radius up to 2,530 tiles) but only 2,558 are charted (radius up to 1,446). `force.chart` / `chart_all` from RCON did not change the charted count, so I scanned the
generated resource entities directly (`find_entities_filtered{name=...}` grouped by 128 or 160 tile cells). Building works in any generated chunk, charted or not. The roboport grid builder still follows the charted map.

## Oil (wells, richest first within reach)
| field | wells | total amount | note |
|---|---|---|---|
| (384,-684) and (392,-679) | 14 | 10.4 M | not charted; about 590 tiles from the bus head; **the "another oil field"** |
| (-701,-406) / (-707,-384) | 15 | 9.6 M | known, unused |
| (-527,540) / (-510,550) | 10 | 6.9 M | known, unused |
| (573,-353) | 11 | 8.4 M | known, unused |
| (52,351) | 7 | 4.9 M | known, unused, nearest to the base |
| (-1830,-1124), (-2153..-2218, 380..554) | 19 / 35 | 11.9 M / 21 M | far, uncharted |

## Uranium
| field | tiles | amount | note |
|---|---|---|---|
| (-317,794) | 256 | 512 B | uncharted; **the "another uranium field"**; about 1,050 tiles from the bus |
| (-398,-825) | 780 | 5 M | low amount per tile |
| (-578,-966) | 105 | 0.16 M | tiny |
| (-2298,527) | 281 | 1.4 M | far |
Uranium ore needs sulfuric acid in every drill, so a uranium outpost needs an acid supply (a fluid train or local acid production). Not built.

## Other uncharted patches (at least 150 tiles, nearest to the bus first)
iron: (858,-746) 285 tiles, (-578,754) 1,178, (-508,-1063) 1,606 | copper: (-373,-771) 1,190 tiles, (-903,-358) 278 | coal: (692,-1049) 379 | stone: (760,-475) 191 and (761,-485) 188 (built, below), (776,-683) 373, (-429,-710) 967.

## Built tonight
- **Stone A** (the (760,-480) patch): 40 drills, raw ore (no furnaces), about 26 stone/s onto an express belt, load stop "Stone A Load" (779,-455), 365-piece track west and south to the new yard track y=-157, stop "Bus Stone Unload" (203,-159), bus lane x=193.5.
  One train (2 locomotives, 4 wagons, 150 coal). About 49 enemy pieces were not in the way, 0 destroyed; 62 nest pieces stand in the wider area (600..950, -700..-300), so expect attacks. Paved.
- Raw-ore mode for `build_train_outpost.py` (`--furnaces 0`), and the `--out S` case (rail on the right-hand side of the arriving train).

## Queue, nearest first (each needs: outpost, stop, track via rail_plan, yard track and lane, train)
1. copper (-373,-771) 1,190 tiles; stone (776,-683); coal (692,-1049); iron (858,-746); iron (-578,754); stone (-429,-710)
2. oil (384,-684): pumpjacks on 14 wells, pipes to a tank, pump onto fluid wagons at a load stop, an unload stop at the bus head pumping into tanks. New templates needed (fluid station); the biggest piece
3. uranium (-317,794): drills plus acid supply; also needs the fluid train
Each outpost adds power: drills 90 kW each, so 40 drills is 3.6 MW.
