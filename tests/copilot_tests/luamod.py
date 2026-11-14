"""Runs the Skippy Copilot mod's real Lua under Lua 5.2 (the version Factorio embeds) against the stand-in game in
fake_game.lua. A test calls a tool exactly as the bridge does over RCON: one `/skippy <tool> <json>` command in, one line
of JSON out. Needs the `lupa` package."""
import json
import pathlib

import lupa.lua52 as lua52

HERE = pathlib.Path(__file__).resolve().parent
MOD = HERE.parents[1] / "mods" / "skippy-copilot"


def to_python(v):
    """A Lua value as Python, the way Factorio's table_to_json sees it: a table with keys 1..n is a list, any other table
    an object, and an empty table an object (Factorio writes {} for it too)."""
    if lua52.lua_type(v) == "table":
        keys = list(v.keys())
        if keys and all(isinstance(k, (int, float)) and float(k).is_integer() for k in keys) and sorted(int(k) for k in keys) == list(range(1, len(keys) + 1)):
            return [to_python(v[i]) for i in range(1, len(keys) + 1)]
        return {str(k): to_python(v[k]) for k in keys}
    if isinstance(v, float) and v.is_integer() and abs(v) < 1e15:
        return int(v)
    return v


class LuaMod:
    def __init__(self):
        self.lua = lua52.LuaRuntime(unpack_returned_tuples=True)
        g = self.lua.globals()
        g.package.path = str(MOD).replace("\\", "/") + "/?.lua"
        self.lua.execute("helpers = {}")
        g.helpers.table_to_json = lambda t: json.dumps(to_python(t))
        g.helpers.json_to_table = self._json_to_table
        self.lua.execute("local names = { [0] = 'North', [4] = 'East', [8] = 'South', [12] = 'West' } "
                         "function helpers.direction_to_string(d) return names[d] or tostring(d) end")
        self.lua.execute("dofile(%s)" % json.dumps(str(HERE / "fake_game.lua").replace("\\", "/")))
        self.lua.execute("dofile(%s)" % json.dumps(str(MOD / "control.lua").replace("\\", "/")))
        self.fake = g.fake
        self.fake.on_init()

    def _to_lua(self, v):
        if isinstance(v, dict):
            return self.lua.table_from({k: self._to_lua(x) for k, x in v.items()})
        if isinstance(v, list):
            return self.lua.table_from([self._to_lua(x) for x in v])
        return v

    def _json_to_table(self, text):
        try:
            return self._to_lua(json.loads(text))
        except ValueError:
            return None

    def call(self, tool, args=None, player_index=None):
        out = self.fake.command(tool if args is None else "%s %s" % (tool, json.dumps(args)), player_index)
        assert out, "the command printed nothing over RCON"
        return json.loads(out)

    def result(self, tool, args=None):
        r = self.call(tool, args)
        assert r["ok"], r
        return r["result"]

    def run(self, code):
        return self.lua.execute(code)

    def place(self, name, x, y, **kw):
        """Put something into the fake world by its centre. status is a name such as 'no_power'."""
        extra = "".join(", %s = %s" % (k, self._literal(v)) for k, v in kw.items())
        self.run("game.surfaces.nauvis.create_entity{name = %s, position = {%s, %s}%s}" % (json.dumps(name), x, y, extra))

    def _literal(self, v):
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, (int, float)):
            return repr(v)
        if isinstance(v, dict):
            return "{" + ", ".join("[%s] = %s" % (json.dumps(k), self._literal(x)) for k, x in v.items()) + "}"
        return json.dumps(v)

    def tick(self, n=1):
        self.fake.tick(n)

    def run_job(self, limit=6000):
        """Advance the world until the avatar's job ends; returns its result. Fails the test if it never ends."""
        for _ in range(limit):
            if not self.lua.eval("storage.avatar.job ~= nil"):
                break
            self.fake.tick(1)
        assert not self.lua.eval("storage.avatar.job ~= nil"), "the avatar's job did not end in %d ticks" % limit
        return self.result("avatar")["last_job"]

    def give(self, **items):
        """Put items into the avatar's inventory (item names with underscores for hyphens)."""
        if self.result("avatar")["mode"] != "my-character":
            self.result("set_mode", {"mode": "my-character"})
        self.result("avatar_walk", {"x": 0, "y": 0, "near": 50})          # makes sure a body exists; ends at once
        self.run_job()
        for name, n in items.items():
            self.run("storage.avatar.body.get_main_inventory().insert{name = %s, count = %d}" % (json.dumps(name.replace("_", "-")), n))

    def body(self):
        return self.lua.eval("storage.avatar.body.position.x"), self.lua.eval("storage.avatar.body.position.y")

    def scene(self):
        """The same small scene scripts/modcheck.py builds on a real server."""
        self.place("assembling-machine-2", 3.5, 1.5, recipe="iron-gear-wheel", status="no_power")
        for x in range(11):
            self.place("transport-belt", x + 0.5, 4.5, direction=4)
        self.place("inserter", 3.5, 3.5, direction=8)
        self.place("electric-mining-drill", -8.5, -3.5, status="no_power")
        for x in range(-10, -5):
            for y in range(-6, -1):
                self.place("iron-ore", x + 0.5, y + 0.5, amount=500, force=False)
        for x in range(12, 17):
            for y in range(-8, -4):
                self.run("game.surfaces.nauvis.set(%d, %d, 'water')" % (x, y))
        self.place("entity-ghost", 0.5, -6.5, inner_name="lab")
        return self
