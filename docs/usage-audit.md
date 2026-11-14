# Machine and recipe usage audit (read-only, 2026-11-14, game tick about 50.75M)

Order: "make sure we are using every machine and every recipe for its intended purpose." Nothing in the game was changed. All numbers below were read with read-only Lua over RCON.

## How it was measured, and what could not be

- **Machines:** one snapshot of every assembling machine, furnace (incl. recycler), lab, mining drill, reactor, beacon, agricultural tower, silo, thruster, asteroid collector on all 26 surfaces (platform-1..25 grouped as "platforms"): name, quality, recipe, status, module contents. A snapshot is not a time average: "full_output" or "item_ingredient_shortage" in one frame may be a few seconds old. Fulgora recyclers were sampled twice 9 s apart (identical).
- **Recipes:** all 643 enabled recipes, with their crafting categories (`recipe.prototype.categories`, works in this 2.1 build; the machine-side list is `prototypes.entity[n].crafting_categories`), allowed effects, and lifetime production statistics per surface (`input_counts` = made, `output_counts` = consumed).
- **Stock:** contents of all chests, cargo pads and platform hubs (about 2,000 containers). Items on belts, in machines, in robots, in the player inventory and in wagons are not counted.
- **Limits of the statistics:** they are lifetime counters, not rates, and have no history, so "never made" means never in the whole game. Placing a building does not register as consumption, so "made, never consumed" for buildings and equipment is normal (they were placed). Hand/god-mode crafting is counted as made. Fluids look balanced (made = consumed) because a fluid cannot pile up; only items give a surplus signal. Module effect numbers are the normal-quality prototype values; the epic/legendary quality multiplier was not applied.
- **Not measured:** belt contents and blocked belts, power headroom per surface, whether a "starved" machine is starved by design (demand gates exist on Fulgora and elsewhere), what beacons actually cover, and how Gleba plants are harvested.

## Summary table

Value = estimated payoff if fixed (H/M/L). Effort = work to fix (L = a script and stock modules, M = a script and a rebuild of one block, H = new buildings in volume).

| # | Finding | Where | Value | Effort |
|---|---|---|---|---|
| 1 | Space platform foundation: 192,779 in stock, 223,433 made, 50 consumed, 34 machines still crafting it | Nauvis, Fulgora, platforms | H | L |
| 2 | Electromagnetic plants (speed 2, +50% base productivity, 5 slots) are used only on Fulgora and 3 platform spots; about 220 Nauvis and 60 platform assemblers craft circuits and modules the EM plant is built for | Nauvis, platforms | H | H |
| 3 | Aquilo: all 41 machines have empty module slots, including 3 cryogenic plants with 8 slots each, while 4,037 productivity module 2 sit on Nauvis | Aquilo | M-H | L |
| 4 | 129,198 depleted uranium cells in stock, the reprocessing recipe never run (5 consumed in the whole game); uranium 235 61,471 and 14,979 fuel cells in stock with 3 Kovarex centrifuges still running | Nauvis | M | L |
| 5 | Science packs: made far beyond use (stock: space 209,989; logistic 168,058; automation 89,918; chemical 62,734; metallurgic 37,569), two Nauvis recyclers void logistic packs | all | M | L |
| 6 | Labs: 10 labs, all with 2 speed module 3, 2 of 10 short of packs, no productivity module anywhere in labs; biolab not built (needs biter egg: spawner tech unresearched) | Gleba | M | L (modules) / H (biolab) |
| 7 | Duplicate suppliers beside the wheels' roles: processing units (stock 98,414), low density structure (34,608), rocket fuel (16,688, 17 of 19 Nauvis plants output-blocked) | Nauvis | M | L |
| 8 | Casting recipes unused on Nauvis: copper cable, gears, steel by foundry use half the ore of plate-then-craft | Nauvis | M | M |
| 9 | Chemical plants (speed 1, 3 slots) run recipes a cryogenic plant (speed 2, 8 slots) can run; heavy/light oil cracking also fits the biochamber (+50% base productivity) | Nauvis, platforms | M | H |
| 10 | Gleba: 2 agricultural towers against 548 plants; 7 heating towers without fuel, half the heat network cold; 6 of 8 pentapod egg chambers starved | Gleba | M | M |
| 11 | Structurally idle machines: 123 Nauvis electric furnaces, 88 platform furnaces, 7 Nauvis assemblers and 8 platform foundries with no recipe, 3 crushers/foundries set to nothing | Nauvis, platforms | L-M | L |
| 12 | Quality below epic: 30 assemblers, 179 bulk inserters, 115 chests, 14 poles, 97 lamps, 21 platform hubs | Nauvis, Fulgora, platforms | L | L |
| 13 | Enabled recipes never run, useful (opportunities): see section 1b | - | varies | varies |
| 14 | Spoilage 66,471 in chests, nutrient makers starved | Gleba | L | L |
| 15 | Nuclear fuel centrifuges (7) output-blocked, 897 fuel in stock, no consumer | Nauvis | L | L |
| 16 | Dormant hardware: heating towers 9, Aquilo reactor, fission furnaces | Gleba, Aquilo | L | L |

## 1. Recipes

### 1a. Intentionally unused (no action)

Enabled recipes whose product was never made, and which we do not need: wooden/iron chest, burner inserter and drill, steam engine, car, tank, spidertron, artillery wagon and turret, shotgun and all shotgun/cannon/flamethrower ammo, light/heavy armor, toolbelt, energy shield, discharge defense, gate, gun/flamethrower/rocket/tesla turret, tesla gun and ammo, capsules (poison, slowdown, defender line), cluster grenade, hazard concrete (refined hazard concrete is made, 4,140), selector combinator, display panel, rail signals, rail ramp/support, turbo belts (needs lubricant and tungsten: unneeded), stack inserter. Fish breeding and nutrients-from-fish: no fish source. Yumako/jellynut artificial and overgrowth soil: Gleba plantation is not soil-based. Iron/copper bacteria cultivation: not used. Carbon fiber and tree seed: not used (carbon fiber is an ingredient of stack inserter, rocket turret and toolbelt only, so nothing demands it). Estimated 90 recipes; the full list came from the lifetime statistics (output 0 on every surface).

### 1b. Useful and unused (opportunities)

- **Quality modules (1, 2, 3):** never made. Quality is not applied by modules; the Captain's standing order is to upgrade by `upgrade_quality.py`. Fine, but note legendary-quality is unresearched, so the module is moot until then.
- **Productivity module 3:** enabled, never made. It needs a biter egg (the captive spawner tech is unresearched), so it is gated on the egg farm. Efficiency module 3 needs spoilage and is unneeded.
- **Efficiency module 1:** never made; no power-driven need.
- **Nuclear fuel reprocessing:** never run (finding 4).
- **Biolab:** enabled, never built (needs biter egg and a capture robot rocket; 10 capture robot rockets exist).
- **Recycler, pumpjack, agricultural tower, electromagnetic plant, lightning rod and collector, heating tower item recipes:** never crafted by a machine (placed from hand or god mode). Not a defect.
- **Fluoroketone cooling:** recipe consumes hot fluoroketone and its cold output is never counted as made while 1,137 cold are consumed (statistics quirk of the fluid loop; the plant is output-blocked, so it is running ahead of demand).
- **Coal liquefaction (the full one):** never made. `simple-coal-liquefaction` is used on platforms and Vulcanus. Not needed on Nauvis (36 pumpjacks, oil is the system's root input; crude P 94.9M, consumed 92.5M).

### 1c. Made with no consumer, or a very large unused stock (waste)

Stock values are chest/pad contents. "Made/used" are lifetime statistics.

| Item | Made | Consumed | Stock | Note |
|---|---|---|---|---|
| space-platform-foundation | 223,433 | 50 | 192,779 | steel 20 and cable 20 each: about 3.9M steel and 3.9M cable sunk |
| depleted-uranium-fuel-cell | 129,178 | 5 | 129,198 | reprocessing recipe unused |
| uranium-235 | 79,632 | 16,858 | 61,471 | plus 14,979 fuel cells |
| uranium-rounds-magazine | 32,572 | 191 | 31,440 | by the ammunition doctrine, to be exported; 5 plants output-blocked, correct |
| space-science-pack | 717,760 | 505,906 | 209,989 | |
| logistic-science-pack | 789,571 | 587,099 | 168,058 | 2 Nauvis recyclers void it |
| metallurgic-science-pack | 76,384 | 38,740 | 37,569 | |
| productivity-module-2 | 8,669 | n/a | 4,037 | still being made (4 working, 5 output-blocked, 4 starved) |
| speed-module-3 | 891 | n/a | 906 | 6 AM3 making more, all working |
| logistic-robot | 8,909 | n/a | 4,154 | |
| processing-unit | 638,640 | 538,520 | 98,414 | |
| nuclear-fuel | 1,269 | 304 | 897 | nobody burns it |
| lubricant | 1,636,180 | 1,253,675 | tanks/barrels | 4 Nauvis plants output-blocked, fine |
| calcite | 625,460 | 329,520 | 139,184 | platform crushers over-produce it |
| scrap | 7.96M | 7.85M | 109,536 | demand-gated on Fulgora by design |

## 2. Machine types

Counts are of the 26 surfaces. Status is the snapshot status. Quality is epic unless noted.

| Machine | Total | Notes |
|---|---|---|
| Assembling machine 3 | 1,465 incl. 12 AM2 | Nauvis ~560, platforms ~270, others ~50. Many output-blocked or starved; 7 on Nauvis have no recipe. |
| Assembling machine 2 | 12 | platforms, space science pack, legendary modules |
| Chemical plant | ~330 | |
| Oil refinery | ~35 | Nauvis 9, platforms 10 (coal liquefaction), Vulcanus 5 |
| Electric furnace | 785 | 211 idle (no ingredients), 285 output-blocked (see section 3) |
| Foundry | 128 | Nauvis 18, Vulcanus 19, platforms ~91; 8 platform foundries have no recipe |
| Electromagnetic plant | 17 | Fulgora 13, platforms 4; none on Nauvis |
| Biochamber | 24 | all Gleba |
| Cryogenic plant | 3 | all Aquilo, all with empty module slots |
| Recycler | 102 | Fulgora 87 (idle, gate closed), Nauvis 8, Aquilo 1 |
| Crusher | ~370 | platforms |
| Centrifuge | 47 | Nauvis |
| Lab | 10 | all Gleba; biolab 0 |
| Rocket silo | 8 | |
| Mining drills | 444 | Nauvis 331 (211 big), Vulcanus 31 |
| Agricultural tower | 2 | Gleba |
| Beacon | 77 | Nauvis only, speed module 2 x2 |
| Nuclear reactor | 51 | Nauvis 40 working, Aquilo 1 no fuel |
| Fusion reactor/generator | 0 | tech unresearched (queued after quantum processor) |
| Thruster | 60 | 52 thrust not required (docked), 8 working |
| Asteroid collector | 1,287 | 1,260 working |

Not owned though a recipe class exists: biolab (needs egg), captive spawner (tech unresearched), fusion reactor and generator (tech unresearched). Every other machine class we own at least one of.

## 3. Findings in detail, ranked

### F1. Foundation overproduction (value H, effort L)

- **What:** `space-platform-foundation` (20 steel plate, 20 copper cable, 10 s) is being made on Nauvis, Fulgora and platforms: 223,433 made, 50 consumed, 192,779 in stock (Nauvis 179,639; Fulgora 7,961; platforms 5,179). That is about 3.9M steel plate and 3.9M cable already sunk. 34 assemblers still craft it (Nauvis 25, of which 24 are normal quality and 19 are starved; Fulgora 6; platforms 3).
- **Where:** Nauvis foundation block (assemblers recipe space-platform-foundation), Fulgora six foundation cells, three platform assemblers.
- **Evidence:** statistics and chest sweep above. On Fulgora the foundation cells compete with the rocket parts for scrap-derived steel (SKILL.md "Fulgora: pack gate deadlock"), so Fulgora is spending its scarce scrap on a product with 8,000 sitting in storage.
- **Recommendation:** under the Captain's surplus rule (stop making it) gate the foundation assemblers on stock (for example enable when foundation in the planet network is below 5,000) or disable them; Fulgora's six cells first, because scrap and steel there are demand-gated. Keep the wheel foundation line, which is the intended orbit supplier.
- **Risk:** low; the platform builds the Captain is planning use hundreds to a few thousand foundations, against 192k in stock.
- **Who:** a script over the assembler recipe or circuit enable condition; no existing script found for the gate.

### F2. EM plants are the intended machine for circuits and modules (value H, effort H)

- **What:** in this build the electromagnetic plant (crafting speed 2, base productivity +50%, 5 module slots) accepts the categories `crafting+electromagnetics`, which include copper cable, electronic circuit, advanced circuit, processing unit, accumulator, productivity and speed modules, beacon, big/medium electric pole, substation. An assembling machine 3 has speed 1.25, no base productivity, 4 slots.
- **Evidence (assembler counts crafting these recipes):** advanced circuit 53 (Nauvis) + 11 (platforms) + 1 (Vulcanus); copper cable 56 + 12; electronic circuit 38 + 19 + 4; processing unit 14 + 3 + 1; productivity module 21 + 4; productivity module 2: 10; speed modules 1/2/3: 23; accumulator 8 (Fulgora). About 220 on Nauvis and 60 on platforms. Only 17 EM plants exist, all on Fulgora and 4 on platforms.
- **Arithmetic:** with 4 productivity module 2 (+6% each) an assembler gets +24%; an EM plant with 5 gets +30% + 50% = +80%, and speed 2 against 1.25 (before modules). That is about 45% more product per ingredient and 1.6x the speed per machine, so fewer buildings. The existing base also shows productivity-module-2 4,037 in stock (enough for the fit-out).
- **Recommendation:** convert in this order: advanced circuit (53 + 11), processing unit (14 + 3 + 1), the module makers, then electronic circuit. Cost per plant: 50 steel, 50 processing unit, 150 holmium plate, 50 refined concrete. Holmium (99,748 made, 97,988 consumed) is nearly all spoken for, so a few hundred plants means a holmium push first. Ask before spending holmium that way.
- **Risk:** large rebuild of busy blocks; beacons (77 on Nauvis) were laid out for assembler footprints. EM plant footprint is 5x5, AM3 3x3.
- **Who:** a new block builder (the replicator compression bench `scripts/replicator_compress.py` is the nearest relative).

### F3. Aquilo runs with no modules (value M-H, effort L)

- **What:** all 41 Aquilo machines have every slot empty: 3 cryogenic plants (8 slots each, `cryogenic-science-pack`, `fluoroketone`, `fluoroketone-cooling`), 7 assemblers (6 `ice-platform`, 1 cryogenic plant crafter), 10 chemical plants, 3 pumpjacks, 1 recycler, 1 furnace, 1 silo.
- **Evidence:** module census (empty(of8) x3, empty(of4) x7, empty(of3) x10, empty(of2)). Every other planet and almost every platform machine carries modules. Cryogenic science pack recipe allows productivity.
- **Recommendation:** 8 x productivity module 2 in the cryogenic-science plant (+48% science per ingredient); productivity in the chemical plants (3 each) and ice-platform assemblers; do not put productivity in `fluoroketone-cooling` or recipes whose `allowed_effects` lack productivity (the audit confirmed no wasted productivity module anywhere else). About 100 modules from a stock of 4,037.
- **Risk:** low; power on Aquilo (heating towers 9 of 12 dormant; reactor out of fuel) is the thing to watch since modules raise consumption.
- **Who:** `scripts/aquilo_cryo.py` family; modules arrive by rocket or from the Nauvis stock by shuttle.

### F4. Uranium: depleted cells pile up unprocessed (value M, effort L)

- **What:** 129,198 depleted uranium fuel cells sit in Nauvis chests (about 2,580 slots at stack 50). `nuclear-fuel-reprocessing` (centrifuge, 5 cells to 3 uranium 238, 60 s, accepts productivity) has produced essentially nothing: 5 consumed in the whole game. The reactors (40) make a cell every time they burn one.
- **Also:** uranium 235 stock 61,471 with 14,979 fuel cells in stock, Kovarex still running on 3 of 10 centrifuges (7 output-blocked), uranium ore 71,403 and U-238 95,489 in stock; uranium ore mined 6.3M.
- **Recommendation:** (a) run the reprocessing recipe in centrifuges to recover about 77k U-238; or at least (b) stop adding depleted cells to chests that grow by thousands (a recycler "trash" sink does not make sense when reprocessing exists). Stop Kovarex (surplus rule 1). Centrifuges are already on site (47, 7 output-blocked in nuclear-fuel).
- **Risk:** low.
- **Who:** a script that sets 4-6 idle centrifuges to the reprocessing recipe fed from the depleted-cell chests.

### F5. Science surplus (value M, effort L)

- **What:** packs made far past use. Stock: space 209,989; logistic 168,058; automation 89,918; chemical 62,734; metallurgic 37,569; electromagnetic 50,853 (Fulgora gate is working: 19,781 Fulgora); military 45,072. The labs on Gleba consumed 164,330 of each of the older packs in the whole game. Two Nauvis recyclers (`logistic-science-pack-recycling`) void logistic packs; the six idle Nauvis recyclers near (0,-448) are the sink block.
- **Recommendation:** the voiding is the third rule; the first rule says gate intake. Gate the pack assemblers on stock (platform pack lines in particular: 32 AM3 and 12 AM2 on space science, 7 working). Check lab capacity first (finding 6): if the labs cannot use the packs, make fewer rather than more.
- **Risk:** low; keep the science target of equal packs.

### F6. Labs (value M, effort L for modules / H for biolab)

- **What:** 10 labs, all on Gleba, with 2 speed module 3 each; `laboratory_speed_modifier` is 2.5; research productivity 0 (research-productivity tech unresearched). 8 working, 2 `missing_science_packs` at snapshot.
- **Judgement:** labs are fed by packs, not limited by speed, when two are starved. A productivity module in a lab gives extra research per pack consumed. If packs, not lab time, are the limit, replacing 2 speed with 2 productivity modules is better. I could not measure the pack inflow, so check that before changing (read the labs for a few minutes).
- **Biolab:** speed 2, 4 module slots, 0 built; needs biter egg and capture robot rocket (10 exist); the egg farm plan is `docs/egg-farm-plan.md`.
- **Who:** modules script, then egg farm.

### F7. Duplicated suppliers beside the wheel roles (value M, effort L)

- The wheel roles: Fulgora wheel processing units, Gleba wheel rocket fuel, Vulcanus wheel low density structure, Nauvis wheel foundations.
- **Nauvis ground lines still run beside them:** processing unit 14 AM3 (9 output-blocked, stock 98,414); low density structure 18 AM3 + 5 foundry (4 output-blocked, stock 34,608); rocket fuel 19 AM3 (17 output-blocked, 16,688 in stock).
- **Recommendation:** after the wheels' exports are proven (SKILL.md "wheel_export_*"), disable ground lines by stock gates and reuse their ore and plate. The unchecked item is whether the Nauvis consumers actually take wheel stock; do not turn them off blind.

### F8. Foundry casting unused where it saves ore (value M, effort M)

- **Recipes (this build):** `casting-copper-cable` 5 molten copper (0.5 ore) to 2 cable; plate route: 1 plate (1 ore) to 2 cable, so casting needs half the ore. `casting-iron-gear-wheel` 10 molten (1 ore) vs 2 plates; `casting-steel` 30 molten (3 ore) vs 5 ore; casting-pipe 1 ore vs 1 plate; iron stick 2 ore for 4. The foundry also has +50% base productivity.
- **Where it is used right:** platforms (casting cable 10, gear 4, iron 9, steel 6, LDS 5, ore melting 20+) and Vulcanus (lava). Nauvis uses AM3 for 56 cable, 6 gear, 3 iron stick, 2 pipe and has only 18 foundries (13 on steel, 5 on iron ore melting).
- **Honest note:** Nauvis ore is not scarce (115 mining drills "waiting for space", iron and copper furnaces output-blocked 117 + 57). The gain is space and power, not ore. Low urgency.

### F9. Chemical plants versus cryogenic plants and biochambers (value M, effort H)

- `chemistry+cryogenics` recipes (battery, explosives, plastic bar, sulfur, sulfuric acid, carbon, steam condensation, ammonia/lithium on Aquilo) can run in a cryogenic plant: speed 2, 8 slots (a chemical plant has speed 1, 3). `chemistry+organic` recipes (heavy and light oil cracking) can run in a biochamber (speed 2, +50% base productivity, 4 slots).
- **Counts running in chemical plants:** plastic bar 11 Nauvis + 13 platforms; sulfur 10; sulfuric acid 6 + 14; battery 8; explosives 5; cracking 31 (Nauvis 10, platforms 19, Fulgora 2).
- Cost of a cryogenic plant: 20 processing unit, 20 superconductor, 20 lithium plate, 40 refined concrete; lithium is Aquilo-only and scarce (lithium plate 1,078 made).
- **Recommendation:** only worth it where a chemical block is the bottleneck; plastic is consumed 6.8M on Nauvis with no starving sign. Hold unless plastic becomes limiting (plastic-bar-productivity is queued).

### F10. Gleba (value M, effort M)

- **Agricultural towers:** 2 (one reports `not_enough_space_in_output`) against 324 yumako trees and 224 jellystems. The statistics say 871,800 yumako and 156,000 jellynut were harvested, so the harvest is done some other way (robots deconstructing mature plants, most likely). A tower is the intended machine; ask the Captain.
- **Heating towers:** 7 of 7 `no_fuel`; the heat network has two cold clusters (temperature 15 and 308), 2 heat exchangers `low_temperature`. Gleba power is solar (388) and accumulators (434) otherwise. Spoilage, the obvious local fuel, has 250 kJ each (66k in stock is only 16 GJ; nutrients 2 MJ, bioflux 6 MJ are better but are food). This is either dormant hardware to remove or a power source to feed.
- **Pentapod egg:** 8 biochambers, 6 starved, 2 working; eggs made and consumed (223,288 and 223,010) so output is fully used; the starvation is upstream.
- **Spoilage handling:** nutrients-from-spoilage assemblers (2) starved while 64,202 spoilage sit in chests. Read the Gleba spoilage warning in memory: this is the stable buffer, not a leak. No action without a long-run measurement.

### F11. Structurally idle machines (value L-M, effort L)

- **Nauvis electric furnaces idle with no ingredients (123):** clusters of 38 at (-192,-192), 22 at (-256,-192), 18 at (-64,-448), 13 at (-64,-128), plus small groups; iron/copper furnaces nearby are output-blocked (174), so the whole smelting layer is oversized for demand, not broken. Recommend: leave, or reclaim (they each carry 2 productivity module 2).
- **Platform electric furnaces (88):** platform-16 (23), platform-17 (18), platform-12 (15), others 1 to 2. Platform-12 and platform-16/17 also have 8 foundries without a recipe and 2 crushers without one. These platforms were likely cloned from a template and do not use the smelter block.
- **Nauvis assemblers with no recipe (7):** at (-128,-512) x3, (-320,-256) x3, (-384,-256) x1.
- **Fulgora recyclers (87):** idle by design (intake gate `packs < 6000`, packs 50,853 in stock); lifetime 5,062,773 cycles. Not misuse.
- **Vulcanus:** 3 mining drills with no minable resources (1 big, 2 electric); remove or move.

### F12. Quality below epic (value L, effort L)

`upgrade_quality.py` standing order; what remains (read at tick 50.75M):
- Nauvis: 26 AM3 normal (logistic robot 4, rocket 2, foundation 20), 171 bulk inserters, 14 medium poles, 4 substations, 3 offshore pumps, 57 passive provider and 58 requester chests, 10 steel chests, 97 small lamps, 1 chemical plant. Legendary (not a defect): 4 rocket silos (the build's best), 2 cargo bays.
- Fulgora: 4 AM3, 8 bulk inserters, 4+4 chests, 75 ruin attractors (not upgradable).
- Platforms: 21 space platform hubs normal, 1 bulk inserter, 4 combinators.
- Legendary quality is not researched; epic is the ceiling.

### F13..F16. Smaller

- **Platform asteroid lines (judged lossy-aware):** crusher recipes with the chunk coming back 30% of the time, reprocessing returning one random chunk 40/20/20/20% none. 87 crushers on reprocessing (carbonic 24, metallic 46, oxide 17) of which 64 are starved, i.e. the shuffle is not the cap; collectors catch (1,260 working) is. Chunk statistics: metallic 2.37M made / 1.42M consumed, carbonic 2.16M / 1.37M, oxide 1.17M / 0.97M. The unconsumed part is platform stock plus lost to "none". Calcite is the one product clearly overproduced (625k made, 330k used, 139k stock): the advanced oxide crushing recipe makes it; consider the plain oxide recipe on the platforms that do not need calcite.
- **Platform thrusters:** 52 of 60 `thrust_not_required` (docked), normal.
- **Nuclear fuel:** 7 centrifuges on nuclear fuel are output-blocked, 897 in stock, no consumer. Retire or find a use (rocket fuel replacement is about 12x its energy; heating tower or reactor fuel).
- **Aquilo:** `fluorine` 6,653 made / 3,250 used; reactor with no fuel; 2 heating towers no fuel (the third works on solid fuel); pumpjacks 2 of 3 waiting for space; electric furnace and recycler idle. Cryogenic science only 379 made so far.
- **Lubricant:** 4 Nauvis plants output-blocked, normal.

## 4. Questions for the Captain

1. Stop all foundation assemblers on Nauvis, Fulgora and platforms, keeping only the Nauvis Wheel line (192,779 in stock)?
2. Spend holmium (150 per plant) on electromagnetic plants for advanced circuits and processing units on Nauvis, or hold holmium for something else?
3. May I fill the Aquilo machines with productivity module 2 from the Nauvis stock (4,037) once a shuttle is free?
4. Reprocess the 129k depleted cells into U-238 (set idle centrifuges), and stop Kovarex?
5. How are the Gleba plants harvested today (robots, or the two towers)? Is that the intended design?
6. Labs: swap one of the two speed module 3 for productivity (if packs, not lab time, are limiting)? Needs a measurement first.
7. Should the Nauvis ground lines for processing units, low density structure and rocket fuel be gated off once the wheels' exports are proven?
8. The 211 idle electric furnaces and 88 platform furnaces: reclaim the machines and their modules, or leave them as headroom?

## 5. Not covered

- Belt-level starvation (why 30 copper cable assemblers are short while 57 copper furnaces are blocked).
- Beacon coverage per machine.
- Power capacity per surface.
- Items inside machines, wagons, robots and the player inventory.
- Whether the "starved" Nauvis machines are starved by design.
