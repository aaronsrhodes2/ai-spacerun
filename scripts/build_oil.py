"""
Oil field in the north-west: power line, then pumpjacks, then the crude pipeline home.

    poles     big electric poles (32 reach) from the westernmost base pole near
              (-201.5,-61.5) to the field, positions found in-game with
              find_non_colliding_position so cliffs and trees don't need planning
    jacks     pumpjacks on the crude-oil spots near (-314,-293)

Usage: scripts/build_oil.py poles [--build]
       scripts/build_oil.py jacks [N] [--build]    N pumpjacks, best yield first
"""
import json
import math
import sys

from _game import tools

START = (-201.5, -61.5)
FIELD = (-314.0, -292.0)


def lua(code):
    return tools["run_lua"](" ".join(code.splitlines()))


def free_spot(name, x, y, radius=10):
    r = lua(f"""
        local p = game.surfaces.nauvis.find_non_colliding_position('{name}', {{{x}, {y}}}, {radius}, 1)
        rcon.print(p and (p.x .. ',' .. p.y) or 'none')
    """)
    if r == "none":
        raise SystemExit(f"no free spot for {name} near {x},{y}")
    px, py = (float(v) for v in r.split(","))
    return px, py


def pole_line():
    """Each pole is placed ~28 tiles from the previous one toward the field."""
    prev = START
    poles = []
    first = True
    while True:
        dist = math.hypot(FIELD[0] - prev[0], FIELD[1] - prev[1])
        if not first and dist <= 22:
            break
        step = 6.5 if first else 28.0
        tx, ty = prev[0] + (FIELD[0] - prev[0]) / dist * step, prev[1] + (FIELD[1] - prev[1]) / dist * step
        px, py = free_spot("big-electric-pole", tx, ty, 6)
        reach = 7.4 if first else 31.0
        gap = math.hypot(px - prev[0], py - prev[1])
        if gap > reach:
            raise SystemExit(f"pole {len(poles) + 1} at {px},{py} is {gap:.1f} from the last (limit {reach})")
        poles.append({"name": "big-electric-pole", "x": px, "y": py})
        prev = (px, py)
        first = False
    return poles


def spots():
    r = json.loads(lua(f"""
        local out = {{}}
        for _, e in pairs(game.surfaces.nauvis.find_entities_filtered{{name='crude-oil', position={{{FIELD[0]}, {FIELD[1]}}}, radius=40}}) do
          out[#out+1] = {{x=e.position.x, y=e.position.y, yield=math.floor(e.amount / 3000)}}
        end
        rcon.print(helpers.table_to_json(out))
    """))
    return sorted(r, key=lambda s: -s["yield"])


def main():
    stage = sys.argv[1]
    build = "--build" in sys.argv
    if stage == "poles":
        poles = pole_line()
        print(len(poles), "big poles:", [(p["x"], p["y"]) for p in poles])
        r = json.loads(tools["place_entities"](json.dumps(poles), dry_run=True))
        print("dry run:", json.dumps(r)[:400])
        if build and not r["failed"]:
            print(tools["place_entities"](json.dumps(poles))[:400])
    elif stage == "jacks":
        n = int(next((a for a in sys.argv[2:] if a.isdigit()), 1))
        found = spots()
        print(len(found), "oil spots:", [(s["x"], s["y"], s["yield"]) for s in found])
        jacks = [{"name": "pumpjack", "x": s["x"], "y": s["y"], "direction": 0} for s in found[:n]]
        r = json.loads(tools["place_entities"](json.dumps(jacks), dry_run=True))
        print("dry run:", json.dumps(r)[:400])
        if build and not r["failed"]:
            print(tools["place_entities"](json.dumps(jacks))[:400])


if __name__ == "__main__":
    main()
