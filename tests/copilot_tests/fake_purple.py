"""A stand-in for purple Skippy's MCP door (SkippyTel's purple-mcp). It answers the same JSON-RPC, either in-process
(pass `post` and `get` to PurpleClient) or as a small real HTTP server on a free local port (`serve()`)."""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from copilot.purple_client import PurpleClient

ANSWER = [{"text": "", "done": False}, {"text": "Two iron plates.", "done": True, "ok": True, "steps": 1}]


class FakePurple:
    def __init__(self, script=None, busy=0, up=True, tool_error=None, key=None, rpc_error=None):
        self.script = ANSWER if script is None else script
        self.busy, self.up, self.tool_error, self.key, self.rpc_error = busy, up, tool_error, key, rpc_error
        self.asked, self.polled, self.cancelled, self.methods = [], [], [], []
        self.server = None

    # ---- the protocol ------------------------------------------------------------------------------------------------
    def _batch(self, i):
        b = dict(self.script[i]) if i < len(self.script) else {"text": "", "done": False}
        b.update(task="task-1", next=i + 1)
        b.setdefault("steps", 0)
        return b

    def _tool(self, name, a):
        if self.tool_error:
            return self.tool_error, True
        if name == "purple_ask":
            self.asked.append(a)
            if self.busy > 0:
                self.busy -= 1
                return {"busy": True, "message": "purple is on another job"}, False
            return dict(self._batch(0), conv=a.get("conv") or "mcp-new"), False
        if name == "purple_result":
            self.polled.append(a)
            return self._batch(int(a.get("after") or 0)), False
        if name == "purple_cancel":
            self.cancelled.append(a["task"])
            return {"ok": True}, False
        return "no such tool", True

    def handle(self, body, headers):
        """(status, answer) for one JSON-RPC POST."""
        if self.key and headers.get("Authorization") != "Bearer " + self.key:
            return 401, {"error": "unauthorized"}
        self.methods.append(body["method"])
        if self.rpc_error:
            return 200, {"jsonrpc": "2.0", "id": body["id"], "error": {"code": -32000, "message": self.rpc_error}}
        if body["method"] == "initialize":
            return 200, {"jsonrpc": "2.0", "id": body["id"], "result": {"serverInfo": {"name": "purple-mcp"}}}
        got, bad = self._tool(body["params"]["name"], body["params"].get("arguments") or {})
        text = got if isinstance(got, str) else json.dumps(got)
        return 200, {"jsonrpc": "2.0", "id": body["id"], "result": {"content": [{"type": "text", "text": text}], "isError": bad}}

    # ---- in-process --------------------------------------------------------------------------------------------------
    def post(self, url, body, headers, timeout):
        if not self.up:
            raise OSError("connection refused")
        return self.handle(body, headers)

    def get(self, url, headers, timeout):
        if not self.up:
            raise OSError("connection refused")
        return 200, {"ok": True, "service": "purple-mcp"}

    def client(self, key=""):
        return PurpleClient("http://127.0.0.1:47860/mcp", key, post=self.post, get=self.get)

    # ---- over real HTTP ----------------------------------------------------------------------------------------------
    def serve(self):
        fake = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _send(self, status, obj):
                data = json.dumps(obj).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self):
                self._send(200, {"ok": True, "service": "purple-mcp"}) if self.path == "/health" else self._send(404, {})

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)).decode())
                self._send(*fake.handle(body, self.headers))

        self.server = HTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        return "http://127.0.0.1:%d/mcp" % self.server.server_address[1]

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
