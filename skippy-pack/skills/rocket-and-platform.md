# Skill: rocket parts, silos, orbital resources

Rockets: a part is 1 processing unit + 1 low density structure + 1 rocket fuel; 50 parts per rocket. Silos launch only when a platform in orbit asks for the contents (auto launch), so the limit is the platform and the cargo (foundations: 50 per rocket by weight).
1. Parts first: `pu-block --extend N`, `cells --kind ec|ac|cable|lds|steel`. A silo at full speed uses 0.33 of each part per second.
2. `silos --centers X Y ...` (each: 3 requester chests for parts on the north, 3 for cargo on the south; the first cargo chest asks for foundations).
3. Cargo supply: `cells --kind foundation` fed by steel and cable; storage = chained red provider chests, never yellow chests.
4. Orbit: see docs/space-factory-plan.md. Measure collectors on platform-1 before sizing anything. Tier 2 asteroid recipes need techs gated behind space and agricultural science.
Power: silos draw about 30 MW each while crafting; the autopilot pauses the extra silos when accumulators fall below 30 percent.
