import pytest

from copilot.plan import cells
from copilot.plan.layout import E, N, S, W, Layout, LayoutError, opposite, turn_right


def test_a_piece_claims_every_tile_it_covers():
    lay = Layout()
    lay.put("assembling-machine-2", 2, 0, 3, 3)
    assert not lay.free(4, 2) and lay.free(5, 0) and lay.at(3, 1)["name"] == "assembling-machine-2"
    assert lay.bounds() == (2, 0, 4, 2) and lay.size() == (3, 3)


def test_an_overlap_names_both_pieces_and_the_tile():
    lay = Layout()
    lay.put("assembling-machine-2", 0, 0, 3, 3)
    with pytest.raises(LayoutError, match=r"'inserter' at 2,2 overlaps 'assembling-machine-2' on tile 2,2"):
        lay.put("inserter", 2, 2)
    assert len(lay.pieces) == 1                               # the refused piece left nothing behind


def test_a_refused_big_piece_claims_no_tiles():
    lay = Layout()
    lay.put("pipe", 2, 0)
    with pytest.raises(LayoutError):
        lay.put("storage-tank", 0, 0, 3, 3)
    assert lay.free(0, 0) and lay.free(1, 1)


def test_bad_sizes_and_directions_are_refused():
    lay = Layout()
    with pytest.raises(LayoutError, match="direction"):
        lay.put("inserter", 0, 0, direction=2)
    with pytest.raises(LayoutError, match="at least one tile"):
        lay.put("x", 0, 0, 0, 1)


def test_entities_are_given_by_their_centre_with_extras():
    lay = Layout()
    lay.put("assembling-machine-2", 0, 0, 3, 3, recipe="iron-gear-wheel")
    lay.put("inserter", 1, 3, direction=N)
    lay.put("splitter", 4, 0, 2, 1, direction=S)
    e = lay.entities()
    assert e[0] == {"name": "assembling-machine-2", "x": 1.5, "y": 1.5, "direction": N, "recipe": "iron-gear-wheel"}
    assert (e[1]["x"], e[1]["y"]) == (1.5, 3.5) and (e[2]["x"], e[2]["y"]) == (5.0, 0.5)


def test_directions_turn():
    assert opposite(N) == S and opposite(E) == W and turn_right(N) == E and turn_right(W) == N and turn_right(N, 2) == S


def test_a_quarter_turn_keeps_shape_and_turns_directions():
    lay = Layout()
    lay.put("splitter", 0, 0, 2, 1, direction=N)              # two wide, facing north
    lay.put("transport-belt", 0, 1, direction=N)              # south of its west half
    t = lay.turned(1).at_origin()
    s = [p for p in t.pieces if p["name"] == "splitter"][0]
    b = [p for p in t.pieces if p["name"] == "transport-belt"][0]
    assert (s["w"], s["h"], s["direction"]) == (1, 2, E)      # now two high, facing east
    assert b["direction"] == E and b["x"] == s["x"] - 1       # what was south of it is now west of it
    assert b["y"] == s["y"]                                   # and beside what was its west half, now its north half


def test_four_quarter_turns_come_back_to_the_start():
    lay = cells.belt_cell("assembling-machine-2", 3, 3)
    assert lay.turned(4).pieces == lay.pieces
    assert lay.turned(1).turned(1).turned(1).turned(1).pieces == lay.pieces
    assert lay.turned(2).turned(2).pieces == lay.pieces


def test_mirror_swaps_east_and_west_only():
    lay = Layout()
    lay.put("transport-belt", 0, 0, direction=E)
    lay.put("transport-belt", 1, 0, direction=N)
    lay.put("assembling-machine-2", 2, 0, 3, 3)
    m = lay.mirrored().at_origin()
    assert [(p["name"], p["x"], p["direction"]) for p in sorted(m.pieces, key=lambda p: p["x"])] == [
        ("assembling-machine-2", 0, N), ("transport-belt", 3, N), ("transport-belt", 4, W)]
    assert lay.mirrored().mirrored().pieces == lay.pieces


def test_add_refuses_overlap_and_moves_pieces():
    a, b = Layout(), Layout()
    a.put("pipe", 0, 0)
    b.put("pipe", 0, 0)
    with pytest.raises(LayoutError):
        a.add(b)
    a.add(b, dx=1)
    assert a.count() == {"pipe": 2} and a.bounds() == (0, 0, 1, 0)


def test_picture_shows_the_layout():
    lay = cells.robot_cell("assembling-machine-3", 3, 3)
    assert lay.picture({"requester-chest": "R", "passive-provider-chest": "P", "inserter": "i", "assembling-machine-3": "M"}) == \
        ".R.\n.i.\nMMM\nMMM\nMMM\n.i.\n.P."


def roles(lay):
    return {p["role"]: p for p in lay.pieces}


def test_belt_cell_shape_for_a_three_by_three_machine():
    lay = cells.belt_cell("assembling-machine-2", 3, 3, recipe="iron-gear-wheel")
    assert lay.picture({"transport-belt": "b", "inserter": "i", "assembling-machine-2": "M"}) == "bbb\n.i.\nMMM\nMMM\nMMM\n.i.\nbbb"
    machine = [p for p in lay.pieces if p["role"] == "machine"][0]
    assert machine["recipe"] == "iron-gear-wheel"
    assert all(p["direction"] == E for p in lay.pieces if p["name"] == "transport-belt")


def test_inserters_stand_between_what_they_serve_and_pick_up_from_the_north():
    for w, h in ((1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (2, 3)):
        lay = cells.belt_cell("machine", w, h)
        machine = [p for p in lay.pieces if p["role"] == "machine"][0]
        for p in lay.pieces:
            if p["role"] in ("in", "out"):
                assert p["direction"] == N
                assert machine["x"] <= p["x"] < machine["x"] + w            # in line with the machine
                north, south = lay.at(p["x"], p["y"] - 1), lay.at(p["x"], p["y"] + 1)
                assert north is not None and south is not None             # something to pick from and to drop into
                assert {north["role"], south["role"]} == ({"input", "machine"} if p["role"] == "in" else {"machine", "output"})


def test_two_input_belts_use_a_long_handed_inserter_that_reaches_the_far_belt():
    lay = cells.belt_cell("assembling-machine-2", 3, 3, two_inputs=True)
    long = [p for p in lay.pieces if p["role"] == "in-2"][0]
    assert long["name"] == "long-handed-inserter" and lay.at(long["x"], long["y"] - 2)["role"] == "input-2"
    assert lay.at(long["x"], long["y"] + 1)["role"] == "machine"
    with pytest.raises(LayoutError):
        cells.belt_cell("small", 1, 1, two_inputs=True)


def test_robot_cell_uses_blue_to_start_and_red_to_end():
    r = roles(cells.robot_cell("assembling-machine-3", 3, 3, recipe="repair-pack"))
    assert r["requests"]["name"] == "requester-chest" and r["stock"]["name"] == "passive-provider-chest"
    assert r["requests"]["y"] < r["machine"]["y"] < r["stock"]["y"] and r["machine"]["recipe"] == "repair-pack"


def test_direct_pair_hands_over_west_to_east():
    lay = cells.direct_pair("furnace", "assembler", 3, 3)
    hand = [p for p in lay.pieces if p["role"] == "hand-over"][0]
    assert hand["direction"] == W                                           # picks up from the west machine
    assert lay.at(hand["x"] - 1, hand["y"])["name"] == "furnace" and lay.at(hand["x"] + 1, hand["y"])["name"] == "assembler"


def test_a_row_joins_the_belts_of_its_cells():
    lay = cells.row(cells.belt_cell("assembling-machine-2", 3, 3), 4)
    assert lay.size() == (12, 7) and lay.count()["assembling-machine-2"] == 4 and lay.count()["transport-belt"] == 24
    assert all(lay.at(x, 0)["role"] == "input" and lay.at(x, 6)["role"] == "output" for x in range(12))


def test_a_row_with_gaps_and_a_bad_count():
    lay = cells.row(cells.robot_cell("assembling-machine-3", 3, 3), 3, gap=1)
    assert lay.size() == (11, 7) and lay.free(3, 2)
    with pytest.raises(LayoutError):
        cells.row(cells.robot_cell("m", 3, 3), 0)


def test_two_rows_face_each_other_and_do_not_overlap():
    cell = cells.belt_cell("assembling-machine-2", 3, 3)
    lay = cells.two_rows(cell, 3, aisle=1)
    assert lay.size() == (9, 15) and lay.count()["assembling-machine-2"] == 6
    assert lay.at(0, 6)["role"] == "output" and lay.at(0, 8)["role"] == "output" and lay.free(0, 7)     # outputs face the aisle
    assert lay.at(0, 0)["role"] == "input" and lay.at(0, 14)["role"] == "input"
    assert lay.at(0, 8)["direction"] == W                                   # the turned row's belts run the other way


def test_no_cell_names_a_recipe_or_a_place_by_itself():
    for lay in (cells.belt_cell("m", 3, 3), cells.robot_cell("m", 3, 3), cells.direct_pair("a", "b", 3, 3)):
        assert all("recipe" not in p for p in lay.pieces)
        assert lay.bounds()[:2] == (0, 0)
