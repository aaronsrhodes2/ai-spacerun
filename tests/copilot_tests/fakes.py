"""Stand-ins for the game and the model, so the bridge is tested with neither running."""

TOOLS = [
    {"name": "lookup", "description": "facts", "parameters": {"name": {"type": "string", "required": True, "description": "internal name"},
                                                             "kind": {"type": "string", "required": False, "description": "kind"}}},
    {"name": "diagnose", "description": "what is wrong", "parameters": {}},
    {"name": "say", "description": "say", "parameters": {"text": {"type": "string", "required": True, "description": "text"}}},
    {"name": "set_state", "description": "light", "parameters": {"state": {"type": "string", "required": True, "description": "state"}}},
    {"name": "chat_read", "description": "chat", "parameters": {}},
    {"name": "events_read", "description": "news", "parameters": {}},
]


class FakeGame:
    def __init__(self, results=None):
        self.results = results or {}            # tool name -> result dict, or a function(args) -> dict
        self.calls = []

    def tools(self):
        return TOOLS

    def call(self, tool, args=None):
        self.calls.append((tool, args))
        r = self.results.get(tool, {"ok": True, "result": {}})
        return r(args) if callable(r) else r

    def named(self, tool):
        return [a for t, a in self.calls if t == tool]


class FakeModel:
    """Replies in order; each reply is a string (a final answer) or a list of (tool name, args) calls."""
    model = "fake"

    def __init__(self, replies):
        self.replies = list(replies)
        self.seen = []

    def chat(self, messages, tools):
        self.seen.append([dict(m) for m in messages])
        r = self.replies.pop(0)
        if isinstance(r, Exception):
            raise r
        if isinstance(r, str):
            return {"content": r, "tool_calls": [], "tokens_in": 10, "tokens_out": 5}
        return {"content": "", "tool_calls": [{"id": "c%d" % i, "name": n, "args": a} for i, (n, a) in enumerate(r)], "tokens_in": 10, "tokens_out": 5}
