"""Skippy's bridge: it connects ONE AI source to the game.

    python -m copilot --check         go through the setup step by step and say plainly what works and what does not
    python -m copilot                 listen to the game chat and answer; keep working toward a standing goal
    python -m copilot --ask "what do I need for green circuits?"      one question, the answer printed

Settings: a file named copilot.env next to this package (copy copilot.env.example), or the same names in the environment.

  The game
    COPILOT_RCON_HOST          default 127.0.0.1
    COPILOT_RCON_PORT          default 27015
    COPILOT_RCON_PASSWORD      or COPILOT_RCON_PASSWORD_FILE (a file holding it)
    COPILOT_GAME               live (default: the address above) or test (the test server, whatever the address says);
                               the map's seed is checked, so one game is never taken for the other (copilot/games.py)

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
    COPILOT_TOOL_GROUPS        on (default): the model carries the core tools and opens groups as needed; off: every tool
    COPILOT_LOG_DIR            where run logs go, default ./runs
    COPILOT_STALL_HOURS        game hours without progress before a stall is logged, default 2
    COPILOT_GOAL_PAUSE         seconds between the turns the assistant takes on its own toward a goal, default 20
"""
import os
import pathlib
import sys
import time

from . import games
from .agent import Agent
from .game import Game
from .loop import AlertWatch, Bridge, alert_prompt, news_prompt, say          # noqa: F401  (re-exported for callers and tests)
from .models import make
from .purple import Purple, PurpleAgent, SourceError
from .purple_client import DEFAULT_URL as PURPLE_URL, PurpleClient
from .toolbox import Toolbox
from .tools import LocalTools
from .tiered import TieredAgent
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
    return games.apply(resolve(env))                    # COPILOT_GAME=test: the test server, whatever copilot.env says


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
        return PurpleAgent(game, purple, Toolbox(game, tools, log_path), which=games.name_of(env))   # purple is told which game, and its door
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
    return Agent(game, model, log_path, max_steps=max_steps, local=tools, groups=groups_on(env))


def quick_from(env, game, tools, log_path):
    """The quick tier: a plain model for short questions and small orders, or None when COPILOT_QUICK_URL is not set (see tiered.py)."""
    url = env.get("COPILOT_QUICK_URL")
    if not url:
        return None
    kind = (env.get("COPILOT_QUICK_SOURCE") or "anthropic").strip().lower()
    if kind not in ("anthropic", "openai", "ollama"):
        raise SetupError("COPILOT_QUICK_SOURCE is '%s'; it must be anthropic, openai or ollama" % kind)
    if not env.get("COPILOT_QUICK_MODEL"):
        raise SetupError("the quick tier needs COPILOT_QUICK_MODEL: the name of the model on %s" % url)
    model = make(kind, env["COPILOT_QUICK_MODEL"], url, secret(env, "COPILOT_QUICK_KEY"))
    return Agent(game, model, log_path, max_steps=int(env.get("COPILOT_QUICK_STEPS", "6")), local=tools, groups=groups_on(env))


def groups_on(env):
    return (env.get("COPILOT_TOOL_GROUPS") or "on").strip().lower() not in ("off", "no", "false", "0")


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


def from_game(env, game):
    """The AI address and model the player set in the game (Mod settings > Map), over copilot.env's own source (the
    Captain, 2026-11-21: "a configurable ollama url:port, and connect automatically"). Returns (env, what was read): with
    no address set in the game, env is unchanged."""
    r = game.call("bridge_settings")
    got = (r.get("result") or {}) if r.get("ok") else {}
    url, model = (got.get("ai_url") or "").strip(), (got.get("ai_model") or "").strip()
    if not url:
        return env, None
    env = dict(env)
    env["COPILOT_SOURCE"] = "ollama"
    env["COPILOT_URL"] = url if "://" in url else "http://" + url
    env["COPILOT_MODEL"] = model or "qwen3:8b"
    env["COPILOT_QUICK_URL"] = ""                       # one source: the one the player chose
    return env, (url, model)


SETTINGS_EVERY = 30                                       # steps between looks at the game's AI setting (about a minute)


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
        which = games.name_of(env)
        ok, why = games.check(game, which)
        if not ok:
            raise SetupError(why)
        print("game: %s (%s)" % (which, why), flush=True)
        env, chosen = from_game(env, game)
        if chosen:
            print("the AI set in the game: %s, model %s" % (env["COPILOT_URL"], env["COPILOT_MODEL"]), flush=True)
        door = voice_door(env)
        if door:
            game = door.wrap(game)
        logs = pathlib.Path(env.get("COPILOT_LOG_DIR", "runs"))
        logs.mkdir(exist_ok=True)
        tools = LocalTools(game, plan_store=games.plan_file(logs, which))         # plans per game, never shared
        stamp = time.strftime("%Y%m%d-%H%M%S")
        agent = agent_from(env, game, tools, logs / (stamp + ".jsonl"))
        quick = quick_from(env, game, tools, logs / (stamp + "-quick.jsonl"))
        if quick:
            agent = TieredAgent(quick, agent)
    except (SetupError, SourceError, RuntimeError, games.WrongGame) as e:
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
    steps = 0
    while True:
        bridge.step()
        steps += 1
        if steps % SETTINGS_EVERY == 0 and from_game(settings(), game)[1] != chosen:
            print("the AI setting in the game changed: starting again with it", flush=True)
            sys.exit(3)                                   # scripts/live_bridge.sh starts it again within seconds
        time.sleep(2)


if __name__ == "__main__":
    main()
