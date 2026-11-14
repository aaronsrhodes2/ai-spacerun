"""Two speeds of thinking: short questions to the quick model, plans and builds to the deep one, and main() starting with both."""
import pytest

import copilot.__main__ as entry
from copilot.agent import Agent
from copilot.tiered import TieredAgent, pick
from copilot.tools import LocalTools
from fakes import FakeModel
from test_goals import LoopGame


def test_short_questions_are_quick_and_plans_are_deep():
    for text in ("what is in my inventory?", "where am I", "how much copper do we have", "status"):
        assert pick(text) == "quick", text
    for text in ("build a smelter column", "plan the oil", "why is copper starved", "think about this carefully", "take over my character",
                 "how should we do Aquilo", "x " * 100):
        assert pick(text) == "deep", text
    assert pick("what is in my inventory?", "game") == "deep"        # news, alerts, research and goals are the foreman's own big jobs
    assert pick("anything", "goal") == "deep"


def agents(quick_replies, deep_replies):
    game = LoopGame()
    tools = LocalTools(game)
    quick, deep = Agent(game, FakeModel(list(quick_replies)), local=tools), Agent(game, FakeModel(list(deep_replies)), local=tools)
    return TieredAgent(quick, deep), quick, deep


def test_a_short_question_is_answered_by_the_quick_agent_alone():
    t, quick, deep = agents(["Iron plates: 40."], [])
    answer, outcome, stats = t.handle("what is in my inventory?")
    assert (answer, outcome, stats["tier"]) == ("Iron plates: 40.", "answered", "quick")
    assert deep.model.seen == []


def test_a_plan_goes_straight_to_the_deep_agent():
    t, quick, deep = agents([], ["Four furnaces, west of the ore."])
    answer, outcome, stats = t.handle("plan the copper smelting")
    assert (answer, stats["tier"]) == ("Four furnaces, west of the ore.", "deep") and quick.model.seen == []


def test_a_quick_model_that_is_down_or_silent_falls_back_to_the_deep_agent():
    t, _, _ = agents([RuntimeError("connection refused")], ["Deep answer."])
    assert t.handle("where am I")[0] == "Deep answer."
    t, _, _ = agents([""], ["Deep answer."])
    answer, _, stats = t.handle("where am I")
    assert answer == "Deep answer." and stats["tier"] == "deep"


def test_everything_else_is_the_deep_agents_own():
    t, quick, deep = agents([], [])
    assert t.model is deep.model and t.tools is deep.tools and t.names is deep.names


def test_main_starts_with_both_tiers_and_keeps_the_voice_door(monkeypatch, tmp_path, capsys):
    """The start-up crash (purple's address replacing the voice door) got past every other test: run main() itself."""
    env = {"COPILOT_SOURCE": "ollama", "COPILOT_MODEL": "m", "COPILOT_PURPLE_URL": "off", "COPILOT_LOG_DIR": str(tmp_path),
           "COPILOT_QUICK_URL": "http://localhost:1/v1", "COPILOT_QUICK_SOURCE": "openai", "COPILOT_QUICK_MODEL": "chat",
           "COPILOT_VOICE_PORT": "0"}
    monkeypatch.setattr(entry, "settings", lambda: env)
    monkeypatch.setattr(entry, "game_from", lambda e: LoopGame())
    monkeypatch.setattr(entry.sys, "argv", ["copilot"])
    ticks = []

    def sleep(_):
        ticks.append(1)
        raise KeyboardInterrupt
    monkeypatch.setattr(entry.time, "sleep", sleep)
    with pytest.raises(KeyboardInterrupt):
        entry.main()
    out = capsys.readouterr().out
    assert "voice door: http://127.0.0.1:" in out and "listening:" in out and ticks


def test_the_quick_tier_is_off_without_a_url_and_refuses_an_odd_source():
    game = LoopGame()
    assert entry.quick_from({}, game, LocalTools(game), None) is None
    with pytest.raises(entry.SetupError):
        entry.quick_from({"COPILOT_QUICK_URL": "http://x", "COPILOT_QUICK_SOURCE": "purple"}, game, LocalTools(game), None)
    with pytest.raises(entry.SetupError):
        entry.quick_from({"COPILOT_QUICK_URL": "http://x"}, game, LocalTools(game), None)
