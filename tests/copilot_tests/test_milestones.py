import pathlib
import re

import pytest

from copilot import milestones as ms
from copilot.milestones import MILESTONES, Watch

EMPTY = {"researched": [], "produced": {}, "built": {}, "rockets_launched": 0, "platforms": [], "planets_reached": [], "won": False, "hours_played": 0.0}


def facts(**kw):
    return dict(EMPTY, **kw)


def test_the_list_is_well_formed():
    ids = [m["id"] for m in MILESTONES]
    assert len(ids) == len(set(ids)) and len(ids) >= 20
    allowed = {"produced", "researched", "built", "launched", "platforms", "reached", "platform_at", "won"}
    for m in MILESTONES:
        assert m["title"] and m["hint"] and m["test"] and set(m["test"]) <= allowed, m["id"]
    assert ids.index("first-plates") < ids.index("rocket-silo") < ids.index("platform") < ids.index("aquilo") < ids.index("edge") < ids.index("won")


def test_the_mod_is_asked_to_count_exactly_what_the_tests_need():
    items, entities = ms.wanted()
    assert "iron-plate" in items and "cryogenic-science-pack" in items and "rocket-silo" in entities and "lab" in entities
    assert items == sorted(set(items)) and entities == sorted(set(entities))


def test_a_new_game_has_done_nothing_and_is_pointed_at_the_first_step():
    s = ms.summary(EMPTY)
    assert s["done"] == 0 and s["of"] == len(MILESTONES) and s["won"] is False
    assert s["next"][0]["id"] == "first-plates"
    assert s["next"][0]["still_needs"] == ["50 more iron-plate made (0 of 50)", "10 more copper-plate made (0 of 10)"]
    assert len(s["after_that"]) == 2 and s["after_that"][0] == "Make electricity"


def test_what_is_missing_is_said_in_numbers():
    m = ms.missing({"produced": {"iron-plate": 50}, "researched": ["steam-power"], "built": {"lab": 2}},
                   facts(produced={"iron-plate": 30}, built={"lab": 2}))
    assert m == ["20 more iron-plate made (30 of 50)", "research steam-power"]


def test_each_kind_of_test():
    assert ms.missing({"launched": 1}, EMPTY) == ["launch a rocket"] and ms.missing({"launched": 1}, facts(rockets_launched=3)) == []
    assert ms.missing({"platforms": 1}, EMPTY) == ["a space platform"]
    assert ms.missing({"platforms": 1}, facts(platforms=[{"name": "x", "at": "nauvis"}])) == []
    assert ms.missing({"reached": ["vulcanus"]}, facts(planets_reached=["nauvis"])) == ["something of ours on vulcanus"]
    assert ms.missing({"platform_at": "solar-system-edge"}, facts(platforms=[{"name": "x", "at": "aquilo"}])) == ["a platform at solar-system-edge"]
    assert ms.missing({"platform_at": "solar-system-edge"}, facts(platforms=[{"name": "x", "at": "solar-system-edge"}])) == []
    assert ms.missing({"won": True}, EMPTY) == ["the game's win"] and ms.missing({"won": True}, facts(won=True)) == []


def test_milestones_count_in_any_order_and_the_next_is_the_first_gap():
    f = facts(produced={"iron-plate": 500, "copper-plate": 500, "steel-plate": 100}, researched=["steel-processing"])
    s = ms.summary(f)
    assert s["done_ids"] == ["first-plates", "steel"] and s["next"][0]["id"] == "power"


def test_a_finished_game():
    items, entities = ms.wanted()
    everything = facts(
        produced={i: 10 ** 6 for i in items}, built={e: 100 for e in entities},
        researched=sorted({t for m in MILESTONES for t in m["test"].get("researched", [])}),
        rockets_launched=500, platforms=[{"name": "Edge Ship", "at": "solar-system-edge"}],
        planets_reached=["nauvis", "vulcanus", "fulgora", "gleba", "aquilo"], won=True)
    s = ms.summary(everything)
    assert s["done"] == s["of"] and s["next"] == [] and s["after_that"] == [] and s["won"] is True


def test_the_watch_stays_quiet_while_anything_moves():
    w = Watch(patience_hours=2)
    assert w.check(facts(hours_played=0)) is None
    assert w.check(facts(hours_played=1.5, produced={"iron-plate": 10})) is None                # counting toward a milestone
    assert w.check(facts(hours_played=3.0, produced={"iron-plate": 20})) is None
    assert w.check(facts(hours_played=4.9, produced={"iron-plate": 20}, researched=["automation"])) is None      # research is progress too


def test_the_watch_reports_a_stall_and_recovers():
    w = Watch(patience_hours=2)
    f = facts(hours_played=1.0, produced={"iron-plate": 20})
    assert w.check(f) is None
    assert w.check(dict(f, hours_played=2.5)) is None
    said = w.check(dict(f, hours_played=3.2))
    assert said == "stalled: nothing counted toward any milestone for 2.2 game hours"
    assert w.check(dict(f, hours_played=3.3, produced={"iron-plate": 21})) is None
    assert w.check(dict(f, hours_played=4.0, produced={"iron-plate": 21})) is None


def test_making_more_of_something_already_counted_in_full_is_not_progress():
    w = Watch(patience_hours=1)
    assert w.check(facts(hours_played=0, produced={"iron-plate": 50, "copper-plate": 10})) is None
    assert w.check(facts(hours_played=1.5, produced={"iron-plate": 90000, "copper-plate": 90000})) is not None


def game_data_names():
    """Every prototype name in the installed game's data files, or None if the game is not installed here."""
    root = pathlib.Path("D:/Steam/steamapps/common/Factorio/data")
    if not root.exists():
        return None
    names = set()
    for sub in ("base", "space-age", "quality", "elevated-rails"):
        for f in (root / sub).rglob("*.lua"):
            names.update(re.findall(r'name\s*=\s*"([a-z0-9-]+)"', f.read_text(encoding="utf-8", errors="ignore")))
    return names


def test_every_name_in_the_list_exists_in_the_installed_game():
    names = game_data_names()
    if names is None:
        pytest.skip("Factorio is not installed on this machine")
    items, entities = ms.wanted()
    techs = sorted({t for m in MILESTONES for t in m["test"].get("researched", [])})
    planets = sorted({p for m in MILESTONES for p in m["test"].get("reached", [])} | {m["test"]["platform_at"] for m in MILESTONES if "platform_at" in m["test"]})
    unknown = [n for n in items + entities + techs + planets if n not in names]
    assert not unknown, "not in the game's data: %s" % unknown
