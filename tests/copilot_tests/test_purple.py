"""Purple Skippy through its MCP door (the Captain's instructions, 2026-11-13). Purple is the development agent: every
call is a task, the work is a job of seconds to minutes, and the game never waits on it. The mod's Lua cannot call out,
so /purple in the game only writes the request down; the bridge passes it on and brings the words back.
A stand-in door answers here; nothing real is called."""
import json
import pathlib
import socket

import pytest

from copilot.agent import Agent
from copilot.loop import PURPLE_TASK, Bridge
from copilot.purple_client import MIN_POLL, PurpleClient, PurpleError
from copilot.tools import LocalTools
from fake_purple import FakePurple
from fakes import FakeModel
from luamod import LuaMod
from test_bridge_with_mod import LuaGame
from test_goals import LoopGame

ROOT = pathlib.Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------- the client, against a real local HTTP server

@pytest.fixture
def door():
    made = []

    def make(**kw):
        f = FakePurple(**kw)
        made.append(f)
        return f, PurpleClient(f.serve(), kw.get("key") or "")
    yield make
    for f in made:
        f.stop()


def test_start_then_poll_to_done(door):
    fake, c = door()
    assert c.health() == (True, "ready")
    got = c.ask("how much iron for a gear?", conv="conv-12345", project="f-ai-factorio", wait_s=5)
    assert (got["task"], got["conv"], got["done"], got["next"]) == ("task-1", "conv-12345", False, 1)
    more = c.result(got["task"], got["next"], wait_s=5)
    assert (more["text"], more["done"], more["ok"]) == ("Two iron plates.", True, True)
    assert fake.methods == ["initialize", "tools/call", "tools/call"]                # one handshake, then plain calls
    assert fake.asked == [{"message": "how much iron for a gear?", "conv": "conv-12345", "project": "f-ai-factorio", "wait_s": 5}]
    assert fake.polled == [{"task": "task-1", "after": 1, "wait_s": 5}]


def test_run_to_completion_gathers_the_text_and_reports_each_piece(door):
    fake, c = door(script=[{"text": "Looking.", "done": False}, {"text": "", "done": False}, {"text": "Done: one file changed.", "done": True, "ok": True, "steps": 4}])
    heard, slept = [], []
    got = c.run_to_completion("fix it", "conv-12345", heard.append, sleep=slept.append)
    assert got == {"text": "Looking.\nDone: one file changed.", "steps": 4, "ok": True, "error": None, "task": "task-1", "conv": "conv-12345"}
    assert heard == ["Looking.", "Done: one file changed."] and slept == [3.0, 3.0]
    assert [p["after"] for p in fake.polled] == [1, 2]
    c.run_to_completion("again", sleep=slept.append, poll=0.1)
    assert slept[-1] == MIN_POLL                                                     # never faster than every two seconds


def test_busy_is_waited_out_slowly_and_then_given_up(door):
    fake, c = door(busy=2)
    slept = []
    assert c.run_to_completion("q", sleep=slept.append)["text"] == "Two iron plates."
    assert slept[:2] == [10, 10] and len(fake.asked) == 3
    fake2, c2 = door(busy=99)
    ticks = iter(range(0, 10000, 200))
    with pytest.raises(PurpleError, match="busy with another job"):
        c2.run_to_completion("q", sleep=lambda s: None, clock=lambda: next(ticks), busy_wait=300)
    assert c2.ask("q") == {"busy": True, "message": "purple is on another job"}       # a plain ask just says so


def test_a_failed_run_and_a_failed_call_are_told_apart(door):
    fake, c = door(script=[{"text": "I started", "done": True, "ok": False, "error": "Claude Code went quiet"}])
    got = c.run_to_completion("q", sleep=lambda s: None)
    assert got["ok"] is False and got["error"] == "Claude Code went quiet" and got["text"] == "I started"
    fake2, c2 = door(tool_error="unknown project 'nope'")
    with pytest.raises(PurpleError, match="could not do that: unknown project 'nope'"):
        c2.ask("q", project="nope")
    fake3, c3 = door(rpc_error="method not found")
    with pytest.raises(PurpleError, match="refused the call: method not found"):
        c3.ask("q")


def test_a_run_that_takes_too_long_is_cancelled(door):
    fake, c = door(script=[{"text": "", "done": False}])
    ticks = iter(range(0, 100000, 700))
    with pytest.raises(PurpleError, match="over 30 minutes; it has been stopped"):
        c.run_to_completion("q", sleep=lambda s: None, clock=lambda: next(ticks))
    assert fake.cancelled == ["task-1"]
    assert c.cancel("task-1") is True


def test_a_dead_server_is_said_plainly_and_never_raises_from_health_or_cancel():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()                                                                        # nothing listens here now
    c = PurpleClient("http://127.0.0.1:%d/mcp" % port, timeout=3)
    ready, why = c.health()
    assert not ready and "could not be reached" in why and "Is purple-mcp running" in why
    with pytest.raises(PurpleError, match="could not be reached"):
        c.ask("q")
    assert c.cancel("t") is False


def test_away_from_this_computer_the_door_wants_its_key_and_only_that_key(door):
    fake, c = door(key="door-key")
    assert c.ask("q")["task"] == "task-1"
    with pytest.raises(PurpleError, match="needs its key"):
        PurpleClient(c.url).ask("q")
    assert fake.asked and "Authorization" not in PurpleClient(c.url)._headers()        # on loopback nothing is sent


# ---------------------------------------------------------------- /purple in the game

@pytest.fixture
def mod():
    m = LuaMod()
    m.run("fake.add_player('captain', 0, 0)")
    return m


def purple_cmd(mod, text, player=1):
    mod.run("fake.commands['purple'] { parameter = %s, player_index = %s, tick = game.tick }" % (json.dumps(text), player or "nil"))


def test_slash_purple_writes_the_request_down_for_the_bridge(mod):
    purple_cmd(mod, "  make the light say hello  ")
    mod.fake.chat(1, "what next?")
    lines = mod.result("chat_read")["lines"]
    assert [(l["text"], l.get("to"), l["player"]) for l in lines] == [("make the light say hello", "purple", "captain"), ("what next?", None, "captain")]
    assert "[purple][/color] asked: make the light say hello" in "\n".join(mod.printed())


def test_slash_purple_is_for_admins_and_needs_words(mod):
    mod.run("game.players[1].admin = false")
    purple_cmd(mod, "do something")
    mod.run("game.players[1].admin = true")
    purple_cmd(mod, "   ")
    assert mod.result("chat_read")["lines"] == {} or mod.result("chat_read")["lines"] == []
    text = "\n".join(mod.printed())
    assert "Only admins can hand tasks to purple Skippy." in text and "Say what purple Skippy should do" in text


def test_purples_words_are_marked_as_purples(mod):
    mod.result("say", {"text": "one file changed", "as": "purple"})
    mod.result("say", {"text": "hello"})
    out = mod.printed()
    assert "[purple][/color] one file changed" in out[-2] and "[Skippy][/color] hello" in out[-1]


def test_the_game_side_makes_no_calls_out():
    for f in (ROOT / "mods" / "skippy-copilot").rglob("*.lua"):
        src = f.read_text(encoding="utf-8")
        assert "47860" not in src and "http://" not in src, "%s reaches outside the game" % f.name


# ---------------------------------------------------------------- the loop: a job in the background

class Clock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def loop(fake, replies=()):
    game = LoopGame()
    tools = LocalTools(game)
    agent = Agent(game, FakeModel(list(replies)), local=tools)
    clock = Clock()
    return game, Bridge(game, agent, tools, clock=clock, out=lambda *a: None, purple=fake.client(), purple_project="f-ai-factorio"), clock


def ask_purple(game, text):
    game.chat.append({"id": len(game.chat) + 1, "player": "captain", "text": text, "to": "purple"})


def purple_said(game):
    return [a["text"] for a in game.named("say") if a.get("as") == "purple"]


def test_a_task_is_started_at_once_and_its_words_come_back_between_other_work():
    fake = FakePurple(script=[{"text": "", "done": False}, {"text": "Reading the mod.", "done": False}, {"text": "Changed one line; tests pass.", "done": True, "ok": True, "steps": 3}])
    game, bridge, clock = loop(fake, ["Iron first."])
    ask_purple(game, "make the light say hello")
    bridge.step()
    assert fake.asked[0]["wait_s"] == 0 and fake.asked[0]["project"] == "f-ai-factorio"       # the loop does not wait
    assert bridge.purple_job["task"] == "task-1" and purple_said(game) == [] and fake.polled == []
    bridge.step()                                                                    # at once again: too soon to ask
    assert fake.polled == []
    clock.t += 3
    game.type("what should we do?")                                                  # the assistant still answers meanwhile
    bridge.step()
    assert game.said()[0] == "Iron first." and purple_said(game) == ["Reading the mod."]
    assert fake.polled[0] == {"task": "task-1", "after": 1, "wait_s": 0}
    clock.t += 3
    bridge.step()
    assert purple_said(game) == ["Reading the mod.", "Changed one line; tests pass."] and bridge.purple_job is None
    clock.t += 30
    bridge.step()
    assert len(fake.polled) == 2                                                     # nothing more is asked once it is done


def test_the_task_carries_the_rules_and_one_conversation():
    fake = FakePurple(script=[{"text": "ok", "done": True, "ok": True}])
    game, bridge, clock = loop(fake)
    ask_purple(game, "add a test")
    bridge.step()
    sent = fake.asked[0]["message"]
    assert "comes from a player inside a running Factorio game" in sent and sent.endswith("The request, from captain: add a test")
    assert "mods/skippy-copilot" in sent and "copilot/" in sent and "Touch nothing else" in sent
    assert "Do not restart, reload or stop the game server" in sent and "unless the request asks for exactly that" in sent
    assert "conv" not in fake.asked[0]                                               # a new conversation the first time
    ask_purple(game, "and another")
    bridge.step()
    assert fake.asked[1]["conv"] == "mcp-new"                                        # then the same one
    assert PURPLE_TASK.count("%s") == 2


def test_busy_one_at_a_time_and_stop():
    fake = FakePurple(busy=1, script=[{"text": "", "done": False}])
    game, bridge, clock = loop(fake)
    ask_purple(game, "first")
    bridge.step()
    assert purple_said(game) == ["busy with another job right now. Ask again in a while."] and bridge.purple_job is None
    ask_purple(game, "first again")
    ask_purple(game, "second")
    bridge.step()
    assert purple_said(game)[-1] == "still working on the last task. Type /purple stop to end it." and len(fake.asked) == 2
    ask_purple(game, "Stop")
    bridge.step()
    assert fake.cancelled == ["task-1"] and purple_said(game)[-1] == "stopped." and bridge.purple_job is None
    ask_purple(game, "stop")
    bridge.step()
    assert purple_said(game)[-1] == "nothing of mine is running."


def test_failure_a_dead_door_and_a_run_that_never_ends_are_all_said_once():
    fake = FakePurple(script=[{"text": "", "done": False}, {"text": "", "done": True, "ok": False, "error": "Claude Code went quiet"}])
    game, bridge, clock = loop(fake)
    ask_purple(game, "x")
    bridge.step()
    clock.t += 3
    bridge.step()
    assert purple_said(game) == ["that did not finish: Claude Code went quiet"]

    dead = FakePurple(up=False)
    game, bridge, clock = loop(dead)
    ask_purple(game, "x")
    bridge.step()
    assert "could not be reached" in purple_said(game)[0] and bridge.purple_job is None

    fake = FakePurple(script=[{"text": "", "done": False}])
    game, bridge, clock = loop(fake)
    ask_purple(game, "x")
    bridge.step()
    fake.up = False                                                                  # the door goes away mid-run
    for _ in range(5):
        clock.t += 3
        bridge.step()
    assert len(purple_said(game)) == 1 and "I lost touch with the run" in purple_said(game)[0] and bridge.purple_job is None

    fake = FakePurple(script=[{"text": "", "done": False}])
    game, bridge, clock = loop(fake)
    ask_purple(game, "x")
    bridge.step()
    clock.t += 1801
    bridge.step()
    assert fake.cancelled == ["task-1"] and purple_said(game) == ["that took over 30 minutes, so I stopped it."]


def test_a_quiet_run_ends_with_done_and_long_words_are_cut():
    fake = FakePurple(script=[{"text": "", "done": True, "ok": True}])
    game, bridge, clock = loop(fake)
    ask_purple(game, "x")
    bridge.step()
    assert purple_said(game) == ["done."]
    fake = FakePurple(script=[{"text": "y" * 5000, "done": True, "ok": True}])
    game, bridge, clock = loop(fake)
    ask_purple(game, "x")
    bridge.step()
    assert sum(len(t) for t in purple_said(game)) == 764 and purple_said(game)[-1].endswith(" ...")


def test_without_a_door_slash_purple_says_so_and_a_task_is_never_given_to_the_model():
    game = LoopGame()
    tools = LocalTools(game)
    agent = Agent(game, FakeModel([]), local=tools)                                  # a model that would fail if asked
    bridge = Bridge(game, agent, tools, clock=lambda: 1000.0, out=lambda *a: None)
    ask_purple(game, "x")
    bridge.step()
    assert purple_said(game) == ["purple Skippy is not connected to this bridge."]


def test_the_whole_path_from_the_command_in_the_game_to_purples_words_in_chat():
    m = LuaMod()
    m.run("fake.add_player('captain', 0, 0)")
    game = LuaGame(m)
    tools = LocalTools(game)
    fake = FakePurple(script=[{"text": "The light now says hello.", "done": True, "ok": True, "steps": 2}])
    bridge = Bridge(game, Agent(game, FakeModel([]), local=tools), tools, clock=lambda: 1000.0, out=lambda *a: None, purple=fake.client())
    purple_cmd(m, "make the light say hello")
    bridge.step()
    assert "[purple][/color] The light now says hello." in m.printed()[-1]
    assert "make the light say hello" in fake.asked[0]["message"]


def test_on_plain_chat_purple_decides_whether_it_is_the_game_or_the_code():
    from copilot.purple import TURN
    assert "You decide what kind of request it is" in TURN and "factorio-copilot skill" in TURN and "skippy-copilot MCP server" in TURN
    assert "mods/skippy-copilot, copilot/ and tests/copilot_tests" in TURN and "do not restart, reload or stop the game server" in TURN
    assert "ask the player in one sentence before changing anything" in TURN and TURN.count("%s") == 1
