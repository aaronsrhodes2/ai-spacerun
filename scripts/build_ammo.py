#!/usr/bin/env python3
"""Explosive-rocket line on Nauvis, the rocket turrets' ammunition for the Fulgora-Aquilo shuttles (the Captain, 2026-11-14: "build everything
to make the rockets ... supply the far planet shuttles"). Three drone-fed cells (scripts/build_cells.py pattern) side by side, on the free strip
south of the water tank at (-287.5,-72.5):

    explosives   (x -294)  coal + sulfur, water by pipe from the tank outlet at (-287,-71)
    rocket       (x -302)  2 iron plate + 1 explosives -> rocket
    explosive    (x -310)  2 explosives + 1 rocket -> explosive rocket (the stronger round for big asteroids)

Each cell's passive chest offers its product to the logistic network; the next cell's requester chest asks for it.
Explosives run only in a chemical plant (the chemistry category) and need 10 water per craft. Water comes from the existing network: a 113-pipe run from the full pipe at (-401,-76) along row -76, up column -326 to row -80, along row -80 to x -298, down column -298 to (-298,-74), joining the pipes at (-299..-301, -74..-76) and the chain at row -71 into the plant. The tank's own outlet is an underground pair that does not connect to the chain.
Usage: build_ammo.py [--apply]     (dry run without --apply)"""
import argparse
import json

import build_cells as B
from _game import tools

B.KINDS.update({
    "explosives": {"machine": "chemical-plant", "recipe": "explosives", "req": [("coal", 2000), ("sulfur", 2000)]},
    "rocketc": {"machine": "assembling-machine-3", "recipe": "rocket", "req": [("iron-plate", 2000), ("explosives", 1000)]},
    "xrocket": {"machine": "assembling-machine-3", "recipe": "explosive-rocket", "req": [("rocket", 1000), ("explosives", 2000)]},
})
B.GROUPS.update({"explosives": "Feed: Explosives", "rocketc": "Feed: Rocket", "xrocket": "Feed: Explosive Rocket"})

CELLS = [("explosives", -294), ("rocketc", -302), ("xrocket", -310)]   # (kind, x0), all at y0 = -70 (rows -70..-68)
Y0 = -70
PIPES = [(-288, -71), (-289, -71), (-290, -71), (-291, -71)]         # from the existing tank outlet pipe at (-287,-71) to the explosives machine


def pipe_ents():
    return [{"name": "pipe", "x": x + .5, "y": y + .5} for x, y in PIPES]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    ents = []
    for kind, x0 in CELLS:
        ents += B.plan(kind, x0, Y0, 1)
    ents += pipe_ents()
    if not a.apply:
        res = json.loads(tools["place_entities"](json.dumps(ents), surface="nauvis", dry_run=True))
        print("dry run:", {k: v for k, v in res.items() if k in ("failed", "placed")})
        print(json.dumps(res, indent=1)[:1500])
        return
    for kind, x0 in CELLS:
        print(kind, B.clear_box(x0, Y0, 1, False, "nauvis"))
    for part in B.batches(ents):
        r = json.loads(tools["place_entities"](json.dumps(part), surface="nauvis"))
        print("placed", r.get("placed"), "failed", r.get("failed"))
    for kind, x0 in CELLS:
        print(kind, B.configure(kind, x0, Y0, 1, "nauvis"))


if __name__ == "__main__":
    main()
