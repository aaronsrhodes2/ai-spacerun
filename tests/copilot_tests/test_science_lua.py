"""Science per minute and the run's counters, run under Lua 5.2 against the stand-in game."""
import pytest

from luamod import LuaMod


@pytest.fixture
def mod():
    return LuaMod()


def rates(mod, **packs):
    for name, (made, used) in packs.items():
        mod.run("game.forces.player.rate[%r] = { %s, %s }" % (name.replace("_", "-") + "-science-pack", made, used))


def test_science_per_minute_is_the_slowest_pack(mod):
    rates(mod, automation=(1200, 1100), logistic=(950.04, 900), chemical=(400, 400))
    s = mod.result("science")
    assert s["science_per_minute"] == 400 and s["slowest_pack"] == "chemical-science-pack"
    assert [p["pack"] for p in s["packs"]] == ["chemical-science-pack", "logistic-science-pack", "automation-science-pack"]      # slowest first
    assert s["packs"][1] == {"pack": "logistic-science-pack", "made_per_minute": 950, "used_per_minute": 900, "researched": True}
    assert "target" not in s and "reached" not in s


def test_a_target_lists_the_packs_that_fall_short_worst_first(mod):
    rates(mod, automation=(1200, 0), logistic=(950, 0), chemical=(400, 0))
    s = mod.result("science", {"target": 1000})
    assert s["reached"] is False and s["target"] == 1000
    assert s["short"] == [{"pack": "chemical-science-pack", "short_by": 600}, {"pack": "logistic-science-pack", "short_by": 50}]


def test_a_target_that_is_met(mod):
    rates(mod, automation=(1200, 0), logistic=(1000, 0), chemical=(1000.2, 0))
    s = mod.result("science", {"target": 1000})
    assert s["reached"] is True and s["short"] == {} and s["science_per_minute"] == 1000


def test_packs_not_yet_researched_are_listed_but_not_counted(mod):
    rates(mod, automation=(300, 0), logistic=(200, 0))
    mod.run("game.forces.player.recipes['chemical-science-pack'].enabled = false")
    s = mod.result("science", {"target": 100})
    assert s["science_per_minute"] == 200 and s["reached"] is True
    chem = [p for p in s["packs"] if p["pack"] == "chemical-science-pack"][0]
    assert chem["researched"] is False and chem["made_per_minute"] == 0


def test_science_made_on_other_planets_counts_too(mod):
    rates(mod, automation=(100, 0), logistic=(100, 0), chemical=(100, 0))
    mod.run("fake.add_planet('vulcanus', true) game.forces.player.rate_elsewhere['chemical-science-pack'] = { 50, 0 }")
    s = mod.result("science")
    chem = [p for p in s["packs"] if p["pack"] == "chemical-science-pack"][0]
    assert chem["made_per_minute"] == 150 and s["science_per_minute"] == 100


def test_a_factory_that_makes_no_science_yet(mod):
    s = mod.result("science", {"target": 60})
    assert s["science_per_minute"] == 0 and s["reached"] is False and len(s["short"]) == 3


def test_prompts_are_counted_and_shown_on_the_working_light(mod):
    mod.run("fake.add_player('captain', 0, 0)")
    label = "game.players[1].gui.top.skippy_light.skippy_prompts.caption"
    assert mod.result("run_stats") == {"prompts": 0, "hours_played": 0, "won": False} and mod.lua.eval(label) == "0 prompts"
    mod.run("fake.chat(1, 'lets get to red science')")
    assert mod.lua.eval(label) == "1 prompt"
    mod.run("fake.chat(1, 'and now green') fake.chat(1, '')")
    assert mod.result("run_stats")["prompts"] == 2 and mod.lua.eval(label) == "2 prompts"


def test_what_the_server_or_the_assistant_says_is_not_a_prompt(mod):
    mod.run("fake.chat(nil, 'server message')")
    mod.result("say", {"text": "I built it."})
    assert mod.result("run_stats")["prompts"] == 0


def test_the_win_is_recorded_once_with_the_prompts_it_took(mod):
    mod.run("fake.add_player('captain', 0, 0) fake.chat(1, 'finish the game') fake.chat(1, 'keep going')")
    mod.tick(400)
    assert mod.result("run_stats")["won"] is False
    mod.run("game.tick = 216000 * 30 game.finished = true")
    mod.tick(300)
    won = mod.result("run_stats")
    assert won["won"] is True and won["prompts_to_win"] == 2 and won["hours_to_win"] == 30
    mod.run("fake.chat(1, 'what now?')")
    mod.tick(600)
    after = mod.result("run_stats")
    assert after["prompts"] == 3 and after["prompts_to_win"] == 2 and after["hours_to_win"] == 30
