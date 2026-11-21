"""The Skippy panel (the Captain, 2026-11-21): a hands-free game, keyboard now and voice later, the mouse never needed.
The panel is the window on the conversation, up all the time on the right where the remote view leaves room; a typed
line goes where console chat goes, and tests type through the same path as the player's Enter key."""
import pytest

from copilot.loop import Bridge
from luamod import LuaMod
from test_bridge_with_mod import LuaGame


@pytest.fixture
def mod():
    m = LuaMod()
    m.run("fake.add_player('captain', 0, 0)")
    return m


def panel(mod):
    return "game.players[1].gui.screen.skippy_panel"


def test_every_player_gets_the_panel_on_the_right_from_the_start(mod):
    assert mod.lua.eval(panel(mod) + " ~= nil")
    x = mod.lua.eval(panel(mod) + ".location.x")
    assert x > 1920 / 2 and x + 420 <= 1920                                         # the right side, inside the screen
    assert mod.lua.eval(panel(mod) + ".location.y") >= 300                            # below the minimap and shortcut buttons
    mod.run("fake.add_player('guest', 5, 5)")
    assert mod.lua.eval("game.players[2].gui.screen.skippy_panel ~= nil")


def test_a_bigger_scale_moves_it_back_inside_the_screen(mod):
    mod.run("game.players[1].display_scale = 2 fake.handlers[defines.events.on_player_display_scale_changed] { player_index = 1 }")
    x = mod.lua.eval(panel(mod) + ".location.x")
    assert x + 420 * 2 <= 1920


def test_enter_sends_the_line_where_chat_goes_and_the_cursor_stays(mod):
    box = panel(mod) + ".skippy_input"
    mod.run("fake.type_in(1, %s, '  build a smelter row  ')" % box)
    lines = mod.result("chat_read")["lines"]
    assert lines[-1]["text"] == "build a smelter row" and lines[-1]["by"] == "panel" and lines[-1]["player"] == "captain"
    assert mod.lua.eval(box + ".text") == "" and mod.lua.eval("fake.focused == " + box)
    mod.run("fake.type_in(1, %s, '   ')" % box)                                      # nothing typed: nothing sent
    assert len(mod.result("chat_read")["lines"]) == 1


def test_the_key_puts_the_cursor_in_the_box(mod):
    mod.run("fake.focused = nil fake.key(1, 'skippy-talk')")
    assert mod.lua.eval("fake.focused == " + panel(mod) + ".skippy_input")


def test_the_whole_talk_shows_in_order_with_who_said_it(mod):
    mod.run("fake.chat(1, 'where is iron?')")
    mod.result("say", {"text": "Nearest iron is 8 tiles west."})
    mod.result("hear", {"text": "thanks"})
    mod.result("say", {"text": "on it", "as": "purple"})
    lines = mod.result("panel_read")["lines"]
    assert [(l["kind"], l["text"]) for l in lines] == [("player", "where is iron?"), ("skippy", "Nearest iron is 8 tiles west."),
                                                       ("voice", "thanks"), ("purple", "on it")]
    captions = [str(c) for c in mod.lua.eval("(function() local t = {} for i, c in ipairs(%s.skippy_log.children) do t[i] = c.caption end return t end)()" % panel(mod)).values()]
    assert captions == ["[captain] where is iron?", "[Skippy] Nearest iron is 8 tiles west.", "[captain (said)] thanks", "[purple] on it"]
    assert mod.lua.eval(panel(mod) + ".skippy_log.scrolled_to_bottom")
    assert mod.result("panel_read", {"after": lines[-2]["id"]})["lines"][0]["text"] == "on it"


def test_the_panel_shows_whether_skippy_is_connected_and_what_it_is_doing(mod):
    status = panel(mod) + ".skippy_status.caption"
    mod.result("set_state", {"state": "thinking", "note": "smelters"})        # a call over RCON counts as connected
    assert mod.lua.eval(status) == "Skippy is thinking: smelters"
    mod.run("game.tick = game.tick + 60 * 31")
    mod.result("set_state", {"state": "idle"})
    assert mod.lua.eval(status) == "Skippy is idle"


def test_panel_type_drives_the_same_path_and_the_bridge_answers_in_the_panel(mod):
    r = mod.result("panel_type", {"text": "hello Skippy"})
    assert r["player"] == "captain"
    from copilot.agent import Agent
    from copilot.tools import LocalTools
    from fakes import FakeModel
    game = LuaGame(mod)
    bridge = Bridge(game, Agent(game, FakeModel(["Hello, Captain."]), local=LocalTools(game)), LocalTools(game), out=lambda *a: None)
    bridge.chat_at = 0
    bridge.step()
    kinds = [(l["kind"], l["text"]) for l in mod.result("panel_read")["lines"]]
    assert kinds == [("panel", "hello Skippy"), ("skippy", "Hello, Captain.")]
    assert mod.call("panel_type", {"text": "  "})["ok"] is False


def test_the_model_is_not_offered_the_panel_tools():
    from copilot.toolbox import BRIDGE_ONLY
    assert {"panel_type", "panel_read", "bridge_settings"} <= BRIDGE_ONLY


def test_not_connected_says_it_joins_by_itself(mod):
    assert "joins by itself" in mod.lua.eval(panel(mod) + ".skippy_status.caption")


def test_the_ai_set_in_the_game_is_what_the_bridge_uses(mod):
    """The Captain, 2026-11-21: a configurable Ollama address in the game, and the bridge connects to it by itself."""
    from copilot.__main__ import from_game
    game = LuaGame(mod)
    env = {"COPILOT_SOURCE": "purple", "COPILOT_QUICK_URL": "http://core"}
    assert from_game(env, game) == (env, None)                                  # nothing set: the bridge's own source
    mod.run("settings.global['skippy-ai-url'] = { value = 'localhost:11434' } settings.global['skippy-ai-model'] = { value = 'qwen3:14b' }")
    got, chosen = from_game(env, game)
    assert (got["COPILOT_SOURCE"], got["COPILOT_URL"], got["COPILOT_MODEL"], got["COPILOT_QUICK_URL"]) == ("ollama", "http://localhost:11434", "qwen3:14b", "")
    assert chosen == ("localhost:11434", "qwen3:14b") and env["COPILOT_SOURCE"] == "purple"          # the env passed in is untouched
    mod.run("settings.global['skippy-ai-model'] = { value = '' }")
    assert from_game(env, game)[0]["COPILOT_MODEL"] == "qwen3:8b"
