"""The mod's own Lua, run under Lua 5.2 against a stand-in game. Every call goes through the /skippy command, as the
bridge's calls do."""
import pytest

from luamod import LuaMod


@pytest.fixture
def mod():
    return LuaMod()


@pytest.fixture
def scene():
    return LuaMod().scene()


# ---------------------------------------------------------------- the command and the registry

def test_the_tool_list_describes_every_tool(mod):
    tools = mod.result("tools")
    names = [t["name"] for t in tools]
    assert {"lookup", "search", "map", "tile", "find_free", "diagnose", "bottlenecks", "alerts", "player", "design_note", "events_read",
            "reveal_map", "chat_read", "say", "set_state", "occupancy", "build", "frames"} == set(names)
    assert all(len(t["description"]) > 30 for t in tools)
    lookup = [t for t in tools if t["name"] == "lookup"][0]
    assert lookup["parameters"]["name"]["required"] is True and lookup["parameters"]["kind"]["required"] is False


def test_a_bare_command_lists_the_tools_too(mod):
    assert mod.call("")["ok"] and len(mod.call("")["result"]) == 18


def test_bad_calls_are_answered_with_what_would_have_been_right(mod):
    r = mod.call("nope")
    assert not r["ok"] and "no tool named 'nope'" in r["error"] and "lookup" in r["tools"]
    r = mod.call("lookup", {"nam": "x"})
    assert not r["ok"] and "no parameter 'nam'" in r["error"] and r["tool"]["name"] == "lookup"
    r = mod.call("lookup", {})
    assert not r["ok"] and "needs the parameter 'name'" in r["error"]
    r = mod.call("lookup", {"name": 5})
    assert not r["ok"] and "must be a string, got a number" in r["error"]
    out = mod.fake.command("lookup {not json")
    assert "not valid JSON" in out


def test_defaults_are_filled_in(mod):
    assert mod.result("search", {"text": "circuit"})["more_exist"] is False


def test_a_crash_inside_a_tool_is_an_answer_not_a_crash(mod):
    mod.run("prototypes.recipe['broken'] = { name = 'broken' }")           # no ingredients, no energy: the tool will trip
    mod.run("game.forces.player.recipes['broken'] = nil")
    r = mod.call("lookup", {"name": "broken", "kind": "recipe"})
    assert r["ok"] or "failed inside the mod" in r["error"]


def test_only_admins_may_type_tool_calls(mod):
    mod.run("fake.add_player('guest', 0, 0, false)")
    assert mod.fake.command("tools", 1) is None                           # nothing went back over RCON
    assert "Only admins" in mod.lua.eval("game.players[1].printed[1]")


def test_an_admin_sees_the_answer_in_the_console(mod):
    mod.run("fake.add_player('captain', 0, 0, true)")
    mod.fake.command('search {"text":"lab"}', 1)
    assert '"ok":' in mod.lua.eval("game.players[1].printed[1]").replace(" ", "")


# ---------------------------------------------------------------- lookup and search

def test_recipe_facts(mod):
    r = mod.result("lookup", {"name": "electronic-circuit", "kind": "recipe"})[0]
    assert {i["name"]: i["amount"] for i in r["ingredients"]} == {"iron-plate": 1, "copper-cable": 3}
    assert r["seconds"] == 0.5 and r["available_now"] is True and r["unlocked_by"] == ["electronics"]
    assert r["made_in"] == ["assembling-machine-2", "electromagnetic-plant"]
    assert "only_where" not in r


def test_surface_conditions_and_probability(mod):
    r = mod.result("lookup", {"name": "cryogenic-science-pack", "kind": "recipe"})[0]
    assert r["only_where"] == [{"property": "pressure", "min": 300, "max": 300}]
    r = mod.result("lookup", {"name": "iron-gear-wheel-recycling", "kind": "recipe"})[0]
    assert r["products"][0]["probability"] == 0.25


def test_item_facts_leave_recycling_out_of_the_recipes(mod):
    r = mod.result("lookup", {"name": "iron-plate", "kind": "item"})[0]
    assert r["made_by_recipes"] == ["iron-plate"] and "1 other items" in r["also_comes_out_of_recycling"]
    assert (r["stack_size"], r["weight_kg"], r["fits_in_one_rocket"]) == (100, 1, 1000)
    coal = mod.result("lookup", {"name": "coal", "kind": "item"})[0]
    assert coal["fuel_megajoules"] == 4 and "made_by_recipes" not in coal
    food = mod.result("lookup", {"name": "nutrients", "kind": "item"})[0]
    assert food["spoils_after_seconds"] == 300 and food["spoils_into"] == "spoilage"
    assert mod.result("lookup", {"name": "transport-belt", "kind": "item"})[0]["places"] == "transport-belt"


def test_entity_facts(mod):
    r = mod.result("lookup", {"name": "assembling-machine-2", "kind": "entity"})[0]
    assert (r["tiles_wide"], r["tiles_high"], r["crafting_speed"], r["module_slots"], r["power_kilowatts"]) == (3, 3, 0.75, 2, 150)
    assert "pole_wire_reach" not in r                                     # only poles report reach
    pole = mod.result("lookup", {"name": "medium-electric-pole", "kind": "entity"})[0]
    assert (pole["pole_supply_tiles"], pole["pole_wire_reach"]) == (7, 9)
    tower = mod.result("lookup", {"name": "heating-tower", "kind": "entity"})[0]
    assert len(tower["heat"]["connections"]) == 4 and tower["heat"]["connections"][0] == {"x": 0, "y": -1}
    assert tower["only_where"] == [{"property": "pressure", "min": 10}]    # an unbounded maximum is left out
    assert mod.result("lookup", {"name": "transport-belt", "kind": "entity"})[0]["belt_items_per_second"] == 15


def test_technology_facts(mod):
    r = mod.result("lookup", {"name": "automation-2", "kind": "technology"})[0]
    assert r["researched"] is False and r["units"] == 40 and r["unlocks_recipes"] == ["assembling-machine-2"]
    assert r["prerequisites"] == [{"name": "electronics", "researched": False}] and len(r["science_packs"]) == 2
    trig = mod.result("lookup", {"name": "cryogenic-science-pack", "kind": "technology"})[0]
    assert trig["earned_by"] == {"type": "craft-item", "item": "cryogenic-plant", "count": 1} and "units" not in trig


def test_a_name_with_no_kind_returns_every_kind_that_has_it(mod):
    kinds = [r["kind"] for r in mod.result("lookup", {"name": "assembling-machine-2"})]
    assert kinds == ["recipe", "item", "entity"]


def test_misspelt_and_unknown_names(mod):
    r = mod.call("lookup", {"name": "electronic-circut"})
    assert not r["ok"] and any(s["name"] == "electronic-circuit" for s in r["similar"])
    r = mod.call("lookup", {"name": "zzz"})
    assert not r["ok"] and "similar" not in r and "search" in r["hint"]
    assert "kind must be one of" in mod.call("lookup", {"name": "lab", "kind": "building"})["error"]


def test_search(mod):
    r = mod.result("search", {"text": "circuit"})
    assert {(m["kind"], m["name"]) for m in r["matches"]} == {("recipe", "electronic-circuit"), ("item", "electronic-circuit")}
    assert mod.result("search", {"text": "e", "limit": 3}) ["more_exist"] is True
    assert mod.result("search", {"text": "pipe", "kind": "entity"})["matches"] == [{"kind": "entity", "name": "pipe"}, {"kind": "entity", "name": "pipe-to-ground"}]


# ---------------------------------------------------------------- map, tile, find_free

def rows_of(picture, left):
    rows = {}
    for line in picture.split("\n")[2:]:
        rows[int(line[:4])] = line[5:]
    return lambda x, y: rows[y][x - left]


def test_the_map_picture(scene):
    m = scene.result("map", {"x": -16, "y": -10, "width": 36, "height": 18})
    at = rows_of(m["picture"], m["left_x"])
    assert at(2, 0) == "A" and at(4, 2) == "A" and at(5, 0) == "."                 # the machine covers 2..4, 0..2
    assert at(0, 4) == "b" and at(10, 4) == "b" and at(11, 4) == "." and at(3, 3) == "i"
    assert at(-9, -4) == "M" and at(-6, -6) == ":"                                 # a drill is drawn over the ore under it
    assert at(12, -8) == "~" and at(0, -7) == "?"
    legend = {e["char"]: e for e in m["legend"]}
    assert legend["A"]["here"] == ["assembling-machine-2 x1"] and legend["?"]["here"] == ["ghost of lab x1"]
    assert legend[":"]["here"] == ["iron-ore x25"] and legend["~"]["means"] == "water"


def test_the_ruler_marks_every_fifth_column(scene):
    lines = scene.result("map", {"x": -16, "y": -10, "width": 36, "height": 4})["picture"].split("\n")
    marks = lines[1][5:]
    assert [i - 16 for i, ch in enumerate(marks) if ch == "|"] == [-15, -10, -5, 0, 5, 10, 15]
    assert lines[0][5 + 6:5 + 9] == "-10" and lines[0][5 + 16] == "0"              # labels start over their column


def test_the_map_window_is_capped(mod):
    m = mod.result("map", {"x": 0, "y": 0, "width": 500, "height": 500})
    assert (m["width"], m["height"]) == (60, 40) and len(m["picture"].split("\n")) == 42


def test_an_unknown_surface_lists_the_surfaces(mod):
    r = mod.call("map", {"x": 0, "y": 0, "surface": "mars"})
    assert not r["ok"] and "no surface named 'mars'" in r["error"] and "nauvis" in r["hint"]


def test_tile(scene):
    t = scene.result("tile", {"x": 3, "y": 1})
    thing = t["things"][0]
    assert not t["free"] and (thing["name"], thing["recipe"], thing["state"], thing["direction"]) == ("assembling-machine-2", "iron-gear-wheel", "no_power", "North")
    assert thing["covers"] == {"from_x": 2, "from_y": 0, "to_x": 4, "to_y": 2} and (thing["centre_x"], thing["centre_y"]) == (3.5, 1.5)
    both = scene.result("tile", {"x": -8, "y": -4})
    assert {x["name"] for x in both["things"]} == {"iron-ore", "electric-mining-drill"}
    assert [x["amount"] for x in both["things"] if x["name"] == "iron-ore"] == [500]
    assert scene.result("tile", {"x": 0, "y": -7})["things"][0]["name"] == "lab"   # a ghost is named by what it will be
    assert scene.result("tile", {"x": 15, "y": 8})["free"] is True
    water = scene.result("tile", {"x": 13, "y": -6})
    assert water["free"] is False and water["ground"] == "water" and water["things"] == {}


def test_find_free_returns_a_rectangle_that_is_really_free(scene):
    r = scene.result("find_free", {"x": 3, "y": 1, "width": 6, "height": 4})
    assert r["found"]
    for x in range(r["left_x"], r["left_x"] + 6):
        for y in range(r["top_y"], r["top_y"] + 4):
            assert scene.result("tile", {"x": x, "y": y})["free"], (x, y)
    assert r["tiles_from_start"] > 0                                              # the spot asked for is taken


def test_find_free_on_ore_only_when_allowed(scene):
    no = scene.result("find_free", {"x": -6, "y": -6, "width": 1, "height": 1, "radius": 0})
    yes = scene.result("find_free", {"x": -6, "y": -6, "width": 1, "height": 1, "radius": 0, "allow_resources": True})
    assert no["found"] is False and "hint" in no and yes["found"] is True


def test_find_free_avoids_water_and_refuses_giant_requests(scene):
    r = scene.result("find_free", {"x": 14, "y": -6, "width": 2, "height": 2})
    for x in range(r["left_x"], r["left_x"] + 2):
        for y in range(r["top_y"], r["top_y"] + 2):
            assert scene.result("tile", {"x": x, "y": y})["ground"] != "water"
    assert "at most 100" in scene.call("find_free", {"x": 0, "y": 0, "width": 101, "height": 5})["error"]


# ---------------------------------------------------------------- diagnose and bottlenecks

def test_diagnose_groups_machines_by_state(scene):
    scene.place("stone-furnace", 20, 20, status="no_fuel")
    scene.place("assembling-machine-2", 30.5, 20.5, recipe="copper-cable", status="working")
    d = scene.result("diagnose")
    problems = {p["state"]: p for p in d["problems"]}
    assert d["machines_checked"] == 4 and problems["no_power"]["count"] == 2 and problems["no_fuel"]["count"] == 1
    assert problems["no_power"]["means"] == "not connected to power" and len(problems["no_power"]["examples"]) == 2
    assert [p["state"] for p in d["problems"]][0] == "no_power"                    # the commonest problem first
    assert d["fine"] == [{"state": "working", "count": 1, "machines": ["assembling-machine-2 x1"]}]
    assert d["research"] == "nothing is being researched"


def test_diagnose_in_an_area_needs_all_four_numbers(scene):
    assert scene.result("diagnose", {"x": 0, "y": 0, "width": 10, "height": 10})["machines_checked"] == 1
    assert "all four" in scene.call("diagnose", {"width": 800, "height": 600})["error"]


def starved_factory(mod):
    for i in range(4):                                                             # four circuit machines out of cable, one also out of iron
        mod.place("assembling-machine-2", 3.5 + 4 * i, 1.5, recipe="electronic-circuit", status="item_ingredient_shortage",
                  items={"iron-plate": 0 if i == 0 else 5, "copper-cable": 1})
    mod.place("assembling-machine-2", 3.5, 11.5, recipe="iron-gear-wheel", status="item_ingredient_shortage", items={"iron-plate": 1})
    for i in range(2):
        mod.place("assembling-machine-2", 3.5 + 4 * i, 21.5, recipe="copper-cable", status="full_output")
    mod.place("assembling-machine-2", 103.5, 101.5, recipe="lab", status="item_ingredient_shortage", items={})
    return mod


def test_bottlenecks_are_ranked_by_the_item_machines_wait_for(mod):
    b = starved_factory(mod).result("bottlenecks", {"top": 10})["bottlenecks"]
    assert [(x["rank"], x["problem"], x["machines_waiting"]) for x in b] == [
        (1, "starved of copper-cable", 4), (2, "starved of iron-plate", 2), (3, "backed up with copper-cable", 2), (4, "starved of electronic-circuit", 1)]
    assert b[0]["those_machines_make"] == ["electronic-circuit x4"] and len(b[0]["examples"]) == 3
    assert (b[0]["centre_x"], b[0]["centre_y"]) == (9, 1)
    assert "find what makes or carries copper-cable" in b[0]["look"] and "takes copper-cable away" in b[2]["look"]


def test_top_three_and_the_rest_counted(mod):
    r = starved_factory(mod).result("bottlenecks")
    assert len(r["bottlenecks"]) == 3 and r["others_not_shown"] == 1 and "power_first" not in r


def test_the_bottleneck_next_to_the_player(mod):
    starved_factory(mod).run("fake.add_player('captain', 104, 102)")
    r = mod.result("bottlenecks", {"near_player": True, "radius": 10})
    assert [x["problem"] for x in r["bottlenecks"]] == ["starved of electronic-circuit"]


def test_bottlenecks_round_a_point_and_refusals(mod):
    starved_factory(mod)
    assert [x["item"] for x in mod.result("bottlenecks", {"x": 4, "y": 21, "radius": 5})["bottlenecks"]] == ["copper-cable"]
    assert "both x and y" in mod.call("bottlenecks", {"x": 4})["error"]
    assert "no player" in mod.call("bottlenecks", {"near_player": True})["error"]


def test_power_comes_before_any_bottleneck(scene):
    r = scene.result("bottlenecks")
    assert r["bottlenecks"] == {} and "1 machines have no power" in r["power_first"]


# ---------------------------------------------------------------- alerts, player, frames, reveal

def test_alerts_with_nobody_in_the_game(mod):
    r = mod.result("alerts")
    assert r["alerts"] == {} and "no player" in r["note"]


def test_alerts_by_kind_with_meaning_and_examples(scene):
    scene.run("local p = fake.add_player('captain', 0, 0) local ghost = game.surfaces.nauvis.entities[#game.surfaces.nauvis.entities] "
              "p.alerts = { [1] = { [defines.alert_type.no_material_for_construction] = { { target = ghost, position = ghost.position }, { position = { x = 5, y = 6 } } }, "
              "[defines.alert_type.train_out_of_fuel] = { { position = { x = -449, y = -410 } } } } }")
    a = scene.result("alerts")["alerts"]
    assert [(x["kind"], x["count"], x["surface"]) for x in a] == [("no_material_for_construction", 2, "nauvis"), ("train_out_of_fuel", 1, "nauvis")]
    assert "not in the logistic network" in a[0]["means"] and a[0]["examples"][0] == {"x": 0.5, "y": -6.5, "what": "ghost of lab"}
    assert a[1]["means"] == "a train has no fuel" and a[1]["examples"] == [{"x": -449, "y": -410}]


def test_player_position_and_what_they_point_at(scene):
    assert "no such player" in scene.call("player")["error"]
    scene.run("local p = fake.add_player('captain', 12.7, -7.2) p.selected = game.surfaces.nauvis.entities[1]")
    r = scene.result("player")
    assert (r["name"], r["surface"], r["x"], r["y"]) == ("captain", "nauvis", 12, -8)
    assert r["pointing_at"] == {"name": "assembling-machine-2", "type": "assembling-machine", "x": 3.5, "y": 1.5}
    assert "no such player" in scene.call("player", {"name": "nobody"})["error"]


def test_frames_for_pointing_with_words(scene):
    assert "no player" in scene.call("frames")["error"]
    assert "no player named 'nobody'" in scene.call("frames", {"name": "nobody"})["error"]
    scene.place("medium-electric-pole", -20.5, -30.5)
    scene.place("medium-electric-pole", 40.5, 10.5)
    scene.run("fake.add_player('captain', 0, 0) for _, c in pairs({ '-2,-1', '1,0', '0,1' }) do game.surfaces.nauvis.charted[c] = true end")
    f = scene.result("frames")
    assert f["view"] == [-30, -17, 30, 16] or f["view"] == [-30, -17, 30, 17]      # 1920 by 1080 pixels at 32 a tile
    assert f["base"] == [-21, -31, 40, 10] and f["player"] == [-15, -15, 15, 15]
    assert f["map"] == [-64, -32, 63, 63] and f["surface"] == "nauvis"


def test_zooming_out_widens_the_view(scene):
    scene.run("local p = fake.add_player('captain', 100, 50) p.zoom = 0.5")
    v = scene.result("frames")["view"]
    assert v[2] - v[0] == 120 and (v[0] + v[2]) // 2 == 100


def test_reveal_map_charts_a_ring_round_the_known_map(mod):
    mod.run("game.surfaces.nauvis.charted['0,0'] = true game.surfaces.nauvis.charted['-1,-1'] = true")
    r = mod.result("reveal_map", {"depth": 64})
    assert r["was"] == [-32, -32, 31, 31] and r["now"] == [-96, -96, 95, 95]
    assert mod.lua.eval("fake.charted[1].area[1][1]") == -96 and mod.lua.eval("fake.charted[1].surface") == "nauvis"
    assert mod.result("reveal_map", {"depth": 5})["now"][0] == -64                 # at least a chunk, whatever was asked
    mod.run("storage.executor = 'avatar'")
    assert "on foot is not built yet" in mod.call("reveal_map")["error"]


# ---------------------------------------------------------------- occupancy and build

def test_occupancy_for_the_router(scene):
    scene.place("pipe", -14.5, 6.5)
    scene.place("tree-01", -12.5, 6.5, force=False)
    o = scene.result("occupancy", {"x": -16, "y": -10, "width": 36, "height": 18})

    def at(x, y):
        return o["rows"][y + 10][x + 16]
    assert at(3, 1) == "#" and at(5, 4) == "#" and at(13, -6) == "#"               # machine, belt, water
    assert at(-6, -6) == "." and at(15, 7) == "."                                  # ore does not block; free ground
    assert at(-15, 6) == "p" and at(-13, 6) == "#" and at(0, -7) == "#"            # a pipe is marked; a tree and a ghost block
    assert len(o["rows"]) == 18 and all(len(r) == 36 for r in o["rows"])
    assert "between 1 and 100" in scene.call("occupancy", {"x": 0, "y": 0, "width": 101, "height": 5})["error"]


BELT = {"name": "transport-belt", "x": 15.5, "y": 8.5, "direction": 4}
ON_MACHINE = {"name": "transport-belt", "x": 3.5, "y": 1.5, "direction": 4}


def test_a_dry_run_places_nothing(scene):
    r = scene.result("build", {"entities": [BELT]})
    assert r["would_place"] == 1 and r["failed_count"] == 0 and "every piece can be placed" in r["note"]
    assert scene.result("tile", {"x": 15, "y": 8})["free"] is True


def test_refusals_carry_a_reason_for_each_piece(scene):
    scene.run("game.forces.player.recipes['lab'].enabled = false")
    r = scene.result("build", {"entities": [ON_MACHINE, {"name": "warp-drive", "x": 20.5, "y": 20.5}, {"name": "lab", "x": 20.5, "y": 20.5},
                                            {"name": "transport-belt", "x": 13.5, "y": -6.5}, {"name": "pipe"}, BELT]})
    why = {(f["name"], f.get("x")): f["why"] for f in r["failed"]}
    assert r["would_place"] == 1 and r["failed_count"] == 5
    assert "in the way" in why[("transport-belt", 3.5)] and "no building named 'warp-drive'" in why[("warp-drive", 20.5)]
    assert "not researched" in why[("lab", 20.5)] and "ground there does not allow" in why[("transport-belt", 13.5)]
    assert "no position" in why[("pipe", None)]


def test_a_recipe_that_is_not_researched_stops_the_machine(scene):
    scene.run("game.forces.player.recipes['electronic-circuit'].enabled = false")
    r = scene.result("build", {"entities": [{"name": "assembling-machine-2", "x": 21.5, "y": 21.5, "recipe": "electronic-circuit"}]})
    assert "recipe 'electronic-circuit' is not researched" in r["failed"][0]["why"]


def test_nothing_is_placed_unless_every_piece_can_be(scene):
    r = scene.result("build", {"entities": [BELT, ON_MACHINE], "dry_run": False})
    assert r["placed"] == 0 and r["failed_count"] == 1 and "nothing was placed" in r["note"]
    assert scene.result("tile", {"x": 15, "y": 8})["free"] is True


def test_a_clean_plan_is_placed_as_asked(scene):
    pieces = [BELT, {"name": "underground-belt", "x": 16.5, "y": 8.5, "direction": 4, "type": "input"},
              {"name": "assembling-machine-2", "x": 21.5, "y": 21.5, "recipe": "copper-cable"}]
    r = scene.result("build", {"entities": pieces, "dry_run": False})
    assert r["placed"] == 3 and r["failed_count"] == 0 and r["executor"] == "god"
    belt = scene.result("tile", {"x": 15, "y": 8})["things"][0]
    assert (belt["name"], belt["direction"]) == ("transport-belt", "East")
    assert scene.result("tile", {"x": 21, "y": 21})["things"][0]["recipe"] == "copper-cable"
    assert scene.lua.eval("game.surfaces.nauvis.entities[#game.surfaces.nauvis.entities - 1].belt_to_ground_type") == "input"
    again = scene.result("build", {"entities": [BELT]})                            # the tile is taken now
    assert again["failed_count"] == 1


def test_build_limits(mod):
    assert "empty" in mod.call("build", {"entities": []})["error"]
    many = [{"name": "transport-belt", "x": i + 0.5, "y": 50.5} for i in range(601)]
    assert "at most 600" in mod.call("build", {"entities": many})["error"]


# ---------------------------------------------------------------- chat, working light, research news

def test_chat_lines_are_kept_in_order_and_read_from_a_point(mod):
    mod.run("fake.add_player('captain', 0, 0)")
    for text in ("first", "", "second", "third"):
        mod.run("fake.chat(1, %r)" % text)
    r = mod.result("chat_read")
    assert [(l["id"], l["player"], l["text"]) for l in r["lines"]] == [(1, "captain", "first"), (2, "captain", "second"), (3, "captain", "third")]
    assert r["last_id"] == 3
    assert [l["text"] for l in mod.result("chat_read", {"after": 2})["lines"]] == ["third"]
    assert mod.result("chat_read", {"after": 3})["lines"] == {}


def test_only_the_last_two_hundred_lines_are_kept(mod):
    for i in range(205):
        mod.run("fake.chat(nil, 'line %d')" % i)
    r = mod.result("chat_read")
    assert len(r["lines"]) == 200 and r["lines"][0]["text"] == "line 5" and r["lines"][0]["player"] == "server" and r["last_id"] == 205


def test_say_prints_in_the_game(mod):
    mod.result("say", {"text": "hello"})
    assert "[Skippy]" in mod.lua.eval("fake.printed[1]") and mod.lua.eval("fake.printed[1]").endswith("hello")


def test_the_working_light_shows_on_every_player_and_on_players_who_join_later(mod):
    mod.run("fake.add_player('captain', 0, 0)")
    assert mod.lua.eval("game.players[1].gui.top.skippy_light.state.caption") == "Skippy: idle"
    mod.result("set_state", {"state": "working", "note": "routing a belt"})
    assert mod.lua.eval("game.players[1].gui.top.skippy_light.state.caption") == "Skippy: working - routing a belt"
    mod.run("fake.add_player('guest', 0, 0)")
    assert mod.lua.eval("game.players[2].gui.top.skippy_light.state.caption") == "Skippy: working - routing a belt"
    mod.result("set_state", {"state": "blocked"})
    assert mod.lua.eval("game.players[2].gui.top.skippy_light.state.caption") == "Skippy: needs you"
    assert "state must be one of" in mod.call("set_state", {"state": "napping"})["error"]
    assert mod.lua.eval("#game.players[1].gui.top.children") == 1                  # one light, not one per update


def test_research_news_carries_the_unlocks_and_the_design_note(mod):
    assert mod.result("events_read") == {"events": {}, "last_id": 0}
    mod.run("fake.research('automation-2') fake.research('worker-robots-speed-1')")
    ev = mod.result("events_read")
    first, second = ev["events"]
    assert (first["kind"], first["technology"], first["unlocks_recipes"]) == ("research_finished", "automation-2", ["assembling-machine-2"])
    assert "half again as fast" in first["design_note"] and first["id"] == 1 and first["tick"] == 100
    assert second["other_effects"] == ["worker-robot-speed"] and "design_note" not in second and "unlocks_recipes" not in second
    assert mod.result("events_read", {"after": 1})["events"][0]["technology"] == "worker-robots-speed-1"


def test_a_numbered_technology_gets_the_note_of_its_family(mod):
    mod.run("fake.research('speed-module-2')")
    assert "Speed modules raise output" in mod.result("events_read")["events"][0]["design_note"]


def test_design_note_by_name_and_for_recent_research(mod):
    r = mod.result("design_note", {"technology": "automation-2"})
    assert r["researched"] is False and "half again" in r["design_note"]
    assert "no technology named" in mod.call("design_note", {"technology": "warp"})["error"]
    assert mod.result("design_note") == {"recent": {}}
    mod.run("fake.research('electronics') fake.research('automation-2')")
    assert [e["technology"] for e in mod.result("design_note")["recent"]] == ["automation-2", "electronics"]


def test_research_by_another_force_is_not_news(mod):
    mod.run("fake.handlers[defines.events.on_research_finished] { research = { name = 'x', force = { name = 'enemy' }, prototype = { effects = {} } } }")
    assert mod.result("events_read")["events"] == {}
