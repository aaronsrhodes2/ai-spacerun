#!/usr/bin/env python3
"""Vulcanus trigger workshop: the three craft triggers that unlock the metallurgic science pack.
  lube     acid well (-11.5,89.5) -> refinery (simple coal liquefaction) -> chemical plant (lubricant) -> assembler (foundry item)
  lava     lava pump (54.5,-12.5) -> foundry A (48.5,-16.5, molten iron from lava) -> foundry B (48.5,-22.5, big mining drill, then tungsten plate)
Usage: vulcanus_triggers.py lube|lava [--apply]     (dry run without --apply)"""
import json
import sys

from _game import tools


def chest_in(x, y):
    return [{"name": "requester-chest", "x": x, "y": y}, {"name": "bulk-inserter", "x": x + 1, "y": y, "direction": 12}]


def chest_out(x, y):
    return [{"name": "bulk-inserter", "x": x, "y": y, "direction": 12}, {"name": "passive-provider-chest", "x": x + 1, "y": y}]


def lube():
    e = [{"name": "pumpjack", "x": -11.5, "y": 89.5, "direction": 0}, {"name": "pipe", "x": -10.5, "y": 87.5},
         {"name": "oil-refinery", "x": -9.5, "y": 84.5, "direction": 0, "recipe": "simple-coal-liquefaction"},
         {"name": "pipe", "x": -11.5, "y": 81.5},
         {"name": "chemical-plant", "x": -12.5, "y": 79.5, "direction": 8, "recipe": "lubricant"},
         {"name": "pipe", "x": -11.5, "y": 77.5},
         {"name": "assembling-machine-3", "x": -11.5, "y": 75.5, "direction": 8, "recipe": "foundry"},
         {"name": "substation", "x": -8, "y": 78}]
    e += chest_in(-13.5, 84.5) + chest_in(-14.5, 75.5) + chest_out(-9.5, 75.5)
    return e


def lava():
    e = [{"name": "offshore-pump", "x": 54.5, "y": -12.5, "direction": 4}]
    e += [{"name": "pipe", "x": x + 0.5, "y": -12.5} for x in range(47, 54)] + [{"name": "pipe", "x": 47.5, "y": -13.5}]
    e += [{"name": "foundry", "x": 48.5, "y": -16.5, "direction": 0, "recipe": "molten-iron-from-lava"}, {"name": "pipe", "x": 47.5, "y": -19.5},
          {"name": "foundry", "x": 48.5, "y": -22.5, "direction": 0}]
    e += chest_in(44.5, -16.5) + chest_out(51.5, -16.5) + chest_in(44.5, -22.5)
    e += [{"name": "bulk-inserter", "x": 48.5, "y": -25.5, "direction": 8}, {"name": "passive-provider-chest", "x": 48.5, "y": -26.5}]
    return e


def main():
    step = sys.argv[1]
    ents = {"lube": lube, "lava": lava}[step]()
    print(tools["place_entities"](json.dumps(ents), surface="vulcanus", dry_run="--apply" not in sys.argv)[:1500])


if __name__ == "__main__":
    main()
