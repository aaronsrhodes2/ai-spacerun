"""Pins each blueprint to the coordinates of the layout that works in the game."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bridge.factorio import blueprints as bp  # noqa: E402


class BlueprintTests(unittest.TestCase):
    def test_refinery_n_matches_the_working_refinery(self):
        r = bp.refinery_n(-152, -114)
        self.assertEqual(r["entities"][0]["x"], -149.5)
        self.assertEqual(r["entities"][0]["y"], -111.5)
        self.assertEqual(r["crude_in"], [(-151, -109), (-149, -109)])
        self.assertEqual(r["gas_out"], (-148, -115))

    def test_refinery_s_shares_the_crude_row_of_the_one_above_it(self):
        s = bp.refinery_s(-152, -108)
        self.assertEqual(s["crude_in"], bp.refinery_n(-152, -114)["crude_in"])

    def test_plastic_plant_matches_the_working_plant(self):
        p = bp.plastic_plant(-148, -119)
        self.assertEqual((p["entities"][0]["x"], p["entities"][0]["y"]), (-146.5, -117.5))
        self.assertEqual(p["gas_in"], (-148, -116))
        self.assertEqual(p["output_inserter"], (-147, -120))
        self.assertEqual(p["coal_inserter"], (-145, -118))

    def test_sulfur_plant_matches_the_working_plant(self):
        s = bp.sulfur_plant(-168, -119)
        self.assertEqual((s["entities"][0]["x"], s["entities"][0]["y"]), (-166.5, -117.5))
        self.assertEqual(s["water_in"], (-168, -120))
        self.assertEqual(s["gas_in"], (-166, -120))
        self.assertEqual(s["output_inserter"], (-167, -120))


if __name__ == "__main__":
    unittest.main()
