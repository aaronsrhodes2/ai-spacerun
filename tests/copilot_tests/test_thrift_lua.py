"""Wasting nothing and using little ground (the Captain, 2026-11-13), run under Lua 5.2 against the stand-in game."""
import pathlib

import pytest

from luamod import LuaMod

ROOT = pathlib.Path(__file__).resolve().parents[2]


@pytest.fixture
def mod():
    return LuaMod()


def rates(mod, **items):
    for name, (made, used) in items.items():
        mod.run("game.forces.player.rate[%r] = { %s, %s }" % (name.replace("_", "-"), made, used))


def test_surpluses_and_shortfalls_are_told_apart(mod):
    rates(mod, iron_plate=(900, 300), copper_plate=(400, 399), copper_cable=(600, 600), iron_gear_wheel=(50, 45), coal=(0.4, 0))
    s = mod.result("surplus")
    assert [(e["item"], e["spare_per_minute"]) for e in s["surpluses"]] == [("iron-plate", 600)]
    assert [e["item"] for e in s["shortfalls"]] == ["copper-cable", "copper-plate"]          # used as fast as made, busiest first
    assert "iron-gear-wheel" not in str(s["surpluses"]) and "coal" not in str(s["surpluses"])   # a tenth over, or a trickle, is not a surplus
    assert s["surpluses"][0] == {"item": "iron-plate", "made_per_minute": 900, "used_per_minute": 300, "spare_per_minute": 600}


def test_the_biggest_surplus_comes_first_and_the_list_is_cut(mod):
    rates(mod, iron_plate=(900, 300), coal=(500, 0), copper_plate=(100, 10))
    s = mod.result("surplus", {"top": 2})
    assert [e["item"] for e in s["surpluses"]] == ["iron-plate", "coal"]


def test_the_order_for_dealing_with_a_surplus_is_given(mod):
    order = mod.result("surplus")["what_to_do_with_a_surplus"]
    assert order.index("make less") < order.index("something useful") < order.index("void") and "reprocess" in order


def test_full_chests_are_counted_with_what_fills_them(mod):
    mod.place("wooden-chest", 5.5, 5.5, items={"iron-plate": 800, "coal": 3})
    mod.place("wooden-chest", 9.5, 5.5, items={"coal": 3})
    mod.run("game.surfaces.nauvis.entities[1].full = true")
    s = mod.result("surplus")
    assert s["full_chests"] == 1 and s["full_chest_examples"] == [{"chest": "wooden-chest", "surface": "nauvis", "x": 5.5, "y": 5.5, "mostly": "iron-plate"}]


def test_surplus_on_one_surface_or_all(mod):
    rates(mod, iron_plate=(900, 300))
    mod.run("fake.add_planet('vulcanus', true) game.forces.player.rate_elsewhere['iron-plate'] = { 0, 300 }")
    assert mod.result("surplus")["surpluses"][0]["spare_per_minute"] == 300       # the other planet uses half of the spare
    assert mod.result("surplus", {"surface": "nauvis"})["surpluses"][0]["spare_per_minute"] == 600
    assert "no surface named" in mod.call("surplus", {"surface": "mars"})["error"]


def test_an_idle_factory_has_nothing_to_report(mod):
    s = mod.result("surplus")
    assert s["surpluses"] == {} and s["shortfalls"] == {} and s["full_chests"] == 0


def block(mod):
    mod.place("assembling-machine-2", 11.5, 11.5, recipe="iron-gear-wheel")
    mod.place("assembling-machine-2", 21.5, 11.5, recipe="iron-gear-wheel")
    mod.place("assembling-machine-2", 11.5, 21.5, recipe="copper-cable")
    for x in range(10, 23):
        mod.place("transport-belt", x + 0.5, 16.5, direction=4)
    mod.place("inserter", 11.5, 13.5)


def test_footprint_measures_the_ground_a_block_really_uses(mod):
    block(mod)
    f = mod.result("footprint", {"x": 0, "y": 0, "width": 40, "height": 40})
    assert f["buildings"] == 17 and f["pieces"] == {"assembling-machine-2": 3, "transport-belt": 13, "inserter": 1}
    assert f["recipes"] == ["copper-cable x1", "iron-gear-wheel x2"]
    assert f["tight_rectangle"] == {"from_x": 10, "from_y": 10, "to_x": 22, "to_y": 22, "width": 13, "height": 13}
    assert (f["tiles_in_rectangle"], f["tiles_covered"], f["tiles_empty"], f["filled"]) == (169, 41, 128, "24%")
    assert "ask the player before removing the old one" in f["to_compact"]


def test_a_compacted_block_shows_fewer_tiles_for_the_same_work(mod):
    block(mod)
    before = mod.result("footprint", {"x": 0, "y": 0, "width": 40, "height": 40})
    for i, recipe in enumerate(("iron-gear-wheel", "iron-gear-wheel", "copper-cable")):      # the same three machines in a row with shared belts
        mod.place("assembling-machine-2", 51.5 + 3 * i, 12.5, recipe=recipe)
        mod.place("inserter", 51.5 + 3 * i, 10.5)
    for x in range(50, 59):
        mod.place("transport-belt", x + 0.5, 9.5, direction=4)
    after = mod.result("footprint", {"x": 45, "y": 0, "width": 40, "height": 40})
    assert after["recipes"] == before["recipes"]
    assert after["tiles_in_rectangle"] == 45 and after["tiles_in_rectangle"] < before["tiles_in_rectangle"] / 3 and after["filled"] == "87%"


def test_footprint_counts_only_what_is_ours_and_refuses_what_it_cannot_measure(mod):
    mod.place("iron-ore", 5.5, 5.5, amount=10, force=False)
    mod.place("tree-01", 6.5, 5.5, force=False)
    mod.place("entity-ghost", 8.5, 8.5, inner_name="lab")
    assert mod.result("footprint", {"x": 0, "y": 0, "width": 20, "height": 20}) == {"buildings": 0, "note": "nothing of ours stands in that rectangle"}
    assert "between 1 and 100" in mod.call("footprint", {"x": 0, "y": 0, "width": 101, "height": 5})["error"]


def test_the_skill_carries_both_aims():
    prompt = (ROOT / "copilot" / "prompt.md").read_text(encoding="utf-8")
    assert "Waste nothing" in prompt and "make less of it, make something useful from it, and only then recycle or void it" in prompt
    assert "To compact a block" in prompt and "`footprint`" in prompt and "ask the player before removing the old one" in prompt
