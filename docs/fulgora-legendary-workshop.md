# Fulgora home island: legendary workshop (design, 2026-11-20)

The Captain's order: the home island (22,-95) lets only legendary products leave, turns scrap into goods the Replicators can use for legendary
machines, and does it by vanilla quality rules, asking the wheel or the planet for normal-quality inputs when it needs them. Goal, restated:
**fulfil legendary orders** (make to order). Decided: the raw-scrap train keeps running until the workshop has filled its first orders, then
the train goes legendary-only. First orders: goods that come straight out of scrap.

## Vanilla rules (checked)
- A recycler returns 25% of a recipe's ingredients at the input's quality; quality modules in the recycler (4 slots) can bump each product.
- A crafted item takes the quality of its ingredients and can be bumped by quality modules in the machine (90% one level, 9% two, 0.9% three,
  0.1% four of the bump chance). Legendary stays legendary; a legendary input gains nothing from modules.
- Upcycling loop: craft with quality modules, send non-legendary products to recyclers with quality modules, feed the returned ingredients back.
  Wiki yields with legendary modules, legendary items per normal input after many cycles: cryogenic plant 4.8%, electromagnetic plant 2.7%,
  foundry 1.6%, assembling machine 3 0.6%, chemical plant 0.3% (171 items recycled per legendary item for the AM3).
  Source: https://wiki.factorio.com/Tutorial:Quality_upcycling_math
- Scrap recycling (0.2 s) gives one of: gear, solid fuel, concrete, ice, steel plate, battery, advanced circuit, stone, cable, processing unit,
  low density structure, holmium ore. Holmium plate recycles into itself (a pure upcycler). Accumulator recycles to batteries.
- Quality modules: 1 / 2 / 3 = 1% / 2% / 2.5%, times 2.5 at legendary quality (legendary tier 3 in four slots = 25%).

## What the island has now (read from the game, 2026-11-20)
- 37 legendary drills, 3 legendary speed module 3 each (speed +3.75, productivity +0.9), 87 legendary accumulators (2,491 MJ stored),
  7 lightning attractors, 2 legendary roboports (0,-96) and (48,-96), 212 logistic and 20 construction robots, **an empty logistic network**.
- 27 steel chests with 117,577 scrap items. Train stop `Scrap Home Load` (1,-107), 4 wagons, 48 bulk inserters.
- 2,248 foundation tile ghosts (x -19.5..72.5, y -120.5..-60.5) mark the planned land extension; nothing built on them yet.
- Stock elsewhere: **no quality module 3 anywhere**. Nauvis network: 200 quality module 1, 100 quality module 2 (normal), 948k iron plate,
  1,972 batteries. Fulgora base network: 216,000 batteries, 1,250 accumulators, 2,705 iron plate.

## Gates
1. **Modules.** Tier 3 needs superconductors (Fulgora) and 4 quality module 2 each: the 100 on Nauvis make 25. Every loop machine takes 4 modules
   (assembler and recycler), so a first loop of 1 assembler + 2 recyclers wants 12. Build quality modules first (the Fulgora Replicator menu has
   quality-module-3; Nauvis `quality_mall.py` makes tiers 1 and 2).
2. **Acid and plastic are not on the island.** Processing units, batteries and low density structures cannot be crafted there. What can: the
   accumulator (5 batteries + 2 iron plate), gears, cables, steel from scrap.
3. **Network stock.** Normal inputs arrive by the Scrap Home train on its empty return leg (it carries nothing back today).
4. **Power.** Island runs on lightning plus accumulators; a recycler draws 180 kW, an AM3 about 375 kW. Measure the night draw before adding more
   than about 30 machines.

## Stages
- S0 (module supply): make quality module 3, move to the island chests.
- S1 (first loop, accumulators): batteries 216k from the base arrive by train. AM3 with 4 quality modules crafts accumulators; legendary goes to
  the export chest at the stop, the rest to 2 recyclers with 4 quality modules, returns to the AM3. Expect about 1 legendary per 170 accumulators
  recycled; 216k batteries support about 250 legendary accumulators.
- S2 (order interface): legendary-quality requests on a provider chest at the stop; train wagon inserters filtered to legendary.
- S3 (direct scrap goods): recycler lines with quality modules over the scrap stock, legendary outputs exported, the rest recycled again.
- S4: switch the train to legendary-only after S1 fills an order; tell the Captain what the base loses (scrap for its recyclers and science).

Not built yet. Nothing on the island was changed in this pass.
