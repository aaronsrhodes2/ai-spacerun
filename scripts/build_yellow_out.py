"""
Yellow (utility) science packs from the yellow block's output belt end (25,-108) to the pack line on y=-25 (flowing west to the ports):
east along y=-107 to x=42, south down x=42 (hop under the coal belt on y=-63), and side-load onto the y=-25 belt at (42,-25).
Usage: scripts/build_yellow_out.py [--build]
"""
import json
import sys

from _game import tools

from bridge.factorio.planner import batches

N, E, S, W = 0, 4, 8, 12
XS = 42


def belt(x, y, d):
    return {"name": "transport-belt", "x": x + 0.5, "y": y + 0.5, "direction": d}


def ug(x, y, d, kind):
    return {"name": "underground-belt", "x": x + 0.5, "y": y + 0.5, "direction": d, "params": {"type": kind}}


def plan():
    e = [belt(x, -107, E) for x in range(25, XS)]
    e += [belt(XS, y, S) for y in range(-107, -65)]          # -107 .. -66
    e += [ug(XS, -65, S, "input"), ug(XS, -61, S, "output")]  # under the coal belt on y=-63
    e += [belt(XS, y, S) for y in range(-60, -25)]            # -60 .. -26
    return e


def main():
    ents = plan()
    for part in batches(ents):
        r = json.loads(tools["place_entities"](json.dumps(part), dry_run=True))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"dry run failed: {json.dumps(r)[:2500]}")
    print("dry run clean", len(ents))
    if "--build" not in sys.argv:
        return
    print(tools["save_game"]("before-yellow-out"))
    for part in batches(ents):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        print(r.get("placed"), r.get("failed"))


if __name__ == "__main__":
    main()
