# Fusion power and the galaxy-edge ship (plan, 2026-11-15)

Captain's choices: first fusion plant on **Aquilo**; the ship is **planned first, built after approval**.

## What the game says (read live)
- Researched: `fusion-reactor`, `fusion-reactor-equipment`, `stellar-discovery-solar-system-edge`, `space-platform-thruster`, `railgun`, `quantum-processor`, `biter-egg-handling`.
- Not researched: `promethium-science-pack` (1,000 units, 10 pack types incl. cryogenic and utility; prerequisites already done) and `captive-biter-spawner` (3,000 units, all 11 packs). The shattered planet (galaxy edge) stays locked until promethium research.
- Both are now first in the research queue.

## Recipes (prototypes)
| Item | Recipe |
|---|---|
| fusion reactor (6x6) | 200 tungsten plate, 200 superconductor, 250 quantum processor |
| fusion generator (3x5) | 100 tungsten plate, 100 superconductor, 50 quantum processor |
| fusion power cell | 1 holmium plate, 5 lithium plate, 100 ammonia (10 s) |
| fluoroketone cooling | 10 hot -> 10 cold (5 s) |
| promethium science pack | 10 biter egg, 1 quantum processor, 25 promethium asteroid chunk -> 10 packs (5 s) |

Fusion cells are not uranium cells: they need Fulgora holmium, Aquilo lithium and ammonia.

## Fusion plant on Aquilo, steps
1. Stock check (pad and chests): tungsten, superconductor (Aquilo pad has 500), quantum processors, holmium, lithium. Order the shortfall through pad requests.
2. Build a cell line first (holmium + lithium + ammonia), since reactors burn cells.
3. Build one reactor + generators + fluoroketone loop, prove it on its own pole group, then scale; keep the existing nuclear reactor as backup.
4. Respect the reactor lesson: feed cells only when the plant needs them.

## Galaxy-edge ship, design questions to settle before placing anything
- Promethium chunks come from asteroids at the Solar System Edge: the ship needs collectors and crushers/processing for that chunk type.
- Biter eggs need captive biter spawners (research above), or a supply route.
- Defence: railguns and rockets (ammunition doctrine), plus repair packs; the shattered planet route has the heaviest asteroids.
- Thrusters, fuel and oxidizer tanks with the oxidizer wire intact (autopilot guard added 2026-11-15).
- Fusion reactors on the ship are an option for later; first ship runs on solar/batteries like the others.

## Open
- Pack stocks per planet not yet surveyed.
- Ship size: Captain asked to plan first.

## Survey result (2026-11-15, scripts/fusion_aquilo.py bom)
First plant = 1 reactor + 2 generators + 20 start cells = 350 quantum processors.
- On Aquilo already: superconductor 5,464, processing units 1,132, lithium plate 1,342 (need 800).
- Far but exists: tungsten plate (Vulcanus 37.9k), tungsten carbide (Vulcanus 48k), holmium plate (Fulgora 8k).
- SHORT, no producer anywhere: quantum processor (built in a cryogenic-plant-class assembler on Aquilo: 1 processing unit, 1 tungsten carbide, 1 superconductor, 1 carbon fiber, 2 lithium plate, 10 cold fluoroketone) and carbon fiber (10 yumako mash + 1 carbon, Gleba; 3,500 mash for 350).
- Site: the empty prepared ice-platform area south of the Aquilo base (about x -50..30, y 28..50).
- Route for far items: Vulcanus -> Nauvis -> Fulgora -> Aquilo kit ship (aq-ghost section); carbon fiber: Gleba-Aquilo shuttle.

## Shipping routes (2026-11-15, scripts/fusion_routes.py apply)
Each hop = ship hub request at the origin (import_from origin) + destination pad request. Sections are `fusion-<kind>-<place>` (group names are global: one shared name made every section carry the last one's items, found on the first apply).
- Tungsten plate 600: Vulcanus -> Nauvis (Nauvis-Vulcanus 1-3) -> Fulgora (Nauvis-Fulgora 1-3) -> Aquilo (Fulgora-Aquilo 5).
- Tungsten carbide 500: Nauvis -> Fulgora -> Aquilo. Holmium plate 60: Fulgora -> Aquilo (the Aquilo pad already asked for 400).
- Carbon fiber 500: Gleba -> Aquilo (Gleba-Aquilo 1; leave rule unchanged).
First deliveries not yet seen; check with `fusion_routes.py show` and `fusion_aquilo.py bom`.
