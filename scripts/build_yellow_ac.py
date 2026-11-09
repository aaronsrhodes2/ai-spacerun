"""
Advanced circuits for the yellow block, same problem and fix as build_yellow_ec.py: the AC row (y0=-80) gives onto trunk 0 BELOW the
yellow taps. West tap on trunk 0 at y=-70, filtered splitter, belt north along x=64 (under the EC branch and the iron tap extension),
side-loading onto the south (AC) lane of S2 at (64,-109).
Usage: scripts/build_yellow_ac.py [--build]
"""
import json
import sys

from _game import tools

from bridge.factorio import bus, westbus
from bridge.factorio.planner import batches

X = 98
R = westbus.real_k
TAP = (R(0), -70)
Y = -70
N, E, S, W = 0, 4, 8, 12


def belt(x, y, d):
    return {"name": "transport-belt", "x": x + 0.5, "y": y + 0.5, "direction": d}


def ug(x, y, d, kind):
    return {"name": "underground-belt", "x": x + 0.5, "y": y + 0.5, "direction": d, "params": {"type": kind}}


def route():
    e = [belt(67, Y, W)]
    e.append({"name": "splitter", "x": 66.5, "y": Y + 1.0, "direction": W})   # rows -70 (north, right) and -69 (south, left)
    e.append(belt(65, Y, W))                                                   # AC output
    e.append(belt(65, Y + 1, W))                                               # steel stub (the non-AC output)
    e += [belt(64, y, N) for y in range(Y, -84, -1)]                           # -70 .. -83
    e.append(ug(64, -84, N, "input"))
    e.append(ug(64, -88, N, "output"))                                         # under the EC branch on row -86
    e += [belt(64, y, N) for y in range(-89, -105, -1)]                        # -89 .. -104
    e.append(ug(64, -105, N, "input"))
    e.append(ug(64, -107, N, "output"))                                        # under the iron tap extension on row -106
    e.append(belt(64, -108, N))                                                # side-loads onto S2's south (AC) lane at (64,-109)
    return e


def plan():
    k, y = TAP
    taps = bus.tap(k, y, X)
    split = [e for e in bus.trunk_entities([TAP]) if e["name"] == "splitter"]
    return westbus.mirror(taps) + route(), westbus.mirror(split)


def main():
    ents, bus_split = plan()
    counts = {}
    for e in ents + bus_split:
        counts[e["name"]] = counts.get(e["name"], 0) + 1
    print(counts)
    for part in batches(ents):
        r = json.loads(tools["place_entities"](json.dumps(part), dry_run=True))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"dry run failed: {json.dumps(r)[:2500]}")
    print("dry run clean")
    if "--build" not in sys.argv:
        return
    print(tools["save_game"]("before-yellow-ac"))
    kv, y = TAP
    x, ty = westbus.real_splitter_tile(kv, y)
    tools["remove_entities"](x + 0.2, ty + 0.2, x + 0.8, ty + 0.8, names="transport-belt")
    for part in batches(ents + bus_split):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"stopped: {json.dumps(r)[:2500]}")
        print("placed", r["placed"])
    print(tools["run_lua"](
        "local sp=game.surfaces.nauvis.find_entities_filtered{name='splitter',position={66.5,%f},radius=0.5}[1] "
        "sp.splitter_filter={name='advanced-circuit'} sp.splitter_output_priority='right' "
        "rcon.print(sp.splitter_filter.name..' '..sp.splitter_output_priority)" % (Y + 1.0)))


if __name__ == "__main__":
    main()
