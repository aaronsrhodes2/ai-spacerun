"""Operator scripts obey the allowance switches: the shared check, and the starter-fuel tool that carries its own."""
import pathlib
import sys

import lupa.lua52 as lua52
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

import _allowance  # noqa: E402
from bridge.factorio import god_tools  # noqa: E402


def game(settings_lua):
    """A run_lua that runs the Lua it is given against a tiny game with the given `settings.global`."""
    out = []
    rt = lua52.LuaRuntime(unpack_returned_tuples=True)
    rt.execute("settings = {global = %s} rcon = {} helpers = {}" % settings_lua)
    rt.globals().rcon.print = lambda s: out.append(str(s))
    rt.globals().helpers.table_to_json = lambda t: "{" + ",".join("%s=%s" % (k, t[k]) for k in sorted(t.keys())) + "}"

    def run_lua(code):
        out.clear()
        rt.execute(code)
        return "".join(out)
    return run_lua


def test_the_switch_is_read_from_the_game_and_missing_means_on():
    assert _allowance.allowed("free-upgrades", game("{}")) is True                                         # a game without the mod
    assert _allowance.allowed("free-upgrades", game("{['skippy-allow-free-upgrades']={value=true}}")) is True
    assert _allowance.allowed("free-upgrades", game("{['skippy-allow-free-upgrades']={value=false}}")) is False
    assert _allowance.allowed("free-upgrades", game("{['skippy-allow-free-fuel']={value=false}}")) is True  # another switch


def test_require_stops_a_script_that_would_act_and_lets_a_dry_run_go_on(capsys):
    off = game("{['skippy-allow-unlimited-wire-reach']={value=false}}")
    _allowance.require("unlimited-wire-reach", False, off)                                                  # a dry run: no exit
    with pytest.raises(SystemExit) as stop:
        _allowance.require("unlimited-wire-reach", True, off)
    assert stop.value.code == 3 and "unlimited-wire-reach" in capsys.readouterr().err
    _allowance.require("unlimited-wire-reach", True, game("{}"))                                           # no switch: on


def test_the_starter_fuel_tool_refuses_when_free_fuel_is_off():
    tools = {}

    class Mcp:
        def tool(self):
            return lambda f: tools.setdefault(f.__name__, f)
    sent = []
    god_tools.register(Mcp(), lambda lua: sent.append(lua) or "")
    tools["seed_starter_fuel"](0, 0, 10, 10)
    assert "skippy-allow-free-fuel" in sent[0]
    out = game("{['skippy-allow-free-fuel']={value=false}}")(sent[0])
    assert "free-fuel is switched off" in out and "seeded" not in out
