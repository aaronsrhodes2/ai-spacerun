# Path to space science packs (2026-11-07)

Goal (the Captain): keep going until the factory produces space science packs.

## What the game says (from the live recipes)
- space-science-pack recipe: 1 ice + 2 iron plate + 1 carbon -> 5 packs (15 s). It is locked behind the tech
  `space-science-pack`, a TRIGGER tech: it fires when an `asteroid-collector` is built (on a space platform).
  Ice comes from oxide asteroid chunks, carbon from carbonic chunks, iron from metallic chunks (crushers on the platform).
- `space-platform` tech (unlocks asteroid-collector, crusher, cargo-bay, the crushing recipes) is a trigger tech: it fires when a
  space platform is created in the game's platform UI. Creating "Alpha" through the script API did NOT fire it
  (platform exists, state 0 = waiting for its starter pack, tech still unresearched). Needs the Captain to create a platform in
  the map's Platforms tab, or a real launch.
- `space-platform-thruster` tech unlocks the thruster. rocket-silo, rocket-fuel, low-density-structure, processing-unit,
  chemical/production/utility/military science techs are all researched.
- A rocket needs 50 rocket parts; rocket-part = 1 processing unit + 1 low density structure + 1 rocket fuel.

## Quantities for the first launch (the platform starter pack)
- starter pack: 20 steel + 20 processing units + 60 platform foundations (each 20 steel + 20 copper cable) = 1,220 steel, 1,200 cable.
- rocket: 50 processing units, 50 low density structures, 50 rocket fuel.
- => 70 processing units (1,400 electronic circuits, 140 advanced circuits, 350 sulfuric acid), 50 LDS (1,000 copper, 100 steel,
  250 plastic), 50 rocket fuel (500 solid fuel + 500 light oil; solid fuel is 10 light oil each, so 5,500 light oil in all).
- The silo itself and platform entities are placed free once researched (rule: placed entities are free; machine inputs are not).
- Then the platform needs thrusters (steel, processing units, electric engines), asteroid collectors (processing units, electric
  engines, LDS), crushers, and thruster fuel/oxidizer made on the platform from asteroids.

## State of the factory against that
- Oil: 7 pumpjacks (about 120 crude/s at the current yields), 2 refineries on basic oil processing using about 40/s.
  Advanced oil processing is researched; light oil is the big need (5,500 for rockets).
- Iron 7.5/s and copper 7/s arrive on the bus by train; steel 0.375/s; stone brick about 3/s; coal by train.
- Plastic and sulfuric acid exist at the refinery (west); the bus does not carry them.

## Order of work
1. [done] military science plant; packs belt to the research train's intake.
2. Get `space-platform` researched (Captain creates a platform in the UI) and queue `space-platform-thruster`.
3. Light oil: advanced-oil-processing refineries + solid fuel + rocket fuel rows.
4. Processing units (electronic circuit, advanced circuit, acid rows), LDS row, foundation row, steel capacity.
5. Place the rocket silo, feed parts by belts, launch the starter pack; platform comes alive.
6. Platform kit launches (thrusters, collectors, crushers); build the first asteroid collector -> `space-science-pack` fires.
7. Space science pack production on the platform (ice + iron + carbon).

## Oil survey (2026-11-08)
Fields (distance from the Captain's new oil complex at about (-260,-270)): current (-314,-292) 7 wells, now 752% total yield (was 1197%, depleting), 14 nests within 120;
best new: (-702,-403) 15 wells 3205% total, no nests within 120, 462 tiles; then (-932,-160) 6 wells 1347%; (52,351) 7 wells 1615% with 7 nests; (383,-684) 14 wells 3466%
and (573,-353) 11 wells 2807% (both far east, no nests). Copper depot expansion was dropped: the Captain is already building on that patch.
