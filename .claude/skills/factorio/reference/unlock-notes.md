# Unlock notes: what each research lets us improve

The Captain's idea (2026-11-13): when a technology or a new level completes, the model should say "you just unlocked this, we could
improve that" instead of inventing the next problem. This file is the list it reads.

**How to use it**
- When a research completes (`scripts/watch_research.py`, the autopilot log, or `research_status`), find it here and suggest the
  improvement to the Captain in one or two lines. They say yes or no; a yes is an order.
- When the improvement is built, move the line to "applied" with the date and the script.
- A technology with no entry: read what it unlocks from the game (`technology.prototype.effects`), think about which machines or
  ships it touches, and add an entry before moving on.
- Keep an entry short: what it unlocks, what we can change, what that lets us remove.

Status words: **open** (unlocked, not applied), **applied**, **waiting** (not researched yet).

## Unlocked, with something still open

| Research | What it allows | The cleanup or gain | Status |
|---|---|---|---|
| asteroid-reprocessing | a crusher turns one chunk kind into the others | wheels: stop crushing a surplus kind and reshuffle it (`wheel_reprocess.py balance`); Aquilo shuttle: one crusher, recipe by circuit | applied 2026-11-13. **Open:** the eight old inner shuttles get it with the new hull (`inner_shuttle.py`) |
| advanced-asteroid-processing | advanced crushing gives a second product (copper, sulfur, calcite) | wheels make blue science from sulfur and carbon. Inner shuttles use basic carbonic crushing: they have no use for sulfur | applied |
| foundry (works in space, ore melting too) | 50 ore + 1 calcite gives 500 molten metal | **open:** foundries on the wheels instead of furnaces for the plate-bound pack lines; calcite sits at its cap there | open |
| coal-liquefaction | oil products from coal, coal from carbon and sulfur | blue science on the wheels with no oil import (`wheel_blue.py`) | applied |
| heating-tower | burns anything, 250% heat | Gleba: all seven spoilage burners feed exchangers and turbines (`gleba_heat.py`). Aquilo: heats the base | applied on Gleba, waiting on Aquilo |
| epic-quality | epic machines, bays, tanks | `upgrade_quality.py --items --apply`, then rerun every `config` (the upgrade drops over-reach wires and belt readers) | applied. **Open:** robots that were in the air at the time |
| tesla-weapons | tesla turrets | Gleba egg row: eight turrets | applied |
| rocket-turret | rockets against big asteroids | Aquilo shuttle only, limited to big and huge asteroids | applied |
| recycling | recyclers | void surplus as the last step (stop making it, then useful goods, then void) | applied where needed |
| logistic-system + rocket silos | requests across planets | building kit on every landing pad (`kit_shipping.py`), fed by `nauvis_mall.py` | applied 2026-11-13 |
| stack-inserter, turbo-transport-belt | higher belt throughput | **open:** the wheels' hub edges are the narrow point (one bulk inserter a tile); stack inserters there would lift every pack line. The mall and the kit still ship express belts | open |
| captivity | captive spawners, biter eggs | **open:** productivity module 3 and overgrowth soil need eggs; no line uses them yet | open |
| elevated-rail, rail-support-foundations | rails over water and other rails | **open:** only if a Nauvis train route needs a crossing; nothing waits on it | open |

## Infinite levels in the queue now

| Research | Each level gives | What to do on each level |
|---|---|---|
| asteroid-productivity | more product per crushed chunk | the wheels reach their caps sooner: check `wheel_reprocess.py status`; fewer chunks needed for the same packs, so more go to the short kind |
| rocket-fuel-productivity | more rocket fuel per craft | rocket launches cost less; the Aquilo base imports less fuel |
| plastic-bar-productivity, processing-unit-productivity, steel-plate-productivity, low-density-structure-productivity | more of that item per craft | look for the pack line where that item was the short one and see whether a machine can go |
| refined-flammables, stronger-explosives, physical damage | weapon damage | shuttles: fewer magazines or rockets per leg, so lower departure stocks in the schedules |
| research-productivity (not researched) | more research per pack | every pack target drops by the same share |

## Waiting: the road to the solve

| Research | Earned by | What it allows | The cleanup or gain when it lands |
|---|---|---|---|
| lithium-processing | mining a lithium iceberg on Aquilo | lithium from brine | start the lithium line; needs holmium plate from the supply relay |
| cryogenic-plant | crafting one lithium plate | the cryogenic plant: chemistry and more, with eight module slots | replace chemical plants on the busiest chemistry lines; fewer machines for the same output |
| cryogenic-science-pack | crafting one cryogenic plant on Aquilo | the last planet pack | build its relay Aquilo -> Fulgora -> Nauvis -> Gleba labs; queue the four techs below |
| railgun | 2,000 units | railgun turrets kill huge asteroids | the edge ship; the Aquilo shuttle can drop its rocket line (coal plant, explosives plant, rocket assembler) |
| fusion-reactor | 2,000 units | power without sun or fuel | Aquilo shuttle and edge ship lose their solar wings; the Aquilo base stops burning fuel for power |
| foundation | units | build on lava, oil ocean and Aquilo's sea | bases stop being shaped by the coastline; pipe and belt detours round water go |
| quantum-processor | 500 units | the top-tier component | needed by fusion and the edge ship; note what else asks for it when it lands |
| legendary-quality | units | legendary machines | the standing order: upgrade everything at once, then rerun every `config` |
