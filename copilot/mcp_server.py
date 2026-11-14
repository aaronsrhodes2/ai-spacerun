"""The game's tools over MCP, for an outside agent (purple Skippy, Claude Code, anything that speaks MCP):

    python -m copilot.mcp_server

It speaks MCP over standard input and output: one JSON-RPC message a line. It offers exactly the tools the bridge's own
loop would offer a model (the mod's, plus the planning tools), reads the same settings (see `python -m copilot`), and
writes every call to the run log so an agent's run is scored the same way.

Standard library only. Three requests matter: initialize, tools/list and tools/call."""
import json
import pathlib
import sys
import time

from .models import schema
from .toolbox import Toolbox

PROTOCOL = "2024-11-05"
MAX_RESULT = 12000


def reply(msg_id, result=None, error=None):
    out = {"jsonrpc": "2.0", "id": msg_id}
    if error is not None:
        out["error"] = error
    else:
        out["result"] = result
    return out


class Server:
    def __init__(self, toolbox):
        self.toolbox = toolbox

    def tools(self):
        out = []
        for t in schema(self.toolbox.offered):
            f = t["function"]
            out.append({"name": f["name"], "description": f["description"], "inputSchema": f["parameters"]})
        return out

    def handle(self, msg):
        """One message in, one reply out (None for a notification)."""
        method, msg_id = msg.get("method"), msg.get("id")
        if msg_id is None:
            return None                                              # notifications need no answer
        if method == "initialize":
            return reply(msg_id, {"protocolVersion": PROTOCOL, "capabilities": {"tools": {}},
                                  "serverInfo": {"name": "skippy-copilot", "version": "0.12.0"}})
        if method == "ping":
            return reply(msg_id, {})
        if method == "tools/list":
            return reply(msg_id, {"tools": self.tools()})
        if method == "tools/call":
            params = msg.get("params") or {}
            name, args = params.get("name"), params.get("arguments") or {}
            result = self.toolbox.call(name, args)
            self.toolbox.log(event="tool", step=0, name=name, args=args, ok=bool(result.get("ok")), error=result.get("error"))
            text = json.dumps(result)
            if len(text) > MAX_RESULT:
                text = text[:MAX_RESULT] + " ...(cut: ask for less at a time)"
            return reply(msg_id, {"content": [{"type": "text", "text": text}], "isError": not result.get("ok")})
        return reply(msg_id, error={"code": -32601, "message": "unknown method: %s" % method})


def serve(server, lines, write):
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            write(json.dumps(reply(None, error={"code": -32700, "message": "not JSON"})))
            continue
        out = server.handle(msg)
        if out is not None:
            write(json.dumps(out))


def main():
    from .__main__ import game_from, settings
    from .tools import LocalTools
    env = settings()
    game = game_from(env)
    logs = pathlib.Path(env.get("COPILOT_LOG_DIR", "runs"))
    logs.mkdir(exist_ok=True)
    local = LocalTools(game, plan_store=logs / "plans.json")
    toolbox = Toolbox(game, local, logs / ("mcp-" + time.strftime("%Y%m%d-%H%M%S") + ".jsonl"))

    def write(text):
        sys.stdout.write(text + "\n")
        sys.stdout.flush()
    serve(Server(toolbox), sys.stdin, write)


if __name__ == "__main__":
    main()
