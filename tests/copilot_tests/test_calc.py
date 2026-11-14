import pytest

from copilot.plan import calc
from copilot.plan.calc import PlanError

GEAR = {"name": "iron-gear-wheel", "seconds": 0.5, "ingredients": [{"name": "iron-plate", "type": "item", "amount": 2}],
        "products": [{"name": "iron-gear-wheel", "type": "item", "amount": 1}]}
CABLE = {"name": "copper-cable", "seconds": 0.5, "ingredients": [{"name": "copper-plate", "type": "item", "amount": 1}],
         "products": [{"name": "copper-cable", "type": "item", "amount": 2}]}
CIRCUIT = {"name": "electronic-circuit", "seconds": 0.5,
           "ingredients": [{"name": "iron-plate", "type": "item", "amount": 1}, {"name": "copper-cable", "type": "item", "amount": 3}],
           "products": [{"name": "electronic-circuit", "type": "item", "amount": 1}]}
RED = {"name": "automation-science-pack", "seconds": 5,
       "ingredients": [{"name": "copper-plate", "type": "item", "amount": 1}, {"name": "iron-gear-wheel", "type": "item", "amount": 1}],
       "products": [{"name": "automation-science-pack", "type": "item", "amount": 1}]}
CRUSH = {"name": "metallic-asteroid-crushing", "seconds": 2, "ingredients": [{"name": "metallic-asteroid-chunk", "type": "item", "amount": 1}],
         "products": [{"name": "iron-ore", "type": "item", "amount": 20}, {"name": "metallic-asteroid-chunk", "type": "item", "amount": 1, "probability": 0.2}]}
BOOK = {r["name"]: r for r in (GEAR, CABLE, CIRCUIT, RED)}


def test_one_machine_rate():
    assert calc.machine_rate(GEAR, "iron-gear-wheel", 0.5) == 1.0            # 1 gear per 0.5 s at speed 0.5
    assert calc.machine_rate(CABLE, "copper-cable", 0.75) == pytest.approx(3.0)
    assert calc.machine_rate(GEAR, "iron-gear-wheel", 1.0, productivity=0.5) == pytest.approx(3.0)


def test_probability_counts_as_an_average():
    assert calc.amount_of(CRUSH["products"], "metallic-asteroid-chunk") == pytest.approx(0.2)
    assert calc.machine_rate(CRUSH, "iron-ore", 1.0) == pytest.approx(10.0)


def test_machines_for_a_rate_round_up_and_list_inputs():
    r = calc.machines_for(CIRCUIT, "electronic-circuit", 5, 0.75)
    assert r["machines_exact"] == pytest.approx(5 / 1.5) and r["machines"] == 4
    assert r["inputs_per_second"] == {"iron-plate": pytest.approx(5), "copper-cable": pytest.approx(15)}


def test_an_exact_fit_is_not_rounded_up_by_float_noise():
    assert calc.machines_for(GEAR, "iron-gear-wheel", 3.0, 0.5)["machines"] == 3
    assert calc.machines_for(CABLE, "copper-cable", 0.3 * 10, 0.75)["machines"] == 1


def test_productivity_cuts_the_inputs():
    r = calc.machines_for(GEAR, "iron-gear-wheel", 3.0, 1.0, productivity=0.5)
    assert r["inputs_per_second"]["iron-plate"] == pytest.approx(4.0) and r["machines"] == 1


def test_belts():
    assert calc.belts_for(15) == {"belts": 1, "lanes": 2, "fills_one_belt": 1.0}
    assert calc.belts_for(7.5)["lanes"] == 1 and calc.belts_for(16)["belts"] == 2
    assert calc.belts_for(45, 45)["belts"] == 1


def test_chain_for_red_science():
    plan = calc.chain("automation-science-pack", 1.0, BOOK.get, lambda r: 0.5)
    steps = {s["recipe"]: s for s in plan["steps"]}
    assert [s["recipe"] for s in plan["steps"]] == ["iron-gear-wheel", "automation-science-pack"]      # ingredients first
    assert steps["automation-science-pack"]["machines"] == 10 and steps["iron-gear-wheel"]["machines"] == 1
    assert plan["raw_per_second"] == {"copper-plate": pytest.approx(1.0), "iron-plate": pytest.approx(2.0)}


def test_chain_adds_up_an_item_used_in_two_places():
    both = {"name": "both", "seconds": 1, "ingredients": [{"name": "iron-gear-wheel", "amount": 1}, {"name": "electronic-circuit", "amount": 1}],
            "products": [{"name": "both", "amount": 1}]}
    book = dict(BOOK, both=both)
    plan = calc.chain("both", 2.0, book.get, lambda r: 1.0)
    assert plan["raw_per_second"]["iron-plate"] == pytest.approx(2 * 2 + 2 * 1)              # gears and circuits both take iron
    assert plan["raw_per_second"]["copper-plate"] == pytest.approx(2 * 3 / 2)                 # 3 cable per circuit, 2 cable per plate
    assert [s["recipe"] for s in plan["steps"]][-1] == "both"


def test_chain_stops_at_items_named_raw():
    plan = calc.chain("electronic-circuit", 1.0, BOOK.get, lambda r: 1.0, raw=["copper-cable"])
    assert plan["raw_per_second"] == {"iron-plate": pytest.approx(1), "copper-cable": pytest.approx(3)}
    assert len(plan["steps"]) == 1


def test_chain_uses_productivity_per_recipe():
    plan = calc.chain("electronic-circuit", 1.5, BOOK.get, lambda r: 1.0, productivity_for=lambda r: 0.5 if r["name"] == "electronic-circuit" else 0.0)
    assert plan["raw_per_second"]["iron-plate"] == pytest.approx(1.0)


def test_refusals_say_what_is_wrong():
    with pytest.raises(PlanError, match="does not make"):
        calc.machine_rate(GEAR, "copper-cable", 1)
    with pytest.raises(PlanError, match="above zero"):
        calc.machines_for(GEAR, "iron-gear-wheel", 0, 1)
    with pytest.raises(PlanError, match="no crafting time"):
        calc.machine_rate(dict(GEAR, seconds=0), "iron-gear-wheel", 1)
    loop = {"name": "kovarex", "seconds": 60, "ingredients": [{"name": "u235", "amount": 40}], "products": [{"name": "u235", "amount": 41}]}
    with pytest.raises(PlanError, match="its own product"):
        calc.chain("u235", 1, {"u235": loop}.get, lambda r: 1)
