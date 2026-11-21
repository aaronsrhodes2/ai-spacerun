"""The spider commander (the Captain, 2026-11-21): the player lives in remote view and places ghosts; the body rides a
spidertron the assistant drives; its robots build; ghost needs go into its own requests. Switched on by a map setting,
in a new game or a running one; a starter spider and kit come once, under the allowance 'commander-kit'."""
import pytest

from luamod import LuaMod


@pytest.fixture
def mod():
    m = LuaMod()
    m.run("fake.players_have_bodies = true fake.add_player('captain', 0, 0) "
          "prototypes.item['construction-robot'] = { name = 'construction-robot', stack_size = 50 }")
    return m


def commander_on(mod):
    mod.run("fake.change_setting('skippy-commander', true)")


def test_off_by_default_nothing_changes(mod):
    assert mod.lua.eval("game.players[1].controller_type == defines.controllers.character")
    assert mod.result("spiders")["spiders"] == {} and mod.result("spiders")["commander"] is False


def test_switching_on_seats_the_body_in_a_starter_spider_and_the_player_in_remote_view(mod):
    commander_on(mod)
    p = "game.players[1]"
    assert mod.lua.eval(p + ".controller_type == defines.controllers.remote")
    spiders = mod.result("spiders")["spiders"]
    assert len(spiders) == 1 and spiders[0]["spider"] == "Skippy 1" and spiders[0]["driver"] is not None
    assert spiders[0]["construction_robots"] == 50
    assert mod.lua.eval(p + ".character.vehicle ~= nil")                                   # the body is kept, in the seat
    assert mod.lua.eval("#storage.commander.spiders[1].grid.equipment") >= 4               # roboports, power, shield
    news = [e["text"] for e in mod.result("events_read")["events"]]
    assert any("starter spidertron" in t for t in news)
    assert mod.lua.eval("storage.run.kits_given") == 1


def test_an_existing_spider_is_used_and_no_kit_is_given(mod):
    mod.place("spidertron", 10.5, 0.5)
    commander_on(mod)
    assert len(mod.result("spiders")["spiders"]) == 1 and mod.lua.eval("(storage.run.kits_given or 0)") == 0


def test_with_the_kit_switched_off_and_no_spider_the_player_is_told(mod):
    mod.run("fake.change_setting('skippy-allow-commander-kit', false)")
    commander_on(mod)
    assert mod.result("spiders")["spiders"] == {}
    assert any("allow the starter kit" in e["text"] for e in mod.result("events_read")["events"])


def test_stepping_into_local_view_returns_to_remote_view(mod):
    commander_on(mod)
    mod.run("game.players[1].set_controller { type = defines.controllers.character }")
    assert mod.lua.eval("game.players[1].controller_type == defines.controllers.remote")


def test_spider_go_walks_there_and_says_so_without_moving_the_view(mod):
    commander_on(mod)
    view = mod.lua.eval("game.players[1].remote_position.x")
    r = mod.result("spider_go", {"x": 20, "y": 0})
    assert r["to"] == {"x": 20, "y": 0}
    mod.tick(80)
    s = mod.result("spiders")["spiders"][0]
    assert (s["x"], s["y"]) == (20, 0) and "going_to" not in s
    assert any(e["kind"] == "spider_arrived" for e in mod.result("events_read")["events"])
    assert mod.lua.eval("game.players[1].remote_position.x") == view
    assert "say where" in mod.call("spider_go", {})["error"]


def test_ghost_needs_near_the_spider_go_into_its_own_requests(mod):
    commander_on(mod)
    mod.run("for i = 1, 3 do game.surfaces.nauvis.create_entity{name='entity-ghost', inner_name='chemical-plant', position={i * 3 + 0.5, 6.5}} end "
            "game.surfaces.nauvis.create_entity{name='entity-ghost', inner_name='transport-belt', position={1.5, 3.5}}")
    dry = mod.result("ghost_requests", {"spider": "first"})
    assert dry["applied"] is False and dry["spiders"][0]["ghosts_near"] == 4
    assert [i["item"] for i in dry["spiders"][0]["items"]] == ["chemical-plant"]         # the kit's belts already cover the belt
    r = mod.result("ghost_requests", {"spider": "first", "apply": True})
    assert r["spiders"][0]["wrote"] == 1
    sec = "storage.commander.spiders[1].requests.sections[1]"
    assert mod.lua.eval(sec + ".group") == "ghost-auto-spider-" + str(mod.lua.eval("storage.commander.spiders[1].unit_number"))
    assert mod.lua.eval(sec + ".slots[1].value.name") == "chemical-plant" and mod.lua.eval(sec + ".slots[1].min") == 3
    mod.result("ghost_requests", {"spider": "first", "apply": True})                     # rewritten, not added to
    assert mod.lua.eval("storage.commander.spiders[1].requests.sections_count") == 1


def test_tending_walks_to_ghosts_the_network_cannot_reach(mod):
    commander_on(mod)
    mod.run("game.surfaces.nauvis.find_logistic_network_by_position = function() return nil end "
            "game.surfaces.nauvis.create_entity{name='entity-ghost', inner_name='transport-belt', position={60.5, 0.5}}")
    r = mod.result("spider_tend_step")
    assert r["doing"] == "going" and r["to"] == {"x": 60, "y": 0}
    assert mod.result("spider_tend_step")["doing"] == "walking"
    mod.tick(200)
    assert mod.result("spider_tend_step")["doing"] == "building"
    mod.result("spider_tend")
    jobs = mod.result("cron_list")["jobs"]
    assert len(jobs) == 1 and jobs[0]["name"].startswith("tend ") and jobs[0]["tool"] == "spider_tend_step"
    mod.result("spider_tend", {"on": False})
    assert mod.result("cron_list")["jobs"] in ([], {})
