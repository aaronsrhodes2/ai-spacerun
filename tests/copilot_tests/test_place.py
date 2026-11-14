import pytest

from copilot.plan import place
from copilot.plan.place import PlaceError


@pytest.mark.parametrize("words, cell", [
    ("middle", (1, 1)), ("the centre", (1, 1)), ("center", (1, 1)),
    ("north", (1, 0)), ("top", (1, 0)), ("south", (1, 2)), ("bottom", (1, 2)), ("east", (2, 1)), ("left", (0, 1)), ("the east side", (2, 1)),
    ("upper right", (2, 0)), ("upper right corner", (2, 0)), ("top-left", (0, 0)), ("lower left", (0, 2)), ("bottom right", (2, 2)),
    ("north-east", (2, 0)), ("northeast", (2, 0)), ("south west", (0, 2)), ("southwest", (0, 2)), ("North East", (2, 0)),
    ("the upper right corner of", (2, 0)), ("in the east", (2, 1)), ("middle of the top", (1, 0)), ("top middle", (1, 0)),
])
def test_ways_of_saying_a_part(words, cell):
    assert place.part_of(words) == cell


def test_unknown_words_are_refused_with_the_choices():
    with pytest.raises(PlaceError, match="not a part I know"):
        place.part_of("over yonder")
    with pytest.raises(PlaceError, match="say which part"):
        place.part_of("the side of")
    with pytest.raises(PlaceError, match="not a part I know"):
        place.part_of("northish")


def test_the_nine_cells_tile_the_rectangle_exactly():
    for rect in ((0, 0, 8, 8), (-50, -20, 49, 39), (3, 3, 13, 9), (0, 0, 2, 2), (10, 10, 20, 12)):
        seen = {}
        for col in range(3):
            for row in range(3):
                x0, y0, x1, y1 = place.cut(rect, col, row)
                assert rect[0] <= x0 <= x1 <= rect[2] and rect[1] <= y0 <= y1 <= rect[3]
                for x in range(x0, x1 + 1):
                    for y in range(y0, y1 + 1):
                        assert (x, y) not in seen, "tile %s in two cells of %s" % ((x, y), rect)
                        seen[(x, y)] = (col, row)
        assert len(seen) == (rect[2] - rect[0] + 1) * (rect[3] - rect[1] + 1)


def test_cells_are_where_their_names_say():
    rect = (0, 0, 89, 59)
    assert place.cut(rect, 0, 0) == (0, 0, 29, 19) and place.cut(rect, 2, 0) == (60, 0, 89, 19)
    assert place.cut(rect, 1, 1) == (30, 20, 59, 39) and place.cut(rect, 2, 2) == (60, 40, 89, 59)


def test_a_frame_too_small_to_cut_is_used_whole():
    assert place.cut((5, 5, 6, 5), 2, 0) == (5, 5, 6, 5)
    with pytest.raises(PlaceError, match="empty"):
        place.cut((5, 5, 4, 5), 1, 1)


FRAMES = {"view": (-40, -22, 39, 22), "base": (-300, -200, 299, 199), "map": (-1000, -1000, 999, 999), "player": place.around(12, -7, 15)}


def test_the_middle_of_the_screen_is_where_the_view_is_centred():
    r = place.locate(FRAMES, "view", "middle")
    assert (r["centre_x"], r["centre_y"]) == (-1, 0) or abs(r["centre_x"]) <= 1 and abs(r["centre_y"]) <= 1


def test_the_east_of_the_base_and_the_upper_right_of_the_view():
    east = place.locate(FRAMES, "base", "east")
    assert east["from_x"] == 100 and east["to_x"] == 299 and east["from_y"] < 0 < east["to_y"]
    corner = place.locate(FRAMES, "view", "upper right corner")
    assert corner["to_x"] == 39 and corner["from_y"] == -22 and corner["centre_x"] > 0 > corner["centre_y"]


def test_around_the_player():
    r = place.locate(FRAMES, "player", "middle")
    assert (r["centre_x"], r["centre_y"]) == (12, -7)


def test_locate_refusals():
    with pytest.raises(PlaceError, match="frame must be one of"):
        place.locate(FRAMES, "screen", "middle")
    with pytest.raises(PlaceError, match="no rectangle"):
        place.locate({"view": None}, "view", "middle")


def test_the_ring_round_the_map_surrounds_it_without_overlap():
    rect = (-10, -5, 9, 4)
    strips = place.ring(rect, 3)
    tiles = set()
    for x0, y0, x1, y1 in strips:
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                assert (x, y) not in tiles
                assert not (rect[0] <= x <= rect[2] and rect[1] <= y <= rect[3])
                tiles.add((x, y))
    assert len(tiles) == (20 + 6) * (10 + 6) - 20 * 10
