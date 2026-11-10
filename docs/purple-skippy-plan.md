# Plan: scripts and skills so a local agent (purple Skippy) can solve Nauvis and white science

Asked 2026-11-09 by the Captain. Framework only, nothing executed: see `skippy-pack/` (manifest.json, milestones.json, nauvis.py, skills/).

## Scope note (the Captain, 2026-11-09)
This only solves friendly build mode (free placement once researched, direct enemy removal, no building costs, no hand crafting). A normal Space Age win is a different and harder problem: paid-for building, real defence and evolution, pollution, a mall for every part,
and hostile planets. The pack should never be described as solving that. If you later want a normal-mode track, it needs its own scripts: a mall and bot build queue instead of `place_entities`, turret and wall generators, and a threat model.

## Is it possible?
Yes for most of it, with one design rule: the model never writes geometry. It picks a step from a runbook, a patch from a registry, runs a script as a dry run, reads a small JSON verdict, applies, verifies, and records. Every script already saves the game and defaults to a dry run.
That is what makes it feasible for a local model: prompts are "which script next and with what arguments", not "design a smelter". Where a script is missing the runbook says `gap` and the agent stops and asks.

## Your ten steps against what exists
| # | step | scriptable now? | what exists | what is missing |
|---|---|---|---|---|
| 1 | audit bottlenecks, equal science rates | audit yes; equalising partly | `fx.py bottlenecks`, autopilot SNAP line (made/s per pack) | `fx.py science-rates` (per pack made, used, target) and a rule that picks the slowest |
| 2 | find patches, clear vegetation, rocks, fauna; leave the crash site; clear a path to the next patch | mostly | scan recipe (docs/new-patches.md), `fx.py clear`, enemies removed directly | one-call `discover`; **crash-site exclusion** (crash site at about (-5,-6), 5 entities) added to `clear`; corridor clear |
| 3 | floor the cleared areas, connect with tracks | yes | `pave.py --box`, `rail_plan.py`, `build_yard.py` | signals and junctions (one train per track today), registry of tracks |
| 4 | dense mining, several outputs on a side | yes | `fx.py mine` (7-tile period, belts both sides), `build_train_outpost.py` | multiple output belts per side for patches wider than one express belt: today one belt (45/s) caps an outpost, so large patches need a second collector |
| 5 | iron and copper: smelter block in a new clearing next to the patch | yes | `build_train_outpost.py` (72 furnaces per output belt) | second smelter line on the same patch, a smelter block placed in a separate cleared box |
| 6 | oil to the main holding tanks by train | yes | `build_oil_train.py` plus the inline unload yard (built tonight) | unload yard script, refinery lane from the tanks |
| 7 | stone ignored until short | yes | raw-ore mode (`--furnaces 0`), Stone A built | a shortage trigger in the autopilot |
| 8 | uranium to the uranium centre; expand the centre on demand | no | existing centre built by hand | acid supply (fluid train or local), uranium outpost, centre expander |
| 9 | production bottlenecks, science and rocket parts first | yes | `build_cells.py`, `build_pu_block.py`, `build_silos.py`, `fx.py logistics`, `fx.py upgrade` | automatic sizing from the audit |
| 10 | maximise science from the revealed map plus orbital platforms | partly | space factory plan, platform-1 | the platform builder and its measurement step |

## Other steps I suggest (your item 11)
- **Defence and clearing policy.** I destroyed nests directly (god mode). Nests regrow near polluting outposts; decide between periodic clearing, turret strips, or land mines (your word) and put it in the runbook.
- **Signals and traffic.** Today every outpost has its own track and one train. More trains per line needs signals, chain signals at the yard, and a train limit per stop.
- **Fuel for trains.** The new stops use 150 coal per locomotive; add the nuclear-fuel feeder chests used at the old stops.
- **Power staging.** The autopilot's guard pauses silos and outposts at low accumulators; extend it to a priority list and add the nuclear block builder so power is not a hand job.
- **Registry and checkpoints.** `state.json` (patches, yard rows, lanes, station names, saves) so an agent can resume after a crash, plus a save before every apply (already done by the scripts).
- **Staging copy.** Run every new script first on a copy of the save (a second container on the VM) before it touches the live game. Cheap and it catches the "overwrote an existing script" class of mistakes.
- **UPS guard** in the autopilot: lower game speed when ticks per second fall under 90 percent.
- **Research priority policy** (what the autopilot queues) written down so it is testable.
- **Permissions.** An allowlist of commands for the local model (only the manifest's `run` lines), no free shell, no scheduled tasks.

## Is it all scriptable? Can it be codified into tech milestones? (item 12)
- About three quarters of it is already scripted and used. The remaining quarter is the parts that were hand-built or never built: nuclear plant and breeder, uranium with acid, fluid unload yard, signals, the platform.
- Yes to milestones. `skippy-pack/milestones.json` maps researched techs to actions: "after `railway` run discover + train-outpost", "after `kovarex-enrichment-process` run the breeder-loop builder" (marked `gap`, it is not written), "after `speed-module-3` re-run the module fill inside the power budget", "after `advanced-asteroid-processing` upgrade the platform recipes", "after `mining-productivity-3` re-audit furnace counts". Tech names were checked against the running game. `nauvis.py milestones` prints it.
- To make a milestone fire without a person: the autopilot already reads research state every minute; it can compare `milestones.json` with `force.technologies[...].researched` and write the due actions into `state.json` for the agent. It should queue and report, not apply, until a script is marked ready and tested on the staging copy.

## Order of work to close the gaps (when you say go)
1. `science-rates`, `discover`, crash-site exclusion in `clear` (small, read mostly)
2. fluid unload script, refinery lane
3. signals and train limits
4. nuclear plant builder, uranium outpost with acid, breeder loop
5. platform builder after the measurement step in the space plan
6. staging copy and milestone trigger in the autopilot

## First planet after this
**Vulcanus.** `planet-discovery-vulcanus` is already researched (Gleba and Fulgora too; Aquilo is open). Vulcanus has fixed, unspoiling resources (lava and calcite, tungsten, big ore patches), so it suits scripts and a local agent best, it gives metallurgic science (needed for asteroid reprocessing) and the foundry, and the surface is static between visits.
Its risks are demolishers (they attack mining outposts, so the first pack needs defence) and heat/power bootstrapping. **Fulgora** second (scrap recycling and electromagnetic science; lightning protection). **Gleba** last for an agent: spoilage and living resources need timing logic that is hard to script safely. Aquilo needs everything else.

## The three-goal plan (the Captain, 2026-11-09): how achievable is it?
Name of the skill: `factorio-nauvis-plus-white` (friendly build mode only, see the scope note).

| goal | what done looks like | achievable? | main risk |
|---|---|---|---|
| 1. Finish Nauvis for maximum science | all seven packs made at the same rate, labs never short, power and fuel never stall, every build named (docs/naming-sop.md) | Yes. It is ordinary work with the tools that exist. Several sessions. | Target set by the Captain: docs/science-target.md (equal packs, 10 per second first, a replicable cell). |
| 2. Skills for purple Skippy | every runbook step has a script, a dry run, a verify check and a rollback; no step marked `gap` | Yes, but it is the largest piece. The gaps are listed above: science-rates, discover, crash-site exclusion, signals, fluid unload, uranium with acid, nuclear builders, the platform builder. | The scripts were written against this one map. Positions, lanes and yard rows are still constants in places and must become registry lookups. |
| 3. Purple Skippy solves a blank world with the skill | a fresh map on the server reaches white science with only short prompts from the runbook, no help from Claude or the Captain | Partly, and not on the first try. Expect it to pass the early steps and stall where a script meets something the map did differently. | Three things, below. |

### What makes goal 3 hard
1. **The pack starts in the middle.** Every script assumes a base that already has robots, a rail yard and a bus. A blank map needs a bootstrap chapter (first drills, furnaces, power, red and green science, the first labs) that has never been written, and the research gate means early builds can only use early entities.
2. **A local model has to read a verdict and choose correctly every time.** One wrong choice in a run of a few hundred steps ends the run. The design rule (the model never writes geometry, only picks a step and reads a small JSON result) is what makes this possible at all; the verify and rollback checks must be strict enough that a wrong step is caught and undone by the script, not by the model.
3. **Time.** Research takes game hours whatever the agent does. A test run is days of server time unless the game speed is raised, and the VM costs money while it runs.

### How to run the test (goal 3), when goals 1 and 2 are far enough
- A second Factorio container on skippy-games with its own save, port and RCON port (SkippyTel `games/docker-compose.yml`), so the Captain's world is never touched. No cloud session; purple Skippy runs on skippy-pc and talks to it over the same tunnel with a different port.
- Stage A (cheap, do this first): give purple Skippy a **copy of the current save** and ask for one step at a time ("add a copper outpost"). This tests the skill and the model without the bootstrap problem.
- Stage B: a blank map with the bootstrap chapter, game speed raised, a step budget and a log of every prompt, command and verdict. Score: how far down the runbook it gets before the first human correction.
- Stage C: repeat on a second seed. One success on one seed proves little.
- Needs the Captain's yes: the second container (disk on the VM is tight), the running cost, and registering purple Skippy with the allowlist (only the manifest's `run` lines).

### Order
Goal 1 and goal 2 feed each other: each thing done by hand for goal 1 is written as a script for goal 2 at the same time, then goal 3 stage A can start before goal 1 is finished.
