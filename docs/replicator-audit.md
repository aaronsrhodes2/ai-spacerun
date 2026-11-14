# Replicator audit (read-only, game tick via RCON)

Question: can the Replicator make every item that Nauvis can make from its own resources, with the recipes researched?

Biome inputs: iron-ore, copper-ore, uranium-ore, coal, stone, wood, raw-fish, crude-oil, water.

## Coverage

- Items reachable from the biome with researched recipes: **200** (7 are raw inputs)
- Covered by the Replicator: **172** (assemblers 156, furnace unit 4, fluid unit 12)
- Not covered, makeable elsewhere in the factory: **21**

### Not covered, by reason
- **science pack (left out of the assembler list by design)**: 6: automation-science-pack, chemical-science-pack, logistic-science-pack, military-science-pack, production-science-pack, utility-science-pack
- **recipe has several products (uranium-processing)**: 2: uranium-235, uranium-238
- **assembler recipe needs a fluid (concrete)**: 1: concrete
- **assembler recipe needs a fluid (rocket-fuel)**: 1: rocket-fuel
- **needs a machine the Replicator lacks: centrifuging (nuclear-fuel)**: 1: nuclear-fuel
- **needs a machine the Replicator lacks: captive-spawner-process (biter-egg)**: 1: biter-egg
- **two or more assembler recipes (ambiguous, left out)**: 1: nutrients
- **assembler recipe needs a fluid (express-transport-belt)**: 1: express-transport-belt
- **assembler recipe needs a fluid (express-underground-belt)**: 1: express-underground-belt
- **assembler recipe needs a fluid (express-splitter)**: 1: express-splitter
- **assembler recipe needs a fluid (refined-concrete)**: 1: refined-concrete
- **assembler recipe needs a fluid (crude-oil-barrel)**: 1: crude-oil-barrel
- **assembler recipe needs a fluid (heavy-oil-barrel)**: 1: heavy-oil-barrel
- **assembler recipe needs a fluid (processing-unit)**: 1: processing-unit
- **assembler recipe needs a fluid (electric-engine-unit)**: 1: electric-engine-unit

### Assembler items nested deeper than 3 levels (43)
active-provider-chest (4), assembling-machine-2 (4), assembling-machine-3 (5), beacon (4), belt-immunity-equipment (4), buffer-chest (4), bulk-inserter (5), centrifuge (4), construction-robot (4), destroyer-capsule (5), discharge-defense-equipment (4), distractor-capsule (4), efficiency-module (4), efficiency-module-2 (5), electric-furnace (4), energy-shield-equipment (4), energy-shield-mk2-equipment (5), fast-inserter (4), fast-splitter (4), fast-underground-belt (4), logistic-robot (4), long-handed-inserter (4), modular-armor (4), night-vision-equipment (4), nuclear-reactor (4), passive-provider-chest (4), personal-laser-defense-equipment (4), personal-roboport-equipment (4), power-armor-mk2 (5), productivity-module (4), productivity-module-2 (5), productivity-module-3 (6), quality-module (4), quality-module-2 (5), requester-chest (4), roboport (4), selector-combinator (4), solar-panel-equipment (4), speed-module (4), speed-module-2 (5), storage-chest (4), substation (4), tank (4)

### Outside the biome: needs imports, 63 items
agricultural-science-pack, agricultural-tower, artificial-jellynut-soil, artificial-yumako-soil, artillery-shell, artillery-turret, artillery-wagon, battery-mk3-equipment, big-mining-drill, biochamber, bioflux, biolab, calcite, capture-robot-rocket, carbon-fiber, carbonic-asteroid-chunk, cliff-explosives, copper-bacteria, cryogenic-plant, cryogenic-science-pack, efficiency-module-3, electromagnetic-plant, electromagnetic-science-pack, fluoroketone-cold-barrel, fluoroketone-hot-barrel, foundry, holmium-plate, ice, ice-platform, iron-bacteria, jelly, jellynut-seed, lightning-collector, lithium, lithium-plate, mech-armor, metallic-asteroid-chunk, metallurgic-science-pack, overgrowth-jellynut-soil, overgrowth-yumako-soil, oxide-asteroid-chunk, pentapod-egg, personal-roboport-mk2-equipment, quality-module-3, rocket-turret, space-science-pack, speed-module-3, spidertron, spoilage, stack-inserter, supercapacitor, superconductor, tesla-ammo, tesla-turret, teslagun, toolbelt-equipment, tungsten-carbide, tungsten-plate, turbo-splitter, turbo-transport-belt, turbo-underground-belt, yumako-mash, yumako-seed

### Recipes not researched yet: 11 items
captive-biter-spawner, foundation, fusion-generator, fusion-power-cell, fusion-reactor, fusion-reactor-equipment, promethium-science-pack, quantum-processor, railgun, railgun-ammo, railgun-turret

## Live build

```
ROM 178 items x 3 machines: present 534, missing 0, naming the wrong item 0
FURNACE table 5 items: present 5, missing 0, wrong 0
FLUID table 14 recipes x 8 deciders: present 112, missing 0
MAKER 1: item_ingredient_shortage, recipe flying-robot-frame, made 922, quality epic
MAKER 2: item_ingredient_shortage, recipe flying-robot-frame, made 1004, quality epic
MAKER 3: item_ingredient_shortage, recipe flying-robot-frame, made 245, quality epic
FURNACE UNIT: no_ingredients
FLUID PLANT: item_ingredient_shortage, barrel machines 4
DEMAND ROBOPORT: working, network robots 43527
ITEM LIST (constant combinator) holds 178 items; the audit counts 178 makeable
STOCK iron-plate=553679, copper-plate=-91, steel-plate=23248, stone-brick=2931, coal=72640, plastic-bar=-1, sulfur=18176, iron-ore=7200, copper-ore=0, stone=82646, wood=794, uranium-ore=72646, electronic-circuit=1255, advanced-circuit=115573, barrel=123
```
