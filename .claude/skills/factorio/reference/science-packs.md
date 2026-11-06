# Science packs: how progress is made

Generated from the live game by scripts/dump_game_data.py. Don't edit by hand.

Progress is research. Each tech needs a set number of units, and one unit consumes one of each listed pack in a lab. A few techs are unlocked by a trigger (doing something) instead. Each pack below is traced back to raw materials. Amounts are per one pack, before productivity.

## Total research needed

| Pack | Packs for all finite techs | Techs that use it | Unlocked by |
|---|---:|---:|---|
| agricultural-science-pack | 47,514 | 34 | agricultural-science-pack |
| automation-science-pack | 125,325 | 245 | automation-science-pack |
| chemical-science-pack | 116,095 | 170 | chemical-science-pack |
| cryogenic-science-pack | 21,000 | 12 | cryogenic-science-pack |
| electromagnetic-science-pack | 38,140 | 25 | electromagnetic-science-pack |
| logistic-science-pack | 124,800 | 230 | logistic-science-pack |
| metallurgic-science-pack | 32,000 | 23 | metallurgic-science-pack |
| military-science-pack | 45,574 | 79 | military-science-pack |
| production-science-pack | 52,092 | 50 | production-science-pack |
| promethium-science-pack | 1,000 | 1 | promethium-science-pack |
| space-science-pack | 82,719 | 73 | space-science-pack |
| utility-science-pack | 75,969 | 73 | utility-science-pack |

## Trigger techs (no labs)

| Tech | Needs |
|---|---|
| agricultural-science-pack | {"type":"craft-item","item":{"name":"bioflux"},"count":100} |
| agriculture | {"type":"mine-entity","entities":["iron-stromatolite"]} |
| artificial-soil | {"type":"craft-item","item":{"name":"nutrients"},"count":500} |
| automation-science-pack | {"type":"craft-item","item":{"name":"lab"},"count":1} |
| bacteria-cultivation | {"type":"craft-item","item":{"name":"bioflux"},"count":1} |
| big-mining-drill | {"type":"craft-item","item":{"name":"foundry"},"count":1} |
| biochamber | {"type":"craft-item","item":{"name":"nutrients"},"count":10} |
| bioflux | {"type":"craft-item","item":{"name":"biochamber"},"count":1} |
| bioflux-processing | {"type":"craft-item","item":{"name":"bioflux"},"count":25} |
| biter-egg-handling | {"type":"capture-spawner"} |
| calcite-processing | {"type":"mine-entity","entities":["calcite"]} |
| cryogenic-plant | {"type":"craft-item","item":{"name":"lithium-plate"},"count":1} |
| cryogenic-science-pack | {"type":"craft-item","item":{"name":"cryogenic-plant"},"count":1} |
| electromagnetic-plant | {"type":"craft-item","item":{"name":"holmium-plate"},"count":50} |
| electromagnetic-science-pack | {"type":"craft-item","item":{"name":"supercapacitor"},"count":1} |
| electronics | {"type":"craft-item","item":{"name":"copper-plate"},"count":10} |
| foundry | {"type":"craft-item","item":{"name":"tungsten-carbide"},"count":1} |
| heating-tower | {"type":"mine-entity","entities":["copper-stromatolite"]} |
| holmium-processing | {"type":"craft-item","item":{"name":"holmium-ore"},"count":1} |
| jellynut | {"type":"mine-entity","entities":["jellystem"]} |
| lithium-processing | {"type":"mine-entity","entities":["lithium-iceberg-big","lithium-iceberg-huge"]} |
| metallurgic-science-pack | {"type":"craft-item","item":{"name":"tungsten-plate"},"count":1} |
| oil-processing | {"type":"mine-entity","entities":["crude-oil"]} |
| recycling | {"type":"mine-entity","entities":["fulgoran-ruin-vault"]} |
| space-platform | {"type":"create-space-platform"} |
| space-science-pack | {"type":"build-entity","entity":{"name":"asteroid-collector"}} |
| steam-power | {"type":"craft-item","item":{"name":"iron-plate"},"count":50} |
| steel-axe | {"type":"craft-item","item":{"name":"steel-plate"},"count":50} |
| tungsten-carbide | {"type":"mine-entity","entities":["big-volcanic-rock","big-volcanic-rock-hot","huge-volcanic-rock","huge-volcanic-rock-hot","small-demolisher-corpse","medium-demolisher-corpse","big-demolisher-corpse"]} |
| tungsten-steel | {"type":"craft-item","item":{"name":"big-mining-drill"},"count":1} |
| uranium-processing | {"type":"mine-entity","entities":["uranium-ore"]} |
| yumako | {"type":"mine-entity","entities":["yumako-tree"]} |

## agricultural-science-pack

Raw per pack: 30 water, 5.39 yumako, 2.16 jellynut, 0.5 pentapod-egg

- 1 × agricultural-science-pack [organic, 4s, only where pressure 2000..2000]
  - 1 × bioflux [organic, 6s]
    - 3.75 × yumako-mash [organic, 1s]
      - 1.88 × yumako (no recipe: raw or special)
    - 3 × jelly [organic, 1s]
      - 0.75 × jellynut (no recipe: raw or special)
  - 1 × pentapod-egg [organic, 15s, only where pressure 2000..2000]
    - 15 × nutrients [organic, 2s; other recipes: nutrients-from-biter-egg, nutrients-from-fish, nutrients-from-spoilage, nutrients-from-yumako-mash]
      - 1.88 × bioflux [organic, 6s]
        - 7.03 × yumako-mash [organic, 1s]
          - 3.52 × yumako (no recipe: raw or special)
        - 5.62 × jelly [organic, 1s]
          - 1.41 × jellynut (no recipe: raw or special)
    - 0.5 × pentapod-egg (loop, see above)
    - 30 × water (mined or pumped)

## automation-science-pack

Raw per pack: 2 iron-ore, 1 copper-ore

- 1 × automation-science-pack [crafting, 5s]
  - 1 × copper-plate [smelting, 3.2s; other recipes: casting-copper]
    - 1 × copper-ore (mined or pumped)
  - 1 × iron-gear-wheel [crafting, 0.5s; other recipes: casting-iron-gear-wheel]
    - 2 × iron-plate [smelting, 3.2s; other recipes: casting-iron]
      - 2 × iron-ore (mined or pumped)

## chemical-science-pack

Raw per pack: 68.2 crude-oil, 41.6 water, 12 iron-ore, 7.5 copper-ore, 1.5 coal

- 1 × chemical-science-pack [crafting, 24s]
  - 0.5 × sulfur [chemistry, 1s; other recipes: advanced-carbonic-asteroid-crushing, biosulfur]
    - 7.5 × water (mined or pumped)
    - 7.5 × petroleum-gas [oil-processing, 5s; other recipes: basic-oil-processing, coal-liquefaction, empty-petroleum-gas-barrel, light-oil-cracking]
      - 6.82 × water (mined or pumped)
      - 13.6 × crude-oil (mined or pumped)
  - 1.5 × advanced-circuit [crafting, 6s]
    - 3 × plastic-bar [chemistry, 1s; other recipes: bioplastic]
      - 1.5 × coal (mined or pumped)
      - 30 × petroleum-gas [oil-processing, 5s; other recipes: basic-oil-processing, coal-liquefaction, empty-petroleum-gas-barrel, light-oil-cracking]
        - 27.3 × water (mined or pumped)
        - 54.5 × crude-oil (mined or pumped)
    - 6 × copper-cable [crafting, 0.5s; other recipes: casting-copper-cable]
      - 3 × copper-plate [smelting, 3.2s; other recipes: casting-copper]
        - 3 × copper-ore (mined or pumped)
    - 3 × electronic-circuit [crafting, 0.5s]
      - 3 × iron-plate [smelting, 3.2s; other recipes: casting-iron]
        - 3 × iron-ore (mined or pumped)
      - 9 × copper-cable [crafting, 0.5s; other recipes: casting-copper-cable]
        - 4.5 × copper-plate [smelting, 3.2s; other recipes: casting-copper]
          - 4.5 × copper-ore (mined or pumped)
  - 1 × engine-unit [advanced-crafting, 10s]
    - 1 × steel-plate [smelting, 16s; other recipes: casting-steel]
      - 5 × iron-plate [smelting, 3.2s; other recipes: casting-iron]
        - 5 × iron-ore (mined or pumped)
    - 1 × iron-gear-wheel [crafting, 0.5s; other recipes: casting-iron-gear-wheel]
      - 2 × iron-plate [smelting, 3.2s; other recipes: casting-iron]
        - 2 × iron-ore (mined or pumped)
    - 2 × pipe [crafting, 0.5s; other recipes: casting-pipe]
      - 2 × iron-plate [smelting, 3.2s; other recipes: casting-iron]
        - 2 × iron-ore (mined or pumped)

## cryogenic-science-pack

Raw per pack: 10 lithium-brine, 10 ammoniacal-solution, 6 fluoroketone-cold, 1 oxide-asteroid-chunk, 0.6 iron-ore, 0.4 water, 0.08 holmium-ore, 0.04 stone

- 1 × cryogenic-science-pack [cryogenics, 20s, only where pressure 300..300]
  - 3 × ice [crushing, 5s; other recipes: ammoniacal-solution-separation, oxide-asteroid-crushing]
    - 1 × oxide-asteroid-chunk [crushing, 5s; other recipes: carbonic-asteroid-reprocessing, metallic-asteroid-reprocessing, oxide-asteroid-crushing, oxide-asteroid-reprocessing]
      - 1 × oxide-asteroid-chunk (loop, see above)
  - 1 × lithium-plate [smelting, 6.4s]
    - 1 × lithium [chemistry, 20s]
      - 0.2 × holmium-plate [crafting-with-fluid, 1s]
        - 4 × holmium-solution [chemistry, 10s]
          - 0.04 × stone (mined or pumped)
          - 0.08 × holmium-ore (no recipe: raw or special)
          - 0.4 × water (mined or pumped)
      - 10 × lithium-brine (mined or pumped)
      - 10 × ammonia [chemistry, 1s]
        - 10 × ammoniacal-solution (no recipe: raw or special)
  - 6 × fluoroketone-cold [crafting-with-fluid, 0.2s; other recipes: fluoroketone-cooling]
    - 0.12 × fluoroketone-cold-barrel [crafting-with-fluid, 0.2s]
      - 0.12 × barrel [crafting, 1s; other recipes: empty-crude-oil-barrel, empty-fluoroketone-cold-barrel, empty-fluoroketone-hot-barrel, empty-heavy-oil-barrel]
        - 0.12 × steel-plate [smelting, 16s; other recipes: casting-steel]
          - 0.6 × iron-plate [smelting, 3.2s; other recipes: casting-iron]
            - 0.6 × iron-ore (mined or pumped)
      - 6 × fluoroketone-cold (loop, see above)

## electromagnetic-science-pack

Raw per pack: 169 crude-oil, 120 sulfuric-acid, 96.6 water, 13 copper-ore, 12 iron-ore, 4.7 stone, 2.4 holmium-ore, 0.5 coal

- 1 × electromagnetic-science-pack [electromagnetics, 10s, only where magnetic-field 99..99]
  - 1 × supercapacitor [electromagnetics, 10s]
    - 1 × battery [chemistry, 4s]
      - 1 × iron-plate [smelting, 3.2s; other recipes: casting-iron]
        - 1 × iron-ore (mined or pumped)
      - 1 × copper-plate [smelting, 3.2s; other recipes: casting-copper]
        - 1 × copper-ore (mined or pumped)
      - 20 × sulfuric-acid (mined or pumped)
    - 4 × electronic-circuit [crafting, 0.5s]
      - 4 × iron-plate [smelting, 3.2s; other recipes: casting-iron]
        - 4 × iron-ore (mined or pumped)
      - 12 × copper-cable [crafting, 0.5s; other recipes: casting-copper-cable]
        - 6 × copper-plate [smelting, 3.2s; other recipes: casting-copper]
          - 6 × copper-ore (mined or pumped)
    - 2 × holmium-plate [crafting-with-fluid, 1s]
      - 40 × holmium-solution [chemistry, 10s]
        - 0.4 × stone (mined or pumped)
        - 0.8 × holmium-ore (no recipe: raw or special)
        - 4 × water (mined or pumped)
    - 2 × superconductor [electromagnetics, 5s]
      - 1 × copper-plate [smelting, 3.2s; other recipes: casting-copper]
        - 1 × copper-ore (mined or pumped)
      - 1 × plastic-bar [chemistry, 1s; other recipes: bioplastic]
        - 0.5 × coal (mined or pumped)
        - 10 × petroleum-gas [oil-processing, 5s; other recipes: basic-oil-processing, coal-liquefaction, empty-petroleum-gas-barrel, light-oil-cracking]
          - 9.09 × water (mined or pumped)
          - 18.2 × crude-oil (mined or pumped)
      - 1 × holmium-plate [crafting-with-fluid, 1s]
        - 20 × holmium-solution [chemistry, 10s]
          - 0.2 × stone (mined or pumped)
          - 0.4 × holmium-ore (no recipe: raw or special)
          - 2 × water (mined or pumped)
      - 5 × light-oil [oil-processing, 5s; other recipes: coal-liquefaction, empty-light-oil-barrel, heavy-oil-cracking]
        - 5.56 × water (mined or pumped)
        - 11.1 × crude-oil (mined or pumped)
    - 10 × electrolyte [electromagnetics, 5s]
      - 1 × stone (mined or pumped)
      - 10 × heavy-oil [oil-processing, 5s; other recipes: coal-liquefaction, empty-heavy-oil-barrel, simple-coal-liquefaction]
        - 20 × water (mined or pumped)
        - 40 × crude-oil (mined or pumped)
      - 10 × holmium-solution [chemistry, 10s]
        - 0.1 × stone (mined or pumped)
        - 0.2 × holmium-ore (no recipe: raw or special)
        - 1 × water (mined or pumped)
  - 1 × accumulator [crafting, 10s]
    - 2 × iron-plate [smelting, 3.2s; other recipes: casting-iron]
      - 2 × iron-ore (mined or pumped)
    - 5 × battery [chemistry, 4s]
      - 5 × iron-plate [smelting, 3.2s; other recipes: casting-iron]
        - 5 × iron-ore (mined or pumped)
      - 5 × copper-plate [smelting, 3.2s; other recipes: casting-copper]
        - 5 × copper-ore (mined or pumped)
      - 100 × sulfuric-acid (mined or pumped)
  - 25 × electrolyte [electromagnetics, 5s]
    - 2.5 × stone (mined or pumped)
    - 25 × heavy-oil [oil-processing, 5s; other recipes: coal-liquefaction, empty-heavy-oil-barrel, simple-coal-liquefaction]
      - 50 × water (mined or pumped)
      - 100 × crude-oil (mined or pumped)
    - 25 × holmium-solution [chemistry, 10s]
      - 0.25 × stone (mined or pumped)
      - 0.5 × holmium-ore (no recipe: raw or special)
      - 2.5 × water (mined or pumped)
  - 25 × holmium-solution [chemistry, 10s]
    - 0.25 × stone (mined or pumped)
    - 0.5 × holmium-ore (no recipe: raw or special)
    - 2.5 × water (mined or pumped)

## logistic-science-pack

Raw per pack: 5.5 iron-ore, 1.5 copper-ore

- 1 × logistic-science-pack [crafting, 6s]
  - 1 × transport-belt [crafting, 0.5s]
    - 0.5 × iron-plate [smelting, 3.2s; other recipes: casting-iron]
      - 0.5 × iron-ore (mined or pumped)
    - 0.5 × iron-gear-wheel [crafting, 0.5s; other recipes: casting-iron-gear-wheel]
      - 1 × iron-plate [smelting, 3.2s; other recipes: casting-iron]
        - 1 × iron-ore (mined or pumped)
  - 1 × inserter [crafting, 0.5s]
    - 1 × iron-plate [smelting, 3.2s; other recipes: casting-iron]
      - 1 × iron-ore (mined or pumped)
    - 1 × iron-gear-wheel [crafting, 0.5s; other recipes: casting-iron-gear-wheel]
      - 2 × iron-plate [smelting, 3.2s; other recipes: casting-iron]
        - 2 × iron-ore (mined or pumped)
    - 1 × electronic-circuit [crafting, 0.5s]
      - 1 × iron-plate [smelting, 3.2s; other recipes: casting-iron]
        - 1 × iron-ore (mined or pumped)
      - 3 × copper-cable [crafting, 0.5s; other recipes: casting-copper-cable]
        - 1.5 × copper-plate [smelting, 3.2s; other recipes: casting-copper]
          - 1.5 × copper-ore (mined or pumped)

## metallurgic-science-pack

Raw per pack: 90 sulfuric-acid, 20 copper-ore, 14 tungsten-ore, 6 coal, 2 iron-ore, 0.44 calcite

- 1 × metallurgic-science-pack [metallurgy, 10s, only where pressure 4000..4000]
  - 3 × tungsten-carbide [crafting-with-fluid, 1s]
    - 3 × carbon [chemistry, 1s; other recipes: advanced-carbonic-asteroid-crushing, burnt-spoilage, carbonic-asteroid-crushing]
      - 6 × coal (mined or pumped)
      - 60 × sulfuric-acid (mined or pumped)
    - 6 × tungsten-ore (mined or pumped)
    - 30 × sulfuric-acid (mined or pumped)
  - 2 × tungsten-plate [metallurgy, 10s]
    - 8 × tungsten-ore (mined or pumped)
    - 20 × molten-iron [metallurgy, 32s; other recipes: molten-iron-from-lava]
      - 2 × iron-ore (mined or pumped)
      - 0.04 × calcite (mined or pumped)
  - 200 × molten-copper [metallurgy, 32s; other recipes: molten-copper-from-lava]
    - 20 × copper-ore (mined or pumped)
    - 0.4 × calcite (mined or pumped)

## military-science-pack

Raw per pack: 10 stone, 5.75 iron-ore, 5 coal, 0.5 copper-ore

- 1 × military-science-pack [crafting, 10s]
  - 0.5 × piercing-rounds-magazine [crafting, 6s]
    - 0.5 × copper-plate [smelting, 3.2s; other recipes: casting-copper]
      - 0.5 × copper-ore (mined or pumped)
    - 0.25 × steel-plate [smelting, 16s; other recipes: casting-steel]
      - 1.25 × iron-plate [smelting, 3.2s; other recipes: casting-iron]
        - 1.25 × iron-ore (mined or pumped)
    - 0.5 × firearm-magazine [crafting, 1s]
      - 2 × iron-plate [smelting, 3.2s; other recipes: casting-iron]
        - 2 × iron-ore (mined or pumped)
  - 0.5 × grenade [crafting, 8s]
    - 5 × coal (mined or pumped)
    - 2.5 × iron-plate [smelting, 3.2s; other recipes: casting-iron]
      - 2.5 × iron-ore (mined or pumped)
  - 1 × stone-wall [crafting, 0.5s]
    - 5 × stone-brick [smelting, 3.2s]
      - 10 × stone (mined or pumped)

## production-science-pack

Raw per pack: 121 crude-oil, 60.6 water, 52.5 iron-ore, 19.2 copper-ore, 11.7 stone, 3.33 coal

- 1 × production-science-pack [crafting, 21s]
  - 10 × rail [crafting, 0.5s]
    - 5 × stone (mined or pumped)
    - 5 × steel-plate [smelting, 16s; other recipes: casting-steel]
      - 25 × iron-plate [smelting, 3.2s; other recipes: casting-iron]
        - 25 × iron-ore (mined or pumped)
    - 5 × iron-stick [crafting, 0.5s; other recipes: casting-iron-stick]
      - 2.5 × iron-plate [smelting, 3.2s; other recipes: casting-iron]
        - 2.5 × iron-ore (mined or pumped)
  - 0.333 × electric-furnace [crafting, 5s]
    - 3.33 × steel-plate [smelting, 16s; other recipes: casting-steel]
      - 16.7 × iron-plate [smelting, 3.2s; other recipes: casting-iron]
        - 16.7 × iron-ore (mined or pumped)
    - 1.67 × advanced-circuit [crafting, 6s]
      - 3.33 × plastic-bar [chemistry, 1s; other recipes: bioplastic]
        - 1.67 × coal (mined or pumped)
        - 33.3 × petroleum-gas [oil-processing, 5s; other recipes: basic-oil-processing, coal-liquefaction, empty-petroleum-gas-barrel, light-oil-cracking]
          - 30.3 × water (mined or pumped)
          - 60.6 × crude-oil (mined or pumped)
      - 6.67 × copper-cable [crafting, 0.5s; other recipes: casting-copper-cable]
        - 3.33 × copper-plate [smelting, 3.2s; other recipes: casting-copper]
          - 3.33 × copper-ore (mined or pumped)
      - 3.33 × electronic-circuit [crafting, 0.5s]
        - 3.33 × iron-plate [smelting, 3.2s; other recipes: casting-iron]
          - 3.33 × iron-ore (mined or pumped)
        - 10 × copper-cable [crafting, 0.5s; other recipes: casting-copper-cable]
          - 5 × copper-plate [smelting, 3.2s; other recipes: casting-copper]
            - 5 × copper-ore (mined or pumped)
    - 3.33 × stone-brick [smelting, 3.2s]
      - 6.67 × stone (mined or pumped)
  - 0.333 × productivity-module [crafting, 15s]
    - 1.67 × electronic-circuit [crafting, 0.5s]
      - 1.67 × iron-plate [smelting, 3.2s; other recipes: casting-iron]
        - 1.67 × iron-ore (mined or pumped)
      - 5 × copper-cable [crafting, 0.5s; other recipes: casting-copper-cable]
        - 2.5 × copper-plate [smelting, 3.2s; other recipes: casting-copper]
          - 2.5 × copper-ore (mined or pumped)
    - 1.67 × advanced-circuit [crafting, 6s]
      - 3.33 × plastic-bar [chemistry, 1s; other recipes: bioplastic]
        - 1.67 × coal (mined or pumped)
        - 33.3 × petroleum-gas [oil-processing, 5s; other recipes: basic-oil-processing, coal-liquefaction, empty-petroleum-gas-barrel, light-oil-cracking]
          - 30.3 × water (mined or pumped)
          - 60.6 × crude-oil (mined or pumped)
      - 6.67 × copper-cable [crafting, 0.5s; other recipes: casting-copper-cable]
        - 3.33 × copper-plate [smelting, 3.2s; other recipes: casting-copper]
          - 3.33 × copper-ore (mined or pumped)
      - 3.33 × electronic-circuit [crafting, 0.5s]
        - 3.33 × iron-plate [smelting, 3.2s; other recipes: casting-iron]
          - 3.33 × iron-ore (mined or pumped)
        - 10 × copper-cable [crafting, 0.5s; other recipes: casting-copper-cable]
          - 5 × copper-plate [smelting, 3.2s; other recipes: casting-copper]
            - 5 × copper-ore (mined or pumped)

## promethium-science-pack

Raw per pack: 8.74 crude-oil, 5.5 sulfuric-acid, 4.55 water, 4.05 copper-ore, 2.5 iron-ore, 2.5 promethium-asteroid-chunk, 2 lithium-brine, 2 ammoniacal-solution, 1 fluoroketone-cold, 0.625 coal, 0.5 yumako, 0.2 tungsten-ore, 0.036 holmium-ore, 0.018 stone

- 1 × promethium-science-pack [cryogenics, 5s, only where gravity 0..0]
  - 1 × biter-egg [captive-spawner-process, 10s]
  - 0.1 × quantum-processor [electromagnetics, 30s, only where pressure -1.7976931348623155e+308..600]
    - 0.1 × processing-unit [crafting-with-fluid, 10s]
      - 2 × electronic-circuit [crafting, 0.5s]
        - 2 × iron-plate [smelting, 3.2s; other recipes: casting-iron]
          - 2 × iron-ore (mined or pumped)
        - 6 × copper-cable [crafting, 0.5s; other recipes: casting-copper-cable]
          - 3 × copper-plate [smelting, 3.2s; other recipes: casting-copper]
            - 3 × copper-ore (mined or pumped)
      - 0.2 × advanced-circuit [crafting, 6s]
        - 0.4 × plastic-bar [chemistry, 1s; other recipes: bioplastic]
          - 0.2 × coal (mined or pumped)
          - 4 × petroleum-gas [oil-processing, 5s; other recipes: basic-oil-processing, coal-liquefaction, empty-petroleum-gas-barrel, light-oil-cracking]
            - 3.64 × water (mined or pumped)
            - 7.27 × crude-oil (mined or pumped)
        - 0.8 × copper-cable [crafting, 0.5s; other recipes: casting-copper-cable]
          - 0.4 × copper-plate [smelting, 3.2s; other recipes: casting-copper]
            - 0.4 × copper-ore (mined or pumped)
        - 0.4 × electronic-circuit [crafting, 0.5s]
          - 0.4 × iron-plate [smelting, 3.2s; other recipes: casting-iron]
            - 0.4 × iron-ore (mined or pumped)
          - 1.2 × copper-cable [crafting, 0.5s; other recipes: casting-copper-cable]
            - 0.6 × copper-plate [smelting, 3.2s; other recipes: casting-copper]
              - 0.6 × copper-ore (mined or pumped)
      - 0.5 × sulfuric-acid (mined or pumped)
    - 0.1 × tungsten-carbide [crafting-with-fluid, 1s]
      - 0.1 × carbon [chemistry, 1s; other recipes: advanced-carbonic-asteroid-crushing, burnt-spoilage, carbonic-asteroid-crushing]
        - 0.2 × coal (mined or pumped)
        - 2 × sulfuric-acid (mined or pumped)
      - 0.2 × tungsten-ore (mined or pumped)
      - 1 × sulfuric-acid (mined or pumped)
    - 0.1 × superconductor [electromagnetics, 5s]
      - 0.05 × copper-plate [smelting, 3.2s; other recipes: casting-copper]
        - 0.05 × copper-ore (mined or pumped)
      - 0.05 × plastic-bar [chemistry, 1s; other recipes: bioplastic]
        - 0.025 × coal (mined or pumped)
        - 0.5 × petroleum-gas [oil-processing, 5s; other recipes: basic-oil-processing, coal-liquefaction, empty-petroleum-gas-barrel, light-oil-cracking]
          - 0.455 × water (mined or pumped)
          - 0.909 × crude-oil (mined or pumped)
      - 0.05 × holmium-plate [crafting-with-fluid, 1s]
        - 1 × holmium-solution [chemistry, 10s]
          - 0.01 × stone (mined or pumped)
          - 0.02 × holmium-ore (no recipe: raw or special)
          - 0.1 × water (mined or pumped)
      - 0.25 × light-oil [oil-processing, 5s; other recipes: coal-liquefaction, empty-light-oil-barrel, heavy-oil-cracking]
        - 0.278 × water (mined or pumped)
        - 0.556 × crude-oil (mined or pumped)
    - 0.1 × carbon-fiber [organic, 5s]
      - 0.1 × carbon [chemistry, 1s; other recipes: advanced-carbonic-asteroid-crushing, burnt-spoilage, carbonic-asteroid-crushing]
        - 0.2 × coal (mined or pumped)
        - 2 × sulfuric-acid (mined or pumped)
      - 1 × yumako-mash [organic, 1s]
        - 0.5 × yumako (no recipe: raw or special)
    - 0.2 × lithium-plate [smelting, 6.4s]
      - 0.2 × lithium [chemistry, 20s]
        - 0.04 × holmium-plate [crafting-with-fluid, 1s]
          - 0.8 × holmium-solution [chemistry, 10s]
            - 0.008 × stone (mined or pumped)
            - 0.016 × holmium-ore (no recipe: raw or special)
            - 0.08 × water (mined or pumped)
        - 2 × lithium-brine (mined or pumped)
        - 2 × ammonia [chemistry, 1s]
          - 2 × ammoniacal-solution (no recipe: raw or special)
    - 1 × fluoroketone-cold [crafting-with-fluid, 0.2s; other recipes: fluoroketone-cooling]
      - 0.02 × fluoroketone-cold-barrel [crafting-with-fluid, 0.2s]
        - 0.02 × barrel [crafting, 1s; other recipes: empty-crude-oil-barrel, empty-fluoroketone-cold-barrel, empty-fluoroketone-hot-barrel, empty-heavy-oil-barrel]
          - 0.02 × steel-plate [smelting, 16s; other recipes: casting-steel]
            - 0.1 × iron-plate [smelting, 3.2s; other recipes: casting-iron]
              - 0.1 × iron-ore (mined or pumped)
        - 1 × fluoroketone-cold (loop, see above)
  - 2.5 × promethium-asteroid-chunk (no recipe: raw or special)

## space-science-pack

Raw per pack: 4 sulfuric-acid, 0.4 iron-ore, 0.4 coal, 0.0667 oxide-asteroid-chunk

- 1 × space-science-pack [crafting, 15s, only where gravity 0..0]
  - 0.2 × ice [crushing, 5s; other recipes: ammoniacal-solution-separation, oxide-asteroid-crushing]
    - 0.0667 × oxide-asteroid-chunk [crushing, 5s; other recipes: carbonic-asteroid-reprocessing, metallic-asteroid-reprocessing, oxide-asteroid-crushing, oxide-asteroid-reprocessing]
      - 0.0667 × oxide-asteroid-chunk (loop, see above)
  - 0.4 × iron-plate [smelting, 3.2s; other recipes: casting-iron]
    - 0.4 × iron-ore (mined or pumped)
  - 0.2 × carbon [chemistry, 1s; other recipes: advanced-carbonic-asteroid-crushing, burnt-spoilage, carbonic-asteroid-crushing]
    - 0.4 × coal (mined or pumped)
    - 4 × sulfuric-acid (mined or pumped)

## utility-science-pack

Raw per pack: 159 crude-oil, 79.7 water, 49.8 copper-ore, 33 iron-ore, 16.7 sulfuric-acid, 3.83 coal

- 1 × utility-science-pack [crafting, 21s]
  - 0.667 × processing-unit [crafting-with-fluid, 10s]
    - 13.3 × electronic-circuit [crafting, 0.5s]
      - 13.3 × iron-plate [smelting, 3.2s; other recipes: casting-iron]
        - 13.3 × iron-ore (mined or pumped)
      - 40 × copper-cable [crafting, 0.5s; other recipes: casting-copper-cable]
        - 20 × copper-plate [smelting, 3.2s; other recipes: casting-copper]
          - 20 × copper-ore (mined or pumped)
    - 1.33 × advanced-circuit [crafting, 6s]
      - 2.67 × plastic-bar [chemistry, 1s; other recipes: bioplastic]
        - 1.33 × coal (mined or pumped)
        - 26.7 × petroleum-gas [oil-processing, 5s; other recipes: basic-oil-processing, coal-liquefaction, empty-petroleum-gas-barrel, light-oil-cracking]
          - 24.2 × water (mined or pumped)
          - 48.5 × crude-oil (mined or pumped)
      - 5.33 × copper-cable [crafting, 0.5s; other recipes: casting-copper-cable]
        - 2.67 × copper-plate [smelting, 3.2s; other recipes: casting-copper]
          - 2.67 × copper-ore (mined or pumped)
      - 2.67 × electronic-circuit [crafting, 0.5s]
        - 2.67 × iron-plate [smelting, 3.2s; other recipes: casting-iron]
          - 2.67 × iron-ore (mined or pumped)
        - 8 × copper-cable [crafting, 0.5s; other recipes: casting-copper-cable]
          - 4 × copper-plate [smelting, 3.2s; other recipes: casting-copper]
            - 4 × copper-ore (mined or pumped)
    - 3.33 × sulfuric-acid (mined or pumped)
  - 0.333 × flying-robot-frame [crafting, 20s]
    - 0.333 × steel-plate [smelting, 16s; other recipes: casting-steel]
      - 1.67 × iron-plate [smelting, 3.2s; other recipes: casting-iron]
        - 1.67 × iron-ore (mined or pumped)
    - 0.667 × battery [chemistry, 4s]
      - 0.667 × iron-plate [smelting, 3.2s; other recipes: casting-iron]
        - 0.667 × iron-ore (mined or pumped)
      - 0.667 × copper-plate [smelting, 3.2s; other recipes: casting-copper]
        - 0.667 × copper-ore (mined or pumped)
      - 13.3 × sulfuric-acid (mined or pumped)
    - 1 × electronic-circuit [crafting, 0.5s]
      - 1 × iron-plate [smelting, 3.2s; other recipes: casting-iron]
        - 1 × iron-ore (mined or pumped)
      - 3 × copper-cable [crafting, 0.5s; other recipes: casting-copper-cable]
        - 1.5 × copper-plate [smelting, 3.2s; other recipes: casting-copper]
          - 1.5 × copper-ore (mined or pumped)
    - 0.333 × electric-engine-unit [crafting-with-fluid, 10s]
      - 0.667 × electronic-circuit [crafting, 0.5s]
        - 0.667 × iron-plate [smelting, 3.2s; other recipes: casting-iron]
          - 0.667 × iron-ore (mined or pumped)
        - 2 × copper-cable [crafting, 0.5s; other recipes: casting-copper-cable]
          - 1 × copper-plate [smelting, 3.2s; other recipes: casting-copper]
            - 1 × copper-ore (mined or pumped)
      - 0.333 × engine-unit [advanced-crafting, 10s]
        - 0.333 × steel-plate [smelting, 16s; other recipes: casting-steel]
          - 1.67 × iron-plate [smelting, 3.2s; other recipes: casting-iron]
            - 1.67 × iron-ore (mined or pumped)
        - 0.333 × iron-gear-wheel [crafting, 0.5s; other recipes: casting-iron-gear-wheel]
          - 0.667 × iron-plate [smelting, 3.2s; other recipes: casting-iron]
            - 0.667 × iron-ore (mined or pumped)
        - 0.667 × pipe [crafting, 0.5s; other recipes: casting-pipe]
          - 0.667 × iron-plate [smelting, 3.2s; other recipes: casting-iron]
            - 0.667 × iron-ore (mined or pumped)
      - 5 × lubricant [chemistry, 1s; other recipes: biolubricant, empty-lubricant-barrel]
        - 5 × heavy-oil [oil-processing, 5s; other recipes: coal-liquefaction, empty-heavy-oil-barrel, simple-coal-liquefaction]
          - 10 × water (mined or pumped)
          - 20 × crude-oil (mined or pumped)
  - 1 × low-density-structure [crafting, 15s; other recipes: casting-low-density-structure]
    - 20 × copper-plate [smelting, 3.2s; other recipes: casting-copper]
      - 20 × copper-ore (mined or pumped)
    - 2 × steel-plate [smelting, 16s; other recipes: casting-steel]
      - 10 × iron-plate [smelting, 3.2s; other recipes: casting-iron]
        - 10 × iron-ore (mined or pumped)
    - 5 × plastic-bar [chemistry, 1s; other recipes: bioplastic]
      - 2.5 × coal (mined or pumped)
      - 50 × petroleum-gas [oil-processing, 5s; other recipes: basic-oil-processing, coal-liquefaction, empty-petroleum-gas-barrel, light-oil-cracking]
        - 45.5 × water (mined or pumped)
        - 90.9 × crude-oil (mined or pumped)
