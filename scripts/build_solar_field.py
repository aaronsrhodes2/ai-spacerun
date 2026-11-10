"""
Solar field that fits itself into the substation lattice (a substation every 16 tiles covers all land, so every free tile is already powered).

Two boxes: one is filled with solar panels on a 3-tile pitch, the other with accumulators on a 2-tile pitch. A slot is used only where the game
says the piece fits, so the lattice substations, roboports and their kits, water and anything else already standing are left alone.
Ratio to aim for: 0.84 accumulators per panel (a panel averages 42 kW over the day, 60 kW at noon; an accumulator holds 5 MJ).

Without --apply the script only counts the free slots (trees and rocks still stand then, so the count is a lower bound).
With --apply it removes trees, rocks and cliffs in the boxes, then places through place_entities (research gate applies).

Usage: scripts/build_solar_field.py --panels X0 Y0 X1 Y1 [--panels ...] [--accus X0 Y0 X1 Y1 ...] [--apply]
"""
import argparse
import json

import fx
from _game import tools

from bridge.factorio.planner import batches

STEP = 96  # scan box edge, keeps each reply small


def _result(out):
    d = json.loads(out)
    return json.loads(d["result"]) if isinstance(d, dict) and "result" in d else d


def clear(box):
    x0, y0, x1, y1 = box
    return fx.lua(
        f"local s=game.surfaces.nauvis local t=0 for _,e in pairs(s.find_entities_filtered{{area={{{{{x0},{y0}}},{{{x1},{y1}}}}},"
        "type={'tree','cliff','simple-entity','item-entity','corpse'}}) do if e.force.name~='player' then e.destroy() t=t+1 end end rcon.print(t)")


def scan(name, size, box):
    """Free slots of `size` tiles on the global size-pitch grid inside the box, as centre positions."""
    x0, y0, x1, y1 = box
    x0, y0 = -(-x0 // size) * size, -(-y0 // size) * size
    out = []
    for bx in range(x0, x1, STEP - STEP % size):
        for by in range(y0, y1, STEP - STEP % size):
            ex, ey = min(bx + STEP - STEP % size, x1), min(by + STEP - STEP % size, y1)
            r = _result(fx.lua(
                f"local s=game.surfaces.nauvis local f=game.forces.player local o={{}} for x={bx},{ex - size},{size} do for y={by},{ey - size},{size} do "
                f"local p={{x+{size / 2},y+{size / 2}}} if s.can_place_entity{{name='{name}',position=p,force=f,build_check_type=defines.build_check_type.manual}} "
                "then o[#o+1]=p end end end if #o==0 then rcon.print('[]') else rcon.print(helpers.table_to_json(o)) end"))
            out += [{"name": name, "x": p[0], "y": p[1]} for p in r]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--panels", nargs=4, type=int, action="append", default=[])
    ap.add_argument("--accus", nargs=4, type=int, action="append", default=[])
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    total = {}
    for name, size, boxes in (("solar-panel", 3, a.panels), ("accumulator", 2, a.accus)):
        for box in boxes:
            if a.apply:
                print("cleared", clear(box))
            ents = scan(name, size, box)
            total[name] = total.get(name, 0) + len(ents)
            print(name, box, "free slots", len(ents))
            if not a.apply:
                continue
            placed = failed = 0
            for part in batches(ents):
                r = json.loads(tools["place_entities"](json.dumps(part)))
                placed += len(r["placed"]) if isinstance(r.get("placed"), list) else (r.get("placed") or 0)
                fl = r.get("failed") or []
                failed += len(fl) if isinstance(fl, list) else fl
                if fl and isinstance(fl, list):
                    print("  failed sample:", json.dumps(fl[:3]))
            print("  placed", placed, "failed", failed)
    print("totals", total)


if __name__ == "__main__":
    main()
