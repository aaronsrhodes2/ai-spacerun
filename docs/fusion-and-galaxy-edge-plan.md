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

## Quantum processor line on Aquilo, survey (2026-11-15, scripts/aquilo_fluid_map.py)
- Recipe: 1 processing unit, 1 tungsten carbide, 1 superconductor, 1 carbon fiber, 2 lithium plate, 10 **cold** fluoroketone -> 1 quantum processor + 5 **hot** fluoroketone, 30 s, category electromagnetics: the **electromagnetic plant** (4x4, speed 2, 5 module slots), not a cryogenic plant. One plant = 4 per minute; 350 processors = 88 plant-minutes. Net fluoroketone loss 5 per processor (1,750 for the first plant), made up by the fluoroketone plant (1 lithium + 1 solid fuel per 50).
- How the fluoroketone loop is built (traced from geometry, Lua cannot read fluidboxes in 2.1): one shared **hot** network (63 pipes: trunk x=-28 from y=-31 to -42, then along y=-48 east to x=-8, columns x=-11 and x=-9). Cold never travels by pipe: each cooling plant's cold output touches its science plant's input directly (plant-to-plant). So a new consumer needs its **own cooling plant** touching it (or a short cold pipe), plus a hot connection to the trunk.
- Unit geometry worked out (cooling plant K, electromagnetic plant E): K dir 8 puts hot inputs on the north edge and the cold output at its south-east corner; E dir 4 takes cold on its top edge at x offset -0.5 and gives hot on its west edge. Unused fluidbox ports do not connect.
- **Why nothing is placed yet:** the hot trunk is boxed in by heat pipes and chests. The only free ground touching it is the pocket x -26..-17, y -47..-43 (south of the y=-48 line), too tight for E+K without underground tricks that risk a cold/hot merge; the roomy foundation to the south-west (x -38..-27, y -23..-14, substation at -27,-19) has no clear pipe path to the trunk.
- **Real blocker on the supply side:** Aquilo has no holmium (lithium needs 1 holmium per 5), so the fluoroketone plant is stalled for lithium; network lithium 0, lithium plate 523, solid fuel 5,984. Tungsten carbide, carbon fiber, tungsten plate and holmium on the Aquilo pad: all 0 (first deliveries not seen). Quantum processors cannot start until those arrive anyway.

## Quantum processor unit 1, built (2026-11-15, scripts/aquilo_qp.py build)
Aquilo only (the Captain: fusion elsewhere makes no sense: fluoroketone, ammonia, lithium are Aquilo products).
- Unit = cooling plant K at (-39.5,-21.5) dir south + electromagnetic plant E at (-37,-17) dir east (quantum-processor). K's cold output touches E's input directly; a pipe loop joins E's hot output to K's hot input; a routed link (3 tunnels) joins that loop to the shared hot trunk through the free pocket at y=-44.5. Traced: hot network now 98 pipes with both ports on it; ammonia, fluorine, brine, solution networks unchanged. Both plants powered and heated (8 heat pipes).
- E is fed from a requester chest (-33.5,-15.5): 20 processing unit, 20 tungsten carbide, 20 superconductor, 20 carbon fiber, 40 lithium plate; output goes to a provider chest (-33.5,-18.5). Entities and plan saved in snapshots/aquilo_qp_unit.json.
- Status now: E "item ingredient shortage" (tungsten carbide and carbon fiber not on Aquilo yet), K waits for hot fluoroketone (fluoroketone plant is stalled for lithium, which needs holmium). Nothing produced yet.
- Lessons: place_entities ignores plant facing (rotate afterwards with e.direction); can_place_entity on a bare pipe finds tiles the tile map calls free (the aquilo_qp grid asks the game); a pipe-to-ground exit only connects straight ahead; no U-turns in the router.
- Scale: one unit = 4 per minute (350 in ~88 minutes). More units: rerun aquilo_qp.py after clearing the site list in choose() (it finds the next free site).

## Railguns: a requirement for the edge ship (2026-11-16, the Captain)
- Researched; none built. Huge asteroids (Aquilo to the edge) resist explosions 99% and have 3,000 flat physical resistance, so rockets and uranium rounds cannot kill them: the edge ship cannot run without railguns. Lower-tier ships do not need them.
- Railgun turret (read live): 30 tungsten plate, 50 superconductor, 20 carbon fiber, 100 quantum processor, 100 cold fluoroketone. Railgun ammo: 5 steel plate, 2 explosives, 10 copper cable (no processors; makes on any planet).
- Budget: fusion 350 processors + 2 railgun turrets 200 = 550, about 138 minutes of one unit. Plan a second processor unit (`aquilo_qp.py`) before the edge ship; tungsten and fiber to Aquilo gate everything.
- Order: tungsten/fiber arrive -> fusion plant -> second processor unit -> railgun turrets (2 to start) and ammo stocked ahead -> edge ship.

## Fusion plant 1 built; what gates it now (2026-11-16)
- Built with `scripts/fusion_plant.py` on the west end of the south area (reactor (-27,49), generators (-29.5,43.5) and (-24.5,43.5), cooling plant (-34.5,43.5), closed loop of 14 pipes, heat rows off the hot column x = -38, substation (-21,47), fuel chest (-23,50) asking for 50 cells). Placed entities are free once researched: no quantum processors were needed for the reactor or generators. Heated, powered, nothing frozen; NOT running (loop empty, no cells).
- The spaceport took the east end of the same area (`spaceport.py --variant aquilo`, top-left (-18,22)); carbon fiber has landed (381).
- Why the loop cannot be charged yet:
  1. The base's hot fluoroketone pipes are dry: the fluoroketone plant (-32.5,-39.5) was gated by its feed inserter on "fluoroketone-hot < 60", read from the science cooling plants, which are full. Gate raised to < 100000 on 2026-11-16: the plant ran 4 crafts at once and now self-limits on its inputs or a full output. This also feeds the quantum processor unit, which hangs on that trunk.
  2. AMMONIA is the real bottleneck: made 32,400 a minute, used 34,000. Six ice-platform machines beside the three separation plants (y -27.5) turn the separation plants' ice into ice platforms: 50 ice + 400 ammonia each, 36 a minute = about 14,400 ammonia a minute, with 15,800 platforms in stock. They are also the only ICE SINK there: stop them without another outlet and the separation plants fill with ice and ammonia stops altogether. Fix proposed, not done: an ice outlet that costs no ammonia (recyclers, or chests into the robot network plus a recycler void) and a stock cap on the platform makers.
  3. Holmium: 0 on Aquilo, eaten by lithium as it lands. Ship 5 now asks for 500 a trip (was 60). Cells need 1 holmium + 5 lithium plate + 100 ammonia each, made in a cryogenic plant on the ammonia network (not built).
  4. No barrels on Aquilo (the loop is 70 tiles from the trunk, so the charge goes by barrel: filler at the quantum processor loop near (-42,-16), emptier at the plant). 200 barrels ordered Nauvis -> Fulgora -> Aquilo.
  5. Processing units on Aquilo: 0 (the quantum processor plant needs them).

## Ammonia fixed (2026-11-16, the Captain: "fix the ammonia")
- The three west-side ice-platform machines beside the separation plants (y -27.5) are gone; a legendary passive provider chest stands at each inserter's drop tile ((-12.5,-27.5), (-0.5,-27.5), (11.5,-27.5)), so separation ice goes into the robot network. The three east-side machines stay, their feed inserters gated on "ice-platform < 2000" (logistic condition).
- Ice void (safety valve, costs no ammonia): two legendary recyclers facing each other at (17,-23) and (21,-23), fed by a bulk inserter (15.5,-21.5) from a requester chest (15.5,-20.5, asks 1,000 ice); the inserter runs only while the network holds more than 8,000 spare ice. It has not had to run yet.
- Measured after: ammonia went from 32,400 made / 34,000 used a minute to a full network (10,400 in the pipes) with production following demand (about 24,700 both ways); the separation plants now sit on full output between bursts. Every ammonia user works. The fluoroketone plant runs, the quantum processor unit's link thawed (two heat pipes at (-33,-44), (-32,-44)) and the unit made its first 22 quantum processors.
- Still open: the fusion loop's charge needs a barrel filler on the hot network and no free spot touches a hot pipe (the pocket at x -32..-29, y -48..-44 could take one if the quantum processor link is re-laid); the cell maker is not built; processing units on Aquilo are at 0.
- Save before the change: `pre-ammonia-fix`.

## Fusion plant 1 is running (2026-11-16, late)
- Charge by barrel: filler (assembling machine 3, fluoroketone-hot-barrel) at (-29.5,-46.5) in the pocket beside the quantum processor link, which was re-laid with a tap: pipes (-32,-45), (-31,-45), (-30,-45), underground entry moved to (-29,-45). Its feed inserter (-30,-49) is gated on "fluoroketone-hot-barrel < 100". Emptier (empty-fluoroketone-hot-barrel) at (-20.5,40.5) on the east end of the plant's hot row (pipe (-23,40)), chest (-22,37) asks for 40 full barrels; the wall piece at (-19,38) is now a heat pipe.
- 72 barrels (3,600 fluoroketone) filled the loop: hot row 1,100, cold link 400, reactor 1,000 cold. The plumbing is proven: hot row -> cooling plant -> cold -> reactor -> plasma -> both generators -> hot row.
- Cell maker: cryogenic plant (fusion-power-cell) at (8.5,-19.5), the one spot where a plant's fluid port meets an ammonia pipe ((5,-22)); chest (12,-21) asks 50 holmium plate and 250 lithium plate, feed inserter gated on "fusion-power-cell < 200".
- Running: reactor working with cells aboard, both generators working, about 10 fluoroketone a second round the loop, fuel burn about 36 MW (measured from the reactor's burning-fuel counter over 10 s). The electric statistics API returned frozen counters, so the electrical output is not measured; the nine steam turbines were still working.
- Saves: `pre-fk-filler`. Not yet done: a long-run check, more generators (the reactor has two free plasma outputs on its south face), and taking load off the nuclear plant.

## Loop overfilled, corrected (2026-11-16, late)
- Mistake: the barrel emptier kept topping the closed loop up until nothing had slack (hot row 1,100 of 1,100, cold link, reactor and cooling plant output all full, plus 650 waiting in the emptier's own buffer). The generators' hot buffers then started to climb (0 -> 46): with no room on the hot side they would have stopped, the reactor after them, and a full ring cannot restart itself.
- Fix: emptier switched off (`disabled_by_script`, request cleared, its buffer cleared: 630 lost), about 1,000 hot fluoroketone let out of the row with `pipe.remove_fluid(1, amount)`. The loop now holds 2,426 (hot row about 690 of 1,100), the total stays constant (the loop is lossless), generator hot buffers are back at 0.
- Rule for this plant: charge to about 2,400, never to full. To top up, re-enable the emptier by hand for a moment and watch the hot row; do not leave it enabled.
- Load: with the steam turbines still running, the plant idles: about 1 fluoroketone a second round the loop and the reactor flips between working and full output. It follows demand; it is not yet carrying the base.

## Load shifted to fusion (2026-11-16, the Captain: "shift the load")
- Fusion generators and steam turbines are both `secondary-output`, so they share load by capacity; the nine turbines were giving 12.6 MW (1.4 each of 14.55).
- Valve, no rebuild: the four ice melters that give the heat exchangers their water ((-10.5,-20.5), (29.5,-11.5), (33.5,-22.5), (35.5,-15.5)) have their feed inserters wired (script wire, red) to the accumulator at (-38,-46), which outputs its charge as signal A; the inserters run only while A < 80. No water, no steam: the turbines idle and come back by themselves if the accumulators fall under 80%.
- Measured over about 5 minutes: exchanger water 800 -> 0, turbines 12.6 -> about 1.6 MW (the last steam), accumulators 100% throughout, nothing unpowered or frozen. Reactor fuel burn about 30 MW (burning-fuel counter), which includes its own 10 MW input. Nuclear reactors and heating towers still heat the base; only the steam side is throttled.
- Not tested: the automatic fallback (nobody stopped the fusion plant on purpose). A fusion cell lasts roughly 20 minutes at this load; 5 were in the reactor and 17 in its chest; the cell maker needs holmium to keep up.
- Save before: `pre-load-shift`.

## Backup test and cold-start answer (2026-11-16)
- Backup test: both fusion generators paused (`disabled_by_script`) for 150 s. The accumulators fell to 80%, the melters got ice, the turbines came on within about 10 s and pulsed between 0 and about 89 MW; accumulator charge stayed between 75% and 98%. Fusion restored afterwards, turbines back to 0. Flaw seen: twice about 22 entities showed low power for a moment between steam pulses (the 48 accumulators cannot discharge fast enough to carry the base alone while the steam is off). Needs more accumulators and a latch (on below 80%, off above 95%) so the steam does not chop.
- Cold start (the Captain: "could this base spin up in a cold start?"): NO, not from a full freeze. Heat comes from 12 heating towers (4 burning; 32 solid fuel and 50 carbon inside all of them together) and 2 nuclear reactors, every one fed by an inserter from a requester chest. Inserters, roboports, pipes and plants need heat to work, so once the heat is gone nothing can refuel the heat. Solar is 1% here (26 panels: nothing). The fusion plant makes electricity, not heat, and its cooling plant and pipes freeze too; the reactor also needs 10 MW to start. From a power cut with the heat still on, yes: the turbine backup above.
- What a cold-start kit would need: a starter heat source that keeps its own fuel reserve and whose feed stays warm from the tower itself, a much larger accumulator bank, and the fusion loop on that starter heat line.

## The edge ship = Nauvis Triangle 1 (design, 2026-11-16; the Captain: "arm the whole triangle", ammunition "made on board from asteroids")
What stands (read live, platform-14, paused at Nauvis): the strip miner of `scripts/triangle_miner.py` / `triangle_plates.py`. A frame 4 tiles wide, apex (0,-577) north, base y = 289 from x -497 to 497, hub at (0,0), spokes; 98 collectors (outside the three sides), about 4,200 express belts (one chunk belt down each slanted side into the base belt, up the south spoke to the hub ring), 8 crushers, 28 furnaces, 144 solar panels; hub 59 slots. Weight 3,812 t. No thrusters, no turrets, no tanks. It flies apex first (north), so the two slanted sides (about 1,050 tiles each) are the leading edges and the base is the stern.

Numbers from the game
- Turrets: gun 2x2 range 18; rocket 3x3 range 36 (min 15); railgun 3x4 range 40, turns only 0.2 of a circle (it must face north); laser 2x2 range 24. Thruster 4x5.
- Solar in orbit: Nauvis 300%, Aquilo 60%, solar system edge 1%. So solar carries the ship to Aquilo; past Aquilo it needs fusion.
- Asteroids: to Aquilo medium and big; Aquilo to the edge (100,000 km) big and HUGE; edge to the shattered planet huge and promethium. Huge ones need railguns.
- Ammunition recipes: railgun ammo = 5 steel + 2 explosives + 10 copper cable; rocket = 2 iron plate + 1 explosives; explosive rocket = rocket + 2 explosives; explosives (2) = coal + sulfur + 10 water; coal = 5 carbon + sulfur + 10 water; piercing magazines (2) = 2 copper + steel + 2 firearm magazines. All from chunks: metallic (advanced: 10 iron ore + 4 copper ore), carbonic (advanced: 5 carbon + 2 sulfur), oxide (5 ice). Thruster fuel 75 = 2 carbon + 10 water; oxidizer 75 = 2 iron ore + 10 water (advanced recipes with calcite give 1,500).
- Scale warning: a 50-wide shuttle burns about 1,800 explosive rockets on a Gleba-Aquilo round trip. This hull is 1,000 wide. Ammunition and fuel demand will be of another order; it has to be MEASURED on a short hop before any long flight.

Stages (each one built, then proven, before the next)
1. Edge pad + ammunition belt prototype: on the first 100 rows below the apex of both sides, widen the strip for turret pads (tile ghosts; the hub pulls foundations as it did for the frame), place gun, rocket and railgun turrets on the pattern, run a second belt (ammunition, outward) beside the chunk belt, inserters with stock limits. Prove: every turret reachable, belt lanes do not jam.
2. Ammunition works at the hub: advanced crushing for copper and sulfur, steel furnaces, ice melting, coal, explosives, then railgun ammo, rockets, explosive rockets, piercing magazines, each capped on hub stock. Prove: each product made from chunks alone, measured per minute.
3. Roll the pads and the ammunition belt out along both sides and the apex; cargo bays on the hub.
4. Stern: move the base collectors, thruster bank along the base with fuel and oxidizer plants and tanks (wire both tanks: see the oxidizer-wire lesson). Prove at Nauvis: thrust, speed against width.
5. Short hop Nauvis -> Fulgora and back, parked defended at each end: measure ammunition and fuel per km; fix what the numbers say.
6. Aquilo: railguns live over Aquilo (goal 3's milestone). Then fusion aboard for the run past Aquilo, then promethium.
Not decided: how many turrets a 100-row stretch needs (start from range: rocket and railgun every 30 rows, guns every 15, then measure), thruster count, whether the plate works keep running while it is rebuilt.

## Edge ship stage 1 done: pads and ammunition belt on the apex stretch (2026-11-16, `scripts/edge_ship.py`)
- The ship is now called **Edgerunner** (the Captain renamed Nauvis Triangle 1; platform-14). `triangle.py`, `triangle_miner.py`, `wheel_foundation.py`, `_wf_rate.py`, `_wf_watch.py` find it by the new name.
- Built on rows -555..-456 of BOTH slanted sides: an ammunition belt (157 tiles a side) on the strip's third column, flowing up to a dead end at the apex; 7 gun turrets, 3 rocket turrets and 3 railguns (facing north) a side, each fed by one bulk inserter from that belt. 198 foundation tiles were laid as tile ghosts and built by the hub from its stock.
- Proven with a test load of real ammunition from Nauvis (140 firearm magazines and 40 explosive rockets a side, moved by Lua): all 14 gun turrets and all 6 rocket turrets armed, the leftovers back up on the belt in order, nothing in the stretch without power (no substations were in the way; foundation carries the power).
- Seen: turrets nearest the feed fill first (a gun took about 10 magazines before the next one got any), so the feed must outrun the first turrets' appetite. A railgun turret's collision box runs 0.1 past its fourth row: it needs deck under a fifth row.
- NOT proven: the railguns. No railgun ammo exists anywhere yet; they stand empty. The belt is fed from nothing so far: stage 2 (ammunition works at the hub) and the feed line from the hub to the sides come next.
