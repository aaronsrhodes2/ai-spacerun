"""
Solar farm in free ground southwest of the base: 12x12 solar panels (cells of 3x3 on a 4-tile pitch),
medium poles on every second gap junction (each covers its four panels, 8 tiles apart), a row of
accumulators below, and a pole link to the science block's pole at (-121,-58).

    field   x -148..-101, y -36..11     (144 panels, 8.6 MW peak, about 6 MW average)
    link    medium poles at (-121.5,-51.5), (-121.5,-43.5), (-121.5,-37.5) then the field

Usage: scripts/build_solar.py [--build]
"""
import json
import sys

from _game import tools

from bridge.factorio.planner import batches

X0, Y0, CELLS = -148, -36, 12


def entities():
    ents = []
    for a in range(CELLS):
        for b in range(CELLS):
            ents.append({"name": "solar-panel", "x": X0 + 4 * a + 1.5, "y": Y0 + 4 * b + 1.5, "direction": 0})
    for a in range(0, CELLS, 2):
        for b in range(0, CELLS, 2):
            ents.append({"name": "medium-electric-pole", "x": X0 + 4 * a + 3.5, "y": Y0 + 4 * b + 3.5})
    ya = Y0 + 4 * CELLS + 1                              # accumulator row, two tiles tall
    for i in range(CELLS * 2):
        ents.append({"name": "accumulator", "x": X0 + 2 * i + 1.0, "y": ya + 1.0, "direction": 0})
    for a in range(0, CELLS, 2):
        ents.append({"name": "medium-electric-pole", "x": X0 + 4 * a + 3.5, "y": ya + 2.5})
    for y in (-51.5, -43.5, -37.5):
        ents.append({"name": "medium-electric-pole", "x": -121.5, "y": y})
    return ents


def main():
    build = "--build" in sys.argv
    ents = entities()
    counts = {}
    for e in ents:
        counts[e["name"]] = counts.get(e["name"], 0) + 1
    print(counts)
    if build:
        n = tools["run_lua"]("local n=0 for _,e in pairs(game.surfaces.nauvis.find_entities_filtered{area={{-150,-38},{-98,16}},type='simple-entity'}) do e.destroy() n=n+1 end rcon.print(n)")
        print("rocks removed:", n)
    for part in batches(ents):
        r = json.loads(tools["place_entities"](json.dumps(part), dry_run=not build))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"failed: {json.dumps(r)[:1500]}")
        print("placed" if build else "dry ok", r["placed"])


if __name__ == "__main__":
    main()
