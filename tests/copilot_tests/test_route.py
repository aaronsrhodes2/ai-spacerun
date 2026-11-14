import pytest

from copilot.plan import route
from copilot.plan.layout import E, N, S, STEP, W, Layout, opposite
from copilot.plan.route import RouteError


def step(pos, d, n=1):
    return (pos[0] + STEP[d][0] * n, pos[1] + STEP[d][1] * n)


def follow_belt(result, start, goal, blocked=(), max_gap=4):
    """Rides the belt as an item would and returns the tiles visited. Fails if the belt does not carry from start to goal
    by the game's rules."""
    by_tile = {}
    for p in result["pieces"]:
        t = (p["x"], p["y"])
        assert t not in by_tile, "two pieces on tile %s" % (t,)
        assert t not in set(blocked), "a piece stands on a blocked tile %s" % (t,)
        by_tile[t] = p
    pos, seen, came_from = start, [], None
    for _ in range(len(by_tile) + 2):
        assert pos in by_tile, "the belt breaks at %s" % (pos,)
        p = by_tile[pos]
        seen.append(pos)
        if pos == goal:
            break
        if p.get("type") == "input":
            assert came_from is None or came_from == p["direction"], "an underground entrance at %s is fed from the side" % (pos,)
            out = None
            for gap in range(1, max_gap + 1):
                q = by_tile.get(step(pos, p["direction"], gap + 1))
                if q and q.get("type") == "output" and q["direction"] == p["direction"]:
                    out = step(pos, p["direction"], gap + 1)
                    break
                assert step(pos, p["direction"], gap) not in by_tile or by_tile[step(pos, p["direction"], gap)].get("type") != "input"
            assert out, "the underground entrance at %s has no exit within reach" % (pos,)
            came_from, pos = p["direction"], out
        else:
            came_from, pos = p["direction"], step(pos, p["direction"])
    assert seen[-1] == goal, "the belt never reaches the goal"
    assert len(seen) == len(by_tile), "pieces that the belt does not pass through"
    return seen


def test_a_straight_belt():
    r = route.belt((0, 0), (5, 0))
    assert [(p["x"], p["y"], p["direction"]) for p in r["pieces"]] == [(x, 0, E) for x in range(6)]
    assert r["length"] == 6 and r["undergrounds"] == 0
    follow_belt(r, (0, 0), (5, 0))


def test_one_corner_not_a_staircase():
    r = route.belt((0, 0), (4, 3))
    follow_belt(r, (0, 0), (4, 3))
    corners = sum(1 for a, b in zip(r["pieces"], r["pieces"][1:]) if a["direction"] != b["direction"])
    assert r["length"] == 8 and corners == 1


def test_start_equals_goal():
    assert route.belt((2, 2), (2, 2), end_direction=S)["pieces"] == [{"name": "transport-belt", "x": 2, "y": 2, "direction": S}]


def test_the_last_tile_can_be_turned_to_feed_something():
    r = route.belt((0, 0), (3, 0), end_direction=S)
    assert r["pieces"][-1]["direction"] == S and r["pieces"][-2]["direction"] == E


def test_goes_round_a_small_obstacle_when_that_is_shorter_than_nothing():
    blocked = {(2, y) for y in range(-10, 11)} - {(2, 3)}            # a wall with one gap
    r = route.belt((0, 0), (4, 0), blocked, max_gap=0)
    tiles = follow_belt(r, (0, 0), (4, 0), blocked)
    assert (2, 3) in tiles


def test_dives_under_a_wall_it_cannot_go_round():
    blocked = {(2, y) for y in range(-30, 31)}
    r = route.belt((0, 0), (4, 0), blocked)
    follow_belt(r, (0, 0), (4, 0), blocked)
    kinds = [(p["x"], p.get("type")) for p in r["pieces"]]
    assert kinds == [(0, None), (1, "input"), (3, "output"), (4, None)] and r["undergrounds"] == 1 and r["length"] == 5


def test_a_wall_thicker_than_the_underground_reach_stops_the_route():
    blocked = {(x, y) for x in range(2, 8) for y in range(-30, 31)}
    with pytest.raises(RouteError, match="no free way"):
        route.belt((0, 0), (10, 0), blocked, max_gap=4)
    r = route.belt((0, 0), (10, 0), blocked, max_gap=6, underground_name="fast-underground-belt")
    follow_belt(r, (0, 0), (10, 0), blocked, max_gap=6)


def test_an_entrance_is_never_fed_from_the_side():
    # the start is beside the wall: the route must first line up with the dive
    blocked = {(x, 2) for x in range(-30, 31)}
    r = route.belt((0, 1), (0, 4), blocked)
    follow_belt(r, (0, 1), (0, 4), blocked)
    r = route.belt((-3, 1), (0, 4), blocked)
    follow_belt(r, (-3, 1), (0, 4), blocked)


def test_the_tile_after_an_exit_lies_straight_ahead():
    # fenced in before the wall, so the dive has to happen on row 0; the goal lies round a corner right behind the wall
    fence = {(x, y) for x in (0, 1) for y in (1, 2, -1, -2)} | {(-1, 0), (-2, 0)}        # too thick to dive under with reach 1
    blocked = {(2, y) for y in range(-30, 31)} | fence
    r = route.belt((0, 0), (3, 3), blocked, max_gap=1)
    tiles = follow_belt(r, (0, 0), (3, 3), blocked, max_gap=1)
    exit_piece = [p for p in r["pieces"] if p.get("type") == "output"][0]
    assert (exit_piece["x"], exit_piece["y"]) == (3, 0)             # out right behind the wall
    assert tiles[tiles.index((3, 0)) + 1] == (4, 0)                 # one tile straight on before it may turn


def test_a_dive_can_end_on_the_goal():
    blocked = {(2, y) for y in range(-30, 31)}
    r = route.belt((0, 0), (3, 5), blocked)
    follow_belt(r, (0, 0), (3, 5), blocked)
    assert r["pieces"][-1]["type"] == "output"


def test_blocked_ends_and_search_limits_are_reported():
    with pytest.raises(RouteError, match="start tile 0,0 is not free"):
        route.belt((0, 0), (3, 0), {(0, 0)})
    with pytest.raises(RouteError, match="end tile 3,0 is not free"):
        route.belt((0, 0), (3, 0), {(3, 0)})
    ring = {(x, y) for x in range(-2, 3) for y in range(-2, 3)} - {(0, 0)}
    with pytest.raises(RouteError, match="no free way"):
        route.belt((0, 0), (9, 0), ring, max_gap=1)


def test_a_route_stays_inside_its_bounds():
    r = route.belt((0, 0), (6, 0), {(3, 0), (3, 1), (3, -1)}, max_gap=0, bounds=(0, -2, 6, 2))
    assert all(0 <= p["x"] <= 6 and -2 <= p["y"] <= 2 for p in r["pieces"])
    with pytest.raises(RouteError):
        route.belt((0, 0), (6, 0), {(3, 0), (3, 1), (3, -1)}, max_gap=0, bounds=(0, -1, 6, 1))


def test_a_route_does_not_double_back_on_the_belt_it_continues():
    r = route.belt((0, 0), (-3, 0), start_direction=E)
    follow_belt(r, (0, 0), (-3, 0))
    assert r["pieces"][0]["direction"] != W


def test_route_pieces_go_straight_into_a_layout():
    blocked = {(2, y) for y in range(-30, 31)}
    lay = Layout()
    for p in route.belt((0, 0), (5, 2), blocked)["pieces"]:
        extra = {"type": p["type"]} if "type" in p else {}
        lay.put(p["name"], p["x"], p["y"], direction=p["direction"], **extra)
    assert lay.count()["underground-belt"] == 2


def pipes_connect(result, start, goal):
    """True if fluid can get from start to goal: pipes join all four neighbours; a pipe-to-ground joins its open end and
    its partner, the nearest pipe-to-ground behind it facing the other way."""
    by_tile = {(p["x"], p["y"]): p for p in result["pieces"]}
    assert len(by_tile) == len(result["pieces"]), "two pieces on one tile"

    def links(t):
        p = by_tile[t]
        if p["name"] == "pipe":
            cand = [step(t, d) for d in (N, E, S, W)]
        else:
            cand = [step(t, p["direction"])]
            back = opposite(p["direction"])
            for gap in range(1, 12):
                q = by_tile.get(step(t, back, gap))
                if q and q["name"] != "pipe" and q["direction"] == back:
                    cand.append(step(t, back, gap))
                    break
        out = []
        for c in cand:
            q = by_tile.get(c)
            if not q:
                continue
            if q["name"] == "pipe" or step(c, q["direction"]) == t or (p["name"] != "pipe" and q["name"] != "pipe"):
                out.append(c)
        return out
    seen, todo = {start}, [start]
    while todo:
        for n in links(todo.pop()):
            if n not in seen:
                seen.add(n)
                todo.append(n)
    return goal in seen


def test_a_plain_pipe_run():
    r = route.pipe((0, 0), (3, 2))
    assert all(p["name"] == "pipe" for p in r["pieces"]) and r["length"] == 6
    assert pipes_connect(r, (0, 0), (3, 2))


def test_a_pipe_dives_under_a_belt_and_its_ends_open_outward():
    blocked = {(2, y) for y in range(-30, 31)}
    r = route.pipe((0, 0), (4, 0), blocked)
    assert [(p["x"], p["name"], p["direction"]) for p in r["pieces"]] == [
        (0, "pipe", 0), (1, "pipe-to-ground", W), (3, "pipe-to-ground", E), (4, "pipe", 0)]
    assert pipes_connect(r, (0, 0), (4, 0))


def test_a_new_pipe_line_keeps_clear_of_an_old_one():
    old = [(x, 2) for x in range(-5, 12)]                           # an existing pipe line across the way
    avoid = route.beside_pipes(old)
    assert (0, 1) in avoid and (0, 3) in avoid and (0, 2) not in avoid
    r = route.pipe((3, 0), (3, 5), blocked=old, avoid=avoid)
    assert pipes_connect(r, (3, 0), (3, 5))
    plain = {(p["x"], p["y"]) for p in r["pieces"] if p["name"] == "pipe"}
    assert not plain & avoid and r["undergrounds"] == 1
    ends = sorted((p["y"], p["direction"]) for p in r["pieces"] if p["name"] != "pipe")
    assert ends == [(0, N), (4, S)] or ends[0][1] == N and ends[1][1] == S


def test_pipe_refusals():
    with pytest.raises(RouteError):
        route.pipe((0, 0), (5, 0), {(x, y) for x in range(1, 13) for y in range(-30, 31)}, max_gap=9, bounds=(0, -30, 20, 30))
    with pytest.raises(RouteError, match="not free"):
        route.pipe((0, 0), (0, 0), avoid={(0, 0)})
