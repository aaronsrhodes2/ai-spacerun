"""The bridge's loop, one step at a time so it can be tested without a game or a model. Each step:
  1. answers what players typed in the game chat
  2. brings up finished research, with its design note
  3. brings up alerts that are new
  4. once a minute, notes milestones done and whether the run has stalled
  5. if a standing goal is set and nobody is waiting, takes one turn toward it on its own
  0. passes on what the player said aloud (the voice door), so it is answered like a typed line
  6. passes a task typed as /purple to purple Skippy and, between its other work, brings back what purple says

Purple's work is a job that takes seconds to minutes. The loop never waits on it: it starts the run, remembers it, and
asks for news no more often than every few seconds.

A turn the assistant takes on its own is not a prompt: only what a player types counts as one."""
import time

from . import milestones as ms
from .milestones import Watch
from .purple_client import MIN_POLL, PurpleError

NOTHING = "nothing"


def say(game, text, voice=None):
    for i in range(0, len(text), 380):                  # a chat line is short; long answers go out in pieces
        game.call("say", dict({"text": text[i:i + 380]}, **({"as": voice} if voice else {})))


PURPLE_TASK = chr(10).join([
    "This request comes from a player inside a running Factorio game, typed as /purple and passed on by the Skippy bridge in this repository. Rules for this task:",
    "- You may change only this repository's mod (mods/skippy-copilot), its bridge (copilot/) and their tests (tests/copilot_tests). Touch nothing else, in this repository or outside it.",
    "- The player is in the middle of a game. Do not restart, reload or stop the game server, and do not start a test server or a model on this computer, unless the request asks for exactly that.",
    "- You cannot see or change the game itself from here; if the request needs that, say so.",
    "- Answer in a few short plain sentences: they are shown in the game's chat. Say honestly what you did and what you did not.",
    "",
    "The request, from %s: %s"])
PURPLE_STOP = ("stop", "cancel")
PURPLE_SAY = 760                                        # of one piece of purple's words, in the chat


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


def research_prompt():
    return ("News from the game: research has stopped because nothing is queued. This is your moment to come to the player. "
            "Call research_options, pick the ONE technology that helps most right now (one a milestone needs, if there is one), and "
            "tell the player in at most three sentences: what you suggest researching, what it unlocks, and what that will let us do "
            "next. End by asking whether to go ahead. Do not queue it yourself unless the player has told you to choose research on your own.")


def bottleneck_prompt(top, power):
    if power:
        return ("News from the game: %s. Tell the player in at most two sentences what is short of power and the one thing you suggest "
                "doing about it, after a look with your tools. Ask whether to go ahead before changing anything that works." % power)
    return ("News from the game: an obvious bottleneck. %d machines are %s (they make %s), around %s,%s. Find out with your tools why, "
            "then tell the player in at most two sentences what is wrong and the one thing you suggest doing about it. Ask whether to go "
            "ahead before changing anything that works. If it needs no action, answer with the single word: nothing."
            % (top.get("machines_waiting") or 0, top.get("problem"), ", ".join(top.get("those_machines_make") or []) or "nothing yet",
               top.get("centre_x"), top.get("centre_y")))


def is_nothing(answer):
    return not answer or answer.strip().lower().rstrip(".") == NOTHING


class AlertWatch:
    """Remembers which alert kinds have been raised with the player, so each is brought up once, and again only after it
    has gone away and come back."""

    def __init__(self):
        self.raised = set()

    def new(self, current):
        fresh = current - self.raised
        self.raised = (self.raised & current) | fresh           # forget kinds that have cleared
        return fresh


class Bridge:
    def __init__(self, game, agent, tools, clock=time.time, stall_hours=2.0, goal_pause=20.0, progress_every=60.0, max_idle_turns=3, out=print,
                 bottleneck_every=180.0, bottleneck_machines=5, purple=None, purple_project=None, purple_poll=3.0, purple_timeout=1800.0, voice=None):
        self.voice = voice                                      # the voice door, or None: lines heard outside the game
        self.purple, self.purple_project = purple, purple_project
        self.purple_poll, self.purple_timeout = max(purple_poll, MIN_POLL), purple_timeout
        self.purple_job = None                                  # the one run in flight: {task, next, at, started, who}
        self.purple_conv = None                                 # one conversation with purple for the whole session
        self.game, self.agent, self.tools, self.clock, self.out = game, agent, tools, clock, out
        self.goal_pause, self.progress_every, self.max_idle_turns = goal_pause, progress_every, max_idle_turns
        self.bottleneck_every, self.bottleneck_machines = bottleneck_every, bottleneck_machines
        self.bottlenecks = AlertWatch()                         # the same once-until-it-clears memory, for bottlenecks
        self.bottleneck_at = None
        # start from now, not from lines and news that were there before the bridge came up
        self.chat_at = (game.call("chat_read", {"after": 10 ** 9}).get("result") or {}).get("last_id", 0)
        self.news_at = (game.call("events_read", {"after": 10 ** 9}).get("result") or {}).get("last_id", 0)
        self.alerts = AlertWatch()
        self.alerts.new(agent.alerts()[1])                      # alerts already showing are not news
        self.stall = Watch(stall_hours)
        self.last_done = -1
        self.progress_at = None
        self.goal_at = None

    # ---- one step ----------------------------------------------------------------------------------------------------
    def step(self):
        self._heard()
        spoke = self._chat()
        self._news()
        self._new_alerts()
        self._bottlenecks()
        self._progress()
        self._purple()
        if not spoke:
            self._goal()

    def _heard(self):
        """What the player said aloud goes into the game as a line of theirs; the chat step then answers it."""
        if self.voice is None:
            return
        for line in self.voice.take():
            r = self.game.call("hear", dict({"text": line["text"]}, **({"player": line["who"]} if line.get("who") else {})))
            if not r.get("ok"):                                 # a game that cannot take it (an older mod): answer it directly
                answer, outcome, stats = self.agent.handle(line["text"], line.get("who") or "player")
                say(self.game, answer or "I could not finish that (%s)." % outcome)
                self.out("(voice)", line["text"], "->", outcome, stats)

    def _lines(self, result, key):
        got = (result.get("result") or {}).get(key)
        return got if isinstance(got, list) else []

    def _chat(self):
        lines = self._lines(self.game.call("chat_read", {"after": self.chat_at}), "lines")
        for line in lines:
            self.chat_at = line["id"]
            if line.get("to") == "purple":
                self._purple_request(line)
                continue
            answer, outcome, stats = self.agent.handle(line["text"], line.get("player", "player"))
            say(self.game, answer or "I could not finish that (%s)." % outcome)
            self.tools.goal_paused = False                      # the player has spoken: a goal that was stuck may go on
            self.out(line["text"], "->", outcome, stats)
        return any(line.get("to") != "purple" for line in lines)

    # ---- purple Skippy, for a task ------------------------------------------------------------------------------------
    def _purple_say(self, text):
        say(self.game, text[:PURPLE_SAY] + (" ..." if len(text) > PURPLE_SAY else ""), "purple")

    def _purple_request(self, line):
        text, who = (line.get("text") or "").strip(), line.get("player", "player")
        if self.purple is None:
            return self._purple_say("purple Skippy is not connected to this bridge.")
        if text.lower() in PURPLE_STOP:
            if not self.purple_job:
                return self._purple_say("nothing of mine is running.")
            stopped = self.purple.cancel(self.purple_job["task"])
            self.purple_job = None
            return self._purple_say("stopped." if stopped else "I could not reach the run to stop it; it may still be going.")
        if self.purple_job:
            return self._purple_say("still working on the last task. Type /purple stop to end it.")
        try:
            got = self.purple.ask(PURPLE_TASK % (who, text), self.purple_conv, self.purple_project, wait_s=0)
        except PurpleError as e:
            self.agent.log(event="purple", ok=False, error=str(e)[:300])
            return self._purple_say(str(e))
        if got.get("busy"):
            return self._purple_say("busy with another job right now. Ask again in a while.")
        self.purple_conv = got.get("conv") or self.purple_conv
        now = self.clock()
        self.purple_job = {"task": got.get("task"), "next": got.get("next") or 0, "at": now, "started": now, "who": who, "said": False}
        self.agent.log(event="purple", ok=True, task=got.get("task"), who=who, text=text)
        self._purple_news(got)

    def _purple(self):
        """Ask for news of the run in flight, no more often than every few seconds, without waiting for any."""
        job = self.purple_job
        if not job:
            return
        now = self.clock()
        if now - job["at"] < self.purple_poll:
            return
        job["at"] = now
        if now - job["started"] > self.purple_timeout:
            self.purple.cancel(job["task"])
            self.purple_job = None
            return self._purple_say("that took over %d minutes, so I stopped it." % (self.purple_timeout // 60))
        try:
            got = self.purple.result(job["task"], job["next"], wait_s=0)
        except PurpleError as e:
            job["errors"] = job.get("errors", 0) + 1
            if job["errors"] >= 5:                              # the door has gone: say so once and let go
                self.purple_job = None
                self._purple_say("I lost touch with the run: %s" % e)
            return
        job["errors"] = 0
        job["next"] = got.get("next") or job["next"]
        self._purple_news(got)

    def _purple_news(self, got):
        job = self.purple_job
        piece = (got.get("text") or "").strip()
        if piece:
            job["said"] = True
            self._purple_say(piece)
        if got.get("done"):
            failed = got.get("ok") is False
            if failed:
                self._purple_say("that did not finish: %s" % (got.get("error") or "no reason given"))
            elif not job["said"]:
                self._purple_say("done.")
            self.agent.log(event="purple_done", task=job["task"], ok=not failed, steps=got.get("steps"))
            self.out("purple", job["task"], "->", "failed" if failed else "done")
            self.purple_job = None

    def _news(self):
        for ev in self._lines(self.game.call("events_read", {"after": self.news_at}), "events"):
            self.news_at = ev["id"]
            if ev.get("kind") == "research_idle":
                answer, outcome, stats = self.agent.handle(research_prompt(), "game")
                if not is_nothing(answer):
                    say(self.game, answer)
                self.out("research stopped ->", outcome, stats)
            elif ev.get("kind") == "research_finished" and (ev.get("design_note") or ev.get("unlocks_recipes")):
                answer, outcome, stats = self.agent.handle(news_prompt(ev), "game")
                if not is_nothing(answer):
                    say(self.game, answer)
                self.out("news", ev.get("technology"), "->", outcome, stats)

    def _new_alerts(self):
        alert_text, kinds = self.agent.alerts()
        fresh = self.alerts.new(kinds)
        if fresh:
            answer, outcome, stats = self.agent.handle(alert_prompt(fresh, alert_text), "game")
            if not is_nothing(answer):
                say(self.game, answer)
            self.out("alert", sorted(fresh), "->", outcome, stats)

    def _bottlenecks(self):
        """Every few minutes: is there an obvious bottleneck the player has not been told about? Many machines waiting
        on one item, or machines without power. Each is brought up once, and again only after it has cleared."""
        now = self.clock()
        if self.bottleneck_at is not None and now - self.bottleneck_at < self.bottleneck_every:
            return
        self.bottleneck_at = now
        r = self.game.call("bottlenecks", {"top": 3})
        if not r.get("ok"):
            return
        result = r.get("result") or {}
        found = result.get("bottlenecks") if isinstance(result.get("bottlenecks"), list) else []
        power = result.get("power_first")
        obvious = [b for b in found if (b.get("machines_waiting") or 0) >= self.bottleneck_machines]
        current = {("bottleneck", b.get("problem")) for b in obvious}
        if power:
            current.add(("bottleneck", "power"))
        fresh = self.bottlenecks.new(current)
        if not fresh:
            return
        if ("bottleneck", "power") in fresh:
            prompt = bottleneck_prompt(None, power)
        else:
            prompt = bottleneck_prompt(next(b for b in obvious if ("bottleneck", b.get("problem")) in fresh), None)
        answer, outcome, stats = self.agent.handle(prompt, "game")
        if not is_nothing(answer):
            say(self.game, answer)
        self.out("bottleneck", sorted(k for _, k in fresh), "->", outcome, stats)

    def _progress(self):
        now = self.clock()
        if self.progress_at is not None and now - self.progress_at < self.progress_every:
            return
        self.progress_at = now
        try:
            facts = self.tools.facts()
        except Exception as e:                                  # a missing tool or a dropped connection must not stop the loop
            self.out("progress check failed:", str(e)[:120])
            return
        done = sum(1 for m in ms.evaluate(facts) if not m["missing"])
        if done != self.last_done:
            self.last_done = done
            self.agent.log(event="milestone", done=done, hours_played=facts.get("hours_played"))
        said = self.stall.check(facts)
        if said:
            self.agent.log(event="stall", text=said, hours_played=facts.get("hours_played"))
            self.out(said)

    def _goal(self):
        self.tools.sync_goal()                                  # the goal may have been set or dropped through another door
        goal = self.tools.goal
        if not goal or self.tools.goal_paused:
            return
        now = self.clock()
        if self.goal_at is not None and now - self.goal_at < self.goal_pause:
            return
        self.goal_at = now
        try:
            facts = self.tools.facts()
            science = None
            measure = goal.measure()
            if measure:
                r = self.game.call(measure[0], measure[1])
                science = r.get("result") if r.get("ok") else None
        except Exception as e:
            self.out("goal check failed:", str(e)[:120])
            return
        reached, where = goal.reached(facts, science)
        if reached:
            say(self.game, "Goal reached: %s (%s). It took %d turns of my own." % (goal.describe(), where, goal.turns))
            self.agent.log(event="goal_reached", goal=goal.describe(), turns=goal.turns, hours_played=facts.get("hours_played"))
            self.tools.goal = None
            self.tools._store_goal()
            self.game.call("set_state", {"state": "idle", "note": ""})
            return
        answer, outcome, stats = self.agent.handle(goal.prompt(facts, science), "goal")
        goal.turns += 1
        goal.idle_turns = goal.idle_turns + 1 if stats.get("calls", 0) == 0 else 0
        blocked = (answer or "").strip().upper().startswith("BLOCKED")
        if outcome != "answered" or blocked or goal.idle_turns >= self.max_idle_turns:
            why = answer if answer else "I could not go on (%s)." % outcome
            if goal.idle_turns >= self.max_idle_turns and not blocked and answer:
                why = "I have stopped working on the goal because I was not getting anywhere. Last thing I said: " + answer
            say(self.game, why)
            self.tools.goal_paused = True                       # wait for the player
            self.game.call("set_state", {"state": "blocked", "note": goal.describe()[:40]})
            self.agent.log(event="goal_blocked", goal=goal.describe(), turns=goal.turns)
        elif not is_nothing(answer):
            say(self.game, answer)
        self.out("goal turn", goal.turns, "->", outcome, stats)
