"""Run the bridge:
    python -m copilot                 listen to the game chat and answer
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
"""
import os
import pathlib
import sys
import time

from .agent import Agent
from .game import Game
from .milestones import Watch
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


def say(game, text):
    for i in range(0, len(text), 380):                  # a chat line is short; long answers go out in pieces
        game.call("say", {"text": text[i:i + 380]})


def news_prompt(ev):
    return ("News from the game: the technology '%s' has just been researched. It unlocks these recipes: %s. Design note: %s\n"
            "If this makes a worthwhile improvement to the factory possible, look at the factory with your tools and suggest "
            "the one most useful change in at most two sentences, starting with what was unlocked. If nothing is worth saying, "
            "answer with the single word: nothing."
            % (ev.get("technology"), ", ".join(ev.get("unlocks_recipes") or []) or "none", ev.get("design_note") or "none written"))


def alert_prompt(new, alert_text):
    kinds = ", ".join("%s on %s" % (k, s) for s, k in sorted(new))
    return ("News from the game: a new alert has appeared (%s). %s "
            "Find out what is behind it with your tools and tell the player in at most two sentences what is wrong and the one thing "
            "you suggest doing about it. If it needs no action, answer with the single word: nothing." % (kinds, alert_text))


class AlertWatch:
    """Remembers which alert kinds have been raised with the player, so each is brought up once, and again only after it
    has gone away and come back."""

    def __init__(self):
        self.raised = set()

    def new(self, current):
        fresh = current - self.raised
        self.raised = (self.raised & current) | fresh           # forget kinds that have cleared
        return fresh


def main():
    env = settings()
    pw = env.get("COPILOT_RCON_PASSWORD") or pathlib.Path(env["COPILOT_RCON_PASSWORD_FILE"]).read_text().strip()
    game = Game(env.get("COPILOT_RCON_HOST", "127.0.0.1"), int(env.get("COPILOT_RCON_PORT", "27015")), pw)
    model = make(env.get("COPILOT_PROVIDER", "ollama"), env.get("COPILOT_MODEL", "qwen3:8b"), env.get("COPILOT_BASE_URL"),
                 env.get("COPILOT_API_KEY", ""), int(env.get("COPILOT_NUM_CTX", "16384")))
    logs = pathlib.Path(env.get("COPILOT_LOG_DIR", "runs"))
    logs.mkdir(exist_ok=True)
    agent = Agent(game, model, logs / (time.strftime("%Y%m%d-%H%M%S") + ".jsonl"), local=LocalTools(game))
    if "--ask" in sys.argv:
        answer, outcome, stats = agent.handle(sys.argv[sys.argv.index("--ask") + 1], light=False)
        print(answer or "(no answer: %s)" % outcome)
        print(stats)
        return
    # start from now, not from lines and news that were there before the bridge came up
    chat_at = (game.call("chat_read", {"after": 10 ** 9}).get("result") or {}).get("last_id", 0)
    news_at = (game.call("events_read", {"after": 10 ** 9}).get("result") or {}).get("last_id", 0)
    tools = agent.local
    stall, last_done, checked_at = Watch(float(env.get("COPILOT_STALL_HOURS", "2"))), -1, 0.0
    watch = AlertWatch()
    watch.new(agent.alerts()[1])                                  # alerts already showing when the bridge starts are not news
    print("listening: model %s, %d tools" % (model.model, len(agent.tools)), flush=True)
    while True:
        r = game.call("chat_read", {"after": chat_at})
        for line in (r.get("result") or {}).get("lines") or []:
            chat_at = line["id"]
            answer, outcome, stats = agent.handle(line["text"], line.get("player", "player"))
            say(game, answer or "I could not finish that (%s)." % outcome)
            print(line["text"], "->", outcome, stats, flush=True)
        r = game.call("events_read", {"after": news_at})
        for ev in (r.get("result") or {}).get("events") or []:
            news_at = ev["id"]
            if ev.get("kind") == "research_finished" and (ev.get("design_note") or ev.get("unlocks_recipes")):
                answer, outcome, stats = agent.handle(news_prompt(ev), "game")
                if answer and answer.strip().lower().rstrip(".") != "nothing":
                    say(game, answer)
                print("news", ev.get("technology"), "->", outcome, stats, flush=True)
        alert_text, kinds = agent.alerts()
        fresh = watch.new(kinds)
        if fresh:
            answer, outcome, stats = agent.handle(alert_prompt(fresh, alert_text), "game")
            if answer and answer.strip().lower().rstrip(".") != "nothing":
                say(game, answer)
            print("alert", sorted(fresh), "->", outcome, stats, flush=True)
        if time.time() - checked_at > 60:                 # once a minute: how far is the game, and is it moving?
            checked_at = time.time()
            try:
                facts = tools.facts()
                done = sum(1 for m in __import__("copilot.milestones", fromlist=["evaluate"]).evaluate(facts) if not m["missing"])
                if done != last_done:
                    last_done = done
                    agent.log(event="milestone", done=done, hours_played=facts.get("hours_played"))
                said = stall.check(facts)
                if said:
                    agent.log(event="stall", text=said, hours_played=facts.get("hours_played"))
                    print(said, flush=True)
            except Exception as e:                        # a missing tool or a dropped connection must not stop the loop
                print("progress check failed:", str(e)[:120], flush=True)
        time.sleep(2)


if __name__ == "__main__":
    main()
