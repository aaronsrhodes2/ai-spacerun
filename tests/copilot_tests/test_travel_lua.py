"""Planet travel and the progress facts, run under Lua 5.2 against the stand-in game. The stand-in has a rocket that
takes a while, platforms that fly their schedule, and cargo pods; it models the calls the mod makes, not how the real
game moves a character through a rocket. The first real trip is the true test."""
import pytest

from luamod import LuaMod


@pytest.fixture
def space():
    """The avatar at home on nauvis with empty hands, a silo with a rocket ready 20 tiles away, vulcanus discovered and
    a shuttle in orbit that flies nauvis <-> vulcanus."""
    m = LuaMod()
    m.result("set_mode", {"mode": "my-character"})
    m.run("fake.add_planet('vulcanus', true) fake.add_planet('aquilo', false)")
    m.place("rocket-silo", 20.5, 0.5, rocket_ready=True)
    m.run("fake.add_platform('Nauvis-Vulcanus 1 Shuttle', 'nauvis', { 'nauvis', 'vulcanus' }, 600, 900)")
    m.give()
    return m


def where(m):
    return m.lua.eval("storage.avatar.body.surface.name")


def test_the_whole_trip(space):
    r = space.result("avatar_travel", {"planet": "vulcanus"})
    assert (r["ship"], r["from"], r["to"], r["silo_x"]) == ("Nauvis-Vulcanus 1 Shuttle", "nauvis", "vulcanus", 20)
    stages = []
    for _ in range(20000):
        st = space.result("avatar")
        if not st.get("job"):
            break
        if not stages or stages[-1] != st["job"]["stage"]:
            stages.append(st["job"]["stage"])
        space.tick(10)
    last = space.result("avatar")["last_job"]
    assert stages == ["to_silo", "ascend", "ride", "descend"] or stages == ["to_silo", "board", "ascend", "ride", "drop", "descend"] \
        or [s for s in stages if s not in ("board", "drop")] == ["to_silo", "ascend", "ride", "descend"]
    assert last["ok"] and (last["planet"], last["from"], last["ship"]) == ("vulcanus", "nauvis", "Nauvis-Vulcanus 1 Shuttle")
    assert where(space) == "vulcanus"
    assert space.lua.eval("game.forces.player.rockets_launched") == 1
    assert space.lua.eval("game.forces.player.platforms[1].schedule.records[1].station") == "nauvis"      # the ship's schedule was not touched


def test_it_walks_to_the_silo_before_boarding(space):
    space.result("avatar_travel", {"planet": "vulcanus"})
    space.tick(40)
    st = space.result("avatar")
    assert st["job"]["stage"] == "to_silo" and 0 < space.body()[0] < 15 and where(space) == "nauvis"


def test_nobody_boards_a_rocket_carrying_items(space):
    space.give(iron_plate=3, coal=1)
    r = space.call("avatar_travel", {"planet": "vulcanus"})
    assert not r["ok"] and "must carry nothing" in r["error"] and "iron-plate" in r["error"] and "avatar_carry" in r["hint"]
    assert space.result("avatar").get("job") is None


def test_refusals_before_setting_off(space):
    r = space.call("avatar_travel", {"planet": "mars"})
    assert "no planet named 'mars'" in r["error"] and "aquilo, nauvis, vulcanus" in r["hint"]
    assert "already on nauvis" in space.call("avatar_travel", {"planet": "nauvis"})["error"]
    space.run("game.forces.player.unlocked['aquilo'] = false")
    assert "has not been discovered" in space.call("avatar_travel", {"planet": "aquilo"})["error"]
    space.run("game.forces.player.unlocked['aquilo'] = nil")
    r = space.call("avatar_travel", {"planet": "aquilo"})
    assert "no ship in orbit over nauvis has aquilo on its schedule" in r["error"] and "Nauvis-Vulcanus 1 Shuttle" in r["hint"]
    r = space.call("avatar_travel", {"planet": "vulcanus", "ship": "Enterprise"})
    assert "no ship named 'Enterprise'" in r["error"]


def test_no_rocket_ready_is_said_plainly(space):
    space.run("game.surfaces.nauvis.find_entities_filtered{type = 'rocket-silo'}[1].rocket_silo_status = defines.rocket_silo_status.building_rocket")
    r = space.call("avatar_travel", {"planet": "vulcanus"})
    assert "no rocket silo on nauvis has a rocket ready" in r["error"]


def test_travel_is_not_for_free_hand_mode(space):
    space.result("set_mode", {"mode": "free-hand"})
    assert "free-hand mode" in space.call("avatar_travel", {"planet": "vulcanus"})["error"]


def test_a_named_ship_is_used_when_given(space):
    space.run("fake.add_platform('Second Ship', 'nauvis', { 'nauvis', 'vulcanus' }, 600, 900)")
    assert space.result("avatar_travel", {"planet": "vulcanus", "ship": "Second Ship"})["ship"] == "Second Ship"


def test_a_named_ship_that_does_not_go_there_is_refused(space):
    space.run("fake.add_platform('Gleba Run', 'nauvis', { 'nauvis', 'gleba' }, 600, 900)")
    assert "does not have vulcanus on its schedule" in space.call("avatar_travel", {"planet": "vulcanus", "ship": "Gleba Run"})["error"]


def test_the_rocket_gone_cold_at_the_last_moment(space):
    space.result("avatar_travel", {"planet": "vulcanus"})
    space.tick(30)
    space.run("game.surfaces.nauvis.find_entities_filtered{type = 'rocket-silo'}[1].rocket_silo_status = defines.rocket_silo_status.building_rocket")
    last = space.run_job()
    assert last["ok"] is False and "rocket is not ready any more" in last["reason"] and last["stage"] == "board" and where(space) == "nauvis"


def test_the_ship_leaving_before_the_avatar_reaches_the_silo(space):
    space.run("game.forces.player.platforms[1].wait = 20")
    space.result("avatar_travel", {"planet": "vulcanus"})
    last = space.run_job()
    assert last["ok"] is False and "ship has left orbit" in last["reason"] and where(space) == "nauvis"


def test_a_silo_that_refuses(space):
    space.run("fake.silo_refuses = true")
    space.result("avatar_travel", {"planet": "vulcanus"})
    last = space.run_job()
    assert last["ok"] is False and "would not launch" in last["reason"]


def test_a_paused_ship_is_reported_with_where_the_avatar_is(space):
    space.result("avatar_travel", {"planet": "vulcanus"})
    for _ in range(4000):
        if (space.result("avatar").get("job") or {}).get("stage") == "ride":
            break
        space.tick(5)
    space.run("game.forces.player.platforms[1].paused = true")
    last = space.run_job()
    assert last["ok"] is False and "paused in flight" in last["reason"] and "aboard 'Nauvis-Vulcanus 1 Shuttle'" in last["reason"]
    assert where(space) == "platform-1"


def test_travel_can_be_resumed_from_aboard_a_ship(space):
    space.result("avatar_travel", {"planet": "vulcanus"})
    for _ in range(4000):
        if (space.result("avatar").get("job") or {}).get("stage") == "ride":
            break
        space.tick(5)
    space.result("avatar_stop")
    r = space.result("avatar_travel", {"planet": "vulcanus"})
    assert "already aboard" in r["note"]
    assert space.run_job(20000)["ok"] and where(space) == "vulcanus"


def test_aboard_a_ship_that_does_not_go_there(space):
    space.result("avatar_travel", {"planet": "vulcanus"})
    for _ in range(4000):
        if (space.result("avatar").get("job") or {}).get("stage") == "ride":
            break
        space.tick(5)
    space.result("avatar_stop")
    r = space.call("avatar_travel", {"planet": "aquilo"})
    assert "whose schedule does not go to aquilo" in r["error"]


def test_the_first_landing_opens_a_planet_that_had_no_surface(space):
    space.run("fake.add_platform('Aquilo Ship', 'nauvis', { 'nauvis', 'aquilo' }, 600, 900)")
    assert space.lua.eval("game.planets.aquilo.surface == nil")
    space.result("avatar_travel", {"planet": "aquilo"})
    assert space.run_job(20000)["ok"] and where(space) == "aquilo" and space.lua.eval("game.planets.aquilo.surface ~= nil")


def test_a_ship_that_cannot_drop_the_avatar(space):
    space.run("fake.no_pods = true")
    space.result("avatar_travel", {"planet": "vulcanus"})
    last = space.run_job(20000)
    assert last["ok"] is False and "could not leave the ship" in last["reason"] and where(space) == "platform-1"


def test_the_players_own_character_lands_the_players_way():
    m = LuaMod()
    m.result("set_mode", {"mode": "my-character"})
    m.run("fake.players_have_bodies = true fake.add_player('captain', 0, 0) fake.add_planet('vulcanus', true)")
    m.place("rocket-silo", 20.5, 0.5, rocket_ready=True)
    m.run("fake.add_platform('Shuttle', 'nauvis', { 'nauvis', 'vulcanus' }, 600, 900)")
    m.result("avatar_travel", {"planet": "vulcanus"})
    last = m.run_job(20000)
    assert last["ok"] and m.lua.eval("game.players[1].character.surface.name") == "vulcanus"
    assert m.lua.eval("#fake.flights") == 0


def test_changing_mode_during_a_trip_stops_the_job_but_not_the_rocket(space):
    space.result("avatar_travel", {"planet": "vulcanus"})
    for _ in range(4000):
        if (space.result("avatar").get("job") or {}).get("stage") == "ascend":
            break
        space.tick(5)
    space.result("set_mode", {"mode": "free-hand"})
    assert space.result("avatar")["last_job"]["reason"] == "the mode was changed to free-hand"
    space.tick(300)
    assert where(space) == "platform-1"                                # the rocket was already on its way


# ---------------------------------------------------------------- progress facts

def test_progress_reports_the_facts_asked_for(space):
    space.run("fake.research('electronics') fake.research('automation-2')")
    space.run("game.forces.player.made['iron-plate'] = 240 game.forces.player.made['iron-gear-wheel'] = 12")
    space.place("lab", 40.5, 40.5)
    space.place("lab", 44.5, 40.5)
    p = space.result("progress", {"items": ["iron-plate", "iron-gear-wheel", "copper-plate", "no-such-item"],
                                  "entities": ["lab", "rocket-silo", "no-such-building"]})
    assert p["researched"] == ["automation-2", "electronics"]
    assert p["produced"] == {"iron-plate": 240, "iron-gear-wheel": 12, "copper-plate": 0, "no-such-item": 0}
    assert p["built"] == {"lab": 2, "rocket-silo": 1, "no-such-building": 0}
    assert p["rockets_launched"] == 0 and p["won"] is False
    assert p["platforms"] == [{"name": "Nauvis-Vulcanus 1 Shuttle", "at": "nauvis"}]
    assert p["planets_reached"] == ["nauvis"] and p["tick"] >= 100


def test_progress_follows_the_game(space):
    space.result("avatar_travel", {"planet": "vulcanus"})
    assert space.run_job(20000)["ok"]
    space.place("lab", 5.5, 5.5)                                      # stays on nauvis
    space.run("game.surfaces.vulcanus.create_entity{name = 'lab', position = {5.5, 5.5}}")
    space.run("game.finished_but_continuing = true")
    p = space.result("progress", {"entities": ["lab"]})
    assert p["rockets_launched"] == 1 and p["planets_reached"] == ["nauvis", "vulcanus"] and p["built"] == {"lab": 2} and p["won"] is True
    assert p["platforms"][0]["at"] in ("vulcanus", "nauvis", "in flight")


def test_progress_with_nothing_asked(space):
    p = space.result("progress")
    assert p["produced"] == {} and p["built"] == {} and p["researched"] == {}
