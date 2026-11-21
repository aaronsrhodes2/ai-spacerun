"""Purple's workspace for turns from a Factorio game (the Captain, 2026-11-21: purple should focus on playing Factorio, with
every tool Claude used to do the same job, voice included, and nothing unrelated). This repository also holds work that is
not playing (the bridge's code, tests, other sessions' changes), so a game turn runs in a folder of its own beside it,
which holds:

    .claude/skills/factorio-copilot/SKILL.md   the player-facing role: how Skippy plays with the player
    .claude/skills/factorio/SKILL.md           the operator's manual: the live server, the backend tools, what is known
    .mcp.json                                  the tools:
        skippy-copilot, skippy-copilot-test    the mod's tools, one door per game (copilot/games.py)
        factorio                               the backend: run_lua, place_entities, game_overview, factory_problems ...
        skippy-gateway                         speech (listen: audio to text; speak: text to Skippy's voice), the house, Mentat
    CLAUDE.md                                  what the folder is for, and the operator scripts in AI-factorio/scripts

purple's bridge opens any folder under the development root as a workspace, so this one is 'f-factorio-play'. It is
written from the repository, never by hand: scripts/live_bridge.sh runs this at every start, so it cannot drift.

    python -m copilot.play_workspace           write or refresh it; prints the workspace id
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
FOLDER = ROOT.parent / "factorio-play"
WORKSPACE = "f-factorio-play"
SKILLS = ("factorio-copilot", "factorio")
GATEWAY = "http://127.0.0.1:47863/mcp"                     # SkippyTel's gateway: listen, speak, the house, Mentat

NOTE = """# factorio-play: purple Skippy's workspace for playing Factorio

Written by AI-factorio's copilot/play_workspace.py at every start of the Skippy bridge; change that, not this folder.

Every message here comes from a player in a running Factorio game. Play: that is the whole job here.
- Your role is the factorio-copilot skill. The factorio skill is the operator's manual: the server, the backend tools,
  what is known about the API. Ignore every other skill.
- Tools: the mod's door for the game the turn names (skippy-copilot: the live game; skippy-copilot-test: the test game),
  the factorio backend (run_lua and the rest, on the live game), and skippy-gateway (speak and listen, the house, Mentat).
- The operator scripts are in {repo}/scripts: run them with python from {repo}, as the factorio skill describes.
  Read before you run; never edit files here or there, and never use git: development is not done in this workspace,
  the player asks for it with /purple in the game.
"""


def make(folder=FOLDER):
    folder = pathlib.Path(folder)
    for name in SKILLS:
        text = (ROOT / ".claude" / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
        (folder / ".claude" / "skills" / name).mkdir(parents=True, exist_ok=True)
        (folder / ".claude" / "skills" / name / "SKILL.md").write_text(text, encoding="utf-8")
    repo = str(ROOT).replace("\\", "/")
    python = sys.executable.replace("\\", "/")
    servers = {name: {"command": python, "args": ["-m", "copilot.mcp_server"],
                      "env": {"COPILOT_GAME": game, "PYTHONPATH": repo, "COPILOT_LOG_DIR": repo + "/runs"}}
               for name, game in (("skippy-copilot", "live"), ("skippy-copilot-test", "test"))}
    servers["factorio"] = {"command": python, "args": ["-m", "bridge.factorio.mcp_server"], "env": {"PYTHONPATH": repo}}
    servers["skippy-gateway"] = {"type": "http", "url": GATEWAY}
    (folder / ".mcp.json").write_text(json.dumps({"mcpServers": servers}, indent=2) + "\n", encoding="utf-8")
    (folder / "CLAUDE.md").write_text(NOTE.replace("{repo}", repo), encoding="utf-8")
    return WORKSPACE


if __name__ == "__main__":
    print(make())
