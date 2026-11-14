"""Skippy Copilot's bridge: it connects ONE AI source to the game.

    python -m copilot --check         go through the setup step by step and say plainly what works and what does not
    python -m copilot                 listen to the game chat and answer; keep working toward a standing goal
    python -m copilot --ask "what do I need for green circuits?"      one question, the answer printed

Settings: a file named copilot.env next to this package (copy copilot.env.example), or the same names in the environment.

  The game
    COPILOT_RCON_HOST          default 127.0.0.1
    COPILOT_RCON_PORT          default 27015
    COPILOT_RCON_PASSWORD      or COPILOT_RCON_PASSWORD_FILE (a file holding it)

  The AI: one source, one key
    COPILOT_SOURCE             purple   purple Skippy, the agent of the SkippyTel project, working in one workspace
                               openai   any server that speaks the OpenAI chat API (most hosted and local servers do)
                               ollama   a local Ollama server
    COPILOT_URL                where the source is. purple: SkippyTel's bridge, default http://localhost:9337
                               openai: the API's base, such as https://api.example.com/v1    ollama: default http://localhost:11434
    COPILOT_KEY                the source's key, or COPILOT_KEY_FILE (a file holding it). Not needed for a local Ollama.
    COPILOT_MODEL              openai and ollama only: the model's name. purple needs none.
    COPILOT_WORKSPACE          purple only: the id of the project (workspace) purple works in

  Optional
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
from .toolbox import Toolbox
from .tools import LocalTools

HERE = pathlib.Path(__file__).parent
SOURCES = ("purple", "openai", "ollama")


class SetupError(Exception):
    """Something in the settings is missing or wrong, said so a newcomer can fix it."""


def settings():
    env = dict(os.environ)
    f = HERE / "copilot.env"
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                env.setdefault(k.strip(), v.strip().strip('"'))
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
        raise SetupError("no AI source is set: put COPILOT_SOURCE in copilot.env. It is one of: purple, openai, ollama.")
    if kind not in SOURCES:
        raise SetupError("COPILOT_SOURCE is '%s'; it must be one of: %s" % (kind, ", ".join(SOURCES)))
    return kind


def agent_from(env, game, tools, log_path, max_steps=12):
    """The one thing that does the thinking, built from the one configured source."""
    kind = source_of(env)
    url = env.get("COPILOT_URL") or env.get("COPILOT_BASE_URL")
    if kind == "purple":
        key = secret(env, "COPILOT_KEY")
        if not key:
            raise SetupError("purple Skippy needs its bridge's key: put COPILOT_KEY (or COPILOT_KEY_FILE) in copilot.env")
        if not env.get("COPILOT_WORKSPACE"):
            raise SetupError("purple Skippy needs a workspace: put COPILOT_WORKSPACE in copilot.env (the id of a project in SkippyTel's registry)")
        purple = Purple(url or "http://localhost:9337", key, env["COPILOT_WORKSPACE"])
        return PurpleAgent(game, purple, Toolbox(game, tools, log_path))
    if kind == "openai":
        if not url:
            raise SetupError("the openai source needs COPILOT_URL: the API's base address, such as http://localhost:1234/v1")
        if not env.get("COPILOT_MODEL"):
            raise SetupError("the openai source needs COPILOT_MODEL: the name of the model on that server")
        model = make("openai", env["COPILOT_MODEL"], url, secret(env, "COPILOT_KEY") or env.get("COPILOT_API_KEY", ""))
    else:
        model = make("ollama", env.get("COPILOT_MODEL", "qwen3:8b"), url, "", int(env.get("COPILOT_NUM_CTX", "16384")))
    return Agent(game, model, log_path, max_steps=max_steps, local=tools)


def main():
    if "--check" in sys.argv:
        from .check import run_check
        sys.exit(0 if run_check(settings()) else 1)
    env = settings()
    try:
        game = game_from(env)
        logs = pathlib.Path(env.get("COPILOT_LOG_DIR", "runs"))
        logs.mkdir(exist_ok=True)
        tools = LocalTools(game, plan_store=logs / "plans.json")
        agent = agent_from(env, game, tools, logs / (time.strftime("%Y%m%d-%H%M%S") + ".jsonl"))
    except (SetupError, SourceError, RuntimeError) as e:
        print("Skippy Copilot cannot start: %s" % e)
        print("Run  python -m copilot --check  to go through the setup step by step.")
        sys.exit(2)
    if "--ask" in sys.argv:
        answer, outcome, stats = agent.handle(sys.argv[sys.argv.index("--ask") + 1], light=False)
        print(answer or "(no answer: %s)" % outcome)
        print(stats)
        return
    bridge = Bridge(game, agent, tools, stall_hours=float(env.get("COPILOT_STALL_HOURS", "2")), goal_pause=float(env.get("COPILOT_GOAL_PAUSE", "20")),
                    out=lambda *a: print(*a, flush=True))
    print("listening: %s, %d tools" % (agent.model.model, len(agent.tools)), flush=True)
    while True:
        bridge.step()
        time.sleep(2)


if __name__ == "__main__":
    main()
