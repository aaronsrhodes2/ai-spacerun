"""Run with: .venv/Scripts/python.exe -m unittest discover tests
These use the rail catalog captured from the game (snapshots/rail-catalog.json)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bridge.factorio import rails  # noqa: E402


class RailTests(unittest.TestCase):
    def test_catalog_has_every_piece_in_every_direction(self):
        self.assertEqual(len(rails.catalog()), 24)

    def test_straight_continues_north(self):
        name, pdir, pos, new = rails.straight((301, 0, 0))
        self.assertEqual((name, new), ("straight-rail", (301, -2, 0)))

    def test_pieces_connect_end_to_end(self):
        pieces, end = rails.route((301, 0, 0), [("E", -31, 20)])
        cur = (301, 0, 0)
        for name, pdir, pos in pieces:
            ok = [c for c in rails.continuations(cur) if c[0] == name and c[1] == pdir and c[2] == pos]
            self.assertTrue(ok, f"{name} {pdir} at {pos} doesn't join {cur}")
            cur = ok[0][3]
        self.assertEqual(cur, end)

    def test_turn_lands_on_the_requested_line(self):
        pieces, end = rails.route((145, 72, 0), [("W", 21), ("N", 71, -54)])
        self.assertEqual(end[2], 0)
        self.assertEqual(end[0], 71)
        self.assertLessEqual(end[1], -54)

    def test_wrong_parity_is_refused(self):
        with self.assertRaises(ValueError):
            rails.route((145, 72, 0), [("W", 22)])

    def test_line_behind_the_track_is_refused(self):
        with self.assertRaises(ValueError):
            rails.route((145, 72, 0), [("W", 80)])

    def test_turns_use_only_curves(self):
        pieces, _ = rails.route((145, 72, 0), [("W", 21)])
        self.assertEqual({p[0] for p in pieces} - {"straight-rail"}, {"curved-rail-a", "curved-rail-b"})


if __name__ == "__main__":
    unittest.main()
