"""Speech in the game (the Captain, 2026-11-13: speech to text and text to speech in the game, in purple Skippy's
voice). The mod has no microphone, speaker or network, and this bridge holds no key to the house's voice, so the
house's own listener does the hearing and the speaking. The bridge offers it a small door on this computer: spoken
lines come in and count like typed ones, and everything Skippy says goes out to be spoken."""
import json
import threading
import time
import urllib.error
import urllib.request

import pytest

import copilot.__main__ as main
from copilot.agent import Agent
from copilot.loop import Bridge
from copilot.toolbox import Toolbox
from copilot.tools import LocalTools
from copilot.voice_door import MAX_TEXT, PORT, VoiceDoor
from fake_purple import FakePurple
from fakes import FakeModel
from luamod import LuaMod
from test_bridge_with_mod import LuaGame
from test_goals import LoopGame


def http(method, url, body=None):
    req = urllib.request.Request(url, data=None if body is None else (body if isinstance(body, bytes) else json.dumps(body).encode()), method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


@pytest.fixture
def door():
    d = VoiceDoor(port=0)
    d.url = d.serve()
    yield d
    d.stop()


# ---------------------------------------------------------------- the door itself, over real HTTP

def test_the_door_listens_on_this_computer_only_and_says_it_is_there(door):
    assert door.url.startswith("http://127.0.0.1:") and PORT == 47862
    assert http("GET", door.url + "/health") == (200, {"ok": True, "service": "skippy-factorio", "heard": 0, "said": 0})
    assert http("GET", door.url + "/nope")[0] == 404 and http("POST", door.url + "/nope", {})[0] == 404


def test_a_spoken_line_comes_in_and_waits_for_the_bridge(door):
    status, got = http("POST", door.url + "/hear", {"text": "  Skippy,  build   more furnaces ", "who": "captain"})
    assert (status, got) == (200, {"ok": True, "id": 1, "after": 0})
    http("POST", door.url + "/hear", {"text": "x" * 5000})
    taken = door.take()
    assert taken[0] == {"id": 1, "text": "Skippy, build more furnaces", "who": "captain"} and len(taken[1]["text"]) == MAX_TEXT
    assert door.take() == []                                                         # each line is handed over once


def test_what_is_not_a_spoken_line_is_refused(door):
    assert http("POST", door.url + "/hear", {"text": "   "}) == (400, {"ok": False, "error": "there was no text"})
    assert http("POST", door.url + "/hear", b"not json")[0] == 400
    assert http("POST", door.url + "/hear", ["a list"])[0] == 400
    assert http("POST", door.url + "/hear", {"text": "y" * 30000})[0] == 413
    assert http("GET", door.url + "/said?after=soon")[0] == 400
    assert door.take() == []


def test_what_skippy_says_goes_out_once_each_in_order(door):
    door.spoke("Four furnaces fit west of the ore.")
    door.spoke("One file changed.", "purple")
    status, got = http("GET", door.url + "/said?after=0")
    assert got == {"lines": [{"id": 1, "text": "Four furnaces fit west of the ore.", "voice": "skippy"}, {"id": 2, "text": "One file changed.", "voice": "purple"}], "next": 2}
    assert http("GET", door.url + "/said?after=2")[1] == {"lines": [], "next": 2}
    assert http("GET", door.url + "/said?after=1")[1]["lines"][0]["id"] == 2


def test_asking_for_news_waits_for_it_instead_of_asking_again_and_again(door):
    threading.Timer(0.3, lambda: door.spoke("Done.")).start()
    started = time.time()
    status, got = http("GET", door.url + "/said?after=0&wait=5")
    assert got["lines"][0]["text"] == "Done." and 0.1 < time.time() - started < 10
    started = time.time()
    assert http("GET", door.url + "/said?after=1&wait=0.3")[1] == {"lines": [], "next": 1} and time.time() - started < 10


def test_hear_tells_the_listener_where_the_answer_will_start(door):
    door.spoke("old news")
    got = http("POST", door.url + "/hear", {"text": "what next?"})[1]
    door.spoke("Iron first.")
    assert [l["text"] for l in http("GET", door.url + "/said?after=%d" % got["after"])[1]["lines"]] == ["Iron first."]


# ---------------------------------------------------------------- in the game: a spoken line is a line

def test_a_spoken_line_is_shown_and_counted_like_a_typed_one():
    mod = LuaMod()
    mod.run("fake.add_player('captain', 0, 0)")
    got = mod.result("hear", {"text": "  what should we do next?  "})
    assert got == {"id": 1, "player": "captain"}
    line = mod.result("chat_read")["lines"][0]
    assert (line["id"], line["player"], line["text"], line["by"]) == (1, "captain", "what should we do next?", "voice")
    assert "[captain, by voice][/color] what should we do next?" in mod.printed()[-1]
    assert mod.lua.eval("game.players[1].gui.top.skippy_light.skippy_prompts.caption") == "1 prompt"
    assert "nothing said" in mod.call("hear", {"text": "   "})["error"]
    assert mod.result("hear", {"text": "hi", "player": "someone-not-here"})["player"] == "captain"
    assert LuaMod().result("hear", {"text": "anyone?"})["player"] == "player"            # nobody in the game


def test_the_model_is_not_offered_the_ear():
    game = LuaGame(LuaMod())
    assert "hear" not in Toolbox(game, LocalTools(game)).names


# ---------------------------------------------------------------- the loop: heard, answered, spoken

def test_spoken_in_answered_in_chat_and_handed_to_the_speaker():
    mod = LuaMod()
    mod.run("fake.add_player('captain', 0, 0)")
    door = VoiceDoor(port=0)
    game = door.wrap(LuaGame(mod))
    tools = LocalTools(game)
    bridge = Bridge(game, Agent(game, FakeModel(["Iron first, then copper."]), local=tools), tools, clock=lambda: 1000.0, out=lambda *a: None, voice=door)
    got = door.hear("what should we do next?", "captain")
    bridge.step()
    shown = mod.printed()
    assert "[captain, by voice][/color] what should we do next?" in shown[-2] and "[Skippy][/color] Iron first, then copper." in shown[-1]
    assert door.said_after(got["after"])["lines"] == [{"id": 1, "text": "Iron first, then copper.", "voice": "skippy"}]
    bridge.step()
    assert len(door.said_after(0)["lines"]) == 1                                     # answered once


def test_everything_skippy_says_is_handed_to_the_speaker_typed_or_not():
    door = VoiceDoor(port=0)
    inner = LoopGame()
    game = door.wrap(inner)
    tools = LocalTools(game)
    fake = FakePurple(script=[{"text": "One line changed.", "done": True, "ok": True}])
    bridge = Bridge(game, Agent(game, FakeModel(["Copper is short."]), local=tools), tools, clock=lambda: 1000.0, out=lambda *a: None, voice=door, purple=fake.client())
    inner.type("what is wrong?")
    inner.chat.append({"id": 2, "player": "captain", "text": "fix the light", "to": "purple"})
    bridge.step()
    assert [(l["text"], l["voice"]) for l in door.said_after(0)["lines"]] == [("Copper is short.", "skippy"), ("One line changed.", "purple")]
    assert game.said() == inner.said()                                               # the wrapped game is still the game


def test_a_game_that_cannot_take_a_spoken_line_still_gets_it_answered():
    door = VoiceDoor(port=0)
    inner = LoopGame()
    inner.results["hear"] = {"ok": False, "error": "there is no tool named 'hear'"}      # an older mod
    game = door.wrap(inner)
    tools = LocalTools(game)
    bridge = Bridge(game, Agent(game, FakeModel(["Iron first."]), local=tools), tools, clock=lambda: 1000.0, out=lambda *a: None, voice=door)
    door.hear("what next?")
    bridge.step()
    assert inner.said() == ["Iron first."] and door.said_after(0)["lines"][0]["text"] == "Iron first."


def test_without_a_door_nothing_changes():
    game = LoopGame()
    tools = LocalTools(game)
    bridge = Bridge(game, Agent(game, FakeModel(["Iron first."]), local=tools), tools, clock=lambda: 1000.0, out=lambda *a: None)
    game.type("what next?")
    bridge.step()
    assert game.said() == ["Iron first."] and game.named("hear") == []


# ---------------------------------------------------------------- settings

def test_the_door_can_be_moved_or_switched_off_and_a_taken_port_does_not_stop_the_bridge():
    said = []
    out = lambda *a, **k: said.append(" ".join(str(x) for x in a))
    assert main.voice_door({"COPILOT_VOICE_PORT": "off"}, out) is None and said == []
    d = main.voice_door({"COPILOT_VOICE_PORT": "0"}, out)
    try:
        assert d is not None and "voice door: http://127.0.0.1:" in said[0] and http("GET", "http://127.0.0.1:%d/health" % d.port)[0] == 200
        assert main.voice_door({"COPILOT_VOICE_PORT": str(d.port)}, out) is None        # taken
        assert "could not be opened" in said[-1] and "Typing in the game still works" in said[-1]
    finally:
        d.stop()
    assert main.voice_door({"COPILOT_VOICE_PORT": "seven"}, out) is None
    assert "COPILOT_VOICE_PORT" in main.__doc__ and "COPILOT_VOICE_PORT" in (main.HERE / "copilot.env.example").read_text(encoding="utf-8")


def test_no_key_to_the_houses_voice_is_in_this_repository():
    for f in list(main.HERE.glob("*.py")) + [main.HERE / "copilot.env.example"]:
        src = f.read_text(encoding="utf-8")
        assert "SKIPPY_HOME_TOKEN" not in src and "/stt" not in src.replace("speech to text", "") or f.name == "voice_door.py", f.name
