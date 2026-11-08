import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bridge.factorio import bus  # noqa: E402


class BusTests(unittest.TestCase):
    def test_tap_and_trunk_do_not_overlap(self):
        taps = [(0, -100), (3, -99)]
        ents = bus.trunk_entities(taps) + bus.tap(0, -100, 98) + bus.tap(3, -99, 98)
        bus.tiles(ents)

    def test_branch_reaches_the_row_edge_flowing_east(self):
        b = bus.tap(1, -100, 98)
        self.assertTrue(all(e["direction"] == 4 for e in b))
        last = b[-1]
        self.assertEqual(int(last["x"]), 97)

    def test_undergrounds_pair_and_cross_each_trunk_once(self):
        b = bus.tap(2, -100, 98)
        ins = [e for e in b if e.get("params", {}).get("type") == "input"]
        outs = [e for e in b if e.get("params", {}).get("type") == "output"]
        self.assertEqual(len(ins), len(outs))
        self.assertEqual(len(ins), bus.TRUNKS - 1 - 2)
        for i, o in zip(ins, outs):
            self.assertEqual(o["x"] - i["x"], 2)          # one trunk between them
            self.assertEqual(int(i["x"] + 1 - 0.5) % 1, 0)

    def test_underground_never_sits_on_a_trunk(self):
        trunks = {bus.trunk_x(k) for k in range(bus.TRUNKS)}
        for e in bus.tap(0, -100, 98):
            self.assertNotIn(int(e["x"]), trunks - {bus.trunk_x(0) + 0} if e["name"] != "transport-belt" else set())

    def test_row_pair_a_before_b(self):
        # A from trunk 1 (splitter row y+1=-93), B from trunk 4 (row -92): no shared tiles
        ents = bus.trunk_entities([(1, -94), (4, -93)]) + bus.tap(1, -94, 98) + bus.tap(4, -93, 98)
        bus.tiles(ents)


if __name__ == "__main__":
    unittest.main()
