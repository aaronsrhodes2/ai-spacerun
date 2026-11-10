# Space factory for maximum ground resources (plan, 2026-11-09)

Brief from the Captain: plan how I would build a space factory that produces the maximum resources for the ground, assuming white (space) science can be skipped. Plan only; nothing here is built.
"Skipping white science" is read as: the techs gated behind space science (advanced asteroid processing, asteroid reprocessing) are assumed available, and the platform does not need to make space science packs.
What I can build today is marked **now**; what needs those techs is marked **tier 2**.

## What the game data says (read from the running game, not from memory)
| recipe | time | in | out | status |
|---|---|---|---|---|
| metallic asteroid crushing | 2 s | 1 metallic chunk | 20 iron ore (+ chunk) | enabled |
| carbonic asteroid crushing | 2 s | 1 carbonic chunk | 10 carbon (+ chunk) | enabled |
| oxide asteroid crushing | 2 s | 1 oxide chunk | 5 ice (+ chunk) | enabled |
| advanced metallic crushing | 5 s | 1 metallic chunk | 10 iron ore + 4 copper ore | tier 2: needs every science pack incl. space and agricultural |
| advanced carbonic crushing | 5 s | 1 carbonic chunk | 5 carbon + 2 sulfur | tier 2 (same tech, advanced-asteroid-processing) |
| advanced oxide crushing | 5 s | 1 oxide chunk | 3 ice + 2 calcite | tier 2 (same tech) |
| chunk reprocessing (any to mixed chunks) | 1 to 2 s | 1 chunk | 1 each of the three types | tier 2: needs space and metallurgic science |
Crusher crafting speed 1 (the printed "(+ chunk)" is what the data shows; I will check in game whether it is a real return or a probability before relying on it). Asteroid collector recipe: 5 processing units + 8 electric engines + 20 low density structure.
Copper ore and sulfur from asteroids exist only at tier 2: until then a space platform makes iron, carbon and ice, and copper must still come from the ground.

## What exists now
Platform-1 (space science): 23 asteroid collectors, 34 crushers, 8 electric furnaces, 28 cargo bays, 46 solar panels, 42 accumulators, hub of 619 slots holding 56,549 space science packs, 7,989 iron plates, 5,707 carbon, 57 foundations.
Platform-3 (yours, nuclear): reactor, 5 turbines, 4 thrusters, 4 collectors, 3 crushers. Platform-2: ghosts only.

## Architecture (one platform, one job: ground resources)
1. **Collect.** Collectors on both long sides of the hull, belts running inward. Each collector grabs only the chunks that pass within its arms, so the supply is set by the number of collectors and by where the platform flies (more asteroids on a route between planets than parked in orbit; the richest are at the edge and shattered planet routes).
   Target 40 collectors per side of a long hull (about 4x platform-1 per side), more if the measured chunks per second per collector is low. **First task: measure chunks per collector per minute on platform-1.** Everything below scales from that one number.
2. **Sort.** Splitters with item filters (chunk type) or a belt per type; carbonic and oxide chunks are the valuable ones for ground chemistry (carbon for plastic and solid fuel, ice for water and ammonia route), metallic for iron.
3. **Crush.** One crusher per 2 s recipe consumes 0.5 chunk/s. 40 crushers give 20 chunks/s; platform-1 already has 34. Speed modules on crushers and productivity if the recipe allows (check `allowed_effects`). Output belts to the next step. Tier 2 swaps in the advanced recipes (copper ore and sulfur) and adds reprocessing to turn surplus chunks into the type in shortest supply.
4. **Smelt on board (now).** Iron ore to plates in electric furnaces on the platform (plates are 1 item instead of ore: halves cargo mass per plate, so more fits in a pod). Platform-1 already smelts iron; scale to about one furnace per 0.625 ore/s.
5. **Store and drop.** Everything flows into the hub and cargo bays (each cargo bay adds slots, platform-1 has 28 bays for 619 slots). The ground **cargo landing pad requests** the items; platforms in orbit drop pods for them. So: set landing pad requests for iron plate, carbon, ice (and copper ore, sulfur, calcite at tier 2), with amounts high enough that the pad never idles. Ground side: the pad is a logistic container; drones move its stock (red provider rules apply: it should provide to the network).
6. **Power and thrust.** Solar in space is full strength (no night): about 60 kW per panel average per the game's space multiplier, check `space-platform` solar multiplier; accumulators are mostly for ramp. Crushers 500 kW each, furnaces 180 kW, collectors about 100 kW: 40 crushers + 40 furnaces + 80 collectors is about 35 MW, i.e. roughly 600 panels, or one reactor (the Captain's platform-3 design). Thrusters set how fast the platform flies; each additional thruster costs fuel and oxidizer (rocket-fuel ground supply or on-board chemistry from carbon and ice).
7. **Defence.** Gun turrets with ammo on both flanks (asteroid damage scales with speed and density); damage to belts stops production. Include repair packs in the hub.

## Throughput model (fill in after the measurement)
Let c = chunks per second collected per collector (measure), N collectors, f = fraction of chunks of each type (about one third each unless filtered).
- iron ore per second = N * c * f_metallic * 20 (basic crushing) or 10 (advanced, plus 4 copper)
- carbon = N * c * f_carbonic * 10; ice = N * c * f_oxide * 5
- cargo mass limit: a rocket carries 1,000,000 weight (foundations weigh 20,000 each, so 50); pods from a platform are limited by hub export rate, not rocket fills: plan 28+ cargo bays per 600 slots and check pods per minute on platform-1.
Example (to be replaced by measured c): with c = 0.1 chunk/s per collector, 80 collectors give 8 chunks/s, about 2.7 per type: 53 iron ore/s, 27 carbon/s, 13 ice/s: more iron than one express belt of plates (45/s) so two output belts.

## Build order
0. Measure platform-1: chunks/min per collector, pods/min from the hub, power draw. (30 minutes of game time, read-only.)
1. **Foundations**: hull growth needs foundations; the ground foundation cells now make about 0.3/s (6 per 20 s), so a 40 by 12 hull extension (480 tiles) is about 27 minutes of production. Order by `platform` requests from the hub.
2. Collectors and belts first (they are what limits everything), then crushers, then smelting, then storage and landing-pad requests, then power, then defence.
3. Tier 2 after the research is allowed: swap recipes, add reprocessing, add copper smelting.
4. Ground: run the pad requests and watch the drones: the pad's stock becomes the ground's iron, carbon and ice source, feeding the bus's raw lanes.

## Decisions I need from the Captain
- Which platform: grow platform-1 (already working, but holds your 56k space science) or build a fresh one next to it.
- Route: park in Nauvis orbit (safe, low density) or fly the Nauvis to Vulcanus route (more asteroids, more damage, needs thrusters and defence).
- Whether tier 2 techs are really meant to be assumed (they need agricultural and metallurgic science, i.e. Gleba and Vulcanus).
