"""Model adapters. Each takes the conversation and the tool list and returns the model's text and its tool calls, in one
shape, whatever the provider. Standard library only, so the bridge installs anywhere.

  ollama   a local Ollama server (native /api/chat, so the context size can be set)
  openai   any server that speaks the OpenAI chat-completions API: LM Studio, llama.cpp, vLLM, OpenAI itself
  anthropic  any server that speaks the Anthropic Messages API (/v1/messages): Skippy Core's model, or Anthropic itself

Messages are kept in the OpenAI shape: {"role": "system"|"user"|"assistant"|"tool", "content": ...}; an assistant turn with
tool calls carries "tool_calls": [{"id", "name", "args"}], which each adapter rewrites for its own wire format."""
import json
import re
import urllib.request

THINK = re.compile(r"<think>.*?</think>", re.S)


def schema(tools):
    """The mod's tool descriptions as function definitions a model understands."""
    out = []
    for t in tools:
        params = t.get("parameters") or {}
        props, required = {}, []
        for key, p in (params.items() if isinstance(params, dict) else []):
            props[key] = {"type": {"table": "object"}.get(p["type"], p["type"]), "description": p.get("description") or ""}
            if p.get("required"):
                required.append(key)
        out.append({"type": "function", "function": {"name": t["name"], "description": t["description"],
                                                     "parameters": {"type": "object", "properties": props, "required": required}}})
    return out


def _post(url, body, headers, timeout):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=dict({"Content-Type": "application/json"}, **headers))
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def _args(a):
    if isinstance(a, dict):
        return a
    try:
        v = json.loads(a or "{}")
        return v if isinstance(v, dict) else {}
    except ValueError:
        return {"_unparsed": str(a)[:200]}


class Ollama:
    def __init__(self, model, base_url="http://localhost:11434", num_ctx=16384, timeout=600):
        self.model, self.base, self.num_ctx, self.timeout = model, base_url.rstrip("/"), num_ctx, timeout

    def chat(self, messages, tools):
        wire = []
        for m in messages:
            w = {"role": m["role"], "content": m.get("content") or ""}
            if m.get("tool_calls"):
                w["tool_calls"] = [{"function": {"name": c["name"], "arguments": c["args"]}} for c in m["tool_calls"]]
            if m["role"] == "tool":
                w["tool_name"] = m.get("name")
            wire.append(w)
        r = _post(self.base + "/api/chat", {"model": self.model, "messages": wire, "tools": tools, "stream": False,
                                            "options": {"num_ctx": self.num_ctx, "temperature": 0.2}}, {}, self.timeout)
        msg = r.get("message") or {}
        calls = [{"id": "call_%d" % i, "name": c["function"]["name"], "args": _args(c["function"].get("arguments"))}
                 for i, c in enumerate(msg.get("tool_calls") or [])]
        return {"content": THINK.sub("", msg.get("content") or "").strip(), "tool_calls": calls,
                "tokens_in": r.get("prompt_eval_count"), "tokens_out": r.get("eval_count")}


class OpenAICompatible:
    def __init__(self, model, base_url, api_key="", timeout=600):
        self.model, self.base, self.key, self.timeout = model, base_url.rstrip("/"), api_key, timeout

    def chat(self, messages, tools):
        wire = []
        for m in messages:
            w = {"role": m["role"], "content": m.get("content") or ""}
            if m.get("tool_calls"):
                w["tool_calls"] = [{"id": c["id"], "type": "function", "function": {"name": c["name"], "arguments": json.dumps(c["args"])}} for c in m["tool_calls"]]
            if m["role"] == "tool":
                w["tool_call_id"] = m.get("tool_call_id")
            wire.append(w)
        headers = {"Authorization": "Bearer " + self.key} if self.key else {}
        r = _post(self.base + "/chat/completions", {"model": self.model, "messages": wire, "tools": tools, "temperature": 0.2}, headers, self.timeout)
        msg = r["choices"][0]["message"]
        calls = [{"id": c.get("id") or "call_%d" % i, "name": c["function"]["name"], "args": _args(c["function"].get("arguments"))}
                 for i, c in enumerate(msg.get("tool_calls") or [])]
        usage = r.get("usage") or {}
        return {"content": THINK.sub("", msg.get("content") or "").strip(), "tool_calls": calls,
                "tokens_in": usage.get("prompt_tokens"), "tokens_out": usage.get("completion_tokens")}


class AnthropicCompatible:
    """The Anthropic Messages API, spoken over plain HTTP so the bridge needs nothing installed. Skippy Core's model
    answers in this format (the Captain's own server), and so does Anthropic. One address, one key."""

    VERSION = "2023-06-01"

    def __init__(self, model, base_url, api_key="", timeout=600, max_tokens=4096, post=None):
        base = base_url.rstrip("/")
        self.model, self.key, self.timeout, self.max_tokens = model, api_key, timeout, max_tokens
        self.base = base
        self.url = base + ("/messages" if base.endswith("/v1") else "/v1/messages")
        self.post = post or _post

    @staticmethod
    def wire(messages):
        """(system text, messages) in the Messages shape: tool calls and their results are content blocks, and the
        results of one step travel together in one user message."""
        system, out = [], []
        for m in messages:
            role = m["role"]
            if role == "system":
                system.append(m.get("content") or "")
            elif role == "assistant":
                blocks = m.get("blocks")                        # what the server sent, replayed unchanged
                if not blocks:
                    blocks = [{"type": "text", "text": m["content"]}] if m.get("content") else []
                    blocks += [{"type": "tool_use", "id": c["id"], "name": c["name"], "input": c["args"]} for c in m.get("tool_calls") or []]
                out.append({"role": "assistant", "content": blocks or [{"type": "text", "text": "(nothing)"}]})
            elif role == "tool":
                block = {"type": "tool_result", "tool_use_id": m.get("tool_call_id"), "content": m.get("content") or ""}
                last = out[-1] if out else None
                if last and last["role"] == "user" and isinstance(last["content"], list) and last["content"][0].get("type") == "tool_result":
                    last["content"].append(block)
                else:
                    out.append({"role": "user", "content": [block]})
            else:
                out.append({"role": "user", "content": m.get("content") or ""})
        return chr(10).join(s for s in system if s), out

    def chat(self, messages, tools):
        system, wire = self.wire(messages)
        body = {"model": self.model, "max_tokens": self.max_tokens, "messages": wire}
        if system:
            body["system"] = system
        if tools:
            body["tools"] = [{"name": t["function"]["name"], "description": t["function"]["description"], "input_schema": t["function"]["parameters"]} for t in tools]
        headers = {"anthropic-version": self.VERSION}
        if self.key:
            headers["x-api-key"] = self.key
        r = self.post(self.url, body, headers, self.timeout)
        if r.get("type") == "error":
            raise RuntimeError("the AI source answered with an error: %s" % ((r.get("error") or {}).get("message") or r))
        blocks = r.get("content") or []
        text = "".join(b.get("text") or "" for b in blocks if b.get("type") == "text")
        calls = [{"id": b.get("id") or "call_%d" % i, "name": b.get("name"), "args": _args(b.get("input"))}
                 for i, b in enumerate(blocks) if b.get("type") == "tool_use"]
        if r.get("stop_reason") == "refusal":
            text = text or "The AI source declined to answer that."
        usage = r.get("usage") or {}
        return {"content": THINK.sub("", text).strip(), "tool_calls": calls, "blocks": blocks if calls else None,
                "tokens_in": usage.get("input_tokens"), "tokens_out": usage.get("output_tokens")}


def make(provider, model, base_url=None, api_key="", num_ctx=16384):
    if provider == "ollama":
        return Ollama(model, base_url or "http://localhost:11434", num_ctx)
    if provider == "openai":
        if not base_url:
            raise ValueError("the openai provider needs a base URL, such as http://localhost:1234/v1")
        return OpenAICompatible(model, base_url, api_key)
    if provider == "anthropic":
        if not base_url:
            raise ValueError("the anthropic provider needs a base URL, such as http://skippy-core:11434")
        return AnthropicCompatible(model, base_url, api_key)
    raise ValueError("unknown provider '%s' (ollama, openai or anthropic)" % provider)
