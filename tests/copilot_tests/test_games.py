"""Two games, never one (the Captain, 2026-11-21): the live game and the skippy-core test game are separate, and purple
Skippy must not conflate their maps. Each piece says which game it talks to; the map seed tells them apart; plans, logs,
purple's conversation and purple's door are per game."""
import json

import pytest

from copilot import games
from copilot.mcp_server import Server
from copilot.purple import PurpleAgent
from copilot.toolbox import Toolbox
from copilot.tools import LocalTools
from luamod import LuaMod
from test_bridge_with_mod import LuaGame


def game(seed):
    mod = LuaMod()
    mod.run("game.surfaces.nauvis.map_gen_settings.seed = %d" % seed)
    return LuaGame(mod)


def test_the_test_game_has_the_test_seed_and_the_live_game_never_does():
    test_map, live_map = game(games.TEST_SEED), game(98765)
    assert games.check(test_map, "test")[0] and games.check(live_map, "live")[0]
    ok, why = games.check(live_map, "test")
    assert not ok and "not the test game" in why
    ok, why = games.check(test_map, "live")
    assert not ok and "it is the test game" in why


def test_a_mod_too_old_to_say_its_seed_passes_only_as_live():
    class Old:
        def call(self, tool, args=None):
            return {"ok": False, "error": "there is no tool named '%s'" % tool}
    assert games.check(Old(), "live")[0] and not games.check(Old(), "test")[0]


def test_choosing_test_points_at_the_test_server_whatever_copilot_env_says():
    env = games.apply({"COPILOT_GAME": "test", "COPILOT_RCON_PORT": "27115", "COPILOT_RCON_PASSWORD": "live-secret"})
    assert env["COPILOT_RCON_PORT"] == "27116" and env["COPILOT_RCON_PASSWORD_FILE"] == ".testserver/rcon.pw"
    assert "COPILOT_RCON_PASSWORD" not in env
    live = games.apply({"COPILOT_RCON_PORT": "27115"})
    assert live["COPILOT_RCON_PORT"] == "27115"                                  # live is the default and unchanged
    with pytest.raises(games.WrongGame):
        games.name_of({"COPILOT_GAME": "staging"})


def test_plans_are_kept_per_game(tmp_path):
    assert games.plan_file(tmp_path, "live") != games.plan_file(tmp_path, "test")


def test_the_door_to_the_wrong_map_is_shut_and_every_answer_says_its_game():
    g = game(98765)
    box = Toolbox(g, LocalTools(g))
    open_door = Server(box, "live")
    r = open_door.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "lookup", "arguments": {"name": "iron-plate"}}})
    assert json.loads(r["result"]["content"][0]["text"])["game"] == "live"
    assert open_door.handle({"jsonrpc": "2.0", "id": 2, "method": "initialize"})["result"]["serverInfo"]["name"] == "skippy-copilot"
    shut = Server(box, "test", refusal=games.check(g, "test")[1])
    r = shut.handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "lookup", "arguments": {"name": "iron-plate"}}})
    assert r["result"]["isError"] and "door to the test game, and it is shut" in r["result"]["content"][0]["text"]
    assert shut.handle({"jsonrpc": "2.0", "id": 4, "method": "initialize"})["result"]["serverInfo"]["name"] == "skippy-copilot-test"


def test_purple_is_told_which_game_and_which_door_and_talks_apart():
    g = game(games.TEST_SEED)
    sent = []

    class Purple:
        workspace = "f-ai-factorio"

        def ask(self, message, conv):
            sent.append((message, conv))
            return {"text": "done", "steps": 0, "ok": True, "error": None}

    test_agent = PurpleAgent(g, Purple(), Toolbox(g, LocalTools(g)), which="test")
    test_agent.handle("build a smelter", light=False)
    message, conv = sent[-1]
    assert "This turn is about the test game" in message and "skippy-copilot-test MCP server" in message
    assert "never carry a fact or a coordinate across" in message and conv.startswith("factorio-test-")
    live_agent = PurpleAgent(g, Purple(), Toolbox(g, LocalTools(g)), which="live")
    live_agent.handle("build a smelter", light=False)
    assert "the skippy-copilot MCP server" in sent[-1][0] and "skippy-copilot-test" not in sent[-1][0] and sent[-1][1].startswith("factorio-live-")


def test_a_game_is_named_by_its_creator_and_seed_in_the_panel_and_the_bridge(tmp_path):
    """The Captain, 2026-11-21: the save and its chat share one name, made from who started the game and its seed."""
    mod = LuaMod()
    mod.run("game.surfaces.nauvis.map_gen_settings.seed = 3141592")
    g = LuaGame(mod)
    assert games.title(g) is None                                                 # nobody has joined: no creator yet
    mod.run("fake.add_player('aaronsrhodes', 0, 0) fake.add_player('guest', 1, 1)")
    assert games.title(g) == "aaronsrhodes-3141592"
    assert mod.lua.eval("game.players[2].gui.screen.skippy_panel.caption") == "Skippy  -  aaronsrhodes-3141592"
    assert games.plan_file(tmp_path, "live", "aaronsrhodes-3141592").name == "plans-aaronsrhodes-3141592.json"
    sent = []

    class Purple:
        workspace = "f-ai-factorio"

        def ask(self, message, conv):
            sent.append((message, conv))
            return {"text": "done", "steps": 0, "ok": True, "error": None}

    PurpleAgent(g, Purple(), Toolbox(g, LocalTools(g)), which="live", title="aaronsrhodes-3141592").handle("hi", light=False)
    assert "the live (aaronsrhodes-3141592) game" in sent[-1][0] and sent[-1][1].startswith("factorio-aaronsrhodes-3141592-")


def test_the_light_says_plainly_what_skippy_is_doing():
    from copilot.agent import light_note
    assert light_note("News from the game: an obvious bottleneck. 4 machines are starved") == "noticed an obvious bottleneck"
    assert light_note("run the ranker and fix the worst bottleneck in the north smelting block please") == "run the ranker and fix the worst bottleneck in the north..."
    assert light_note("where is iron?") == "where is iron?"


def test_the_mcp_config_has_one_door_per_game():
    cfg = json.loads((games.pathlib.Path(__file__).resolve().parents[2] / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"]
    assert cfg["skippy-copilot"]["env"]["COPILOT_GAME"] == "live" and cfg["skippy-copilot-test"]["env"]["COPILOT_GAME"] == "test"
