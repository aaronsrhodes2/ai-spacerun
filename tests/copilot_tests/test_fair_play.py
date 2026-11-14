"""Solving a whole planet in one prompt, and playing fair (the Captain, 2026-11-13: people will say "solve Nauvis" and
expect one prompt per planet; that may be optimistic, and problems will come up that they have to deal with, but the
assistant does the best job an expert could and never cheats, and the record of a run says honestly how it was built)."""
import pathlib
import re

import pytest

from copilot import milestones as ms
from copilot.goals import Goal, GoalError
from copilot.tools import LocalTools
from luamod import LuaMod
from test_goals import EMPTY, LoopGame, make

ROOT = pathlib.Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------- a planet as one goal

def test_every_milestone_belongs_to_a_place_and_every_place_has_some():
    assert all(m.get("place") in ms.PLACES for m in ms.MILESTONES)
    assert all(ms.of_place(p) for p in ms.PLACES)
    assert [m["id"] for m in ms.of_place("nauvis")][0] == "first-plates" and [m["id"] for m in ms.of_place("nauvis")][-1] == "first-rocket"
    assert [m["id"] for m in ms.of_place("edge")] == ["railgun-and-fusion", "edge", "won"]


def test_solve_nauvis_is_a_goal():
    g = Goal("place", "Nauvis")
    assert g.describe() == "solve Nauvis" and Goal("place", "space").describe() == "get the first platform working"
    assert g.reached(EMPTY) == (False, "0 of 11 steps done, next: Smelt the first iron and copper plates")
    with pytest.raises(GoalError, match="no place 'mars'.*nauvis"):
        Goal("place", "mars")
    with pytest.raises(GoalError, match="no place ''"):
        Goal("place", None)


def nauvis_done():
    items, entities = ms.wanted(ms.of_place("nauvis"))
    return dict(EMPTY, produced={i: 10 ** 5 for i in items}, built={e: 50 for e in entities}, rockets_launched=1,
                researched=sorted({t for m in ms.of_place("nauvis") for t in m["test"].get("researched", [])}))


def test_a_planet_is_solved_when_all_its_steps_are_done_whatever_else_is_not():
    g = Goal("place", "nauvis")
    assert g.reached(nauvis_done()) == (True, "11 of 11 steps done")
    almost = nauvis_done()
    almost["rockets_launched"] = 0
    assert g.reached(almost) == (False, "10 of 11 steps done, next: Launch a rocket")
    assert Goal("place", "vulcanus").reached(nauvis_done())[0] is False


def test_the_turn_prompt_for_a_planet_points_at_its_next_step_and_at_an_earlier_one_still_open():
    p = Goal("place", "nauvis").prompt(EMPTY)
    assert "standing goal the player gave you: solve Nauvis" in p and "The next milestone is: Smelt the first iron and copper plates" in p
    assert "An earlier step is not done yet" not in p
    p = Goal("place", "vulcanus").prompt(EMPTY)
    assert "The next milestone is: Land on Vulcanus and make metallurgic science" in p
    assert "An earlier step is not done yet and may be needed first: Smelt the first iron and copper plates." in p
    assert "honestly: if something failed or is not working yet, say so" in p


def test_solve_nauvis_through_the_tool_and_the_loop():
    game, tools, agent, bridge, clock = make([[("set_goal", {"kind": "place", "place": "nauvis"})], "I will solve Nauvis.",
                                              [("diagnose", {})], "Placed the first furnaces."])
    game.type("solve nauvis")
    bridge.step()
    assert tools.goal.describe() == "solve Nauvis"
    clock[0] += 30
    bridge.step()
    assert tools.goal.turns == 1
    game.facts = nauvis_done()
    clock[0] += 30
    bridge.step()
    assert tools.goal is None and game.said()[-1] == "Goal reached: solve Nauvis (11 of 11 steps done). It took 1 turns of my own."


def test_set_goal_refuses_a_place_that_does_not_exist():
    tools = LocalTools(LoopGame())
    assert "no place 'mars'" in tools.call("set_goal", {"kind": "place", "place": "mars"})["error"]
    assert tools.call("set_goal", {"kind": "place", "place": "gleba"})["result"]["goal"] == "solve Gleba"


# ---------------------------------------------------------------- an honest record of how things were built

def belts(xs, y):
    return [{"name": "transport-belt", "x": x + 0.5, "y": y + 0.5, "direction": 4} for x in xs]


def test_pieces_placed_freely_and_by_hand_are_counted_apart():
    mod = LuaMod()
    assert mod.result("run_stats")["built_by_hand_only"] is True
    mod.result("build", {"entities": belts(range(4), 3), "dry_run": False})
    s = mod.result("run_stats")
    assert (s["placed_freely"], s["placed_by_character"], s["built_by_hand_only"]) == (4, 0, False)
    mod.result("set_mode", {"mode": "my-character"})
    mod.give(transport_belt=3)
    mod.result("build", {"entities": belts(range(10, 13), 3), "dry_run": False})
    mod.run_job()
    s = mod.result("run_stats")
    assert (s["placed_freely"], s["placed_by_character"], s["built_by_hand_only"]) == (4, 3, False)


def test_a_game_built_only_by_the_character_says_so():
    mod = LuaMod()
    mod.result("set_mode", {"mode": "my-character"})
    mod.give(transport_belt=2)
    mod.result("build", {"entities": belts(range(2), 3), "dry_run": False})
    mod.run_job()
    s = mod.result("run_stats")
    assert s["placed_by_character"] == 2 and s["placed_freely"] == 0 and s["built_by_hand_only"] is True


def test_dry_runs_and_refused_builds_count_as_nothing():
    mod = LuaMod()
    mod.result("build", {"entities": belts(range(4), 3)})
    mod.place("wooden-chest", 20.5, 3.5)
    mod.result("build", {"entities": belts([19, 20], 3), "dry_run": False})
    assert mod.result("run_stats")["placed_freely"] == 0


# ---------------------------------------------------------------- no cheating anywhere in the mod

MOD = ROOT / "mods" / "skippy-copilot"


def lua_code():
    from test_mod_static import strip
    return {f.name: strip(f.read_text(encoding="utf-8")) for f in sorted(MOD.glob("**/*.lua"))}


def test_the_mod_never_conjures_items_or_writes_research():
    """Nothing in the mod gives items out of thin air or touches research state. The only inserts move an item that was
    just removed from somewhere else (the avatar carrying, and what did not fit going back)."""
    for name, code in lua_code().items():
        assert not re.search(r"\.researched\s*=\s*(true|false)", code), "%s writes research state" % name
        assert "research_all_technologies" not in code and "cheat_mode" not in code, name
        assert not re.search(r"\.enabled\s*=", code), "%s unlocks a recipe" % name
        if name != "avatar.lua":
            assert not re.search(r"\binsert\s*[({]", code), "%s inserts items" % name
    avatar = lua_code()["avatar.lua"]
    assert len(re.findall(r"\binsert\s*\{", avatar)) == 2 and avatar.count("remove_item") == 1


def test_the_mod_never_teleports_anything():
    for name, code in lua_code().items():
        assert "teleport" not in code, "%s teleports" % name


def test_free_placement_is_the_only_place_a_piece_appears_without_an_item_and_it_is_gated_on_research():
    code = lua_code()
    makers = {name: len(re.findall(r"create_entity\s*\{", c)) for name, c in code.items() if "create_entity" in c}
    assert makers == {"avatar.lua": 2, "build.lua": 1}                # the avatar's own body and its hand-placed piece; the free hand
    build = code["build.lua"]
    assert build.index("researched(force, proto)") < build.index("place(surface, force, piece)")


def test_the_skill_prompt_says_to_play_fair_and_to_be_honest():
    prompt = (ROOT / "copilot" / "prompt.md").read_text(encoding="utf-8")
    assert "never cheat" in prompt and "nothing is conjured" in prompt and "Research is earned in labs" in prompt
    assert "never report something as done that you have not checked with a tool" in prompt
