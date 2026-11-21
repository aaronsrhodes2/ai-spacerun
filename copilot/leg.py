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


def run(agent, prompts, out=print, game=None, folder=None, logs=None):
    """Ask each prompt in turn. Returns one row per prompt: the prompt, the answer, the outcome and the counts.
    With a game and a folder, each turn is typed into the Skippy panel and answered there, as the player would see it,
    and gets a picture of where it worked (turn-NN.png); `logs` gives the log files the turn's tool calls go to."""
    rows = []
    for i, prompt in enumerate(prompts, 1):
        if game is not None:
            game.call("panel_type", {"text": prompt})        # shows in the panel; no player in the game is fine
        started = time.time()
        answer, outcome, stats = agent.handle(prompt, "leg", light=False)
        if game is not None and answer:
            game.call("say", {"text": answer})
        rows.append({"prompt": prompt, "answer": answer, "outcome": outcome, "calls": stats.get("calls", 0), "misses": stats.get("misses", 0),
                     "seconds": stats.get("seconds", 0)})
        if game is not None and folder is not None:
            rows[-1]["picture"] = snap(game, folder, i, prompt, logs if logs is not None else [], started)
        out("%2d. %s" % (i, prompt))
        out("    -> %s" % (answer or "(no answer: %s)" % outcome))
        out("    %d tool calls, %d refused, %s s" % (rows[-1]["calls"], rows[-1]["misses"], rows[-1]["seconds"]))
    return rows


def snap(game, folder, i, prompt, logs, started):
    """The picture after turn i, centred where the turn's tool calls last pointed, else on the first spider, else on 0,0.
    Returns its file name, or None."""
    from . import picture
    spot = picture.where(logs, started, time.time())
    if spot is None:
        r = game.call("spiders")
        found = (r.get("result") or {}).get("spiders") if r.get("ok") else None
        spot = (found[0]["x"], found[0]["y"], found[0].get("surface")) if found else (0, 0, None)
    img = picture.draw(game, spot[0], spot[1], spot[2], title="%d. %s" % (i, prompt))
    if img is None:
        return None
    name = "turn-%02d.png" % i
    img.save(pathlib.Path(folder) / name)
    return name


def main(argv):
    from .__main__ import agent_from, game_from, settings
    from .tools import LocalTools
    if len(argv) < 2:
        print(__doc__)
        return 2
    try:                                            # found live 2026-11-20: a Windows console's cp1252 killed the leg on an arrow in an answer
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    env = settings()
    prompts = prompts_of(pathlib.Path(argv[1]).read_text(encoding="utf-8"))
    game = game_from(env)
    logs = pathlib.Path(env.get("COPILOT_LOG_DIR", "runs"))
    logs.mkdir(exist_ok=True)
    log = logs / ("leg-" + time.strftime("%Y%m%d-%H%M%S") + ".jsonl")
    agent = agent_from(env, game, LocalTools(game), log, max_steps=int(env.get("COPILOT_MAX_STEPS", "16")))   # the bridge's one source
    print("leg: %d prompts, model %s, %d tools" % (len(prompts), agent.model.model, len(agent.tools)), flush=True)
    began = time.time()

    def turn_logs():                                    # the bridge's log, and the MCP server's that purple's calls go through
        found = [log] + [p for d in {logs, pathlib.Path("runs")} for p in d.glob("mcp-*.jsonl") if p.stat().st_mtime >= began - 5]
        return [str(p) for p in found]

    class Logs(list):                                   # read afresh each turn: purple's MCP log may start mid-leg
        def __iter__(self):
            return iter(turn_logs())

    rows = run(agent, prompts, out=lambda s: print(s, flush=True), game=game, folder=logs, logs=Logs())
    from .picture import page
    (logs / "report.html").write_text(page(rows, "Leg %s: %s" % (log.stem, argv[1])), encoding="utf-8")
    print("page: %s" % (logs / "report.html"), flush=True)
    s = score(read(log))
    print()
    print(line(log.name, s))
    for m in s["miss_list"]:
        print("   refused:", m["name"], m["args"], "->", m["error"])
    return 0 if s["clean"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
