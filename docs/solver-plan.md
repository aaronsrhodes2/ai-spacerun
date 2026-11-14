# Space Age solver skill: plan

Written 2026-11-13 from the Captain's brief. **Status: not started.** Work on this plan begins only after the current run on
Fable reaches a verified Space Age solve under today's easy rules (see Gate). Until then this file is the agreed intent.

## Goal

A skill, a mod and a tool library with which a local model (purple Skippy: qwen, 130k context) solves Factorio Space Age,
start to finish, on a map it has not seen. It ends in a pull request: against ai-player-v3 if the designs still match, or
published as our own mod if they do not.

The Fable run is the data source, not the product. It will not be repeated on Fable.

## Gate

Start when all three hold:

1. The Fable run has finished Space Age in friendly build mode (free placement once researched, no enemies, no pollution).
2. The finish is verified in the game, not inferred: the win condition is read back from the save.
3. Every step of the run is in git and in the session transcripts.

"Solved" is the game's own win: a platform reaches the solar system edge (the Captain, 2026-11-13). The Captain has never
been there and wants to see what lies past it, the promethium science made out there, so the run should carry on to
that after the win.

## Principles

- **The model operates, code does geometry.** The model decides what to build, how big, where and in what order, and
  troubleshoots what does not run. Code does the arithmetic and the routing a small model gets wrong.
- **Clues, not answers.** Small generic patterns are allowed: one machine with its inputs and outputs arranged for belts
  or for robots, the same for every recipe. No large blueprints, no starter factory per planet. The test: a library
  piece has no recipe, no count and no coordinates in it.
- **The solve is a conversation.** The model makes passes over the factory (bottlenecks, alerts, errors, missed requests)
  the way a player talks a game through with a partner.
- **Everything is counted.** A run is scored by code, not judged by the model.

## What we start with

- This repository is already a fork of ai-player-v3 (remote `upstream`, our mod copy is 0.3.5, upstream is 0.4.2, four
  commits ahead of us). It brings the mod (primitives, skills, perception), a Python bridge with Anthropic and
  OpenAI-compatible providers (so a local model already plugs in), per-exchange metrics, and a latency benchmark.
- About 40 scripts from the Fable run, each with the same steps (check, dry run, apply, config, status), and the skill
  notes with every API trap met. Each script hardcodes one layout for one map: they become test references and a source
  of rules, not library pieces.
- The session transcripts and the git history: every mistake and its fix, in order.

**Finding on avatar movement.** Upstream does not walk. In 0.3.5 and in 0.4.2 alike, `move` teleports the character up
to 16 tiles, `goto` teleports anywhere, and `build_ghosts` revives ghosts with no reach check (it only removes the item
from the inventory). So there is no walking code to pull in: increment 1 is ours to write. What we keep from upstream is
the character itself, the inventory handling, the perception and the bridge.

## How it plays

The Captain's picture of the loop (2026-11-13): you start as the avatar and say, in the game, "let's start getting to red
science". Your words become the prompt; whichever model you configured plans the work and carries it out.

- **The channel is the in-game chat.** The mod reads chat lines and the model answers there, so the whole exchange sits
  in the game and in the save's log.
- **Voice sits outside the game.** A Factorio mod is sandboxed Lua and cannot reach a microphone. A small companion on
  the player's machine listens on a push-to-talk key, turns speech into text (SkippyTel already runs whisper) and types it
  into the chat. Text chat works without it.
- **Two ways to run.** Co-op: the player talks, the model works, both build. Solo: the harness feeds the milestone list
  as the prompts and nobody speaks. The scored runs are solo; the mod people play with is co-op.

## Parts to build

| Part | What it is |
|---|---|
| Executor | One layer under every tool that places, removes or configures. Two modes: god hand (today) and avatar. Tools never know which. |
| Avatar | The character walks, reaches, mines, crafts and builds under the game's own limits. Increment 1. |
| Calculators | Target rate and recipe in; machines, inputs and power out. |
| Finders | Free land, ore, water, robot coverage, nearest pole. Three ad hoc ones exist from 2026-11-13. |
| Routers | Belt, pipe, heat pipe and rail from A to B around what stands there. |
| Cells | The small generic patterns: belt-fed machine, robot-fed machine, fluid machine, direct insertion pair, train stop, miner on ore, crusher on a platform loop. |
| Diagnostics | Starved, backed up, unpowered, open alerts, stalled research. |
| Mistakes list | The traps of the Fable run as rules ("a mixed-item belt must be a loop"). |
| Milestones | A fixed list from first plate to the win, each with a test code can run. |
| Harness | Runs a model against a save, scores it, saves at each milestone, resumes after a crash. |
| Voice companion | Push-to-talk speech to text into the game chat. Optional; outside the mod. |
| Provider plugin | Paid API, local model, or a local server that speaks the Anthropic API. Upstream's two providers are the base. |

## Increments

Each has an exit test. None starts before the one above it passes, except where marked parallel.

| # | Increment | Exit test |
|---|---|---|
| 0 | Mine the Fable run: mistakes list, milestone list, the minimum set of prompts that drives a solve | A written list reviewed by the Captain |
| 1 | **Avatar**: walking by the game's pathfinder, reach and build distance enforced, mining and crafting by the character's own states, no teleport anywhere in the mod | A script walks the character across a base with obstacles and builds a 10-machine line from its inventory, with zero teleports and zero out-of-reach actions |
| 2 | Library and harness, tuned for qwen | qwen finishes Nauvis (rocket launched) under easy rules, scored |
| 3 | Full solve under easy rules by purple Skippy | No tool misses, hallucinations, stalls or destructive steps over a whole run |
| 4 | Same on a new seed | Same score, no map-specific code |
| 5a | Avatar only: the god hand is switched off | Full solve |
| 5b | Pollution, evolution and aggression at vanilla | Full solve, base never lost (parallel with 5c, 5d) |
| 5c | Every machine manufactured, nothing placed free | Full solve (parallel) |
| 5d | Quality only from quality modules | Full solve (parallel) |
| 6 | 5a to 5d folded together, no mods but ours | Full solve |
| 7 | Fresh vanilla seed, purple Skippy, Lua through a model only | Full solve with a clean score |
| 8 | Last, for people without a strong machine at home: stock qwen coder on ollama, our skill, nothing else | Full solve |

On "no mods but ours": our mod and RCON are how the model reaches the game, so the end state is vanilla rules with one
mod, not zero mods. Achievements stay off for that reason.

## Increment 1 in detail: the avatar

- **Walk.** Ask the game's pathfinder for a path (`surface.request_path`), then follow it by setting the character's
  `walking_state` each tick toward the next waypoint. Detect a stuck character (no progress for N ticks) and re-path.
- **Reach.** Every build, mine, insert and take checks the character's own reach and build distance first. Out of
  reach is an error the tool reports, never a silent teleport.
- **Build.** The item leaves the inventory and the entity is placed only where the game would let a player place it.
  Ghosts are built by walking to them, nearest first.
- **Mine and craft.** By the character's mining and crafting states, so they take the time the game says.
- **Travel.** Vehicles, trains and rockets between planets come after walking works; until then other planets are
  reached the way the run reaches them.
- **Remove.** `goto`, `/ai-come` and the 16-tile `move` teleport go, or stay behind a debug setting that the harness
  counts as a violation.

The executor makes this a swap: under easy rules a tool calls the god hand, under increment 5a the same call queues work
for the avatar.

## Scoring

Per run, counted by the harness:

- **Tool miss:** a call the tool rejected (bad name, bad arguments, failed dry run that was applied anyway).
- **Hallucination:** a claim in the model's report that the game state contradicts (checked for a fixed set of facts:
  counts, positions, research, production rates).
- **Stall:** no milestone progress in a set amount of game time.
- **Destructive step:** removing or breaking something that was working, measured by production before and after.
- **Restart:** a crash or a resume from a milestone save.

A clean run has zero of the first four.

## Running it

- Game speed 10x has held without crashes; runs are cut into nightly portions.
- A save at every milestone; a crashed night resumes from the last one.
- The server and client run in a sandbox that restarts either when it falls over.
- More than one game server on GCP and a client on skippy-core are possible. GCP servers cost money: ask before
  starting any.

## Risks

1. **Design by a small model.** Without large blueprints qwen must size and place every block. Expect working but ugly
   factories and many passes. The cells and routers are what keep this within reach.
2. **Enemies at vanilla levels** and **quality from modules** are the two longest steps; Gleba spoilage under attack is
   the worst single case.
3. **Run length.** A full solve is hundreds of game hours even at 10x.
4. **Drift from upstream.** The further our mod goes, the less likely a merge. Decide at increment 1 whether to send
   the walking avatar upstream as its own pull request.

## Upstream and our own mod

Settled 2026-11-13 (the Captain):

- We take the concept and the mechanism from ai-player-v3 (a mod with primitive actions and a remote interface, a bridge
  over RCON, a model behind a provider adapter), not its code. We write our own mod and bridge with those mechanisms.
- Everything is offered to the ai-player-v3 author once, at the end, for them to pull from if they wish. No early pull
  request.
- Today this repository is a fork: `mod/` and most of `bridge/` are the upstream author's code under the MIT licence.
  Writing our own replaces them; that is a work item in increment 1 (mod) and increment 2 (bridge). The upstream project
  is credited by name in our README either way.
- The solve is the solar system edge. The stock qwen coder run is the very last step; our own runs use purple Skippy with
  our skill and tuning, to get the most out of the machines at home without paying for tokens.
