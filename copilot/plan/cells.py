"""The small generic patterns the skill may carry as clues (the Captain, 2026-11-13): one machine with its inputs and
outputs arranged for belts or for robots, the same for every recipe. Nothing here names a recipe, a count or a place;
the caller supplies the machine, its size and how many. No pattern is larger than one machine and what touches it,
except `row`, which only repeats a cell.

Every cell is designed facing north: inputs arrive on the north side, products leave on the south side. Turn the result
with Layout.turned() for other orientations."""
from .layout import E, N, S, Layout, LayoutError


def _centre(width):
    return width // 2


def belt_cell(machine, width, height, belt="transport-belt", inserter="inserter", recipe=None, two_inputs=False):
    """A machine fed from a belt along its north side and emptied onto a belt along its south side.

        b b b      input belt, running east
          i        inserter: picks up from the north (the belt), drops south into the machine
        M M M
        M M M
        M M M
          i        inserter: picks up from the north (the machine), drops south onto the belt
        b b b      output belt, running east

    With two_inputs a second input belt runs north of the first and a long-handed inserter reaches over to it, for
    recipes with more ingredients than one belt's two lanes can carry. Belts span the cell's width, so cells placed
    side by side share continuous belts."""
    if width < 1 or height < 1:
        raise LayoutError("a machine is at least one tile wide and high")
    if two_inputs and width < 2:
        raise LayoutError("two input belts need a machine at least two tiles wide (one inserter each)")
    lay = Layout()
    top = 0
    if two_inputs:
        for x in range(width):
            lay.put(belt, x, 0, direction=E, role="input-2")
        top = 1
    for x in range(width):
        lay.put(belt, x, top, direction=E, role="input")
    c = _centre(width)
    lay.put(inserter, c, top + 1, direction=N, role="in")
    if two_inputs:
        lay.put("long-handed-inserter", c - 1 if c > 0 else c + 1, top + 1, direction=N, role="in-2")
    extra = {"recipe": recipe} if recipe else {}
    lay.put(machine, 0, top + 2, width, height, role="machine", **extra)
    lay.put(inserter, c, top + 2 + height, direction=N, role="out")
    for x in range(width):
        lay.put(belt, x, top + 3 + height, direction=E, role="output")
    return lay


def robot_cell(machine, width, height, inserter="inserter", recipe=None, requester="requester-chest", provider="passive-provider-chest"):
    """A machine fed and emptied by logistic robots: a requester chest above, a provider chest below.

          R        requester chest (blue: the start of a line)
          i
        M M M
        M M M
        M M M
          i
          P        passive provider chest (red: the end of a line)

    The caller sets the requests on the requester and a limit on the provider, so the machine stops when stock stands."""
    if width < 1 or height < 1:
        raise LayoutError("a machine is at least one tile wide and high")
    lay = Layout()
    c = _centre(width)
    lay.put(requester, c, 0, role="requests")
    lay.put(inserter, c, 1, direction=N, role="in")
    extra = {"recipe": recipe} if recipe else {}
    lay.put(machine, 0, 2, width, height, role="machine", **extra)
    lay.put(inserter, c, 2 + height, direction=N, role="out")
    lay.put(provider, c, 3 + height, role="stock")
    return lay


def direct_pair(first, second, width, height, inserter="inserter", first_recipe=None, second_recipe=None):
    """Two machines side by side, the first handing its product straight to the second: no belt between.

        A A A i B B B      the inserter picks up from the west (machine A) and drops east into machine B
        A A A . B B B
        A A A . B B B
    """
    lay = Layout()
    lay.put(first, 0, 0, width, height, role="machine", **({"recipe": first_recipe} if first_recipe else {}))
    lay.put(inserter, width, height // 2, direction=12, role="hand-over")
    lay.put(second, width + 1, 0, width, height, role="machine", **({"recipe": second_recipe} if second_recipe else {}))
    return lay


def row(cell, count, gap=0):
    """The same cell `count` times, left to right, `gap` empty tiles between. Belts that span each cell join up when gap is 0."""
    if count < 1:
        raise LayoutError("a row has at least one cell")
    w, _ = cell.size()
    base = cell.at_origin()
    out = Layout()
    for i in range(count):
        out.add(base, dx=i * (w + gap))
    return out


def two_rows(cell, count, gap=0, aisle=0):
    """Two rows back to back: the second is the first turned half round, so both rows' output sides face the middle
    (aisle tiles apart) and both input sides face outward. Use it to share one output belt or one line of poles."""
    first = row(cell, count, gap)
    w, h = first.size()
    second = first.turned(2).at_origin()
    out = Layout()
    out.add(first)
    out.add(second, dy=h + aisle)
    return out
