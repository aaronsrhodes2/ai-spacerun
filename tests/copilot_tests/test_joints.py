"""Joints: the small patterns for where supply lines meet and cross. Each is checked for the property that makes it
work in the game (the belt really passes under, the feeder really ends against the side, each wagon tile has its
inserter), then built through the mod's Lua to see the filters and priorities arrive on the pieces."""
import pytest

from copilot.plan import joints
from copilot.plan.layout import E, N, S, W, LayoutError
from copilot.tools import LocalTools
from luamod import LuaMod
from test_bridge_with_mod import LuaGame
from test_route import follow_belt

CHARS = {"transport-belt": "b", "underground-belt": "U", "splitter": "S", "inserter": "i", "pipe": "p", "pipe-to-ground": "q", "steel-chest": "C"}


def pieces(lay, role):
    return [p for p in lay.pieces if p.get("role") == role]


def test_every_joint_says_what_problem_it_solves_and_holds_no_recipe_or_place():
    cat = joints.catalogue()
    assert len(cat) >= 8 and all(len(j["solves"]) > 30 for j in cat)
    ports = [{"flow": "input", "x": -1, "y": -1, "direction": "north"}]
    gives = [{"flow": "output", "x": 0, "y": -1, "direction": "north"}]
    sample = {"item": "iron-plate", "machine": "chemical-plant", "width": 3, "height": 3, "ports": ports, "length": 20,
              "first": "boiler", "first_width": 3, "first_height": 2, "first_ports": gives,
              "second": "steam-engine", "second_width": 3, "second_height": 5, "second_ports": [{"flow": "input", "x": 0, "y": 2, "direction": "south"}]}
    for name in joints.JOINTS:
        need = {k: sample[k] for k, v in joints.JOINTS[name]["options"].items() if "required" in v}
        lay = joints.make(name, **need)
        assert all("recipe" not in p for p in lay.pieces), name
        assert len(lay.pieces) <= 30, "%s is too big to be a joint" % name
        machines = [p for p in lay.pieces if p.get("role") == "machine"]
        assert len(machines) <= 1, "%s holds more than one machine: that is a production line, not a joint" % name
        assert len({p["name"] for p in lay.pieces if p.get("role") in ("drill", "first", "second")}) <= 2, name


def test_a_belt_crosses_a_belt_underneath():
    lay = joints.belt_crossing()
    assert lay.picture(CHARS) == ".b.\n.U.\nbbb\n.U.\n.b."
    main = {"pieces": [dict(p) for p in lay.pieces if p["role"] != "crossing"]}
    follow_belt(main, (0, 4), (0, 0))                                   # an item on the main belt comes out the other side
    assert all(p["direction"] == E for p in pieces(lay, "crossing"))
    assert pieces(lay, "entrance")[0]["type"] == "input" and pieces(lay, "exit")[0]["type"] == "output"
    assert pieces(lay, "entrance")[0]["y"] > pieces(lay, "exit")[0]["y"]            # going north: in at the south, out at the north


def test_a_wider_crossing_and_other_belts():
    lay = joints.belt_crossing(width=3)
    assert lay.picture(CHARS) == ".b.\n.U.\nbbb\nbbb\nbbb\n.U.\n.b."
    fast = joints.belt_crossing(belt="fast-transport-belt")
    assert fast.count() == {"fast-transport-belt": 5, "fast-underground-belt": 2}
    mixed = joints.belt_crossing(belt="express-transport-belt", crossing_belt="transport-belt")
    assert mixed.count()["transport-belt"] == 3 and mixed.count()["express-underground-belt"] == 2
    with pytest.raises(LayoutError, match="no underground belt"):
        joints.belt_crossing(belt="rope")
    with pytest.raises(LayoutError):
        joints.belt_crossing(width=0)


def test_a_pipe_crosses_belts_and_its_ends_open_away_from_them():
    lay = joints.pipe_crossing(width=2)
    assert lay.picture(CHARS) == ".p.\n.q.\nbbb\nbbb\n.q.\n.p."
    assert pieces(lay, "open-north")[0]["direction"] == N and pieces(lay, "open-south")[0]["direction"] == S
    north, south = pieces(lay, "open-north")[0], pieces(lay, "open-south")[0]
    assert lay.at(north["x"], north["y"] - 1)["name"] == "pipe" and lay.at(south["x"], south["y"] + 1)["name"] == "pipe"


def test_a_splitter_as_a_filter():
    lay = joints.filter_splitter("copper-plate")
    assert lay.picture(CHARS) == "bb\nSS\n.b"
    s = pieces(lay, "splitter")[0]
    assert (s["w"], s["h"], s["filter"], s["output_priority"]) == (2, 1, "copper-plate", "left")
    assert pieces(lay, "filtered")[0]["x"] == 0 and pieces(lay, "rest")[0]["x"] == 1
    right = joints.filter_splitter("copper-plate", to="right")
    assert pieces(right, "filtered")[0]["x"] == 1 and pieces(right, "splitter")[0]["output_priority"] == "right"
    with pytest.raises(LayoutError, match="'left' or 'right'"):
        joints.filter_splitter("coal", to="up")


def test_left_and_right_stay_true_when_the_joint_is_turned():
    """Left is left as seen along the flow. Facing east, left is north."""
    lay = joints.filter_splitter("copper-plate", to="left").turned(1).at_origin()        # the flow now runs east
    s = pieces(lay, "splitter")[0]
    assert (s["w"], s["h"], s["direction"], s["output_priority"]) == (1, 2, E, "left")
    filtered, rest = pieces(lay, "filtered")[0], pieces(lay, "rest")[0]
    assert filtered["y"] < rest["y"] and filtered["x"] == rest["x"] > s["x"]             # filtered leaves on the north side, east of the splitter


def test_a_mirror_swaps_a_splitters_sides():
    lay = joints.filter_splitter("copper-plate", to="left").mirrored().at_origin()
    assert pieces(lay, "splitter")[0]["output_priority"] == "right"
    assert pieces(lay, "filtered")[0]["x"] > pieces(lay, "rest")[0]["x"]             # the filtered belt is on the right now, and so is the priority


def test_two_belts_into_one_with_one_going_first():
    lay = joints.priority_merge(first="right")
    assert lay.picture(CHARS) == "b.\nSS\nbb"
    s = pieces(lay, "splitter")[0]
    assert s["input_priority"] == "right" and s["output_priority"] == "left" and "filter" not in s


def test_side_loading_fills_one_lane():
    lay = joints.side_load(side="left")
    assert lay.picture(CHARS) == ".b\nbb\n.b"
    feeder, main = pieces(lay, "feeder")[0], pieces(lay, "main")
    assert feeder["direction"] == E and lay.at(feeder["x"] + 1, feeder["y"])["role"] == "main"      # it ends against the main belt's side
    assert all(p["direction"] == N for p in main)
    right = joints.side_load(side="right")
    assert pieces(right, "feeder")[0]["direction"] == W and right.picture(CHARS) == "b.\nbb\nb."


def test_a_lane_each_for_two_items():
    lay = joints.lane_pair()
    assert lay.picture(CHARS) == ".b.\nbbb\n.b."
    assert sorted(p["direction"] for p in pieces(lay, "feeder")) == [E, W]


def test_picking_one_item_off_a_mixed_belt():
    lay = joints.filtered_pick("iron-gear-wheel")
    pick = pieces(lay, "pick")[0]
    assert pick["direction"] == S and pick["filter"] == "iron-gear-wheel" and lay.at(pick["x"], pick["y"] + 1)["role"] == "mixed"


def test_the_row_beside_a_train_wagon():
    lay = joints.wagon_side()
    assert lay.picture(CHARS) == "iiiiii\nCCCCCC\niiiiii\nbbbbbb"
    assert all(p["direction"] == N for p in lay.pieces if p["name"] == "inserter")       # unloading: every hand picks from the north
    load = joints.wagon_side(action="load")
    assert all(p["direction"] == S for p in load.pieces if p["name"] == "inserter")
    two = joints.wagon_side(wagons=2)
    assert two.size() == (13, 4) and two.free(6, 0) and two.count()["inserter"] == 24 and two.count()["transport-belt"] == 13
    with pytest.raises(LayoutError):
        joints.wagon_side(action="wave")


def test_asking_for_a_joint_wrongly_names_the_joints_or_the_options():
    with pytest.raises(LayoutError, match="no joint 'belt_bridge'.*belt_crossing"):
        joints.make("belt_bridge")
    with pytest.raises(LayoutError, match="no option 'colour'.*width"):
        joints.make("belt_crossing", colour="red")
    with pytest.raises(LayoutError, match="needs: item"):
        joints.make("filter_splitter")


# ---------------------------------------------------------------- through the tools and the mod

@pytest.fixture
def world():
    mod = LuaMod()
    return mod, LocalTools(LuaGame(mod), sleep=lambda s: mod.tick(30), patience=2000)


def ok(tools, name, args):
    r = tools.call(name, args)
    assert r["ok"], r
    return r["result"]


def test_the_model_can_read_the_joints_and_plan_one(world):
    mod, tools = world
    cat = ok(tools, "joints", {})
    assert [j["joint"] for j in cat["joints"]][:2] == ["belt_crossing", "pipe_crossing"]
    plan = ok(tools, "plan_joint", {"joint": "belt_crossing", "x": 10, "y": 10})
    assert plan["picture"] == ".b.\n.U.\nbbb\n.U.\n.b." and plan["covers"] == {"from_x": 10, "from_y": 10, "to_x": 12, "to_y": 14}
    assert "cross another without their items mixing" in plan["solves"]


def test_a_filter_splitter_is_built_with_its_filter_and_priority(world):
    mod, tools = world
    plan = ok(tools, "plan_joint", {"joint": "filter_splitter", "x": 0, "y": 20, "item": "iron-plate", "side": "right"})
    assert ok(tools, "build_plan", {"plan_id": plan["plan_id"]})["failed_count"] == 0
    assert ok(tools, "build_plan", {"plan_id": plan["plan_id"], "dry_run": False})["placed"] == 4
    built = "game.surfaces.nauvis.find_entities_filtered{name = 'splitter'}[1]"
    assert mod.lua.eval(built + ".splitter_filter") == "iron-plate" and mod.lua.eval(built + ".splitter_output_priority") == "right"


def test_a_merge_gets_its_input_priority_and_a_pick_gets_its_filter(world):
    mod, tools = world
    plan = ok(tools, "plan_joint", {"joint": "priority_merge", "x": 0, "y": 30, "side": "left"})
    ok(tools, "build_plan", {"plan_id": plan["plan_id"]})
    ok(tools, "build_plan", {"plan_id": plan["plan_id"], "dry_run": False})
    assert mod.lua.eval("game.surfaces.nauvis.find_entities_filtered{name = 'splitter'}[1].splitter_input_priority") == "left"
    plan = ok(tools, "plan_joint", {"joint": "filtered_pick", "x": 10, "y": 30, "item": "copper-cable"})
    ok(tools, "build_plan", {"plan_id": plan["plan_id"]})
    ok(tools, "build_plan", {"plan_id": plan["plan_id"], "dry_run": False})
    ins = "game.surfaces.nauvis.find_entities_filtered{name = 'inserter'}[1]"
    assert mod.lua.eval(ins + ".filters[1]") == "copper-cable" and mod.lua.eval(ins + ".use_filters") is True
    assert mod.lua.eval(ins + ".inserter_filter_mode") == "whitelist"


def test_the_avatar_builds_a_joint_with_its_settings_too(world):
    mod, tools = world
    mod.result("set_mode", {"mode": "my-character"})
    mod.give(splitter=1, transport_belt=3)
    plan = ok(tools, "plan_joint", {"joint": "filter_splitter", "x": 12, "y": 0, "item": "iron-plate"})
    ok(tools, "build_plan", {"plan_id": plan["plan_id"]})
    built = ok(tools, "build_plan", {"plan_id": plan["plan_id"], "dry_run": False})
    assert built["finished"] and built["placed"] == 4
    assert mod.lua.eval("game.surfaces.nauvis.find_entities_filtered{name = 'splitter'}[1].splitter_filter") == "iron-plate"


def test_a_joint_turned_to_face_east_is_planned_where_asked(world):
    mod, tools = world
    plan = ok(tools, "plan_joint", {"joint": "wagon_side", "x": 5, "y": 5, "facing": "east", "action": "load"})
    assert plan["covers"] == {"from_x": 5, "from_y": 5, "to_x": 8, "to_y": 10} and plan["pieces"]["inserter"] == 12
    assert plan["picture"].split("\n")[0] == "biCi"                     # the wagon side is now the east edge


def test_joint_refusals_through_the_tool(world):
    mod, tools = world
    assert "no joint 'bridge'" in tools.call("plan_joint", {"joint": "bridge", "x": 0, "y": 0})["error"]
    assert "no item named 'unobtainium'" in tools.call("plan_joint", {"joint": "filter_splitter", "x": 0, "y": 0, "item": "unobtainium"})["error"]
    assert "needs: item" in tools.call("plan_joint", {"joint": "filter_splitter", "x": 0, "y": 0})["error"]
    assert "facing must be" in tools.call("plan_joint", {"joint": "lane_pair", "x": 0, "y": 0, "facing": "up"})["error"]


def test_a_filter_that_is_not_an_item_is_refused_by_the_game_side_check(world):
    mod, _ = world
    r = mod.result("build", {"entities": [{"name": "splitter", "x": 1, "y": 0.5, "direction": 0, "filter": "unobtainium"}]})
    assert "its filter 'unobtainium' is not an item" in r["failed"][0]["why"]
