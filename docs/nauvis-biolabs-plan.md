# Biolabs on Nauvis (plan, 2026-11-16)

The Captain asked for biolabs in place of Gleba's labs. Nothing is built; this is the plan.

## What the game says (read live)
- Biolab: researched. Placeable only at pressure 1000, which is Nauvis (Gleba is 2000). So the labs have to move planets, not upgrade in place.
- Biolab vs lab: research speed 2 vs 1, science pack drain 50% vs 100%, 4 module slots vs 2, 5x5 vs 3x3, 300 kW vs 60 kW.
- Today: 10 legendary labs on Gleba (x 124.5, y 24.5 and down), 2 legendary speed module 3 each. Nauvis has 0 labs and 0 biolabs.
- Agricultural science packs spoil in 216,000 ticks (60 minutes). A Nauvis-Gleba leg measured about 40 seconds, so spoilage in transit is small; stock sitting in a hub or a chest is the risk.
- Lab research speed bonus 2.5, productivity bonus 0. Current research: promethium science pack.
- Placed entities are free once researched, so the biolabs themselves need no biter eggs. Only the science packs have to arrive.

## Why it is worth it
Half the pack drain means every pack does twice the research. With double speed and 4 module slots, 10 biolabs outrun the 10 labs several times over. It helps most on promethium science (10 pack types) and everything after it.

## What has to change
1. **Site on Nauvis:** 10 biolabs (5x5) in a row or 2x5 block beside the landing pad / Replicator area, inside the robot network, fed by requester chests and inserters like the Gleba labs. Check power headroom (10 x 300 kW before modules and beacons).
2. **Pack routes reverse.** Today every Wheel ships its packs to Gleba. After the move:
   - Nauvis packs (automation, logistic, military, chemical, production, utility, space) stay home: no shipping at all.
   - Vulcanus (metallurgic), Fulgora (electromagnetic): the Nauvis shuttles already carry these; they unload on Nauvis instead of carrying them on to Gleba.
   - Gleba (agricultural): Nauvis-Gleba shuttles carry packs Gleba -> Nauvis. Keep the request small and frequent so packs do not age in a hub.
   - Aquilo (cryogenic): today the Gleba-Aquilo shuttle takes 1,000 a trip to Gleba. It needs a hop on to Nauvis (Gleba pad -> Nauvis-Gleba shuttle), or a new Aquilo -> Nauvis leg.
3. **Switch-over without a research gap:** build and feed the biolabs first, move one pack type at a time, and only then empty the Gleba labs. Keep the Gleba labs standing until the biolabs have run a full research.
4. **Modules:** move the 20 legendary speed modules from the Gleba labs; biolabs take 40. The rest come from the Nauvis stock (2,500 normal speed modules) and upgrade_quality.py.

## Order
1. Dry-run the biolab block on Nauvis (place_entities dry_run), then build it.
2. Point the Nauvis-made packs at it and confirm research runs on those alone where a tech allows.
3. Re-route metallurgic and electromagnetic, then agricultural, then cryogenic.
4. Empty and remove the Gleba labs; update the wheel-roles note ("all labs on Gleba" becomes "all labs on Nauvis").

## Open
- Research is paused whenever a pack type is missing; the cryogenic hop is the longest and should be proven before the Gleba labs are removed.
- Lab status on Gleba read as code 35 on all four sampled labs; not decoded here.
- This reverses the wheel-roles decision (all labs on Gleba). The Captain decides.
