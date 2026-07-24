# Space Age building reference

Partial — covers the four planets' signature buildings only (what the
deep-research pass fetched primary-source data for). **Space platform
hub/thrusters, elevated rails, quality modules/recyclers, and agricultural
towers are not yet covered** — flagged as an open question in
`space-age-strategy.md`, fill in before those become relevant.

| Building | Planet | Size | Power | Module slots | Built-in productivity | What it does | Build cost |
|---|---|---|---|---|---|---|---|
| **Foundry** | Vulcanus (craft-exclusive; usable elsewhere once shipped) | 5×5 | 2500 kW | 4 | 50% | Converts ore + lava into molten iron/copper; casts plates/gears/pipes/cables etc. at higher efficiency than furnace-based production. Base crafting speed 4 (up to 10 at legendary). ~6 pollution/min. | — |
| **Electromagnetic Plant** | Fulgora | 4×4 | 2 MW | 5 | none noted | Space-Age-exclusive assembler; the top-tier crafting building, built from Fulgora's holmium output. Base crafting speed 2. | 150 holmium plate, 50 processing units, 50 refined concrete, 50 steel plate (10s) |
| **Recycler** | Fulgora | — | — | — | — | Turns scrap (from ruins) into base components — Fulgora's *only* production input, since the planet has no minable ore. | — |
| **Biochamber** | Gleba | — | Runs on **Nutrients**, not electricity (0.25/s active; 2 MJ/nutrient = 4s runtime) | 4 | 50% | Biological equivalent of an assembler — processes nutrient-fed biological recipes. Base crafting speed 2 (up to 5 legendary). | 20 iron plate, 5 electronic circuit, 5 nutrients, 1 pentapod egg, 1 landfill (20s) |
| **Cryogenic Plant** | Aquilo | 5×5 | 1.5 MW | 8 | **none** (unlike the other three signature buildings) | Specialized chemical plant: fluoroketone, fusion power cells, railguns, cryogenic science packs. Aquilo's lithium recipe (50 ammonia + 1 holmium plate + 50 lithium brine → 5 lithium, 20s) effectively only runs here — ammonia/lithium brine can't be barreled for transport, so holmium plate has to be imported from Fulgora instead. | — |

## Cross-planet resource dependency

- **Holmium plate** (Fulgora-sourced) is needed on **Aquilo** for lithium
  production — since lithium brine/ammonia can't be barreled and shipped,
  the dependency runs holmium → Aquilo, not the other way around.
- Vulcanus's Foundry-cast components (plates, gears, etc.) are usable on any
  planet once physically shipped there via space platform — the "Vulcanus
  first" ordering logic is that this compounds: better components available
  everywhere else, sooner.

## Still needed (not covered by the research pass yet)

- Space platform hub, thrusters, and the actual logistics of inter-planet
  travel (fuel, speed, tiers).
- Elevated rails.
- Quality modules and the recycling/quality-upgrade loop in general (only
  Fulgora's Recycler-for-scrap use case is covered above).
- Agricultural towers (Gleba farming, separate from the Biochamber).
