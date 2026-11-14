# Egg farm plan (read-only study, 2026-11-14, tick ~50.68M)

## 0. Urgent finding: the captured spawner is already gone
- `find_entities_filtered{name='captive-biter-spawner'}` returns 0 on every surface. At (151.5, -2303.5) there is a wild
  `biter-spawner`, force enemy, 365.6 hp (full health). Per the wiki a starved captive spawner loses 1 hp/s and reverts at 0 hp
  "with full health"; that is what happened. Nothing to feed or save there. The capture cost 1 rare rocket (9 left in the
  Captain's inventory).
- So option A (outpost at the 2.3k-tile spawner) has nothing to protect any more. Dropped (section 6).

## 1. Verified facts
- Prototype `captive-biter-spawner`: assembling machine, 350 hp, collision 4.4 x 4.4 (selection 5x5), burner energy source,
  fuel category `food` only, fuel inventory 1 slot, 100 kW (1666.7 J/tick), crafting category `captive-spawner-process`,
  surface condition pressure = 1000 (Nauvis only; no other surface has any). Its one recipe `biter-egg`: no ingredients,
  10 s, +5 eggs (0.5 eggs/s = 30/min = 1,800/h). Output slot holds 100 (wiki).
- `bioflux` = 6 MJ = exactly 60 s of burn: 1 bioflux/min = 60/h per spawner. Wiki: freshness does not matter for the fuel,
  but bioflux itself spoils in about 120 min (gleba_core.py notes), so it cannot be stockpiled for days.
- **Eggs spoil in 30 min (normal quality) into a BIG BITER, but not while inside the spawner.** Never leave eggs in a chest
  or the network; take them only when a machine is ready to use them.
- Only one recipe makes `biter-egg` (the captive spawner). `pentapod-egg` is Gleba's own item and has no link. `nutrients-from-biter-egg`,
  `productivity-module-3`, promethium science and biolab use eggs. No loot or other source. Recycling an egg returns 25%, useless.
- The item recipe `captive-biter-spawner` (15 U-235, 10 eggs, 1 capture rocket, 100 cold fluoroketone, in cryogenics) exists
  but its tech `captive-biter-spawner` is NOT researched (recipe disabled). Researching it would let us craft more spawners
  and place them anywhere on Nauvis (it cannot be picked up once placed). Not needed for the first stage.
- Capture rocket: 2 steel, 2 processing units, 1 flying robot frame, 20 bioflux, 10 s. The capture rocket recipe is enabled.
  The network holds 0 frames and 0 bioflux, so make no more rockets for now; the 9 rare ones are enough.
- Enemy state: `surface.peaceful_mode = true` on Nauvis, expansion off, pollution off, evolution 0.019 (only small worms in
  the central nests). Wild units do not attack our things; roboports with solar kits already stand 4 to 10 tiles from nests.
- Roboport: logistic range 25, construction 55. Poles: substation wire 18 (supply 9), big pole wire 32, medium 9.

## 2. Egg need (computed)
Installed productivity-module-2 slots, all surfaces (4,584 in total): Nauvis 2,625; Vulcanus 233; Gleba 95; Fulgora 35; platforms 1,596
(platforms 12, 13, 16, 17 hold 343, 353, 327, 400). Prod-1 slots: 88. Slots total about 8,400; the rest are speed.
- Full upgrade of every p2 slot: **4,584 eggs** (+88 if the p1 slots go to p3 via p2 first), 22.9k advanced circuits, 22.9k processing units.
- Recipe: 1 egg + 5 adv + 5 PU + **4 productivity-module-2**. That last term is the real limit: 4,584 p3 eat 18,336 p2; the 4,584 pulled
  out of the machines return, leaving 13,752 new p2, roughly 344k advanced circuits. The network holds 147k adv, 90k PU, 3,465 p2.
- Gain per slot: p3 +10% productivity, -15% speed, +80% energy; p2 +6%, -10%, +60%. So +4 points per slot, +3.8% output relative.
  Modest. Eggs are the cheap part; circuits and module-2 stock are the limit.
- **Staged target** (decide by product value per slot, not by count):
  S1 500 p3 (500 eggs; 2,000 p2, covered by stock 3,465): put into the highest-value slots first (promethium/space-science
  assemblers, foundries, then the wheel crushers; speed slots at Gleba labs stay speed).
  S2 +1,500 once S1 is measured (does the output rise as computed?). S3 the rest only if circuits allow. One spawner supplies
  1,800 eggs/h, so egg supply is never the pacing item.

## 3. Options
| | Where | Eggs/h | Build | Verdict |
|---|---|---|---|---|
| A | captured spawner 2.3k tiles north | n/a (dead) | 1,150 rails or 128 substations or 48 roboports + defence | dropped |
| **B** | **nest inside the base, capture there** | up to 1,800 | 1 inserter, 1 chest, 1 requester chest + inserter; mall units | **recommended** |
| C | other egg source | none exists | | none |
| D | stage the p3 target | see section 2 | | adopted |

Nearest nests to the roboport network (936 roboports, whole map): 77,403 (4 tiles from a roboport), 649,-33, -460,-455 and many others
within 4 to 12 tiles. Sampled 1,756 spawners; every nest I checked has a roboport with solar kit and substations inside 25 tiles.

## 4. Recommended: capture a nest at the base centre
Site: the central nest, 4 spawners at (351,-47) biter, (349,-41) spitter, (358,-39) biter, (349,-33) biter. Three small worms
(353,-39), (353,-37), (356,-34), 28 small biters, nothing stronger within 45 tiles. Peaceful mode applies.
Roboport (360,-24) is 15 to 23 tiles away (inside its 25 logistic range); substations at (362,-40), (344,-40), (360,-56), (344,-24) power
inserters (supply radius 9).
Pick **(358,-39)** (east-most, the substation (362,-40) stands about 2 tiles clear of its footprint). The tiles at the south side
(358.5,-36.5) and (358.5,-35.5) are the intended inserter and chest; confirm with `can_place_entity` first (small worm at 356,-34 is 2 tiles away; remove it with `clear` only if it blocks).

Order of work (everything before the shot, because the health clock starts at capture: it starts "just run out of food" with ~350 s to revert):
1. Move about 200 bioflux from Gleba (production 139/h, belts at y 10, about 29 on belts now) into the Nauvis network with
   `network.remove_item` on Gleba and `network.insert` on Nauvis (the precedent in SKILL.md; it is factory-made). **Needs the Captain's yes.**
2. Place beside the target: a requester chest for bioflux (request 10, barred), an inserter into the spawner's fuel slot (the spawner takes
   fuel by inserter), an output inserter plus a red chest barred to 1 slot (max 100 eggs, so a stall can spoil at most 100 eggs).
   Place them on a free side, powered by the substation. (Placed entities are free.)
3. Fire one rare rocket with the scripted capture (`capture_spawner.py capture --apply` after changing TARGET to the new coordinates;
   the script moves one rocket and fires the game's own projectile). Check `status`: entity `captive-biter-spawner`, health rising.
4. Robots deliver bioflux; the inserter feeds; the spawner heals 1 hp/s while burning. Eggs appear in the chest at 0.5/s.
5. Egg users: robot-fed "p3 units" in the module mall (module_mall.py layout: assembling-machine-3, requester chests for adv, PU, p2, eggs; red
   chest out). Request only 10 eggs per unit so eggs never rest. The recipe is 60 s, so one asm-3 (speed 1.25) makes 1.25/min; 12 units
   with speed modules about 15/min; S1's 500 modules take about 35 min, S2 about 2 h. Eggs are in the network for at most a few minutes.
   Eggs are carried by robots from (358,-39) to the mall (-121,-466) which is about 600 tiles: fine for robots, but ask whether to build
   the p3 units near the nest instead (shorter, same free cost).
6. Modules install with the existing `module_mall.py install` path (replace p2; the freed p2 go back to the network).

Numbers: 1 spawner, bioflux 60/h, a 2.5 h run for 4,584 eggs needs about 150 bioflux; S1 needs about 20. Bioflux budget = 15% of Gleba's
current 139/h. The captured spawner needs nothing else; no power. Time to build: under an hour of game work for steps 1 to 4 (about 6
entities); p3 unit block similar to the existing mall build.

## 5. Risks and unknowns
- If bioflux stops for 350 s the spawner reverts (the wild one is back at full hp). Run it only while someone watches the stock, or stop it on purpose
  when the harvest is done; losing it costs one rocket (9 left) plus 20 bioflux of parts. There is no way to keep a "buffer of hours": the
  fuel slot holds 1 and bioflux spoils in 2 h.
- Unknown: whether a full output slot still burns bioflux (assumed yes, 100 kW regardless). The egg chest is barred to 1 slot to cap it.
- Unknown: how nearby wild units react once a structure is "captive" (the wiki is silent). Peaceful mode should keep them passive; the
  other three nests stay wild around the new one.
- Eggs spoiling into big biters if nothing consumes them (30 min). Mitigation: barred chest and short requests.
- The quality of eggs is that of the nest; the p3 recipe does not care.
- Productivity limit: p2 and circuit stock set the real pace (section 2), not eggs.
- The tech `captive-biter-spawner` (not researched) would allow crafting spawners with 10 eggs, 15 U-235, a rocket and 100 cold fluoroketone, useful
  only if a second source is wanted; not needed.

## 6. Why not A (remote outpost)
2,300 tiles: rails about 1,150 pieces plus signals, locomotive on nuclear fuel (965 in stock), wagons; or 128 substations / 72 big poles; or 48
roboports chained with solar kits; plus defence in 24 nests of wild spawners with worms. The captured spawner has already reverted, so the
whole thing would also need a new capture. Cliffs not counted: not worth it when a nest stands 15 tiles from a roboport.

## 7. Go / no-go list for the Captain
1. Approve moving about 200 bioflux from Gleba to Nauvis network (consumes about 1.4 hours of Gleba bioflux output).
2. Approve capturing (358,-39) in the base centre with one rare rocket (alternatives: (349,-41), (351,-47), (349,-33), or (77,403) in the south).
3. Approve placing the six small entities (fuel inserter, bioflux requester, output inserter, 1-slot red chest, plus power if short).
4. S1 target of 500 p3 and the order of slots (or tell me the products you value most).
5. Egg users near the nest (new p3 unit block beside it) or at the existing mall (600 tiles away).
6. Whether to also research `captive-biter-spawner` later (no cost to ask; it is not on the path to S1).
