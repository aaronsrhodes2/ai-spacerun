# Space Age solver skill: plan

Written 2026-11-13 from the Captain's brief. **Status: the mod is started.** The Captain lifted the gate for the mod the same
day: one chat builds the mod while the main chat finishes the Fable run. Scored runs on purple Skippy still wait for the
verified solve (see Gate).

Built so far:
- **The mod** (`mods/skippy-copilot`, version 0.14.0), forty tools: lookup, search, map, tile, find_free, diagnose,
  bottlenecks, alerts, player, design_note, events_read, reveal_map, chat_read, say, set_state, and for the planner
  occupancy, build and frames. `build` is a dry run unless told otherwise, refuses anything not researched, and sits on
  an executor layer so the walking avatar can replace free placement without changing a tool.
- **The walking avatar** (increment 1, mod 0.4.0): walks by the game's pathfinder, re-paths when stuck, builds each piece
  from its own inventory within building reach, steps aside when it stands where a piece goes, mines and crafts by hand,
  carries items to and from chests in reach. No teleport anywhere. `build` hands a checked plan to it when the executor is
  `avatar`; under free placement nothing changes. The increment's exit test (walk across a base with obstacles, build a
  ten-machine line from the inventory, zero teleports, zero out-of-reach placements) passes against the stand-in game.
  It has not walked in the real game yet.
- **Three modes, one ladder, switchable at any time** (the Captain, 2026-11-13: a mode of the mod, not a choice for a
  whole run; the moves between playing by hand, talking to an assistant and being moved must be smooth, because people
  start by hand and are uncomfortable until they get the hang of it). Advises only (mod 0.16.0): the player plays, the
  assistant looks and says what it would do, and every tool that changes the world refuses except as a dry run. Builds
  on its own. Moves the player's character. Switched by asking, by a button on the working light that steps through
  them, or in the map's mod settings. While the assistant moves the character, the player's own controls (move, mine,
  build, heard through linked custom inputs in `data.lua`) take it back at once; the mode stays. A scored run can lock
  the mode. The default is still builds-on-its-own. Not yet tried in a real game: whether the linked inputs fire as
  the documentation says.
- **Voice** (the Captain, 2026-11-13: speech to text and text to speech in the game, in purple Skippy's voice, so the
  game can be played with Claude Desktop closed and no keyboard). A mod cannot hear, speak or reach the network, and
  the house's voice gate wants a pass signed from the home token, which must never come here. So the house's own
  listener (SkippyTel `services/satellite`: wake word "Skippy", Whisper, Skippy's voice) keeps the ears and the mouth,
  and the bridge offers it a door on loopback, `copilot/voice_door.py`, port 47862: `POST /hear` for a spoken line,
  `GET /said` (long poll) for everything Skippy says, `GET /health` as the sign that a Factorio session is on. A spoken
  line enters the game through the mod's `hear` tool (0.17.0) and counts exactly like a typed one. Built and unit-tested
  on this side. **Not built: the listener's side**, a SkippyTel change: while the door's /health answers, what follows
  the wake word goes to /hear unless it is a house command, and the lines from /said are spoken (long ones through
  the gate's /summary). Also not built: starting the bridge by itself when the game starts.
- **Planet travel** (mod 0.6.0): the avatar walks to a silo with a rocket ready, rides the rocket to a ship in orbit whose
  schedule already goes there (no ship is re-routed), rides it, and drops to the surface. It must carry nothing. The first
  landing opens a planet that had no surface.
- **The milestone list** (`copilot/milestones.py`): 21 steps from the first plates to the edge of the solar system and
  promethium science beyond, each with a test run against facts the mod reports. The model is told the next goal and what
  it still needs; a watch logs a stall when nothing counts toward any milestone for two game hours. A unit test checks
  every name in the list against the installed game's data.
- **The two ways people will play it** (the Captain, 2026-11-13), mod 0.7.0:
  - *Fewest prompts to finish the game.* The mod counts every line a player types, shows the count on the working light and
    records what the win took. A standing goal lets one prompt go a long way: the model calls `set_goal` and the bridge then
    gives it a turn of its own every so often, with the goal and the next milestone, until the goal is reached, the model
    says it is blocked, three turns in a row do nothing, or the player says stop. Turns of its own are logged but are not
    prompts.
  - *Science per minute.* The `science` tool measures every pack over ten minutes on all surfaces; a factory's rate is its
    slowest researched pack. "1,000 a minute of each" is a standing goal of its own kind.
- **A planet as one goal, and playing fair** (the Captain, 2026-11-13): people will say "solve Nauvis" and expect a planet
  per prompt. Every milestone now belongs to a place, and a place is a standing goal. That expectation may be optimistic:
  real problems will come up and the player will have to deal with some. We do not invent problems and we do not hide them.
  The assistant does the best job an expert could and never cheats: nothing conjured, research earned, nothing built before
  it is researched, failures said plainly. The run's record counts pieces placed freely apart from pieces placed by a
  character's hands, and unit tests check that no file of the mod inserts items, unlocks recipes, writes research or
  teleports.
- **Joints** (the Captain, 2026-11-13: the acceptable small blueprints are the ones for where lines intersect, and there
  must be many more than the first eight): twenty layouts and one set of rules so far, each for one kind of meeting, with
  the problem it solves. Belts: crossing, filter splitter, priority merge, overflow valve, tee, balancer (two and four
  belts; a unit test sends flow through it to prove every output gets a quarter of every input), side load, lane pair.
  Inserters: filtered pick, reach over. Robots: belt to robots, robots to belt, robot-run machine. Fluids: pipe crossing,
  long pipe, machine fluid ports, fluid machine on belts (pipes tunnel under the belts), barrel station. Power: pole line.
  Trains: wagon side, and rail signals as rules only until signal positions are checked in the game. Anything that
  depends on a building is read from the game when the joint is laid out. A test refuses any joint with more than one
  machine or more than thirty pieces. More will be added as real games show which meetings come up.
- **A building's finite set of connections** (the Captain, 2026-11-13): the `connections` tool lists, for any building,
  every way it can meet its lines, from the game's facts: sides, fluid connections, free tiles for inserters, heat, and
  for a recipe the belts its ingredients need and the joint that fits.
- **What a blank map needs** (mod 0.11.0): finding ore, oil and water (`find_resources`); finding where a fussy piece can
  really go by trying it (`find_placement`, the habit that found the offshore pump's spot in the Fable run); single pieces
  (`plan_pieces`); drills on both sides of a belt (`miner_row`); two fluid buildings joined port to port, such as a boiler
  and a steam engine (`direct_coupling`); removing pieces with a dry run first; changing a recipe.
- **Research is the player's to steer, and three things make the assistant come to the player** (the Captain,
  2026-11-13): research running out, a new alert, and an obvious bottleneck. Each is an opening to engage: the assistant
  looks into it, makes ONE suggestion with its reason, and asks before acting. For research it suggests a technology (one a
  milestone needs comes first) and queues it when the player agrees; it chooses on its own only if told to.
- **A leg of skills testing** (`python -m copilot.leg copilot/legs/first.txt`): a fixed list of twenty prompts on a fresh
  map covering facts, seeing the world, diagnosis, small builds, research and honesty (it must refuse "give me 500 iron
  plates" and "build a rocket silo right now"). The same list every time, scored by the log.
- **One AI source, and a setup a newcomer can get through** (the Captain, 2026-11-13: purple Skippy in a specific workspace
  is the source for all turns; one source, one key, no collections of models; friendly to new AI users):
  - Settings name exactly one source: `anthropic`, `openai`, `ollama` or `purple`, with one address and one key.
  - `anthropic` is any server that speaks the Anthropic Messages API. Skippy Core serves purple's model that way, with
    tool use, so the bridge's own loop can run every turn on it in seconds: one address, one key. Not yet tried live.
    The Captain's final choice (2026-11-13) is purple for all turns: `copilot/copilot.env` on skippy-pc sets
    `COPILOT_SOURCE=purple` with workspace `f-ai-factorio`. The Core settings are kept there, commented out, read from
    the dev-root vault by name (`COPILOT_VAULT`, `$SKIPPY_CORE_URL` and so on), for comparison runs.
  - Purple Skippy is the development agent, reached through its MCP door on skippy-pc (`127.0.0.1:47860/mcp`,
    SkippyTel's purple-mcp; no key on loopback, and the home token never comes near this repository). Every call is a
    task; the work is a job of seconds to minutes, one at a time. `copilot/purple_client.py` is the client (plain
    JSON-RPC over urllib). Two uses: `/purple <task>` in the game (mod 0.15.0), run by the bridge as a background job
    with the house rules in the prompt, and the `purple` source for every turn, which now goes through the same door.
    Tried live 2026-11-13: health, and a one-word run that came back done in one call.
  - Purple Skippy is an agent, so it thinks in its own loop: the bridge sends each turn to SkippyTel's bridge for one
    conversation in one workspace, and purple reaches the game through this repository's MCP server, which offers the same
    tools. The skill purple reads is the same text a plain model is given; a test keeps them identical.
  - `python -m copilot --check` walks the setup in order, stops at the first thing wrong and says the one thing to do. It
    ends with a real question and checks the answer was looked up in the game.
  - The working light reads "not connected" when nothing outside the game is calling it.
  - The standing goal is kept in the save and plans in a file, so the bridge and an agent's tool server agree.
  - Not done: the workspace itself. SkippyTel's project registry has no entry for this repository yet; adding one is a
    change to SkippyTel and the Captain's call.
- **Thrift** (the Captain, 2026-11-13): two more aims players drive toward. *Waste nothing*: `surplus` lists what is made
  faster than used, what runs short and which chests stand full; the skill's order for a surplus is make less, make
  something useful, then recycle or void, and on a platform reprocess before throwing overboard. *Compact*: `footprint`
  measures the ground a block really uses and what it does; the skill's routine is measure, plan the same work tighter,
  build beside, see it working, ask, remove the old. A search for the tightest layout is not written: the model plans it
  from cells and joints and the tiles are compared.
- **Everything moving** (the Captain, 2026-11-13): a third aim, every machine working and none idle. `utilisation` gives
  the share of machines working now and averaged over the last two minutes, and the idle groups with why. It is a standing
  goal of its own kind (`busy`, a percentage). The game has no dial for a machine's effort or power, so the skill says
  what really balances a factory: machine counts by ratio, the throughput between them, and modules and beacons.
- **Context budget** (the Captain, 2026-11-13: a local model has about 130k of context; the skill, joints, planners and
  game knowledge must fit comfortably). Measured: the skill text is about 1,600 tokens and the 42 tool descriptions about
  7,500, so a model always carries about 9,100 tokens, 7% of the window. Everything else is fetched when asked for and is
  not in the model until then: game facts by `lookup`, the joints by their catalogue, plans by id. One tool result is cut
  at 6,000 characters. With a plain model every turn starts fresh and carries only a short note of the last six
  exchanges, words only, so a long game does not fill the context; purple Skippy keeps its own conversation. Unit tests
  hold these lines: the fixed part under a tenth of the window, no joint and no game fact spelled out in the skill, no
  runaway tool description. Condensing further (fewer, broader rules; shorter descriptions; rarely used tools offered
  only when relevant) waits for run data.
- **Planning code in the bridge** (`copilot/plan/`, pure and unit-tested): production calculator, layouts with overlap
  check and turning, the generic cells (belt-fed machine, robot-fed machine, direct pair, rows), a belt and pipe router
  with underground pairs, and pointing with words. The model reaches them as plan_production, plan_row, plan_route,
  build_plan and locate.
- **Design notes by technology** (32 notes): on a finished research the model is told what it unlocked and what can now be
  improved, and offers the player one change.
- **Alerts** (the Captain, 2026-11-13): the game's alerts are given to the model at the start of every turn, and a new
  kind of alert makes the model look into it and offer one suggestion.
- **The bridge** (`copilot/`): game chat in, model with tools, answer out, working light, a log of every call, and a
  scorer for those logs. Providers: Ollama, any OpenAI-compatible server, and any server speaking the Anthropic Messages API.
- **Tests**: 460 unit tests that need no game and no model, including the mod's own Lua run under Lua 5.2 against a
  stand-in game; `scripts/modcheck.py` for the mod on a local headless test server. The Lua tests found three bugs on
  their first run (a search centred one tile off, a wrong player returned for an unknown name, an unstable ranking).
- **First run with a local model** (qwen3:8b on Ollama, 2026-11-13, mod 0.2.0): three questions through the bridge, all
  answered correctly from tool results, 4 tool calls, 1 miss that the tool's error message corrected in one retry, 35 to
  44 seconds each once the model was loaded.

Where the code lives: the mod holds everything that touches the game; the bridge holds the planning. The split was made so
the planning could be unit-tested with no game running. Both ship together.

Not yet run in a real game: everything added in mod 0.3.0 (alerts, player, bottlenecks, occupancy, build, frames,
reveal_map). They pass against the stand-in game only. Live runs are for late at night, when the Captain is not playing
(2026-11-13).

Next, the first night run, in this order:
1. `scripts/modserver.sh new` then `start`: the mod has not loaded in a real game since version 0.2.0, so expect errors
   here first; fix until it loads.
2. `scripts/modcheck.py`: every tool against a known scene, including the avatar and the fluid-port check.
3. `python -m copilot.leg copilot/legs/first.txt` on a fresh map with a local model; read the score and the refused calls.
4. Fix what the run shows, in the tool descriptions and the skill prompt first, then in code.
Still to write after that: the first hour by hand (the avatar has no way yet to take pieces down), a real trip between
planets, and the Anthropic model adapter.

## Publishing on the mod portal (researched 2026-11-13)

- **The name** (the Captain, 2026-11-13): in the game it is **Skippy**, in long form **Skippy the Foreman** (the mod's
  title), and "Skippy" is the wake word, the same one
  purple Skippy answers to. "Copilot" is not to be used as a name (Microsoft's and GitHub's products). A public name is
  only needed before publishing, and must be chosen then; "Compy" (after Compilatron, the game's own helper robot) was
  liked as a wake word and is the candidate. The internal identifiers still say `skippy-copilot`, `copilot` and
  `COPILOT_`; they are renamed once, together with the public name. A wake word wants two syllables with hard sounds.

What it takes, from the official packaging and API pages and the terms of service; items marked unconfirmed had no
official source.

- **Account**: a factorio.com account that owns the game. No fee was found (unconfirmed).
- **Package**: `skippy-copilot_x.y.z.zip` holding one folder with `info.json` at its root. Required fields: name, version,
  title, author. Also wanted: `thumbnail.png` (144 by 144), `changelog.txt` in the game's strict format (added, and checked
  by a unit test), a LICENSE file matching the licence chosen on the portal.
- **Still to do before a first upload**: the thumbnail; the LICENSE file (the Captain's choice of licence and copyright
  name); confirm the right `factorio_version` for the portal (ours says 2.1, the installed game's line; the documentation
  example is 2.0); gallery pictures; a load test with only base and our mod enabled, and one with Space Age.
- **Upload**: by the web form, or by API key (scopes for publish, upload and edit) through the publish and upload
  endpoints; `fmtk` is the usual command-line tool.
- **Portal fields**: category (ours: utilities), tags, licence (MIT is offered), source URL, summary of at most 500
  characters, description and FAQ in Markdown.
- **Rules**: the terms require permission for anything that is not ours and let the makers remove a mod without notice. No
  review before a mod goes live was found, and no rule about a companion program or RCON (both unconfirmed). A mod cannot
  open network connections itself, which is why the bridge exists.
- **The upstream mod**: we use its idea and mechanism, not its code, and credit it. Had we kept its files, the MIT licence
  would require shipping its licence text and copyright notice.
- **Achievements**: with any mod enabled the game keeps a separate achievement set that does not register with Steam.
  Script commands (`/c`, `/sc`) disable achievements for the save; whether our own `/skippy` command does is unconfirmed
  and must be tested. This corrects an earlier claim in the mod's readme.
- **Multiplayer**: keep all changing state in `storage`, register events and commands at load and never conditionally.
  The mod does this; it has not been run with two players.

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

### The aim: a whole game with no mouse, keyboard or controller

The Captain, 2026-11-13: the player sees a problem, says what to do about it, and the model reasons as far as it can and
uses every tool it has to do the best job of it. The player never has to touch an input device.

What that asks for beyond building:

- **A working light.** Always visible in the game: idle, thinking, working, blocked, failed. The player can read the
  model's text as it goes or ignore it and wait.
- **A spoken summary.** Short and friendly, of what was done and what was not. Speech is made by the companion, not the
  mod (a mod can only play sounds shipped with it).
- **The camera by voice.** "Show me the copper line", "go to Gleba", "zoom out": the mod moves the player's view and
  tags the spot.
- **Stop and undo by voice.** "Stop" halts the work at once. Anything that removes or replaces working machines is
  said aloud first and waits for a yes.
- **The game's own menus.** Starting, saving, loading and joining are outside any mod; the companion does those.

This is a second product goal beside the scored solve. The solve proves the model can play; this makes it a game someone
plays.

## Parts to build

| Part | What it is |
|---|---|
| Executor | One layer under every tool that places, removes or configures. Two modes: god hand (today) and avatar. Tools never know which. |
| Avatar | The character walks, reaches, mines, crafts and builds under the game's own limits. Increment 1. |
| Calculators | Target rate and recipe in; machines, inputs and power out. |
| Map grid | A labelled text grid of any window of the map, with a legend. The model's eyes; no screenshots. |
| Finders | Free land, ore, water, robot coverage, nearest pole. Three ad hoc ones exist from 2026-11-13. |
| Routers | Belt, pipe, heat pipe and rail from A to B around what stands there. |
| Cells | The small generic patterns: belt-fed machine, robot-fed machine, fluid machine, direct insertion pair, train stop, miner on ore, crusher on a platform loop. |
| Diagnostics | Starved, backed up, unpowered, open alerts, stalled research. |
| Mistakes list | The traps of the Fable run as rules ("a mixed-item belt must be a loop"). |
| Milestones | A fixed list from first plate to the win, each with a test code can run. |
| Harness | Runs a model against a save, scores it, saves at each milestone, resumes after a crash. |
| Voice companion | Speech to text into the game chat, spoken summaries back, and the game's menus. Outside the mod. |
| View control | Camera moves, map tags and the working light, driven by the model. In the mod. |
| Provider plugin | Paid API, local model, or a local server that speaks the Anthropic API. Upstream's two providers are the base. |

## How the model sees the map: text grids, not screenshots

Settled 2026-11-13 (the Captain: essential, and much better than screenshots, which are costly and need a different model).
The Fable run found room for every build this way: the game prints one character per tile and the model reads the layout.
A local text model can do the same with no vision model at all, if the tool is strict:

- **The grid is for orientation only.** It carries a legend, labelled rows and columns and a small fixed window (about 40
  tiles wide). The model never works out a coordinate by counting characters.
- **Exact questions go to code.** "A free 3 by 5 rectangle near here", "what stands on this tile", "a path from A to B"
  each return coordinates. The model chooses among answers; it does not measure.
- **Every placement is dry-run first**, so a misread costs one retry and breaks nothing.
- **It is measured.** The harness quizzes the model on grids with known answers (where is the gap, what blocks this spot)
  to find how large a window it reads reliably, before the solve depends on it.

## Working habits from the Fable run, to build into the skill

These are what got designs working in practice (2026-11-13). Each becomes a tool or a rule, so a local model gets the habit
without having to think of it.

| Habit | What it replaces | In the skill as |
|---|---|---|
| Ask the game for facts: recipe inputs, machine speed, item weight, where a machine's pipe and heat connections sit | Remembering them, often wrongly | Lookup tools; the rule "never state a game number you did not look up" |
| Wrap the game's scripting: the model calls named tools, it does not write raw Lua | Most errors of the run (wrong field names, one-line limits, silent empty replies) | The tool library itself; raw Lua only as a last resort |
| Check a layout in code before the game sees it: every piece claims its tiles, two claims on one tile stop the build | Overlaps found one failed placement at a time | A layout checker under every placement call |
| Dry run, then apply, then read back what each machine is doing | "Placed" mistaken for "working" | Every build tool returns machine states a minute later |
| Build one unit, see it work, then repeat it | A whole block built on one wrong assumption | The rule, and a "repeat this cell N times" tool |
| Probe when the rule is unclear: try every position or direction and keep what the game accepts | Reasoning about placement rules | A "where can this go near here" tool |
| Copy a working example: look at one the player or an earlier step already built | Guessing an orientation | An "inspect and describe" tool |
| Measure before sizing: production and use per minute, per item | Building for a guessed rate | The diagnostics; no sizing call without a measured rate |
| Design for one side, turn it in code | Four hand-made copies with four chances to slip | Rotation and mirroring inside the placement tool |
| Steps safe to run again: check, build, configure, status | A half-finished build nobody can resume | The shape of every tool |
| Wait outside the conversation: a watcher that wakes the model on an event | Polling, and filling the context with waiting | The harness |
| Keep the mistakes: every trap written down as a rule the day it is met | Meeting it again | The mistakes list, loaded with the skill |

What does not transfer as a habit: long chains of reasoning about circuit logic and ratios across a whole factory. Those
go into calculators and a small set of named control patterns (cap a stock, gate an inserter on a count, loop a mixed belt).

## Knowledge the skill carries, so nobody has to say "go read the documentation"

The Captain, 2026-11-13: Fable came with a great deal of Factorio knowledge and could search the web; a local model has
neither to the same degree, and the player should not have to send it off to read. The skill must already be good at this.
Four sources, all offline, all reached by lookup so they never fill the context:

| Source | What it answers | Where it comes from |
|---|---|---|
| Game data | Recipes, technologies and what they need, machines, surface conditions, item weights | Read from the running game itself, so it is exact for the installed version and mods |
| Scripting reference | Which fields and calls exist on which object | The game makers' published reference, indexed for search; only the tool builders and the last-resort raw script need it |
| Playbook | How each planet works and in what order to do things: heat on Aquilo, spoilage on Gleba, scrap on Fulgora, lava on Vulcanus, platforms | Written by us from this run, in our own words |
| Mistakes list | What not to do, and why | This run's transcripts and git history |

**The game is the source of truth** (the Captain, 2026-11-13). The in-game Factoriopedia is drawn from the game's own
object library, and a mod can read that same library live: every item, recipe, machine, resource and technology, as the
installed game and its mods define them. The skill reads it live and never from online knowledge, so a modded game gives
modded answers.

**What the library does not say is found by experiment.** Behaviour is not in the data: that an inserter cannot reach into
a cargo bay, that a boiler does nothing in space, that a rocket turret fires at small asteroids. The skill keeps a set of
small scripted experiments, run in a scratch area, each asking one such question and recording the answer for this game
version and mod set. This is our own test suite. The game's engine and its makers' tests are not public (only the game's
data files and the scripting reference are), so there is nothing of theirs to borrow here.

Rules: the model looks things up by topic or by name and gets a short answer; nothing is loaded whole. The playbook is our
own writing, not copied from the wiki. The web stays available as a last resort when the player asks for it.

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
- **Travel between planets.** "Now I want to go to Vulcanus" is a routine of its own: empty the inventory (the game lets
  nobody board a rocket carrying items), board the silo's rocket, ride a platform that is scheduled there, drop to the
  surface. The first landing on each planet has to be the avatar: nothing can be built there until a roboport stands.
- **After robots, build as a player does.** Vanilla lets a player place ghosts anywhere through the remote view, other
  planets included, and robots build them. So under the avatar rule the character builds by hand within reach until
  robots exist; after that the model places ghosts and the robots do the work, as a human would. That is still vanilla.
- **The camera is separate from the avatar.** The remote view looks anywhere without moving the character, so the camera
  director ("show me the copper line", "zoom out") never needs the avatar to walk.
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
