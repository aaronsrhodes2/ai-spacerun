"""Run the bridge:
    python -m copilot                 listen to the game chat and answer; keep working toward a standing goal
    python -m copilot --ask "what do I need for green circuits?"      one question, the answer printed

Settings come from the environment, or from a file named copilot.env next to this package (KEY=VALUE per line):
  COPILOT_RCON_HOST      default 127.0.0.1
  COPILOT_RCON_PORT      default 27015
  COPILOT_RCON_PASSWORD  or COPILOT_RCON_PASSWORD_FILE (a file holding it)
  COPILOT_PROVIDER       ollama (default) or openai (any server that speaks the OpenAI chat API)
  COPILOT_MODEL          default qwen3:8b
  COPILOT_BASE_URL       the model server; default http://localhost:11434 for ollama
  COPILOT_API_KEY        for a paid server; never needed for a local one
  COPILOT_NUM_CTX        context size asked of Ollama, default 16384
  COPILOT_LOG_DIR        where run logs go, default ./runs
  COPILOT_STALL_HOURS    game hours without progress before a stall is logged, default 2
  COPILOT_GOAL_PAUSE     seconds between the turns the assistant takes on its own toward a goal, default 20
"""
import os
import pathlib
import sys
import time

from .agent import Agent
from .game import Game
from .loop import AlertWatch, Bridge, alert_prompt, news_prompt, say          # noqa: F401  (re-exported for callers and tests)
from .models import make
from .tools import LocalTools

HERE = pathlib.Path(__file__).parent


def settings():
    env = dict(os.environ)
    f = HERE / "copilot.env"
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                env.setdefault(k.strip(), v.strip().strip('"'))
    return env


def main():
    env = settings()
    pw = env.get("COPILOT_RCON_PASSWORD") or pathlib.Path(env["COPILOT_RCON_PASSWORD_FILE"]).read_text().strip()
    game = Game(env.get("COPILOT_RCON_HOST", "127.0.0.1"), int(env.get("COPILOT_RCON_PORT", "27015")), pw)
    model = make(env.get("COPILOT_PROVIDER", "ollama"), env.get("COPILOT_MODEL", "qwen3:8b"), env.get("COPILOT_BASE_URL"),
                 env.get("COPILOT_API_KEY", ""), int(env.get("COPILOT_NUM_CTX", "16384")))
    logs = pathlib.Path(env.get("COPILOT_LOG_DIR", "runs"))
    logs.mkdir(exist_ok=True)
    tools = LocalTools(game)
    agent = Agent(game, model, logs / (time.strftime("%Y%m%d-%H%M%S") + ".jsonl"), local=tools)
    if "--ask" in sys.argv:
        answer, outcome, stats = agent.handle(sys.argv[sys.argv.index("--ask") + 1], light=False)
        print(answer or "(no answer: %s)" % outcome)
        print(stats)
        return
    bridge = Bridge(game, agent, tools, stall_hours=float(env.get("COPILOT_STALL_HOURS", "2")), goal_pause=float(env.get("COPILOT_GOAL_PAUSE", "20")),
                    out=lambda *a: print(*a, flush=True))
    print("listening: model %s, %d tools" % (model.model, len(agent.tools)), flush=True)
    while True:
        bridge.step()
        time.sleep(2)


if __name__ == "__main__":
    main()
