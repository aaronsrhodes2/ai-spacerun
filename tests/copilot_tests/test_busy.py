"""Everything moving (the Captain, 2026-11-13): the share of machines working, and a goal to keep it high."""
import pytest

from copilot.goals import Goal, GoalError
from copilot.tools import LocalTools
from luamod import LuaMod
from test_bridge_with_mod import LuaGame


@pytest.fixture
def mod():
    return LuaMod()


def factory(mod):
    for i in range(6):
        mod.place("assembling-machine-2", 3.5 + 4 * i, 1.5, recipe="electronic-circuit", status="working" if i < 2 else "item_ingredient_shortage")
    for i in range(2):
        mod.place("assembling-machine-2", 3.5 + 4 * i, 11.5, recipe="copper-cable", status="working")
    mod.place("stone-furnace", 40, 40, recipe="iron-plate", status="full_output")
    mod.place("lab", 50.5, 50.5, status="working")


def test_the_share_of_machines_working_and_who_stands_idle(mod):
    factory(mod)
    u = mod.result("utilisation")
    assert (u["machines"], u["working_now"], u["percent_now"]) == (10, 5, 50)
    assert [(g["machine"], g["recipe"], g["idle"], g["of"], g["mostly"]) for g in u["idle_groups"]] == [
        ("assembling-machine-2", "electronic-circuit", 4, 6, "item_ingredient_shortage"), ("stone-furnace", "iron-plate", 1, 1, "full_output")]
    assert "supply more or run fewer" in u["idle_groups"][0]["why"] and "add what uses it" in u["idle_groups"][1]["why"]
    assert "percent_lately" not in u and "plan_production" in u["how_to_balance"]


def test_the_average_over_the_last_minutes(mod):
    factory(mod)
    mod.tick(600)
    mod.run("for _, e in ipairs(game.surfaces.nauvis.entities) do e.status = defines.entity_status.working end")
    mod.tick(600)
    u = mod.result("utilisation")
    assert u["percent_now"] == 100 and u["percent_lately"] == 75                    # one sample at half, one at full
    mod.tick(600 * 20)
    assert mod.result("utilisation")["percent_lately"] == 100                       # the old sample has dropped out


def test_a_factory_with_everything_working_and_one_with_nothing(mod):
    assert mod.result("utilisation") == {"machines": 0, "note": "there are no machines here yet"}
    mod.place("lab", 50.5, 50.5, status="working")
    u = mod.result("utilisation")
    assert u["percent_now"] == 100 and u["idle_groups"] == {} and u["more_groups_not_shown"] == 0


def test_keeping_everything_moving_is_a_goal():
    g = Goal("busy", 90)
    assert g.describe() == "keep 90% of the machines working" and g.measure() == ("utilisation", {})
    assert Goal("busy").value == 95
    assert g.reached({}, {"machines": 10, "percent_now": 50, "percent_lately": 92}) == (True, "92% of 10 machines working")
    assert g.reached({}, {"machines": 10, "percent_now": 95}) == (True, "95% of 10 machines working (right now; no average yet)")
    assert g.reached({}, {"machines": 10, "percent_now": 100, "percent_lately": 70})[0] is False        # the average counts, not a lucky moment
    assert g.reached({}, {"machines": 0}) == (False, "there are no machines yet")
    with pytest.raises(GoalError, match="between 1 and 100"):
        Goal("busy", 140)
    assert Goal("science", 60).measure() == ("science", {"target": 60.0}) and Goal("win").measure() is None


def test_the_turn_prompt_names_the_idle_groups_and_the_real_levers():
    u = {"machines": 10, "percent_now": 50, "idle_groups": [{"machine": "assembling-machine-2", "recipe": "electronic-circuit", "idle": 4, "of": 6,
                                                            "why": "starved: supply more or run fewer"}]}
    p = Goal("busy", 95).prompt({}, u)
    assert "keep 95% of the machines working" in p and "4 of 6 assembling-machine-2 making electronic-circuit (starved: supply more or run fewer)" in p
    assert "no dial for a machine's effort" in p and "plan_production" in p


def test_a_busy_goal_through_the_tool_and_the_loop(mod):
    from copilot.agent import Agent
    from copilot.loop import Bridge
    from fakes import FakeModel
    factory(mod)
    game = LuaGame(mod)
    tools = LocalTools(game)
    assert tools.call("set_goal", {"kind": "busy", "percent": 90})["result"]["goal"] == "keep 90% of the machines working"
    agent = Agent(game, FakeModel([[("utilisation", {})], "Four circuit machines are starved; I would add two cable machines."]), local=tools)
    clock = [1000.0]
    bridge = Bridge(game, agent, tools, clock=lambda: clock[0], out=lambda *a: None, bottleneck_machines=99)
    bridge.step()
    assert tools.goal.turns == 1 and "4 of 6 assembling-machine-2 making electronic-circuit" in agent.model.seen[0][1]["content"]
    mod.run("for _, e in ipairs(game.surfaces.nauvis.entities) do e.status = defines.entity_status.working end")
    mod.tick(600 * 13)                                                              # the average fills with full samples
    clock[0] += 60
    bridge.step()
    assert tools.goal is None and "Goal reached: keep 90% of the machines working (100% of 10 machines working)" in mod.lua.eval("fake.printed[#fake.printed]")
