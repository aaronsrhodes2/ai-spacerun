"""The walking avatar, run under Lua 5.2 against the stand-in game: a character that moves a little each tick, a
pathfinder that answers a tick later, ore that takes time to mine. The exit test of increment 1 in docs/solver-plan.md is
at the bottom: walk across a base with obstacles and build a ten-machine line from the inventory, with no teleport and
nothing placed out of reach."""
import math

import pytest

from luamod import LuaMod

STEP = 0.15 + 1e-6            # the stand-in character's speed: tiles a tick


@pytest.fixture
def mod():
    m = LuaMod()
    m.result("set_mode", {"mode": "my-character"})          # the avatar only moves in this mode
    return m


def walk_and_watch(mod, limit=6000):
    """Run the avatar's job to its end, checking every tick that the body never moved further than one step."""
    mod.tick(1)
    last = mod.body()
    for _ in range(limit):
        if not mod.lua.eval("storage.avatar.job ~= nil"):
            break
        mod.tick(1)
        now = mod.body()
        assert math.hypot(now[0] - last[0], now[1] - last[1]) <= STEP, "the avatar jumped from %s to %s" % (last, now)
        last = now
    assert not mod.lua.eval("storage.avatar.job ~= nil"), "the job did not end"
    return mod.result("avatar")["last_job"]


def wall(mod, x, y0, y1):
    for y in range(y0, y1 + 1):
        mod.place("wooden-chest", x + 0.5, y + 0.5)


# ---------------------------------------------------------------- the body and walking

def test_with_nobody_in_the_game_the_mod_keeps_a_body_of_its_own(mod):
    assert mod.result("avatar")["has_body"] is False
    r = mod.result("avatar_walk", {"x": 6, "y": 0})
    assert r["job"] == 1 and (r["from_x"], r["from_y"]) == (0, 0)
    a = mod.result("avatar")
    assert a["has_body"] and a["job"]["kind"] == "walk" and a["executor"] == "avatar" and a["mode"] == "my-character"
    assert a["reach"] == {"build": 10, "mine": 2.7, "touch": 10}


def test_it_walks_there_step_by_step(mod):
    mod.result("avatar_walk", {"x": 12, "y": 5})
    last = walk_and_watch(mod)
    a = mod.result("avatar")
    assert last["ok"] and last["kind"] == "walk" and abs(a["x"] - 12) <= 1 and abs(a["y"] - 5) <= 1
    assert last["ticks"] >= 12 / 0.15 * 0.8                               # it took walking time, not an instant
    assert mod.lua.eval("storage.avatar.body.walking_state.walking") is False


def test_near_decides_how_close_is_close_enough(mod):
    mod.result("avatar_walk", {"x": 20, "y": 0, "near": 5})
    walk_and_watch(mod)
    assert 14 <= mod.body()[0] <= 16.5


def test_it_goes_round_a_wall_and_never_through_it(mod):
    wall(mod, 5, -6, 6)
    mod.result("avatar_walk", {"x": 10, "y": 0})
    mod.tick(1)
    crossed_at = None
    for _ in range(4000):
        if not mod.lua.eval("storage.avatar.job ~= nil"):
            break
        mod.tick(1)
        x, y = mod.body()
        if 5 <= x <= 6:
            crossed_at = y
            assert y < -6 or y > 7, "the avatar walked through the wall at %s,%s" % (x, y)
    assert mod.result("avatar")["last_job"]["ok"] and crossed_at is not None


def test_a_place_that_cannot_be_reached_on_foot_is_reported(mod):
    for x in range(8, 13):
        for y in range(-2, 3):
            if x in (8, 12) or y in (-2, 2):
                mod.place("wooden-chest", x + 0.5, y + 0.5)               # a closed ring round 10,0
    mod.result("avatar_walk", {"x": 10, "y": 0, "near": 0.5})
    last = mod.run_job()
    assert last["ok"] is False and "no way on foot" in last["reason"]
    assert math.hypot(*mod.body()) < 2                                    # it did not set off


def test_water_is_walked_round(mod):
    for y in range(-8, 9):
        mod.run("game.surfaces.nauvis.set(4, %d, 'water')" % y)
    mod.result("avatar_walk", {"x": 8, "y": 0})
    assert walk_and_watch(mod)["ok"] and mod.body()[0] > 6


def test_a_new_obstacle_makes_it_find_another_way(mod):
    mod.result("avatar_walk", {"x": 14, "y": 0})
    mod.tick(20)
    wall(mod, 7, -4, 4)                                                   # dropped in its path after the path was made
    last = walk_and_watch(mod)
    assert last["ok"] and mod.body()[0] > 12


def test_boxed_in_after_setting_off_ends_as_blocked(mod):
    mod.result("avatar_walk", {"x": 14, "y": 0})
    mod.tick(20)
    x, y = (math.floor(v) for v in mod.body())
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            if abs(dx) == 2 or abs(dy) == 2:
                mod.place("wooden-chest", x + dx + 0.5, y + dy + 0.5)
    last = mod.run_job()
    assert last["ok"] is False and ("no way on foot" in last["reason"] or "blocked" in last["reason"])


def test_a_slow_pathfinder_is_waited_for_and_a_silent_one_given_up_on(mod):
    mod.run("fake.path_delay = 100")
    mod.result("avatar_walk", {"x": 5, "y": 0})
    mod.tick(50)
    assert math.hypot(*mod.body()) < 1 and mod.result("avatar")["job"]["kind"] == "walk"      # waiting, not wandering
    assert mod.run_job()["ok"]
    mod.run("fake.path_delay = 100000")
    mod.result("avatar_walk", {"x": 0, "y": 9})
    last = mod.run_job()
    assert last["ok"] is False and "pathfinder did not answer" in last["reason"]


def test_one_job_at_a_time_and_stop_means_stop(mod):
    mod.result("avatar_walk", {"x": 30, "y": 0})
    r = mod.call("avatar_walk", {"x": 0, "y": 30})
    assert not r["ok"] and "busy with a walk job (id 1)" in r["error"] and "avatar_stop" in r["hint"]
    mod.tick(30)
    assert mod.result("avatar_stop") == {"stopped": True, "was": "walk"}
    here = mod.body()
    mod.tick(30)
    assert mod.body() == here                                             # it stands still
    last = mod.result("avatar")["last_job"]
    assert last["ok"] is False and last["reason"] == "stopped on request"
    assert mod.result("avatar_stop")["stopped"] is False


def test_the_players_own_character_is_the_avatar(mod):
    mod.run("fake.players_have_bodies = true fake.add_player('captain', 20, 20)")
    r = mod.result("avatar_walk", {"x": 26, "y": 20})
    assert (r["from_x"], r["from_y"]) == (20, 20)
    walk_and_watch(mod)
    assert abs(mod.lua.eval("game.players[1].position.x") - 26) <= 1.5
    assert mod.lua.eval("storage.avatar.own") is False


# ---------------------------------------------------------------- mining, crafting, carrying

def ore(mod, x, y, amount=10):
    mod.place("iron-ore", x + 0.5, y + 0.5, amount=amount, force=False)


def test_mining_walks_there_and_takes_the_time_the_game_says(mod):
    ore(mod, 12, 3)
    r = mod.result("avatar_mine", {"x": 12, "y": 3, "count": 3})
    assert (r["mining"], r["gives"]) == ("iron-ore", "iron-ore")
    last = walk_and_watch(mod)
    assert last["ok"] and last["mined"] == 3 and mod.result("avatar")["carries"] == {"iron-ore": 3}
    assert last["ticks"] >= 3 * 30                                        # three items at thirty ticks each, plus the walk
    assert math.hypot(mod.body()[0] - 12.5, mod.body()[1] - 3.5) <= 2.7 + 0.4          # it mined from within reach
    assert mod.lua.eval("game.surfaces.nauvis.entities[1].amount") == 7


def test_mining_stops_when_the_ore_runs_out(mod):
    ore(mod, 3, 0, amount=2)
    mod.result("avatar_mine", {"x": 3, "y": 0, "count": 10})
    last = mod.run_job()
    assert last["ok"] is True and last["mined"] == 2 and "no more iron-ore" in last["reason"]


def test_a_tree_gives_wood(mod):
    mod.place("tree-01", 4.5, 0.5, force=False)
    assert mod.result("avatar_mine", {"x": 4, "y": 0, "count": 1})["gives"] == "wood"
    assert mod.run_job()["ok"] and mod.result("avatar")["carries"] == {"wood": 1}


def test_mining_refusals(mod):
    r = mod.call("avatar_mine", {"x": 50, "y": 50})
    assert not r["ok"] and "nothing to mine at 50,50" in r["error"]
    mod.place("cliff", 4.5, 0.5, force=False)
    assert "nothing to mine" in mod.call("avatar_mine", {"x": 4, "y": 0})["error"]     # a cliff is not hand-mined


def test_crafting_by_hand_uses_what_is_carried_and_takes_time(mod):
    mod.give(iron_plate=5)
    r = mod.result("avatar_craft", {"recipe": "iron-gear-wheel", "count": 2})
    assert r["started"] == 2 and mod.result("avatar")["carries"] == {"iron-plate": 1} and mod.result("avatar")["crafting_queue"] == 2
    mod.tick(40)
    assert mod.result("avatar")["carries"] == {"iron-plate": 1, "iron-gear-wheel": 1}
    mod.tick(40)
    a = mod.result("avatar")
    assert a["carries"] == {"iron-plate": 1, "iron-gear-wheel": 2} and a["crafting_queue"] == 0


def test_crafting_only_as_many_as_the_ingredients_allow(mod):
    mod.give(iron_plate=5)
    r = mod.result("avatar_craft", {"recipe": "iron-gear-wheel", "count": 9})
    assert r["started"] == 2 and r["asked"] == 9 and "only this many" in r["note"]


def test_crafting_refusals(mod):
    mod.give(iron_plate=1)
    r = mod.call("avatar_craft", {"recipe": "iron-gear-wheel"})
    assert "cannot craft" in r["error"] and r["hint"] == "it lacks: iron-plate"
    assert "no recipe named" in mod.call("avatar_craft", {"recipe": "warp-core"})["error"]
    mod.run("game.forces.player.recipes['lab'].enabled = false")
    assert "not researched" in mod.call("avatar_craft", {"recipe": "lab"})["error"]


def test_taking_from_and_putting_into_a_chest_within_reach(mod):
    mod.give(iron_plate=10)
    mod.place("wooden-chest", 3.5, 0.5, items={"copper-plate": 40})
    took = mod.result("avatar_carry", {"x": 3, "y": 0, "item": "copper-plate", "count": 15, "direction": "take"})
    put = mod.result("avatar_carry", {"x": 3, "y": 0, "item": "iron-plate", "count": 4, "direction": "put"})
    assert took["moved"] == 15 and put["moved"] == 4 and put["with"] == "wooden-chest"
    assert mod.result("avatar")["carries"] == {"iron-plate": 6, "copper-plate": 15}
    assert mod.lua.eval("game.surfaces.nauvis.entities[2].items['copper-plate']") == 25
    assert mod.lua.eval("game.surfaces.nauvis.entities[2].items['iron-plate']") == 4
    over = mod.result("avatar_carry", {"x": 3, "y": 0, "item": "copper-plate", "count": 999, "direction": "take"})
    assert over["moved"] == 25                                            # only what is there


def test_carrying_refusals(mod):
    mod.give(iron_plate=1)
    mod.place("wooden-chest", 40.5, 0.5, items={"copper-plate": 5})
    r = mod.call("avatar_carry", {"x": 40, "y": 0, "item": "copper-plate", "direction": "take"})
    assert "out of reach" in r["error"] and "walk to within 10 tiles" in r["hint"]
    assert "nothing of ours stands" in mod.call("avatar_carry", {"x": 9, "y": 9, "item": "coal", "direction": "put"})["error"]
    assert "'take' or 'put'" in mod.call("avatar_carry", {"x": 9, "y": 9, "item": "coal", "direction": "grab"})["error"]
    mod.place("wooden-chest", 2.5, 0.5)
    assert "no coal to put" in mod.call("avatar_carry", {"x": 2, "y": 0, "item": "coal", "direction": "put"})["error"]


def test_a_chest_that_fills_up_gives_the_rest_back(mod):
    mod.give(iron_plate=10)
    mod.place("wooden-chest", 2.5, 0.5)
    mod.run("game.surfaces.nauvis.entities[2].capacity = 3")
    assert mod.result("avatar_carry", {"x": 2, "y": 0, "item": "iron-plate", "count": 10, "direction": "put"})["moved"] == 3
    assert mod.result("avatar")["carries"] == {"iron-plate": 7}


# ---------------------------------------------------------------- building by hand

def belts(xs, y):
    return [{"name": "transport-belt", "x": x + 0.5, "y": y + 0.5, "direction": 4} for x in xs]


def test_the_mode_can_be_switched_at_any_time():
    mod = LuaMod()
    a = mod.result("avatar")
    assert (a["mode"], a["executor"], a["mode_means"]) == ("free-hand", "god", "builds on its own")
    assert mod.result("set_mode", {"mode": "my-character"}) == {"mode": "my-character", "means": "moves your character", "changed": True}
    assert mod.result("avatar")["executor"] == "avatar"
    assert mod.lua.eval("settings.global['skippy-copilot-mode'].value") == "my-character"      # the game's setting follows
    assert mod.result("set_mode", {"mode": "my-character"})["changed"] is False
    assert mod.result("set_mode", {"mode": "free-hand"})["changed"] is True
    assert "'free-hand' or 'my-character'" in mod.call("set_mode", {"mode": "wizard"})["error"]


def test_in_free_hand_mode_the_assistant_does_not_move_a_character():
    mod = LuaMod()
    for tool, args in (("avatar_walk", {"x": 5, "y": 5}), ("avatar_mine", {"x": 5, "y": 5}), ("avatar_craft", {"recipe": "iron-gear-wheel"}),
                       ("avatar_carry", {"x": 5, "y": 5, "item": "coal", "direction": "put"})):
        r = mod.call(tool, args)
        assert not r["ok"] and "free-hand mode" in r["error"] and "my-character" in r["hint"], tool
    assert mod.result("avatar")["has_body"] is False


def test_changing_the_setting_in_the_game_changes_the_mode():
    mod = LuaMod()
    mod.run("fake.add_player('captain', 0, 0)")
    mod.run("fake.change_setting('skippy-copilot-mode', 'my-character')")
    assert mod.result("avatar")["mode"] == "my-character"
    assert mod.lua.eval("game.players[1].gui.top.skippy_light.skippy_mode.caption") == "moves your character"
    mod.run("fake.change_setting('some-other-mods-setting', 'x')")
    assert mod.result("avatar")["mode"] == "my-character"


def test_the_button_on_the_working_light_switches_the_mode():
    mod = LuaMod()
    mod.run("fake.add_player('captain', 0, 0)")
    button = "game.players[1].gui.top.skippy_light.skippy_mode"
    assert mod.lua.eval(button + ".caption") == "builds on its own"
    mod.run("fake.click(1, %s)" % button)
    assert mod.result("avatar")["mode"] == "my-character" and mod.lua.eval(button + ".caption") == "moves your character"
    mod.run("fake.click(1, %s)" % button)
    assert mod.result("avatar")["mode"] == "free-hand"
    mod.run("fake.click(1, game.players[1].gui.top.skippy_light.state)")                         # clicking elsewhere does nothing
    assert mod.result("avatar")["mode"] == "free-hand"


def test_taking_the_character_back_stops_it_at_once(mod):
    mod.result("avatar_walk", {"x": 40, "y": 0})
    mod.tick(30)
    assert mod.result("set_mode", {"mode": "free-hand"})["changed"] is True
    here = mod.body()
    mod.tick(30)
    last = mod.result("avatar")["last_job"]
    assert mod.body() == here and last["ok"] is False and last["reason"] == "the mode was changed to free-hand"


def test_a_locked_mode_cannot_be_changed_during_a_scored_run(mod):
    assert mod.result("lock_mode", {"locked": True}) == {"mode": "my-character", "locked": True}
    r = mod.call("set_mode", {"mode": "free-hand"})
    assert not r["ok"] and "locked for this run to 'my-character'" in r["error"]
    mod.run("fake.add_player('captain', 0, 0)")
    mod.run("fake.click(1, game.players[1].gui.top.skippy_light.skippy_mode)")
    assert mod.result("avatar")["mode"] == "my-character" and "locked" in mod.lua.eval("game.players[1].printed[1]")
    mod.result("lock_mode", {"locked": False})
    assert mod.result("set_mode", {"mode": "free-hand"})["changed"] is True


def test_a_dry_run_says_what_the_avatar_must_carry_first(mod):
    mod.give(transport_belt=2)
    r = mod.result("build", {"entities": belts(range(5), 3) + [{"name": "inserter", "x": 0.5, "y": 5.5}]})
    assert r["would_place"] == 6 and r["failed_count"] == 0 and r["executor"] == "avatar"
    assert r["avatar_lacks"] == {"transport-belt": 3, "inserter": 1} and "must carry these items first" in r["note"]


def test_nothing_is_started_while_the_avatar_lacks_a_piece(mod):
    mod.give(transport_belt=2)
    r = mod.result("build", {"entities": belts(range(5), 3), "dry_run": False})
    assert r["placed"] == 0 and r["avatar_lacks"] == {"transport-belt": 3} and "nothing was started" in r["note"]
    assert mod.result("avatar").get("job") is None


def test_building_by_hand_walks_into_reach_places_and_uses_up_the_items(mod):
    mod.give(transport_belt=10)
    r = mod.result("build", {"entities": belts(range(30, 36), 4), "dry_run": False})
    assert r["queued"] == 6 and r["placed"] == 0 and r["executor"] == "avatar" and "job" in r
    assert mod.result("tile", {"x": 30, "y": 4})["free"] is True          # nothing appears at once
    last = walk_and_watch(mod)
    assert last["ok"] and (last["placed"], last["of"]) == (6, 6)
    for x in range(30, 36):
        thing = mod.result("tile", {"x": x, "y": 4})["things"][0]
        assert (thing["name"], thing["direction"]) == ("transport-belt", "East")
    assert mod.result("avatar")["carries"] == {"transport-belt": 4}
    assert mod.body()[0] > 15                                             # it had to walk: the pieces were 30 tiles off


def test_every_piece_is_placed_from_within_building_reach(mod):
    mod.give(transport_belt=40)
    pieces = belts(range(20, 60), 0)                                      # a line much longer than the reach
    mod.result("build", {"entities": pieces, "dry_run": False})
    mod.tick(1)
    seen = 0
    for _ in range(8000):
        if not mod.lua.eval("storage.avatar.job ~= nil"):
            break
        mod.tick(1)
        count = mod.lua.eval("game.surfaces.nauvis.count_entities_filtered{name = 'transport-belt'}")
        if count > seen:
            newest = mod.lua.eval("game.surfaces.nauvis.entities[#game.surfaces.nauvis.entities].position")
            bx, by = mod.body()
            assert math.hypot(newest.x - bx, newest.y - by) <= 10 + 1e-6, "placed from %s tiles away" % math.hypot(newest.x - bx, newest.y - by)
            seen = count
    assert seen == 40 and mod.result("avatar")["last_job"]["ok"]


def test_pieces_are_built_in_walking_order_not_in_the_order_given(mod):
    mod.give(transport_belt=3)
    far, near, mid = belts([60], 0)[0], belts([15], 0)[0], belts([35], 0)[0]
    mod.result("build", {"entities": [far, near, mid], "dry_run": False})
    assert [p.x for p in mod.lua.eval("storage.avatar.job.pieces").values()] == [15.5, 35.5, 60.5]


def test_a_spot_that_gets_taken_while_it_walks_stops_the_job_with_the_count_so_far(mod):
    mod.give(transport_belt=3)
    mod.result("build", {"entities": belts([20, 40, 60], 0), "dry_run": False})
    mod.tick(5)
    mod.place("wooden-chest", 40.5, 0.5)
    last = mod.run_job()
    assert last["ok"] is False and (last["placed"], last["of"]) == (1, 3)
    assert "in the way at 40.5,0.5" in last["reason"] and last["stopped_at"]["name"] == "transport-belt"


def test_a_machine_gets_its_recipe_and_an_underground_its_type(mod):
    mod.give(assembling_machine_2=1, underground_belt=1)
    mod.result("build", {"entities": [{"name": "assembling-machine-2", "x": 6.5, "y": 6.5, "recipe": "copper-cable"},
                                      {"name": "underground-belt", "x": 9.5, "y": 6.5, "direction": 4, "type": "input"}], "dry_run": False})
    assert mod.run_job()["ok"]
    assert mod.result("tile", {"x": 6, "y": 6})["things"][0]["recipe"] == "copper-cable"
    assert mod.lua.eval("game.surfaces.nauvis.entities[#game.surfaces.nauvis.entities].belt_to_ground_type") == "input"


def test_research_still_gates_the_avatar(mod):
    mod.give(lab=1)
    mod.run("game.forces.player.recipes['lab'].enabled = false")
    r = mod.result("build", {"entities": [{"name": "lab", "x": 6.5, "y": 6.5}], "dry_run": False})
    assert r["placed"] == 0 and "not researched" in r["failed"][0]["why"] and mod.result("avatar").get("job") is None


def test_a_build_cannot_start_while_the_avatar_is_busy(mod):
    mod.give(transport_belt=2)
    mod.result("avatar_walk", {"x": 50, "y": 0})
    r = mod.call("build", {"entities": belts([3], 3), "dry_run": False})
    assert not r["ok"] and "busy with a walk job" in r["error"]


def test_free_placement_needs_no_character():
    mod = LuaMod()
    r = mod.result("build", {"entities": belts(range(3), 3), "dry_run": False})
    assert r["placed"] == 3 and r["executor"] == "god" and mod.result("avatar")["has_body"] is False


# ---------------------------------------------------------------- the exit test of increment 1

def test_walk_across_a_base_with_obstacles_and_build_a_ten_machine_line_from_the_inventory(mod):
    """Plan increment 1: 'A script walks the character across a base with obstacles and builds a 10-machine line from
    its inventory, with zero teleports and zero out-of-reach actions.'"""
    wall(mod, 12, -15, 15)                                                # a base in the way: two walls with gaps at different ends
    wall(mod, 24, -5, 25)
    for y in range(-30, 31):
        mod.run("game.surfaces.nauvis.set(36, %d, 'water')" % y)          # and a river with one crossing
    mod.run("game.surfaces.nauvis.set(36, 28, 'grass-1')")
    mod.give(assembling_machine_2=10, inserter=20, transport_belt=60)

    line = []                                                             # ten belt-fed machines in a row, east of everything
    for i in range(10):
        x = 45 + 3 * i
        line += belts(range(x, x + 3), 0)
        line.append({"name": "inserter", "x": x + 1.5, "y": 1.5, "direction": 0})
        line.append({"name": "assembling-machine-2", "x": x + 1.5, "y": 3.5, "recipe": "iron-gear-wheel"})
        line.append({"name": "inserter", "x": x + 1.5, "y": 5.5, "direction": 0})
        line += belts(range(x, x + 3), 6)
    dry = mod.result("build", {"entities": line})
    assert dry["would_place"] == 90 and dry["failed_count"] == 0 and "avatar_lacks" not in dry

    mod.result("build", {"entities": line, "dry_run": False})
    mod.tick(1)
    last_pos, placed_seen, worst_reach = mod.body(), 0, 0.0
    for _ in range(30000):
        if not mod.lua.eval("storage.avatar.job ~= nil"):
            break
        mod.tick(1)
        now = mod.body()
        assert math.hypot(now[0] - last_pos[0], now[1] - last_pos[1]) <= STEP, "teleport: %s to %s" % (last_pos, now)
        last_pos = now
        placed = mod.lua.eval("storage.avatar.job and storage.avatar.job.placed or -1")
        if placed > placed_seen:
            newest = mod.lua.eval("game.surfaces.nauvis.entities[#game.surfaces.nauvis.entities].position")
            worst_reach = max(worst_reach, math.hypot(newest.x - now[0], newest.y - now[1]))
            placed_seen = placed
    last = mod.result("avatar")["last_job"]
    assert last["ok"], last
    assert (last["placed"], last["of"]) == (90, 90)
    assert worst_reach <= 10 + 1e-6, "a piece was placed from %.1f tiles away" % worst_reach
    assert mod.lua.eval("game.surfaces.nauvis.count_entities_filtered{name = 'assembling-machine-2'}") == 10
    assert mod.result("avatar")["carries"] == {}                          # every carried piece was used, none conjured
    d = mod.result("diagnose")
    assert d["machines_checked"] == 10
