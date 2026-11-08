import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bridge.factorio.blocks import assembler_row, chain_ok, footprint  # noqa: E402


class RowTests(unittest.TestCase):
    def test_no_overlaps(self):
        footprint(assembler_row(0, 0, "firearm-magazine", 4).entities)

    def test_every_inserter_drops_into_the_machine_or_belt(self):
        b = assembler_row(10, 20, "grenade", 3)
        tiles = footprint(b.entities)
        for e in b.entities:
            if e["name"] in ("inserter", "long-handed-inserter") and e["y"] > 20 + 4:
                reach = 2 if e["name"].startswith("long") else 1
                drop = (int(e["x"]), int(e["y"] - reach))
                self.assertEqual(tiles.get(drop), "assembling-machine-2")
                pick = (int(e["x"]), int(e["y"] + reach))
                self.assertEqual(tiles.get(pick), "transport-belt")
            if e["name"] == "inserter" and e["y"] < 20 + 3:
                self.assertEqual(tiles.get((int(e["x"]), int(e["y"] - 1))), "transport-belt")
                self.assertEqual(tiles.get((int(e["x"]), int(e["y"] + 1))), "assembling-machine-2")

    def test_every_machine_has_pole_in_both_inserter_rows(self):
        b = assembler_row(0, 0, "piercing-rounds-magazine", 5)
        poles = {(int(e["x"]), int(e["y"])) for e in b.entities if e["name"] == "small-electric-pole"}
        for i in range(5):
            self.assertIn((3 * i + 2, 5), poles)
            self.assertIn((3 * i + 2, 1), poles)

    def test_blocks_chain_east_with_aligned_ports(self):
        a = assembler_row(0, 0, "a", 4)
        self.assertTrue(chain_ok(a, assembler_row(12, 0, "b", 2)))
        self.assertFalse(chain_ok(a, assembler_row(13, 0, "b", 2)))
        self.assertFalse(chain_ok(a, assembler_row(12, 1, "b", 2)))


if __name__ == "__main__":
    unittest.main()
