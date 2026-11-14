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
console; the bridge sends them over RCON. The command is not a script command, so it does not disable achievements.

## Tools (version 0.2.0, all read-only except `say` and `set_state`)

| Tool | What it does |
|---|---|
| `lookup` | Facts about a recipe, item, entity, technology or fluid, read live from the game |
| `search` | Internal names that contain a piece of text |
| `map` | A labelled text picture of a window of the map, one character per tile, with a legend |
| `tile` | Exactly what stands on one tile |
| `find_free` | The nearest empty rectangle of a given size |
| `diagnose` | Every machine by what it is doing, with examples and what each problem means |
| `design_note` | What a researched technology makes possible, and our note on what can now be improved |
| `events_read` | News from the game: research that finished, with its unlocks and design note |
| `chat_read` | What players typed in the game chat |
| `say` | Say something in the game chat |
| `set_state` | The working light at the top of the screen: idle, thinking, working, blocked, failed |

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

`scripts/modserver.sh start` runs a second, headless copy of the Steam install with its own data folder (`.testserver/`),
so the live game is never touched. `scripts/modcheck.py` builds a small known scene there and checks what every tool says
about it (29 checks). `scripts/modtest.py <tool> '<json>'` calls one tool by hand.

Not yet tested: the working light and chat with a real player in the game (the test server has no players).
