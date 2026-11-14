"""Joints: the small patterns for where supply lines meet and cross (the Captain, 2026-11-13). These are the hard part
of a layout and the part worth showing: a belt under a belt, a pipe under a belt, a splitter used as a filter, one belt
feeding one lane of another, the row of inserters beside a train wagon. Each solves one kind of meeting and nothing
more; none names a recipe, a count or a place. Whole production lines are never stored: they are made from these.

Every joint is designed with its main flow running NORTH (toward smaller y) and is turned in code for other directions.
"Left" and "right" are as seen looking along the flow: with the flow north, left is west.

Facts of the game these lean on:
  - An underground belt or pipe pair passes under anything; the two ends face along the run.
  - A belt that ends pointing into the SIDE of another belt puts its items on the near lane of that belt only.
  - A splitter is two tiles wide across the flow. With a filter set, the filtered item leaves on the side named by its
    output priority and everything else leaves on the other side. With only a priority set, that side is served first.
  - An inserter's direction is the side it picks up from; it drops on the opposite side.
  - A wagon is six tiles long; one inserter per tile along its side is the most that can reach it."""
from .layout import E, N, S, W, Layout, LayoutError

UNDERGROUND = {"transport-belt": "underground-belt", "fast-transport-belt": "fast-underground-belt",
               "express-transport-belt": "express-underground-belt", "turbo-transport-belt": "turbo-underground-belt"}


def _under(belt):
    if belt not in UNDERGROUND:
        raise LayoutError("no underground belt is known for '%s'" % belt)
    return UNDERGROUND[belt]


def belt_crossing(belt="transport-belt", crossing_belt=None, width=1):
    """One belt crossing another without mixing: the main belt (running north) dives under a belt running east.

        b      main belt, north
        U      underground exit
        > > >  the crossing belt, running east (width rows of it)
        U      underground entrance
        b      main belt

    width is how many belts side by side are crossed (the underground's reach limits it: 4 for the basic belt)."""
    if width < 1:
        raise LayoutError("at least one belt must be crossed")
    crossing_belt = crossing_belt or belt
    lay = Layout()
    lay.put(belt, 0, 0, direction=N, role="main")
    lay.put(_under(belt), 0, 1, direction=N, type="output", role="exit")
    for row in range(width):
        for x in (-1, 0, 1):
            lay.put(crossing_belt, x, 2 + row, direction=E, role="crossing")
    lay.put(_under(belt), 0, 2 + width, direction=N, type="input", role="entrance")
    lay.put(belt, 0, 3 + width, direction=N, role="main")
    return lay


def pipe_crossing(pipe="pipe", underground="pipe-to-ground", belt="transport-belt", width=1):
    """A pipe (running north-south) passing under belts running east. The two pipe-to-ground pieces open outward, away
    from the belts, so the pipe touches nothing in between: no leak into a neighbouring pipe line."""
    if width < 1:
        raise LayoutError("at least one belt must be crossed")
    lay = Layout()
    lay.put(pipe, 0, 0, role="pipe")
    lay.put(underground, 0, 1, direction=N, role="open-north")
    for row in range(width):
        for x in (-1, 0, 1):
            lay.put(belt, x, 2 + row, direction=E, role="crossing")
    lay.put(underground, 0, 2 + width, direction=S, role="open-south")
    lay.put(pipe, 0, 3 + width, role="pipe")
    return lay


def filter_splitter(item, splitter="splitter", belt="transport-belt", to="left"):
    """Take one kind of item off a mixed belt. The mixed belt comes in from the south on the right half of a splitter;
    the filtered item leaves north on the side named by `to`, everything else on the other side.

        L R      two belts out, north: L gets the filtered item when to is 'left'
        S S      the splitter, filter set
        . b      the mixed belt in, from the south

    Unlike a filtered inserter this keeps the belt's full speed."""
    if to not in ("left", "right"):
        raise LayoutError("to must be 'left' or 'right'")
    lay = Layout()
    lay.put(belt, 0, 0, direction=N, role="filtered" if to == "left" else "rest")
    lay.put(belt, 1, 0, direction=N, role="filtered" if to == "right" else "rest")
    lay.put(splitter, 0, 1, 2, 1, direction=N, filter=item, output_priority=to, role="splitter")
    lay.put(belt, 1, 2, direction=N, role="mixed")
    return lay


def priority_merge(splitter="splitter", belt="transport-belt", first="left"):
    """Two belts into one, with one of them always served first (science packs before ore, say). Both come in from the
    south; the output leaves north on the left half. The other output is left empty on purpose.

        b .      one belt out
        S S      the splitter, input priority set
        b b      two belts in: the `first` side is drained before the other gets a turn"""
    if first not in ("left", "right"):
        raise LayoutError("first must be 'left' or 'right'")
    lay = Layout()
    lay.put(belt, 0, 0, direction=N, role="out")
    lay.put(splitter, 0, 1, 2, 1, direction=N, input_priority=first, output_priority="left", role="splitter")
    lay.put(belt, 0, 2, direction=N, role="in-left")
    lay.put(belt, 1, 2, direction=N, role="in-right")
    return lay


def side_load(belt="transport-belt", feeder_belt=None, side="left"):
    """Put one belt's items onto ONE lane of another: the feeder ends pointing into the side of the main belt. Two
    feeders, one from each side, give a belt carrying a different item on each lane.

        b          main belt, north
        > b        the feeder from the left (west) ends against the main belt's side: its items take the left lane
        b          main belt"""
    if side not in ("left", "right"):
        raise LayoutError("side must be 'left' or 'right'")
    feeder_belt = feeder_belt or belt
    lay = Layout()
    for y in range(3):
        lay.put(belt, 0, y, direction=N, role="main")
    if side == "left":
        lay.put(feeder_belt, -1, 1, direction=E, role="feeder")
    else:
        lay.put(feeder_belt, 1, 1, direction=W, role="feeder")
    return lay


def lane_pair(belt="transport-belt"):
    """A belt with a lane each for two items: a feeder from each side, both ending against the main belt."""
    lay = side_load(belt, side="left")
    lay.put(belt, 1, 1, direction=W, role="feeder")
    return lay


def filtered_pick(item, inserter="inserter", belt="transport-belt"):
    """Pick one kind of item off a mixed belt into whatever stands north of the inserter: the inserter picks up from
    the south (the belt) and only takes the filtered item."""
    lay = Layout()
    lay.put(inserter, 0, 0, direction=S, filter=item, role="pick")
    lay.put(belt, 0, 1, direction=E, role="mixed")
    return lay


def wagon_side(action="unload", inserter="inserter", chest="steel-chest", belt="transport-belt", wagons=1, gap=1):
    """The row beside a stopped train's cargo wagons, one inserter per wagon tile, with a chest each as a buffer and a
    belt beyond. The wagons stand along the NORTH edge of this joint, the first wagon's first tile above column 0.

        unload:  i i i i i i    inserters pick up from the north (the wagon)
                 C C C C C C    chests
                 i i i i i i    inserters pick up from the north (the chests)
                 > > > > > >    the belt away, east

        load:    the same shape with every inserter turned round and the belt bringing items in.

    wagons is how many wagons the train has on this side; gap is the tiles between wagons (1, for the coupling)."""
    if action not in ("unload", "load"):
        raise LayoutError("action must be 'unload' or 'load'")
    if wagons < 1:
        raise LayoutError("at least one wagon")
    pick = N if action == "unload" else S
    lay = Layout()
    for w in range(wagons):
        x0 = w * (6 + gap)
        for i in range(6):
            x = x0 + i
            lay.put(inserter, x, 0, direction=pick, role="wagon-inserter")
            lay.put(chest, x, 1, role="buffer")
            lay.put(inserter, x, 2, direction=pick, role="belt-inserter")
    for x in range(wagons * 6 + (wagons - 1) * gap):
        lay.put(belt, x, 3, direction=E, role="belt")
    return lay


JOINTS = {
    "belt_crossing": {"solves": "one belt has to cross another without their items mixing", "make": belt_crossing,
                      "options": {"width": "how many belts side by side are crossed (default 1)"}},
    "pipe_crossing": {"solves": "a pipe has to cross belts, or pass close to another pipe without joining it", "make": pipe_crossing,
                      "options": {"width": "how many belts side by side are crossed (default 1)"}},
    "filter_splitter": {"solves": "one kind of item has to be taken off a mixed belt at full belt speed", "make": filter_splitter,
                        "options": {"item": "the item to take off (required)", "to": "'left' or 'right': the side the filtered item leaves on (default left)"}},
    "priority_merge": {"solves": "two belts join into one and one of them must always go first", "make": priority_merge,
                       "options": {"first": "'left' or 'right': the input served first (default left)"}},
    "side_load": {"solves": "a belt's items must go onto one lane of another belt, to carry two items on one belt", "make": side_load,
                  "options": {"side": "'left' or 'right': the side the feeder comes from, and the lane it fills (default left)"}},
    "lane_pair": {"solves": "two items must share one belt, a lane each", "make": lane_pair, "options": {}},
    "filtered_pick": {"solves": "a machine or chest must take only one kind of item from a mixed belt", "make": filtered_pick,
                      "options": {"item": "the item to pick (required)"}},
    "wagon_side": {"solves": "a train's cargo wagons must be unloaded onto a belt, or loaded from one", "make": wagon_side,
                   "options": {"action": "'unload' or 'load' (default unload)", "wagons": "how many wagons (default 1)"}},
}


def catalogue():
    """What the model is shown: each joint, the problem it solves and its options."""
    return [{"joint": name, "solves": j["solves"], "options": j["options"]} for name, j in JOINTS.items()]


def make(name, **options):
    if name not in JOINTS:
        raise LayoutError("there is no joint '%s'; joints are: %s" % (name, ", ".join(JOINTS)))
    spec = JOINTS[name]
    unknown = [k for k in options if k not in spec["options"] and k not in ("belt", "inserter", "splitter", "chest", "pipe", "underground", "crossing_belt", "feeder_belt")]
    if unknown:
        raise LayoutError("the joint '%s' has no option '%s'; its options are: %s" % (name, unknown[0], ", ".join(spec["options"]) or "none"))
    try:
        return spec["make"](**options)
    except TypeError:
        need = [k for k, v in spec["options"].items() if "required" in v and k not in options]
        raise LayoutError("the joint '%s' needs: %s" % (name, ", ".join(need) or "different options"))
