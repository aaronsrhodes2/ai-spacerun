"""One AI source for every turn (the Captain, 2026-11-13): purple Skippy in a workspace, or one model behind one address
and one key. And a setup a newcomer can get through: a step-by-step check, plain errors, a light in the game that says
when nothing is connected."""
import json
import pathlib

import pytest

import copilot.__main__ as main
from copilot import check, mcp_server
from copilot.agent import Agent
from copilot.loop import Bridge
from copilot.purple import Purple, PurpleAgent, SourceError
from copilot.toolbox import BRIDGE_ONLY, PLAN_ONLY, Toolbox
from copilot.tools import LocalTools
from fake_purple import FakePurple
from fakes import FakeGame, FakeModel
from luamod import LuaMod
from test_bridge_with_mod import LuaGame

ROOT = pathlib.Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------- purple Skippy's door, faked (see test_purple.py for the door itself)

def FakeBridge(events=None, busy=0, status=200, ready=True, ok=True, error=None):
    """A stand-in door with a run that answers 'Two iron plates.' after one step, or the script given."""
    if events is not None:
        script = [{"text": t, "done": False} for t in events[:-1]] + [{"text": events[-1], "done": True, "ok": ok, "error": error}]
    else:
        script = None
    return FakePurple(script=script, busy=busy, up=ready, tool_error={503: "purple is not ready: no login", 400: "unknown project 'ai-factorio'"}.get(status))


def purple(door, **kw):
    return Purple(None, "", "ai-factorio", client=door.client(), sleep=lambda s: None, **kw)


def test_a_turn_goes_to_purple_in_its_workspace_and_the_answer_comes_back():
    b = FakeBridge()
    got = purple(b).ask("how much iron for a gear?", "conv-12345")
    assert got == {"text": "Two iron plates.", "steps": 1, "ok": True, "error": None}
    sent = b.asked[0]
    assert (sent["conv"], sent["project"], sent["message"]) == ("conv-12345", "ai-factorio", "how much iron for a gear?")
    assert b.polled[0]["after"] == 1


def test_it_waits_while_purple_is_busy_with_someone_else():
    b = FakeBridge(busy=2)
    slept = []
    p = Purple(None, "", "ai-factorio", client=b.client(), sleep=slept.append)
    assert p.ask("q", "c")["text"] == "Two iron plates." and len(b.asked) == 3 and slept[:2] == [10, 10]
    with pytest.raises(SourceError, match="busy with another job"):
        Purple(None, "", "ai-factorio", client=FakeBridge(busy=99).client(), sleep=lambda s: None, busy_wait=-1).ask("q", "c")


def test_refusals_from_the_door_are_said_plainly():
    with pytest.raises(SourceError, match="not ready"):
        purple(FakeBridge(status=503)).ask("q", "c")
    with pytest.raises(SourceError, match="unknown project 'ai-factorio'"):
        purple(FakeBridge(status=400)).ask("q", "c")
    with pytest.raises(SourceError, match="Is purple-mcp running"):
        purple(FakeBridge(ready=False)).ask("q", "c")


def test_purple_needs_a_workspace_but_no_key_on_this_computer():
    with pytest.raises(SourceError, match="needs a workspace"):
        Purple("http://x", "", "")
    p = Purple(None, "", "w")
    assert p.url == "http://127.0.0.1:47860/mcp" and p.client.key == ""


def test_health_says_whether_purples_door_is_open():
    assert purple(FakeBridge()).health() == (True, "ready")
    ready, why = purple(FakeBridge(ready=False)).health()
    assert not ready and "could not be reached" in why


def test_a_run_that_fails_is_not_an_answer():
    got = purple(FakeBridge(events=["I started..."], ok=False, error="Claude Code went quiet")).ask("q", "c")
    assert got["ok"] is False and got["error"] == "Claude Code went quiet"


# ---------------------------------------------------------------- purple as the thing that thinks

def purple_agent(bridge, game=None, log=None):
    game = game or FakeGame()
    return PurpleAgent(game, purple(bridge), Toolbox(game, None, log), conv="conv-1"), game


def test_purple_stands_where_the_agent_stands():
    agent, game = purple_agent(FakeBridge())
    answer, outcome, stats = agent.handle("how much iron for a gear?")
    assert (answer, outcome, stats["calls"], stats["misses"]) == ("Two iron plates.", "answered", 1, 0)
    assert [a["state"] for a in game.named("set_state")] == ["thinking", "idle"]
    assert agent.model.model == "purple Skippy in workspace 'ai-factorio'" and "lookup" in agent.names


def test_every_turn_goes_to_the_same_conversation_with_the_skill_named_and_the_alerts_attached():
    b = FakeBridge()
    alerts = {"ok": True, "result": {"alerts": [{"surface": "nauvis", "kind": "no_power", "count": 3, "means": "not connected to power"}]}}
    game = FakeGame({"alerts": alerts})
    game.tools = lambda: FakeGame().tools() + [{"name": "alerts", "description": "a", "parameters": {}}]
    agent = PurpleAgent(game, purple(b), Toolbox(game), conv="conv-7")
    agent.handle("what is wrong?")
    msg = b.asked[0]["message"]
    assert b.asked[0]["conv"] == "conv-7" and "factorio-copilot skill" in msg and "skippy-copilot MCP server" in msg
    assert "what is wrong?" in msg and "no_power x3 on nauvis (not connected to power)" in msg


def test_a_source_that_cannot_answer_is_reported_with_the_reason(tmp_path):
    agent, game = purple_agent(FakeBridge(status=503), log=tmp_path / "run.jsonl")
    answer, outcome, stats = agent.handle("q")
    assert answer is None and outcome == "source error" and "not ready" in agent.last_error
    assert game.named("set_state")[-1] == {"state": "failed", "note": "source error"}
    events = [json.loads(l) for l in (tmp_path / "run.jsonl").read_text().splitlines()]
    assert [e["event"] for e in events] == ["request", "error", "answer"] and events[-1]["outcome"] == "source error"


def test_the_loop_runs_on_purple_exactly_as_on_a_plain_model():
    from test_goals import LoopGame
    game = LoopGame()
    tools = LocalTools(game)
    agent = PurpleAgent(game, purple(FakeBridge(events=["Iron first."])), Toolbox(game, tools))
    bridge = Bridge(game, agent, tools, clock=lambda: 1000.0, out=lambda *a: None)
    game.type("what should we do?")
    bridge.step()
    assert game.said() == ["Iron first."]


# ---------------------------------------------------------------- the tools over MCP

def rpc(server, method, params=None, msg_id=1):
    return server.handle({"jsonrpc": "2.0", "id": msg_id, "method": method, "params": params or {}})


@pytest.fixture
def mcp(tmp_path):
    mod = LuaMod()
    game = LuaGame(mod)
    return mod, mcp_server.Server(Toolbox(game, LocalTools(game), tmp_path / "mcp.jsonl")), tmp_path


def test_mcp_initialize_and_tool_list(mcp):
    mod, server, _ = mcp
    init = rpc(server, "initialize")["result"]
    assert init["serverInfo"]["name"] == "skippy-copilot" and "tools" in init["capabilities"]
    tools = {t["name"]: t for t in rpc(server, "tools/list")["result"]["tools"]}
    assert {"lookup", "map", "bottlenecks", "plan_row", "build_plan", "set_goal", "milestones", "joints", "queue_research"} <= set(tools)
    assert not (BRIDGE_ONLY | PLAN_ONLY) & set(tools)                               # the channel and the raw calls stay with the bridge
    assert tools["lookup"]["inputSchema"]["required"] == ["name"] and tools["lookup"]["inputSchema"]["properties"]["name"]["type"] == "string"


def test_mcp_tool_calls_reach_the_game_and_are_logged(mcp):
    mod, server, tmp = mcp
    out = rpc(server, "tools/call", {"name": "lookup", "arguments": {"name": "iron-gear-wheel", "kind": "recipe"}})["result"]
    assert out["isError"] is False and json.loads(out["content"][0]["text"])["result"][0]["ingredients"][0]["name"] == "iron-plate"
    bad = rpc(server, "tools/call", {"name": "lookup", "arguments": {"nam": "x"}})["result"]
    assert bad["isError"] is True and "no parameter 'nam'" in bad["content"][0]["text"]
    kept = rpc(server, "tools/call", {"name": "say", "arguments": {"text": "hi"}})["result"]
    assert kept["isError"] is True and "no tool named 'say'" in kept["content"][0]["text"]
    log = [json.loads(l) for l in (tmp / "mcp.jsonl").read_text().splitlines()]
    assert [(e["name"], e["ok"]) for e in log] == [("lookup", True), ("lookup", False), ("say", False)]


def test_mcp_planning_tools_work_through_the_same_door(mcp):
    mod, server, _ = mcp
    plan = json.loads(rpc(server, "tools/call", {"name": "plan_row", "arguments": {"machine": "assembling-machine-2", "count": 2, "x": 0, "y": 0}})["result"]["content"][0]["text"])
    built = json.loads(rpc(server, "tools/call", {"name": "build_plan", "arguments": {"plan_id": plan["result"]["plan_id"]}})["result"]["content"][0]["text"])
    assert plan["ok"] and built["ok"] and built["result"]["would_place"] == 18


def test_mcp_protocol_edges(mcp):
    mod, server, _ = mcp
    assert server.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None
    assert rpc(server, "ping")["result"] == {}
    assert rpc(server, "resources/list")["error"]["code"] == -32601
    written = []
    mcp_server.serve(server, ['{"jsonrpc":"2.0","id":5,"method":"ping"}', "", "not json", '{"jsonrpc":"2.0","method":"notifications/initialized"}'], written.append)
    assert [json.loads(w).get("id") for w in written] == [5, None] and json.loads(written[1])["error"]["code"] == -32700


def test_a_huge_result_is_cut_for_an_agent_too(mcp):
    mod, server, _ = mcp
    server.toolbox.call = lambda name, args: {"ok": True, "result": "x" * 50000}
    text = rpc(server, "tools/call", {"name": "lookup", "arguments": {}})["result"]["content"][0]["text"]
    assert len(text) < mcp_server.MAX_RESULT + 100 and text.endswith("ask for less at a time)")


# ---------------------------------------------------------------- one goal and one set of plans, whoever is talking

def test_a_goal_set_through_one_door_is_seen_through_the_other():
    mod = LuaMod()
    bridge_side, agent_side = LocalTools(LuaGame(mod)), LocalTools(LuaGame(mod))     # two processes in real life
    agent_side.call("set_goal", {"kind": "place", "place": "nauvis"})
    assert bridge_side.goal is None
    bridge_side.sync_goal()
    assert bridge_side.goal.describe() == "solve Nauvis"
    assert mod.result("goal_state")["goal"] == {"kind": "place", "value": "nauvis"}
    agent_side.call("clear_goal", {})
    bridge_side.sync_goal()
    assert bridge_side.goal is None and mod.result("goal_state")["goal"] == {"kind": "none"}


def test_syncing_does_not_reset_a_goal_that_has_not_changed():
    mod = LuaMod()
    tools = LocalTools(LuaGame(mod))
    tools.call("set_goal", {"kind": "science", "per_minute": 1000})
    tools.goal.turns = 5
    tools.sync_goal()
    assert tools.goal.turns == 5 and tools.goal.describe() == "make 1000 of every science pack a minute"


def test_the_loop_takes_turns_on_a_goal_that_an_agent_set_over_mcp():
    mod = LuaMod()
    game = LuaGame(mod)
    tools = LocalTools(game)
    agent = Agent(game, FakeModel([[("diagnose", {})], "Placed the first furnaces."]), local=tools)
    bridge = Bridge(game, agent, tools, clock=lambda: 1000.0, out=lambda *a: None)
    LocalTools(LuaGame(mod)).call("set_goal", {"kind": "milestone", "milestone": "first-plates"})        # the other door
    bridge.step()
    assert tools.goal is not None and tools.goal.turns == 1


def test_plans_survive_a_restart_of_the_tool_server(tmp_path):
    mod = LuaMod()
    store = tmp_path / "plans.json"
    first = LocalTools(LuaGame(mod), plan_store=store)
    pid = first.call("plan_row", {"machine": "assembling-machine-2", "count": 1, "x": 0, "y": 0})["result"]["plan_id"]
    first.call("build_plan", {"plan_id": pid})
    second = LocalTools(LuaGame(mod), plan_store=store)                             # a new process: the next turn
    assert second.call("build_plan", {"plan_id": pid, "dry_run": False})["result"]["placed"] == 9      # the dry run it passed is remembered
    assert second.call("plan_row", {"machine": "assembling-machine-2", "count": 1, "x": 9, "y": 0})["result"]["plan_id"] == "plan-2"
    assert LocalTools(LuaGame(mod), plan_store=tmp_path / "missing.json").plans == {}


# ---------------------------------------------------------------- settings: one source, said plainly

def test_exactly_one_source_is_configured():
    assert main.source_of({"COPILOT_SOURCE": "Purple"}) == "purple"
    assert main.source_of({"COPILOT_PROVIDER": "ollama"}) == "ollama"                # the older name still works
    with pytest.raises(main.SetupError, match="no AI source is set.*anthropic, openai, ollama, purple"):
        main.source_of({})
    with pytest.raises(main.SetupError, match="'claude'; it must be one of"):
        main.source_of({"COPILOT_SOURCE": "claude"})


def test_a_secret_can_be_given_as_a_file(tmp_path):
    f = tmp_path / "key.txt"
    f.write_text("s3cret\n", encoding="utf-8")
    assert main.secret({"COPILOT_KEY_FILE": str(f)}, "COPILOT_KEY") == "s3cret"
    assert main.secret({"COPILOT_KEY": "direct", "COPILOT_KEY_FILE": str(f)}, "COPILOT_KEY") == "direct"
    assert main.secret({}, "COPILOT_KEY") == ""
    with pytest.raises(main.SetupError, match="does not exist"):
        main.secret({"COPILOT_KEY_FILE": str(tmp_path / "nope")}, "COPILOT_KEY")


def test_each_source_says_what_it_still_needs():
    g = FakeGame()
    t = LocalTools(g)
    with pytest.raises(main.SetupError, match="needs a workspace"):
        main.agent_from({"COPILOT_SOURCE": "purple"}, g, t, None)
    with pytest.raises(main.SetupError, match="needs COPILOT_URL"):
        main.agent_from({"COPILOT_SOURCE": "openai", "COPILOT_MODEL": "m"}, g, t, None)
    with pytest.raises(main.SetupError, match="needs COPILOT_MODEL"):
        main.agent_from({"COPILOT_SOURCE": "openai", "COPILOT_URL": "http://h/v1"}, g, t, None)
    with pytest.raises(main.SetupError, match="RCON password is not set"):
        main.game_from({})


def test_each_source_builds_the_one_thing_that_thinks():
    g = FakeGame()
    t = LocalTools(g)
    p = main.agent_from({"COPILOT_SOURCE": "purple", "COPILOT_WORKSPACE": "f-ai-factorio"}, g, t, None)       # no key: the door holds it
    assert isinstance(p, PurpleAgent) and p.purple.url == "http://127.0.0.1:47860/mcp" and p.purple.workspace == "f-ai-factorio"
    o = main.agent_from({"COPILOT_SOURCE": "openai", "COPILOT_URL": "http://h/v1", "COPILOT_MODEL": "m", "COPILOT_KEY": "k"}, g, t, None)
    assert isinstance(o, Agent) and o.model.key == "k" and o.model.base == "http://h/v1"
    l = main.agent_from({"COPILOT_SOURCE": "ollama"}, g, t, None)
    assert l.model.model == "qwen3:8b" and l.model.base == "http://localhost:11434"


# ---------------------------------------------------------------- the first-run check

class CheckGame(FakeGame):
    def __init__(self, reachable=True, mod=True):
        super().__init__({"lookup": {"ok": True, "result": [{"ingredients": [{"name": "iron-plate", "amount": 2}]}]},
                          "avatar": {"ok": True, "result": {"mode": "free-hand", "mode_means": "builds on its own"}}})
        self.reachable, self.mod = reachable, mod

    def call(self, tool, args=None):
        if not self.reachable:
            return {"ok": False, "error": "the game could not be reached: refused"}
        if tool == "tools":
            return {"ok": True, "result": self.tools()} if self.mod else {"ok": False, "error": "the game gave no answer; is the Skippy mod enabled?"}
        return super().call(tool, args)


def run(env, game, replies, monkeypatch, tmp_path, settings_file=True):
    monkeypatch.setattr(main, "HERE", tmp_path)
    if settings_file:
        (tmp_path / "copilot.env").write_text("COPILOT_SOURCE=ollama\n", encoding="utf-8")
    lines = []
    made = lambda e, g, t, log: Agent(g, FakeModel(replies), local=t)
    ok = check.run_check(env, out=lines.append, game_factory=lambda e: game, agent_factory=made)
    return ok, "\n".join(lines)


ENV = {"COPILOT_SOURCE": "ollama", "COPILOT_RCON_PASSWORD": "x"}


def test_the_check_passes_when_everything_works(monkeypatch, tmp_path):
    ok, text = run(ENV, CheckGame(), [[("lookup", {"name": "iron-gear-wheel"})], "It takes two iron plates."], monkeypatch, tmp_path)
    assert ok and "Everything works. Start it with:  python -m copilot" in text
    assert "the game answers and the mod is loaded" in text and "'free-hand' mode: the assistant builds on its own" in text
    assert "the AI source is 'ollama': one source for every turn" in text and "the AI answered: It takes two iron plates." in text
    assert "it looked the answer up in the game (1 tool calls)" in text and "STOP" not in text


def test_the_check_stops_at_the_first_thing_that_is_wrong_and_says_what_to_do(monkeypatch, tmp_path):
    ok, text = run({}, CheckGame(), [], monkeypatch, tmp_path, settings_file=False)
    assert not ok and "there is no settings file yet" in text and "copy copilot/copilot.env.example" in text
    ok, text = run(ENV, CheckGame(reachable=False), [], monkeypatch, tmp_path)
    assert not ok and "the game does not answer on 127.0.0.1:27015" in text and "RCON switched on" in text
    ok, text = run(ENV, CheckGame(mod=False), [], monkeypatch, tmp_path)
    assert not ok and "the Skippy mod does not" in text and "enable the mod" in text
    ok, text = run({"COPILOT_RCON_PASSWORD": "x"}, CheckGame(), [], monkeypatch, tmp_path)
    assert not ok and "no AI source is set" in text
    assert text.count("STOP") == 1                                                  # one problem at a time


def test_the_check_catches_a_model_that_cannot_use_tools_or_does_not_answer(monkeypatch, tmp_path):
    ok, text = run(ENV, CheckGame(), ["Two iron plates, I believe."], monkeypatch, tmp_path)
    assert not ok and "answered without looking anything up" in text and "supports tool calling" in text
    ok, text = run(ENV, CheckGame(), [RuntimeError("connection refused")], monkeypatch, tmp_path)
    assert not ok and "the AI did not answer (model error)" in text and "address, key and model name" in text


def test_the_check_asks_purple_whether_it_is_ready(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "HERE", tmp_path)
    (tmp_path / "copilot.env").write_text("x=1\n", encoding="utf-8")
    g = CheckGame()
    lines = []
    made = lambda e, game, t, log: PurpleAgent(game, purple(FakeBridge(ready=False)), Toolbox(game, t))
    ok = check.run_check({"COPILOT_SOURCE": "purple"}, out=lines.append, game_factory=lambda e: g, agent_factory=made)
    assert not ok and "purple Skippy is not ready: purple Skippy's door could not be reached" in "\n".join(lines)
    lines.clear()
    made = lambda e, game, t, log: PurpleAgent(game, purple(FakeBridge()), Toolbox(game, t))
    ok = check.run_check({"COPILOT_SOURCE": "purple"}, out=lines.append, game_factory=lambda e: g, agent_factory=made)
    assert ok and "purple Skippy answers, workspace 'ai-factorio'" in "\n".join(lines)


# ---------------------------------------------------------------- in the game: is anything connected?

def test_the_light_says_not_connected_until_an_assistant_calls_and_again_when_it_goes_quiet():
    mod = LuaMod()
    mod.run("fake.add_player('captain', 0, 0)")
    caption = "game.players[1].gui.top.skippy_light.state.caption"
    assert mod.lua.eval(caption) == "Skippy: not connected"
    assert "python -m copilot --check" in mod.lua.eval("game.players[1].gui.top.skippy_light.state.tooltip")
    mod.result("chat_read")                                                         # the bridge polls
    assert mod.lua.eval(caption) == "Skippy: idle"
    mod.tick(60 * 20)
    mod.result("chat_read")
    mod.tick(60 * 20)
    assert mod.lua.eval(caption) == "Skippy: idle"                                  # still heard from within the half minute
    mod.tick(60 * 31)
    assert mod.lua.eval(caption) == "Skippy: not connected"
    mod.result("chat_read")
    assert mod.lua.eval(caption) == "Skippy: idle"


def test_a_player_typing_a_tool_call_does_not_count_as_the_assistant_being_connected():
    mod = LuaMod()
    mod.run("fake.add_player('captain', 0, 0)")
    mod.fake.command("tools", 1)
    assert mod.lua.eval("game.players[1].gui.top.skippy_light.state.caption") == "Skippy: not connected"


# ---------------------------------------------------------------- the workspace's files

def test_the_workspace_offers_the_mcp_server_and_the_skill_is_the_prompt():
    mcp = json.loads((ROOT / ".mcp.json").read_text(encoding="utf-8"))
    assert mcp["mcpServers"]["skippy-copilot"] == {"command": "python", "args": ["-m", "copilot.mcp_server"]}
    skill = (ROOT / ".claude" / "skills" / "factorio-copilot" / "SKILL.md").read_text(encoding="utf-8")
    prompt = (ROOT / "copilot" / "prompt.md").read_text(encoding="utf-8")
    assert skill.startswith("---\nname: factorio-copilot\n") and skill.endswith(prompt), "the skill has drifted from copilot/prompt.md"


def test_the_example_settings_cover_every_setting_a_newcomer_needs():
    example = (ROOT / "copilot" / "copilot.env.example").read_text(encoding="utf-8")
    for name in ("COPILOT_RCON_HOST", "COPILOT_RCON_PORT", "COPILOT_RCON_PASSWORD", "COPILOT_SOURCE", "COPILOT_URL", "COPILOT_KEY", "COPILOT_MODEL", "COPILOT_WORKSPACE"):
        assert name in example and name in main.__doc__, name
    assert "python -m copilot --check" in example and example.count("\nCOPILOT_SOURCE=") == 1       # one source switched on, the others commented out
    assert "copilot/copilot.env" in (ROOT / ".gitignore").read_text(encoding="utf-8")                # a filled-in file with a key is never committed
