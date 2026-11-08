"""
Reusable layouts ("blueprints") for oil processing, as code. Every number here was taken from a
layout that works in the game (see docs/progress.md) and is pinned by tests/test_blueprints.py.

Coordinates are tiles; `tx, ty` is the top-left tile of the machine. Each function returns
entity dicts for place_entities plus the tiles the caller must connect to.

  refinery_n(tx, ty)   5x5 refinery facing north. Crude goes in on the south side at
                       (tx+1, ty+5) and (tx+3, ty+5); petroleum gas leaves at (tx+4, ty-1).
  refinery_s(tx, ty)   facing south: crude in on the NORTH side at (tx+1, ty-1) and (tx+3, ty-1),
                       gas out at (tx, ty+5). Two refineries can share one crude pipe row
                       (one facing north below it, one facing south above it).
  plastic_plant(tx, ty)  3x3 chemical plant facing south; a pipe row under it joins both inputs to
                       the gas line; coal comes in by inserter, plastic out by inserter.
  sulfur_plant(tx, ty) 3x3 facing north. Recipe order is water then gas, so water goes to the WEST
                       input at (tx, ty-1) and gas to the EAST input at (tx+2, ty-1). Returns
                       those two tiles as anchors.

Fluid boxes for chemical plants: the first fluid ingredient uses the first input box, which sits
at the west (-1) side when facing north and the east side when facing south.
"""

N, E, S, W = 0, 4, 8, 12


def _pipe(tx, ty):
    return {"name": "pipe", "x": tx + 0.5, "y": ty + 0.5}


def refinery_n(tx, ty, recipe="basic-oil-processing"):
    return {
        "entities": [{"name": "oil-refinery", "x": tx + 2.5, "y": ty + 2.5, "direction": N, "recipe": recipe}],
        "crude_in": [(tx + 1, ty + 5), (tx + 3, ty + 5)],
        "gas_out": (tx + 4, ty - 1),
    }


def refinery_s(tx, ty, recipe="basic-oil-processing"):
    return {
        "entities": [{"name": "oil-refinery", "x": tx + 2.5, "y": ty + 2.5, "direction": S, "recipe": recipe}],
        "crude_in": [(tx + 1, ty - 1), (tx + 3, ty - 1)],
        "gas_out": (tx, ty + 5),
    }


def plastic_plant(tx, ty):
    return {
        "entities": [{"name": "chemical-plant", "x": tx + 1.5, "y": ty + 1.5, "direction": S, "recipe": "plastic-bar"}]
                    + [_pipe(tx + i, ty + 3) for i in range(3)],
        "gas_in": (tx, ty + 3),
        "coal_inserter": (tx + 3, ty + 1),        # picks from the east, drops west into the plant
        "output_inserter": (tx + 1, ty - 1),      # picks from the plant, drops north
    }


def sulfur_plant(tx, ty):
    return {
        "entities": [{"name": "chemical-plant", "x": tx + 1.5, "y": ty + 1.5, "direction": N, "recipe": "sulfur"}],
        "water_in": (tx, ty - 1),
        "gas_in": (tx + 2, ty - 1),
        "output_inserter": (tx + 1, ty - 1),      # between the two inputs; drops north
    }
