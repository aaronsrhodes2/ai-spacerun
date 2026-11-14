"""The bridge's tools driving the mod's real Lua (under Lua 5.2, against the stand-in game). This is the whole path a
model's tool call takes except for RCON and the game itself: planning code in Python, the /skippy command, the mod's
tools, and for the avatar the waiting in between, where every wait lets the stand-in world run on."""
import pytest

from copilot.agent import Agent
from copilot.tools import LocalTools
from fakes import FakeModel
from luamod import LuaMod


class LuaGame:
    """The bridge's view of the game, answered by the mod's Lua instead of over RCON."""

    def __init__(self, mod):
        self.mod = mod

    def call(self, tool, args=None):
        return self.mod.call(tool, args or None)

    def tools(self):
        return self.mod.result("tools")


@pytest.fixture
def world():
    mod = LuaMod()
    tools = LocalTools(LuaGame(mod), sleep=lambda seconds: mod.tick(30), poll=0.5, patience=2000)
    return mod, tools


def ok(tools, name, args):
    r = tools.call(name, args)
    assert r["ok"], r
    return r["result"]


def test_a_production_plan_from_the_games_own_recipes(world):
    mod, tools = world
    r = ok(tools, "plan_production", {"item": "electronic-circuit", "per_second": 1.5})
    steps = {s["make"]: s for s in r["steps"]}
    assert steps["electronic-circuit"]["machines"] == 1 and steps["electronic-circuit"]["machine"] == "assembling-machine-2"
    assert steps["copper-cable"]["per_minute"] == 270 and steps["iron-plate"]["machine"] == "stone-furnace"
    assert r["supplied_per_minute"] == {"iron-ore": 90, "copper-plate": 135}


def test_a_row_is_planned_checked_and_built_by_the_free_hand(world):
    mod, tools = world
    plan = ok(tools, "plan_row", {"machine": "assembling-machine-2", "count": 3, "x": 10, "y": 10, "recipe": "iron-gear-wheel"})
    dry = ok(tools, "build_plan", {"plan_id": plan["plan_id"]})
    assert dry["would_place"] == 27 and dry["failed_count"] == 0 and mod.result("tile", {"x": 11, "y": 13})["free"]
    built = ok(tools, "build_plan", {"plan_id": plan["plan_id"], "dry_run": False})
    assert built["placed"] == 27 and built["executor"] == "god"
    machine = mod.result("tile", {"x": 11, "y": 13})["things"][0]
    assert (machine["name"], machine["recipe"]) == ("assembling-machine-2", "iron-gear-wheel")
    picture = mod.result("map", {"x": 10, "y": 10, "width": 9, "height": 7})["picture"].split("\n")[2:]
    assert [line[5:] for line in picture] == ["bbbbbbbbb", ".i..i..i.", "AAAAAAAAA", "AAAAAAAAA", "AAAAAAAAA", ".i..i..i.", "bbbbbbbbb"]


def test_a_row_planned_on_top_of_something_fails_its_dry_run_and_cannot_be_built(world):
    mod, tools = world
    mod.place("wooden-chest", 11.5, 13.5)
    plan = ok(tools, "plan_row", {"machine": "assembling-machine-2", "count": 2, "x": 10, "y": 10})
    dry = ok(tools, "build_plan", {"plan_id": plan["plan_id"]})
    assert dry["failed_count"] == 1 and "in the way" in dry["failed"][0]["why"]
    assert "not passed a dry run" in tools.call("build_plan", {"plan_id": plan["plan_id"], "dry_run": False})["error"]


def test_a_belt_is_routed_round_what_the_game_says_is_there_and_built(world):
    mod, tools = world
    for y in range(-20, 21):
        mod.place("wooden-chest", 5.5, y + 0.5)
    plan = ok(tools, "plan_route", {"kind": "belt", "from_x": 0, "from_y": 0, "to_x": 10, "to_y": 0})
    assert plan["underground_pairs"] == 1 and plan["tiles"] == 11
    ok(tools, "build_plan", {"plan_id": plan["plan_id"]})
    assert ok(tools, "build_plan", {"plan_id": plan["plan_id"], "dry_run": False})["placed"] == plan["pieces"]
    assert mod.result("tile", {"x": 4, "y": 0})["things"][0]["name"] == "underground-belt"
    assert mod.result("tile", {"x": 6, "y": 0})["things"][0]["name"] == "underground-belt"
    assert mod.result("tile", {"x": 10, "y": 0})["things"][0]["direction"] == "East"


def test_pointing_with_words_uses_the_games_frames(world):
    mod, tools = world
    mod.run("fake.add_player('captain', 100, 50)")
    mod.place("medium-electric-pole", -20.5, -30.5)
    mod.place("medium-electric-pole", 40.5, 10.5)
    r = ok(tools, "locate", {"frame": "view", "part": "middle"})
    assert abs(r["centre_x"] - 100) <= 1 and abs(r["centre_y"] - 50) <= 1
    assert ok(tools, "locate", {"frame": "base", "part": "east"})["to_x"] == 40
    assert ok(tools, "locate", {"frame": "player"})["centre_x"] == 100


def test_walk_to_waits_until_the_avatar_is_there(world):
    mod, tools = world
    r = ok(tools, "walk_to", {"x": 15, "y": 4})
    assert r["arrived"] and abs(r["x"] - 15) <= 1 and abs(r["y"] - 4) <= 1 and r["game_seconds"] > 1
    assert mod.result("avatar").get("job") is None


def test_walk_to_says_why_it_could_not_arrive_and_where_it_is(world):
    mod, tools = world
    mod.run("fake.no_path = true")
    r = tools.call("walk_to", {"x": 15, "y": 4})
    assert not r["ok"] and "no way on foot" in r["error"] and "it is at 0,0 now" in r["hint"]


def test_mine_waits_and_reports_what_is_carried(world):
    mod, tools = world
    mod.place("iron-ore", 6.5, 0.5, amount=3, force=False)
    r = ok(tools, "mine", {"x": 6, "y": 0, "count": 2})
    assert (r["item"], r["mined"], r["carries"]) == ("iron-ore", 2, {"iron-ore": 2})
    r = ok(tools, "mine", {"x": 6, "y": 0, "count": 5})                      # only one is left
    assert r["mined"] == 1 and "no more iron-ore" in r["note"]
    assert "nothing to mine" in tools.call("mine", {"x": 30, "y": 30})["error"]


def test_under_the_avatar_a_plan_needs_the_pieces_carried_then_is_walked_and_built(world):
    mod, tools = world
    mod.result("set_executor", {"mode": "avatar"})
    plan = ok(tools, "plan_row", {"machine": "assembling-machine-2", "count": 2, "x": 30, "y": 10, "recipe": "copper-cable"})
    dry = ok(tools, "build_plan", {"plan_id": plan["plan_id"]})
    assert dry["avatar_lacks"] == {"assembling-machine-2": 2, "inserter": 4, "transport-belt": 12}
    assert "not passed a dry run" in tools.call("build_plan", {"plan_id": plan["plan_id"], "dry_run": False})["error"]

    mod.give(assembling_machine_2=2, inserter=4, transport_belt=12)
    assert "avatar_lacks" not in ok(tools, "build_plan", {"plan_id": plan["plan_id"]})
    built = ok(tools, "build_plan", {"plan_id": plan["plan_id"], "dry_run": False})
    assert built["finished"] and (built["placed"], built["of"]) == (18, 18) and built["executor"] == "avatar"
    assert built["avatar_carries"] == {} and built["game_seconds"] > 3
    assert mod.result("tile", {"x": 31, "y": 13})["things"][0]["recipe"] == "copper-cable"
    assert "not passed a dry run" in tools.call("build_plan", {"plan_id": plan["plan_id"], "dry_run": False})["error"]     # not twice


def test_something_put_in_the_way_after_the_dry_run_is_caught_before_the_avatar_sets_off(world):
    mod, tools = world
    mod.result("set_executor", {"mode": "avatar"})
    mod.give(transport_belt=11)
    plan = ok(tools, "plan_route", {"kind": "belt", "from_x": 20, "from_y": 0, "to_x": 30, "to_y": 0})
    ok(tools, "build_plan", {"plan_id": plan["plan_id"]})
    mod.place("wooden-chest", 26.5, 0.5)
    built = ok(tools, "build_plan", {"plan_id": plan["plan_id"], "dry_run": False})
    assert built["placed"] == 0 and "nothing was started" in built["note"] and "in the way" in built["failed"][0]["why"]
    assert mod.result("avatar").get("job") is None and mod.result("avatar")["carries"] == {"transport-belt": 11}


def test_a_build_the_avatar_cannot_finish_reports_how_far_it_got(world):
    mod, _ = world
    dropped = []

    def sleep(seconds):                                                       # the world runs on while the bridge waits...
        if not dropped:
            mod.place("wooden-chest", 26.5, 0.5)                              # ...and something lands in the way mid-job
            dropped.append(True)
        mod.tick(30)
    tools = LocalTools(LuaGame(mod), sleep=sleep, patience=2000)
    mod.result("set_executor", {"mode": "avatar"})
    mod.give(transport_belt=11)
    plan = ok(tools, "plan_route", {"kind": "belt", "from_x": 20, "from_y": 0, "to_x": 30, "to_y": 0})
    ok(tools, "build_plan", {"plan_id": plan["plan_id"]})
    built = ok(tools, "build_plan", {"plan_id": plan["plan_id"], "dry_run": False})
    assert built["finished"] is False and built["placed"] == 6 and "in the way at 26.5,0.5" in built["stopped_because"]
    assert built["stopped_at"]["name"] == "transport-belt" and built["avatar_carries"] == {"transport-belt": 5}


def test_waiting_gives_up_politely_when_the_avatar_takes_too_long(world):
    mod, _ = world
    tools = LocalTools(LuaGame(mod), sleep=lambda s: mod.tick(1), patience=5)
    r = tools.call("walk_to", {"x": 50, "y": 0})
    assert not r["ok"] and "still working" in r["error"] and "avatar_stop" in r["hint"]
    assert mod.result("avatar")["job"]["kind"] == "walk"                      # the walk itself goes on


def test_the_model_is_offered_the_waiting_tools_not_the_raw_ones(world):
    mod, tools = world
    agent = Agent(LuaGame(mod), FakeModel(["ok"]), local=tools)
    assert {"walk_to", "mine", "avatar", "avatar_craft", "avatar_carry", "avatar_stop", "build_plan", "bottlenecks", "locate"} <= agent.names
    assert not {"avatar_walk", "avatar_mine", "set_executor", "build", "occupancy", "frames", "say"} & agent.names


def test_a_whole_request_through_the_agent_the_bridge_and_the_mod(world):
    """A model that asks for a plan, checks it, builds it and answers, with every call answered by the real mod code."""
    mod, tools = world
    model = FakeModel([
        [("plan_row", {"machine": "assembling-machine-2", "count": 2, "x": 0, "y": 20, "recipe": "iron-gear-wheel"})],
        [("build_plan", {"plan_id": "plan-1"})],
        [("build_plan", {"plan_id": "plan-1", "dry_run": False})],
        [("diagnose", {})],
        "Two gear machines are built at 0,20.",
    ])
    agent = Agent(LuaGame(mod), model, local=tools)
    answer, outcome, stats = agent.handle("build two gear machines south of here")
    assert (answer, outcome, stats["calls"], stats["misses"]) == ("Two gear machines are built at 0,20.", "answered", 4, 0)
    assert mod.lua.eval("game.surfaces.nauvis.count_entities_filtered{name = 'assembling-machine-2'}") == 2
    assert '"machines_checked": 2' in model.seen[4][-1]["content"]
    assert mod.result("set_state", {"state": "idle"})["state"] == "idle"
