"""Run a fixed list of prompts through the assistant, one after another, and score the run. This is how a leg of skills
testing is run: the same prompts every time, so one night's score can be set beside the next.

    python -m copilot.leg copilot/legs/first.txt

The prompts file has one prompt a line; blank lines and lines starting with # are skipped. Settings are the bridge's
(see `python -m copilot`). Each answer is printed; the log goes to COPILOT_LOG_DIR and is scored at the end."""
import pathlib
import sys
import time

from .score import line, read, score


def prompts_of(text):
    return [l.strip() for l in text.splitlines() if l.strip() and not l.strip().startswith("#")]


def run(agent, prompts, out=print):
    """Ask each prompt in turn. Returns one row per prompt: the prompt, the answer, the outcome and the counts."""
    rows = []
    for i, prompt in enumerate(prompts, 1):
        answer, outcome, stats = agent.handle(prompt, "leg", light=False)
        rows.append({"prompt": prompt, "answer": answer, "outcome": outcome, "calls": stats.get("calls", 0), "misses": stats.get("misses", 0),
                     "seconds": stats.get("seconds", 0)})
        out("%2d. %s" % (i, prompt))
        out("    -> %s" % (answer or "(no answer: %s)" % outcome))
        out("    %d tool calls, %d refused, %s s" % (rows[-1]["calls"], rows[-1]["misses"], rows[-1]["seconds"]))
    return rows


def main(argv):
    from .__main__ import settings
    from .agent import Agent
    from .game import Game
    from .models import make
    from .tools import LocalTools
    if len(argv) < 2:
        print(__doc__)
        return 2
    env = settings()
    prompts = prompts_of(pathlib.Path(argv[1]).read_text(encoding="utf-8"))
    pw = env.get("COPILOT_RCON_PASSWORD") or pathlib.Path(env["COPILOT_RCON_PASSWORD_FILE"]).read_text().strip()
    game = Game(env.get("COPILOT_RCON_HOST", "127.0.0.1"), int(env.get("COPILOT_RCON_PORT", "27015")), pw)
    model = make(env.get("COPILOT_PROVIDER", "ollama"), env.get("COPILOT_MODEL", "qwen3:8b"), env.get("COPILOT_BASE_URL"),
                 env.get("COPILOT_API_KEY", ""), int(env.get("COPILOT_NUM_CTX", "16384")))
    logs = pathlib.Path(env.get("COPILOT_LOG_DIR", "runs"))
    logs.mkdir(exist_ok=True)
    log = logs / ("leg-" + time.strftime("%Y%m%d-%H%M%S") + ".jsonl")
    agent = Agent(game, model, log, local=LocalTools(game), max_steps=int(env.get("COPILOT_MAX_STEPS", "16")))
    print("leg: %d prompts, model %s, %d tools" % (len(prompts), model.model, len(agent.tools)), flush=True)
    run(agent, prompts, out=lambda s: print(s, flush=True))
    s = score(read(log))
    print()
    print(line(log.name, s))
    for m in s["miss_list"]:
        print("   refused:", m["name"], m["args"], "->", m["error"])
    return 0 if s["clean"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
