# Replicator fluid-assembler unit (design, 2026-11-14; not built yet)

Closes the gap the Replicator audit found (docs/replicator-audit.md): 10 items whose assembler recipe needs a fluid. The Captain chose the
**barrel-fed** design (like scripts/omni_fluid.py): no pipes to the network.

## What it makes

Generated from the game's recipes (`scripts/omni_fluid_asm.py list`), not typed. Rule: an enabled recipe an assembling machine 3 can run, one item
product, exactly one fluid ingredient that has a barrel, no fluid product, product not already on the assembler list, product not a barrel.

| Item | Fluid (barrel) per craft | In biome? |
|---|---|---|
| processing-unit | sulfuric acid 5 | yes |
| electric-engine-unit | lubricant 15 | yes |
| express-transport-belt / underground-belt / splitter | lubricant 20 / 40 / 80 | yes |
| concrete, refined-concrete | water 100 | yes |
| rocket-fuel | light oil 10 | yes |
| foundry, tungsten-carbide | lubricant 20, sulfuric acid 10 | no (tungsten) |
| overgrowth yumako / jellynut soil | water 100 | no (Gleba) |

Not made here: `crude-oil-barrel` and `heavy-oil-barrel` (the raw barrels the fluid units ask for; `scripts/nauvis_taps.py` fills them) and the
molten-iron concrete, jelly rocket fuel and ammonia rocket fuel variants (no barrel, or a machine the unit lacks).

## Layout (P = tile under the product machine's centre)

An assembling machine 3 facing north has its fluid **input at the top centre** and its fluid **output at the bottom centre** (prototype data), so:

    E  emptier   centre (P.x, P.y-3)   recipe empty-<fluid>-barrel   fluid out (bottom) -> P fluid in (top)
    P  maker     centre (P.x, P.y)     recipe set by circuit

Each machine has a blue requester chest + fast inserter on its west side and a fast inserter + red passive provider chest on its east side
(P: solids in, product out; E: barrels in, empty barrels out). Control (west): constant combinator (item list), decider, selector. A
substation sits north-east. The recipe table is one row of 4 deciders per item (P recipe, P solids, E recipe, E barrels), 1 x 2 each, south of the unit.

Control is omni_maker's: the demand roboport's missing requests (the Replicator's roboport at (-352,-229), over-reach script wire) pass the
unit's item list, the selector picks the most-missing item, and the table answers with recipes and requests (batch 10, barrels = ceil(fluid x 10 / 50)).

## Site

Dry runs (nothing placed): **(-330,-178)** and **(-300,-178)** place all 62 entities with no failure, inside the logistic network, nearest pole 6-7
tiles. (-340,-184), (-282,-215), (-330,-246), (-270,-178), (-282,-200) and (-270,-240) are blocked. Recommended: (-330,-178), just south of the
Replicator box, next to the assembler units.

## Stock check

Network barrels at design time: water 111, lubricant 100, sulfuric acid 100, light oil 106, empty barrels 122; crude and heavy oil barrels 0.
Solid ingredient stock is whatever the factory holds (engine-unit was -12, i.e. requested and missing).

## Build

    python scripts/omni_fluid_asm.py check --at -330 -178        # dry run again
    python scripts/omni_fluid_asm.py build --at -330 -178 --apply  # save first; builds, then wires (never twice at one site)
    python scripts/omni_fluid_asm.py status --at -330 -178
Re-run `config --at -330 -178` after any recipe research that adds a fluid-assembler item.

## Not verified

The fluid connection E -> P (port alignment) is derived from prototype data; it has not been seen working. The first build should be watched:
E should show the fluid in its output and P a fluid in its input within a minute of the first order.
