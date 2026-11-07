"""Helpers shared by the line-building scripts."""
import json
import math

from _game import tools


def lua(code):
    return tools["run_lua"](" ".join(code.splitlines()))


def free_spot(name, x, y, radius=6):
    r = lua(f"""
        local p = game.surfaces.nauvis.find_non_colliding_position('{name}', {{{x}, {y}}}, {radius}, 1)
        rcon.print(p and (p.x .. ',' .. p.y) or 'none')
    """)
    if r == "none":
        raise SystemExit(f"no free spot for {name} near {x},{y}")
    px, py = (float(v) for v in r.split(","))
    return px, py


def big_pole_chain(start, end, first_reach=7.4, step=28.0, last_within=22.0, build=False):
    """Big electric poles from `start` (an existing pole's centre) toward `end`, each ~`step`
    tiles on, positions found in-game. The first must be within `first_reach` of the start pole
    (7.4 for a small pole, 9 for a medium one). Stops once within `last_within` of `end`.
    Returns the placed/planned poles."""
    prev = start
    poles = []
    first = True
    while True:
        dist = math.hypot(end[0] - prev[0], end[1] - prev[1])
        if not first and dist <= last_within:
            break
        move = (first_reach - 1.0) if first else step
        move = min(move, dist)
        tx, ty = prev[0] + (end[0] - prev[0]) / dist * move, prev[1] + (end[1] - prev[1]) / dist * move
        px, py = free_spot("big-electric-pole", tx, ty, 6)
        reach = first_reach if first else 31.0
        gap = math.hypot(px - prev[0], py - prev[1])
        if gap > reach:
            raise SystemExit(f"pole {len(poles) + 1} at {px},{py} is {gap:.1f} from the last (limit {reach})")
        poles.append({"name": "big-electric-pole", "x": px, "y": py})
        prev = (px, py)
        first = False
    if build:
        r = json.loads(tools["place_entities"](json.dumps(poles)))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"pole line failed: {json.dumps(r)[:600]}")
    return poles
