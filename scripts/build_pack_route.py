"""
Military science packs from the east base to the research train's intake.

The packs leave the plant on the belt at y=-126 (flowing east, ends x=127). The route:
    east to x=130, south down x=130 to y=-25, west along y=-25 to x=-100, north up x=-100 to y=-52, where the last tile
    side-loads onto the fast belt (y=-53.5) that carries red/green packs west to the "Sandro Salvati" train stop.
Any tile the dry run reports blocked becomes an underground hop (up to 4 tiles). The route avoids the old base by
using the free ground south of it.

Usage: scripts/build_pack_route.py [--build]
"""
import json
import sys

from _game import tools

from bridge.factorio.planner import batches

N_, E_, S_, W_ = 0, 4, 8, 12


def segment(points):
    """Tiles along straight segments through corner points, with the direction of travel for each."""
    tiles = []
    for a, b in zip(points, points[1:]):
        dx = (b[0] > a[0]) - (b[0] < a[0])
        dy = (b[1] > a[1]) - (b[1] < a[1])
        d = {(1, 0): E_, (-1, 0): W_, (0, 1): S_, (0, -1): N_}[(dx, dy)]
        x, y = a
        while (x, y) != b:
            tiles.append((x, y, d))
            x, y = x + dx, y + dy
    last = points[-1]
    tiles.append((last[0], last[1], tiles[-1][2]))
    return tiles


def belt(x, y, d):
    return {"name": "transport-belt", "x": x + 0.5, "y": y + 0.5, "direction": d}


def blocked_tiles(tiles):
    ents = [belt(x, y, d) for x, y, d in tiles]
    bad = set()
    for i0 in range(0, len(ents), 400):
        r = json.loads(tools["place_entities"](json.dumps(ents[i0:i0 + 400]), dry_run=True))
        if r.get("error"):
            raise SystemExit(r)
        for f in r["failed"]:
            bad.add(i0 + f["i"] - 1)
    return bad


def with_hops(tiles):
    bad = blocked_tiles(tiles)
    ents, i = [], 0
    while i < len(tiles):
        x, y, d = tiles[i]
        if i not in bad:
            ents.append(belt(x, y, d))
            i += 1
            continue
        j = i
        while j in bad:
            j += 1
        if j - i > 4:
            raise SystemExit(f"blocked run of {j - i} tiles at {tiles[i][:2]}")
        # entrance is the previous tile, exit is tile j
        if i == 0 or (i - 1) in bad or j >= len(tiles):
            raise SystemExit(f"cannot hop at {tiles[i][:2]}")
        px, py, pd = tiles[i - 1]
        ents.pop()                                    # replace the previous belt with the entrance
        ents.append({"name": "underground-belt", "x": px + 0.5, "y": py + 0.5, "direction": pd, "params": {"type": "input"}})
        ex, ey, ed = tiles[j]
        ents.append({"name": "underground-belt", "x": ex + 0.5, "y": ey + 0.5, "direction": pd, "params": {"type": "output"}})
        i = j + 1
    return ents


def main():
    build = "--build" in sys.argv
    pts = [(128, -126), (130, -126), (130, -25), (-100, -25), (-100, -52)]
    tiles = segment(pts)
    print("tiles:", len(tiles))
    ents = with_hops(tiles)
    hops = sum(1 for e in ents if e.get("params", {}).get("type") == "input")
    print("entities:", len(ents), "hops:", hops)
    for part in batches(ents):
        r = json.loads(tools["place_entities"](json.dumps(part), dry_run=True))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"dry run failed: {json.dumps(r)[:1500]}")
    print("dry run clean")
    if not build:
        return
    print(tools["save_game"]("before-pack-route"))
    for part in batches(ents):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"stopped: {json.dumps(r)[:1500]}")
        print("placed", r["placed"])


if __name__ == "__main__":
    main()
