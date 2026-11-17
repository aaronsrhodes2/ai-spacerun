# Planet Replicators: plan (2026-11-14)

## Status

The Captain chose **inclusive menus, Fulgora first** (2026-11-14).

**Fulgora phase 1 BUILT** at tile (122,-78) on Fulgora (save `pre-fulgora-replicator` before it): `scripts/omni_maker.py` now has a menu filter (MENUS), per-planet depth
(DEPTHS) and stock-roboport position (STOCK_AT); Fulgora's islands have no 24 x 14 patch, so the unit is one maker (depth 1) in a 16 x 14 patch, the stock roboport beside
it and the recipe table in the strip east of the machine. Menu (solid assembler recipes, 7): lightning-rod, recycler, battery-mk3-equipment, mech-armor,
personal-roboport-mk2-equipment, electromagnetic-plant, quality-module-3. Wired: its silo reads orbital requests; 7 table entries. Nauvis and the
Replicator are unchanged (regression-checked: 178 entries, 0 to place). **Tested:** a temporary request for a lightning rod made the unit pick the recipe and request
copper cable, steel plate and stone brick; it stalled for lack of steel and cable, because **Fulgora's main logistic network holds none of the basics** (steel, plates, circuits,
plastic, cable all 0; it holds processing units 256, supercapacitors 308, superconductors 600, holmium plates 800, accumulators 1143). The unit stays dormant until Nauvis ships them.

**Aquilo: SKIPPED (the Captain's decision, 2026-11-14); revisit only if a piped cryogenic block is wanted. Nothing built. With a correction (2026-11-14).** Earlier notes said Aquilo's lithium and fluoroketone chain was unresearched. That was wrong: lithium (2,200 made), lithium plate (2,337),
cryogenic science pack (2,233) and fluoroketone barrels are enabled and in production. My menu analysis left them out because they are **cross-planet** (lithium needs a holmium plate, which Fulgora
makes), and the analysis only allowed a planet's own resources plus Nauvis basics. What Aquilo's Replicator could do with the generators that exist:
- ice (445,550 made, 3,999 in the network): ammoniacal-solution separation (two products, fluid has no barrel) or asteroid crushing: not buildable by the patterns;
- ice platform (6,400 made, 1,049 in stock): needs 400 ammonia, no barrel: piped only;
- lithium: lithium brine and ammonia, no barrels, plus a Fulgora holmium plate: piped only;
- lithium plate: single-ingredient smelting, the one pattern-friendly item, but the network holds no lithium (all consumed on the lines);
- cryogenic science pack: a science pack (left out of Replicators by design).
Every Aquilo-unique item is already made in bulk by dedicated lines and served from stock, so an Aquilo Replicator built from the existing patterns would have almost nothing to make.
Options: skip Aquilo; or a small unit (lithium-plate furnace + rocket fuel, which Aquilo makes 1,910 of); or a piped cryogenic block (the ammonia, brine and fluoroketone supply) — a real build.

**Gleba BUILT (2026-11-14, save `pre-gleba-replicator` before it); two units, demand wire from the maker unit's roboport (126,-28):**
- **maker unit** (`omni_maker.py ... gleba`, site tile (124,-30), depth 2, 17 x 27 patch, recipe tables below it): artificial-jellynut-soil, artificial-yumako-soil, agricultural-tower, biolab,
  capture-robot-rocket, rocket-turret, spidertron, stack-inserter, toolbelt-equipment, biochamber, efficiency-module-3. Depth 2 because biolab and spidertron nest (capture robot rocket, rocket turret).
  Its silo reads orbital requests. 22 table entries wired.
- **biochamber barrel unit** (`omni_fluid_asm.py --planet gleba --maker biochamber --solid --menu carbon-fiber,rocket-fuel --recipes carbon-fiber,rocket-fuel-from-jelly --fuel nutrients:20`, site (177,16)):
  carbon fiber (never made on Gleba, yet 3 menu items need it) and **rocket fuel from jelly** (the Gleba Wheel mission item; water barrels). The biochamber (3 x 3) burns nutrients, so every order also asks for
  20 nutrients; its fluid inputs are on the north face, the emptier stands above it one tile west. New generator options: --maker biochamber|foundry, --recipes, --solid, --fuel.
  Tested on real demand (12 rocket fuel were missing): it chose rocket fuel, set the recipe, set the emptier to empty-water-barrel; it waits for nutrients, jelly and water barrels (none on Gleba).
  The fluid link is derived from prototype ports, not seen working. A bridging substation at (168,14) joined the unit's isolated substation to the main grid (network 11943); nothing unpowered.
- Not on the menu: jelly, yumako mash, bioflux, pentapod egg, agricultural science pack (Gleba makes them in bulk: 941k, 2.18M, 413k, 231k, 290k; multi-product or science-pack recipes besides), seeds,
  bacteria and spoilage (multi-product recipes), the overgrowth soils (need 10 biter eggs each: the spawner capture research is not done).
- Gleba's main network holds almost nothing the menu needs: spoilage 18,200, stone 4,550, iron plate 400; no nutrients, carbon, jelly, steel, circuits, barrels or landfill.

**Vulcanus BUILT (2026-11-14, save `pre-vulcanus-replicator` before it); three units on land patches in its main logistic network, demand wire from the maker unit's roboport (-50,-86):**
- **maker unit** (`omni_maker.py ... vulcanus`, site tile (-52,-88), one maker, depth 1): artillery-shell, artillery-turret, artillery-wagon, cliff-explosives, speed-module-3, low-density-structure
  (the Vulcanus Wheel mission item). Its silo reads orbital requests. Tested with a temporary artillery-shell request: it picked the recipe and ordered explosives, tungsten plate, calcite and radar
  (calcite and radar arrived; stalls on explosives and tungsten plate, which the network does not hold).
- **assembler barrel unit** (`omni_fluid_asm.py --planet vulcanus --menu tungsten-carbide,foundry`, site (-68,-51)): sulfuric-acid and lubricant barrels. It already picked up real demand
  (974 tungsten carbide missing) and ordered 2 sulfuric-acid barrels.
- **foundry barrel unit** (`--maker foundry --menu turbo-splitter,turbo-transport-belt,turbo-underground-belt`, site (-64,-84)): lubricant barrels; the 5 x 5 foundry has its fluid inputs on the south face,
  so the emptier stands directly south of it. Geometry derived from prototype ports, **not yet seen working** (no barrels on Vulcanus).
- Left out: metallurgic-science-pack (science packs stay with the wheel lines), tungsten-plate (100,279 made on the planet's own lines) and big-mining-drill (needs molten iron, no barrel).
- Vulcanus holds no steel, plates, gears or barrels in its network, but does hold plastic 9,100, electronic circuits 36,400, advanced circuits 18,200, processing units 9,100, calcite 4,538 and carbon 13,650.

**Fulgora phase 2 (2026-11-14): barrel-fed part BUILT, piped part decided.**
- `scripts/omni_fluid_asm.py` now takes --planet, --maker, --menu, --demand and has a `sites` scan (land patches of 16 x 14 in the main network) and a geometry per maker type
  (assembling machine 3: emptier stacked above, ports top and bottom; electromagnetic plant: 4 x 4 with fluid inputs on its WEST and EAST faces, so the emptier stands west of it, facing
  west). The Nauvis unit is unchanged (regression-checked). Save `pre-fulgora-phase2` before the builds.
- **processing-unit unit** at tile (127,-50): assembler maker + sulfuric-acid barrel emptier, wired (demand wire from the Fulgora maker unit's roboport (124,-76)). Same stacked geometry as the
  Nauvis unit that is proven working.
- **superconductor unit** at tile (160,-30): electromagnetic plant maker + light-oil barrel emptier west of it, wired. Geometry derived from prototype ports and checked by coordinates (emptier
  east port (157.5,-29.5) meets the plant's west port (158.5,-29.5)); **not yet seen working** because this game build has no fluid-connection API and Fulgora holds no light-oil barrels.
  The first real order will prove it (the Fulgora network needs light-oil barrels from Nauvis).
- Both units idle for now: the network already holds 256 processing units and 600 superconductors, so nothing is missing; both powered (0 no_power).
- **Piped items (decided, not built):** electrolyte and holmium solution cannot be barrelled. Fulgora already makes supercapacitor (63,636 made, 316 in the network), EM science pack
  (115,665 made, 21,965 in stock) and holmium plate (102,130 made, 800 in stock) on dedicated lines, so the Replicator serves those from stock and does not make them. Tesla ammo, tesla gun,
  tesla turret and lightning collector have never been made; building them needs a piped block (holmium-solution chemical plant -> electrolyte plant -> maker plant, with heavy-oil
  and water barrel emptiers, holmium ore and stone) of 5 to 7 machines for four items nobody has asked for. Recommendation: do not build it until a tesla item is wanted.

(The earlier phase 2 notes follow.)

**Fulgora phase 2 (not built), as first planned:**
- barrel-fed: processing-unit (sulfuric acid; assembler) and superconductor (light oil; EM plant only, so the fluid-assembler unit needs the EM plant's port geometry);
- piped only, no barrel exists for electrolyte or holmium solution: supercapacitor, tesla ammo, tesla gun, tesla turret, lightning collector, EM science pack, holmium plate.
  They need the unit beside Fulgora's existing electrolyte / holmium-solution pipes (heavy oil and holmium solution run in 45 and 112 pipes; the 13 EM plants there make these).
- holmium ore and ice come out of scrap recycling as a mix, so they stay on the recyclers, not the menu.

Vulcanus, Gleba, Aquilo: not started.

## Original plan (before the build)

The Captain's order: each inner and outer planet gets a version of the Replicator that serves only what is **unique to that planet** or what the
planet **makes in great plenty to match its Wheel's mission**. Nauvis keeps serving the standard (vanilla) menu to the solar system.

Candidate menus are in docs/planet-menus.md (`scripts/planet_menus.py`, read-only, from the game's enabled recipes, the planet's own resources and
each recipe's surface conditions). Wheel missions (memory wheel-roles): Nauvis foundations, Fulgora processing units, Gleba rocket fuel, Vulcanus
low-density structure. Aquilo has no wheel.

## Menus (first cut)

| Planet | Unique alone | + with Nauvis basics | Wheel mission item | Machines the planet unit needs |
|---|---|---|---|---|
| Vulcanus | 13 (tungsten plate, carbide, foundry, turbo belts, artillery, big drill, metallurgic pack, cliff explosives, speed module 3) | 0 | low-density structure (own resources) | foundry (metallurgy), assembler, fluid assembler, EM plant (speed module 3) |
| Fulgora | 5 (holmium ore, holmium plate, ice, lightning rod, recycler) | 12 (supercapacitor, superconductor, EM plant, EM pack, tesla gear, quality module 3, mech armor ...) | processing unit (own resources) | EM plant, foundry, recycler, assembler, barrel-fed assembler (sulfuric acid) |
| Gleba | 15 (bioflux, jelly, mash, carbon fiber, bacteria, seeds, pentapod egg, agricultural pack, soils ...) | 9 (biolab, biochamber, agricultural tower, stack inserter, spidertron ...) | rocket fuel (own resources) | biochamber (organic), assembler, barrel-fed assembler |
| Aquilo | 2 now (ice, ice platform) | 0 | none (no wheel) | cryogenic plant, assembler; the lithium and fluoroketone chain is not researched, so the menu grows with research |

Nauvis: unchanged (the audited Replicator, 180 of its 200 reachable items; foundation mission item already in its menu).

## Design

Same machine as the Nauvis Replicator (scripts/omni_maker.py, omni_fluid.py, omni_fluid_asm.py, replicator_buffers.py), parametrised by planet:
1. **Menu filter:** the item list (constant combinator) holds only the planet's menu, so its deciders answer nothing else.
2. **Machine type per category:** the same circuit-set-recipe pattern with the planet's machine in the maker slot (foundry, EM plant, biochamber,
   cryogenic plant, recycler, plus assemblers and the barrel-fed assembler for fluid recipes).
3. **Demand:** the planet's silos read ORBITAL REQUESTS (what a shuttle overhead asks this planet for), minus the stock the planet's network holds;
   the planet's own roboport reads local missing requests. Items outside the menu are ignored.
4. **Wheel mission items:** the Replicator tops up from planet stock; the mission production itself stays on the Wheel.
5. **Buffer field:** per planet, a small field of buffer chests for the menu's basic inputs (like the Nauvis one).
6. **Check:** each unit gets an audit like scripts/audit_replicator.py (menu covered, tables not stale, units powered).

## Open decisions (the Captain)

1. Menu rule: strict (unique alone) or inclusive (also what Nauvis basics plus the planet's resource can make)? Recommended: inclusive for Fulgora and Gleba.
2. Aquilo: build the small unit now (ice, ice platform) or wait for the lithium chain to be researched?
3. How the goods leave: the planet's silos and shuttle (current Replicator design), or the Wheel's export? Recommended: silos and shuttle, the Wheel keeps its own mission.
4. First planet to build: recommended Fulgora (the largest unique menu, EM plant, holmium and processing units).

## Fulgora: storage check and the refined-concrete line (2026-11-17)

**Storage "88% full" is a hoard, not a blockage.** Measured (one-hour production ledger): every by-product is used as fast as it is made
(gears 4,058 made / 4,048 used a minute, cable 3,171 / 3,165, solid fuel 1,421 / 1,418, concrete 1,223 / 1,221, stone 815 / 812, and so on).
The 346 storage chests split into about 304 plain chests with no inserter (full: 1.14M gears, 480k cable, 414k solid fuel, 384k concrete,
234k stone, 216k batteries, 120k processing units, 96k plastic, 60k holmium ore, 54k LDS) and the 37 trash-yard chests of `fulgora_base.py`
(each with an inserter into a recycler), which held 62 of 4,440 slots. Robots fill the hoard first and the overflow goes to the yard, where
most recyclers idle for lack of input. So the existing void keeps up with headroom and nothing was added to it.
`worst_bottleneck.py` now reads this: a surface whose trash yard is at least half empty scores 5 ("hoard, not a blockage") instead of 120 to 300.

**Refined concrete (useful good from the concrete surplus).** `scripts/fulgora_refined.py` (plan | build | config | status), origin tile (214,6),
all legendary, inside a wall ring (x 212..228, y 3..12) on striped concrete (120 tile ghosts, built by robots from stock):
- ice requester (215,10) -> melter (chemical plant 215.5,7.5, outputs north) -> pipe row y 5 -> the north fluid port of both assemblers;
- refined-concrete assemblers at (218.5,7.5) and (226.5,7.5), iron-stick assembler between them (222.5,7.5) handing sticks both ways;
- requesters (217,10) and (225,10): 400 concrete + 40 steel; (222,10): 200 iron plate; providers (219,10) and (226,10).
- Gate: the concrete and ice inserters run only while the network holds under 16,000 refined concrete (2x Aquilo's 7,848 tile ghosts).
- Power from the substations at (220,0) / (220,20); lightning collector at (210,8); logistic cover from the roboport at (202,-13) ends at x 226.
Measured: 240 refined concrete a minute (two assemblers at speed 3.125, before the module mall fits anything); uses about 500 concrete,
200 iron sticks, 25 steel and 125 ice a minute. 16,000 takes a little over an hour.
Not done here: no platform asks for it yet (the Fulgora-Aquilo shuttle request is the parent task's). Steel on Fulgora is thin (about 240 in the
network, the rest is recycled); the line needs 25 a minute and had no shortage in the first minutes, not checked over an hour.
