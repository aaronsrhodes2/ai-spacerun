"""
Blue (chemical) science, west of the last green chain, along the extended plate belts.

Inputs
    y=-57  copper | gears   (the existing belt, extended west)
    y=-56  iron plates   (extended west)
    y=-63  N1  plastic (south lane, fed from the refinery) | advanced circuits (north lane)
    y=-64  N2  sulfur  (south lane, fed from the refinery) | engine units      (north lane)

Row A (machines y=-61..-59, south inserters y=-58, north inserters y=-62):
    engine sets   [pipe asm][engine asm][steel furnace + coal chest]: steel direct from the
                  furnace, gears by normal inserter from y=-57, pipes direct from the pipe asm;
                  engines out by long inserter onto N2. (Steel on the shared iron belt deadlocks
                  when iron stops being consumed, so steel is made in each set.)
    adv chains    [cable][circuit][advanced circuit][cable], plastic from N1 by normal
                  inserter, output onto N1.
Row B (machines y=-68..-66, inserter row y=-65, output row y=-69):
    pack asms     engines + sulfur from N2 (normal), advanced circuits from N1 (long),
                  packs out north onto the belt at y=-70, which runs east to the labs.

Inserter direction = the side it picks from: S picks from the south and drops north, N the
reverse, E picks from the east and drops west, W the reverse.

Stages: belts | engines | adv | nbelts | packs     Usage: scripts/build_blue.py <stage> [--build]
"""
import json
import sys

from _game import tools

from bridge.factorio.planner import E, N, S, W, Grid, Plan, batches

BOX = (-362, -80, -204, -50)
AM2 = "assembling-machine-2"
ENGINE_SETS = 4
ADV_CHAINS = 3
ENGINE_X0 = -224            # engine asm left column of the first set; later sets step -12
ADV_XA0 = -276              # first cable asm of the first adv chain; later chains step -16
PACK_XS = [-334, -338, -342, -346]
BELT_WEST = -352            # N1/N2 run west to here
PLATE_WEST = -326           # plate belts run west to here


def pole(plan, x, y):
    if (x, y) not in plan.taken:        # neighbouring groups share gap columns
        plan.machine("small-electric-pole", x, y, 1, 1)


def ins(plan, kind, x, y, d):
    plan.machine(kind, x, y, 1, 1, direction=d)


def belts_plan(plan):
    plan.line((-211, -57), (PLATE_WEST, -57), last_direction=W)
    plan.line((-211, -56), (PLATE_WEST, -56), last_direction=W)


def engines_plan(plan):
    """Each set: [pipe asm][engine asm][steel furnace] with a coal chest above the furnace.
    The furnace is a TEMPORARY coal burner (chest seeded by hand): the electric furnace
    replaces it once advanced-material-processing-2 is researched."""
    pole(plan, -214, -58)                                       # link to the last green chain
    for i in range(ENGINE_SETS):
        ex = ENGINE_X0 - 12 * i
        plan.machine(AM2, ex, -61, 3, 3, recipe="engine-unit")
        plan.machine(AM2, ex - 4, -61, 3, 3, recipe="pipe")
        plan.machine("steel-furnace", ex + 4, -60, 2, 2)
        ins(plan, "long-handed-inserter", ex - 3, -58, S)      # iron for the pipe asm
        ins(plan, "inserter", ex + 1, -58, S)                  # gears for the engine asm (y=-57)
        ins(plan, "long-handed-inserter", ex + 4, -58, S)      # iron plates into the steel furnace
        ins(plan, "inserter", ex - 1, -60, W)                  # pipes: pipe asm (west) -> engine asm
        ins(plan, "inserter", ex + 3, -60, E)                  # steel: furnace (east) -> engine asm
        ins(plan, "inserter", ex + 4, -61, N)                  # coal: chest above -> furnace
        plan.machine("iron-chest", ex + 4, -62, 1, 1)
        ins(plan, "long-handed-inserter", ex + 1, -62, S)      # engines out onto N2 (y=-64)
        pole(plan, ex - 1, -58)
        pole(plan, ex + 3, -58)
        pole(plan, ex + 3, -62)


def adv_plan(plan):
    for k in range(ADV_CHAINS):
        xa = ADV_XA0 - 16 * k
        xc, xd, xb = xa - 4, xa - 8, xa - 12
        plan.machine(AM2, xa, -61, 3, 3, recipe="copper-cable")
        plan.machine(AM2, xc, -61, 3, 3, recipe="electronic-circuit")
        plan.machine(AM2, xd, -61, 3, 3, recipe="advanced-circuit")
        plan.machine(AM2, xb, -61, 3, 3, recipe="copper-cable")
        ins(plan, "inserter", xa + 1, -58, S)                  # copper for cable A
        ins(plan, "long-handed-inserter", xc + 1, -58, S)      # iron for the circuit asm
        ins(plan, "inserter", xb + 1, -58, S)                  # copper for cable B
        ins(plan, "inserter", xa - 1, -60, E)                  # cable A -> circuit asm
        ins(plan, "inserter", xc - 1, -60, E)                  # circuits -> advanced circuit asm
        ins(plan, "inserter", xb + 3, -60, W)                  # cable B -> advanced circuit asm
        ins(plan, "inserter", xd + 1, -62, N)                  # plastic in from N1 (y=-63)
        ins(plan, "inserter", xd + 2, -62, S)                  # advanced circuits out onto N1
        for g in (xa + 3, xa - 1, xa - 5, xb + 3, xb - 1):
            pole(plan, g, -58)
        pole(plan, xa - 5, -62)


def nbelts_plan(plan):
    plan.line((-214, -63), (BELT_WEST, -63), last_direction=W)   # N1: plastic | advanced circuits
    plan.line((-215, -64), (BELT_WEST, -64), last_direction=W)   # N2: sulfur | engines


def packs_plan(plan):
    for xp in PACK_XS:
        plan.machine(AM2, xp, -68, 3, 3, recipe="chemical-science-pack")
        ins(plan, "inserter", xp, -65, S)                      # engines + sulfur from N2 (y=-64)
        ins(plan, "long-handed-inserter", xp + 1, -65, S)      # advanced circuits from N1 (y=-63)
        ins(plan, "inserter", xp + 1, -69, S)                  # packs out north onto y=-70
        pole(plan, xp + 3, -65)
        pole(plan, xp + 3, -69)
    plan.line((PACK_XS[-1] - 1, -70), (-212, -70), last_direction=E)


STAGES = {"belts": belts_plan, "engines": engines_plan, "adv": adv_plan,
          "nbelts": nbelts_plan, "packs": packs_plan}


def main():
    stage = sys.argv[1]
    build = "--build" in sys.argv
    plan = Plan(Grid(json.loads(tools["map_grid"](*BOX))))
    STAGES[stage](plan)
    counts = {}
    for e in plan.entities:
        counts[e["name"]] = counts.get(e["name"], 0) + 1
    print(stage, "plan:", counts)
    for part in batches(plan.entities):
        r = json.loads(tools["place_entities"](json.dumps(part), dry_run=True))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"dry run failed, nothing built: {json.dumps(r)[:1800]}")
    print(stage, "dry run clean")
    if not build:
        return
    placed = 0
    for part in batches(plan.entities):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"{stage} stopped after {placed}: {json.dumps(r)[:1800]}")
        placed += r["placed"]
    print(stage, "placed", placed)


if __name__ == "__main__":
    main()
