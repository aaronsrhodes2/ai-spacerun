import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bridge.factorio import bus, military  # noqa: E402
from bridge.factorio.blocks import footprint  # noqa: E402


class MilitaryTests(unittest.TestCase):
    def test_plant_has_no_overlaps_with_bus_and_taps(self):
        ents, taps = military.plant()
        ents = military.dedupe(ents)
        footprint([e for e in ents if e["name"] != "transport-belt" or True])
        all_ents = list(ents) + bus.trunk_entities(taps)
        for k, y in taps:
            all_ents += bus.tap(k, y, military.X)
        bus.tiles([e for e in all_ents if e["name"] in ("transport-belt", "splitter", "underground-belt")])

    def test_flipped_grenade_row_outputs_on_the_shared_belt(self):
        ents, _ = military.plant()
        import math
        outs = [e for e in ents if e["name"] == "inserter" and e["direction"] == 0 and math.floor(e["y"]) == military.Y_S - 1]
        self.assertEqual(len(outs), military.GRENADE_MACHINES)   # pick north (machine), drop south onto Y_S

    def test_pack_row_belt_a_is_the_shared_belt(self):
        ents, _ = military.plant()
        row = {int(e["x"]) for e in ents if e["name"] == "transport-belt" and int(e["y"] - 0.5) == military.Y_S}
        sci_x0 = military.X + 16 + 2
        for x in range(military.X, sci_x0 + 3 * military.SCIENCE_MACHINES):
            self.assertIn(x, row)


if __name__ == "__main__":
    unittest.main()
