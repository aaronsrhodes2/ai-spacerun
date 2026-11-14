"""Standing goals: something the player asks for once and the assistant keeps working toward on its own, turn after turn,
until it is reached or the player says stop. This is what lets a whole game be played in a handful of prompts, and what a
target such as "1,000 science a minute of each science" needs.

Four kinds:
  win         play to the win (the edge of the solar system)
  place       finish everything the list holds for one place: "solve Nauvis", "solve Vulcanus", "the first platform"
  milestone   reach one milestone of the list, by its id
  science     make at least N of every researched science pack a minute
  busy        have at least N percent of the machines working, averaged over the last minutes ("everything moving")

A goal knows whether it is reached, from facts the mod reports, and what to tell the model to do next."""
from . import milestones as ms


class GoalError(Exception):
    pass


class Goal:
    def __init__(self, kind, value=None, said=""):
        if kind not in ("win", "place", "milestone", "science", "busy"):
            raise GoalError("a goal is 'win', 'place', 'milestone', 'science' or 'busy'")
        if kind == "busy":
            try:
                value = float(value if value is not None else 95)
            except (TypeError, ValueError):
                raise GoalError("a busy goal needs a percentage of machines working, such as 95")
            if not 1 <= value <= 100:
                raise GoalError("a busy goal needs a percentage between 1 and 100")
        if kind == "place":
            value = str(value or "").strip().lower()
            if not ms.of_place(value):
                raise GoalError("there is no place '%s'; places are: %s" % (value, ", ".join(ms.PLACES)))
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
        if self.kind == "place":
            names = {"space": "get the first platform working", "edge": "reach the edge of the solar system", "beyond": "make promethium science"}
            return names.get(self.value) or "solve %s" % self.value.capitalize()
        if self.kind == "milestone":
            title = next(m["title"] for m in ms.MILESTONES if m["id"] == self.value)
            return "reach the milestone: %s" % title
        if self.kind == "busy":
            return "keep %g%% of the machines working" % self.value
        return "make %g of every science pack a minute" % self.value

    def needs_science(self):
        return self.kind == "science"

    def measure(self):
        """The mod tool and arguments that measure this goal, or None when the milestone facts are enough."""
        if self.kind == "science":
            return "science", {"target": self.value}
        if self.kind == "busy":
            return "utilisation", {}
        return None

    def reached(self, facts, science=None):
        """(reached, one line on where things stand)."""
        if self.kind == "win":
            state = ms.summary(facts)
            return bool(facts.get("won")), "%d of %d milestones done" % (state["done"], state["of"])
        if self.kind == "place":
            mine = ms.of_place(self.value)
            left = [m for m in mine if ms.missing(m["test"], facts)]
            return not left, "%d of %d steps done%s" % (len(mine) - len(left), len(mine), (", next: " + left[0]["title"]) if left else "")
        if self.kind == "milestone":
            m = next(m for m in ms.MILESTONES if m["id"] == self.value)
            lacks = ms.missing(m["test"], facts)
            return not lacks, ("done" if not lacks else "still needs: " + "; ".join(lacks))
        if self.kind == "busy":
            u = science or {}
            if not u.get("machines"):
                return False, "there are no machines yet"
            lately = u.get("percent_lately")
            now = u.get("percent_now") or 0
            seen = lately if lately is not None else now
            return seen >= self.value, "%g%% of %d machines working%s" % (seen, u["machines"], "" if lately is not None else " (right now; no average yet)")
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
        if self.kind == "busy":
            idle = (science or {}).get("idle_groups") or []
            if idle:
                lines.append("Idle, largest first: " + "; ".join("%d of %d %s%s (%s)" % (g.get("idle"), g.get("of"), g.get("machine"),
                             (" making " + g["recipe"]) if g.get("recipe") else "", g.get("why") or g.get("mostly")) for g in idle[:5]) + ".")
            lines.append("Balance it: the game has no dial for a machine's effort. Use plan_production for the exact machine counts; where machines "
                         "are starved, supply more or run fewer; where they are backed up, add what uses the product or run fewer.")
        elif self.kind == "science":
            short = (science or {}).get("short") or []
            if short:
                lines.append("Packs that fall short, worst first: " + ", ".join("%s (short by %g a minute)" % (x["pack"], x["short_by"]) for x in short[:6]) + ".")
            state = ms.summary(facts)
            if state["next"] and not facts.get("won"):
                lines.append("Science you cannot make yet needs research first; the next milestone is: %s." % state["next"][0]["goal"])
        else:
            state = ms.summary(facts, ms.of_place(self.value)) if self.kind == "place" else ms.summary(facts)
            if state["next"]:
                n = state["next"][0]
                lines.append("The next milestone is: %s. It still needs: %s. Hint: %s." % (n["goal"], "; ".join(n["still_needs"]), n["hint"]))
                if self.kind == "place":                 # a step that belongs to an earlier place may have to come first
                    earlier = ms.summary(facts)
                    if earlier["next"] and earlier["next"][0]["id"] not in [m["id"] for m in ms.of_place(self.value)]:
                        lines.append("An earlier step is not done yet and may be needed first: %s." % earlier["next"][0]["goal"])
        lines.append("Do the one most useful thing toward it now, using your tools: find what limits progress (alerts, bottlenecks, "
                     "what the next step needs), then plan it, dry-run it and build it. Then say in one or two sentences what you did, "
                     "honestly: if something failed or is not working yet, say so. "
                     "If you cannot go on without the player, say exactly what you need and begin your answer with the word BLOCKED.")
        return "\n".join(lines)
