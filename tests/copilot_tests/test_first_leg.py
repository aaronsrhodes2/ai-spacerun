"""What a first run on a blank map needs: finding ore and water, placing fussy pieces, drills on a patch, joining two
fluid buildings, single pieces, removing and changing things, and research. Research is the player's to steer: when it
runs out the assistant comes to the player with one suggestion (the Captain, 2026-11-13), and it does the same for a new
alert and for an obvious bottleneck."""
import pytest

from copilot.agent import Agent
from copilot.loop import Bridge, bottleneck_prompt, research_prompt
from copilot.plan import joints
from copilot.plan.layout import E, N, S, W, LayoutError
from copilot.tools import LocalTools
from fakes import FakeModel
from luamod import LuaMod
from test_bridge_with_mod import LuaGame

CHARS = {"transport-belt": "b", "electric-mining-drill": "D", "boiler": "B", "steam-engine": "G", "chemical-plant": "M"}


@pytest.fixture
def mod():
    return LuaMod()


@pytest.fixture
def world(mod):
    return mod, LocalTools(LuaGame(mod), sleep=lambda s: mod.tick(30), patience=2000)


def ok(tools, name, args=None):
    r = tools.call(name, args or {})
    assert r["ok"], r
    return r["result"]


def ore(mod, name, x0, y0, w, h, amount=100):
    mod.run("prototypes.entity[%r] = prototypes.entity[%r] or { name = %r, type = 'resource', tile_width = 1, tile_height = 1, items_to_place_this = {} }" % (name, name, name))
    for x in range(x0, x0 + w):
        for y in range(y0, y0 + h):
            mod.run("local s = game.surfaces.nauvis local e = s.create_entity{name = 'iron-ore', position = {%s, %s}, amount = %d, force = false} e.name = %r"
                    % (x + 0.5, y + 0.5, amount, name))


# ---------------------------------------------------------------- finding things

def test_patches_are_found_nearest_first_with_size_and_place(mod):
    ore(mod, "iron-ore", 20, 0, 10, 6)
    ore(mod, "copper-ore", -60, -40, 4, 4, amount=250)
    r = mod.result("find_resources", {"x": 0, "y": 0})
    assert [(p["kind"], p["tiles"], p["amount"]) for p in r["patches"]] == [("iron-ore", 60, 6000), ("copper-ore", 16, 4000)]
    iron = r["patches"][0]
    assert (iron["from_x"], iron["from_y"], iron["to_x"], iron["to_y"]) == (20, 0, 29, 5) and (iron["centre_x"], iron["centre_y"]) == (25, 3)
    assert iron["tiles_away"] < r["patches"][1]["tiles_away"] and r["more_not_shown"] == 0


def test_ore_in_touching_cells_is_one_patch_and_ore_far_apart_is_two(mod):
    ore(mod, "iron-ore", 0, 0, 20, 3)                                       # spans three grid cells
    ore(mod, "iron-ore", 80, 0, 3, 3)
    assert [p["tiles"] for p in mod.result("find_resources", {"x": 0, "y": 0})["patches"]] == [60, 9]


def test_one_kind_only_and_a_kind_that_does_not_exist(mod):
    ore(mod, "iron-ore", 20, 0, 4, 4)
    ore(mod, "copper-ore", 30, 0, 4, 4)
    assert [p["kind"] for p in mod.result("find_resources", {"kind": "copper-ore", "x": 0, "y": 0})["patches"]] == ["copper-ore"]
    assert "no resource named 'unobtainium'" in mod.call("find_resources", {"kind": "unobtainium"})["error"]
    assert "try a larger radius" in mod.result("find_resources", {"kind": "copper-ore", "x": 300, "y": 300, "radius": 20})["hint"]


def test_the_nearest_water(mod):
    for x in range(40, 50):
        for y in range(-10, 10):
            mod.run("game.surfaces.nauvis.set(%d, %d, 'water')" % (x, y))
    r = mod.result("find_resources", {"kind": "water", "x": 0, "y": 0})
    assert r["found"] and r["x"] == 40 and abs(r["y"]) <= 1 and "find_placement" in r["note"]
    assert mod.result("find_resources", {"kind": "water", "x": 300, "y": 300, "radius": 30})["found"] is False


def test_the_search_starts_at_the_player_when_no_point_is_given(mod):
    ore(mod, "iron-ore", 100, 100, 3, 3)
    mod.run("fake.add_player('captain', 98, 98)")
    r = mod.result("find_resources", {"radius": 20})
    assert r["searched_around"] == {"x": 98, "y": 98} and len(r["patches"]) == 1


def test_find_placement_tries_until_the_game_accepts(mod):
    for x in range(0, 6):
        for y in range(0, 6):
            mod.place("wooden-chest", x + 0.5, y + 0.5)
    r = mod.result("find_placement", {"name": "assembling-machine-2", "x": 2, "y": 2})
    assert r["found"] and 1 <= len(r["places"]) <= 5
    first = r["places"][0]
    assert first["direction"] == "north" and first["tiles_away"] >= 3
    assert mod.result("build", {"entities": [{"name": "assembling-machine-2", "x": first["x"], "y": first["y"]}]})["failed_count"] == 0
    assert mod.result("find_placement", {"name": "assembling-machine-2", "x": 2, "y": 2, "radius": 1})["found"] is False
    assert "no building named" in mod.call("find_placement", {"name": "warp-core", "x": 0, "y": 0})["error"]


# ---------------------------------------------------------------- removing and changing

def test_remove_lists_first_and_takes_only_what_is_ours(mod):
    mod.place("assembling-machine-2", 3.5, 1.5, recipe="iron-gear-wheel", status="working")
    mod.place("transport-belt", 0.5, 4.5)
    mod.place("iron-ore", 0.5, 0.5, amount=10, force=False)
    mod.place("tree-01", 6.5, 0.5, force=False)
    dry = mod.result("remove", {"x": 0, "y": 0, "width": 8, "height": 6})
    assert dry["would_remove"] == 2 and dry["pieces"] == {"assembling-machine-2": 1, "transport-belt": 1}
    assert dry["working_now"] == 1 and "ask the player" in dry["note"]
    assert mod.result("tile", {"x": 3, "y": 1})["free"] is False                    # a dry run removed nothing
    real = mod.result("remove", {"x": 0, "y": 0, "width": 8, "height": 6, "dry_run": False})
    assert real["removed"] == 2
    assert mod.result("tile", {"x": 3, "y": 1})["free"] is True
    assert mod.result("tile", {"x": 0, "y": 0})["things"][0]["name"] == "iron-ore" and mod.result("tile", {"x": 6, "y": 0})["things"][0]["name"] == "tree-01"


def test_remove_by_name_and_refusals(mod):
    mod.place("transport-belt", 0.5, 0.5)
    mod.place("inserter", 1.5, 0.5)
    assert mod.result("remove", {"x": 0, "y": 0, "width": 3, "name": "inserter", "dry_run": False})["removed"] == 1
    assert mod.result("tile", {"x": 0, "y": 0})["things"][0]["name"] == "transport-belt"
    assert mod.result("remove", {"x": 20, "y": 20})["note"] == "nothing of ours stands there"
    assert "between 1 and 60" in mod.call("remove", {"x": 0, "y": 0, "width": 61})["error"]
    mod.result("set_mode", {"mode": "my-character"})
    assert "by hand is not built yet" in mod.call("remove", {"x": 0, "y": 0, "dry_run": False})["error"]


def test_set_recipe_on_a_standing_machine(mod):
    mod.place("assembling-machine-2", 3.5, 1.5, recipe="iron-gear-wheel")
    r = mod.result("set_recipe", {"x": 3, "y": 1, "recipe": "copper-cable"})
    assert r == {"machine": "assembling-machine-2", "recipe": "copper-cable", "was": "iron-gear-wheel"}
    assert mod.result("tile", {"x": 3, "y": 1})["things"][0]["recipe"] == "copper-cable"
    assert "no machine that takes a recipe" in mod.call("set_recipe", {"x": 20, "y": 20, "recipe": "copper-cable"})["error"]
    assert "no recipe named" in mod.call("set_recipe", {"x": 3, "y": 1, "recipe": "warp"})["error"]
    mod.run("game.forces.player.recipes['lab'].enabled = false")
    assert "not researched" in mod.call("set_recipe", {"x": 3, "y": 1, "recipe": "lab"})["error"]


# ---------------------------------------------------------------- research

def test_what_can_be_researched_now(mod):
    r = mod.result("research_available")
    names = [t["technology"] for t in r["available"]]
    assert "electronics" in names and "automation-2" not in names               # automation-2 waits on electronics
    assert "researching" not in r and r["queued"] == {} and r["labs"] == 0
    electronics = [t for t in r["available"] if t["technology"] == "electronics"][0]
    assert electronics["units"] == 30 and electronics["unlocks_recipes"] == ["electronic-circuit", "lab"] and electronics["science_packs"] == ["automation-science-pack"]
    trigger = [t for t in r["available"] if t["technology"] == "cryogenic-science-pack"][0]
    assert trigger["earned_by"] == "make cryogenic-plant" and "units" not in trigger
    mod.run("fake.research('electronics')")
    assert "automation-2" in [t["technology"] for t in mod.result("research_available")["available"]]


def test_queueing_research_only_queues_it(mod):
    r = mod.result("queue_research", {"technology": "electronics"})
    assert r == {"queued": "electronics", "queue": ["electronics"]}
    assert mod.lua.eval("game.forces.player.technologies['electronics'].researched") is False       # nothing was researched by asking
    state = mod.result("research_available")
    assert state["researching"] == "electronics" and state["queued"] == ["electronics"]
    assert "already in the queue" in mod.call("queue_research", {"technology": "electronics"})["error"]


def test_research_that_cannot_be_queued_says_why(mod):
    assert "no technology named" in mod.call("queue_research", {"technology": "warp"})["error"]
    r = mod.call("queue_research", {"technology": "cryogenic-science-pack"})
    assert "earned in the game, not in labs" in r["error"] and r["hint"] == "to earn it: make cryogenic-plant"
    mod.run("fake.research('electronics')")
    assert "already researched" in mod.call("queue_research", {"technology": "electronics"})["error"]
    mod.run("fake.queue_full = true")
    r = mod.call("queue_research", {"technology": "automation-2"})
    assert "would not queue" in r["error"] and "queue may be full" in r["hint"]


def test_research_standing_still_is_news_once_and_again_after_it_has_run(mod):
    mod.tick(600)
    assert mod.result("events_read")["events"] == {}                               # no lab yet: nothing to choose for
    mod.place("lab", 10.5, 10.5)
    mod.tick(600)
    ev = mod.result("events_read")["events"]
    assert [e["kind"] for e in ev] == ["research_idle"]
    mod.tick(1800)
    assert len(mod.result("events_read")["events"]) == 1                            # told once, not every ten seconds
    mod.result("queue_research", {"technology": "electronics"})
    mod.tick(600)
    mod.run("fake.research('electronics')")                                        # it finishes and the queue is empty again
    kinds = [e["kind"] for e in mod.result("events_read")["events"]]
    assert kinds == ["research_idle", "research_finished", "research_idle"]


def test_research_options_put_what_a_milestone_needs_first(world):
    mod, tools = world
    mod.run("prototypes.technology['steam-power'] = { name = 'steam-power', research_unit_count = 500, research_unit_ingredients = {}, effects = {} } "
            "game.forces.player.technologies['steam-power'] = { name = 'steam-power', researched = false, prerequisites = {}, prototype = prototypes.technology['steam-power'], force = game.forces.player }")
    r = ok(tools, "research_options")
    first = r["can_start_now"][0]
    assert first["technology"] == "steam-power" and first["needed_for"] == "Make electricity"       # dearest, yet first: a milestone needs it
    assert r["standing_still"] is True and "needed_for" not in r["can_start_now"][1]
    mod.result("queue_research", {"technology": "electronics"})
    assert ok(tools, "research_options")["standing_still"] is False


# ---------------------------------------------------------------- single pieces, drills, coupling

def test_single_pieces_are_planned_by_their_centre_and_built(world):
    mod, tools = world
    plan = ok(tools, "plan_pieces", {"pieces": [{"name": "assembling-machine-2", "x": 11.5, "y": 11.5, "recipe": "copper-cable"},
                                                {"name": "inserter", "x": 11.5, "y": 13.5, "direction": "south", "filter": "copper-cable"},
                                                {"name": "transport-belt", "x": 11.5, "y": 14.5, "direction": "east"}]})
    assert plan["pieces"] == {"assembling-machine-2": 1, "inserter": 1, "transport-belt": 1} and plan["covers"] == {"from_x": 10, "from_y": 10, "to_x": 12, "to_y": 14}
    ok(tools, "build_plan", {"plan_id": plan["plan_id"]})
    assert ok(tools, "build_plan", {"plan_id": plan["plan_id"], "dry_run": False})["placed"] == 3
    assert mod.result("tile", {"x": 11, "y": 14})["things"][0]["direction"] == "East"
    assert mod.lua.eval("game.surfaces.nauvis.find_entities_filtered{name = 'inserter'}[1].filters[1]") == "copper-cable"


def test_single_pieces_are_checked_before_anything_is_planned(world):
    mod, tools = world
    r = tools.call("plan_pieces", {"pieces": [{"name": "assembling-machine-2", "x": 11, "y": 11}]})
    assert "3 by 3 tiles, so its centre must be at a half (such as 5.5)" in r["error"] and "find_placement" in r["hint"]
    r = tools.call("plan_pieces", {"pieces": [{"name": "inserter", "x": 5.5, "y": 5.5}, {"name": "transport-belt", "x": 5.5, "y": 5.5}]})
    assert "overlaps" in r["error"]
    assert "needs x and y" in tools.call("plan_pieces", {"pieces": [{"name": "inserter"}]})["error"]
    assert "has no name" in tools.call("plan_pieces", {"pieces": [{"x": 1, "y": 1}]})["error"]
    assert "direction must be" in tools.call("plan_pieces", {"pieces": [{"name": "inserter", "x": 0.5, "y": 0.5, "direction": "up"}]})["error"]
    assert "at least one piece" in tools.call("plan_pieces", {"pieces": []})["error"]
    assert "nothing is named" in tools.call("plan_pieces", {"pieces": [{"name": "warp-core", "x": 0.5, "y": 0.5}]})["error"]


def test_a_two_wide_piece_turned_on_its_side_changes_where_its_centre_may_be(world):
    mod, tools = world
    assert ok(tools, "plan_pieces", {"pieces": [{"name": "splitter", "x": 6, "y": 5.5}]})["covers"] == {"from_x": 5, "from_y": 5, "to_x": 6, "to_y": 5}
    assert ok(tools, "plan_pieces", {"pieces": [{"name": "splitter", "x": 5.5, "y": 6, "direction": "east"}]})["covers"] == {"from_x": 5, "from_y": 5, "to_x": 5, "to_y": 6}
    assert "whole number" in tools.call("plan_pieces", {"pieces": [{"name": "splitter", "x": 5.5, "y": 5.5}]})["error"]


def test_drills_on_both_sides_of_a_belt_drop_onto_it():
    lay = joints.miner_row("electric-mining-drill", 3, 3, count=2)
    assert lay.picture(CHARS) == "DDDDDD\nDDDDDD\nDDDDDD\nbbbbbb\nDDDDDD\nDDDDDD\nDDDDDD"
    north = [p for p in lay.pieces if p["role"] == "drill" and p["y"] == 0]
    south = [p for p in lay.pieces if p["role"] == "drill" and p["y"] == 4]
    assert all(p["direction"] == S for p in north) and all(p["direction"] == N for p in south)       # each drops toward the belt
    assert all(p["direction"] == E for p in lay.pieces if p["role"] == "belt")
    with pytest.raises(LayoutError):
        joints.miner_row("electric-mining-drill", 3, 3, count=0)


def test_a_miner_row_is_laid_on_a_patch_through_the_tool(world):
    mod, tools = world
    plan = ok(tools, "plan_joint", {"joint": "miner_row", "x": 20, "y": 0, "machine": "electric-mining-drill", "count": 3})
    assert plan["pieces"] == {"electric-mining-drill": 6, "transport-belt": 9} and plan["covers"] == {"from_x": 20, "from_y": 0, "to_x": 28, "to_y": 6}
    assert ok(tools, "build_plan", {"plan_id": plan["plan_id"]})["failed_count"] == 0


BOILER = [{"flow": "input-output", "x": -1, "y": 0.5, "direction": "west"}, {"flow": "input-output", "x": 1, "y": 0.5, "direction": "east"},
          {"flow": "output", "fluid": "steam", "x": 0, "y": -0.5, "direction": "north"}]
ENGINE = [{"flow": "input-output", "fluid": "steam", "x": 0, "y": -2, "direction": "north"}, {"flow": "input-output", "fluid": "steam", "x": 0, "y": 2, "direction": "south"}]


def test_a_boiler_and_a_steam_engine_are_placed_touching_port_to_port():
    lay = joints.direct_coupling("boiler", 3, 2, BOILER, "steam-engine", 3, 5, ENGINE)
    assert lay.picture(CHARS) == "GGG\nGGG\nGGG\nGGG\nGGG\nBBB\nBBB"               # the engine stands on the boiler's steam outlet
    first, second = [p for p in lay.pieces if p["role"] == "first"][0], [p for p in lay.pieces if p["role"] == "second"][0]
    assert (second["w"], second["h"]) == (3, 5) and second["y"] + second["h"] == first["y"]


def test_coupling_turns_the_second_building_when_it_must():
    sideways = [{"flow": "output", "x": 1, "y": 0.5, "direction": "east"}]          # an outlet on the east side
    lay = joints.direct_coupling("boiler", 3, 2, sideways, "steam-engine", 3, 5, ENGINE)
    second = [p for p in lay.pieces if p["role"] == "second"][0]
    assert (second["w"], second["h"]) == (5, 3) and second["direction"] in (E, W) and second["x"] == 3


def test_coupling_refusals():
    with pytest.raises(LayoutError, match="no fluid output"):
        joints.direct_coupling("a", 3, 3, [{"flow": "input", "x": 0, "y": -1, "direction": "north"}], "b", 3, 3, ENGINE)
    with pytest.raises(LayoutError, match="no fluid input"):
        joints.direct_coupling("a", 3, 2, BOILER, "b", 3, 3, [{"flow": "output", "x": 0, "y": -1, "direction": "north"}])
    water_in = [{"flow": "input", "fluid": "water", "x": 0, "y": -2, "direction": "north"}]
    with pytest.raises(LayoutError, match="join them with a pipe"):
        joints.direct_coupling("boiler", 3, 2, [BOILER[2]], "pump", 3, 5, water_in)       # steam cannot go into a water inlet


def test_coupling_through_the_tool_reads_both_buildings_from_the_game(world):
    mod, tools = world
    plan = ok(tools, "plan_joint", {"joint": "direct_coupling", "x": 0, "y": 0, "machine": "chemical-plant", "second": "chemical-plant"})
    assert plan["pieces"] == {"chemical-plant": 2} and plan["covers"] == {"from_x": 0, "from_y": 0, "to_x": 2, "to_y": 5}
    assert "needs 'machine'" in tools.call("plan_joint", {"joint": "direct_coupling", "x": 0, "y": 0, "machine": "chemical-plant"})["error"]
    assert "no fluid connections" in tools.call("plan_joint", {"joint": "direct_coupling", "x": 0, "y": 0, "machine": "chemical-plant", "second": "lab"})["error"]


# ---------------------------------------------------------------- the assistant comes to the player

def bridge_on(mod, replies, **kw):
    game = LuaGame(mod)
    tools = LocalTools(game)
    agent = Agent(game, FakeModel(replies), local=tools)
    clock = [1000.0]
    return Bridge(game, agent, tools, clock=lambda: clock[0], out=lambda *a: None, **kw), agent, clock


def said(mod):
    return [mod.lua.eval("fake.printed[%d]" % i).split("[/color] ", 1)[1] for i in range(1, int(mod.lua.eval("#fake.printed")) + 1)]


def test_when_research_runs_out_the_assistant_suggests_one_and_asks(mod):
    bridge, agent, clock = bridge_on(mod, [[("research_options", {})], "Research has stopped. I suggest electronics: it unlocks circuits and labs. Shall I queue it?"])
    mod.place("lab", 10.5, 10.5)
    mod.tick(600)
    bridge.step()
    assert said(mod) == ["Research has stopped. I suggest electronics: it unlocks circuits and labs. Shall I queue it?"]
    prompt = agent.model.seen[0][1]["content"]
    assert "research has stopped" in prompt and "ONE technology" in prompt and "Do not queue it yourself" in prompt
    assert mod.result("research_available")["queued"] == {}                         # it asked; it did not choose
    bridge.step()
    assert len(said(mod)) == 1                                                      # and it does not nag


def test_the_player_agrees_and_it_is_queued(mod):
    bridge, agent, clock = bridge_on(mod, ["I suggest electronics. Shall I queue it?", [("queue_research", {"technology": "electronics"})], "Queued electronics."])
    mod.run("fake.add_player('captain', 0, 0)")
    mod.place("lab", 10.5, 10.5)
    mod.tick(600)
    bridge.step()
    mod.run("fake.chat(1, 'yes, do that')")
    bridge.step()
    assert said(mod)[-1] == "Queued electronics." and mod.result("research_available")["researching"] == "electronics"
    assert mod.result("run_stats")["prompts"] == 1                                  # the suggestion cost the player one prompt, an honest one


def test_an_obvious_bottleneck_is_brought_to_the_player_once(mod):
    for i in range(6):
        mod.place("assembling-machine-2", 3.5 + 4 * i, 1.5, recipe="electronic-circuit", status="item_ingredient_shortage", items={"iron-plate": 5})
    bridge, agent, clock = bridge_on(mod, [[("bottlenecks", {})], "Six circuit machines are starved of copper cable. I suggest two more cable machines; shall I?"])
    bridge.step()
    assert said(mod) == ["Six circuit machines are starved of copper cable. I suggest two more cable machines; shall I?"]
    prompt = agent.model.seen[0][1]["content"]
    assert "6 machines are starved of copper-cable" in prompt and "electronic-circuit x6" in prompt and "Ask whether to go ahead" in prompt
    clock[0] += 500
    bridge.step()
    assert len(said(mod)) == 1                                                      # still the same bottleneck: not raised again


def test_a_small_bottleneck_is_not_worth_interrupting_for(mod):
    for i in range(2):
        mod.place("assembling-machine-2", 3.5 + 4 * i, 1.5, recipe="electronic-circuit", status="item_ingredient_shortage", items={})
    bridge, agent, clock = bridge_on(mod, [])
    bridge.step()
    assert said(mod) == []


def test_no_power_comes_before_any_bottleneck(mod):
    for i in range(6):
        mod.place("assembling-machine-2", 3.5 + 4 * i, 1.5, recipe="electronic-circuit", status="item_ingredient_shortage", items={})
    mod.place("assembling-machine-2", 3.5, 11.5, status="no_power")
    bridge, agent, clock = bridge_on(mod, ["One machine has no power: it needs a pole. Shall I place one?"])
    bridge.step()
    assert "have no power" in agent.model.seen[0][1]["content"] and said(mod) == ["One machine has no power: it needs a pole. Shall I place one?"]


def test_a_bottleneck_that_clears_and_comes_back_is_raised_again(mod):
    for i in range(6):
        mod.place("assembling-machine-2", 3.5 + 4 * i, 1.5, recipe="electronic-circuit", status="item_ingredient_shortage", items={"iron-plate": 5})
    bridge, agent, clock = bridge_on(mod, ["First.", "Second."], bottleneck_every=60)
    bridge.step()
    mod.run("for _, e in ipairs(game.surfaces.nauvis.entities) do e.status = defines.entity_status.working end")
    clock[0] += 61
    bridge.step()
    mod.run("for _, e in ipairs(game.surfaces.nauvis.entities) do e.status = defines.entity_status.item_ingredient_shortage end")
    clock[0] += 61
    bridge.step()
    assert said(mod) == ["First.", "Second."]


def test_the_prompts_for_coming_to_the_player_ask_before_acting():
    assert "End by asking whether to go ahead" in research_prompt()
    assert "Ask whether to go ahead" in bottleneck_prompt({"machines_waiting": 5, "problem": "starved of x", "those_machines_make": ["y x5"], "centre_x": 1, "centre_y": 2}, None)
    assert "short of power" in bottleneck_prompt(None, "3 machines have no power")
