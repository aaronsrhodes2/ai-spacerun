"""Every way one building can be connected, worked out from the game's facts about it (the Captain, 2026-11-13: each
building has a finite number of joint configurations)."""
import pytest

from copilot.tools import LocalTools
from luamod import LuaMod
from test_bridge_with_mod import LuaGame


@pytest.fixture
def tools():
    mod = LuaMod()
    mod.run("prototypes.recipe['sulfuric-acid'] = { name = 'sulfuric-acid', energy = 1, categories = { chemistry = true }, "
            "ingredients = { { type = 'item', name = 'iron-plate', amount = 1 }, { type = 'fluid', name = 'water', amount = 100 } }, "
            "products = { { type = 'fluid', name = 'sulfuric-acid', amount = 50 } } } "
            "prototypes.recipe['three-fluids'] = { name = 'three-fluids', energy = 1, categories = { chemistry = true }, "
            "ingredients = { { type = 'fluid', name = 'a', amount = 1 }, { type = 'fluid', name = 'b', amount = 1 }, { type = 'fluid', name = 'c', amount = 1 } }, products = {} } "
            "prototypes.recipe['five-items'] = { name = 'five-items', energy = 1, categories = { crafting = true }, products = {}, "
            "ingredients = { { type = 'item', name = 'a', amount = 1 }, { type = 'item', name = 'b', amount = 1 }, { type = 'item', name = 'c', amount = 1 }, "
            "{ type = 'item', name = 'd', amount = 1 }, { type = 'item', name = 'e', amount = 1 } } } "
            "for _, n in pairs({ 'sulfuric-acid', 'three-fluids', 'five-items' }) do game.forces.player.recipes[n] = { name = n, enabled = true, ingredients = {}, products = {} } end")
    return LocalTools(LuaGame(mod))


def ok(tools, args):
    r = tools.call("connections", args)
    assert r["ok"], r
    return r["result"]


def test_a_plain_assembler_has_all_its_sides_free():
    c = ok(tools=LocalTools(LuaGame(LuaMod())), args={"machine": "assembling-machine-2"})
    assert (c["tiles_wide"], c["tiles_high"]) == (3, 3) and c["heat_connections"] is None
    assert all(s == {"tiles": 3, "fluid_connections": [], "tiles_free_for_inserters": 3} for s in c["sides"].values())
    assert [w["way"] for w in c["ways"]] == ["items by belt", "items by robots", "items straight from a neighbouring machine"]


def test_a_chemical_plant_has_inputs_north_and_outputs_south(tools):
    c = ok(tools, {"machine": "chemical-plant"})
    assert c["sides"]["north"] == {"tiles": 3, "fluid_connections": [{"flow": "input", "fluid": None}, {"flow": "input", "fluid": None}], "tiles_free_for_inserters": 1}
    assert [p["flow"] for p in c["sides"]["south"]["fluid_connections"]] == ["output", "output"] and c["sides"]["south"]["fluid_connections"][0]["fluid"] == "water"
    assert c["sides"]["east"]["tiles_free_for_inserters"] == 3 and c["sides"]["west"]["fluid_connections"] == []
    ways = [w["way"] for w in c["ways"]]
    assert "fluids by pipe" in ways and "items by belt and fluids by pipe together" in ways and "turning the building turns them" in c["note"]


def test_heat_connections_are_counted(tools):
    c = ok(tools, {"machine": "heating-tower"})
    assert c["heat_connections"] == 4 and c["ways"][-1]["way"] == "heat"


def test_a_recipe_with_an_item_and_a_fluid_points_at_the_joint_that_fits(tools):
    r = ok(tools, {"machine": "chemical-plant", "recipe": "sulfuric-acid"})["for_recipe"]
    assert r["items_in"] == ["iron-plate"] and r["fluids_in"] == ["water"] and r["fluids_out"] == ["sulfuric-acid"]
    assert r["belts_needed_for_items"] == "one belt" and r["joint_that_fits"] == "fluid_machine_on_belts" and r["problems"] is None


def test_two_items_share_a_belt_and_four_need_two_belts(tools):
    r = ok(tools, {"machine": "assembling-machine-2", "recipe": "electronic-circuit"})["for_recipe"]
    assert "a lane for each item" in r["belts_needed_for_items"] and r["joint_that_fits"].startswith("plan_row")
    r = ok(tools, {"machine": "assembling-machine-2", "recipe": "five-items"})["for_recipe"]
    assert "feed it by robots" in r["belts_needed_for_items"]


def test_a_recipe_that_needs_more_fluid_inputs_than_the_building_has_is_flagged(tools):
    r = ok(tools, {"machine": "chemical-plant", "recipe": "three-fluids"})["for_recipe"]
    assert r["problems"] == ["the recipe takes 3 fluids and the building has 2 fluid inputs"] and r["joint_that_fits"] == "machine_ports"
    assert r["belts_needed_for_items"] == "none"


def test_refusals(tools):
    assert "cannot run the recipe" in tools.call("connections", {"machine": "stone-furnace", "recipe": "sulfuric-acid"})["error"]
    assert "nothing is named" in tools.call("connections", {"machine": "warp-core"})["error"]
    assert "needs the parameter 'machine'" in tools.call("connections", {})["error"]
