"""Standing goals and the bridge's loop, with a fake model. The loop is stepped by hand; time is a number the test moves."""
import pytest

from copilot.agent import Agent
from copilot.goals import Goal, GoalError
from copilot.loop import AlertWatch, Bridge, is_nothing
from copilot.score import read, score
from copilot.tools import LocalTools
from fakes import TOOLS, FakeGame, FakeModel

EMPTY = {"researched": [], "produced": {}, "built": {}, "rockets_launched": 0, "platforms": [], "planets_reached": [], "won": False, "hours_played": 1.0}
SPM = {"science_per_minute": 400, "slowest_pack": "chemical-science-pack", "reached": False,
       "short": [{"pack": "chemical-science-pack", "short_by": 600}, {"pack": "logistic-science-pack", "short_by": 50}]}


# ---------------------------------------------------------------- goals

def test_the_three_kinds_describe_themselves():
    assert Goal("win").describe() == "win the game"
    assert Goal("milestone", "rocket-silo").describe() == "reach the milestone: Build a rocket silo"
    assert Goal("science", 1000).describe() == "make 1000 of every science pack a minute"


def test_bad_goals_are_refused_with_the_choices():
    with pytest.raises(GoalError, match="'win', 'milestone' or 'science'"):
        Goal("conquer")
    with pytest.raises(GoalError, match="no milestone 'moon'.*first-plates"):
        Goal("milestone", "moon")
    with pytest.raises(GoalError, match="needs a number"):
        Goal("science", None)
    with pytest.raises(GoalError, match="above zero"):
        Goal("science", 0)


def test_a_win_goal_is_reached_only_by_the_win():
    g = Goal("win")
    assert g.reached(EMPTY) == (False, "0 of 21 milestones done")
    assert g.reached(dict(EMPTY, won=True))[0] is True


def test_a_milestone_goal_says_what_it_still_needs():
    g = Goal("milestone", "first-plates")
    ok, where = g.reached(dict(EMPTY, produced={"iron-plate": 50}))
    assert not ok and where == "still needs: 10 more copper-plate made (0 of 10)"
    assert g.reached(dict(EMPTY, produced={"iron-plate": 50, "copper-plate": 10})) == (True, "done")


def test_a_science_goal_goes_by_the_slowest_pack():
    g = Goal("science", 1000)
    assert g.needs_science() and not Goal("win").needs_science()
    assert g.reached(EMPTY, SPM) == (False, "400 a minute now (slowest: chemical-science-pack)")
    assert g.reached(EMPTY, {"science_per_minute": 1010, "slowest_pack": "x", "reached": True, "short": []})[0] is True
    assert g.reached(EMPTY, None) == (False, "0 a minute now (slowest: none made yet)")


def test_the_prompt_for_a_turn_of_its_own_carries_the_goal_and_the_next_step():
    p = Goal("win").prompt(EMPTY)
    assert "standing goal the player gave you: win the game" in p and "Nobody has typed anything" in p
    assert "The next milestone is: Smelt the first iron and copper plates" in p and "50 more iron-plate made" in p and "BLOCKED" in p
    p = Goal("science", 1000).prompt(EMPTY, SPM)
    assert "chemical-science-pack (short by 600 a minute), logistic-science-pack (short by 50 a minute)" in p
    assert "Science you cannot make yet needs research first" in p


# ---------------------------------------------------------------- the loop

class LoopGame(FakeGame):
    """A fake game with the tools the loop uses and a scriptable state."""

    def __init__(self):
        super().__init__()
        self.chat, self.events, self.alert_list = [], [], []
        self.facts = dict(EMPTY)
        self.science = dict(SPM)
        self.results = {
            "chat_read": lambda a: {"ok": True, "result": {"lines": [l for l in self.chat if l["id"] > (a or {}).get("after", 0)], "last_id": len(self.chat)}},
            "events_read": lambda a: {"ok": True, "result": {"events": [e for e in self.events if e["id"] > (a or {}).get("after", 0)], "last_id": len(self.events)}},
            "alerts": lambda a: {"ok": True, "result": {"alerts": self.alert_list}},
            "progress": lambda a: {"ok": True, "result": dict(self.facts)},
            "science": lambda a: {"ok": True, "result": dict(self.science)},
            "diagnose": {"ok": True, "result": {"problems": []}},
        }

    def tools(self):
        return TOOLS + [{"name": n, "description": n, "parameters": {}} for n in ("alerts", "progress", "science")]

    def type(self, text):
        self.chat.append({"id": len(self.chat) + 1, "player": "captain", "text": text})

    def said(self):
        return [a["text"] for a in self.named("say")]


def make(replies, tmp_path=None, **kw):
    game = LoopGame()
    tools = LocalTools(game)
    agent = Agent(game, FakeModel(replies), (tmp_path / "run.jsonl") if tmp_path else None, local=tools)
    clock = [1000.0]
    bridge = Bridge(game, agent, tools, clock=lambda: clock[0], out=lambda *a: None, **kw)
    return game, tools, agent, bridge, clock


def test_a_typed_line_is_answered_in_the_chat():
    game, tools, agent, bridge, _ = make(["Iron first."])
    game.type("what should we do?")
    bridge.step()
    assert game.said() == ["Iron first."]
    bridge.step()                                                    # nothing new: nothing more is said
    assert game.said() == ["Iron first."]


def test_lines_from_before_the_bridge_started_are_not_answered():
    game = LoopGame()
    game.type("old line")
    tools = LocalTools(game)
    bridge = Bridge(game, Agent(game, FakeModel([]), local=tools), tools, out=lambda *a: None)
    bridge.step()
    assert game.said() == []


def test_finished_research_is_brought_up_unless_the_model_has_nothing_to_say():
    game, tools, agent, bridge, _ = make(["You unlocked assembler 2: swap the gear machines.", "nothing."])
    game.events.append({"id": 1, "kind": "research_finished", "technology": "automation-2", "unlocks_recipes": ["assembling-machine-2"], "design_note": "Faster."})
    bridge.step()
    game.events.append({"id": 2, "kind": "research_finished", "technology": "worker-robots-speed-1", "unlocks_recipes": ["x"]})
    bridge.step()
    assert game.said() == ["You unlocked assembler 2: swap the gear machines."] and is_nothing("Nothing.") and not is_nothing("Nothing to add, but...")


def test_a_new_alert_is_looked_into_once():
    game, tools, agent, bridge, _ = make(["A train is out of fuel at -449,-410; refuel it."])
    bridge.step()
    game.alert_list = [{"surface": "nauvis", "kind": "train_out_of_fuel", "count": 1, "means": "a train has no fuel"}]
    bridge.step()
    bridge.step()
    assert game.said() == ["A train is out of fuel at -449,-410; refuel it."]
    assert "train_out_of_fuel on nauvis" in agent.model.seen[0][1]["content"]


def test_setting_a_goal_makes_the_assistant_carry_on_by_itself(tmp_path):
    game, tools, agent, bridge, clock = make([
        [("set_goal", {"kind": "milestone", "milestone": "first-plates"})], "I will get us the first plates.",
        [("diagnose", {})], "I placed two furnaces.",
        [("diagnose", {})], "I am feeding them ore.",
    ], tmp_path, goal_pause=20)
    game.type("get us the first plates")
    bridge.step()
    assert tools.goal.describe().startswith("reach the milestone") and game.said() == ["I will get us the first plates."]
    clock[0] += 5
    bridge.step()                                                    # too soon after the first step? the first goal turn runs at once
    assert game.said()[-1] == "I placed two furnaces." and tools.goal.turns == 1
    clock[0] += 5
    bridge.step()                                                    # within the pause: no new turn
    assert tools.goal.turns == 1
    clock[0] += 20
    bridge.step()
    assert tools.goal.turns == 2 and game.said()[-1] == "I am feeding them ore."
    assert "standing goal the player gave you" in agent.model.seen[2][1]["content"]
    game.facts = dict(EMPTY, produced={"iron-plate": 60, "copper-plate": 12})
    clock[0] += 20
    bridge.step()
    assert tools.goal is None and game.said()[-1] == "Goal reached: reach the milestone: Smelt the first iron and copper plates (done). It took 2 turns of my own."
    s = score(read(tmp_path / "run.jsonl"))
    assert s["requests"] == 3 and s["clean"]                         # one prompt from the player, two turns of its own, all logged


def test_a_goal_turn_never_runs_while_the_player_is_being_answered():
    game, tools, agent, bridge, clock = make(["Hello."])
    tools.set_goal("win")
    game.type("hi")
    bridge.step()
    assert tools.goal.turns == 0 and game.said() == ["Hello."]


def test_a_science_goal_measures_with_the_science_tool():
    game, tools, agent, bridge, clock = make([[("diagnose", {})], "Adding chemical science machines."])
    tools.set_goal("science", per_minute=1000)
    bridge.step()
    assert game.named("science") == [{"target": 1000.0}] and "short by 600 a minute" in agent.model.seen[0][1]["content"]
    game.science = {"science_per_minute": 1005, "slowest_pack": "chemical-science-pack", "reached": True, "short": []}
    clock[0] += 60
    bridge.step()
    assert tools.goal is None and "Goal reached: make 1000 of every science pack a minute (1005 a minute now" in game.said()[-1]


def test_blocked_stops_the_turns_until_the_player_speaks():
    game, tools, agent, bridge, clock = make(["BLOCKED: I need a rocket silo with a rocket ready.", "Thanks, going on.", [("diagnose", {})], "Travelling now."])
    tools.set_goal("win")
    bridge.step()
    assert tools.goal_paused and game.said() == ["BLOCKED: I need a rocket silo with a rocket ready."]
    assert game.named("set_state")[-1]["state"] == "blocked"
    clock[0] += 500
    bridge.step()
    assert tools.goal.turns == 1                                     # still waiting
    game.type("the rocket is ready now")
    bridge.step()
    assert not tools.goal_paused
    clock[0] += 30
    bridge.step()
    assert tools.goal.turns == 2 and game.said()[-1] == "Travelling now."


def test_turns_that_do_nothing_in_the_game_end_the_goals_run():
    game, tools, agent, bridge, clock = make(["Thinking about it.", "Still thinking.", "Hmm."], max_idle_turns=3)
    tools.set_goal("win")
    for _ in range(3):
        bridge.step()
        clock[0] += 30
    assert tools.goal_paused and tools.goal.idle_turns == 3
    assert game.said()[-1].startswith("I have stopped working on the goal because I was not getting anywhere.")


def test_a_model_failure_during_a_goal_turn_waits_for_the_player():
    game, tools, agent, bridge, clock = make([RuntimeError("model server down")])
    tools.set_goal("win")
    bridge.step()
    assert tools.goal_paused and game.said() == ["I could not go on (model error)."]


def test_the_player_can_stop_the_goal():
    game, tools, agent, bridge, clock = make([[("clear_goal", {})], "Stopped."])
    tools.set_goal("win")
    game.type("stop")
    bridge.step()
    assert tools.goal is None and game.said() == ["Stopped."]
    clock[0] += 100
    bridge.step()
    assert game.said() == ["Stopped."]


def test_goal_tools_through_the_tool_call_path():
    game = LoopGame()
    tools = LocalTools(game)
    r = tools.call("set_goal", {"kind": "science", "per_minute": 1000})
    assert r["ok"] and r["result"]["goal"] == "make 1000 of every science pack a minute"
    assert tools.call("milestones", {})["result"]["standing_goal"] == "make 1000 of every science pack a minute"
    assert "no milestone 'moon'" in tools.call("set_goal", {"kind": "milestone", "milestone": "moon"})["error"]
    assert "needs a number" in tools.call("set_goal", {"kind": "science"})["error"]
    assert tools.call("clear_goal", {})["result"] == {"cleared": True, "was": "make 1000 of every science pack a minute"}
    assert tools.call("clear_goal", {})["result"]["cleared"] is False


def test_progress_is_checked_once_a_minute_and_a_stall_is_logged(tmp_path):
    game, tools, agent, bridge, clock = make([], tmp_path, stall_hours=2.0)
    bridge.step()
    bridge.step()
    assert len(game.named("progress")) == 1                          # not again within the minute
    game.facts = dict(EMPTY, hours_played=4.0)
    clock[0] += 61
    bridge.step()
    events = [e["event"] for e in read(tmp_path / "run.jsonl")]
    assert events == ["milestone", "stall"] and not score(read(tmp_path / "run.jsonl"))["clean"]


def test_a_game_that_cannot_report_progress_does_not_stop_the_loop():
    game, tools, agent, bridge, clock = make(["Hello."])
    game.results["progress"] = {"ok": False, "error": "no such tool"}
    game.type("hi")
    bridge.step()
    assert game.said() == ["Hello."]
    tools.set_goal("win")
    clock[0] += 100
    bridge.step()                                                    # the goal check fails quietly too
    assert tools.goal.turns == 0


def test_alert_watch_still_exported_for_older_callers():
    import copilot.__main__ as main
    assert main.AlertWatch is AlertWatch and main.say and main.news_prompt and main.alert_prompt
