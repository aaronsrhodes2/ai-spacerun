"""The second batch of joints. The balancer is checked by sending a unit of flow down each input belt through a small
model of belts, undergrounds and splitters and seeing that every output gets the same share of every input."""
import pytest

from copilot.plan import joints
from copilot.plan.layout import E, N, S, STEP, W, LayoutError
from copilot.tools import LocalTools
from luamod import LuaMod
from test_bridge_with_mod import LuaGame

CHARS = {"transport-belt": "b", "underground-belt": "U", "splitter": "S", "inserter": "i", "long-handed-inserter": "L", "pipe": "p",
         "pipe-to-ground": "q", "chemical-plant": "M", "assembling-machine-2": "M", "medium-electric-pole": "P",
         "passive-provider-chest": "R", "requester-chest": "B"}
PLANT = [{"flow": "input", "x": -1, "y": -1, "direction": "north"}, {"flow": "input", "x": 1, "y": -1, "direction": "north"},
         {"flow": "output", "x": -1, "y": 1, "direction": "south", "fluid": "water"}, {"flow": "output", "x": 1, "y": 1, "direction": "south"}]


def pieces(lay, role):
    return [p for p in lay.pieces if p.get("role") == role]


def shares(lay):
    """For a layout of belts, underground belts and splitters: {output tile: {input tile: share}}. An input is a belt
    tile nothing feeds; an output is one that feeds nothing. A splitter gives half of what reaches it to each side."""
    tile = {}
    for p in lay.pieces:
        for x in range(p["x"], p["x"] + p["w"]):
            for y in range(p["y"], p["y"] + p["h"]):
                tile[(x, y)] = p

    def ahead(t, d, n=1):
        return (t[0] + STEP[d][0] * n, t[1] + STEP[d][1] * n)

    def targets(t):
        """Where what is on tile t goes next, with the share each gets."""
        p = tile[t]
        d = p["direction"]
        if p["name"].endswith("splitter"):
            halves = [(x, y) for x in range(p["x"], p["x"] + p["w"]) for y in range(p["y"], p["y"] + p["h"])]
            outs = [ahead(h, d) for h in halves if ahead(h, d) in tile]
            return [(o, 1.0 / len(outs)) for o in outs] if outs else []
        if p.get("type") == "input":
            for gap in range(1, 9):
                q = tile.get(ahead(t, d, gap + 1))
                if q and q.get("type") == "output" and q["direction"] == d:
                    return [(ahead(t, d, gap + 1), 1.0)]
            raise AssertionError("an underground entrance at %s has no exit" % (t,))
        nxt = ahead(t, d)
        return [(nxt, 1.0)] if nxt in tile else []

    fed = {t: 0 for t in tile}
    for t in tile:
        for o, _ in targets(t):
            fed[o] += 1
    for p in lay.pieces:                                    # a splitter is fed if either half is
        if p["name"].endswith("splitter"):
            halves = [(x, y) for x in range(p["x"], p["x"] + p["w"]) for y in range(p["y"], p["y"] + p["h"])]
            total = sum(fed[h] for h in halves)
            for h in halves:
                fed[h] = total
    inputs = [t for t in tile if fed[t] == 0]
    result = {}
    for source in inputs:
        flow, todo = {source: 1.0}, [source]
        steps = 0
        while todo:
            steps += 1
            assert steps < 2000, "the flow goes round in a circle"
            t = todo.pop()
            amount = flow.pop(t, 0.0)
            if amount == 0.0:
                continue
            p = tile[t]
            if p["name"].endswith("splitter"):            # what reaches either half is shared from the whole splitter
                halves = [(x, y) for x in range(p["x"], p["x"] + p["w"]) for y in range(p["y"], p["y"] + p["h"])]
                t = halves[0]
            nxt = targets(t)
            if not nxt:
                result.setdefault(t, {})
                result[t][source] = result[t].get(source, 0.0) + amount
                continue
            for o, share in nxt:
                flow[o] = flow.get(o, 0.0) + amount * share
                todo.append(o)
    return result


def test_the_flow_model_itself_on_a_plain_splitter():
    got = shares(joints.tee())
    assert len(got) == 2 and all(list(v.values()) == [0.5] for v in got.values())


def test_a_two_belt_balancer_is_one_splitter():
    lay = joints.balancer(lanes=2)
    assert lay.picture(CHARS) == "bb\nSS\nbb"
    got = shares(lay)
    assert len(got) == 2 and all(sorted(v.values()) == [0.5, 0.5] for v in got.values())


def test_the_four_belt_balancer_gives_every_output_a_quarter_of_every_input():
    lay = joints.balancer()
    assert lay.picture(CHARS) == ".bbbb\n.SSSS\n.UUUb\nbbbbb\nbUUU.\nSSSS.\nbbbb."
    got = shares(lay)
    assert sorted(got) == [(1, 0), (2, 0), (3, 0), (4, 0)]                         # four outputs, side by side
    for out, from_inputs in got.items():
        assert sorted(from_inputs) == [(0, 6), (1, 6), (2, 6), (3, 6)], out        # each hears from all four inputs
        assert all(abs(v - 0.25) < 1e-9 for v in from_inputs.values()), (out, from_inputs)


def test_the_balancer_stays_balanced_when_turned():
    got = shares(joints.balancer().turned(1).at_origin())
    assert len(got) == 4 and all(len(v) == 4 and all(abs(x - 0.25) < 1e-9 for x in v.values()) for v in got.values())


def test_a_wrong_naive_balancer_would_be_caught_by_the_flow_model():
    """Three rows of splitters without the crossing look like a balancer and are not. The model must tell them apart."""
    from copilot.plan.layout import Layout
    lay = Layout()
    for x in range(4):
        lay.put("transport-belt", x, 6, direction=N)
        lay.put("transport-belt", x, 0, direction=N)
    lay.put("splitter", 0, 5, 2, 1, direction=N)
    lay.put("splitter", 2, 5, 2, 1, direction=N)
    for x in (0, 3):
        lay.put("transport-belt", x, 4, direction=N)
        lay.put("transport-belt", x, 3, direction=N)
        lay.put("transport-belt", x, 2, direction=N)
    lay.put("transport-belt", 1, 4, direction=N)
    lay.put("transport-belt", 2, 4, direction=N)
    lay.put("splitter", 1, 3, 2, 1, direction=N)
    lay.put("transport-belt", 1, 2, direction=N)
    lay.put("transport-belt", 2, 2, direction=N)
    lay.put("splitter", 0, 1, 2, 1, direction=N)
    lay.put("splitter", 2, 1, 2, 1, direction=N)
    got = shares(lay)
    assert any(abs(v - 0.25) > 0.01 for out in got.values() for v in out.values())


def test_other_balancer_sizes_are_refused():
    with pytest.raises(LayoutError, match="2 or 4"):
        joints.balancer(lanes=3)


def test_an_overflow_valve_serves_the_main_line_first():
    lay = joints.overflow_valve(keep="right")
    assert lay.picture(CHARS) == "bb\nSS\n.b"
    assert pieces(lay, "splitter")[0]["output_priority"] == "right" and pieces(lay, "main")[0]["x"] == 1 and pieces(lay, "overflow")[0]["x"] == 0
    assert pieces(lay, "in")[0]["x"] == 1                                           # the line comes in under its own side


def test_reaching_over_the_near_belt():
    lay = joints.reach_over("assembling-machine-2", 3, 3)
    assert lay.picture(CHARS) == "bbb\nbbb\n.L.\nMMM\nMMM\nMMM"
    hand = pieces(lay, "reach")[0]
    assert hand["direction"] == N and lay.at(hand["x"], hand["y"] - 2)["role"] == "far" and lay.at(hand["x"], hand["y"] + 2) is None \
        or lay.at(hand["x"], hand["y"] + 1)["role"] == "machine"


def test_belt_ends_and_starts_at_the_robot_network():
    to = joints.belt_to_robots()
    assert [(p["name"], p["y"]) for p in sorted(to.pieces, key=lambda p: p["y"])] == [("passive-provider-chest", 0), ("inserter", 1), ("transport-belt", 2)]
    assert pieces(to, "hand")[0]["direction"] == S and pieces(to, "belt")[0]["direction"] == N
    back = joints.robots_to_belt()
    assert [(p["name"], p["y"]) for p in sorted(back.pieces, key=lambda p: p["y"])] == [("transport-belt", 0), ("inserter", 1), ("requester-chest", 2)]
    assert pieces(back, "hand")[0]["direction"] == S                                # picks up from the chest, drops on the belt


def test_a_long_pipe_is_pairs_end_to_end_whose_open_ends_meet():
    lay = joints.long_pipe(22)
    ends = sorted((p["y"], p["direction"]) for p in lay.pieces)
    assert ends == [(0, N), (1, S), (2, N), (11, S), (12, N), (21, S)]
    assert lay.count() == {"pipe-to-ground": 6}                                     # six pieces for twenty-two tiles
    for (y1, d1), (y2, d2) in zip(ends, ends[1:]):
        if y2 - y1 == 1 and d1 == S and d2 == N:
            continue                                                                # two pairs meeting: open ends face each other
        assert (d1, d2) == (N, S) and y2 - y1 <= 9                                  # one pair: within reach of each other
    assert joints.long_pipe(10).count() == {"pipe-to-ground": 2}
    with pytest.raises(LayoutError, match="one tile over"):
        joints.long_pipe(11)
    with pytest.raises(LayoutError):
        joints.long_pipe(1)


def test_poles_along_a_line_reach_both_ends():
    lay = joints.pole_line(20, spacing=7)
    ys = sorted(p["y"] for p in lay.pieces)
    assert ys == [0, 7, 14, 19] and all(b - a <= 7 for a, b in zip(ys, ys[1:]))
    assert sorted(p["y"] for p in joints.pole_line(15, spacing=7).pieces) == [0, 7, 14]
    assert joints.pole_line(1).count() == {"medium-electric-pole": 1}


def test_pipe_stubs_on_a_machines_fluid_ports():
    lay = joints.machine_ports("chemical-plant", 3, 3, PLANT)
    assert lay.picture(CHARS) == "p.p\nMMM\nMMM\nMMM\np.p"
    assert sorted((p["x"], p["y"], p["role"]) for p in lay.pieces if p["name"] == "pipe") == [(0, -1, "input"), (0, 3, "output"), (2, -1, "input"), (2, 3, "output")]
    assert [p["fluid"] for p in lay.pieces if p["name"] == "pipe" and p["y"] == 3 and p["x"] == 0] == ["water"]


def test_ports_that_make_no_sense_are_refused_rather_than_guessed():
    with pytest.raises(LayoutError, match="no fluid connections"):
        joints.machine_ports("assembling-machine-2", 3, 3, [])
    with pytest.raises(LayoutError, match="lies outside the machine"):
        joints.machine_ports("chemical-plant", 3, 3, [{"flow": "input", "x": -2, "y": -2, "direction": "north"}])
    with pytest.raises(LayoutError, match="points into the machine"):
        joints.machine_ports("chemical-plant", 3, 3, [{"flow": "input", "x": -1, "y": -1, "direction": "south"}])
    with pytest.raises(LayoutError, match="no usable direction"):
        joints.machine_ports("chemical-plant", 3, 3, [{"flow": "input", "x": -1, "y": -1}])


def test_a_machine_on_belts_with_its_pipes_tunnelled_past_them():
    lay = joints.fluid_machine_on_belts("chemical-plant", 3, 3, PLANT, recipe="sulfur")
    assert lay.picture(CHARS) == "q.q\nbbb\nqiq\nMMM\nMMM\nMMM\nqiq\nbbb\nq.q"
    q = sorted((p["x"], p["y"], p["direction"]) for p in lay.pieces if p["name"] == "pipe-to-ground")
    # against the machine the open end faces it; beyond the belt the open end faces away
    assert q == [(0, -1, N), (0, 1, S), (0, 5, N), (0, 7, S), (2, -1, N), (2, 1, S), (2, 5, N), (2, 7, S)]
    assert pieces(lay, "machine")[0]["recipe"] == "sulfur"
    assert [p["x"] for p in pieces(lay, "in")] == [1] and [p["x"] for p in pieces(lay, "out")] == [1]       # inserters where no pipe is
    assert all(p["direction"] == E for p in lay.pieces if p["name"] == "transport-belt")


def test_the_inserter_moves_aside_for_a_port_in_the_middle():
    middle = [{"flow": "input", "x": 0, "y": -1, "direction": "north"}, {"flow": "output", "x": 1, "y": 0, "direction": "east"}]
    lay = joints.fluid_machine_on_belts("assembling-machine-2", 3, 3, middle)
    assert lay.picture(CHARS) == ".q..\nbbb.\niq..\nMMM.\nMMMp\nMMM.\n.i..\nbbb."        # the input inserter moved west of the pipe
    full = [{"flow": "input", "x": x, "y": -1, "direction": "north"} for x in (-1, 0, 1)]
    with pytest.raises(LayoutError, match="no room for an inserter"):
        joints.fluid_machine_on_belts("assembling-machine-2", 3, 3, full)


def test_a_robot_run_machine():
    lay = joints.robot_machine("assembling-machine-2", 3, 3, recipe="repair-pack")
    assert lay.picture(CHARS) == ".B.\n.i.\nMMM\nMMM\nMMM\n.i.\n.R."


def test_rail_signals_are_given_as_rules_not_as_a_layout():
    entry = [j for j in joints.catalogue() if j["joint"] == "rail_signals"][0]
    assert len(entry["rules"]) >= 6 and "rules only" in entry["note"] and any("CHAIN signal before a junction" in r for r in entry["rules"])
    with pytest.raises(LayoutError, match="given as rules, not as a layout.*right-hand side"):
        joints.make("rail_signals")


def test_the_catalogue_has_grown_and_stays_small_per_joint():
    cat = joints.catalogue()
    assert len(cat) == 21 and len({j["joint"] for j in cat}) == 21
    for name in ("balancer", "barrel_station", "machine_ports", "fluid_machine_on_belts", "robot_machine", "overflow_valve", "long_pipe", "pole_line", "rail_signals"):
        assert any(j["joint"] == name for j in cat), name


# ---------------------------------------------------------------- through the tools and the mod

@pytest.fixture
def world():
    mod = LuaMod()
    return mod, LocalTools(LuaGame(mod), sleep=lambda s: mod.tick(30), patience=2000)


def ok(tools, name, args):
    r = tools.call(name, args)
    assert r["ok"], r
    return r["result"]


def test_lookup_reports_fluid_ports_and_leaves_out_what_is_not_a_plain_pipe_connection(world):
    mod, _ = world
    plant = mod.result("lookup", {"name": "chemical-plant", "kind": "entity"})[0]
    assert plant["fluid_ports"] == [
        {"flow": "input", "x": -1, "y": -1, "direction": "north"}, {"flow": "input", "x": 1, "y": -1, "direction": "north"},
        {"flow": "output", "fluid": "water", "x": -1, "y": 1, "direction": "south"}, {"flow": "output", "x": 1, "y": 1, "direction": "south"}]
    assert "fluid_ports" not in mod.result("lookup", {"name": "stone-furnace", "kind": "entity"})[0]


def test_machine_ports_are_read_from_the_game_and_built(world):
    mod, tools = world
    plan = ok(tools, "plan_joint", {"joint": "machine_ports", "x": 10, "y": 10, "machine": "chemical-plant"})
    assert plan["picture"] == "p.p\nMMM\nMMM\nMMM\np.p"
    ok(tools, "build_plan", {"plan_id": plan["plan_id"]})
    assert ok(tools, "build_plan", {"plan_id": plan["plan_id"], "dry_run": False})["placed"] == 5
    assert mod.result("tile", {"x": 10, "y": 10})["things"][0]["name"] == "pipe" and mod.result("tile", {"x": 11, "y": 12})["things"][0]["name"] == "chemical-plant"
    r = tools.call("plan_joint", {"joint": "machine_ports", "x": 0, "y": 0, "machine": "stone-furnace"})
    assert "no fluid connections" in r["error"]
    assert "needs the parameter 'machine'" in tools.call("plan_joint", {"joint": "machine_ports", "x": 0, "y": 0})["error"]


def test_a_pole_line_takes_its_spacing_from_the_poles_own_reach(world):
    mod, tools = world
    plan = ok(tools, "plan_joint", {"joint": "pole_line", "x": 0, "y": 0, "length": 20})
    assert plan["pieces"] == {"medium-electric-pole": 4} and plan["picture"].count("P") == 4       # 7 tiles apart: the pole's supply width
    r = tools.call("plan_joint", {"joint": "pole_line", "x": 0, "y": 0, "length": 40, "spacing": 12})
    assert "out of wire reach" in r["error"] and "reaches 9" in r["error"]
    assert "is not a power pole" in tools.call("plan_joint", {"joint": "pole_line", "x": 0, "y": 0, "length": 9, "pole": "inserter"})["error"]


def test_a_balancer_and_a_long_pipe_through_the_tool(world):
    mod, tools = world
    plan = ok(tools, "plan_joint", {"joint": "balancer", "x": 0, "y": 40, "lanes": 4, "facing": "east"})
    assert plan["covers"] == {"from_x": 0, "from_y": 40, "to_x": 6, "to_y": 44} and plan["pieces"]["splitter"] == 4
    ok(tools, "build_plan", {"plan_id": plan["plan_id"]})
    assert ok(tools, "build_plan", {"plan_id": plan["plan_id"], "dry_run": False})["placed"] == 25
    plan = ok(tools, "plan_joint", {"joint": "long_pipe", "x": 30, "y": 0, "length": 20})
    assert plan["pieces"] == {"pipe-to-ground": 4}


def test_a_reach_over_and_a_robot_machine_read_the_machines_size(world):
    mod, tools = world
    assert ok(tools, "plan_joint", {"joint": "reach_over", "x": 0, "y": 0, "machine": "electromagnetic-plant"})["covers"]["to_x"] == 3
    plan = ok(tools, "plan_joint", {"joint": "robot_machine", "x": 20, "y": 0, "machine": "assembling-machine-2", "item": "iron-gear-wheel"})
    assert plan["pieces"] == {"requester-chest": 1, "inserter": 2, "assembling-machine-2": 1, "passive-provider-chest": 1}
    r = tools.call("plan_joint", {"joint": "robot_machine", "x": 20, "y": 0, "machine": "stone-furnace", "item": "iron-gear-wheel"})
    assert "cannot run the recipe" in r["error"]


def test_a_barrel_station_finds_the_recipe_and_a_machine_that_can_run_it(world):
    mod, tools = world
    mod.run("prototypes.recipe['water-barrel'] = { name = 'water-barrel', energy = 0.2, categories = { chemistry = true }, ingredients = {}, products = {} } "
            "prototypes.recipe['empty-water-barrel'] = { name = 'empty-water-barrel', energy = 0.2, categories = { chemistry = true }, ingredients = {}, products = {} } "
            "for _, n in pairs({ 'water-barrel', 'empty-water-barrel' }) do game.forces.player.recipes[n] = { name = n, enabled = true, ingredients = {}, products = {} } end")
    plan = ok(tools, "plan_joint", {"joint": "barrel_station", "x": 0, "y": 0, "item": "water", "action": "empty"})
    assert plan["picture"] == "q.q\nbbb\nqiq\nMMM\nMMM\nMMM\nqiq\nbbb\nq.q" and "barrels" in plan["solves"]
    plant = [e for e in tools.plans[plan["plan_id"]]["entities"] if e["name"] == "chemical-plant"][0]
    assert plant["recipe"] == "empty-water-barrel"
    fill = ok(tools, "plan_joint", {"joint": "barrel_station", "x": 20, "y": 0, "item": "water"})
    assert [e["recipe"] for e in tools.plans[fill["plan_id"]]["entities"] if e["name"] == "chemical-plant"] == ["water-barrel"]
    assert "no barrel recipe for 'lava'" in tools.call("plan_joint", {"joint": "barrel_station", "x": 0, "y": 0, "item": "lava"})["error"]
    assert "needs 'item'" in tools.call("plan_joint", {"joint": "barrel_station", "x": 0, "y": 0})["error"]
    assert "'fill' or 'empty'" in tools.call("plan_joint", {"joint": "barrel_station", "x": 0, "y": 0, "item": "water", "action": "pour"})["error"]


def test_rail_signal_rules_reach_the_model_through_both_tools(world):
    mod, tools = world
    cat = ok(tools, "joints", {})["joints"]
    assert any(j["joint"] == "rail_signals" and j.get("rules") for j in cat)
    r = tools.call("plan_joint", {"joint": "rail_signals", "x": 0, "y": 0})
    assert not r["ok"] and "given as rules" in r["error"] and "CHAIN signal" in r["error"]
