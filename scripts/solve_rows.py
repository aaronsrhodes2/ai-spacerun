"""
Offline solver: place the purple rows on the existing bus (east or west side, any band) without colliding with what is built.
Prints every solution's placements. No game connection.
"""
import itertools
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bridge.factorio import bus, military, westbus  # noqa: E402
from bridge.factorio.blocks import assembler_row  # noqa: E402

X = 98
SIZES = {"assembling-machine-2": (3, 3), "big-electric-pole": (2, 2), "splitter": (2, 1)}


def foot(e):
    w, h = SIZES.get(e["name"], (1, 1))
    x0, y0 = e["x"] - w / 2, e["y"] - h / 2
    return {(int(round(x0)) + i, int(round(y0)) + j) for i in range(w) for j in range(h)}


def tiles(ents):
    out = set()
    for e in ents:
        out |= foot(e)
    return out


def existing():
    ents = []
    plant, taps = military.plant()
    ents += military.dedupe(plant) + [e for k, y in taps for e in bus.tap(k, y, X)]
    trunk_xs = {bus.trunk_x(k) + 0.5 for k in range(bus.TRUNKS)}
    ents += [e for e in bus.trunk_entities(taps) if not (e["name"] == "transport-belt" and e["x"] in trunk_xs)]  # splitters + riser
    # electronics rows
    rows = [("copper-cable", 2, -96, (1, None), 3), ("electronic-circuit", 2, -88, (3, 1), 2), ("advanced-circuit", 6, -80, (3, 2), 0)]
    for recipe, n, y0, (ka, kb), kg in rows:
        ents += assembler_row(X, y0, recipe, n, o_west=True).entities
        ents += bus.tap(ka, y0 + 6, X) + (bus.tap(kb, y0 + 7, X) if kb is not None else []) + bus.give(kg, y0, X - 1)
        for k, y in ((ka, y0 + 6), (kb, y0 + 7)):
            if k is not None:
                ents.append({"name": "splitter", "x": bus.trunk_x(k) + 1.0, "y": y - 0.5, "direction": 8})
    ents += [{"name": "medium-electric-pole", "x": 97.5, "y": -132.5 + 8 * k} for k in range(0, 10)]
    occ = tiles(ents)
    occ |= {(x, -137) for x in range(-200, 78)}               # plastic belt
    occ |= {(x, y) for x in range(60, 100) for y in (-56,)}   # coal feed row
    occ |= {(x, y) for x in range(64, 70) for y in range(-63, -54)}
    occ |= {(x, y) for x in range(72, 76) for y in range(-48, -42)}   # hub stop and the AC pickup
    return occ


def candidate(spec, side, y0):
    recipe, n, (ka, kb), kg, flows_out = spec
    ents = assembler_row(X, y0, recipe, n, o_west=kg is not None).entities
    taps = [(ka, y0 + 6)] + ([(kb, y0 + 7)] if kb is not None else [])
    ents += [e for k, y in taps for e in bus.tap(k, y, X)]
    if kg is not None:
        ents += bus.give(kg, y0, X - 1)
    spl = [{"name": "splitter", "x": bus.trunk_x(k) + 1.0, "y": y - 0.5, "direction": 8} for k, y in taps]
    ents += spl
    ents += [{"name": "medium-electric-pole", "x": 97.5, "y": -132.5 + 8 * k, "direction": 0} for k in range(0, 10)]  # spine (virtual)
    if side == "W":
        ents = westbus.mirror(ents)
    return ents, taps


# recipe, machines, (virtual A trunk, B trunk) per side handled by caller, give trunk
def run():
    occ0 = existing()
    # (name, spec per side) -- real trunk numbers; west specs use virtual numbers = 7 - real
    R = lambda r: 7 - r
    rows = {
        "IS":   dict(recipe="iron-stick", n=1, sides={"E": ((1, None), 4)}),
        "PM":   dict(recipe="productivity-module", n=1, sides={"E": ((2, 0), 6)}),
        "RAIL": dict(recipe="rail", n=2, sides={"W": ((R(0), R(4)), R(6))}),
        "EF":   dict(recipe="electric-furnace", n=1, sides={"W": ((R(0), R(5)), R(5))}),
        "PUR":  dict(recipe="production-science-pack", n=2, sides={"E": ((5, 6), None), "W": ((R(5), R(6)), None)}),
    }
    sols = []
    names = ["IS", "PM", "RAIL", "EF", "PUR"]
    cache = {}
    def cands(nm):
        if nm in cache:
            return cache[nm]
        out = []
        r = rows[nm]
        for side, (ab, kg) in r["sides"].items():
            for y0 in range(-136, -62):
                spec = (r["recipe"], r["n"], ab, kg, None)
                try:
                    ents, taps = candidate(spec, side, y0)
                except Exception:
                    continue
                t = tiles([e for e in ents if not (e["name"] == "medium-electric-pole")])
                give_row = y0 if kg is not None else None
                out.append((side, y0, t, taps, give_row))
        cache[nm] = out
        return out
    def ok_order(nm, y0, side, placed):
        # ordering: items given at row g are usable by taps strictly south of g
        need = {"PM": [(-88,), (-80,)], "EF": [(-80,)]}
        if nm in ("PM", "EF") and y0 + 6 <= -80:
            return False
        if nm == "RAIL" and y0 + 7 <= placed["IS"][1] if "IS" in placed else False:
            return False
        if nm == "PUR":
            for dep in ("PM", "RAIL", "EF"):
                if dep in placed and y0 + 6 <= placed[dep][1]:
                    return False
        return True
    def dfs(i, used, placed):
        if i == len(names):
            sols.append(dict((k, (v[0], v[1])) for k, v in placed.items()))
            return len(sols) >= 5
        nm = names[i]
        for side, y0, t, taps, give_row in cands(nm):
            if t & occ0 or t & used:
                continue
            if not ok_order(nm, y0, side, placed):
                continue
            placed[nm] = (side, y0)
            if dfs(i + 1, used | t, placed):
                return True
            del placed[nm]
        return False
    dfs(0, set(), {})
    return sols


if __name__ == "__main__":
    s = run()
    print(len(s), "solutions")
    for x in s:
        print(x)
