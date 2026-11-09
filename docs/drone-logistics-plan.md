# Replacing conveyor belts with drone logistics chests (plan, 2026-11-09)

## Where we are
- One logistic network covers the whole revealed map: 721 roboports, 36,050 construction and 36,600 logistic robots (50 of each per roboport, group "Nauvis Land").
- Chests researched: passive provider, active provider, storage, buffer, requester. In play: 95 passive providers and 22 storage chests, no requesters yet.
- Belts today: 7,359 fast + 2,604 yellow + 292 express belt tiles, 618 undergrounds, 93 splitters. About 4,400 iron plates, 3,600 copper plates, 3,400 plastic, 5,600 coal, 3,200 stone sit on belts right now.
- Inserters: 687 fast, 164 bulk, 151 long-handed, 155 basic.
- Every belt bug we fixed this week (iron on the copper lane, plastic or sulfur on the circuit lane, EC and AC tapped upstream of where they are made, lane-limited iron) comes from belts. A requester chest asks for an item by name, so none of those can happen.

## What drones are good and bad at
- Good: long distance (the 330-tile fuel line, the plastic line, plates from outposts), many different items to many places (the bus), low-to-medium flow, anything a lane bug can hit.
- Bad: very high flow over a short distance. Ore into furnaces, a drill row onto a collector, furnace output to a chest all stay as a few belts or direct insertion. A chest-to-machine hop is limited by the inserter (fast inserter about 2.3 swings/s; use bulk inserters or several).
- Cost: every robot in flight costs server time. 36,000 idle robots cost almost nothing (566 of 600 ticks/s); thousands in flight will cost real UPS. So the target is "ask only for what is consumed" (small request amounts), never "stock every chest full".
- Trains stay for bulk (coal, ore, plate hauls), as the Captain said.

## Target design
1. **Supply side (passive provider chests):** every producer drops its output into a passive provider chest instead of a belt: furnace outputs (the outposts already do this), assembler outputs (circuits, steel, plastic, cable, science packs), the oil site products (plastic, sulfur, rocket fuel), the platform landing pad.
2. **Demand side (requester chests):** every consumer machine (or small group of machines sharing one chest) gets a requester chest with an inserter. The request is the recipe's ingredients for about 60 seconds of work, set from the recipe table, so the chest is never full of anything else.
3. **Buffers:** storage chests as optional local stock where a producer outruns the swarm.
4. **Science:** packs go provider chest -> requester chest at the labs; no more pack belt or train for them.
5. **What stays a belt:** drill -> furnace ore lines inside a mine or depot, and furnace -> output chest hops.

## Phases (each reversible: save first, convert one block, measure, only then remove belts)
0. **Survey** (`fx.py logistics survey AREA`, to build): groups belts into lines, reads what each carries and how fast (production statistics and belt samples), lists which machines it feeds, and ranks lines by flow. Output: the conversion list, easiest first.
1. **Pilot: the yellow block.** It has 5 machine types fed by 5 taps, is already starved or jammed in odd ways, and its feeders are all low flow. Replace its S1/S2/N1/N2 belts and sorters with requester chests. Gate: yellow output equals or beats the belt version for an hour of game time, and the bottleneck report shows zero new findings.
2. **Bus consumers:** convert the east bus consumers row by row (EC, cable, AC, military, purple). Producers go to provider chests. Gate after each row: same output, UPS within 5 percent.
3. **Long lines:** plastic line, rocket-fuel line, science pack routes, iron/copper plates from outposts to the bus heads. This is where drones win most. Remove each belt line only after its replacement has run clean.
4. **Retire the bus trunks:** when no tap remains, remove the trunks, splitters and filter sorters. Then run `fx.py compact` on the freed area to reclaim ground.
5. **Old base (west):** last, since it is the oldest and densest.

## Tooling to build (in order)
1. `fx.py logistics survey AREA` (belt lines, flows, consumers).
2. `fx.py logistics convert AREA [--keep-belts]`: for each machine in the area derive its inputs and outputs from the recipe, place the requester chest + inserter on a free side, set the request (60 s of consumption, bounded by chest slots), place provider chests for outputs, leave the belts in place (`--keep-belts`) so both run in parallel during the trial.
3. `fx.py logistics retire LINE`: remove a belt line after checking that nothing still picks from or drops onto it.
4. Add to `fx.py bottlenecks`: requester chests that are short, provider chests that are full, robots stuck without charge, and network congestion by roboport.
5. A UPS guard in the autopilot: if ticks/s at the current game speed falls below 90 percent, lower the speed one step and log it.

## Numbers to check before phase 1
- Robot payload and speed with current research (worker-robots-storage 1-2, speed 1-2 done; speed 3-5 and storage 3 are in the queue and need yellow).
- How many robots one requester chest pulls at once (it asks for the full shortfall, so cap requests per chest).
- Chest slots: 48 per chest; request 1 to 2 slots per item so one chest can hold several ingredients.
- Roboport charge pads: 4 per cell; the solar kits are small (3 panels), so check the roboport power status at night before the swarm gets busy.

## Not started, needs your word
- The copper outpost (north patch) is built but partly: 684 of 739 pieces placed, 55 blocked by roboport kits and rails in its footprint. Under this plan it is a supplier (plates into passive provider chests), so I would finish it and then add the base-side requester hub, not extend belts.
- No belt has been removed. Phase 0 and the pilot are the next steps if you approve.
