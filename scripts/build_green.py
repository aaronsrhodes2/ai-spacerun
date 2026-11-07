"""
Green science (logistic-science-pack = 1 inserter + 1 transport-belt, 6 s).

  power2  second boiler and two more engines east of the first, sharing the water
          pipe and the coal belt (belt end turned east, one more tile, burner inserter)
  labs3   third lab row at y=-75..-73: red arrives lab-to-lab from labs2 (inserters at
          y=-72), green by belt at y=-77 (inserters at y=-76)
  chain   one direct-insertion chain west of the red block, on the plate belts extended
          to x=-90:  [cable][circuit][inserter][green pack][belt]  at y=-61..-59
          Gears already ride the copper belt's south lane (the red block's gear
          assembler), so inserter and belt assemblers take them straight off it.
          Pack output goes to a belt that loops west, north and east to labs3.

One chain makes 0.083 packs/s. Duplicate the chain westward to scale.
Usage: scripts/build_green.py <stage> [--build]
"""

import json
import sys

from _game import tools

from bridge.factorio.planner import E, N, S, W, Grid, Plan, batches
from build_science import PACK_XS, pole

SLOTS = {"copper-cable": -72, "electronic-circuit": -76, "inserter": -80,
         "logistic-science-pack": -84, "transport-belt": -88}
WEST = -90


def power2_plan(plan):
    for x in (32, 33, 34, 35):
        plan.machine("pipe", x, 49, 1, 1)
    plan.machine("boiler", 36, 48, 3, 2)
    plan.machine("steam-engine", 36, 43, 3, 5)
    plan.machine("steam-engine", 36, 38, 3, 5)
    plan.belt(33, 48, E)          # was the end of the coal belt, facing south
    plan.belt(34, 48, E)
    plan.inserter(35, 48, W)      # burner, so power can restart from cold
    pole(plan, 35, 44)


def labs3_plan(plan):
    for x in PACK_XS:
        plan.machine("lab", x, -75, 3, 3)
        plan.machine("inserter", x + 1, -72, 1, 1, direction=S)
        plan.machine("inserter", x + 1, -76, 1, 1, direction=N)
        pole(plan, x + 3, -72)
        pole(plan, x + 3, -76)


def chain_plan(plan, shift=0):
    """One chain. `shift` moves it west by whole chains (20 tiles each)."""
    slots = {k: v - 20 * shift for k, v in SLOTS.items()}
    west = WEST - 20 * shift
    east = -67 if shift == 0 else WEST - 20 * (shift - 1) - 1
    plan.line((east, -57), (west, -57), last_direction=W)
    plan.line((east, -56), (west, -56), last_direction=W)
    for recipe, x in slots.items():
        plan.machine("assembling-machine-2", x, -61, 3, 3, recipe=recipe)
    c, e, i, p, b = (slots[k] for k in slots)
    plan.machine("inserter", c + 1, -58, 1, 1, direction=S)                 # copper
    plan.machine("long-handed-inserter", e + 1, -58, 1, 1, direction=S)     # iron
    plan.machine("long-handed-inserter", i + 1, -58, 1, 1, direction=S)     # iron
    plan.machine("inserter", i, -58, 1, 1, direction=S)                     # gears
    plan.machine("long-handed-inserter", b + 1, -58, 1, 1, direction=S)     # iron
    plan.machine("inserter", b, -58, 1, 1, direction=S)                     # gears
    plan.machine("inserter", c - 1, -60, 1, 1, direction=E)   # cable -> circuit
    plan.machine("inserter", e - 1, -60, 1, 1, direction=E)   # circuit -> inserter asm
    plan.machine("inserter", i - 1, -60, 1, 1, direction=E)   # inserters -> pack asm
    plan.machine("inserter", p - 1, -60, 1, 1, direction=W)   # belts -> pack asm
    plan.machine("inserter", p + 1, -62, 1, 1, direction=S)   # packs out
    pole(plan, p + 2, -62)   # the output inserter sits outside the y=-58 poles' reach
    for x in ([east - 2] if shift == 0 else []) + [c - 1, e - 1, i - 1, p - 1, b - 1]:
        pole(plan, x, -58)
    if shift == 0:
        plan.line((p + 1, -63), (west, -63), (west, -77), (-44, -77), last_direction=E)
    else:
        plan.line((p + 1, -63), (west, -63), (west, -77), (west + 19, -77), last_direction=E)


def chain2_plan(plan):
    chain_plan(plan, shift=1)


STAGES = {"power2": (power2_plan, (20, 30, 45, 56)),
          "labs3": (labs3_plan, (-72, -80, -40, -68)),
          "chain": (chain_plan, (-95, -80, -40, -50)),
          "chain2": (chain2_plan, (-115, -80, -60, -50)),
          "chain3": (lambda plan: chain_plan(plan, shift=2), (-135, -80, -108, -50)),
          "chain4": (lambda plan: chain_plan(plan, shift=3), (-155, -80, -128, -50))}
for _s in range(4, 8):
    _w = WEST - 20 * _s
    STAGES[f"chain{_s + 1}"] = ((lambda plan, _s=_s: chain_plan(plan, shift=_s)), (_w - 6, -80, _w + 26, -50))


def main():
    stage = sys.argv[1]
    build = "--build" in sys.argv
    fn, box = STAGES[stage]
    snap = json.loads(tools["map_grid"](*box))
    if stage == "power2":
        snap["rows"] = [r.replace("E", ".") for r in snap["rows"]]   # the belt end is re-laid
    plan = Plan(Grid(snap))
    fn(plan)
    counts = {}
    for e in plan.entities:
        counts[e["name"]] = counts.get(e["name"], 0) + 1
    print(stage, "plan:", counts)
    if stage == "power2" and build:
        print("old belt end:", tools["remove_entities"](33.3, 48.3, 33.7, 48.7, names="transport-belt"))
    for part in batches(plan.entities):
        r = json.loads(tools["place_entities"](json.dumps(part), dry_run=True))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"dry run failed, nothing built: {json.dumps(r)[:1500]}")
    print("dry run clean")
    if not build:
        return
    placed = 0
    for part in batches(plan.entities):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"build stopped after {placed}: {json.dumps(r)[:1500]}")
        placed += r["placed"]
    print("placed", placed)
    if stage == "power2":
        print("fuel:", tools["seed_starter_fuel"](30, 46, 40, 50))


if __name__ == "__main__":
    main()
