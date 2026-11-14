"""The link to the game: every tool call goes through the mod's one command, /skippy <tool> <json>, over RCON."""
import json

import factorio_rcon


class Game:
    def __init__(self, host, port, password):
        self.host, self.port, self.password = host, port, password
        self.client = None

    def _send(self, command):
        for attempt in (1, 2):                       # one reconnect: a server restart drops the socket
            try:
                if self.client is None:
                    self.client = factorio_rcon.RCONClient(self.host, self.port, self.password)
                return self.client.send_command(command) or ""
            except Exception:
                self.client = None
                if attempt == 2:
                    raise
        return ""

    def call(self, tool, args=None):
        """One tool call. Always returns a dict with 'ok'; a failure to reach the game is an answer too, not an exception."""
        try:
            out = self._send("/skippy %s %s" % (tool, json.dumps(args) if args else ""))
        except Exception as e:
            return {"ok": False, "error": "the game could not be reached: %s" % e}
        if not out.strip():
            return {"ok": False, "error": "the game gave no answer; is the Skippy Copilot mod enabled?"}
        try:
            return json.loads(out)
        except ValueError:
            return {"ok": False, "error": "the game's answer was not JSON", "raw": out[:300]}

    def tools(self):
        r = self.call("tools")
        if not r.get("ok"):
            raise RuntimeError(r.get("error"))
        return r["result"]
