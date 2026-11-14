"""Skippy's bridge: it connects ONE AI source to the game.

    python -m copilot --check         go through the setup step by step and say plainly what works and what does not
    python -m copilot                 listen to the game chat and answer; keep working toward a standing goal
    python -m copilot --ask "what do I need for green circuits?"      one question, the answer printed

Settings: a file named copilot.env next to this package (copy copilot.env.example), or the same names in the environment.

  The game
    COPILOT_RCON_HOST          default 127.0.0.1
    COPILOT_RCON_PORT          default 27015
    COPILOT_RCON_PASSWORD      or COPILOT_RCON_PASSWORD_FILE (a file holding it)

  The AI: one source, one key
    COPILOT_SOURCE             anthropic  any server that speaks the Anthropic Messages API: Skippy Core's model, or Anthropic
                               openai     any server that speaks the OpenAI chat API (most hosted and local servers do)
                               ollama     a local Ollama server
                               purple     purple Skippy, the agent of the SkippyTel project, working in one workspace.
                                          An agent built for long jobs: a turn takes minutes and it runs one at a time.
    COPILOT_URL                where the source is. anthropic: the server's address, such as http://skippy-core:11434
                               openai: the API's base, such as https://api.example.com/v1    ollama: default http://localhost:11434
                               purple: its MCP door, default http://127.0.0.1:47860/mcp
    COPILOT_KEY                the source's key, or COPILOT_KEY_FILE (a file holding it). Not needed for a local Ollama,
                               nor for purple on the same computer.
    COPILOT_MODEL              anthropic, openai and ollama: the model's name. purple needs none.
    COPILOT_WORKSPACE          purple only: the id of the project (workspace) purple works in

  Purple Skippy for a task, whatever the source: type  /purple <what to do>  in the game (and  /purple stop).
    COPILOT_PURPLE_URL         purple's MCP door, default http://127.0.0.1:47860/mcp; set it to "off" to switch /purple off
    COPILOT_PURPLE_PROJECT     the project purple works in for those tasks, default f-ai-factorio

  Voice: the house's listener hands what it hears to a door on this computer and speaks what Skippy says (copilot/voice_door.py).
    COPILOT_VOICE_PORT         the door's port, default 47862; set it to "off" for no door

  Optional
    COPILOT_VAULT              a file of NAME=value lines kept elsewhere (a shared .env). Any setting here may then be written
                               as $NAME and is read from that file, so a key need not be copied into copilot.env.
    COPILOT_NUM_CTX            context size asked of Ollama, default 16384
    COPILOT_LOG_DIR            where run logs go, default ./runs
    COPILOT_STALL_HOURS        game hours without progress before a stall is logged, default 2
    COPILOT_GOAL_PAUSE         seconds between the turns the assistant takes on its own toward a goal, default 20
"""
import os
import pathlib
import sys
import time

from .agent import Agent
from .game import Game
from .loop import AlertWatch, Bridge, alert_prompt, news_prompt, say          # noqa: F401  (re-exported for callers and tests)
from .models import make
from .purple import Purple, PurpleAgent, SourceError
from .purple_client import DEFAULT_URL as PURPLE_URL, PurpleClient
from .toolbox import Toolbox
from .tools import LocalTools
from .voice_door import PORT as VOICE_PORT, VoiceDoor

HERE = pathlib.Path(__file__).parent
SOURCES = ("anthropic", "openai", "ollama", "purple")


class SetupError(Exception):
    """Something in the settings is missing or wrong, said so a newcomer can fix it."""


def _lines(path):
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def settings():
    env = dict(os.environ)
    f = HERE / "copilot.env"
    if f.exists():
        for k, v in _lines(f).items():
            env.setdefault(k, v)
    return resolve(env)


def resolve(env):
    """Settings written as $NAME are read from the vault file (COPILOT_VAULT), or from the environment."""
    refs = [k for k, v in env.items() if k.startswith("COPILOT_") and v.startswith("$") and len(v) > 1]
    if not refs:
        return env
    vault = {}
    if env.get("COPILOT_VAULT"):
        p = pathlib.Path(env["COPILOT_VAULT"])
        if not p.exists():
            raise SetupError("COPILOT_VAULT points at %s, which does not exist" % p)
        vault = _lines(p)
    for k in refs:
        name = env[k][1:]
        value = vault.get(name) or os.environ.get(name)
        if not value:
            raise SetupError("%s is set to $%s, but %s has no value named %s" % (k, name, env.get("COPILOT_VAULT") or "the environment", name))
        env[k] = value
    return env


def secret(env, name):
    """A secret given directly or as a file that holds it."""
    if env.get(name):
        return env[name]
    path = env.get(name + "_FILE")
    if path:
        p = pathlib.Path(path)
        if not p.exists():
            raise SetupError("%s_FILE points at %s, which does not exist" % (name, path))
        return p.read_text(encoding="utf-8").strip()
    return ""


def game_from(env):
    pw = secret(env, "COPILOT_RCON_PASSWORD")
    if not pw:
        raise SetupError("the game's RCON password is not set: put COPILOT_RCON_PASSWORD (or COPILOT_RCON_PASSWORD_FILE) in copilot.env. "
                         "It is the password the game server was started with (--rcon-password).")
    return Game(env.get("COPILOT_RCON_HOST", "127.0.0.1"), int(env.get("COPILOT_RCON_PORT", "27015")), pw)


def source_of(env):
    """Which one source is configured. COPILOT_PROVIDER is the older name for the same setting."""
    kind = (env.get("COPILOT_SOURCE") or env.get("COPILOT_PROVIDER") or "").strip().lower()
    if not kind:
        raise SetupError("no AI source is set: put COPILOT_SOURCE in copilot.env. It is one of: %s." % ", ".join(SOURCES))
    if kind not in SOURCES:
        raise SetupError("COPILOT_SOURCE is '%s'; it must be one of: %s" % (kind, ", ".join(SOURCES)))
    return kind


def agent_from(env, game, tools, log_path, max_steps=12):
    """The one thing that does the thinking, built from the one configured source."""
    kind = source_of(env)
    url = env.get("COPILOT_URL") or env.get("COPILOT_BASE_URL")
    if kind == "purple":
        if not env.get("COPILOT_WORKSPACE"):
            raise SetupError("purple Skippy needs a workspace: put COPILOT_WORKSPACE in copilot.env (the id of a project in purple's registry)")
        purple = Purple(url or PURPLE_URL, secret(env, "COPILOT_KEY"), env["COPILOT_WORKSPACE"])
        return PurpleAgent(game, purple, Toolbox(game, tools, log_path))
    if kind == "anthropic":
        if not url:
            raise SetupError("the anthropic source needs COPILOT_URL: the server's address, such as http://skippy-core:11434")
        if not env.get("COPILOT_MODEL"):
            raise SetupError("the anthropic source needs COPILOT_MODEL: the name of the model on that server")
        model = make("anthropic", env["COPILOT_MODEL"], url, secret(env, "COPILOT_KEY"))
    elif kind == "openai":
        if not url:
            raise SetupError("the openai source needs COPILOT_URL: the API's base address, such as http://localhost:1234/v1")
        if not env.get("COPILOT_MODEL"):
            raise SetupError("the openai source needs COPILOT_MODEL: the name of the model on that server")
        model = make("openai", env["COPILOT_MODEL"], url, secret(env, "COPILOT_KEY") or env.get("COPILOT_API_KEY", ""))
    else:
        model = make("ollama", env.get("COPILOT_MODEL", "qwen3:8b"), url, "", int(env.get("COPILOT_NUM_CTX", "16384")))
    return Agent(game, model, log_path, max_steps=max_steps, local=tools)


def voice_door(env, out=print):
    """The voice door, listening, or None when it is switched off or its port is taken (the bridge still runs)."""
    port = env.get("COPILOT_VOICE_PORT", str(VOICE_PORT)).strip().lower()
    if port == "off":
        return None
    try:
        door = VoiceDoor(port=int(port))
        out("voice door: %s (spoken lines in at /hear, Skippy's words out at /said)" % door.serve(), flush=True)
        return door
    except (ValueError, OSError) as e:
        out("no voice door: port %s could not be opened (%s). Typing in the game still works." % (port, e), flush=True)
        return None


def main():
    try:
        env = settings()
    except SetupError as e:
        print("Skippy cannot start: %s" % e)
        sys.exit(2)
    if "--check" in sys.argv:
        from .check import run_check
        sys.exit(0 if run_check(env) else 1)
    try:
        game = game_from(env)
        door = voice_door(env)
        if door:
            game = door.wrap(game)
        logs = pathlib.Path(env.get("COPILOT_LOG_DIR", "runs"))
        logs.mkdir(exist_ok=True)
        tools = LocalTools(game, plan_store=logs / "plans.json")
        agent = agent_from(env, game, tools, logs / (time.strftime("%Y%m%d-%H%M%S") + ".jsonl"))
    except (SetupError, SourceError, RuntimeError) as e:
        print("Skippy cannot start: %s" % e)
        print("Run  python -m copilot --check  to go through the setup step by step.")
        sys.exit(2)
    if "--ask" in sys.argv:
        answer, outcome, stats = agent.handle(sys.argv[sys.argv.index("--ask") + 1], light=False)
        print(answer or "(no answer: %s)" % outcome)
        print(stats)
        return
    purple_url = env.get("COPILOT_PURPLE_URL", PURPLE_URL)
    helper = None if purple_url.lower() == "off" else PurpleClient(purple_url, secret(env, "COPILOT_PURPLE_KEY"))
    bridge = Bridge(game, agent, tools, stall_hours=float(env.get("COPILOT_STALL_HOURS", "2")), goal_pause=float(env.get("COPILOT_GOAL_PAUSE", "20")),
                    out=lambda *a: print(*a, flush=True), voice=door, purple=helper, purple_project=env.get("COPILOT_PURPLE_PROJECT", "f-ai-factorio"))
    print("listening: %s, %d tools" % (agent.model.model, len(agent.tools)), flush=True)
    while True:
        bridge.step()
        time.sleep(2)


if __name__ == "__main__":
    main()
