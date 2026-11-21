# Edgerunner 3: the Universal 1 Proto with a big T on its nose (2026-11-21)

The Captain's decision (replaces the inverted-triangle layout of `docs/edgerunner-2-plan.md`): "take the universal proto and use that as the
basis for our edge runner ... add a big T shape onto the top of it, where it breaks through with railguns everything that it comes in
contact with ... and railguns to the sides as well, because when we're at rest we need railguns to protect from the incoming ones while we're
loading". `scripts/edge3_design.py plan | arcs` reads the live ship and computes the extension; nothing is placed. The way back is the
blueprint `universal-1-proto v1` (designs/, and the Design library chest on Nauvis).

## What the live Universal 1 Proto gives us
947 entities, 3,414 deck tiles, 723 t, nose north at y -29, 12 cargo bays (659 hub slots), 4 collectors, 16 rocket turrets, 30 guns, 84 panels,
4 thrusters, a closed ammunition loop round the hull (outer lane rockets, inner lane magazines), crushers and works that run on chunks.
It flew three clean round trips Nauvis-Gleba; it has never met a big or huge asteroid.

## The extension (numbers from the script)
- T bar: 160 wide x 37 deep on the nose. 6,132 new deck tiles = 123 rocket launches of foundation; the ship becomes about 9,500 tiles.
- Front line: 45 railguns facing north along the bar's top row (4 spots go to collectors, which need empty space in front), feed inserters
  and one rounds belt behind. Nothing of ours stands in front, so no shot line crosses our own parts.
- The 16 rocket turrets become railguns on the same pads (rockets cannot hurt a huge asteroid: 99% explosion resistance). 2 of those pads, at the
  very nose, would fire across the bar: they are dropped or become guns.
- 16 railguns on new deck outside the flanks for the ship at rest, facing west or east (2 turned south-west/south-east where a west arc
  would cross the bar), 2 at the stern: 79 railguns in all. Fouled shot lines: 0 for the ears and the front line.
- Collectors (4) move to the bar's top row (wing tips and mid-wings); the chunk belt is re-laid down the stem.
- Power: 79 railguns all firing about 308 MW. Fusion plant in the bar's middle (4 reactors, 8 generators, 500 MW) and room for about 320
  accumulators (10 GJ) in the wings.
- The loop's outer lane carries railgun rounds (the hub's rocket port changes its filter); a filtered splitter at the nose feeds the bar's belt.

## Problems the numbers raised (to settle before anything is built)
1. **Rounds do not fit.** Railgun rounds stack to 10: the whole hub (659 slots) holds 6,590. A 30,000-round reserve needs about 3,000 slots, i.e.
   some 35 more legendary cargo bays chained to the hub (the bar's wings can hold them, behind the accumulators, if they touch the bay chain).
   Or a smaller reserve (6,000 rounds, about 1.7 hours at one kill a second) plus rounds made aboard.
2. **Mass and thrust.** The bar roughly doubles the ship (estimate by the live deck-to-weight ratio, about +1,300 t); four thrusters will not
   do. Thruster count and the speed limiter must be set from the game's own thrust formula before the first leg.
3. **Rounds works.** Chunks give only a few rounds a minute of steel and explosives; the works are a supplement, so the reserve is the doctrine.
4. **The Universal proto is the fleet's candidate hull too** (the Captain's earlier wish to try it as the shuttle replacement). Edgerunner 3 should
   be a CLONE built from the blueprint on a new platform, leaving the proto flying.

## Stages
0. Blueprint of the clone's base: done (`universal-1-proto v1`, with deck tiles).
1. This layout (done). Then settle the three problems above.
2. New platform from the blueprint at Nauvis, then the bar in stages, a blueprint export after each.
3. Gleba to Aquilo at 30 km/s, then Aquilo toward the edge at 10 km/s under `edge_guard.py`, first 5,000 km only.
