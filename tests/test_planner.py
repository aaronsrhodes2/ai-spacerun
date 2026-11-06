"""Run with: .venv/Scripts/python.exe -m unittest discover tests"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bridge.factorio.planner import E, N, S, W, Grid, Plan, PlanError, batches  # noqa: E402


def make_plan(rows):
    return Plan(Grid({"x1": 0, "y1": 0, "rows": rows}))


def belt_at(plan, x, y):
    for e in plan.entities:
        if e["name"] == "transport-belt" and e["x"] == x + 0.5 and e["y"] == y + 0.5:
            return e
    return None


class RouteTests(unittest.TestCase):
    def test_straight_route_points_at_each_next_tile(self):
        plan = make_plan(["....."])
        path = plan.route((0, 0), E, (4, 0), E)
        self.assertEqual(len(path), 5)
        self.assertTrue(all(e["direction"] == E for e in plan.entities))

    def test_corner_directions_follow_the_path(self):
        plan = make_plan([".....", ".....", "....."])
        path = plan.route((0, 0), E, (2, 2), S)
        for a, b in zip(path, path[1:]):
            d = belt_at(plan, *a)["direction"]
            self.assertEqual((a[0] + {E: 1, W: -1}.get(d, 0), a[1] + {S: 1, N: -1}.get(d, 0)), b)

    def test_goes_around_water_and_cliffs(self):
        plan = make_plan([".....", ".~K~.", "....."])
        path = plan.route((2, 0), E, (2, 2), S)
        self.assertNotIn((2, 1), path)
        self.assertEqual(path[-1], (2, 2))

    def test_never_crosses_an_existing_belt(self):
        plan = make_plan(["....."] * 5)
        plan.line((2, 0), (2, 4))
        with self.assertRaises(PlanError):
            plan.route((0, 2), E, (4, 2), E)

    def test_detours_around_an_existing_belt_when_it_can(self):
        plan = make_plan(["....."] * 5)
        plan.line((2, 1), (2, 4))
        path = plan.route((0, 2), E, (4, 2), E)
        self.assertTrue(all(t[0] != 2 or t[1] == 0 for t in path))

    def test_prefers_going_round_a_rock_but_can_cross_trees(self):
        plan = make_plan(["TTT"])
        self.assertEqual(len(plan.route((0, 0), E, (2, 0), E)), 3)

    def test_does_not_arrive_head_on(self):
        plan = make_plan([".....", "....."])
        path = plan.route((0, 0), E, (3, 0), W)
        self.assertNotEqual(path[-2], (2, 0))


class PlacementTests(unittest.TestCase):
    def test_drill_refuses_mixed_ore(self):
        plan = make_plan(["kk", "ks"])
        with self.assertRaises(PlanError):
            plan.drill(0, 0, N, "k")

    def test_drill_position_is_center_of_its_tiles(self):
        plan = make_plan(["kk", "kk"])
        plan.drill(0, 0, N, "k")
        self.assertEqual((plan.entities[0]["x"], plan.entities[0]["y"]), (1, 1))

    def test_machine_position_is_center_of_its_tiles(self):
        plan = make_plan(["...", "...", "..."])
        plan.machine("assembling-machine-1", 0, 0, 3, 3, recipe="iron-gear-wheel")
        e = plan.entities[0]
        self.assertEqual((e["x"], e["y"], e["recipe"]), (1.5, 1.5, "iron-gear-wheel"))

    def test_overlap_is_refused(self):
        plan = make_plan(["kk", "kk"])
        plan.belt(0, 0, E)
        with self.assertRaises(PlanError):
            plan.drill(0, 0, N, "k")

    def test_line_keeps_requested_last_direction(self):
        plan = make_plan(["...."])
        plan.line((0, 0), (3, 0), last_direction=S)
        self.assertEqual(belt_at(plan, 3, 0)["direction"], S)
        self.assertEqual(belt_at(plan, 2, 0)["direction"], E)

    def test_diagonal_line_is_refused(self):
        with self.assertRaises(PlanError):
            make_plan(["..", ".."]).line((0, 0), (1, 1))

    def test_batches_keep_everything(self):
        self.assertEqual(sum(len(b) for b in batches(list(range(1001)))), 1001)
        self.assertEqual(max(len(b) for b in batches(list(range(1001)))), 400)


if __name__ == "__main__":
    unittest.main()
