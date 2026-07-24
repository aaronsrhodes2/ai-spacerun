# AI-factorio

Playing Factorio: Space Age by talking to Claude Code. The goal is to actually
finish Space Age — all planets, final objectives — with Claude doing the
building, driven conversationally by the player.

As far as we know, this hasn't been done before. Progress, dead ends, and
design decisions are logged in [docs/progress.md](docs/progress.md) as we go.

## How it works

This repo is a fork of [thedemon117/ai-player-v3](https://github.com/thedemon117/ai-player-v3)
(MIT), a Factorio 2.0 mod that spawns a controllable AI character and exposes
it over RCON. The upstream project supports two modes:

- **Autonomous** (`python -m bridge.main`) — the mod's own bridge calls an LLM
  provider in a loop and drives the character itself.
- **MCP** (`python -m bridge.factorio.mcp_server`) — an external MCP client
  drives the character on demand instead.

We use the **MCP mode exclusively**. Claude Code is registered as this
project's MCP client (see `.mcp.json`), so Claude itself is the brain — no
LLM API key is configured anywhere in the mod or bridge, only RCON
credentials. The mod's built-in autonomy loop is switched off
(`set_autonomy(false)`) so nothing competes with Claude for control.

```
Factorio (hosted as solo Multiplayer — RCON is not available in Singleplayer)
   │  RCON (loopback, local-rcon-socket/password in config.ini)
   ▼
bridge/factorio/mcp_server.py  ──stdio (MCP)──►  Claude Code (this repo's .mcp.json)
```

## What's ours vs. upstream

- `mod/`, `bridge/` — upstream `ai-player-v3`, as cloned. Changes we make here
  are genuine mod/bridge development (new skills, new MCP tools), kept in the
  same layout as upstream so a diff against `thedemon117/ai-player-v3` stays
  meaningful.
- `scripts/` — our own tooling (dev-loop scripts, blueprint indexing, etc.),
  not part of upstream.
- `blueprints/` — our own local reference library of blueprint strings.
- `docs/` — our own project documentation and progress log.

## House rules for this playthrough

See the "Play parameters" and "Project discipline" sections of the working
plan for the full list; the two that matter most:

- **Destructive in-game actions are fine, no need to hesitate** — Factorio is
  lossless. Mining, deconstructing, rebuilding: all reversible.
- **The save file is never edited directly to shortcut a goal.** All progress
  comes from legitimate in-game actions through the AI character. Reading the
  save/map for information is fine; writing to it outside the game's own
  mechanisms is not.

## Setup

See upstream's own [README](https://github.com/thedemon117/ai-player-v3#readme)
for the general mod/bridge setup. Two things this fork does differently:

1. **RCON on the desktop client**: Factorio's RCON only binds when the save is
   hosted as (solo) Multiplayer — Singleplayer never opens the port, no matter
   what launch flags are passed. Enable it via `config.ini`'s `[other]`
   section (`local-rcon-socket` / `local-rcon-password`), then launch via
   **Multiplayer → Host saved game**, not Singleplayer → Load Game.
2. **No LLM key needed** — `bridge/.env` only needs `FACTORIO_RCON_HOST`,
   `FACTORIO_RCON_PORT`, `FACTORIO_RCON_PASSWORD`, and `FACTORIO_OUTPUT_DIR`.
   We only ever run `bridge/factorio/mcp_server.py`, which never calls an LLM
   provider itself.
