"""A picture after every turn (the Captain, 2026-11-21): drawn from the mod's own map, so a headless test server needs
no game client; each turn is typed into the Skippy panel and answered there; one page holds the run."""
import json
import time

from PIL import Image

from copilot import leg, picture
from copilot.agent import Agent
from copilot.tools import LocalTools
from fakes import FakeModel
from luamod import LuaMod
from test_bridge_with_mod import LuaGame


def test_where_takes_the_last_spot_a_tool_call_of_the_turn_named(tmp_path):
    now = time.time()
    stamp = lambda t: time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t))
    log = tmp_path / "mcp-1.jsonl"
    log.write_text("\n".join(json.dumps(e) for e in [
        {"event": "tool", "name": "tile", "args": {"x": 1, "y": 2}, "time": stamp(now - 100)},          # before the turn
        {"event": "tool", "name": "find_free", "args": {"x": 5, "y": 6, "surface": "nauvis"}, "time": stamp(now)},
        {"event": "tool", "name": "lookup", "args": {"name": "x"}, "time": stamp(now)},                  # no spot
        {"event": "answer", "time": stamp(now)}]) + "\nnot json\n", encoding="utf-8")
    assert picture.where([str(log)], now - 10, now) == (5.0, 6.0, "nauvis")
    assert picture.where([str(tmp_path / "missing.jsonl")], now - 10, now) is None


def test_a_leg_types_in_the_panel_answers_there_and_draws_each_turn(tmp_path):
    mod = LuaMod()
    mod.run("fake.add_player('captain', 0, 0)")
    mod.place("assembling-machine-2", 3.5, 1.5)
    mod.run("game.surfaces.nauvis.create_entity{name='entity-ghost', inner_name='transport-belt', position={6.5, 1.5}}")
    game = LuaGame(mod)
    log = tmp_path / "leg.jsonl"
    agent = Agent(game, FakeModel([[("tile", {"x": 3, "y": 1})], "An assembler stands there.", "Nothing to add."]), log_path=str(log), local=LocalTools(game))
    rows = leg.run(agent, ["what is at 3,1?", "anything else?"], out=lambda s: None, game=game, folder=tmp_path, logs=[str(log)])
    assert [r["picture"] for r in rows] == ["turn-01.png", "turn-02.png"]
    img = Image.open(tmp_path / "turn-01.png")
    assert img.size == (60 * picture.CELL, 40 * picture.CELL + 22)
    talk = [(l["kind"], l["text"]) for l in mod.result("panel_read")["lines"]]
    assert talk[:2] == [("panel", "what is at 3,1?"), ("skippy", "An assembler stands there.")]
    html = picture.page(rows, "Leg test")
    assert html.count("<img") == 2 and "what is at 3,1?" in html and "An assembler stands there." in html


def test_the_picture_colours_ghosts_as_outlines_and_buildings_filled():
    mod = LuaMod()
    mod.place("assembling-machine-2", 1.5, 1.5)
    mod.run("game.surfaces.nauvis.create_entity{name='entity-ghost', inner_name='transport-belt', position={5.5, 1.5}}")
    img = picture.draw(LuaGame(mod), 0, 0, width=20, height=10)
    band = 0
    cell = lambda x, y: ((x + 10) * picture.CELL, band + (y + 5) * picture.CELL)
    cx, cy = cell(1, 1)
    assert img.getpixel((cx + 5, cy + 5)) == picture.COLOURS["A"]
    gx, gy = cell(5, 1)
    assert img.getpixel((gx, gy)) == picture.GHOST and img.getpixel((gx + 5, gy + 5)) == picture.COLOURS["."]
