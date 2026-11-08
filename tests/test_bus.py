import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bridge.factorio import bus  # noqa: E402


class BusTests(unittest.TestCase):
    def test_tap_and_trunk_do_not_overlap(self):
        taps = [(1, -100), (0, -99)]
        ents = bus.trunk_entities(taps) + bus.tap(1, -100, 98) + bus.tap(0, -99, 98)
        bus.tiles(ents)

    def test_branch_reaches_the_row_edge_flowing_east(self):
        b = bus.tap(1, -100, 98)
        self.assertTrue(all(e["direction"] == 4 for e in b))
        self.assertEqual(int(b[-1]["x"]), 97)

    def test_undergrounds_pair_and_cross_each_trunk_and_the_riser(self):
        b = bus.tap(2, -100, 98)
        ins = [e for e in b if e.get("params", {}).get("type") == "input"]
        outs = [e for e in b if e.get("params", {}).get("type") == "output"]
        self.assertEqual(len(ins), len(outs))
        self.assertEqual(len(ins), bus.TRUNKS - 1 - 2 + 1)         # later trunks plus the riser
        for i, o in zip(ins, outs):
            self.assertEqual(o["x"] - i["x"], 2)

    def test_coal_riser_reaches_trunk_seven(self):
        ents = bus.trunk_entities()
        tiles = bus.tiles(ents)
        self.assertIn((bus.RISER_X, -100), tiles)
        self.assertIn((bus.trunk_x(7), -141), tiles)

    def test_splitter_rows(self):
        self.assertEqual(bus.splitter_tile(1, -100), (75, -101))


if __name__ == "__main__":
    unittest.main()
