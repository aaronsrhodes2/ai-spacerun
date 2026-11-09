"""
Electronic circuits for the yellow block. The EC row (east, y0=-88) puts EC on trunk 2 at y=-88, and trunk 2 flows SOUTH, so the
yellow block's tap at y=-117 never saw any. This adds a west tap on trunk 2 at y=-86 (below the give), sorts EC out with a filtered
splitter, and carries it north along x=62 (under the iron feeder rows -109..-106) and west along y=-112 into the S1 feeder at (57,-112).
Usage: scripts/build_yellow_ec.py [--build]
"""
import json
import sys

from _game import tools

from bridge.factorio import bus, westbus
from bridge.factorio.planner import batches

X = 98
R = westbus.real_k
TAP = (R(2), -86)
Y = -86
N, E, S, W = 0, 4, 8, 12


def belt(x, y, d):
    return {"name": "transport-belt", "x": x + 0.5, "y": y + 0.5, "direction": d}


def ug(x, y, d, kind):
    return {"name": "underground-belt", "x": x + 0.5, "y": y + 0.5, "direction": d, "params": {"type": kind}}


def route():
    e = [belt(x, Y, W) for x in (67, 66, 65, 64)]
    e.append({"name": "splitter", "x": 63.5, "y": Y + 1.0, "direction": W})   # rows -86 (north, right) and -85 (south, left)
    e.append(belt(62, Y, N))                                                   # EC output turns north
    e.append(belt(62, Y + 1, W))                                               # plastic stub (the non-EC output)
    e += [belt(62, y, N) for y in range(Y - 1, -105, -1)]                      # -87 .. -104
    e.append(ug(62, -105, N, "input"))
    e.append(ug(62, -110, N, "output"))                                        # under the iron feeder rows -109..-106
    e += [belt(62, -111, N), belt(62, -112, W)]
    e += [belt(x, -112, W) for x in range(61, 57, -1)]                         # 61..58, side-loads into the S1 feeder at (57,-112)
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
    print(tools["save_game"]("before-yellow-ec"))
    kv, y = TAP
    x, ty = westbus.real_splitter_tile(kv, y)
    tools["remove_entities"](x + 0.2, ty + 0.2, x + 0.8, ty + 0.8, names="transport-belt")
    for part in batches(ents + bus_split):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"stopped: {json.dumps(r)[:2500]}")
        print("placed", r["placed"])
    print(tools["run_lua"](
        "local sp=game.surfaces.nauvis.find_entities_filtered{name='splitter',position={63.5,%f},radius=0.5}[1] "
        "sp.splitter_filter={name='electronic-circuit'} sp.splitter_output_priority='right' "
        "rcon.print(sp.splitter_filter.name..' '..sp.splitter_output_priority)" % (Y + 1.0)))


if __name__ == "__main__":
    main()
