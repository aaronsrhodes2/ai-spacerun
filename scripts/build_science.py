"""
Red science block, west of the hub, on the plate belts that end at x=-66.

    y=-67..-65  labs, 6 of them, inserters at y=-64 picking off the pack belt
    y=-63       pack belt, flowing west
    y=-62       pack output inserters
    y=-61..-59  pack assemblers (6), a gear assembler at -42, an ammo assembler at -38
    y=-58       input inserters, poles in the gap columns
    y=-57       copper belt (north lane copper, gears dropped onto the south lane)
    y=-56       iron belt (long inserters reach it)

All inserters here are electric: power is up, so no fuel paradox (the Captain, 2026-11-06).

Stages:  labs        labs, poles, pack belt (no research needed)
         assemblers  after `automation`: gear, pack and ammo assemblers
Usage: scripts/build_science.py <stage> [--build]
"""

import json
import sys

from _game import tools

from bridge.factorio.planner import E, N, S, W, Grid, Plan, batches, overlay

BOX = (-72, -70, -34, -50)
PACK_XS = [-66, -62, -58, -54, -50, -46]   # left column of each pack assembler and lab
GEAR_X, AMMO_X = -42, -38
AMMO_CHEST = (-37, -63)


def pole(plan, x, y):
    plan.machine("small-electric-pole", x, y, 1, 1)


def labs_plan(plan):
    for x in PACK_XS:
        plan.machine("lab", x, -67, 3, 3)
        plan.machine("inserter", x + 1, -64, 1, 1, direction=S)
        pole(plan, x + 3, -64)
        pole(plan, x + 3, -58)
    pole(plan, -39, -58)   # bridges to the smelter pole at (-35, -60)
    plan.line((-45, -63), (-67, -63), last_direction=W)


def assemblers_plan(plan):
    for x in PACK_XS:
        plan.machine("assembling-machine-1", x, -61, 3, 3, recipe="automation-science-pack")
        plan.machine("inserter", x + 1, -58, 1, 1, direction=S)
        plan.machine("inserter", x + 1, -62, 1, 1, direction=S)
    plan.machine("assembling-machine-1", GEAR_X, -61, 3, 3, recipe="iron-gear-wheel")
    plan.machine("long-handed-inserter", GEAR_X + 1, -58, 1, 1, direction=S)
    plan.machine("inserter", GEAR_X + 2, -58, 1, 1, direction=N)
    plan.machine("assembling-machine-1", AMMO_X, -61, 3, 3, recipe="firearm-magazine")
    plan.machine("long-handed-inserter", AMMO_X + 1, -58, 1, 1, direction=S)
    plan.machine("inserter", AMMO_X + 1, -62, 1, 1, direction=S)
    plan.machine("iron-chest", *AMMO_CHEST, 1, 1)


def main():
    stage = sys.argv[1]
    build = "--build" in sys.argv
    x1, y1, x2, y2 = BOX
    plan = Plan(Grid(json.loads(tools["map_grid"](x1, y1, x2, y2))))
    {"labs": labs_plan, "assemblers": assemblers_plan}[stage](plan)
    counts = {}
    for e in plan.entities:
        counts[e["name"]] = counts.get(e["name"], 0) + 1
    print("plan:", counts)
    if not build:
        print(overlay(plan, -70, -68, -34, -55))
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


if __name__ == "__main__":
    main()
