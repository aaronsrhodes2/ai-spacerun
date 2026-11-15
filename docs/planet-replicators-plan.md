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

**Fulgora phase 2 (not built):**
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
