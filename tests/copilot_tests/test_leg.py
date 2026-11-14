import pathlib

from copilot import leg
from copilot.agent import Agent
from fakes import FakeGame, FakeModel

ROOT = pathlib.Path(__file__).resolve().parents[2]


def test_prompts_file_skips_comments_and_blank_lines():
    assert leg.prompts_of("# heading\n\nfirst prompt\n   second prompt  \n# another\n") == ["first prompt", "second prompt"]


def test_a_leg_asks_every_prompt_in_order_and_keeps_the_counts():
    agent = Agent(FakeGame(), FakeModel(["One.", [("diagnose", {})], "Two.", [("nope", {})], "Three."]))
    printed = []
    rows = leg.run(agent, ["a", "b", "c"], out=printed.append)
    assert [(r["prompt"], r["answer"], r["calls"], r["misses"]) for r in rows] == [("a", "One.", 0, 0), ("b", "Two.", 1, 0), ("c", "Three.", 1, 1)]
    assert printed[0] == " 1. a" and printed[1] == "    -> One." and "1 refused" in printed[8]


def test_a_prompt_the_model_cannot_finish_is_shown_as_such():
    agent = Agent(FakeGame(), FakeModel([RuntimeError("down")]))
    printed = []
    rows = leg.run(agent, ["a"], out=printed.append)
    assert rows[0]["answer"] is None and rows[0]["outcome"] == "model error" and "(no answer: model error)" in printed[1]


def test_the_first_leg_has_prompts_for_each_kind_of_skill():
    prompts = leg.prompts_of((ROOT / "copilot" / "legs" / "first.txt").read_text(encoding="utf-8"))
    assert 15 <= len(prompts) <= 30 and len(set(prompts)) == len(prompts)
    text = " ".join(prompts).lower()
    for word in ("nearest iron ore", "water", "bottleneck", "research", "drills", "belt", "remove", "rocket silo", "give me"):
        assert word in text, word
