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
