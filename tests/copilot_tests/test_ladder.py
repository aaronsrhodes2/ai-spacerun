"""Three ways of playing, steps of one ladder (the Captain, 2026-11-13): the player plays by hand and the assistant only
advises; the player plays and the assistant builds on its own from afar; the assistant moves the player's character.
Moving between them must be smooth and chosen in the game: by a word, by one button, or simply by touching the
controls to take the character back. Run under Lua 5.2 against the stand-in game."""
import pathlib
import re

from luamod import LuaMod

ROOT = pathlib.Path(__file__).resolve().parents[2]
MOD = ROOT / "mods" / "skippy-copilot"
CONTROLS = ["move-up", "move-down", "move-left", "move-right", "mine", "build"]
PIECE = {"entities": [{"name": "transport-belt", "x": 5.5, "y": 5.5}]}


def press(mod, control, player=1):
    mod.run("fake.handlers['skippy-hands-%s'] { player_index = %d, tick = game.tick }" % (control, player))


def test_the_button_steps_through_the_three_and_round_again():
    mod = LuaMod()
    mod.run("fake.add_player('captain', 0, 0)")
    button = "game.players[1].gui.top.skippy_light.skippy_mode"
    seen = []
    for _ in range(4):
        seen.append((mod.result("avatar")["mode"], mod.lua.eval(button + ".caption")))
        mod.run("fake.click(1, %s)" % button)
    assert seen == [("free-hand", "builds on its own"), ("my-character", "moves your character"), ("advise", "advises only"), ("free-hand", "builds on its own")]
    assert "Touch your own controls" in mod.lua.eval(button + ".tooltip")


def test_in_advise_mode_the_assistant_looks_and_checks_but_changes_nothing():
    mod = LuaMod()
    assert mod.result("set_mode", {"mode": "advise"}) == {"mode": "advise", "means": "advises only", "changed": True}
    assert mod.result("avatar")["mode_means"] == "advises only"
    assert mod.result("lookup", {"name": "iron-gear-wheel", "kind": "recipe"})                  # looking still works
    assert mod.result("build", dict(PIECE, dry_run=True))["would_place"] == 1                    # and so does checking a plan
    refused = mod.call("build", dict(PIECE, dry_run=False))
    assert refused["ok"] is False and "advise mode" in refused["error"] and "go do it yourself" in refused["hint"]
    assert mod.result("build", dict(PIECE, dry_run=True))["would_place"] == 1                    # nothing was placed
    for tool, args in (("remove", {"x": 0, "y": 0, "width": 4, "height": 4, "dry_run": False}), ("reveal_map", {})):
        assert "advise mode" in mod.call(tool, args)["error"], tool
    walk = mod.call("avatar_walk", {"x": 5, "y": 5})
    assert "advise mode" in walk["error"] and "take over my character" in walk["hint"]


def test_going_up_the_ladder_lets_the_same_request_through():
    mod = LuaMod()
    mod.result("set_mode", {"mode": "advise"})
    assert mod.call("build", dict(PIECE, dry_run=False))["ok"] is False
    mod.result("set_mode", {"mode": "free-hand"})
    assert mod.result("build", dict(PIECE, dry_run=False))["placed"] == 1
    assert "'advise', 'free-hand' or 'my-character'" in mod.call("set_mode", {"mode": "sideways"})["error"]


def test_touching_the_controls_takes_the_character_back_at_once():
    mod = LuaMod()
    mod.result("set_mode", {"mode": "my-character"})
    mod.run("fake.players_have_bodies = true fake.add_player('captain', 20, 20)")
    mod.result("avatar_walk", {"x": 60, "y": 20})
    mod.tick(30)
    assert mod.result("avatar")["job"]["kind"] == "walk"
    press(mod, "move-left")
    state = mod.result("avatar")
    assert state.get("job") is None and state["mode"] == "my-character"                     # the job ends, the mode stays
    assert state["last_job"]["ok"] is False and "the player took the controls" in state["last_job"]["reason"]
    assert mod.lua.eval("game.players[1].character.walking_state.walking") is False
    assert "You have the controls. I stopped the walk" in mod.printed()[-1]
    x = mod.lua.eval("game.players[1].position.x")
    mod.tick(120)
    assert mod.lua.eval("game.players[1].position.x") == x                                  # and it really has let go
    assert mod.result("avatar_walk", {"x": 24, "y": 20})["job"]                             # asked again, it moves again


def test_the_controls_only_matter_while_the_assistant_is_moving_that_player():
    mod = LuaMod()
    mod.run("fake.players_have_bodies = true fake.add_player('captain', 20, 20)")
    before = len(mod.printed())
    press(mod, "build")                                                                    # free-hand: the player just plays
    mod.result("set_mode", {"mode": "my-character"})
    press(mod, "mine")                                                                     # nothing is running
    assert len(mod.printed()) == before

    alone = LuaMod()                                                                       # nobody's character: the mod's own body walks on
    alone.result("set_mode", {"mode": "my-character"})
    alone.result("avatar_walk", {"x": 30, "y": 0})
    alone.run("fake.add_player('visitor', 5, 5)")
    press(alone, "move-up")
    assert alone.result("avatar")["job"]["kind"] == "walk"


def test_every_control_listened_to_is_defined_and_takes_nothing_from_the_player():
    data = (MOD / "data.lua").read_text(encoding="utf-8")
    control = (MOD / "control.lua").read_text(encoding="utf-8")
    listed = lambda src: re.findall(r'"((?:move-\w+|mine|build))"', src)
    assert listed(data) == CONTROLS and listed(control) == CONTROLS
    assert 'key_sequence = ""' in data and "linked_game_control = control" in data and "consuming" not in data
    mod = LuaMod()
    for c in CONTROLS:
        assert mod.lua.eval("fake.handlers['skippy-hands-%s'] ~= nil" % c), c


def test_the_setting_the_words_and_the_skill_all_name_the_three():
    settings = (MOD / "settings.lua").read_text(encoding="utf-8")
    assert 'allowed_values = { "advise", "free-hand", "my-character" }' in settings and 'default_value = "free-hand"' in settings
    locale = (MOD / "locale" / "en" / "skippy-copilot.cfg").read_text(encoding="utf-8")
    for line in ("skippy-copilot-mode-advise=Advises only", "skippy-copilot-mode-free-hand=Builds on its own", "skippy-copilot-mode-my-character=Moves your character"):
        assert line in locale
    prompt = (ROOT / "copilot" / "prompt.md").read_text(encoding="utf-8")
    for words in ("three modes", "just advise me", "go do it yourself", "take over my character", "the player took the controls"):
        assert words in prompt, words
    assert "co-pilot" not in prompt.lower() and "copilot" not in prompt.lower()
