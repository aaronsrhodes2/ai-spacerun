"""A source that speaks the Anthropic Messages API (2026-11-13): Skippy Core serves purple Skippy's model that way, with
tool use, so the bridge's own loop can run every turn on it. One address, one key. No server is called here."""
import pytest

import copilot.__main__ as main
from copilot.agent import Agent
from copilot.models import AnthropicCompatible, make, schema
from copilot.tools import LocalTools
from fakes import FakeGame

TOOLS = schema([{"name": "lookup", "description": "look a thing up", "parameters": {"name": {"type": "string", "required": True, "description": "its name"}}}])


class Server:
    def __init__(self, replies):
        self.replies, self.seen = list(replies), []

    def __call__(self, url, body, headers, timeout):
        self.seen.append((url, body, headers))
        return self.replies.pop(0)


def reply(*blocks, stop="end_turn"):
    return {"type": "message", "role": "assistant", "content": list(blocks), "stop_reason": stop, "usage": {"input_tokens": 900, "output_tokens": 40}}


def use(name, args, call_id="toolu_1"):
    return {"type": "tool_use", "id": call_id, "name": name, "input": args}


def text(t):
    return {"type": "text", "text": t}


def model(server, url="http://core:11434", key="k"):
    return AnthropicCompatible("coder", url, key, post=server)


def test_the_request_is_in_the_messages_shape():
    s = Server([reply(text("Hello."))])
    got = model(s).chat([{"role": "system", "content": "You are Skippy."}, {"role": "user", "content": "hi"}], TOOLS)
    url, body, headers = s.seen[0]
    assert url == "http://core:11434/v1/messages"
    assert headers == {"anthropic-version": "2023-06-01", "x-api-key": "k"}
    assert body["model"] == "coder" and body["max_tokens"] == 4096 and body["system"] == "You are Skippy."
    assert body["messages"] == [{"role": "user", "content": "hi"}]
    assert body["tools"] == [{"name": "lookup", "description": "look a thing up",
                              "input_schema": {"type": "object", "properties": {"name": {"type": "string", "description": "its name"}}, "required": ["name"]}}]
    assert "temperature" not in body                                 # newer models refuse it
    assert got == {"content": "Hello.", "tool_calls": [], "blocks": None, "tokens_in": 900, "tokens_out": 40}


def test_the_address_may_end_in_v1_or_not_and_no_key_sends_no_key():
    s = Server([reply(text("a")), reply(text("b"))])
    model(s, "http://core:11434/v1/").chat([{"role": "user", "content": "q"}], [])
    model(s, "https://funnel.example/", key="").chat([{"role": "user", "content": "q"}], [])
    assert s.seen[0][0] == "http://core:11434/v1/messages" and s.seen[1][0] == "https://funnel.example/v1/messages"
    assert "x-api-key" not in s.seen[1][2] and "tools" not in s.seen[1][1] and "system" not in s.seen[1][1]


def test_tool_calls_come_back_in_the_one_shape_the_agent_knows():
    s = Server([reply({"type": "thinking", "thinking": "hm"}, text("Let me look."), use("lookup", {"name": "iron-gear-wheel"}), stop="tool_use")])
    got = model(s).chat([{"role": "user", "content": "q"}], TOOLS)
    assert got["content"] == "Let me look." and got["tool_calls"] == [{"id": "toolu_1", "name": "lookup", "args": {"name": "iron-gear-wheel"}}]
    assert [b["type"] for b in got["blocks"]] == ["thinking", "text", "tool_use"]


def test_results_of_one_step_go_back_together_and_the_servers_blocks_are_replayed_unchanged():
    blocks = [{"type": "thinking", "thinking": "", "signature": "sig"}, use("lookup", {"name": "a"}, "t1"), use("lookup", {"name": "b"}, "t2")]
    history = [{"role": "system", "content": "S"}, {"role": "user", "content": "q"},
               {"role": "assistant", "content": "", "tool_calls": [{"id": "t1", "name": "lookup", "args": {"name": "a"}}, {"id": "t2", "name": "lookup", "args": {"name": "b"}}], "blocks": blocks},
               {"role": "tool", "name": "lookup", "tool_call_id": "t1", "content": "A"},
               {"role": "tool", "name": "lookup", "tool_call_id": "t2", "content": "B"}]
    system, wire = AnthropicCompatible.wire(history)
    assert system == "S" and [m["role"] for m in wire] == ["user", "assistant", "user"]
    assert wire[1]["content"] is blocks
    assert wire[2]["content"] == [{"type": "tool_result", "tool_use_id": "t1", "content": "A"}, {"type": "tool_result", "tool_use_id": "t2", "content": "B"}]


def test_an_assistant_turn_without_kept_blocks_is_rebuilt():
    _, wire = AnthropicCompatible.wire([{"role": "user", "content": "q"},
                                        {"role": "assistant", "content": "Looking.", "tool_calls": [{"id": "t1", "name": "lookup", "args": {"name": "a"}}]},
                                        {"role": "tool", "tool_call_id": "t1", "content": "A"}, {"role": "user", "content": "and?"}])
    assert wire[1]["content"] == [text("Looking."), use("lookup", {"name": "a"}, "t1")]
    assert wire[3] == {"role": "user", "content": "and?"}             # a new line from the player is not folded into the results


def test_a_whole_turn_runs_through_the_agent():
    s = Server([reply(use("diagnose", {}), stop="tool_use"), reply(text("All is well."))])
    agent = Agent(FakeGame({"diagnose": {"ok": True, "result": {"fine": True}}}), model(s))
    answer, outcome, stats = agent.handle("what is wrong?", light=False)
    assert (answer, outcome, stats["calls"], stats["tokens_in"]) == ("All is well.", "answered", 1, 1800)
    second = s.seen[1][1]["messages"]
    assert second[1]["content"] == [use("diagnose", {})] and second[2]["content"][0]["type"] == "tool_result" and second[2]["content"][0]["tool_use_id"] == "toolu_1"


def test_errors_and_refusals_are_said():
    with pytest.raises(RuntimeError, match="answered with an error: model not found"):
        model(Server([{"type": "error", "error": {"type": "not_found_error", "message": "model not found"}}])).chat([{"role": "user", "content": "q"}], [])
    got = model(Server([reply(stop="refusal")])).chat([{"role": "user", "content": "q"}], [])
    assert got["content"] == "The AI source declined to answer that." and got["tool_calls"] == []


def test_the_settings_build_it_and_say_what_is_missing():
    g = FakeGame()
    t = LocalTools(g)
    a = main.agent_from({"COPILOT_SOURCE": "anthropic", "COPILOT_URL": "http://skippy-core:11434", "COPILOT_MODEL": "coder", "COPILOT_KEY": "k"}, g, t, None)
    assert isinstance(a, Agent) and isinstance(a.model, AnthropicCompatible) and a.model.url == "http://skippy-core:11434/v1/messages" and a.model.key == "k"
    with pytest.raises(main.SetupError, match="anthropic source needs COPILOT_URL"):
        main.agent_from({"COPILOT_SOURCE": "anthropic", "COPILOT_MODEL": "m"}, g, t, None)
    with pytest.raises(main.SetupError, match="anthropic source needs COPILOT_MODEL"):
        main.agent_from({"COPILOT_SOURCE": "anthropic", "COPILOT_URL": "http://h"}, g, t, None)
    with pytest.raises(ValueError, match="needs a base URL"):
        make("anthropic", "m")
    assert "COPILOT_SOURCE=anthropic" in (main.HERE / "copilot.env.example").read_text(encoding="utf-8")


def test_settings_written_as_a_name_are_read_from_the_vault(tmp_path, monkeypatch):
    vault = tmp_path / "vault.env"
    vault.write_text("# shared\nCORE_URL=http://core:11434\nCORE_KEY='s3cret'\nOTHER=x\n", encoding="utf-8")
    env = main.resolve({"COPILOT_VAULT": str(vault), "COPILOT_URL": "$CORE_URL", "COPILOT_KEY": "$CORE_KEY", "COPILOT_MODEL": "plain", "PATH": "$HOME"})
    assert (env["COPILOT_URL"], env["COPILOT_KEY"], env["COPILOT_MODEL"], env["PATH"]) == ("http://core:11434", "s3cret", "plain", "$HOME")
    monkeypatch.setenv("FROM_ENVIRONMENT", "e")
    assert main.resolve({"COPILOT_MODEL": "$FROM_ENVIRONMENT"})["COPILOT_MODEL"] == "e"
    with pytest.raises(main.SetupError, match="COPILOT_KEY is set to .NOPE, but .* has no value named NOPE"):
        main.resolve({"COPILOT_VAULT": str(vault), "COPILOT_KEY": "$NOPE"})
    with pytest.raises(main.SetupError, match="COPILOT_VAULT points at .*which does not exist"):
        main.resolve({"COPILOT_VAULT": str(tmp_path / "gone"), "COPILOT_KEY": "$X"})
    assert main.resolve({"COPILOT_KEY": "direct"}) == {"COPILOT_KEY": "direct"}
    assert "COPILOT_VAULT" in main.__doc__ and "COPILOT_VAULT" in (main.HERE / "copilot.env.example").read_text(encoding="utf-8")
