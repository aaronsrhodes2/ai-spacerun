"""Standing goals: something the player asks for once and the assistant keeps working toward on its own, turn after turn,
until it is reached or the player says stop. This is what lets a whole game be played in a handful of prompts, and what a
target such as "1,000 science a minute of each science" needs.

Three kinds:
  win         play to the win (the edge of the solar system)
  milestone   reach one milestone of the list, by its id
  science     make at least N of every researched science pack a minute

A goal knows whether it is reached, from facts the mod reports, and what to tell the model to do next."""
from . import milestones as ms


class GoalError(Exception):
    pass


class Goal:
    def __init__(self, kind, value=None, said=""):
        if kind not in ("win", "milestone", "science"):
            raise GoalError("a goal is 'win', 'milestone' or 'science'")
        if kind == "milestone":
            ids = [m["id"] for m in ms.MILESTONES]
            if value not in ids:
                raise GoalError("there is no milestone '%s'; milestones are: %s" % (value, ", ".join(ids)))
        if kind == "science":
            try:
                value = float(value)
            except (TypeError, ValueError):
                raise GoalError("a science goal needs a number of packs a minute")
            if value <= 0:
                raise GoalError("a science goal needs a number above zero")
        self.kind, self.value, self.said = kind, value, said
        self.turns = 0                       # turns the assistant has taken on its own toward this goal
        self.idle_turns = 0                  # of those, how many in a row did nothing in the game

    def describe(self):
        if self.kind == "win":
            return "win the game"
        if self.kind == "milestone":
            title = next(m["title"] for m in ms.MILESTONES if m["id"] == self.value)
            return "reach the milestone: %s" % title
        return "make %g of every science pack a minute" % self.value

    def needs_science(self):
        return self.kind == "science"

    def reached(self, facts, science=None):
        """(reached, one line on where things stand)."""
        if self.kind == "win":
            state = ms.summary(facts)
            return bool(facts.get("won")), "%d of %d milestones done" % (state["done"], state["of"])
        if self.kind == "milestone":
            m = next(m for m in ms.MILESTONES if m["id"] == self.value)
            lacks = ms.missing(m["test"], facts)
            return not lacks, ("done" if not lacks else "still needs: " + "; ".join(lacks))
        s = science or {}
        spm = s.get("science_per_minute") or 0
        short = s.get("short") or []
        ok = bool(s.get("reached")) if "reached" in s and s["reached"] is not None else (spm >= self.value and not short)
        where = "%g a minute now (slowest: %s)" % (spm, s.get("slowest_pack") or "none made yet")
        return ok, where

    def prompt(self, facts, science=None):
        """What the model is told at the start of a turn it takes on its own."""
        _, where = self.reached(facts, science)
        lines = ["You are working on a standing goal the player gave you: %s. Nobody has typed anything; carry on by yourself." % self.describe(),
                 "Where it stands: %s." % where]
        if self.kind == "science":
            short = (science or {}).get("short") or []
            if short:
                lines.append("Packs that fall short, worst first: " + ", ".join("%s (short by %g a minute)" % (x["pack"], x["short_by"]) for x in short[:6]) + ".")
            state = ms.summary(facts)
            if state["next"] and not facts.get("won"):
                lines.append("Science you cannot make yet needs research first; the next milestone is: %s." % state["next"][0]["goal"])
        else:
            state = ms.summary(facts)
            if state["next"]:
                n = state["next"][0]
                lines.append("The next milestone is: %s. It still needs: %s. Hint: %s." % (n["goal"], "; ".join(n["still_needs"]), n["hint"]))
        lines.append("Do the one most useful thing toward it now, using your tools: find what limits progress (alerts, bottlenecks, "
                     "what the next step needs), then plan it, dry-run it and build it. Then say in one or two sentences what you did. "
                     "If you cannot go on without the player, say exactly what you need and begin your answer with the word BLOCKED.")
        return "\n".join(lines)
