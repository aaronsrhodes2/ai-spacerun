"""
Crude oil pipeline from the NW field to the refinery site.

    manifold  A* pipes joining the seven pumpjack outputs (N-facing jack: output on
              the tile one up and one right of its centre) to a trunk start at (-300,-292)
    trunk     underground pairs south along x=-300 to y=-110, a corner pipe at
              (-300,-109), then east along y=-109 to x=-153
    arrival   plain pipes (-152..-149,-109), the refinery's crude inputs (see
              build_refinery.py: refinery top-left (-152,-114))

Usage: scripts/build_crude_pipe.py [--build]
"""
import json
import math
import sys

from _game import tools

from bridge.factorio.planner import Grid, Plan, PlanError, batches, pipe_route, underground_run

S0 = (-300, -292)
CORNER = (-300, -109)
ARRIVAL = [(-152 + i, -109) for i in range(4)]


def grid(x1, y1, x2, y2):
    return Grid(json.loads(tools["map_grid"](x1, y1, x2, y2)))


def pipe(plan, tile):
    plan.machine("pipe", tile[0], tile[1], 1, 1)


# Output tile of a pumpjack by facing, as an offset from its centre (from the prototype's
# connection positions: N (1,-1), E (1,1), S (-1,1), W (-1,-1), one tile further out).
OUT = {0: (1, -2), 4: (2, 1), 8: (-1, 2), 12: (-2, -1)}


def out_tile(j, d):
    return (math.floor(j["x"] + OUT[d][0]), math.floor(j["y"] + OUT[d][1]))


def facing(plan, j, d, taken_outs):
    t = out_tile(j, d)
    return t not in taken_outs and t not in plan.taken and plan.grid.at(*t) not in "~K?E"


def build(rotate=False):
    jacks = json.loads(tools["run_lua"](" ".join("""
        local out = {}
        for _, e in pairs(game.surfaces.nauvis.find_entities_filtered{force='player', name='pumpjack'}) do out[#out+1] = {x=e.position.x, y=e.position.y} end
        rcon.print(helpers.table_to_json(out))
    """.splitlines())))
    field = Plan(grid(-335, -312, -290, -276))
    pipe(field, S0)
    placed = {S0}
    chosen, outs_taken = [], set()
    for j in jacks:
        for d in (0, 4, 8, 12):
            if facing(field, j, d, outs_taken):
                chosen.append((j, d))
                outs_taken.add(out_tile(j, d))
                break
        else:
            raise PlanError(f"no free output tile for the pumpjack at {j['x']},{j['y']}")
    for j, d in chosen:
        if d != 0 and rotate:
            print("rotating the jack at", j["x"], j["y"], "to", d)
            tools["run_lua"](f"local e = game.surfaces.nauvis.find_entity('pumpjack', {{{j['x']}, {j['y']}}}) e.direction = {d} rcon.print('ok')")
    outs = sorted((out_tile(j, d) for j, d in chosen), key=lambda t: math.hypot(t[0] - S0[0], t[1] - S0[1]))
    for out in outs:
        path = pipe_route(field, out, placed)
        for t in path:
            pipe(field, t)
            placed.add(t)
    vertical = Plan(grid(-306, -300, -294, -104))
    underground_run(vertical, (S0[0], S0[1] + 1), (CORNER[0], CORNER[1] - 1))
    pipe(vertical, CORNER)
    horizontal = Plan(grid(-306, -114, -146, -104))
    underground_run(horizontal, (CORNER[0] + 1, CORNER[1]), (ARRIVAL[0][0] - 1, ARRIVAL[0][1]))
    for t in ARRIVAL:
        pipe(horizontal, t)
    return field.entities, vertical.entities, horizontal.entities


def main():
    do_build = "--build" in sys.argv
    try:
        parts = build(rotate=do_build)
    except PlanError as e:
        raise SystemExit(f"plan error: {e}")
    entities = [e for part in parts for e in part]
    counts = {}
    for e in entities:
        counts[e["name"]] = counts.get(e["name"], 0) + 1
    print("plan:", counts)
    for part in batches(entities):
        r = json.loads(tools["place_entities"](json.dumps(part), dry_run=True))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"dry run failed, nothing built: {json.dumps(r)[:1800]}")
    print("dry run clean")
    if not do_build:
        return
    placed = 0
    for part in batches(entities):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"build stopped after {placed}: {json.dumps(r)[:1800]}")
        placed += r["placed"]
    print("placed", placed)


if __name__ == "__main__":
    main()
