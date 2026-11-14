"""Two speeds of thinking (the Captain, 2026-11-14: a snappy answer for simple things, the high-reasoning one for hard things).

Purple Skippy is the deep tier: an agent with a loop of its own, about six seconds a step. A plain model on SkippyCore (the
anthropic-format door, the always-loaded chat slot) is the quick tier: one or two tool calls in a few seconds. This agent stands
where either would stand and picks per request:

    quick   a short question or a small order from the player ("what is in my inventory?", "where am I", "how much copper")
    deep    anything that plans or builds, long requests, standing goals, news and alerts, and anything the player asks for
            by words ("think", "plan", "carefully")

If the quick tier cannot answer (the model is down, or it gave nothing), the request goes to the deep one, so a down chat slot
never leaves the player without an answer. Without COPILOT_QUICK_URL there is no quick tier and everything is deep."""
import re

DEEP = re.compile(
    r"\b(build|place|plan|design|set ?up|make|create|fix|repair|solve|automate|expand|scale|connect|research|travel|launch|rocket|train|"
    r"platform|take over|take me|go to|clear|mine|craft|why|how (?:do|should|can|would)|should we|what should|think|carefully|thoroughly|"
    r"step by step|everything|goal|strategy|improve|optimi[sz]e|blueprint)\b", re.I)
LONG = 160                                     # characters; a long request is rarely a small one


def pick(text, who="player"):
    """-> "quick" or "deep" for one request."""
    if who != "player":                        # standing goals, news, research and alert prompts are the foreman's own big jobs
        return "deep"
    text = (text or "").strip()
    if len(text) > LONG or DEEP.search(text):
        return "deep"
    return "quick"


class TieredAgent:
    def __init__(self, quick, deep, choose=pick):
        self.quick, self.deep, self.choose = quick, deep, choose

    def __getattr__(self, name):               # everything but `handle` is the deep agent's own (model, tools, alerts, log, ...)
        return getattr(self.deep, name)

    def handle(self, text, who="player", light=True):
        if self.choose(text, who) == "quick":
            try:
                answer, outcome, stats = self.quick.handle(text, who, light)
            except Exception as e:                                  # a down chat slot must not end the turn
                answer, outcome, stats = None, "source error: %s" % str(e)[:120], {}
            if answer and outcome == "answered":
                stats["tier"] = "quick"
                return answer, outcome, stats
            self.deep.log(event="escalated", why=outcome, text=text[:120])
        answer, outcome, stats = self.deep.handle(text, who, light)
        stats["tier"] = "deep"
        return answer, outcome, stats
