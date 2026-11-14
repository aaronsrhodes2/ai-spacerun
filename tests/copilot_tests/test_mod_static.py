"""Checks on the mod's Lua that need no Lua interpreter and no game. They do not prove the Lua runs; they catch the slips
that would stop the mod loading (an unclosed block, a missing file, two tools with one name) and keep the bridge and the
mod agreeing on tool names. The real test of the Lua is scripts/modcheck.py against a test server."""
import json
import pathlib
import re

from copilot.agent import BRIDGE_ONLY, PLAN_ONLY
from copilot.tools import SPECS

MOD = pathlib.Path(__file__).resolve().parents[2] / "mods" / "skippy-copilot"
LUA = sorted(MOD.glob("**/*.lua"))


def strip(source):
    """Lua source with comments and string contents removed, so words inside them are not counted as code."""
    out, i, n = [], 0, len(source)
    while i < n:
        c = source[i]
        if source.startswith("--[[", i):
            i = source.index("]]", i) + 2
        elif source.startswith("--", i):
            while i < n and source[i] != "\n":
                i += 1
        elif source.startswith("[[", i):
            i = source.index("]]", i) + 2
            out.append('""')
        elif c in "\"'":
            j = i + 1
            while source[j] != c:
                j += 2 if source[j] == "\\" else 1
            i = j + 1
            out.append('""')
        else:
            out.append(c)
            i += 1
    return "".join(out)


def words(code):
    return re.findall(r"[A-Za-z_][A-Za-z_0-9]*", code)


def tool_names():
    names = []
    for f in LUA:
        text = f.read_text(encoding="utf-8")
        for m in re.finditer(r"R\.register\s*\{\s*name\s*=\s*\"([a-z_]+)\"", text):
            names.append((m.group(1), f.name))
    return names


def test_there_is_lua_to_check():
    assert len(LUA) >= 10 and (MOD / "control.lua") in LUA


def test_every_block_is_closed():
    for f in LUA:
        w = words(strip(f.read_text(encoding="utf-8")))
        opens = w.count("function") + w.count("if") + w.count("do")           # for and while each bring their own `do`
        assert opens == w.count("end"), "%s: %d blocks opened, %d closed" % (f.name, opens, w.count("end"))
        assert w.count("repeat") == w.count("until"), f.name


def test_brackets_balance():
    for f in LUA:
        code = strip(f.read_text(encoding="utf-8"))
        for a, b in ("()", "{}", "[]"):
            assert code.count(a) == code.count(b), "%s: %d '%s' but %d '%s'" % (f.name, code.count(a), a, code.count(b), b)


def test_every_required_file_exists():
    for f in LUA:
        for m in re.finditer(r"require\(\"([a-z_.]+)\"\)", f.read_text(encoding="utf-8")):
            assert (MOD / (m.group(1).replace(".", "/") + ".lua")).exists(), "%s requires %s, which is missing" % (f.name, m.group(1))


def test_control_loads_every_script_that_registers_a_tool():
    control = (MOD / "control.lua").read_text(encoding="utf-8")
    for name, fname in tool_names():
        assert 'require("scripts.%s")' % fname[:-4] in control, "%s registers '%s' but control.lua never loads it" % (fname, name)


def test_tool_names_are_unique_and_none_clash_with_the_bridge():
    names = [n for n, _ in tool_names()]
    assert len(names) == len(set(names)), sorted(n for n in names if names.count(n) > 1)
    local = {s["name"] for s in SPECS}
    assert not local & set(names), "the bridge and the mod both define: %s" % (local & set(names))


def test_the_bridge_only_names_tools_the_mod_has():
    names = {n for n, _ in tool_names()}
    assert BRIDGE_ONLY <= names and PLAN_ONLY <= names
    assert {"lookup", "alerts", "bottlenecks", "player", "reveal_map", "diagnose", "map", "tile", "find_free"} <= names


def test_every_tool_has_a_description_and_documented_parameters():
    for f in LUA:
        text = f.read_text(encoding="utf-8")
        for block in re.split(r"R\.register\s*\{", text)[1:]:
            name = re.search(r"name\s*=\s*\"([a-z_]+)\"", block).group(1)
            assert re.search(r"description\s*=\s*\"[^\"]{30,}", block), "%s has no real description" % name
            params = block[block.index("params"):block.index("run = function")]
            for p in re.finditer(r"(\w+)\s*=\s*\{([^{}]*)\}", params):
                if p.group(1) == "params":                        # a tool with no parameters: params = {}
                    continue
                assert "type =" in p.group(2), "%s.%s has no type" % (name, p.group(1))
                assert "description =" in p.group(2), "%s.%s has no description" % (name, p.group(1))


def test_the_prompt_only_mentions_tools_that_exist():
    prompt = (MOD.parents[1] / "copilot" / "prompt.md").read_text(encoding="utf-8")
    known = {n for n, _ in tool_names()} | {s["name"] for s in SPECS}
    for name in re.findall(r"`([a-z_]+)`", prompt):
        if "_" in name or name in known:
            assert name in known, "the prompt mentions `%s`, which is not a tool" % name


def test_info_json_is_valid_and_versioned():
    info = json.loads((MOD / "info.json").read_text(encoding="utf-8"))
    assert info["name"] == "skippy-copilot" and re.fullmatch(r"\d+\.\d+\.\d+", info["version"]) and info["factorio_version"] == "2.1"


def test_design_notes_are_short_plain_sentences():
    text = (MOD / "scripts" / "notes.lua").read_text(encoding="utf-8")
    notes = re.findall(r'^  \["([a-z0-9-]+)"\] = "(.*)",$', text, re.M)
    assert len(notes) >= 30
    for name, note in notes:
        assert 40 <= len(note) <= 320, "%s: %d characters" % (name, len(note))
        assert note.endswith(".") and "\\n" not in note


def test_the_changelog_follows_the_games_strict_format():
    """The game refuses a changelog that strays: a line of exactly 99 dashes, 'Version: x.y.z', an optional 'Date: ',
    category lines indented two spaces ending in a colon, entries indented four spaces starting '- ', no tabs, no
    trailing spaces, no version twice."""
    lines = (MOD / "changelog.txt").read_text(encoding="utf-8").split("\n")
    assert lines[-1] == "", "the file must end with a newline"
    lines = lines[:-1]
    versions, i = [], 0
    while i < len(lines):
        assert lines[i] == "-" * 99, "line %d must be 99 dashes" % (i + 1)
        m = re.fullmatch(r"Version: (\d+)\.(\d+)\.(\d+)", lines[i + 1])
        assert m, "line %d must be 'Version: x.y.z'" % (i + 2)
        versions.append(tuple(int(g) for g in m.groups()))
        i += 2
        if i < len(lines) and lines[i].startswith("Date: "):
            i += 1
        saw_entry = False
        while i < len(lines) and lines[i] != "-" * 99:
            line = lines[i]
            assert "\t" not in line and line == line.rstrip(), "line %d has a tab or trailing space" % (i + 1)
            assert re.fullmatch(r"  [A-Z][A-Za-z ]*:", line) or line.startswith("    - ") or line.startswith("      "), "line %d is not a category or an entry" % (i + 1)
            saw_entry = saw_entry or line.startswith("    - ")
            i += 1
        assert saw_entry, "version %s has no entries" % (versions[-1],)
    assert len(versions) == len(set(versions)) and versions == sorted(versions, reverse=True)
    info = json.loads((MOD / "info.json").read_text(encoding="utf-8"))
    assert ".".join(str(n) for n in versions[0]) == info["version"], "the newest changelog entry must match info.json"


def test_the_setting_and_its_names_agree():
    settings = (MOD / "settings.lua").read_text(encoding="utf-8")
    locale = (MOD / "locale" / "en" / "skippy-copilot.cfg").read_text(encoding="utf-8")
    avatar = (MOD / "scripts" / "avatar.lua").read_text(encoding="utf-8")
    assert 'name = "skippy-copilot-mode"' in settings and 'local SETTING = "skippy-copilot-mode"' in avatar
    for value in ("free-hand", "my-character"):
        assert '"%s"' % value in settings and "skippy-copilot-mode-%s=" % value in locale and '["%s"]' % value in avatar
    assert "skippy-copilot-mode=" in locale
