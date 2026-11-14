import json

from copilot import models
from copilot.agent import Agent, MAX_RESULT
from copilot.score import read, score, total
from fakes import FakeGame, FakeModel


def make(replies, results=None, tmp_path=None, **kw):
    game = FakeGame(results)
    log = (tmp_path / "run.jsonl") if tmp_path else None
    return Agent(game, FakeModel(replies), log, **kw), game


def test_the_model_only_gets_the_tools_meant_for_it():
    agent, _ = make(["hi"])
    assert agent.names == {"lookup", "diagnose"}


def test_answer_without_tools():
    agent, game = make(["Hello."])
    answer, outcome, stats = agent.handle("hi")
    assert (answer, outcome, stats["calls"], stats["misses"], stats["steps"]) == ("Hello.", "answered", 0, 0, 1)
    assert [a["state"] for a in game.named("set_state")] == ["thinking", "idle"]


def test_tool_result_reaches_the_model_and_the_light_shows_work():
    agent, game = make([[("lookup", {"name": "iron-plate"})], "Iron plate stacks to 100."],
                       {"lookup": {"ok": True, "result": [{"stack_size": 100}]}})
    answer, outcome, stats = agent.handle("how big is a stack of iron plate?")
    assert answer == "Iron plate stacks to 100." and stats["calls"] == 1 and stats["misses"] == 0
    assert game.named("lookup") == [{"name": "iron-plate"}]
    tool_msg = agent.model.seen[1][-1]
    assert tool_msg["role"] == "tool" and tool_msg["name"] == "lookup" and json.loads(tool_msg["content"])["result"][0]["stack_size"] == 100
    assert [a["state"] for a in game.named("set_state")] == ["thinking", "working", "idle"]


def test_a_refused_call_is_a_miss_and_the_error_goes_back():
    agent, _ = make([[("lookup", {"nam": "x"})], [("lookup", {"name": "x"})], "done"],
                    {"lookup": lambda a: {"ok": True, "result": []} if "name" in a else {"ok": False, "error": "lookup has no parameter nam"}})
    answer, outcome, stats = agent.handle("q")
    assert outcome == "answered" and stats["calls"] == 2 and stats["misses"] == 1
    assert "no parameter nam" in agent.model.seen[1][-1]["content"]


def test_a_tool_that_does_not_exist_never_reaches_the_game():
    agent, game = make([[("build_everything", {})], "sorry"])
    _, _, stats = agent.handle("q")
    assert stats["misses"] == 1 and game.named("build_everything") == []
    assert "lookup" in json.loads(agent.model.seen[1][-1]["content"])["tools"]


def test_bridge_only_tools_are_refused_to_the_model():
    agent, game = make([[("say", {"text": "x"})], "ok"])
    _, _, stats = agent.handle("q")
    assert stats["misses"] == 1 and game.named("say") == []


def test_the_same_call_a_third_time_is_stopped():
    call = [("diagnose", {})]
    agent, game = make([call, call, call, "fine"])
    _, _, stats = agent.handle("q")
    assert len(game.named("diagnose")) == 2 and stats["misses"] == 1
    assert "this exact call 3 times" in agent.model.seen[3][-1]["content"]


def test_running_out_of_steps_is_not_an_answer():
    agent, game = make([[("diagnose", {"x": i})] for i in range(5)], max_steps=3)
    answer, outcome, stats = agent.handle("q")
    assert answer is None and outcome == "ran out of steps" and stats["steps"] == 3
    assert game.named("set_state")[-1]["state"] == "failed"


def test_a_model_server_failure_is_reported_not_raised():
    agent, game = make([RuntimeError("connection refused")])
    answer, outcome, _ = agent.handle("q")
    assert answer is None and outcome == "model error" and game.named("set_state")[-1]["state"] == "failed"


def test_a_huge_result_is_cut_before_the_model_sees_it():
    agent, _ = make([[("diagnose", {})], "ok"], {"diagnose": {"ok": True, "result": "x" * (MAX_RESULT * 3)}})
    agent.handle("q")
    shown = agent.model.seen[1][-1]["content"]
    assert len(shown) < MAX_RESULT + 100 and shown.endswith("ask for less at a time)")


def test_the_light_can_be_left_alone():
    agent, game = make(["hi"])
    agent.handle("q", light=False)
    assert game.named("set_state") == []


def test_the_log_scores_a_clean_and_a_dirty_run(tmp_path):
    agent, _ = make([[("lookup", {"name": "a"})], "one", [("nope", {})], "two"], tmp_path=tmp_path)
    agent.handle("first")
    s = score(read(tmp_path / "run.jsonl"))
    assert s["clean"] and (s["requests"], s["answered"], s["calls"], s["misses"]) == (1, 1, 1, 0)
    agent.handle("second")
    s = score(read(tmp_path / "run.jsonl"))
    assert not s["clean"] and (s["requests"], s["calls"], s["misses"], s["unknown_tools"]) == (2, 2, 1, 1)
    assert s["miss_list"][0]["name"] == "nope" and s["miss_rate"] == 0.5
    t = total([s, s])
    assert t["calls"] == 4 and not t["clean"]


def test_score_counts_stalls_and_repeats(tmp_path):
    call = [("diagnose", {})]
    agent, _ = make([call, call, call, call], tmp_path=tmp_path, max_steps=4)
    agent.handle("q")
    s = score(read(tmp_path / "run.jsonl"))
    assert s["stalls"] == 1 and s["repeats"] == 2 and not s["clean"]


def test_an_empty_log_is_not_clean():
    assert score([])["clean"] is False


def test_schema_turns_tool_descriptions_into_function_definitions():
    f = models.schema(FakeGame().tools())[0]["function"]
    assert f["name"] == "lookup" and f["parameters"]["required"] == ["name"]
    assert f["parameters"]["properties"]["kind"] == {"type": "string", "description": "kind"}
    assert models.schema([{"name": "t", "description": "d", "parameters": []}])[0]["function"]["parameters"]["properties"] == {}
    table = models.schema([{"name": "t", "description": "d", "parameters": {"a": {"type": "table"}}}])
    assert table[0]["function"]["parameters"]["properties"]["a"]["type"] == "object"


def test_arguments_arrive_as_text_or_as_an_object():
    assert models._args(json.dumps({"a": 1})) == {"a": 1} and models._args({"a": 1}) == {"a": 1}
    assert models._args("") == {} and models._args(None) == {} and models._args("[1]") == {}
    assert "_unparsed" in models._args("{broken")


CONVERSATION = [{"role": "system", "content": "s"}, {"role": "user", "content": "u"},
                {"role": "assistant", "content": "", "tool_calls": [{"id": "c0", "name": "lookup", "args": {"name": "x"}}]},
                {"role": "tool", "name": "lookup", "tool_call_id": "c0", "content": "{}"}]


def test_ollama_wire_format(monkeypatch):
    sent = {}

    def post(url, body, headers, timeout):
        sent.update(url=url, body=body)
        return {"message": {"content": "<think>hmm\nlong</think>Answer.", "tool_calls": [{"function": {"name": "lookup", "arguments": {"name": "y"}}}]},
                "prompt_eval_count": 7, "eval_count": 3}
    monkeypatch.setattr(models, "_post", post)
    r = models.make("ollama", "qwen3:8b", num_ctx=4096).chat(CONVERSATION, [])
    assert sent["url"] == "http://localhost:11434/api/chat" and sent["body"]["options"]["num_ctx"] == 4096 and sent["body"]["stream"] is False
    assert sent["body"]["messages"][2]["tool_calls"] == [{"function": {"name": "lookup", "arguments": {"name": "x"}}}]
    assert sent["body"]["messages"][3]["tool_name"] == "lookup"
    assert r == {"content": "Answer.", "tool_calls": [{"id": "call_0", "name": "lookup", "args": {"name": "y"}}], "tokens_in": 7, "tokens_out": 3}


def test_openai_compatible_wire_format(monkeypatch):
    sent = {}

    def post(url, body, headers, timeout):
        sent.update(url=url, body=body, headers=headers)
        return {"choices": [{"message": {"content": None, "tool_calls": [{"id": "abc", "function": {"name": "lookup", "arguments": json.dumps({"name": "y"})}}]}}],
                "usage": {"prompt_tokens": 9, "completion_tokens": 2}}
    monkeypatch.setattr(models, "_post", post)
    r = models.make("openai", "m", "http://host:1234/v1/", "key").chat(CONVERSATION, [])
    assert sent["url"] == "http://host:1234/v1/chat/completions" and sent["headers"] == {"Authorization": "Bearer key"}
    assert sent["body"]["messages"][2]["tool_calls"][0] == {"id": "c0", "type": "function", "function": {"name": "lookup", "arguments": json.dumps({"name": "x"})}}
    assert sent["body"]["messages"][3]["tool_call_id"] == "c0"
    assert r["tool_calls"] == [{"id": "abc", "name": "lookup", "args": {"name": "y"}}] and r["content"] == "" and r["tokens_in"] == 9


def test_no_key_means_no_header_and_unknown_providers_are_refused(monkeypatch):
    sent = {}
    monkeypatch.setattr(models, "_post", lambda url, body, headers, timeout: sent.update(headers=headers) or {"choices": [{"message": {"content": "x"}}]})
    models.make("openai", "m", "http://h/v1").chat([], [])
    assert sent["headers"] == {}
    for bad in (("openai", "m", None), ("claude", "m", "http://h")):
        try:
            models.make(*bad)
            assert False, "should have been refused"
        except ValueError:
            pass
