"""Model adapters. Each takes the conversation and the tool list and returns the model's text and its tool calls, in one
shape, whatever the provider. Standard library only, so the bridge installs anywhere.

  ollama   a local Ollama server (native /api/chat, so the context size can be set)
  openai   any server that speaks the OpenAI chat-completions API: LM Studio, llama.cpp, vLLM, OpenAI itself

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


def make(provider, model, base_url=None, api_key="", num_ctx=16384):
    if provider == "ollama":
        return Ollama(model, base_url or "http://localhost:11434", num_ctx)
    if provider == "openai":
        if not base_url:
            raise ValueError("the openai provider needs a base URL, such as http://localhost:1234/v1")
        return OpenAICompatible(model, base_url, api_key)
    raise ValueError("unknown provider '%s' (ollama or openai)" % provider)
