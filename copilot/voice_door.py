"""The voice door: how speech reaches Skippy in the game and how Skippy's words get back to be spoken.

A Factorio mod has no microphone, no speaker and no network, so voice cannot live in the game. And this bridge holds no
key to the house's ears and mouth (SkippyTel's voice gate wants a pass signed from the home token, which never comes
near this repository). So the hearing and the speaking stay with the house's own listener, which already wakes on
"Skippy", turns speech into text and speaks in Skippy's voice. This door is the small piece between the two:

    microphone -> the house listener (wake word, speech to text)  --POST /hear-->   this door -> the game, as if typed
    speaker    <- the house listener (text to speech)             <--GET /said--    this door <- everything Skippy says

The door listens on this computer only (127.0.0.1), so it needs no key.

    GET  /health                    {"ok": true, "service": "skippy-factorio", "heard": n, "said": n}
    POST /hear   {"text", "who"?}   a spoken line for Skippy. -> {"ok": true, "id": n, "after": m}
                                    `after` is where /said stood at that moment: ask /said?after=m for the answer.
    GET  /said?after=N&wait=S       what Skippy has said since N, waiting up to S seconds (at most 30) for news.
                                    -> {"lines": [{"id", "text", "voice"}], "next": M}
                                    voice is "skippy" (the foreman) or "purple" (a development task's words).

While this door answers, a Factorio session is on: a listener can take that as the sign to send what it hears here.
Standard library only."""
import collections
import json
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 47862                        # purple's door is 47860, the house's 47861
MAX_TEXT = 1000
MAX_WAIT = 30.0
KEEP = 200


class VoiceGame:
    """The game, with one ear on it: everything said into the game's chat is also kept for the speaker."""

    def __init__(self, game, door):
        self._game, self._door = game, door

    def __getattr__(self, name):
        return getattr(self._game, name)

    def call(self, tool, args=None):
        r = self._game.call(tool, args)
        if tool == "say" and isinstance(r, dict) and r.get("ok") and args and args.get("text"):
            self._door.spoke(args["text"], args.get("as") or "skippy")
        return r


class VoiceDoor:
    def __init__(self, host="127.0.0.1", port=PORT):
        self.host, self.port = host, port
        self.lock = threading.Condition()
        self.heard = collections.deque()
        self.heard_count = 0
        self.said = collections.deque(maxlen=KEEP)
        self.said_next = 1
        self.server = None

    # ---- the bridge's side -------------------------------------------------------------------------------------------
    def wrap(self, game):
        return VoiceGame(game, self)

    def take(self):
        """The lines heard since last asked, oldest first."""
        with self.lock:
            lines = list(self.heard)
            self.heard.clear()
        return lines

    def spoke(self, text, voice="skippy"):
        with self.lock:
            self.said.append({"id": self.said_next, "text": text, "voice": voice})
            self.said_next += 1
            self.lock.notify_all()

    # ---- the listener's side -----------------------------------------------------------------------------------------
    def hear(self, text, who=""):
        text = " ".join(str(text or "").split())[:MAX_TEXT]
        if not text:
            return None
        with self.lock:
            self.heard_count += 1
            self.heard.append({"id": self.heard_count, "text": text, "who": str(who or "")[:60]})
            return {"ok": True, "id": self.heard_count, "after": self.said_next - 1}

    def said_after(self, after=0, wait=0.0):
        wait = max(0.0, min(float(wait or 0), MAX_WAIT))
        with self.lock:
            if wait and not any(l["id"] > after for l in self.said):
                self.lock.wait(wait)
            lines = [dict(l) for l in self.said if l["id"] > after]
            return {"lines": lines, "next": lines[-1]["id"] if lines else max(after, 0)}

    def health(self):
        with self.lock:
            return {"ok": True, "service": "skippy-factorio", "heard": self.heard_count, "said": self.said_next - 1}

    # ---- over HTTP ---------------------------------------------------------------------------------------------------
    def serve(self):
        door = self

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
                url = urllib.parse.urlparse(self.path)
                q = urllib.parse.parse_qs(url.query)
                if url.path == "/health":
                    return self._send(200, door.health())
                if url.path == "/said":
                    try:
                        after, wait = int(q.get("after", ["0"])[0]), float(q.get("wait", ["0"])[0])
                    except ValueError:
                        return self._send(400, {"ok": False, "error": "after and wait must be numbers"})
                    return self._send(200, door.said_after(after, wait))
                self._send(404, {"ok": False, "error": "there is /health, /hear and /said"})

            def do_POST(self):
                if urllib.parse.urlparse(self.path).path != "/hear":
                    return self._send(404, {"ok": False, "error": "there is /health, /hear and /said"})
                try:
                    size = int(self.headers.get("Content-Length") or 0)
                    if size > 20000:
                        return self._send(413, {"ok": False, "error": "too long: one spoken line at a time"})
                    body = json.loads(self.rfile.read(size).decode() or "{}")
                    got = door.hear(body.get("text"), body.get("who")) if isinstance(body, dict) else None
                except (ValueError, UnicodeDecodeError):
                    return self._send(400, {"ok": False, "error": "send JSON: {\"text\": \"what was said\"}"})
                if not got:
                    return self._send(400, {"ok": False, "error": "there was no text"})
                self._send(200, got)

        class Server(ThreadingHTTPServer):
            allow_reuse_address = False                 # a port already taken must be refused, on Windows too

        self.server = Server((self.host, self.port), H)
        self.server.daemon_threads = True
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        return "http://%s:%d" % (self.host, self.port)

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
