"""The allowances: one list of deliberate rule relaxations, a switch for each, the two the mod keeps itself, and the tools."""
import re

import pytest

from luamod import MOD, LuaMod
from test_mod_lua import BELT


@pytest.fixture
def mod():
    return LuaMod()


@pytest.fixture
def scene():
    return LuaMod().scene()


def rows():
    """The ids and kinds read out of skippy_allowances.lua itself, not from the mod under test."""
    text = (MOD / "skippy_allowances.lua").read_text(encoding="utf-8")
    return re.findall(r'\{ id = "([a-z-]+)", kept_by = "(\w+)"', text)


def test_the_list_has_the_captains_allowances_each_with_a_kind():
    found = dict(rows())
    for must in ("free-placement", "free-upgrades", "unlimited-wire-reach", "ring-foundations", "free-fuel", "player-boosts", "infinite-scrap"):
        assert must in found
    assert set(found.values()) <= {"mod", "skill", "script"} and len(found) == len(rows())


def test_every_allowance_has_a_setting_and_words_for_it():
    text = (MOD / "locale" / "en" / "skippy-copilot.cfg").read_text(encoding="utf-8")
    settings = (MOD / "settings.lua").read_text(encoding="utf-8")
    assert 'require("skippy_allowances")' in settings and '"skippy-allow-" .. row.id' in settings and "default_value = true" in settings
    for allow_id, _ in rows():
        assert text.count("skippy-allow-%s=" % allow_id) == 2, allow_id                 # a name and a description


def test_allowances_lists_all_of_them_on(mod):
    r = mod.result("allowances")
    assert [a["id"] for a in r["allowances"]] == [i for i, _ in rows()]
    assert r["off"] == 0 and r["note"] == "every allowance is on" and all(a["on"] and a["vanilla"] and a["means"] for a in r["allowances"])


def test_set_allowance_switches_one_and_tells_who_keeps_it(mod):
    r = mod.result("set_allowance", {"id": "free-fuel", "on": False})
    assert r["on"] is False and r["changed"] is True and r["kept_by"] == "skill" and "obey" in r["means"]
    r = mod.result("allowances")
    assert r["off"] == 1 and "follow vanilla" in r["note"] and [a for a in r["allowances"] if a["id"] == "free-fuel"][0]["on"] is False
    assert mod.result("set_allowance", {"id": "free-fuel", "on": False})["changed"] is False
    assert "no allowance named" in mod.call("set_allowance", {"id": "nope", "on": True})["error"]


def test_a_missing_setting_counts_as_on_and_cannot_be_set(mod):
    mod.run("settings.global['skippy-allow-free-fuel'] = nil")
    assert [a for a in mod.result("allowances")["allowances"] if a["id"] == "free-fuel"][0]["on"] is True
    assert "does not exist" in mod.call("set_allowance", {"id": "free-fuel", "on": False})["error"]


def test_free_placement_off_refuses_building_in_free_hand_mode(scene):
    assert scene.result("build", {"entities": [BELT]})["would_place"] == 1
    scene.result("set_allowance", {"id": "free-placement", "on": False})
    r = scene.call("build", {"entities": [BELT], "dry_run": False})
    assert "free-placement" in r["error"] and "moves your character" in r["hint"]
    assert scene.result("tile", {"x": 15, "y": 8})["free"] is True                       # nothing was placed
    scene.result("set_allowance", {"id": "free-placement", "on": True})
    assert scene.result("build", {"entities": [BELT], "dry_run": False})["placed"] == 1


def test_remote_exploring_off_refuses_revealing_the_map(scene):
    scene.result("set_allowance", {"id": "remote-exploring", "on": False})
    r = scene.call("reveal_map", {"depth": 64})
    assert "remote-exploring" in r["error"] and "walk_to" in r["hint"]
    scene.result("set_allowance", {"id": "remote-exploring", "on": True})
    assert scene.result("reveal_map", {"depth": 64})["now"]
