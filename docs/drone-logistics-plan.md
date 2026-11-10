# Replacing LONG conveyor belts with trains or drone logistics chests (plan, 2026-11-09, scope set by the Captain)

## Where we are
- One logistic network covers the whole revealed map: 721 roboports, 36,050 construction and 36,600 logistic robots (50 of each per roboport, group "Nauvis Land").
- Chests researched: passive provider, active provider, storage, buffer, requester. In play: 95 passive providers and 22 storage chests, no requesters yet.
- Belts today: 7,359 fast + 2,604 yellow + 292 express belt tiles, 618 undergrounds, 93 splitters. About 4,400 iron plates, 3,600 copper plates, 3,400 plastic, 5,600 coal, 3,200 stone sit on belts right now.
- Inserters: 687 fast, 164 bulk, 151 long-handed, 155 basic.
- Every belt bug we fixed this week (iron on the copper lane, plastic or sulfur on the circuit lane, EC and AC tapped upstream of where they are made, lane-limited iron) comes from belts. A requester chest asks for an item by name, so none of those can happen.

## Scope (the Captain, 2026-11-09)
Short belts inside a compact factory area stay belts; any belt that carries goods over a long distance becomes a train (bulk) or a drone chest pair (mixed or moderate flow). Rule of thumb: a connected belt network that spans 100 tiles or more is a candidate; the east bus trunks (about 100 tiles, one tight block) stay as belts for now.

## The long lines found today (connected belt networks spanning 60+ tiles; 35 in all, the 20 longest)
| Line (span, pieces) | Carries | Becomes |
|---|---|---|
| x -326..-22, y -63..-55 (304, 321) | iron plate | drone: provider chests at the old smelters, requesters at consumers |
| x -345..-84, y -137..-63 (261, 362) and x -79..47, y -137 (125, 126) | plastic, sulfur (oil site to bus) | drone (provider at the oil site, requester at the bus head) |
| x -341..-81, y -55..-50 (260, 266); x -348..-210 (138); x -210..-83 (127) | red/green science packs | drone straight to the lab chests (no pack belt, no pack train leg) |
| x -217..22, y -37..-25 (238, 251); x -333..-219, y -41..-37 (114); x 73..131 (101) | military and purple packs | drone straight to the labs |
| x -136..-10, y -213..-138 (126, 202) | space science (pad to labs) | drone |
| x 80..100, y -399..-148 (251, 272) and x 82, y -398..-148 (250, 251) | stone and stone brick (stone depot to bus) | drone or train (bulk) |
| x -208..37 (244, 374), x -242..-17 (225, 239) | coal, copper ore (old base) | coal stays train/belt near boilers, ore by train or in place |
| x -209..-34 (175, 205), x -326..-216 (110, 111) | copper plate, gears | drone |
| x 17..38, y -64..49 (112, 174) and x 91..111, y -147..-46 (101, 217) | coal | train from Coal2, short local belts |
| the 330-tile rocket fuel line | rocket fuel | drone (requester chests at the loco feeders) |
| the 700-tile yellow/military pack route | packs | drone |

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

## Phases, long lines first (each reversible: save first, run both in parallel, measure, only then remove the belt)
0. **Survey** (`fx.py logistics survey AREA`, to build): groups belts into lines, reads what each carries and how fast (production statistics and belt samples), lists which machines it feeds, and ranks lines by flow. Output: the conversion list, easiest first.
1. **Pilot: science pack delivery to the labs** (the longest belts, low flow, one clear consumer: the labs). Provider chests at every pack assembler or port, requester chests beside the labs, labs fed by inserters from the chests. Gate: lab pack stock and research rate equal or better over an hour of game time, and the old pack belts and train leg can be removed.
1b. **Optional second pilot: the yellow block** (short belts, but starved in odd ways). It has 5 machine types fed by 5 taps, is already starved or jammed in odd ways, and its feeders are all low flow. Replace its S1/S2/N1/N2 belts and sorters with requester chests. Gate: yellow output equals or beats the belt version for an hour of game time, and the bottleneck report shows zero new findings.
2. **Oil site to bus:** plastic and sulfur (261 + 125 tiles) and the fuel line (330). Provider chests at the oil site, requester hub at the bus head feeding the trunk heads over a few tiles of belt.
2b. **East bus consumers** only where a feeder is long or jam-prone; the compact bus itself stays belts.
3. **Plates and ore:** the 304-tile iron belt, copper plate and gear lines, stone and brick, plates from the new outposts (chests already). Bulk hauls that are one item in volume stay on trains.
4. **Retire what is replaced:** remove each long line only when nothing still picks from or drops onto it; then reclaim ground with `fx.py compact`.
5. **Old base (west):** its long runs convert in the order above; the dense core stays belts.

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


## Done so far (2026-11-09)
- **Train fueling by drone:** every loco feeder chest (Coal2 x2, science front, copper depot, iron depot x2, Callie) and the four belt tiles at the iron and copper unload stops are now requester chests asking for rocket fuel (40-60 each). Measured: empty requesters filled in under a minute from the provider chest at (-253.5,-127.5), which the train unload keeps full. The 330-tile fuel belt was removed (121 pieces; the original belt tile at the unload splitter restored).
- **Copper plate outpost** (north patch, x -60..-16, y -544..-417): 71 drills, 54 furnaces, 54 plate chests, powered through new substations; made 3,700+ plates in the first minutes of game time.
- **Iron plate outpost** (south-west patch, x -492..-324, y 260..318): 137 drills, 72 furnaces, 72 plate chests (about 45 ore/s through one express belt; half the drills idle by design until a second smelter line is added).
- **Base hubs:** 6 copper-plate requester chests with fast inserters onto the copper unload belt (x 83.5..88.5, y -144.5) and 4 iron-plate requester chests onto the iron feeder belt (x 69.5..72.5, y -156.5), 1,200 plates each. The iron hub filled to 900+ plates in a minute; the copper hub empties into the belt as fast as it fills.
- Gotcha: dropping 11,000 uncharged robots into new roboports made demand spike to about 200 MW for a minute (machines went low_power until they were charged). Next time add robots in batches.
- Gotcha: `build_roboport_grid.py --revealed` makes the revealed map grow (roboports chart their surroundings), so each run finds new cells. Run it only on purpose.
- Next: pack delivery to the labs by drone (the pilot), plastic/sulfur from the oil site, stone and brick, more outposts (iron (-723,-317), copper (317,233), (732,97), (-902,-345)).

## Update 2026-11-09: tooling built
`fx.py logistics survey|convert|retire` now exist (scripts/logistics.py, see the factorio skill). Tried once: the rail assembler pair converted cleanly (4 requesters, 2 providers, provider chests filled with rails), but their stone and
iron-stick inputs have no provider in the network, so they wait. Not yet tested: retire with --apply, undergrounds and splitters (skipped by convert), whole-chunk conversions.
