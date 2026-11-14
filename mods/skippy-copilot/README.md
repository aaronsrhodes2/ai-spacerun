# Skippy Copilot

Play Factorio by talking to an AI model. The mod holds the tools the model uses and the chat between player and model.
The bridge in [copilot/](../../copilot) connects a model to it. Plan: [docs/solver-plan.md](../../docs/solver-plan.md).

The idea and the mechanism (a mod with tools, a bridge over RCON, a model behind an adapter) come from
[ai-player-v3](https://github.com/thedemon117/ai-player-v3) by demon117_. The code here is our own.

## Calling a tool

One console command carries every call:

    /skippy tools
    /skippy lookup {"name":"electronic-circuit"}

The answer is one line of JSON: `{"ok":true,"result":...}` or `{"ok":false,"error":"...","hint":"..."}`. A wrong call is
answered with what would have been right (the tool names, or that tool's parameters). Admins can type calls in the game
console; the bridge sends them over RCON. With any mod enabled the game keeps a separate set of achievements that do not
register with Steam; whether calling this command changes anything further has not been tested.

## Two ways people will play it

- **Fewest prompts.** How few things do you have to say to finish the game? The mod counts every line you type to the
  assistant, shows the count on the working light, and records how many it took at the win. One prompt can go a long way:
  say "finish the game" and the assistant takes it on as a standing goal, working through the milestones on its own, turn
  after turn, until it is done, it is stuck and needs you, or you say stop. Turns it takes on its own are not prompts.
- **Science per minute.** Say "I want 1,000 science a minute of each science". The assistant measures every pack, takes the
  target as a standing goal, and works on whichever pack is slowest until all of them are there.

## Modes

The mod has two modes, and the player can switch between them at any time: in the map's mod settings, with the button on
the working light, or by asking the assistant.

- **Builds on its own** (`free-hand`): the assistant places pieces freely while you do your own thing.
- **Moves your character** (`my-character`): the assistant walks your character around and builds with its hands and its
  inventory. With nobody in the game it uses a character the mod keeps for itself.

Switching modes stops whatever the avatar was doing. A scored run can lock the mode.

## Tools in the mod (version 0.7.0)

| Tool | What it does |
|---|---|
| `lookup`, `search` | Facts about a recipe, item, entity, technology or fluid, read live from the game |
| `map`, `tile`, `find_free` | A labelled text picture of the map; exactly what stands on a tile; the nearest empty rectangle |
| `diagnose` | Every machine by what it is doing, with examples and what each problem means |
| `bottlenecks` | The worst bottlenecks ranked by the item machines wait for; whole surface or near the player |
| `alerts` | The game's own alerts by kind, with what each means |
| `player` | Where the player is and what they point at |
| `science` | Science per minute: every pack made and used a minute, the slowest pack, and what falls short of a target |
| `run_stats` | Prompts typed so far, hours played, and what the win took |
| `design_note`, `events_read` | What a research makes possible; news of finished research |
| `reveal_map` | Reveal more map round the known edge |
| `chat_read`, `say`, `set_state` | The chat channel and the working light (used by the bridge) |
| `avatar`, `avatar_craft`, `avatar_carry`, `avatar_stop` | The character: where it is and what it carries; craft by hand; move items to and from a chest within reach; stop |
| `set_mode` | Switch between the two modes, when the player asks |
| `avatar_walk`, `avatar_mine`, `avatar_travel`, `progress`, `lock_mode` | For the bridge and the operator: start a walk, a mining job or a trip to another planet; the facts milestones are tested against; fix the mode for a scored run |
| `occupancy`, `build`, `frames` | For the bridge's planning tools: what is in the way, placing a checked plan (dry run first), the rectangles spoken places refer to |

`build` keeps the rule that nothing is built before it is researched, and places nothing unless every piece of a plan can
be placed. How a piece gets placed is decided in one spot (the executor); today that is free placement, later the walking
avatar.

## The avatar

In my-character mode nothing is placed freely. The character walks by the game's own pathfinder, and places
each piece of a plan from its own inventory once it is within building reach. It mines and crafts by hand in the time the
game takes. There is no teleport anywhere in the mod. The body is the player's own character when a player is in the game,
otherwise a character the mod keeps for itself.

## Planning tools in the bridge

These are added by the bridge and look the same to the model. They do the arithmetic and geometry in tested code
(`copilot/plan/`), reading their facts from the game through the mod.

| Tool | What it does |
|---|---|
| `plan_production` | Machines per recipe, raw inputs and belts for an item at a rate |
| `plan_row` | A row of identical machines fed by belt or by robots, from one generic cell per machine |
| `plan_route` | A belt or pipe from A to B round what stands between, underground where it must |
| `build_plan` | Send a plan to the game: dry run first, build only after a clean dry run, never twice |
| `walk_to`, `mine`, `travel_to` | Start the avatar walking, mining or travelling to another planet, and wait until it has finished |
| `milestones` | How far the game has come and what the next goal still needs |
| `set_goal`, `clear_goal` | Take on a standing goal (win the game, reach a milestone, or a science-per-minute target) and keep working toward it without further prompts; drop it |
| `locate` | Words to tiles: "the east of the base", "the upper right of my view" |

## Design notes

`scripts/notes.lua` holds one or two sentences per technology on what it lets you improve, simplify or remove. When a
research finishes, the mod puts the note and the live list of unlocks into the news, and the bridge has the model offer the
player one improvement. Notes are our own words; what a technology unlocks is always read from the game.

## The bridge

    COPILOT_RCON_PORT=27015 COPILOT_RCON_PASSWORD_FILE=path/to/file COPILOT_MODEL=qwen3:8b python -m copilot

It listens to the game chat, hands each line to the model with the mod's tools, and says the answer in the game. It drives
the working light, and it logs every tool call to `runs/` for scoring. Providers: `ollama` (default) and `openai` (any
server that speaks the OpenAI chat API). `python -m copilot --ask "..."` asks one question without the chat.

## Testing

- `python -m pytest tests/copilot_tests` runs with no game and no model: 306 tests. They cover the bridge, the planning
  code, the scorer, and the mod's own Lua run under Lua 5.2 against a stand-in game (`tests/copilot_tests/fake_game.lua`).
  Needs `pip install lupa`.
- `scripts/modserver.sh start` runs a second, headless copy of the Steam install with its own data folder (`.testserver/`),
  so the live game is never touched. `scripts/modcheck.py` builds a small known scene there and checks what every tool
  says about it. `scripts/modtest.py <tool> '<json>'` calls one tool by hand.
- `python -m copilot.score runs/` scores the bridge's logs: tool misses, repeats, stalls.

Not yet run in a real game (written 2026-11-13 while the test server was off): everything added since version 0.2.0,
which is `alerts`, `player`, `bottlenecks`, `occupancy`, `build`, `frames`, `reveal_map`, the modes, the whole avatar, planet
travel and `progress`, with the
checks for them in `modcheck.py`. They pass against the stand-in game, which models what the mod calls, not the game
itself. The avatar and planet travel lean hardest on the real game (its pathfinder, how a character walks and mines, how
a character rides a rocket and a cargo pod), so they are the parts most likely to need changes after the first real run. The working light and chat have not been seen with a real player.
