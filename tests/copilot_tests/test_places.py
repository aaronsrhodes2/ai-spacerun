"""Place names: the force's map tags read as an address book; only the mod's own tags are moved or removed by it."""
import pytest

from luamod import LuaMod


@pytest.fixture
def mod():
    m = LuaMod()
    m.run("fake.add_player('captain', 0, 0)")
    return m


def players_tag(mod, text, x, y):
    mod.run("game.forces.player.add_chart_tag(game.surfaces.nauvis, {position = {%d, %d}, text = %r})" % (x, y, text))


def test_marking_listing_and_finding_by_name(mod):
    r = mod.result("mark_place", {"name": "Copper outpost B", "x": 40, "y": -12, "icon": "copper-plate"})
    assert r["place"] == {"name": "Copper outpost B", "surface": "nauvis", "x": 40, "y": -12, "icon": "item:copper-plate", "ours": True}
    players_tag(mod, "Home", 0, 0)
    names = [p["name"] for p in mod.result("places")["places"]]
    assert names == ["Copper outpost B", "Home"]
    assert [p["name"] for p in mod.result("places", {"near": "copper"})["places"]] == ["Copper outpost B"]


def test_marking_again_moves_our_tag_and_never_the_players(mod):
    mod.result("mark_place", {"name": "build site", "x": 1, "y": 1})
    r = mod.result("mark_place", {"name": "Build Site", "x": 9, "y": 9})
    assert r["moved"] is True and mod.result("places")["count"] == 1 and r["place"]["x"] == 9
    players_tag(mod, "Home", 0, 0)
    assert "player's own tag" in mod.call("mark_place", {"name": "home", "x": 5, "y": 5})["error"]
    assert "player's tag" in mod.call("forget_place", {"name": "home"})["error"]
    assert mod.result("forget_place", {"name": "build"})["removed"]["name"] == "Build Site"   # one tag contains it: that one
    assert mod.result("places")["count"] == 1


def test_names_that_fit_several_places_or_none_are_refused(mod):
    mod.result("mark_place", {"name": "iron east", "x": 1, "y": 1})
    mod.result("mark_place", {"name": "iron west", "x": 2, "y": 2})
    assert "more than one place" in mod.call("forget_place", {"name": "iron"})["error"]
    assert "no place named" in mod.call("forget_place", {"name": "gold"})["error"]


def test_uncharted_ground_takes_no_tag_and_a_bad_icon_is_named(mod):
    mod.run("fake.uncharted = true")
    assert "charted" in mod.call("mark_place", {"name": "far", "x": 900, "y": 900})["hint"]
    mod.run("fake.uncharted = false")
    assert "no item or signal" in mod.call("mark_place", {"name": "x", "x": 1, "y": 1, "icon": "item:unobtainium"})["error"]


def test_find_placement_takes_a_place_name(mod):
    mod.result("mark_place", {"name": "belt spot", "x": 20, "y": 20})
    r = mod.result("find_placement", {"name": "transport-belt", "at": "belt spot", "radius": 2})
    assert r["found"] and r["places"][0]["tile_x"] == 20
    assert "say where" in mod.call("find_placement", {"name": "transport-belt"})["error"]
