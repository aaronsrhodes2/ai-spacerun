# Edgerunner 2: stage 1, the layout on paper (2026-11-21)

Approved plan: the inverted triangle (flat front toward the flight), railgun doctrine, fusion plus a large accumulator bank, edge leg
at 10 km/s, blueprint before every risky step. `scripts/edge2_design.py plan | map | arcs | json` is the layout; nothing is placed yet.

## Numbers behind it (read from the prototypes)
One railgun round does 38,000 (10,000 x 3.8): it kills a medium, big or huge asteroid in one shot. Huge asteroids resist explosions
99%, bullets do nothing to big or huge, so rockets and guns cannot answer the edge; only railguns can. The old ship's railguns were
limited to huge only and too few bore on its pointed nose; it was lost on 2026-11-21 with no blueprint.

## Layout (tiles, flight toward y = 0)
- Hull: 160 wide at the flat front, 120 deep to the apex, 9,600 deck tiles = 9,600 foundation = 192 rocket launches.
- Front line: 53 railguns side by side on the face (3 wide each), feed inserters and one rounds belt behind them. Nothing of ours stands
  in front of the face, so no shot line crosses our own parts.
- Sides: 15 railguns facing straight out from the slanted edges (south-west and south-east), 16 gun turrets between. First tried facing
  north-west: that fouled 10 shot lines (the ears near the face aimed across the front line); turned outward, 0 are fouled.
- Apex: 1 railgun and 2 guns to the rear. Total railguns 68.
- Inside, front to rear: rounds works both sides of a 3-wide spine, hub, cargo bays and smelting, tanks, fusion block, accumulator bank
  (320 legendary), 8 thrusters. All blocks lie on the hull without overlap (`fit` check); a first depth of 90 left the rear too narrow
  and was deepened to 120.
- Power: 68 railguns firing at once draw about 265 MW; fusion 4 reactors and 8 generators give 500 MW; the bank carries a full volley for
  about 34 s if the plant trips.
- Rounds: a kill is a round. Reserve 30,000 carried; on-board works are a supplement because asteroid chunks give only a few rounds a
  minute of steel and explosives. This is the honest limit of "make rounds on the ship".

## Still to settle before stage 2
- Foundation: 192 rocket launches from Nauvis (Nauvis holds about 385,000 foundation).
- The rounds works recipe chain and its chunk supply; where the 30,000 reserve rounds come from (Nauvis makes railgun ammunition).
- Whether the final flat front should carry a sacrificial deck strip ahead of the railguns.
