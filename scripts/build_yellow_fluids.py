"""
Piping for the yellow block: sulfuric acid and lubricant from the two tanks at (-264,-130) / (-252,-130).
Two long east-west pipe-to-ground trunks (acid on y=-125.5, lubricant on y=-123.5), tapped off the existing
acid line at (-234.5,-127.5) and the lubricant line at (-242.5,-130.5), then branches south into the machines'
north fluid inputs (the machines face north): PU (21,-115), battery (29,-119), electric engine unit (33,-115).
Usage: scripts/build_yellow_fluids.py [--build]
"""
import json
import sys

from _game import tools

from bridge.factorio.planner import batches

N, E, S, W = 0, 4, 8, 12
ACID_Y, LUBE_Y = -123, -124          # tile rows (centre = +0.5); a rail runs along y=-126..-125 west of x=-210
X_ACID_TAP, X_LUBE_TAP = -234, -242  # first free tile east of the existing lines
X_PU, X_BAT, X_EEU = 21, 29, 33
ACID_START_Y, ACID_MID_Y, X_DROP, X_JOG = -128, -122, -216, -150   # rail junction: acid runs east on the tap row, drops under the E-W rail at x=-216, then returns to row -123


def pipe(x, y):
    return {"name": "pipe", "x": x + 0.5, "y": y + 0.5}


def ptg(x, y, d):
    return {"name": "pipe-to-ground", "x": x + 0.5, "y": y + 0.5, "direction": d}


def row_free(y, x1, x2):
    lua = ("local s=game.surfaces.nauvis local o={} for x=%d,%d do if s.can_place_entity{name='pipe-to-ground',"
           "position={x+0.5,%f},direction=4,force='player'} then o[#o+1]=x end end rcon.print(table.concat(o,','))"
           % (x1, x2, y + 0.5))
    return {int(v) for v in tools["run_lua"](lua).split(",") if v}


def chain(y, x0, x_last, free, forbidden=()):
    """Eastbound underground chain on tile row y. ptg at x0 opens west (connects to whatever is at x0-1);
    the last ptg at x_last opens east. Returns the entity list."""
    ok = lambda x: x in free and x not in forbidden
    ents = []
    while True:
        if not ok(x0):
            raise SystemExit(f"start tile {x0},{y} blocked")
        ents.append(ptg(x0, y, W))
        if x_last - x0 <= 10 and ok(x_last):
            ents.append(ptg(x_last, y, E))
            return ents
        x1 = max((x for x in range(x0 + 1, x0 + 11) if ok(x) and ok(x + 1) and x + 1 < x_last), default=None)
        if x1 is None:
            raise SystemExit(f"stuck at {x0},{y}")
        ents.append(ptg(x1, y, E))
        x0 = x1 + 1


def plan():
    ents = []
    # acid: tap east of the corner pipe (-234.5,-127.5), step down to ACID_Y, then run east on ACID_Y
    ents.append(pipe(X_ACID_TAP, ACID_START_Y))
    ents += chain(ACID_START_Y, X_ACID_TAP + 1, X_DROP - 1, row_free(ACID_START_Y, X_ACID_TAP + 1, X_DROP))
    ents += [pipe(X_DROP, ACID_START_Y), ptg(X_DROP, ACID_START_Y + 1, N), ptg(X_DROP, ACID_MID_Y - 1, S), pipe(X_DROP, ACID_MID_Y)]
    ents += chain(ACID_MID_Y, X_DROP + 1, X_JOG - 1, row_free(ACID_MID_Y, X_DROP + 1, X_JOG))
    ents += [pipe(X_JOG, y) for y in range(ACID_Y, ACID_MID_Y + 1)]
    ents += chain(ACID_Y, X_JOG + 1, X_PU - 1, row_free(ACID_Y, X_JOG + 1, X_PU))
    ents.append(pipe(X_PU, ACID_Y))
    ents.append(ptg(X_PU, ACID_Y + 1, N))                        # branch south to the processing unit
    ents.append(ptg(X_PU, -115, S))
    ents.append(ptg(X_PU + 1, ACID_Y, W))                        # on to the battery column
    ents.append(ptg(X_BAT - 1, ACID_Y, E))
    ents.append(pipe(X_BAT, ACID_Y))
    ents.append(ptg(X_BAT, ACID_Y + 1, N))
    ents.append(ptg(X_BAT, -119, S))
    # lubricant: pipe at (-241.5,-131.5) east of the existing line, ptg south, then east on LUBE_Y
    ents += [pipe(X_LUBE_TAP, -132), ptg(X_LUBE_TAP, -131, N), ptg(X_LUBE_TAP, LUBE_Y - 1, S), pipe(X_LUBE_TAP, LUBE_Y)]
    free_l = row_free(LUBE_Y, X_LUBE_TAP + 1, X_EEU)
    forb_l = {X_PU, X_BAT, X_PU + 1, X_BAT - 1}
    ents += chain(LUBE_Y, X_LUBE_TAP + 1, X_EEU - 1, free_l, forb_l)
    ents.append(pipe(X_EEU, LUBE_Y))
    ents.append(ptg(X_EEU, LUBE_Y + 1, N))
    ents.append(ptg(X_EEU, -115, S))
    return ents


def main():
    ents = plan()
    counts = {}
    for e in ents:
        counts[e["name"]] = counts.get(e["name"], 0) + 1
    print(counts)
    for part in batches(ents):
        r = json.loads(tools["place_entities"](json.dumps(part), dry_run=True))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"dry run failed: {json.dumps(r)[:2500]}")
    print("dry run clean")
    if "--build" not in sys.argv:
        return
    print(tools["save_game"]("before-yellow-fluids"))
    for part in batches(ents):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        print(r.get("placed"), r.get("failed"))


if __name__ == "__main__":
    main()
